# Milestone 4 — Console UI & File Transfer

## 1. Mục tiêu

Hoàn thiện giao diện Console và tính năng truyền file qua TCP:

- `/send <file>`: Gửi file cho đối tác chat hiện tại.
- Hiển thị tiến độ truyền theo phần trăm (`%`).
- File nhận được lưu an toàn trong thư mục `downloads/`.
- Vẫn nhắn tin chat bình thường trong lúc đang gửi/nhận file lớn.
- Tin nhắn hoặc thông báo đến không làm mất nội dung đang gõ dở.
- Đồng bộ hiển thị, không để các Thread in chồng chéo lên Terminal.

**Checkpoint:** Gửi và nhận file thành công (khớp mã SHA-256) trong lúc hai peer vẫn chat qua lại bình thường.

---

## 2. Phân công nhiệm vụ

### Thành viên A — `cli.py`, `console_ui.py`

Phụ trách Console UI & trải nghiệm nhập liệu:

- Bổ sung lệnh `/send <file>` (kiểm tra đã chọn đối tác `/chat` trước khi gửi).
- Gọi API File Transfer của C (`send_file(...)`).
- Nhận sự kiện từ `events` Queue để hiển thị tiến độ truyền file theo các mốc phần trăm và thông báo hoàn thành/thất bại.
- Xây dựng cơ chế Console Redraw bằng `prompt_toolkit` (`PromptSession` + `patch_stdout`), giữ nguyên đoạn văn bản người dùng đang gõ dở khi có tin nhắn hoặc tiến độ file mới.
- Điều phối toàn bộ thông báo bất đồng bộ qua hàm hiển thị chung (cấm các thread nền tự ý `print()` trực tiếp).
- Cập nhật `/help`, `requirements.txt` và hướng dẫn cài đặt `prompt_toolkit`.

**API dự kiến:**
- `show_notification(message)`
- `show_progress(transfer_id, filename, percent)`
- `refresh_input()`

---

### Thành viên B — `tcp_transport.py`, `protocol.py`, `main.py`

Phụ trách hạ tầng TCP & định tuyến giao thức cho File Transfer:

- Giữ ổn định toàn bộ luồng TCP Chat của Milestone 3 (`HI`, `MSG`, `BYE`).
- Hỗ trợ kết nối TCP độc lập cho từng phiên truyền file.
- Tại `TCPTransport` Acceptor: chỉ đọc dòng header đầu tiên (`_recv_line`) để phân loại kết nối:
  - Bắt đầu bằng `HI|` → xử lý kết nối chat như M3.
  - Bắt đầu bằng `FILE|` → dùng `protocol.py` tách `metadata` và **bàn giao nguyên `sock` (đang đứng đúng byte đầu tiên của dữ liệu file)** cho module của C xử lý.
- Bổ sung hàm mã hóa/giải mã header `FILE` và gói xác nhận `FILE_OK` vào `protocol.py` (không đọc toàn bộ payload file vào RAM).
- Tích hợp và kết nối các API của A, B, C trong `main.py`.

---

### Thành viên C — `file_transfer.py`, `file_receiver.py`

Phụ trách luồng đọc/ghi và truyền/nhận dữ liệu file:

**`file_transfer.py` (Bên gửi):**
- Kiểm tra file nguồn tồn tại, hợp lệ và lấy dung lượng thực (`size` byte).
- Mở một kết nối TCP riêng tới `(peer_ip, peer_tcp_port)` và chạy trên `File Sender Thread`.
- Gửi header `FILE|<sender_name>|<filename>|<size>\n`, sau đó đọc file và gửi theo từng chunk (ví dụ `8192` byte).
- Tính `sent_bytes` và đẩy sự kiện tiến độ qua `events` Queue cho A hiển thị.
- Sau khi gửi đủ `size` byte, gọi `sock.shutdown(socket.SHUT_WR)` và chờ nhận phản hồi `FILE_OK\n` từ bên nhận trước khi đóng socket để tránh mất dữ liệu cuối.
- Xử lý ngoại lệ khi mất kết nối giữa chừng và báo lỗi lên UI.

**`file_receiver.py` (Bên nhận):**
- Nhận `sock` và `metadata` (`sender_name`, `filename`, `size`) từ B.
- Chuẩn hóa tên file an toàn, tạo đường dẫn trong `downloads/` (tự đổi tên nếu trùng, không ghi đè file cũ).
- Ghi dữ liệu nhận theo chunk (`sock.recv(8192)`) vào file tạm `.part` cho tới khi đủ chính xác `size` byte.
- Đổi tên file `.part` thành tên file chính thức, gửi phản hồi `FILE_OK\n` lại cho bên gửi rồi đóng socket.
- Nếu đứt kết nối hoặc thiếu byte, xóa ngay file `.part` và thông báo lỗi.

