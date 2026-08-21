import json
from io import BytesIO

from django.test import SimpleTestCase
from docx import Document

from quizapp.parser import parse_docx, parse_lines


class ParserTests(SimpleTestCase):
    def parse_one(self, answer_lines, correct_line=None):
        lines = ["Câu 1: Thủ đô Việt Nam là gì?", *answer_lines]
        if correct_line:
            lines.append(correct_line)
        return parse_lines(lines)[0]

    def test_legacy_correct_answer_line(self):
        question = self.parse_one(
            ["A. Hà Nội", "B. Hồ Chí Minh"],
            "Đáp án: A",
        )

        self.assertEqual(question["status"], "valid")
        self.assertEqual(question["correct_key"], "A")

    def test_legacy_docx_is_parsed_end_to_end(self):
        document = Document()
        for line in [
            "Câu 1: Thủ đô Việt Nam là gì?",
            "A. Hà Nội",
            "B. Hồ Chí Minh",
            "Đáp án: A",
        ]:
            document.add_paragraph(line)

        file_obj = BytesIO()
        document.save(file_obj)
        file_obj.seek(0)

        question = parse_docx(file_obj)[0]

        self.assertEqual(question["text"], "Thủ đô Việt Nam là gì?")
        self.assertEqual(question["correct_key"], "A")
        self.assertEqual(question["status"], "valid")

    def test_correct_answer_line_with_dung(self):
        question = self.parse_one(
            ["A. Hà Nội", "B. Hồ Chí Minh"],
            "Đáp án đúng: A",
        )

        self.assertEqual(question["status"], "valid")
        self.assertEqual(question["correct_key"], "A")

    def test_star_before_key_without_space(self):
        question = self.parse_one(["*A. Hà Nội", "B. Hồ Chí Minh"])

        self.assertEqual(question["status"], "valid")
        self.assertEqual(question["correct_key"], "A")

    def test_star_before_key_with_space(self):
        question = self.parse_one(["* A. Hà Nội", "B. Hồ Chí Minh"])

        self.assertEqual(question["status"], "valid")
        self.assertEqual(question["correct_key"], "A")

    def test_star_before_answer_text(self):
        question = self.parse_one(["A. *Hà Nội", "B. Hồ Chí Minh"])

        self.assertEqual(question["status"], "valid")
        self.assertEqual(question["correct_key"], "A")
        self.assertEqual(question["answers"][0]["text"], "Hà Nội")

    def test_word_bullet_before_answer_is_accepted(self):
        question = self.parse_one(
            ["- A. Hà Nội", "B. Hồ Chí Minh"],
            "Đáp án: A",
        )

        self.assertEqual(question["status"], "valid")
        self.assertEqual(question["answers"][0]["key"], "A")

    def test_missing_correct_answer_does_not_raise(self):
        question = self.parse_one(["A. Hà Nội", "B. Hồ Chí Minh"])

        self.assertEqual(question["status"], "missing_correct_answer")
        self.assertIsNone(question["correct_key"])

    def test_question_with_fewer_than_two_answers_has_missing_answers_status(self):
        question = self.parse_one(["A. Hà Nội"], "Đáp án: A")

        self.assertEqual(question["status"], "missing_answers")
        self.assertIn("ít nhất 2 lựa chọn", " ".join(question["issues"]))

    def test_question_without_text_has_invalid_question_status(self):
        question = parse_lines(
            ["Câu 1:", "A. Hà Nội", "B. Hồ Chí Minh", "Đáp án: A"]
        )[0]

        self.assertEqual(question["status"], "invalid_question")
        self.assertIn("chưa có nội dung", " ".join(question["issues"]))

    def test_two_starred_answers_are_a_conflict(self):
        question = self.parse_one(["*A. Hà Nội", "*B. Hồ Chí Minh"])

        self.assertEqual(question["status"], "conflict_correct_answer")
        self.assertIsNone(question["correct_key"])

    def test_star_and_declared_answer_conflict(self):
        question = self.parse_one(
            ["*A. Hà Nội", "B. Hồ Chí Minh"],
            "Đáp án: B",
        )

        self.assertEqual(question["status"], "conflict_correct_answer")
        self.assertIsNone(question["correct_key"])

    def test_matching_star_and_declared_answer_are_valid(self):
        question = self.parse_one(
            ["*A. Hà Nội", "B. Hồ Chí Minh"],
            "Đáp án: A",
        )

        self.assertEqual(question["status"], "valid")
        self.assertEqual(question["correct_key"], "A")

    def test_one_incomplete_question_does_not_reject_other_questions(self):
        questions = parse_lines(
            [
                "Câu 1: Câu hợp lệ?",
                "A. Một",
                "B. Hai",
                "Đáp án: A",
                "Câu 2: Câu thiếu đáp án đúng?",
                "A. Ba",
                "B. Bốn",
            ]
        )

        self.assertEqual(len(questions), 2)
        self.assertEqual(questions[0]["status"], "valid")
        self.assertEqual(questions[1]["status"], "missing_correct_answer")

    def test_result_has_required_fields_and_is_json_serializable(self):
        question = self.parse_one(
            ["A. Hà Nội", "B. Hồ Chí Minh"],
            "Đáp án: A",
        )

        self.assertTrue(
            {
                "number",
                "text",
                "answers",
                "correct_key",
                "status",
                "issues",
            }.issubset(question)
        )
        self.assertEqual(question["content"], question["text"])
        self.assertEqual(question["answers"][0]["label"], "A")
        json.dumps(question, ensure_ascii=False)
