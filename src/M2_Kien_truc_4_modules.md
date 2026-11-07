# Milestone 2 — Giải thích toàn bộ chương trình (4 file Python)

> **Một ứng dụng, bốn file:** `main.py` khởi tạo và điều phối → `udp_discovery.py` (A) giao tiếp UDP → `peer_registry.py` (C) quản lý peer → `cli.py` (B) nhận lệnh, hiển thị.
>
> **Mỗi máy chạy một bản ứng dụng riêng.** Mỗi bản có Registry và Queue của chính nó; các máy trao đổi với nhau bằng UDP HELLO, **không dùng chung Queue qua mạng**.

## 1. Mỗi file làm gì, lưu cái gì?

| File | Nhiệm vụ | Dữ liệu/đối tượng quan trọng |
|---|---|---|
| **`main.py`** | Điểm vào: đọc tham số, kết nối A/B/C, khởi động và dọn dẹp | `args` (name, tcp_port, bcast), **một `events = Queue()`**, **một `registry`**, **một `discovery`** |
| **`udp_discovery.py` (A)** | Gửi HELLO mỗi 3 giây, nhận HELLO từ mạng, chuyển cho C | `name`, `tcp_port`, `status`, `bcast_addr`, `port=9999`, UDP socket `sock`, tham chiếu đến `registry`, hai Thread gửi/nhận |
| **`peer_registry.py` (C)** | Giữ danh sách peer; ghi nhận hoạt động, kiểm tra timeout và tạo sự kiện | `_peers`: dictionary khóa `(ip, tcp_port)`; mỗi peer có `name`, `ip`, `tcp_port`, `status`, `last_seen`. Có `_lock`, `events` Queue, Thread kiểm tra timeout |
| **`cli.py` (B)** | Nhận lệnh từ bàn phím và in kết quả/thông báo | `HELP`, vòng lặp `input("> ")`, Event Thread; **không sở hữu danh bạ riêng**, dùng `registry` và `events` do `main.py` truyền vào |

**Cần phân biệt hai chỗ lưu dữ liệu trong C:**

- **Registry (`_peers`)** = **ai đang được phát hiện**. Ví dụ: Minh, IP `192.168.1.20`, TCP port `5002`, status `online`, thời điểm HELLO cuối `last_seen`.
- **Queue (`events`)** = **chuyện gì vừa thay đổi, đang chờ B thông báo**. Mỗi phần tử là một cặp `(loại_sự_kiện, thông_tin_peer)`, gồm `online`, `status_changed`, `offline`.
- B gọi `events.get(...)` thì **chỉ lấy sự kiện khỏi Queue**, không xóa Minh khỏi Registry. B nhập `/list` thì đọc Registry, **không đọc Queue**.
- M2 chỉ lưu trong **RAM**, chưa lưu danh bạ ra file.

## 2. Vòng đời chương trình: từ mở đến tắt

Ví dụ mở trên máy Quan:

```powershell
python main.py --name Quan --tcp-port 5001
```

**Bước 1 — `main.py` nhận tham số.** `argparse` đọc `--name`, `--tcp-port`, `--bcast` (mặc định `255.255.255.255`). Hàm `tcp_port()` kiểm tra port là số nguyên từ `1` đến `65535`; `main()` kiểm tra tên hợp lệ.

**Bước 2 — Tạo và nối ba module.**

```python
events = Queue()                                  # Hàng đợi chung C → B
registry = PeerRegistry(events=events, timeout_seconds=10.0)  # C
discovery = UDPDiscovery(                       # A
    name=args.name, tcp_port=args.tcp_port,
    registry=registry, bcast_addr=args.bcast, port=9999
)
```

Quan trọng: A nhận **chính đối tượng `registry` đã tạo**, không tạo danh sách khác. B cũng nhận **đúng `registry`, `discovery` và `events` đó**.

**Bước 3 — Khởi động các công việc nền.**