**API dự kiến:**
- `send_file(peer_id, sender_name, file_path)`
- `receive_file(sock, metadata)`
- `get_download_path(filename)`
- `cleanup_partial_file(path)`

*(Thành viên C chịu trách nhiệm chính trong việc kiểm thử toàn bộ các tình huống File Transfer).*

---

## 3. Quy ước kỹ thuật thống nhất

### 3.1. Kiến trúc kết nối File Transfer

- Sử dụng giao thức **TCP**.
- Mỗi lần gửi file mở **một kết nối TCP riêng biệt**; tuyệt đối không gửi dữ liệu file chung trên socket chat đang mở (tránh nghẽn tin nhắn chat khi gửi file lớn).
- Mỗi lượt gửi file chạy trên một `File Sender Thread` riêng để không chặn vòng lặp nhập lệnh của CLI.
- `TCP Acceptor` nhận kết nối đến, đọc dòng header đầu tiên để phân biệt ngay giữa kết nối chat (`HI|...`) và kết nối nhận file (`FILE|...`).

### 3.2. Đặc tả giao thức `FILE`

**Header gửi file (từ bên gửi sang bên nhận):**
```text
FILE|<sender_name>|<filename>|<size>\n<raw bytes>
```

**Gói xác nhận hoàn tất (từ bên nhận trả về bên gửi):**
```text
FILE_OK\n
```

**Quy định chi tiết:**
- `sender_name`: Nickname của người gửi (bắt buộc có trong header vì socket truyền file dùng cổng nguồn ngẫu nhiên của hệ điều hành, không trùng với cổng lắng nghe trong `PeerRegistry`).
- `filename`: Chỉ lấy tên file gốc qua `os.path.basename()`, không chứa đường dẫn thư mục hay ký tự phân tách `|`.
- `size`: Dung lượng file tính bằng byte (số nguyên không âm `>= 0`).
- `raw bytes`: Dữ liệu nhị phân thuần của file.
- Phần header mã hóa **UTF-8**, kết thúc bằng `\n`.
- Truyền và nhận theo từng chunk (`8192` byte); không dùng `recv()` một lần cho toàn bộ file.
- Bên nhận đọc vòng lặp cho tới khi gom đủ chính xác `size` byte, lưu xong mới gửi `FILE_OK\n`.

### 3.3. Quy tắc lưu trữ & An toàn dữ liệu

