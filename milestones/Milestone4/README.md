# Milestone 4 — Console UI & File Transfer

## 1. Mục tiêu

Hoàn thiện giao diện Console và truyền file qua TCP.

- `/send <file>`: Gửi file cho đối tác hiện tại.
- Hiển thị tiến độ truyền theo phần trăm.
- File nhận được lưu trong `downloads/`.
- Vẫn chat được khi đang gửi file.
- Tin nhắn đến không làm mất nội dung đang gõ.
- Không để các Thread in chồng lên Terminal.

**Checkpoint:** Gửi file thành công trong lúc vẫn chat được.

## 2. Phân công nhiệm vụ

### Thành viên A — `cli.py`, `console_ui.py`

Phụ trách Console UI:

- Bổ sung lệnh `/send <file>`.
- Kiểm tra đã chọn đối tác chat trước khi gửi.
- Gọi API File Transfer của C.
- Hiển thị tiến độ và thông báo hoàn thành.
- Xây dựng cơ chế Console Redraw.
- Giữ nội dung đang nhập khi tin nhắn đến.
- Đồng bộ việc hiển thị từ nhiều Thread.
- Cập nhật `/help` và hướng dẫn sử dụng.

API dự kiến:
- `show_notification(message)`
- `show_progress(transfer_id, percent)`
- `refresh_input()`

Thống nhất dùng `prompt_toolkit` cho Console Redraw.
Nếu sử dụng thư viện này, phải bổ sung vào hướng dẫn cài đặt.

### Thành viên B — `tcp_transport.py`, `protocol.py`, `main.py`

Phụ trách hỗ trợ TCP cho File Transfer:

- Giữ ổn định TCP Chat của M3.
- Hỗ trợ kết nối TCP riêng để truyền file.
- Phân biệt kết nối chat với kết nối file.
- Chuyển kết nối nhận file cho module C xử lý.
- Bổ sung định dạng FILE vào Protocol.
- Kiểm tra đồng bộ khi chat và gửi file cùng lúc.
- Tích hợp các API mới vào `main.py`.

B không trực tiếp phụ trách đọc/ghi nội dung file.

### Thành viên C — `file_transfer.py`, `file_receiver.py`

Phụ trách File Transfer.

**`file_transfer.py`:**
- Kiểm tra file nguồn.
- Mở kết nối TCP riêng đến peer.
- Tạo File Sender Thread.
- Gửi thông tin file và dữ liệu theo chunk.
- Tính số byte đã gửi.
- Phát sự kiện tiến độ cho A hiển thị.
- Xử lý mất kết nối khi đang gửi.

**`file_receiver.py`:**
- Nhận metadata của file.
- Nhận đủ số byte dữ liệu.
- Lưu file vào thư mục `downloads/`.
- Tránh ghi đè khi trùng tên.
- Xử lý file tạm `.part`.
- Xóa file tạm nếu truyền lỗi.
- Kiểm tra file nhận được.

API dự kiến:
- `send_file(peer_id, file_path)`
- `receive_file(sock, metadata)`
- `get_download_path(filename)`
- `cleanup_partial_file(path)`

C chịu trách nhiệm kiểm thử File Transfer.

## 3. Quy ước kỹ thuật thống nhất

### File Transfer

- Sử dụng TCP.
- Mỗi lần truyền file sử dụng một kết nối TCP riêng.
- Không truyền file trên socket chat đang hoạt động.
- Mỗi lần gửi file có File Sender Thread.
- TCP Acceptor nhận kết nối mới và chuyển cho File Receiver khi nhận diện được frame FILE.
- File Transfer không được chặn hoạt động chat.

### FILE Protocol

Sử dụng định dạng:

`FILE|<filename>|<size>\n<raw bytes>`

Quy định:
- `filename`: Tên file, không chứa đường dẫn thư mục.
- `size`: Dung lượng file tính bằng byte.
- `raw bytes`: Dữ liệu nhị phân.
- Header dùng UTF-8.
- File được đọc và truyền theo từng chunk.
- Bên nhận phải đọc đủ `size` byte.
- Kết nối file được phân biệt với kết nối chat ngay khi xử lý header.
- Không dùng `recv()` một lần cho toàn bộ file.

### Lưu file

- Thư mục nhận: `downloads/`.
- Ghi dữ liệu vào file tạm `.part`.
- Khi nhận đủ và kiểm tra thành công mới đổi thành tên chính.
- Nếu bị ngắt kết nối, xóa file `.part`.
- Nếu trùng tên, tạo tên mới.
- Không chấp nhận đường dẫn `../` hoặc đường dẫn tuyệt đối từ bên gửi.
- Không tự động thực thi file nhận được.

### Tiến độ truyền

Công thức:

`percent = sent_bytes / total_bytes * 100`

- A hiển thị tiến độ do C gửi qua Queue.
- Không in phần trăm liên tục gây spam Terminal.
- Thông báo rõ hoàn thành hoặc thất bại.
- File rỗng phải được xử lý riêng.
- Kiểm tra file nhận bằng SHA-256 khi kiểm thử.

### Console Redraw

- Sử dụng `prompt_toolkit`.
- Tin nhắn đến được hiển thị phía trên dòng nhập.
- Giữ nguyên phần văn bản chưa nhấn Enter.
- Mọi thông báo bất đồng bộ đi qua UI chung.
- Không cho các module tự ý `print()` vào Terminal khi UI đang quản lý màn hình.
- Đồng bộ tài nguyên giao diện khi cần.

## 4. Kiểm thử

- [ ] Gửi TXT thành công.
- [ ] Gửi PDF hoặc ảnh thành công.
- [ ] Hiển thị tiến độ đến 100%.
- [ ] File nhận giống file gốc theo SHA-256.
- [ ] Chat vẫn hoạt động trong lúc truyền file lớn.
- [ ] File không tồn tại được báo lỗi.
- [ ] File rỗng không làm chương trình crash.
- [ ] Ngắt kết nối giữa chừng, file `.part` được xóa.
- [ ] Trùng tên file không ghi đè bản cũ.
- [ ] Tin đến khi đang gõ không làm mất nội dung.

## 5. Ảnh và báo cáo

- [ ] Ảnh bên gửi và tiến độ truyền.
- [ ] Ảnh bên nhận và thư mục `downloads/`.
- [ ] Ảnh kiểm tra SHA-256 hai file.
- [ ] Ảnh chat trong lúc truyền file.
- [ ] Ảnh Console Redraw khi đang nhập dở.
- [ ] Ảnh xử lý lỗi truyền file.
- [ ] Wireshark thể hiện kết nối TCP chat/file riêng biệt.

**Phải giải thích trong báo cáo:**
- Tại sao truyền file dùng TCP.
- Vì sao cần kết nối file riêng.
- File Sender Thread hoạt động như thế nào.
- Cách lưu file tạm và xử lý lỗi.
- Console Redraw và đồng bộ hiển thị.

**Không ưu tiên ở M4:** Resume, Rate Limiting hoặc tính năng mở rộng khi chức năng chính chưa hoàn tất.
