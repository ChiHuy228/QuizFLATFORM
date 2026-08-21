import json
import logging
import random

from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import WordUploadForm
from .models import Answer, Attempt, Question, Quiz
from .parser import ANSWER_KEYS, parse_docx


logger = logging.getLogger(__name__)

QUIZ_DRAFT_SESSION_KEY = "quiz_draft"
QUIZ_DRAFT_SCHEMA_VERSION = 1
MAX_DRAFT_JSON_BYTES = 5 * 1024 * 1024


def _make_quiz_draft(title, parsed_questions):
    questions = []
    for item in parsed_questions:
        questions.append(
            {
                "number": item["number"],
                "text": item["text"],
                "answers": [
                    {
                        "key": answer["key"],
                        "text": answer["text"],
                    }
                    for answer in item["answers"]
                ],
                "correct_key": item["correct_key"],
                "status": item["status"],
                "issues": item["issues"],
            }
        )

    draft = {
        "schema_version": QUIZ_DRAFT_SCHEMA_VERSION,
        "title": title,
        "questions": questions,
    }

    serialized = json.dumps(draft, ensure_ascii=False).encode("utf-8")
    if len(serialized) > MAX_DRAFT_JSON_BYTES:
        raise ValueError(
            "Nội dung sau khi phân tích quá lớn. "
            "Vui lòng chia file thành các đề nhỏ hơn."
        )

    return draft


def _get_quiz_draft(request):
    draft = request.session.get(QUIZ_DRAFT_SESSION_KEY)
    if not isinstance(draft, dict):
        return None
    if draft.get("schema_version") != QUIZ_DRAFT_SCHEMA_VERSION:
        return None
    if not isinstance(draft.get("title"), str) or not draft["title"].strip():
        return None
    if not isinstance(draft.get("questions"), list) or not draft["questions"]:
        return None
    return draft


def _validate_review(draft, post_data=None):
    reviewed_questions = []
    is_valid = True

    for index, item in enumerate(draft["questions"]):
        errors = []
        answers = item.get("answers", []) if isinstance(item, dict) else []

        if not isinstance(answers, list):
            answers = []
            errors.append("Danh sách lựa chọn không hợp lệ.")

        answer_keys = []
        for answer in answers:
            if not isinstance(answer, dict):
                errors.append("Dữ liệu lựa chọn không hợp lệ.")
                continue

            key = answer.get("key")
            text = answer.get("text")
            if not isinstance(key, str) or key not in ANSWER_KEYS:
                errors.append("Nhãn lựa chọn phải thuộc A-D.")
            else:
                answer_keys.append(key)
            if not isinstance(text, str) or not text.strip():
                errors.append("Mỗi lựa chọn phải có nội dung.")

        question_text = item.get("text") if isinstance(item, dict) else None
        if not isinstance(question_text, str) or not question_text.strip():
            errors.append("Câu hỏi chưa có nội dung.")
        if len(answers) < 2:
            errors.append("Câu hỏi cần có ít nhất 2 lựa chọn.")
        if len(answer_keys) != len(set(answer_keys)):
            errors.append("Các lựa chọn không được trùng nhãn.")

        field_name = f"correct_{index}"
        if post_data is None:
            parser_key = item.get("correct_key") if isinstance(item, dict) else None
            selected_values = [parser_key] if parser_key else []
        elif hasattr(post_data, "getlist"):
            selected_values = post_data.getlist(field_name)
        else:
            posted_key = post_data.get(field_name)
            selected_values = [posted_key] if posted_key else []

        selected_key = selected_values[0] if len(selected_values) == 1 else None
        if len(selected_values) != 1:
            errors.append("Câu hỏi phải có chính xác 1 đáp án đúng.")
        elif selected_key not in answer_keys:
            errors.append("Đáp án đúng đã chọn không thuộc câu hỏi này.")

        reviewed_questions.append(
            {
                **(item if isinstance(item, dict) else {}),
                "field_name": field_name,
                "selected_key": selected_key,
                "errors": list(dict.fromkeys(errors)),
            }
        )
        if errors:
            is_valid = False

    return reviewed_questions, is_valid


