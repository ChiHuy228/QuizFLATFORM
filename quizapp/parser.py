import re

from docx import Document


STATUS_VALID = "valid"
STATUS_MISSING_CORRECT = "missing_correct_answer"
STATUS_CONFLICT_CORRECT = "conflict_correct_answer"
STATUS_MISSING_ANSWERS = "missing_answers"
STATUS_INVALID_QUESTION = "invalid_question"

ANSWER_KEYS = {"A", "B", "C", "D"}
CORRECT_PREFIXES = (
    "correct answer",
    "đáp án đúng",
    "dap an dung",
    "answer",
    "đáp án",
    "dap an",
    "đa",
    "da",
)

QUESTION_RE = re.compile(
    r"^\s*(?:Câu|Cau|Question|Q)\s*(\d+)\s*[:.)-]?\s*(.*)$",
    re.IGNORECASE,
)
ANSWER_RE = re.compile(
    r"^\s*([A-D])\s*[.)\-:]\s*(.*)$",
    re.IGNORECASE,
)


def clean(text):
    return re.sub(r"\s+", " ", text).strip()


def _match_question(line):
    match = QUESTION_RE.match(line)
    if not match:
        return None
    return int(match.group(1)), match.group(2).strip()


def _match_answer(line):
    value = line.strip()
    is_starred = False

    if value.startswith("*"):
        is_starred = True
        value = value[1:].lstrip()
    elif value.startswith("-"):
        # Accept a common Word bullet without treating it as a correct marker.
        value = value[1:].lstrip()

    match = ANSWER_RE.match(value)
    if not match:
        return None

    key = match.group(1).upper()
    text = match.group(2).strip()
    if text.startswith("*"):
        is_starred = True
        text = text[1:].lstrip()

    return {
        "key": key,
        "text": text,
        # Compatibility aliases for the existing create view.
        "label": key,
        "content": text,
    }, is_starred


def _match_declared_correct(line):
    folded_line = line.casefold()

    for prefix in CORRECT_PREFIXES:
        if not folded_line.startswith(prefix):
            continue

        remainder = line[len(prefix):].lstrip(" \t:.)-")
        if not remainder:
            return None

        key = remainder[0].upper()
        if key in ANSWER_KEYS and (
            len(remainder) == 1 or not remainder[1].isalnum()
        ):
            return key

    return None


def _resolve_correct_key(starred_keys, declared_keys):
    signals = starred_keys + declared_keys

    if len(starred_keys) > 1 or len(set(signals)) > 1:
        return None, True
    if signals:
        return signals[0], False
    return None, False


def _structure_issues(question, correct_key):
    answers = question["answers"]
    answer_keys = [answer["key"] for answer in answers]
    issues = []

    if not question["text"]:
        issues.append("Câu hỏi chưa có nội dung.")
    if len(answers) < 2:
        issues.append("Câu hỏi cần có ít nhất 2 lựa chọn.")
    if len(answer_keys) != len(set(answer_keys)):
        issues.append("Các lựa chọn trong câu hỏi bị trùng nhãn A-D.")
    if any(not answer["text"] for answer in answers):
        issues.append("Có lựa chọn chưa có nội dung.")
    if correct_key is not None and correct_key not in answer_keys:
        issues.append("Đáp án đúng không thuộc các lựa chọn của câu hỏi.")

    return issues


def _question_status(question, correct_key, has_conflict):
    answers = question["answers"]
    answer_keys = [answer["key"] for answer in answers]

    if has_conflict:
        return STATUS_CONFLICT_CORRECT
    if (
        not question["text"]
        or len(answer_keys) != len(set(answer_keys))
        or any(not answer["text"] for answer in answers)
        or (correct_key is not None and correct_key not in answer_keys)
    ):
        return STATUS_INVALID_QUESTION
    if len(answers) < 2:
        return STATUS_MISSING_ANSWERS
    if correct_key is None:
        return STATUS_MISSING_CORRECT
    return STATUS_VALID


def _finalize_question(question):
    correct_key, has_conflict = _resolve_correct_key(
        question.pop("starred_keys"),
        question.pop("declared_correct_keys"),
    )
    issues = _structure_issues(question, correct_key)

    if has_conflict:
        issues.insert(
            0,
            "Có nhiều đáp án được đánh dấu đúng hoặc các dấu hiệu bị mâu thuẫn.",
        )
    elif correct_key is None and len(question["answers"]) >= 2:
        issues.append("Chưa xác định được đáp án đúng.")

    status = _question_status(question, correct_key, has_conflict)
    question.update(
        {
            "correct_key": correct_key,
            "status": status,
            "issues": issues,
            # Compatibility aliases for the existing create view.
            "content": question["text"],
            "correct": correct_key,
        }
    )
    return question


def parse_lines(lines):
    """Parse normalized Word lines into JSON-serializable question drafts."""
    questions = []
    current = None

    def flush():
        nonlocal current
        if current is not None:
            questions.append(_finalize_question(current))
            current = None

    for raw_line in lines:
        line = clean(raw_line)
        if not line:
            continue

        matched_question = _match_question(line)
        if matched_question:
            flush()
            number, text = matched_question
            current = {
                "number": number,
                "text": text,
                "answers": [],
                "starred_keys": [],
                "declared_correct_keys": [],
            }
            continue

        if current is None:
            continue

        declared_key = _match_declared_correct(line)
        if declared_key:
            current["declared_correct_keys"].append(declared_key)
            continue

        matched_answer = _match_answer(line)
        if matched_answer:
            answer, is_starred = matched_answer
            current["answers"].append(answer)
            if is_starred:
                current["starred_keys"].append(answer["key"])
            continue

        # Preserve the old behavior for multi-line question text.
        if not current["answers"]:
            current["text"] = f'{current["text"]} {line}'.strip()

    flush()

    if not questions:
        raise ValueError(
            "Không tìm thấy câu hỏi. Hãy dùng đúng mẫu DOCX trong README."
        )

    return questions


def parse_docx(file_obj):
    """Parse a DOCX without rejecting the whole file for one incomplete question."""
    document = Document(file_obj)
    return parse_lines(paragraph.text for paragraph in document.paragraphs)
