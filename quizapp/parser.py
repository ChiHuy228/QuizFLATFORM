import re
from docx import Document

QUESTION_RE = re.compile(r'^\s*(?:Câu|Cau|Question|Q)\s*(\d+)\s*[:.)-]?\s*(.+)$', re.I)
ANSWER_RE = re.compile(r'^\s*([A-D])\s*[.)\-:]\s*(.+)$', re.I)
CORRECT_RE = re.compile(r'^\s*(?:Đáp án|Dap an|ĐA|DA|Answer|Correct answer)\s*[:.)\-]?\s*([A-D])\b', re.I)


def clean(text):
    return re.sub(r'\s+', ' ', text).strip()


def parse_docx(file_obj):
    """Parse a deliberately simple, stable DOCX format.

    Example:
      Câu 1: Thủ đô Việt Nam là gì?
      A. Hà Nội
      B. Huế
      C. Đà Nẵng
      D. Cần Thơ
      Đáp án: A
    """
    document = Document(file_obj)
    lines = [clean(p.text) for p in document.paragraphs if clean(p.text)]

    questions = []
    current = None
    current_correct = None

    def flush():
        nonlocal current
        if not current:
            return
        if not current['answers']:
            raise ValueError(f"Câu {current['number']} chưa có đáp án A-D.")
        if current['correct'] is None:
            raise ValueError(f"Câu {current['number']} chưa có dòng 'Đáp án: X'.")
        labels = {a['label'] for a in current['answers']}
        if current['correct'] not in labels:
            raise ValueError(f"Đáp án đúng của câu {current['number']} không tồn tại trong A-D.")
        questions.append(current)
        current = None

    for line in lines:
        q_match = QUESTION_RE.match(line)
        a_match = ANSWER_RE.match(line)
        c_match = CORRECT_RE.match(line)

        if q_match:
            flush()
            current = {
                'number': int(q_match.group(1)),
                'content': q_match.group(2).strip(),
                'answers': [],
                'correct': None,
            }
        elif current and a_match:
            current['answers'].append({
                'label': a_match.group(1).upper(),
                'content': a_match.group(2).strip(),
            })
        elif current and c_match:
            current['correct'] = c_match.group(1).upper()
        elif current:
            # A continuation line is appended to the question text before answers.
            if not current['answers']:
                current['content'] = f"{current['content']} {line}".strip()

    flush()

    if not questions:
        raise ValueError('Không tìm thấy câu hỏi. Hãy dùng đúng mẫu DOCX trong README.')
    return questions
