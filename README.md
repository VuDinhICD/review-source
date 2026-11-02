# 🔍 ServiceNow Script Include AI Reviewer

Đây là công cụ hỗ trợ Review Code tự động dành riêng cho **Script Include** trên nền tảng ServiceNow. Dự án sử dụng **Streamlit** để xây dựng giao diện web và tích hợp **Google Gemini AI** để phân tích mã nguồn dựa trên các tiêu chuẩn Best Practices của ServiceNow và nguyên tắc thiết kế **SOLID**.

Đặc biệt, ứng dụng cung cấp giao diện so sánh code (Side-by-Side Diff) trực quan giống như GitHub Desktop/VS Code để developer dễ dàng nhận biết các thay đổi.

## ✨ Tính năng nổi bật

* 🚀 Lấy mã nguồn trực tiếp từ ServiceNow thông qua Table API.
* 🤖 Tự động review code bằng Google Gemini (đánh giá cấu trúc, hiệu năng, bảo mật, và SOLID).
* 🔄 Hiển thị Side-by-Side Diff so sánh code cũ và code mới trực quan (tô đỏ dòng xóa, tô xanh dòng thêm, vạch sọc dòng trống).
* 📋 Hỗ trợ copy nhanh toàn bộ mã nguồn đã được Refactor.

## 🛠 Yêu cầu hệ thống

* Python 3.9 trở lên.
* [Poetry](https://python-poetry.org/docs/#installation) (Trình quản lý gói chuẩn hiện đại của Python).
* Tài khoản ServiceNow (có quyền đọc bảng `sys_script_include`).
* Google Gemini API Key (Miễn phí qua Google AI Studio).

## 🚀 Hướng dẫn cài đặt

Dự án này sử dụng **Poetry** để quản lý thư viện (hoạt động tương tự như `npm` trong Node.js).

**Bước 1: Tải mã nguồn về máy**
Clone repository này hoặc tải mã nguồn về và giải nén.

**Bước 2: Cài đặt thư viện**
Mở Terminal/Command Prompt tại thư mục dự án và chạy lệnh sau (chỉ cần gõ 1 lệnh duy nhất):

```bash
poetry install
```

**Bước 3: Thiết lập biến môi trường**

1. Copy file `.env.example` và đổi tên thành `.env`.
2. Mở file `.env` và điền các thông tin xác thực của bạn:
   * `SN_INSTANCE`: Đường dẫn instance của bạn (VD: `https://devXXXXX.service-now.com`).
   * `SN_USER`: Tên đăng nhập ServiceNow.
   * `SN_PASSWORD`: Mật khẩu ServiceNow.
   * `GEMINI_API_KEY`: API Key lấy từ Google AI Studio.

*(Lưu ý: File `.env` đã được cấu hình ẩn trong `.gitignore` để tránh bị lộ mật khẩu khi push lên Git).*

## 🎯 Hướng dẫn sử dụng

Tại thư mục gốc của dự án, khởi chạy giao diện web bằng lệnh:

```bash
poetry run streamlit run app.py
```

*(Hoặc bạn có thể gõ `poetry shell` để vào môi trường ảo, sau đó chạy trực tiếp `streamlit run app.py`).*

Trình duyệt sẽ tự động mở trang web (thường tại `http://localhost:8501`). Bạn chỉ cần nhập tên Script Include cần kiểm tra và bấm nút **"Bắt đầu Review"**.