# Tóm Tắt Dự Án: Trợ Lý Điều Khiển Laptop Igris

Dự án phát triển một Trợ lý điều khiển Laptop chạy local 100% trên hệ điều hành Windows 11, hoạt động như một kỵ sĩ hộ vệ kỹ thuật số trung thành mang tên **Igris**.

## 🖥️ Môi Trường Cấu Hình Phần Cứng
- **Thiết bị**: Legion 5 Pro 2023
- **CPU**: Intel Core i9-13900HX
- **GPU**: NVIDIA GeForce RTX 4060
- **Hệ điều hành**: Windows 11

## ⚙️ Công Nghệ Sử Dụng (Tech Stack)
1. **Ngôn ngữ & Runtime**: Python bất đồng bộ (`asyncio`).
2. **Framework điều khiển**: Google Antigravity SDK (`LocalAgentConfig`).
3. **Mô hình ngôn ngữ (LLM)**: Ollama kết nối qua local endpoint (`http://localhost:11434/v1`) sử dụng model `qwen2.5:7b`.
4. **Nhận diện giọng nói (STT)**: `faster-whisper` chạy trực tiếp trên GPU Nvidia qua CUDA (`device="cuda"`, `compute_type="float16"`).

## ⚔️ Các Tính Năng Chính
- **Điều khiển ứng dụng (`tools/apps.py`)**:
  - Mở ứng dụng hệ thống (Chrome, Notepad, v.v.).
  - Thao tác trình duyệt (Mở tab mới, truy cập URL được chỉ định).
- **Điều khiển hệ thống (`tools/system.py`)**:
  - Truy vấn trạng thái pin và nguồn điện qua PowerShell.
  - Tăng, giảm hoặc tắt tiếng âm lượng hệ thống.
  - Tăng, giảm độ sáng màn hình laptop.
- **Tương tác giọng nói thời gian thực (`core/stt.py`)**:
  - Thu âm từ micrô và nhận diện ngôn ngữ tự động (Việt, Anh, Nhật, Trung...).
- **Xử lý hội thoại & Ký tự kỵ sĩ (`core/agent.py`)**:
  - Định hình phong cách giao tiếp cung kính, ngắn gọn của Igris.
  - Tự động gọi các công cụ điều khiển hệ thống dựa trên yêu cầu của chủ nhân.

## 🛡️ Nguyên Tắc An Toàn Hệ Thống
- Tuyệt đối không tích hợp các chức năng phá hủy hoặc nguy hiểm như: xóa file/thư mục, tạo file tự do ngoài vùng chỉ định, tắt nguồn (shutdown) hoặc khởi động lại (restart) thiết bị.
- Nếu chủ nhân đưa ra yêu cầu phá hủy hoặc nằm ngoài phạm vi an toàn, Igris sẽ cung kính từ chối thực hiện để bảo vệ an toàn cho hệ thống.