def _create_quiz_from_review(draft, reviewed_questions):
    with transaction.atomic():
        quiz = Quiz.objects.create(title=draft["title"].strip())

        question_rows = Question.objects.bulk_create(
            [
                Question(
                    quiz=quiz,
                    content=item["text"].strip(),
                    order=question_order,
                )
                for question_order, item in enumerate(
                    reviewed_questions,
                    start=1,
                )
            ]
        )

        answer_rows = []
        for question, item in zip(question_rows, reviewed_questions):
            answer_rows.extend(
                Answer(
                    question=question,
                    label=answer["key"],
                    content=answer["text"].strip(),
                    is_correct=answer["key"] == item["selected_key"],
                    order=answer_order,
                )
                for answer_order, answer in enumerate(
                    item["answers"],
                    start=1,
                )
            )

        Answer.objects.bulk_create(answer_rows)

    return quiz


def home(request):
    """Upload and parse a DOCX into a session-backed review draft."""

    if request.method == "POST":

        form = WordUploadForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            try:

                # ==========================================
                # 1. ĐỌC FILE WORD
                # ==========================================

                parsed = parse_docx(
                    form.cleaned_data["docx_file"]
                )

                if not parsed:
                    raise ValueError(
                        "Không tìm thấy câu hỏi nào trong file Word. "
                        "Vui lòng kiểm tra lại định dạng file."
                    )

                draft = _make_quiz_draft(
                    form.cleaned_data["title"],
                    parsed,
                )
                request.session[QUIZ_DRAFT_SESSION_KEY] = draft

                return redirect("quiz_review")

            except ValueError as exc:

                messages.error(
                    request,
                    f"Không thể phân tích file: {exc}"
                )

            except Exception:

                logger.exception("Không thể phân tích file DOCX")
                messages.error(
                    request,
                    "Không thể đọc file Word. Vui lòng kiểm tra file và thử lại."
                )

    else:

        form = WordUploadForm()
            
     

    return render(
        request,
        "quizapp/home.html",
        {
            "form": form
        }
    )


def quiz_review(request):
    """Review a parsed draft and create the quiz only after validation."""
    draft = _get_quiz_draft(request)
    if draft is None:
        request.session.pop(QUIZ_DRAFT_SESSION_KEY, None)
        messages.error(
            request,
            "Bản nháp không còn tồn tại. Vui lòng tải lại file Word."
        )
        return redirect("home")

    post_data = request.POST if request.method == "POST" else None
    reviewed_questions, is_valid = _validate_review(draft, post_data)

    if request.method == "POST" and is_valid:
        try:
            quiz = _create_quiz_from_review(draft, reviewed_questions)
        except Exception:
            logger.exception("Không thể tạo quiz từ draft")
            messages.error(
                request,
                "Không thể tạo bài trắc nghiệm lúc này. Vui lòng thử lại."
            )
        else:
            request.session.pop(QUIZ_DRAFT_SESSION_KEY, None)
            return redirect(
                "quiz_created",
                share_code=quiz.share_code,
            )

    return render(
        request,
        "quizapp/quiz_review.html",
        {
            "draft": draft,
            "reviewed_questions": reviewed_questions,
        },
    )


# ==========================================================
# TRANG TẠO BÀI THÀNH CÔNG
# ==========================================================

def quiz_created(request, share_code):
    """
    Trang xuất hiện ngay sau khi tạo Quiz.

    Người tạo có thể:
    - Xem số câu
    - Sao chép link
    - Làm bài thử
    - Tạo bài khác
    """

    quiz = get_object_or_404(
        Quiz,
        share_code=share_code
    )

    # Tạo URL của trang làm bài
    share_url = request.build_absolute_uri(
        reverse(
            "take_quiz",
            kwargs={
                "share_code": str(
                    quiz.share_code
                )
            }
        )
    )

    return render(
        request,
        "quizapp/quiz_created.html",
        {
            "quiz": quiz,
            "share_url": share_url,
        }
    )


