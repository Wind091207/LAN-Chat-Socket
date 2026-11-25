# 🧪 Demo & Kiểm thử Hệ thống (3 Peers — Windows & Ubuntu)

<div align="center">
  <p><strong>📊 Tài liệu kiểm thử thực nghiệm đa nền tảng (Windows & Ubuntu Linux) và phân tích gói tin giao thức qua Wireshark</strong></p>
</div>

## 🖥️ Môi trường & Cấu hình Triển khai

Quá trình kiểm thử được thực hiện đồng thời trên **3 peer** chạy trên 2 hệ điều hành khác nhau (2 tiến trình trên máy chủ Windows và 1 tiến trình trên máy ảo Ubuntu Linux qua card mạng VirtualBox Host-Only):

| Peer | Hệ điều hành | Địa chỉ IP | TCP Port | UDP Discovery | Vai trò kiểm thử |
|---|---|---|:---:|:---:|---|
| **Quan** | Windows 10/11 | `192.168.56.1` | `5000` | `9999` | Chủ động kết nối, gửi chat & truyền file lớn |
| **Minh** | Windows 10/11 | `192.168.56.1` | `6000` | `9999` | Kiểm thử đa kết nối (`+unread`) & kịch bản offline |
| **Huy** | Ubuntu Linux (VM) | `192.168.56.104` | `5000` | `9999` | Kiểm thử cross-platform, nhận file & ngắt mạng |

### Chuẩn bị & Khởi chạy

