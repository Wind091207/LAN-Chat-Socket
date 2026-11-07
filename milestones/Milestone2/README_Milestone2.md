# Milestone 2 — UDP Discovery, Online List & Status

## 1. Mục tiêu

Theo `LAN_Chat_Socket_Project.docx`, Milestone 2 triển khai:

- **UDP Discovery:** Mỗi peer tự phát `HELLO|name|tcp_port|status` khoảng **3 giây/lần** qua UDP port **9999**.
- **Online List:** Lưu tên, IP, TCP port, trạng thái và thời điểm nhận HELLO gần nhất (`last_seen`).
- **Status:** Hỗ trợ `online` và `away`; xóa peer khi **quá 10 giây** không nhận HELLO.
- **CLI:** Xem danh sách peer, đổi trạng thái và nhận thông báo online/offline.

**Checkpoint:** Hai peer trên cùng LAN tự phát hiện nhau, cập nhật trạng thái và phát hiện peer ngắt kết nối. M2 **chưa thực hiện TCP Chat**; TCP port trong HELLO mới là thông tin quảng bá cho M3.

## 2. Phân công

| Thành viên | File phụ trách | Nhiệm vụ |
|---|---|---|
| **A — Discovery** | `src/udp_discovery.py` | Tạo UDP socket, gửi/nhận HELLO, cập nhật trạng thái của chính mình, chuyển thông tin peer nhận được cho C |
| **B — CLI & Integration** | `src/cli.py`, `src/main.py` | Xử lý lệnh `/list`, `/status`, `/help`, `/quit`; hiển thị sự kiện; kết nối và khởi động A/B/C |
| **C — Registry & Test** | `src/peer_registry.py`, kiểm thử | Quản lý danh sách peer, `last_seen`, timeout, Queue sự kiện; kiểm thử và ghi nhận kết quả |

**Lưu ý:** A/B/C là **phân công phát triển**, không phải ba chương trình riêng. **Mỗi peer chạy đủ cả 4 file** thông qua `main.py`.

## 3. Kiến trúc và dữ liệu

| Module | Dữ liệu quản lý | Hàm chính |
|---|---|---|
| `main.py` | Tham số chạy, một `Queue` chung, tham chiếu `registry` và `discovery` | `main()`, `tcp_port()` |
| `udp_discovery.py` — A | Socket UDP, `name`, `tcp_port`, `status`, địa chỉ broadcast | `start()`, `_send_loop()`, `_recv_loop()`, `set_status()`, `stop()` |
| `peer_registry.py` — C | `_peers[(ip, tcp_port)]`, `last_seen`, Queue sự kiện | `update_peer()`, `get_peers()`, `remove_expired_peers()`, `start_timeout_monitor()` |
| `cli.py` — B | Lệnh người dùng, Event Thread; đọc Registry và Queue | `run_cli()`, `_show_events()` |

### Luồng hoạt động

```text
Người dùng chạy main.py
       |
       +--> Tạo Queue + PeerRegistry (C) + UDPDiscovery (A)
       +--> Khởi động các thread nền
       `--> run_cli() (B) nhận lệnh

Máy Minh: A gửi HELLO|Minh|5002|online
       |
       v (UDP broadcast trong LAN)
Máy Quan: A nhận HELLO -> C.update_peer(...)
       |
       +--> C lưu/cập nhật peer trong Registry (lệnh /list đọc ở đây)
       `--> Nếu mới/đổi trạng thái: C.put_nowait(event) vào Queue
                                         |
                                         v
                                  B._show_events() in thông báo
```

**Registry khác Queue:** Registry lưu **trạng thái hiện tại** của peer; Queue chỉ lưu **sự kiện chờ CLI hiển thị**. HELLO định kỳ cùng trạng thái chỉ làm mới `last_seen`, không in `online` liên tục.

### Các thread sau khi ứng dụng khởi động

| Thread | Hàm | Chức năng |
|---|---|---|
| Main Thread — B | `run_cli()` | Chờ và xử lý lệnh nhập từ bàn phím |
| UDP Send Thread — A | `_send_loop()` | Gửi HELLO khoảng 3 giây/lần |
| UDP Receive Thread — A | `_recv_loop()` | Nhận HELLO, gọi C cập nhật peer |
| Timeout Monitor Thread — C | `_monitor_loop()` | Kiểm tra và xóa peer hết hạn |
| Event Thread — B | `_show_events()` | Lấy sự kiện từ Queue và hiển thị |