```python
registry.start_timeout_monitor()  # C bật Thread kiểm tra peer hết hạn
discovery.start()                  # A mở UDP socket và bật 2 Thread
run_cli(registry, discovery, events)  # B chạy CLI trong Main Thread
```

**Bước 4 — Ứng dụng hoạt động.** Main Thread chờ người dùng nhập lệnh; các Thread nền vẫn gửi/nhận UDP, kiểm tra timeout và in sự kiện.

**Bước 5 — Người dùng nhập `/quit`.** `run_cli()` thoát, yêu cầu Event Thread dừng. Quyền điều khiển trở về `main.py`, khối `finally` gọi `discovery.stop()` và `registry.stop_timeout_monitor()`, đóng socket và kết thúc ứng dụng.

## 3. Có những Thread nào đang chạy?

Sau khi `run_cli()` khởi động, thông thường có **5 Thread** trong mỗi bản ứng dụng:

| Thread | Hàm chạy | Việc thực hiện |
|---|---|---|
| **1. Main Thread — B** | `run_cli()` | Đứng ở `input("> ")`, xử lý lệnh người dùng |
| **2. UDP Send Thread — A** | `_send_loop()` | Mỗi khoảng **3 giây** gửi `HELLO|name|tcp_port|status` bằng `sendto()` |
| **3. UDP Receive Thread — A** | `_recv_loop()` | Chờ `recvfrom()`, phân tích HELLO, gọi C: `registry.update_peer(...)` |
| **4. Timeout Monitor Thread — C** | `_monitor_loop()` | Định kỳ kiểm tra: **quá 10 giây** kể từ `last_seen` thì xóa peer, tạo sự kiện `offline` |
| **5. Event Thread — B** | `_show_events()` | Đợi `events.get(timeout=0.2)`, rồi in peer `online` / `away` / `offline` |

**Không phải 5 chương trình.** Đây là 5 luồng công việc trong **một tiến trình** trên **một máy**. `main.py` không cần thêm Thread riêng ngoài Main Thread.

- **`Lock` của C:** bảo vệ dictionary `_peers` khi Receive Thread cập nhật và Timeout Thread xóa/đọc dữ liệu.
- **`Lock` của A:** bảo vệ việc đọc/đổi `self.status` giữa Send Thread và lệnh `/status`.
- **`Queue`:** chuyển sự kiện từ C sang Event Thread của B một cách an toàn.
- **Giới hạn hiện tại:** Event Thread có thể in chen vào dòng người dùng đang gõ. Console redraw hoàn chỉnh xử lý ở M4.

## 4. Khi có một máy Minh xuất hiện: A → C → B

Giả sử máy Minh đang chạy và phát `HELLO|Minh|5002|online`:

```text
MÁY MINH: A._send_loop() — gửi HELLO qua UDP port 9999
                 ↓ mạng LAN
MÁY QUAN: A._recv_loop() — nhận HELLO và tách name/port/status/IP
                 ↓ gọi registry.update_peer(...)
MÁY QUAN: C — thêm/cập nhật Minh trong _peers; ghi last_seen
                 ↓ nếu là peer mới: events.put_nowait(("online", peer))
MÁY QUAN: B._show_events() — events.get(...) → in "Minh is online"
```

**HELLO không đồng nghĩa với một thông báo `online` mới mỗi lần.** Minh gửi lại HELLO cùng status sau 3 giây → C cập nhật `last_seen` nhưng **không thêm sự kiện `online` lần nữa**. Nếu Minh đổi từ `online` sang `away` → C tạo `status_changed`.

**Nếu Minh tắt máy:** không còn HELLO; sau **hơn 10 giây từ HELLO cuối**, C xóa Minh khi Thread monitor kiểm tra và đưa `("offline", peer)` vào Queue. B lấy ra rồi in thông báo. Timeout `recvfrom()` **1 giây** ở A chỉ để hàm nhận không chờ vô hạn, **không phải** timeout offline 10 giây.

