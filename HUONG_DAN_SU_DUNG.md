# 📘 HƯỚNG DẪN SỬ DỤNG ZALO AUTO-REPLY STUDIO

Ứng dụng giúp bạn tự động trả lời tin nhắn Zalo cá nhân theo kịch bản riêng cho **từng Người**, **từng Nhóm**, và tự động nhận diện khi bạn được nhắc tên **`@Tag`** trong nhóm.

---

## 1. Cách khởi động ứng dụng

### Khi dùng hàng ngày trên máy tính:
- Nhấp đúp vào file **`start.bat`** trong thư mục [`zalo-auto-reply`](file:///C:/Users/artelia-L098/.gemini/antigravity/scratch/zalo-auto-reply/start.bat).
- Trình duyệt sẽ tự động mở trang quản lý tại địa chỉ: **http://127.0.0.1:8000**

### Khi muốn điều khiển từ Điện thoại hoặc Thiết bị khác:
1. Trên giao diện máy tính, bấm nút màu vàng **"📱 Mở trên Điện thoại / Thiết bị khác"** ở thanh trên cùng.
2. Mở Camera điện thoại quét **Mã QR bên trái (Link Internet Mọi Nơi - dùng được cả 4G/5G)** hoặc **Mã QR bên phải (Cùng mạng Wi-Fi)**.
3. **Cài thành App trên màn hình điện thoại:**
   - **iPhone (Safari):** Bấm nút **Chia sẻ (Share)** ➔ Chọn **"Thêm vào Màn hình chính"**.
   - **Android (Chrome):** Bấm biểu tượng **3 chấm (`⋮`)** ➔ Chọn **"Cài đặt ứng dụng"** hoặc **"Thêm vào Màn hình chính"**.

---

## 2. Kết nối tài khoản Zalo (Chỉ cần quét QR 1 lần đầu)

1. Trên thanh công cụ đầu trang, bấm nút **"Mở Zalo Web (Chrome)"**.
2. Ngay bên dưới thanh tiêu đề sẽ hiện ra khung **"📲 Quét Mã QR Zalo Trực Tiếp Tại Đây"** (đồng thời một cửa sổ Chrome tự động hóa cũng được mở lên).
3. Mở ứng dụng **Zalo trên điện thoại** ➔ Bấm biểu tượng quét mã QR ➔ Quét mã QR trên màn hình và bấm **Đăng nhập**.
   - *Lưu ý:* Nếu mã QR bị hết hạn, bấm nút màu xanh **"🔄 Lấy mã QR mới / Tải lại trang"**.
4. Sau khi đăng nhập xong, trạng thái sẽ báo **"Zalo Web: Đã đăng nhập"** và phiên đăng nhập được lưu tự động vào thư mục `data/chrome_profile` (những lần mở sau không cần quét lại QR).

> ⚠️ **Quan trọng:** Khi bot đang chạy, hãy **giữ nguyên cửa sổ Chrome Zalo Web mở** (có thể thu nhỏ xuống thanh Taskbar, nhưng **đừng tắt nút X** của cửa sổ Chrome đó).

---

## 3. Thiết lập tên `@Tag` của bạn & Độ trễ (Tab số 3)

Vào tab **"3. Cấu hình @Tag & Độ trễ"**:

1. **Danh sách tên `@Tag` của bạn trong Nhóm:**
   - Nhập đúng tên hiển thị Zalo của bạn (có dấu `@` phía trước), cách nhau bằng dấu phẩy.
   - *Ví dụ:* `@Nguyễn Văn A, @Minh, @All`
   - Ngoài việc kiểm tra tên trong ô này, hệ thống cũng tự động phát hiện thẻ highlight `@mention` màu xanh trên giao diện Zalo Web.
2. **Quy tắc trả lời trong Nhóm & Tin nhắn riêng (1-1):**
   - **Trong Nhóm: Chỉ trả lời khi được tag @** *(Nên bật)*: Giúp bot không trả lời lung tung vào cuộc nói chuyện của người khác trong nhóm, chỉ khi ai đó gõ `@Tên_bạn` thì bot mới phản hồi.
   - **Tin nhắn riêng (1-1): Bắt buộc có tag @** *(Nên tắt)*: Để khi khách hàng, đồng nghiệp hoặc sếp nhắn riêng 1-1 cho bạn, bot tự động khớp từ khóa kịch bản và trả lời mà không cần họ phải tag `@`.
3. **Độ trễ ngẫu nhiên & Chống lặp:**
   - **Độ trễ tối thiểu / tối đa (VD: `2s` đến `5.5s`):** Trước khi trả lời, bot sẽ đợi ngẫu nhiên vài giây và gõ từng ký tự như người thật đang gõ phím.
   - **Thời gian nghỉ chống lặp (VD: `15s`):** Trong vòng 15 giây sau khi đã trả lời một cuộc trò chuyện, bot sẽ tạm nghỉ ở hội thoại đó để tránh spam liên tục.
4. Bấm **"Lưu Cấu hình Chung"**.

---

## 4. Tạo & Quản lý Kịch bản Trả lời (Tab số 1)

Vào tab **"1. Kịch bản trả lời (Scenarios)"** ➔ Bấm nút **"+ Thêm Kịch bản mới"**:

- **Tên kịch bản:** Đặt tên dễ nhớ (VD: *Kịch bản trả lời Sếp Tuấn*, *Báo giá khách hàng*, *Nhóm Dự Án A*...).
- **Độ ưu tiên (Priority):** Số càng lớn càng được kiểm tra trước (VD: Kịch bản riêng cho Sếp đặt `100`, kịch bản theo từ khóa chung đặt `80`, kịch bản trả lời mặc định khi được tag trong nhóm đặt `10`).
- **Phạm vi áp dụng:**
  - `Chỉ Nhóm hoặc Người cụ thể (Theo tên)`: Nhập chính xác tên Nhóm hoặc tên Người trên Zalo vào ô **Tên Nhóm hoặc Tên Người áp dụng** (VD: `Nhóm Dự Án Công Ty, Sếp Tuấn`).
  - `Tất cả các Nhóm`: Áp dụng cho mọi nhóm Zalo.
  - `Tất cả Tin nhắn riêng 1-1`: Chỉ áp dụng cho chat cá nhân 1-1.
  - `Tất cả (Mọi Nhóm & Tin nhắn riêng)`: Áp dụng chung.
- **Điều kiện được Tag `@Tên_bạn`:**
  - `Theo mặc định`: Nhóm thì cần `@Tag`, 1-1 thì không cần.
  - `Luôn bắt buộc phải có @Tag tên tôi`: Dù ở đâu cũng phải có `@Tag` mới trả lời.
  - `Không cần @Tag`: Cứ khớp từ khóa là trả lời ngay cả trong nhóm.
- **Kiểu khớp nội dung & Từ khóa:**
  - `Chứa một trong các từ khóa`: Chỉ cần tin nhắn có chứa từ khóa (VD: `báo giá, chi phí, tiến độ, hỗ trợ`).
  - `Khớp chính xác từ khóa`: Nội dung tin nhắn trùng khớp hoàn toàn với từ khóa.
  - `Mọi nội dung tin nhắn (Mặc định)`: Khớp tất cả tin nhắn (thường dùng làm câu trả lời mặc định khi có người tag `@` bạn trong nhóm mà không chứa từ khóa đặc biệt nào).
- **Nội dung tin nhắn trả lời tự động:**
  - Nếu bạn nhập **nhiều dòng**, mỗi lần trả lời bot sẽ **chọn ngẫu nhiên 1 dòng** để câu chữ tự nhiên, không bị máy móc.
  - Hỗ trợ chèn các biến tự động:
    - `{sender}`: Tên người vừa nhắn / tag bạn.
    - `{chat_name}`: Tên nhóm hoặc tên cuộc trò chuyện.
    - `{time}`: Giờ hiện tại (VD: `14:30`).
    - `{date}`: Ngày hiện tại (VD: `13/11/2026`).
    - `{message}`: Nội dung tin nhắn gốc của người gửi.

---

## 5. Bật / Tắt riêng từng Nhóm hoặc từng Người (Tab số 2)

Vào tab **"2. Bật/Tắt Từng Người & Từng Nhóm"**:
- Nếu có những nhóm bạn **tuyệt đối không muốn bot tự động trả lời** (ví dụ: *Nhóm Gia Đình*, *Nhóm Bạn Cấp 3*), hãy nhập tên nhóm đó, chọn trạng thái **"Chặn / Không tự động trả lời (Tắt)"** rồi bấm **Lưu**.
- Bạn cũng có thể bấm nút **"Đổi Bật/Tắt"** nhanh cho từng nhóm/người bất cứ lúc nào.

---

## 6. Kiểm thử Kịch bản & Xem Nhật ký (Tab số 4)

Trước khi cho bot chạy thật, hãy vào tab **"4. Giả lập Kiểm thử & Nhật ký (Logs)"**:
1. Ở khung **Phòng Giả lập & Kiểm thử Kịch bản** bên trái:
   - Nhập thử tên nhóm/người, tên người gửi, chọn loại hội thoại (`Nhóm` hoặc `Tin nhắn riêng 1-1`), tích chọn có `@Tag` hay không, và nhập câu tin nhắn thử nghiệm.
   - Bấm **"Chạy Kiểm thử Kịch bản"** ➔ Hệ thống sẽ báo ngay kịch bản nào được kích hoạt và câu trả lời thực tế sẽ gửi đi là gì.
2. Khi mọi thứ đã ưng ý, bấm nút màu xanh lá **"ĐANG BẬT TỰ ĐỘNG TRẢ LỜI"** trên thanh công cụ đầu trang để bot bắt đầu làm việc tự động!