1. **Tạo sẵn 2 tệp dữ liệu kiểm thử trên Windows (`D:\`):**
   - `D:\demo_50mb.zip` (`52,428,800` bytes) — kiểm thử truyền file song song với chat.
   - `D:\demo_200mb.zip` (`223,428,800` bytes) — kiểm thử tải nặng và kịch bản ngắt mạng giữa chừng.
2. **Kích hoạt `.venv` trên Ubuntu (tránh xung đột PEP 668) và khởi chạy cả 3 peer từ thư mục gốc repository:**

   ```bash
   # Windows Terminal 1 (Quan)
   python src/main.py --name Quan --tcp-port 5000 --bcast 192.168.56.255

   # Windows Terminal 2 (Minh)
   python src/main.py --name Minh --tcp-port 6000 --bcast 192.168.56.255

   # Ubuntu Terminal (Huy - đã kích hoạt .venv)
   source .venv/bin/activate
   python3 src/main.py --name Huy --tcp-port 5000 --bcast 192.168.56.255
   ```

---

## 📡 Giai đoạn 1: Khám phá LAN & Đồng bộ Trạng thái (UDP 9999)

### 1.1. Tự động phát hiện 3 Peer trong mạng LAN

Ngay sau khi khởi chạy, cả 3 peer tự động phát quảng bá gói tin `HELLO` mỗi **3 giây** qua cổng UDP `9999` và hiển thị đầy đủ danh sách trên thanh sidebar:

![Cả 3 peer cùng tham gia mạng LAN](Assets/Pasted%20image%2020261125164010.png)

### 1.2. Đối chiếu đồng bộ trạng thái `/status away`

Trên terminal của **Huy (Ubuntu)**, nhập lệnh `/status away`. Trạng thái của Huy lập tức chuyển sang `AWAY` màu vàng và được đồng bộ sang giao diện của **Quan (Windows)** ở chu kỳ quảng bá tiếp theo:

| Máy thực hiện — Huy (`/status away`) | Máy quan sát — Quan (Cập nhật tức thì) |
| :---: | :---: |
| ![Huy chuyển trạng thái sang AWAY](Assets/Pasted%20image%2020261125164126.png) | ![Quan thấy Huy chuyển sang AWAY màu vàng](Assets/Pasted%20image%2020261125164139.png) |

### 1.3. Phân tích gói tin UDP trên Wireshark (`udp.port == 9999`)

![Wireshark bắt gói tin UDP HELLO trạng thái away](Assets/Pasted%20image%2020261125164353.png)

- **Giải thích gói tin (Frame `633`):** Máy Ubuntu (`192.168.56.104`) gửi gói UDP broadcast tới `192.168.56.255:9999` với phần dữ liệu (`Data: 19 bytes`) là chuỗi ASCII **`HELLO|Huy|5000|away`**, khớp hoàn toàn với đặc tả giao thức discovery.

---

## 💬 Giai đoạn 2: Kết nối TCP & Chat Thời gian thực (UTF-8 Framing)

### 2.1. Bắt tay 3 bước thiết lập phiên chat (`SYN` $\rightarrow$ `SYN, ACK` $\rightarrow$ `ACK`)

Khi **Quan** gõ `/chat Huy`, tầng giao vận chủ động mở kết nối TCP trực tiếp từ cổng nguồn tạm `49806` tới cổng lắng nghe `5000` của Huy:

![Wireshark bắt tay 3 bước TCP](Assets/Pasted%20image%2020261125164924.png)

- **Frames `793` – `795`:** Thể hiện trọn vẹn quy trình bắt tay 3 bước TCP (`[SYN] Seq=0` $\rightarrow$ `[SYN, ACK] Seq=0 Ack=1` $\rightarrow$ `[ACK] Seq=1 Ack=1`) trước khi trao đổi dữ liệu tầng ứng dụng.

### 2.2. Đối chiếu giao diện chống đè dòng nhập & Luồng TCP Stream (`tcp.stream eq 0`)

Khi **Huy** đang gõ dở câu `Minh dang go do cau nay chua bam EntSS` ở thanh nhập liệu dưới cùng thì tin nhắn tiếng Việt có dấu từ **Quan** (`Chào Huy, sẵn sàng demo chưa ?`) gửi tới. Nhờ tách luồng I/O bằng `prompt_toolkit`, nội dung Huy đang gõ không bị cắt ngang hay vỡ giao diện:

| Giao diện TUI trên máy Huy (Không đè dòng nhập) | Wireshark — `Follow TCP Stream (tcp.stream eq 0)` |
| :---: | :---: |
| ![Huy nhận tin nhắn khi đang gõ dở câu](Assets/Pasted%20image%2020261125164858.png) | ![Follow TCP Stream luồng chat](Assets/Pasted%20image%2020261125165152.png) |

- **Giải thích luồng dữ liệu (`tcp.stream eq 0`):**
  1. Hai bên trao đổi gói định danh `HI|Quan|5000` và `HI|Huy|5000`.
  2. Tin nhắn tiếng Việt của Quan được đóng khung bằng header `MSG|35` (đúng **35 byte** UTF-8 của chuỗi `Chào Huy, sẵn sàng demo chưa ?`).
  3. Sau khi Huy nhấn Enter, chuỗi `Minh dang go do cau nay chua bam EntSS` được gửi đi với header `MSG|38` (**38 byte**), đảm bảo tách bạch ranh giới bản tin trên luồng byte TCP.

---

## 📁 Giai đoạn 3: Truyền File Song song với Chat (Dedicated TCP Stream)

### 3.1. Đối chiếu truyền `demo_50mb.zip` xen kẽ tin nhắn chat

Trong lúc **Quan** gửi tệp `demo_50mb.zip` (`52,428,800` bytes) sang **Huy**, Quan tiếp tục nhắn tin `chat en`. Do truyền file chạy trên **một kết nối TCP riêng và luồng nền độc lập**, tiến trình truyền đạt `100%` mượt mà và không làm nghẽn luồng chat:

| Bên gửi — Quan (Tiến độ 25%–100% xen lẫn chat) | Bên nhận — Huy (Nhận đủ chat & lưu `downloads/`) |
| :---: | :---: |
| ![Quan gửi file 50MB song song chat](Assets/Pasted%20image%2020261125171749.png) | ![Huy nhận đủ tin nhắn và file 50MB](Assets/Pasted%20image%2020261125171816.png) |

### 3.2. Phân tích gói tin truyền file trên Wireshark (`tcp.stream == 2`)

Lọc gói tin với điều kiện `tcp.stream == 2 && (tcp.flags.syn == 1 || tcp.flags.fin == 1 || tcp contains "FILE")` cho thấy toàn bộ vòng đời kết nối truyền file tách biệt hoàn toàn với luồng chat (`stream 0`):

| Mở kết nối, Header `FILE\|` & Kết thúc dữ liệu | Gói phản hồi xác nhận `FILE_OK` từ bên nhận |
| :---: | :---: |
| ![Wireshark header FILE và cờ FIN](Assets/Pasted%20image%2020261125171536.png) | ![Wireshark gói xác nhận FILE_OK](Assets/Pasted%20image%2020261125171715.png) |

- **Frames `92509` – `92510`:** Mở kết nối TCP thứ hai trên cổng nguồn mới (`49954` $\rightarrow$ `5000`).
- **Frame `92512` (`Len=33`):** Bên gửi truyền header `FILE|Quan|demo_50mb.zip|52428800\n` (dài đúng 33 bytes).
- **Frame `118057`:** Bên gửi phát cờ `[FIN, ACK]` tại `Seq=52428834` ($= 1 + 33\text{ bytes header} + 52,428,800\text{ bytes dữ liệu}$), chứng minh toàn bộ 50 MB dữ liệu tệp đã được đẩy đi trọn vẹn.
- **Frames `118059` – `118060`:** Sau khi ghi xong file vào `downloads/`, máy Huy phản hồi gói `FILE_OK\n` (`Len=8` bytes, mã hex `46 49 4c 45 5f 4f 4b 0a`) và đóng hoàn toàn kết nối truyền file.

---

## 🔔 Giai đoạn 4: Kịch bản Nhiều Peer & Quản lý Tin chưa đọc (`unread`)

Giữ nguyên **Huy** đang trò chuyện trong phòng của **Quan**, đồng thời từ cửa sổ **Minh**, gõ `/chat Huy` và gửi liên tiếp 2 tin nhắn (`Huy ơi xem giùm mình phần báo cáo` và `alo`):

| Huy đang chat với Quan — Minh nhắn tới (`+2`) | Huy chuyển sang phòng Minh — Xóa badge `+2` |
| :---: | :---: |
| ![Huy nhận thông báo +2 unread từ Minh](Assets/Pasted%20image%2020261125172057.png) | ![Huy mở phòng Minh và đọc tin nhắn](Assets/Pasted%20image%2020261125172233.png) |

- **Kết quả đối chiếu:**
  - Khi đang tập trung ở phòng **Quan**, tin nhắn từ **Minh** không làm nhảy nội dung màn hình chính mà cập nhật badge **`+2`** màu xanh trên thanh sidebar.
  - Khi chuyển sang phòng **Minh**, bộ đếm `+2` được đặt lại về `0`, toàn bộ tin nhắn được hiển thị đầy đủ, đồng thời kết nối TCP với **Quan** vẫn duy trì trạng thái `(Joined)` để chuyển đổi qua lại tức thì.

---

## 🛡️ Giai đoạn 5: Rời phòng (`/leave`) & 5 Tình huống Xử lý Lỗi

### 5.0. Rời phiên trò chuyện êm đẹp (`/leave`)

Khi **Huy** gõ `/leave` trong phiên chat với **Minh**, ứng dụng gửi khung điều khiển `BYE\n` và thực hiện đóng kết nối TCP chuẩn 4 bước:

| Giao diện TUI bên Minh (Khóa sang `Read-Only`) | Wireshark — Khung `BYE` & Cờ `[FIN, ACK]` (`stream 3`) |
| :---: | :---: |
| ![Minh nhận thông báo Huy rời phòng](Assets/Pasted%20image%2020261125172809.png) | ![Wireshark gói BYE và FIN ACK](Assets/Pasted%20image%2020261125172713.png) |

- **Frame `118897` (`Len=4`):** Gửi chuỗi `BYE\n` (`42 59 45 0a`), theo sau ngay bởi các gói `[FIN, ACK]` (`Frames 118898–118900`), đưa phòng chat trên máy Minh về chế độ `[READ-ONLY]`.

---

### 5.1. Lỗi 1 — Kết nối tới Peer vừa Offline (`< 10s` trước khi hết hạn UDP)

Tắt hẳn ứng dụng của **Minh** bằng `/quit`. Trong khoảng thời gian dưới **10 giây** (trước khi cơ chế timeout UDP xóa Minh khỏi danh sách), **Huy** thực hiện lệnh `/chat Minh`:

![Xử lý lỗi kết nối tới peer vừa offline](Assets/Pasted%20image%2020261125173035.png)

- **Kết quả:** Hệ thống bắt ngoại lệ kết nối, hiển thị thông báo đỏ `[Error] Failed to connect to Minh: timed out`, sau đó tự động dọn dẹp trạng thái `[System] Minh went offline.` mà không làm treo chương trình.

---

### 5.2. Lỗi 2 — Peer Crash đột ngột giữa lúc đang chat

Trong lúc **Huy** và **Quan** đang mở phiên chat, đóng ngang cửa sổ terminal của **Quan** trên Windows bằng nút **`X`** (không gửi `BYE`):

| Giao diện TUI bên Huy (Phát hiện mất kết nối) | Wireshark — Gói `[RST, ACK]` đột ngột |
| :---: | :---: |
| ![Huy phát hiện Quan ngắt kết nối đột ngột](Assets/Pasted%20image%2020261125173252.png) | ![Wireshark bắt gói RST ACK khi crash](Assets/Pasted%20image%2020261125173327.png) |

- **Đối chiếu kỹ thuật:** Khác với cờ `[FIN, ACK]` khi dùng `/leave`, việc tắt ngang tiến trình khiến hệ điều hành Windows phát gói **`[RST, ACK]`** (`Frame 119332`, `49806 -> 5000`). Socket phía Huy lập tức nhận diện EOF/Reset, báo `[Read-Only] Quan disconnected unexpectedly (connection lost).` và khóa khung nhập an toàn.

---

### 5.3. Lỗi 3 — Mất kết nối mạng giữa lúc đang truyền file

Khởi động lại **Quan**, thực hiện gửi tệp nặng `D:\demo_200mb.zip` sang **Huy**. Khi tiến độ đạt **75%**, ngắt kết nối card mạng ảo (`Connect Network Adapter 2`) của máy ảo Ubuntu:

| Bên gửi — Quan (Treo tiến độ & báo `timed out`) | Bên nhận — Huy (Báo `timed out` & dọn file `.part`) |
| :---: | :---: |
| ![Quan báo lỗi timeout khi gửi file 200MB](Assets/Pasted%20image%2020261125174629.png) | ![Huy báo lỗi timeout khi nhận file 200MB](Assets/Pasted%20image%2020261125174426.png) |

- **Kết quả:** Cả hai đầu đều phát hiện đứt luồng truyền qua cơ chế socket timeout (`[Error] File transfer (demo_200mb.zip): timed out`), đồng thời phía nhận tự động xóa bỏ tệp tạm chưa hoàn chỉnh (`demo_200mb.zip.part`) trong thư mục `downloads/`.

---

### 5.4. Lỗi 4 — Gói tin sai định dạng (Malformed Packet)

Từ một cửa sổ PowerShell độc lập trên Windows, mở kết nối TCP thô tới cổng `5000` của **Huy** và bơm trực tiếp chuỗi rác `b'abc\n'` không tuân thủ header `HI|` hay `FILE|`:

![Bắn gói tin rác vào cổng TCP của Huy](Assets/Pasted%20image%2020261125174938.png)

- **Kết quả:** Server của Huy phát hiện khung bản tin không hợp lệ, chủ động đóng kết nối ngay lập tức (khiến phía client nhận về `Server reply: b''`) trong khi ứng dụng của Huy vẫn tiếp tục hoạt động bình thường.

---

### 5.5. Lỗi 5 — Nhập sai cú pháp lệnh & Gửi file không tồn tại

Kiểm thử các thao tác nhập sai từ người dùng: gõ sai tên lệnh (`/chta`), thử gửi file khi phòng đang ở trạng thái `Read-Only`, và gửi đường dẫn tệp không tồn tại (`/send khongco.pdf`):

![Xử lý lỗi sai lệnh và file không tồn tại](Assets/Pasted%20image%2020261125175114.png)

- **Kết quả:** Toàn bộ các thao tác sai đều được kiểm tra hợp lệ ở tầng giao diện/tầng truyền tải và trả về cảnh báo rõ ràng (`Unknown command...`, `This room is Read-Only...`, `[Errno 2] No such file or directory: 'khongco.pdf'`) mà không phát sinh ngoại lệ chưa xử lý.