# ==========================================================
# TRANG LÀM BÀI
# ==========================================================

def take_quiz(request, share_code):
    """
    Trang làm bài.

    Mỗi lần mở link:
    - Lấy toàn bộ câu hỏi
    - Đảo thứ tự câu hỏi
    - Đảo thứ tự đáp án
    """

    quiz = get_object_or_404(
        Quiz,
        share_code=share_code
    )

    # ==========================================
    # LẤY TOÀN BỘ CÂU HỎI
    # ==========================================

    questions = list(
        quiz.questions.prefetch_related(
            "answers"
        )
    )

    # ==========================================
    # ĐẢO CÂU HỎI
    # ==========================================

    random.shuffle(
        questions
    )

    # ==========================================
    # ĐẢO ĐÁP ÁN
    # ==========================================

    for question in questions:

        answers = list(
            question.answers.all()
        )

        random.shuffle(
            answers
        )

        # Gắn danh sách đáp án đã đảo
        # cho template sử dụng
        question.randomized_answers = answers

    return render(
        request,
        "quizapp/take_quiz.html",
        {
            "quiz": quiz,
            "questions": questions,
        }
    )


# ==========================================================
# NỘP BÀI
# ==========================================================

def submit_quiz(request, share_code):
    """
    Nhận bài làm và chấm điểm.

    Việc random đáp án không ảnh hưởng đến chấm điểm
    vì chúng ta gửi Answer ID thay vì chỉ gửi A/B/C/D.
    """

    quiz = get_object_or_404(
        Quiz,
        share_code=share_code
    )

    # Nếu người dùng truy cập bằng GET
    if request.method != "POST":

        return redirect(
            "take_quiz",
            share_code=share_code
        )

    # ==========================================
    # LẤY TÊN
    # ==========================================

    name = request.POST.get(
        "participant_name",
        ""
    ).strip()

    if not name:

        messages.error(
            request,
            "Vui lòng nhập họ tên."
        )

        return redirect(
            "take_quiz",
            share_code=share_code
        )

    # ==========================================
    # LẤY CÂU HỎI
    # ==========================================

    questions = list(
        quiz.questions.prefetch_related(
            "answers"
        )
    )

    score = 0

    # ==========================================
    # CHẤM ĐIỂM
    # ==========================================

    for question in questions:

        selected_answer_id = request.POST.get(
            f"question_{question.id}"
        )

        if not selected_answer_id:
            continue

        try:

            selected_answer = question.answers.get(
                id=int(
                    selected_answer_id
                )
            )

            if selected_answer.is_correct:
                score += 1

        except (
            Answer.DoesNotExist,
            ValueError,
            TypeError
        ):

            continue

    # ==========================================
    # LƯU KẾT QUẢ
    # ==========================================

    attempt = Attempt.objects.create(
        quiz=quiz,
        participant_name=name[:120],
        score=score,
        total=len(questions),
    )

    return redirect(
        "result",
        share_code=share_code,
        attempt_id=attempt.id
    )


# ==========================================================
# KẾT QUẢ
# ==========================================================

def result(request, share_code, attempt_id):

    quiz = get_object_or_404(
        Quiz,
        share_code=share_code
    )

    attempt = get_object_or_404(
        Attempt,
        id=attempt_id,
        quiz=quiz
    )

    share_url = request.build_absolute_uri(
        reverse(
            "take_quiz",
            kwargs={
                "share_code": str(
                    quiz.share_code
                )
            }
        )
    )

    return render(
        request,
        "quizapp/result.html",
        {
            "quiz": quiz,
            "attempt": attempt,
            "share_url": share_url,
        }
    )