C dùng `Lock` để bảo vệ Registry khi nhiều thread truy cập; A dùng `Lock` để bảo vệ trạng thái của chính mình. `Queue` hỗ trợ chuyển sự kiện an toàn giữa C và B.

## 4. Kết quả hiện tại

Đã kiểm thử giữa **Windows host (192.168.56.1)** và **Ubuntu VirtualBox (192.168.56.104)** trên mạng **Host-only**, broadcast `192.168.56.255`, UDP `9999`:

- **PASS:** Hai peer tự động phát hiện nhau và `/list` hiển thị đúng IP/port.
- **PASS:** `/status online` / `/status away` cập nhật và thông báo giữa hai peer.
- **PASS:** Timeout offline và phát hiện lại khi peer khởi chạy lại (kiểm thử thủ công).
- **PASS:** Wireshark bắt được gói UDP HELLO từ cả hai IP, chu kỳ khoảng 3 giây.
- **PASS:** Trường hợp hai peer **cùng nickname `Quan` và TCP port `5001` nhưng khác IP** vẫn nhận diện được nhau sau khi sửa bộ lọc HELLO.
- **Đã xác nhận thủ công:** Để chạy ổn định, không xuất hiện thông báo online lặp lại mỗi 3 giây.

Ảnh terminal và Wireshark cần được lưu vào thư mục minh chứng của nhóm. Đây là **một máy vật lý + một máy ảo**, chưa thay cho demo hai máy vật lý.

## 5. Vấn đề gặp phải và cách khắc phục

| Vấn đề thực tế | Nguyên nhân | Cách khắc phục và kết quả |
|---|---|---|
| **M2-01:** Receiver Thread dừng khi nhận `HELLO|Broken|5003|busy` | `peer_registry.update_peer()` từ chối status `busy` và ném `ValueError`; exception trước đó làm thoát vòng nhận UDP | Bọc lời gọi `registry.update_peer(...)` bằng `try/except (ValueError, TypeError)` và `continue` để bỏ qua HELLO không hợp lệ. **Đã sửa, kiểm thử lại: PASS** |
| Hai máy khác IP nhưng trùng nickname và TCP port không nhìn thấy nhau | Điều kiện lọc HELLO của chính máy chỉ so sánh `name` và `tcp_port`, nên bỏ nhầm HELLO từ peer khác | Bổ sung so sánh `peer_ip` với địa chỉ IP cục bộ dùng để broadcast. Đã kiểm thử Windows `192.168.56.1` và Ubuntu `192.168.56.104` cùng tên `Quan`, port `5001`: **PASS trên mạng Host-only**; giải pháp chưa bao quát mọi cấu hình nhiều interface |
| Test với `--bcast 127.0.0.1` không chứng minh discovery giữa hai máy | `127.0.0.1` là loopback của từng máy, không phải broadcast LAN | Thiết lập mạng VirtualBox Host-only và gửi tới broadcast của subnet (đã thử `192.168.56.255:9999`). Wireshark xác nhận HELLO từ hai IP, chu kỳ khoảng 3 giây: **PASS** |
| Thông báo `online/offline` xuất hiện chen vào dòng nhập, con trỏ không trở lại sau dấu `>` | Main Thread đang chạy `input()` trong khi Event Thread gọi `print()`; chưa có cơ chế redraw giao diện | **Chưa xử lý trong M2**. Chuyển sang M4: Console Redraw và đồng bộ đầu ra; không đánh dấu lỗi này là đã sửa |

**Lưu ý về phạm vi test:** Các kết quả trên được ghi nhận từ Windows host + Ubuntu VirtualBox trên mạng Host-only; cần tiếp tục kiểm thử trên hai máy vật lý khi thực hiện demo cuối.

## 6. Giới hạn và bước tiếp theo

- Chưa có TCP Chat, Message Framing hay gửi file: tiếp tục ở các milestone sau.
- Việc in sự kiện có thể chen vào dòng `input()`; console redraw hoàn chỉnh xử lý ở M4.
- Bộ lọc self-HELLO hiện dựa trên tên, TCP port và IP cục bộ phù hợp bài test Host-only; chưa bảo đảm nhận diện duy nhất trong mọi cấu hình nhiều interface/cùng IP.
- Cần review PR, lưu bằng chứng và kiểm thử lại trên hai máy thật trước demo nếu giảng viên yêu cầu.

**Hướng dẫn thực hiện:** xem `HUONG_DAN_CHAY_M2.md`.
