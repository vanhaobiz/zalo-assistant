# 🤖 Zalo Auto-Reply Studio (Zalo Assistant)

Ứng dụng tự động trả lời tin nhắn Zalo Web cá nhân theo kịch bản tùy biến cho **từng Người**, **từng Nhóm**, và nhận diện khi được nhắc tên (`@Tag`).

---

## 🌟 Tính năng chính

- 🤖 **Tự động hóa Zalo Web (Playwright)**: Đăng nhập an toàn bằng quét mã QR trực quan, ghi nhớ phiên đăng nhập.
- 🎯 **Kịch bản linh hoạt**:
  - Trả lời riêng cho từng người cụ thể (Sếp, khách VIP, người thân...).
  - Trả lời theo từng nhóm, chỉ kích hoạt khi được tag `@Tên_của_bạn`.
  - Hỗ trợ trả lời tự động tất cả tin nhắn cá nhân (1-1) mà không cần tag `@`.
  - Khớp từ khóa (`chứa từ`, `chính xác`, `regex`, `tất cả`).
  - Hỗ trợ biến động: `{sender}`, `{chat_name}`, `{time}`, `{date}`, `{message}`.
- ⏱️ **Mô phỏng người thật**:
  - Độ trễ gõ phím ngẫu nhiên (VD: 2.0s - 5.5s).
  - Cơ chế chống spam / lặp tin nhắn cho mỗi hội thoại (`cooldown`).
- 🌐 **Web Dashboard trực quan**:
  - Quản lý kịch bản, bật/tắt từng người/nhóm nhanh chóng.
  - Xem màn hình Zalo trực tiếp ngay trên Dashboard.
  - Nút chuyển đổi **Giao diện Sáng / Tối (Light / Dark Mode)**.
  - Phòng giả lập kiểm thử kịch bản & nhật ký hoạt động thời gian thực (Live Logs).
- 📱 **Truy cập từ xa & Di động (PWA)**:
  - Tự động tạo link Internet công khai (Cloudflare Tunnel HTTPS) & link Wi-Fi LAN.
  - Cài đặt trực tiếp lên màn hình chính điện thoại (iOS / Android) như một ứng dụng native.

---

## 🚀 Hướng dẫn cài đặt & Khởi chạy

### 1. Yêu cầu hệ thống
- Windows 10/11
- Python 3.10+
- Google Chrome hoặc Microsoft Edge

### 2. Cài đặt môi trường
```bash
# Tạo môi trường ảo
python -m venv .venv

# Kích hoạt môi trường (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Cài đặt thư viện
pip install -r requirements.txt
playwright install chromium
```

### 3. Khởi chạy
Chỉ cần nhấp đúp vào file `start.bat` hoặc chạy lệnh:
```bash
python app.py
```
Sau đó mở trình duyệt tại: **http://127.0.0.1:8000**

---

## 📖 Hướng dẫn sử dụng chi tiết

Vui lòng xem file [HUONG_DAN_SU_DUNG.md](HUONG_DAN_SU_DUNG.md) để biết cách cấu hình kịch bản, đặt tên `@Tag`, phân biệt nhóm/cá nhân và mẹo sử dụng hiệu quả.