## 5. Các lệnh CLI: nhập gì, gọi ai?

| Lệnh | `cli.py` làm gì? | Liên quan đến file nào? |
|---|---|---|
| `/list` | Gọi `registry.get_peers()` rồi in tên, IP, TCP port, status | **C** (đọc Registry) |
| `/status online` | Gọi `discovery.set_status("online")` | **A** (HELLO tiếp theo mang status mới) |
| `/status away` | Gọi `discovery.set_status("away")` | **A** (HELLO tiếp theo mang status mới) |
| `/help` | In biến `HELP` chứa hướng dẫn | **B** |
| `/quit` | Thoát CLI, để `main.py` dừng các Thread/module | **B → main** |

**Ví dụ:** Quan nhập `/status away` → B gọi A đổi `self.status` → Send Thread của A gửi HELLO có `away` ở lượt tiếp theo → **máy khác** nhận HELLO, C của máy đó cập nhật Quan và Event Thread B của máy đó in `Quan is now away`.

**Lưu ý:** `--tcp-port 5001` trong M2 **chỉ quảng bá số port trong HELLO**, **chưa mở TCP socket để chat**; chức năng TCP thuộc M3.

## 6. Các hàm phải nhận ra khi cô chỉ vào code

| Hàm | Giải thích một câu |
|---|---|
| `main()` | Tạo Queue, Registry, Discovery; khởi động, chạy CLI, dọn dẹp |
| `tcp_port()` | Kiểm tra tham số TCP port từ Terminal |
| `UDPDiscovery.start()` / `stop()` | Mở UDP và tạo hai Thread / yêu cầu dừng và đóng socket |
| `UDPDiscovery._send_loop()` | Định kỳ phát HELLO |
| `UDPDiscovery._recv_loop()` | Nhận HELLO và gọi Registry cập nhật |
| `UDPDiscovery.set_status()` | Đổi status của máy mình cho lần gửi HELLO tiếp theo |
| `PeerRegistry.update_peer()` | Thêm/cập nhật peer, `last_seen`, tạo sự kiện khi có thay đổi |
| `PeerRegistry.get_peers()` | Trả về danh sách peer hiện tại cho `/list` |
| `PeerRegistry.remove_expired_peers()` | Xóa các peer quá timeout và tạo sự kiện offline |
| `PeerRegistry.start_timeout_monitor()` / `stop_timeout_monitor()` | Bật / dừng Thread kiểm tra timeout |
| `run_cli()` | Vòng lặp nhận lệnh và gọi A/C tương ứng |
| `_show_events()` | Lấy sự kiện từ Queue và in thông báo |

## 7. Đoạn thuyết trình ngắn (khoảng 45 giây)

> Thưa cô, Milestone 2 là một ứng dụng Python gồm bốn file. `main.py` nhận tham số, tạo một Queue và một Peer Registry chung, khởi tạo UDP Discovery, sau đó chạy giao diện CLI. Module A dùng hai Thread để phát HELLO mỗi 3 giây và nhận HELLO từ các máy trong LAN. Khi nhận được HELLO, A gọi C cập nhật danh sách peer và thời điểm nhận gần nhất. C có Thread kiểm tra timeout, xóa peer khi hơn 10 giây không nhận HELLO. Nếu có peer mới, đổi trạng thái hoặc offline, C đưa sự kiện vào Queue. Module B có Main Thread nhận các lệnh `/list`, `/status`, `/help`, `/quit` và một Event Thread lấy sự kiện từ Queue để in thông báo. Registry lưu trạng thái peer hiện tại, còn Queue chỉ lưu sự kiện chưa được xử lý. Khi thoát, `main.py` dừng các module và đóng socket.

**Công thức nhớ nhanh:** `main` **khởi động** → A **nhận/gửi** → C **lưu + kiểm tra** → Queue **báo thay đổi** → B **hiển thị/nhận lệnh** → `main` **dọn dẹp**.
