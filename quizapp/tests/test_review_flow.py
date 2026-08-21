import json
import uuid
from io import BytesIO
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from docx import Document

from quizapp.models import Answer, Question, Quiz
from quizapp.views import QUIZ_DRAFT_SESSION_KEY


def parsed_question(
    number=1,
    text="Thủ đô Việt Nam là gì?",
    correct_key="A",
    status="valid",
    answers=None,
):
    if answers is None:
        answers = [
            {"key": "A", "text": "Hà Nội"},
            {"key": "B", "text": "Hồ Chí Minh"},
        ]

    return {
        "number": number,
        "text": text,
        "answers": [
            {
                "key": answer["key"],
                "text": answer["text"],
                "label": answer["key"],
                "content": answer["text"],
            }
            for answer in answers
        ],
        "correct_key": correct_key,
        "status": status,
        "issues": [],
        "content": text,
        "correct": correct_key,
    }


class QuizReviewFlowTests(TestCase):
    def upload(self, parsed_questions):
        upload = SimpleUploadedFile(
            "questions.docx",
            b"fake docx content",
            content_type=(
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ),
        )
        with patch("quizapp.views.parse_docx", return_value=parsed_questions):
            return self.client.post(
                reverse("home"),
                {"title": "Đề kiểm tra", "docx_file": upload},
            )

    def test_upload_stores_json_draft_without_creating_database_records(self):
        response = self.upload([parsed_question()])

        self.assertRedirects(
            response,
            reverse("quiz_review"),
            fetch_redirect_response=False,
        )
        self.assertEqual(Quiz.objects.count(), 0)
        self.assertEqual(Question.objects.count(), 0)
        self.assertEqual(Answer.objects.count(), 0)

        draft = self.client.session[QUIZ_DRAFT_SESSION_KEY]
        json.dumps(draft, ensure_ascii=False)
        self.assertEqual(draft["title"], "Đề kiểm tra")
        self.assertNotIn("label", draft["questions"][0]["answers"][0])
        self.assertNotIn("content", draft["questions"][0]["answers"][0])

    def test_review_get_renders_draft_without_creating_records(self):
        self.upload(
            [
                parsed_question(),
                parsed_question(
                    number=2,
                    text="Một cộng một bằng mấy?",
                    correct_key=None,
                    status="missing_correct_answer",
                ),
            ]
        )

        response = self.client.get(reverse("quiz_review"))

        self.assertContains(response, "Thủ đô Việt Nam là gì?")
        self.assertContains(response, "Một cộng một bằng mấy?")
        self.assertContains(response, "Thiếu đáp án đúng")
        self.assertContains(response, "Parser chưa tìm thấy đáp án đúng")
        self.assertContains(response, 'class="col-lg-5 d-flex"')
        self.assertContains(response, 'class="col-lg-7 d-flex"')
        self.assertContains(response, "review-panel__body", count=2)
        self.assertContains(response, 'name="correct_0"', count=2)
        self.assertContains(response, "checked", count=1)
        self.assertEqual(Quiz.objects.count(), 0)

    def test_review_rejects_answer_key_not_owned_by_question(self):
        self.upload([parsed_question()])

        response = self.client.post(
            reverse("quiz_review"),
            {"correct_0": "D"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Đáp án đúng đã chọn không thuộc câu hỏi này")
        self.assertEqual(Quiz.objects.count(), 0)
        self.assertIn(QUIZ_DRAFT_SESSION_KEY, self.client.session)

    def test_review_rejects_more_than_one_posted_correct_answer(self):
        self.upload([parsed_question()])

        response = self.client.post(
            reverse("quiz_review"),
            {"correct_0": ["A", "B"]},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "phải có chính xác 1 đáp án đúng")
        self.assertEqual(Quiz.objects.count(), 0)
        self.assertIn(QUIZ_DRAFT_SESSION_KEY, self.client.session)

    def test_one_invalid_question_prevents_every_database_write(self):
        self.upload(
            [
                parsed_question(),
                parsed_question(
                    number=2,
                    text="Câu bị thiếu lựa chọn",
                    correct_key="A",
                    status="missing_answers",
                    answers=[{"key": "A", "text": "Chỉ một lựa chọn"}],
                ),
            ]
        )

        response = self.client.post(
            reverse("quiz_review"),
            {"correct_0": "A", "correct_1": "A"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Câu hỏi cần có ít nhất 2 lựa chọn")
        self.assertEqual(Quiz.objects.count(), 0)
        self.assertEqual(Question.objects.count(), 0)
        self.assertEqual(Answer.objects.count(), 0)

    def test_review_post_creates_quiz_and_clears_draft(self):
        self.upload(
            [
                parsed_question(),
                parsed_question(
                    number=2,
                    text="Một cộng một bằng mấy?",
                    correct_key=None,
                    status="missing_correct_answer",
                ),
            ]
        )

        response = self.client.post(
            reverse("quiz_review"),
            {"correct_0": "A", "correct_1": "B"},
        )

        quiz = Quiz.objects.get()
        self.assertRedirects(
            response,
            reverse("quiz_created", kwargs={"share_code": quiz.share_code}),
            fetch_redirect_response=False,
        )
        self.assertEqual(quiz.questions.count(), 2)
        self.assertEqual(Answer.objects.filter(question__quiz=quiz).count(), 4)
        for question in quiz.questions.prefetch_related("answers"):
            self.assertEqual(
                sum(answer.is_correct for answer in question.answers.all()),
                1,
            )
        self.assertTrue(
            Answer.objects.get(
                question__quiz=quiz,
                question__order=2,
                label="B",
            ).is_correct
        )
        self.assertNotIn(QUIZ_DRAFT_SESSION_KEY, self.client.session)

    def test_real_legacy_docx_completes_full_create_flow(self):
        document = Document()
        for line in [
            "Câu 1: Thủ đô Việt Nam là gì?",
            "A. Hà Nội",
            "B. Hồ Chí Minh",
            "C. Đà Nẵng",
            "D. Hải Phòng",
            "Đáp án: A",
        ]:
            document.add_paragraph(line)

        file_obj = BytesIO()
        document.save(file_obj)
        upload = SimpleUploadedFile(
            "legacy.docx",
            file_obj.getvalue(),
            content_type=(
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ),
        )

        upload_response = self.client.post(
            reverse("home"),
            {"title": "Đề DOCX thật", "docx_file": upload},
        )
        self.assertRedirects(
            upload_response,
            reverse("quiz_review"),
            fetch_redirect_response=False,
        )
        self.assertEqual(Quiz.objects.count(), 0)

        create_response = self.client.post(
            reverse("quiz_review"),
            {"correct_0": "A"},
        )

        quiz = Quiz.objects.get(title="Đề DOCX thật")
        self.assertRedirects(
            create_response,
            reverse("quiz_created", kwargs={"share_code": quiz.share_code}),
            fetch_redirect_response=False,
        )
        self.assertEqual(quiz.questions.count(), 1)
        self.assertEqual(quiz.questions.get().answers.count(), 4)
        self.assertTrue(quiz.questions.get().answers.get(label="A").is_correct)

    @patch("quizapp.views.Answer.objects.bulk_create", side_effect=RuntimeError)
    def test_failed_create_rolls_back_and_keeps_draft(self, _bulk_create):
        self.upload([parsed_question()])

        with self.assertLogs("quizapp.views", level="ERROR"):
            response = self.client.post(
                reverse("quiz_review"),
                {"correct_0": "A"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Quiz.objects.count(), 0)
        self.assertEqual(Question.objects.count(), 0)
        self.assertEqual(Answer.objects.count(), 0)
        self.assertIn(QUIZ_DRAFT_SESSION_KEY, self.client.session)

    def test_missing_draft_redirects_to_upload(self):
        response = self.client.get(reverse("quiz_review"))

        self.assertRedirects(
            response,
            reverse("home"),
            fetch_redirect_response=False,
        )

    def test_existing_quiz_routes_are_unchanged(self):
        share_code = uuid.uuid4()

        self.assertEqual(
            reverse("take_quiz", kwargs={"share_code": share_code}),
            f"/quiz/{share_code}/",
        )
        self.assertEqual(
            reverse("submit_quiz", kwargs={"share_code": share_code}),
            f"/quiz/{share_code}/submit/",
        )
        self.assertEqual(
            reverse(
                "result",
                kwargs={"share_code": share_code, "attempt_id": 10},
            ),
            f"/quiz/{share_code}/result/10/",
        )