- Thư mục lưu mặc định: `downloads/` (tự động tạo nếu chưa tồn tại).
- Luôn ghi dữ liệu đang tải vào file tạm `<ten_file>.part`. Chỉ đổi tên sang `<ten_file>` khi đã nhận đủ `size` byte.
- Nếu kết nối bị ngắt ngang hoặc gặp lỗi I/O trước khi đủ `size` byte, bắt buộc xóa file `.part`.
- Nếu trong `downloads/` đã có file trùng tên, tự động sinh tên mới theo dạng `ten_file (1).ext`, `ten_file (2).ext`... không ghi đè dữ liệu cũ.
- Từ chối mọi `filename` chứa `..`, `/`, `\` hoặc đường dẫn tuyệt đối (chống lỗi Path Traversal).
- Tuyệt đối không tự động mở hay thực thi file sau khi tải xong.

### 3.4. Tiến độ truyền (`Progress`)

Công thức tính phần trăm:
```text
percent = int(sent_bytes / total_bytes * 100)
```

- Thành viên C đẩy sự kiện tiến độ vào `events` Queue theo các **mốc chẵn** (ví dụ mỗi `25%`: `25% -> 50% -> 75% -> 100%`) để Thành viên A in thành từng dòng thông báo gọn gàng.
- Không dùng ký tự `\r` ghi đè liên tục và không bắn sự kiện theo từng chunk nhỏ gây spam Terminal hoặc xung đột với `prompt_toolkit`.
- **Trường hợp file rỗng (`size == 0`):** Không chia cho `0`; gửi header `FILE|<sender>|<filename>|0\n`, bên nhận tạo file rỗng hợp lệ, trả `FILE_OK\n` và báo hoàn tất `100%`.
- Khi kiểm thử, đối chiếu mã băm **SHA-256** giữa file gốc và file trong `downloads/` để xác nhận toàn vẹn 100%.

### 3.5. Console Redraw

- Sử dụng thư viện `prompt_toolkit` (`PromptSession` kết hợp `patch_stdout(raw=True)`).
- Mọi tin nhắn chat đến, thông báo `online/offline` và tiến độ truyền file đều được in phía trên dòng nhập lệnh hiện tại.
- Giữ nguyên toàn bộ ký tự người dùng đang gõ dở (chưa nhấn `Enter`).
- Mọi luồng nền giao tiếp với giao diện thông qua `events` Queue; không gọi `print()` trực tiếp từ worker thread.

---

## 4. Danh sách kiểm thử (Test Cases)

- [ ] Gửi file văn bản `.txt` thành công, mở đọc bình thường.
- [ ] Gửi file nhị phân (`.pdf`, `.png`/`.jpg` hoặc `.zip` vài MB) thành công.
- [ ] Hiển thị tiến độ truyền theo mốc phần trăm tới `100%` và báo hoàn thành ở cả hai máy.
- [ ] File nhận trong `downloads/` có mã **SHA-256** trùng khớp 100% với file gốc.
- [ ] Nhắn tin chat hai chiều mượt mà trong lúc đang truyền file dung lượng lớn.
- [ ] Nhập đường dẫn file không tồn tại → báo lỗi rõ ràng, không mở kết nối thừa, không crash.
- [ ] Gửi file rỗng (`0 byte`) → bên nhận lưu được file rỗng, không gặp lỗi chia cho 0 (`ZeroDivisionError`).
- [ ] Ngắt kết nối / tắt ngang bên gửi giữa lúc đang truyền → bên nhận tự động xóa file tạm `.part` và báo lỗi.
- [ ] Gửi cùng một file nhiều lần → tự động đánh số `(1)`, `(2)` trong `downloads/`, không ghi đè file cũ.
- [ ] Người dùng đang gõ dở câu trên CLI mà bên kia gửi tin nhắn hoặc tiến độ file tới → chữ đang gõ không bị mất hay vỡ dòng.

---

## 5. Minh chứng ảnh & Nội dung chuẩn bị cho báo cáo

- [ ] Ảnh màn hình bên gửi hiển thị lệnh `/send` và các mốc tiến độ truyền file.
- [ ] Ảnh màn hình bên nhận thông báo nhận file thành công và danh sách file trong thư mục `downloads/`.
- [ ] Ảnh kết quả lệnh kiểm tra mã **SHA-256** (`Get-FileHash` trên Windows / `sha256sum` trên Linux) trùng khớp giữa hai máy.
- [ ] Ảnh thể hiện hai peer vẫn nhắn tin chat trong khi tiến trình truyền file đang chạy.
- [ ] Ảnh minh chứng **Console Redraw**: đang gõ dở nội dung ở dấu nhắc mà có tin nhắn đến phía trên nhưng chữ đang gõ vẫn nguyên vẹn.
- [ ] Ảnh xử lý lỗi (file không tồn tại hoặc ngắt ngang giữa chừng và xóa file `.part`).
- [ ] Ảnh **Wireshark** cho thấy hai luồng TCP độc lập: một luồng TCP cho Chat (`HI`, `MSG`) và một luồng TCP riêng cho File Transfer (`FILE|<sender>|<filename>|<size>`, dữ liệu chunk, `FILE_OK`).

**Các điểm kỹ thuật cần giải thích rõ trong báo cáo PDF:**
1. Tại sao truyền file bắt buộc dùng **TCP** thay vì UDP (đảm bảo tin cậy, đúng thứ tự byte, kiểm soát luồng).
2. Tại sao phải tách **kết nối TCP riêng** cho mỗi lần truyền file thay vì dùng chung socket chat (tránh nghẽn đầu hàng *Head-of-Line blocking* và tách biệt luồng dữ liệu nhị phân).
3. Cách `File Sender Thread` và cơ chế đọc/ghi theo chunk + xác nhận `FILE_OK\n` hoạt động để không tốn RAM và không mất byte cuối.
4. Cơ chế file tạm `.part`, dọn dẹp khi lỗi và phòng chống Path Traversal (`../`).
5. Cách `prompt_toolkit` (`patch_stdout`) và `events` Queue giải quyết triệt để vấn đề đồng bộ hiển thị đa luồng trên Console.

**Phạm vi không ưu tiên ở M4:** Chưa triển khai tạm dừng/tiếp tục tải (Resume), giới hạn băng thông (Rate Limiting) hoặc giao diện đồ họa (GUI) khi chưa hoàn tất ổn định toàn bộ các chức năng cốt lõi trên.
