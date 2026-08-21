from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from docx import Document

from quizapp.models import Answer, Attempt, Question, Quiz
from quizapp.views import QUIZ_DRAFT_SESSION_KEY


def make_docx_upload(name, lines):
    document = Document()
    for line in lines:
        document.add_paragraph(line)

    file_obj = BytesIO()
    document.save(file_obj)
    return SimpleUploadedFile(
        name,
        file_obj.getvalue(),
        content_type=(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
    )


class AzulQuizFullRegressionTests(TestCase):
    def upload_docx(self, title, lines):
        return self.client.post(
            reverse("home"),
            {
                "title": title,
                "docx_file": make_docx_upload("questions.docx", lines),
            },
        )

    def test_legacy_docx_upload_reaches_review_without_database_write(self):
        response = self.upload_docx(
            "Đề format cũ",
            [
                "Câu 1: Thủ đô Việt Nam là gì?",
                "A. Hà Nội",
                "B. Hồ Chí Minh",
                "C. Đà Nẵng",
                "D. Hải Phòng",
                "Đáp án: A",
            ],
        )

        self.assertRedirects(
            response,
            reverse("quiz_review"),
            fetch_redirect_response=False,
        )
        draft = self.client.session[QUIZ_DRAFT_SESSION_KEY]
        self.assertEqual(draft["questions"][0]["correct_key"], "A")
        self.assertEqual(draft["questions"][0]["status"], "valid")
        self.assertEqual(Quiz.objects.count(), 0)

    def test_missing_correct_is_completed_during_review(self):
        upload_response = self.upload_docx(
            "Đề thiếu correct",
            [
                "Câu 1: Một cộng một bằng mấy?",
                "A. Một",
                "B. Hai",
            ],
        )
        self.assertRedirects(
            upload_response,
            reverse("quiz_review"),
            fetch_redirect_response=False,
        )

        review_response = self.client.get(reverse("quiz_review"))
        self.assertContains(review_response, "Thiếu đáp án đúng")
        self.assertEqual(Quiz.objects.count(), 0)

        create_response = self.client.post(
            reverse("quiz_review"),
            {"correct_0": "B"},
        )

        quiz = Quiz.objects.get(title="Đề thiếu correct")
        self.assertRedirects(
            create_response,
            reverse("quiz_created", kwargs={"share_code": quiz.share_code}),
            fetch_redirect_response=False,
        )
        self.assertTrue(quiz.questions.get().answers.get(label="B").is_correct)
        self.assertFalse(quiz.questions.get().answers.get(label="A").is_correct)

    def test_star_docx_runs_through_share_take_submit_and_result(self):
        upload_response = self.upload_docx(
            "Đề full regression",
            [
                "Câu 1: Màu của bầu trời quang là gì?",
                "A. Đỏ",
                "*B. Xanh",
                "C. Vàng",
                "D. Tím",
            ],
        )
        self.assertRedirects(
            upload_response,
            reverse("quiz_review"),
            fetch_redirect_response=False,
        )

        review_response = self.client.get(reverse("quiz_review"))
        self.assertContains(review_response, 'value="B"')
        self.assertContains(review_response, "checked", count=1)

        create_response = self.client.post(
            reverse("quiz_review"),
            {"correct_0": "B"},
        )
        quiz = Quiz.objects.get(title="Đề full regression")
        self.assertRedirects(
            create_response,
            reverse("quiz_created", kwargs={"share_code": quiz.share_code}),
            fetch_redirect_response=False,
        )
        self.assertNotIn(QUIZ_DRAFT_SESSION_KEY, self.client.session)

        question = Question.objects.get(quiz=quiz)
        answers = list(Answer.objects.filter(question=question))
        self.assertEqual(len(answers), 4)
        self.assertEqual(sum(answer.is_correct for answer in answers), 1)
        correct_answer = Answer.objects.get(question=question, label="B")
        self.assertTrue(correct_answer.is_correct)

        created_response = self.client.get(
            reverse("quiz_created", kwargs={"share_code": quiz.share_code})
        )
        take_url = reverse("take_quiz", kwargs={"share_code": quiz.share_code})
        expected_share_url = f"http://testserver{take_url}"
        self.assertContains(created_response, expected_share_url)
        self.assertContains(created_response, "Đề full regression")

        take_response = self.client.get(take_url)
        self.assertContains(take_response, "Màu của bầu trời quang là gì?")
        self.assertContains(take_response, "Xanh")
        self.assertContains(take_response, f'value="{correct_answer.id}"')

        submit_response = self.client.post(
            reverse("submit_quiz", kwargs={"share_code": quiz.share_code}),
            {
                "participant_name": "Người kiểm thử",
                f"question_{question.id}": str(correct_answer.id),
            },
        )

        attempt = Attempt.objects.get(quiz=quiz)
        self.assertEqual(attempt.participant_name, "Người kiểm thử")
        self.assertEqual(attempt.score, 1)
        self.assertEqual(attempt.total, 1)
        result_url = reverse(
            "result",
            kwargs={
                "share_code": quiz.share_code,
                "attempt_id": attempt.id,
            },
        )
        self.assertRedirects(
            submit_response,
            result_url,
            fetch_redirect_response=False,
        )

        result_response = self.client.get(result_url)
        self.assertContains(result_response, "Người kiểm thử")
        self.assertContains(result_response, "1/1")
        self.assertContains(result_response, "100,0%")
        self.assertContains(result_response, expected_share_url)
