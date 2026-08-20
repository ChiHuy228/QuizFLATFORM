# AzulQuiz - Django

Website tạo bài trắc nghiệm từ file Word `.docx` và chia sẻ bằng link.

## 1. Cài đặt

```bash
python -m venv venv
```

Windows:
```bash
venv\Scripts\activate
```

macOS/Linux:
```bash
source venv/bin/activate
```

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Mở: http://127.0.0.1:8000/

## 2. Format DOCX

Dùng đúng mẫu:

```text
Câu 1: Thủ đô của Việt Nam là gì?
A. Hà Nội
B. Hồ Chí Minh
C. Đà Nẵng
D. Hải Phòng
Đáp án: A

Câu 2: 1 + 1 bằng bao nhiêu?
A. 1
B. 2
C. 3
D. 4
Đáp án: B
```

Parser hiện hỗ trợ tiêu đề `Câu`, `Cau`, `Question`, `Q`; đáp án A-D; dòng `Đáp án`, `Dap an`, `ĐA`, `DA`, `Answer`.

## 3. Cách chia sẻ cho bạn bè

Khi chạy local, link kiểu `http://127.0.0.1:8000/quiz/...` chỉ dùng trên máy bạn. Để bạn bè truy cập từ Internet, cần deploy website lên một server/hosting và dùng domain/URL công khai.

## 4. Đây là bản MVP

Đã có:
- Upload DOCX
- Parse câu hỏi và đáp án
- Lưu SQLite
- Tạo quiz
- Link chia sẻ bằng UUID
- Người khác mở link và làm bài
- Tự động chấm điểm
- Hiển thị kết quả

Chưa có:
- Tài khoản người tạo
- Quản lý danh sách quiz
- Hẹn giờ
- Trộn câu/đáp án
- Bảng xếp hạng
- Giới hạn số lần làm
- PostgreSQL production
