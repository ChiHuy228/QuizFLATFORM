import random

from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import WordUploadForm
from .models import Answer, Attempt, Question, Quiz
from .parser import parse_docx


def home(request):
    """
    Trang chủ:
    Upload file DOCX -> bóc tách -> tạo Quiz.
    Sau khi tạo xong sẽ chuyển sang trang lấy link,
    KHÔNG bắt người dùng làm bài trước.
    """

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

                # Nếu file Word không có câu hỏi
                if not parsed:
                    raise ValueError(
                        "Không tìm thấy câu hỏi nào trong file Word. "
                        "Vui lòng kiểm tra lại định dạng file."
                    )

                # ==========================================
                # 2. TẠO QUIZ + CÂU HỎI + ĐÁP ÁN
                # ==========================================

                with transaction.atomic():

                    quiz = Quiz.objects.create(
                        title=form.cleaned_data["title"]
                    )

                    # Số câu phụ thuộc hoàn toàn vào file Word
                    for q_index, item in enumerate(
                        parsed,
                        start=1
                    ):

                        question = Question.objects.create(
                            quiz=quiz,
                            content=item["content"],
                            order=q_index,
                        )

                        # Lưu các đáp án
                        for a_index, answer in enumerate(
                            item["answers"],
                            start=1
                        ):

                            Answer.objects.create(
                                question=question,
                                label=answer["label"],
                                content=answer["content"],

                                # Đánh dấu đáp án đúng
                                is_correct=(
                                    answer["label"]
                                    == item["correct"]
                                ),

                                order=a_index,
                            )

                # ==========================================
                # 3. QUAN TRỌNG NHẤT
                # ==========================================
                #
                # TẠO XONG -> ĐI ĐẾN TRANG HIỂN THỊ LINK
                #
                # KHÔNG đi thẳng vào take_quiz
                #
                # ==========================================

                return redirect(
                    "quiz_created",
                    share_code=quiz.share_code
                )

            except Exception as exc:

                messages.error(
                    request,
                    f"Không thể tạo đề: {exc}"
                )

    else:

        form = WordUploadForm(
            initial={
                "title": "Bài trắc nghiệm mới"
            }
        )

    return render(
        request,
        "quizapp/home.html",
        {
            "form": form
        }
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