# AzulQuiz

AzulQuiz là ứng dụng Django tạo bài trắc nghiệm từ file Word `.docx`. Người tạo có thể review câu hỏi, chọn lại đáp án đúng, tạo quiz và chia sẻ link cho người khác làm bài.

Project chỉ sử dụng Supabase PostgreSQL, không sử dụng SQLite.

## Yêu cầu

- Python 3.12 trở lên.
- Git.
- Một Supabase project và thông tin kết nối PostgreSQL.

## Chạy project trên máy local

### 1. Clone repository

```bash
git clone https://github.com/ChiHuy228/QuizFLATFORM.git
cd QuizFLATFORM
```

### 2. Tạo virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```bat
python -m venv .venv
.venv\Scripts\activate.bat
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Cài đặt dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Chuẩn bị Supabase PostgreSQL

Tạo một Supabase project hoặc xin thông tin kết nối từ chủ repository.

Trong Supabase Dashboard, mở **Connect** và lấy các giá trị:

- Database name
- User
- Password
- Host
- Port

Với mạng local chỉ hỗ trợ IPv4, có thể dùng **Session pooler** port `5432`. Xem thêm [Supabase database connection guide](https://supabase.com/docs/guides/database/connecting-to-postgres).

### 5. Tạo file `.env`

Sao chép file mẫu:

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Windows Command Prompt:

```bat
copy .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

Mở `.env` và điền cấu hình local:

```dotenv
DJANGO_SECRET_KEY=your-secret-key
DEBUG=True

DB_NAME=postgres
DB_USER=your-supabase-database-user
DB_PASSWORD=your-supabase-database-password
DB_HOST=your-supabase-database-host
DB_PORT=5432

ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
```

Có thể tạo Django secret key bằng lệnh:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Sao chép kết quả vào `DJANGO_SECRET_KEY`.

Không commit file `.env` hoặc chia sẻ password Supabase.

### 6. Tạo các bảng Django trên Supabase

Nếu Supabase project chưa có các bảng của AzulQuiz, chạy:

```bash
python manage.py migrate
```

Lệnh này tạo các bảng cần thiết như `quizapp_quiz`, `quizapp_question`, `quizapp_answer`, `quizapp_attempt` và `django_session`.

Nếu dùng database đã có sẵn dữ liệu, hãy kiểm tra đúng Supabase project trước khi chạy migration.

### 7. Kiểm tra cấu hình

```bash
python manage.py check
python manage.py shell -c "from django.db import connection; print(connection.vendor)"
```

Kết quả database vendor phải là:

```text
postgresql
```

### 8. Khởi động ứng dụng

```bash
python manage.py runserver
```

Mở trình duyệt tại:

```text
http://127.0.0.1:8000/
```

Trên Windows, có thể dùng Waitress thay cho Django development server:

```bat
start.bat
```

## Cách sử dụng

1. Mở trang chủ.
2. Nhập tên quiz và upload file `.docx`.
3. Kiểm tra nội dung đã parse ở trang review.
4. Chọn đúng một đáp án đúng cho mỗi câu hỏi.
5. Tạo quiz.
6. Sao chép link chia sẻ để mở trang làm bài.

## Format file DOCX

Format cơ bản:

```text
Câu 1: Thủ đô của Việt Nam là gì?
A. Hà Nội
B. Thành phố Hồ Chí Minh
C. Đà Nẵng
D. Hải Phòng
Đáp án: A

Câu 2: 1 + 1 bằng bao nhiêu?
A. 1
B. 2
C. 3
D. 4
Đáp án đúng: B
```

Có thể đánh dấu đáp án đúng bằng dấu `*`:

```text
*A. Nội dung đáp án
* A. Nội dung đáp án
A. *Nội dung đáp án
```

Parser cũng chấp nhận Word bullet:

```text
- A. Nội dung đáp án
- B. Nội dung đáp án
```

Nếu thiếu hoặc có nhiều dấu hiệu đáp án đúng mâu thuẫn, file vẫn được parse. Người tạo sẽ chọn lại đáp án đúng ở trang review.

## Khắc phục lỗi thường gặp

### `no such table: django_session`

Project đang chạy sai database hoặc chưa apply migrations.

Kiểm tra backend:

```bash
python manage.py shell -c "from django.conf import settings; from django.db import connection; print(settings.SETTINGS_MODULE); print(connection.vendor)"
```

Kết quả đúng:

```text
quizplatform.settings
postgresql
```

Sau đó kiểm tra migration:

```bash
python manage.py showmigrations --plan
python manage.py migrate
```

### Không kết nối được Supabase

Kiểm tra lại `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, trạng thái Supabase project và kết nối mạng. Với mạng IPv4, ưu tiên Session pooler port `5432`.

### Port 8000 đang được sử dụng

Dừng server cũ hoặc chạy bằng port khác:

```bash
python manage.py runserver 127.0.0.1:8010
```

Sau đó mở `http://127.0.0.1:8010/`.
