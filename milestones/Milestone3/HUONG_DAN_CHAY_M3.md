# Milestone 3 — Hướng dẫn chạy và kiểm thử

## 1. Chuẩn bị

- Mỗi peer có Python 3 và cùng phiên bản mã nguồn với **7 file** trong `src/`:
  - Từ Milestone 2: `main.py`, `cli.py`, `udp_discovery.py`, `peer_registry.py`.
  - Bổ sung ở Milestone 3: `protocol.py`, `chat_state.py`, `tcp_transport.py`.
- Các peer phải thông mạng qua cùng mạng LAN / Wi-Fi / VirtualBox Host-only và cho phép qua Firewall:
  - **UDP port `9999`** (gửi/nhận gói `HELLO`).
  - **Các TCP port riêng của từng peer** (ví dụ `5001`, `5002`, `5003` cho TCP Chat P2P).
- Ví dụ thử nghiệm đã thực hiện: **Windows (Quan `5001` & Huy `5003`) + Ubuntu VirtualBox (Minh `5002`)**.
- Nếu dùng VirtualBox: **Adapter 1 = NAT** (truy cập Internet, clone/pull GitHub), **Adapter 2 = Host-only Adapter** (`Ethernet 2` trên Windows — dùng để trao đổi UDP `HELLO` và TCP Chat).

**Không cần chạy A/B/C riêng:** chỉ chạy `main.py` trên **mỗi máy**. Các luồng UDP Discovery, Peer Registry, TCP Server/Client và CLI sẽ tự động được khởi động.

---

## 2. Xác định IP và broadcast

Trên Windows, mở PowerShell:

```powershell
ipconfig
```

Trên Ubuntu:

```bash
ip -4 addr
```

Ví dụ mạng Host-only khi kiểm thử 3 peer:

| Máy / Terminal | IPv4 | TCP Port | Vai trò |
|---|---|---|---|
| Windows (PowerShell 1) | `192.168.56.1/24` | `5001` | Quan |
| Ubuntu VM | `192.168.56.104/24` | `5002` | Minh |
| Windows (PowerShell 2) | `192.168.56.1/24` | `5003` | Huy |
| Địa chỉ broadcast | `192.168.56.255` | UDP `9999` | Đích gửi `HELLO` |

**Quan trọng:** Các IP trên là ví dụ từ lần thử của nhóm; nếu dùng mạng LAN/Wi-Fi khác, phải thay địa chỉ `--bcast` phù hợp. Không dùng `127.0.0.1` khi kiểm thử giao tiếp giữa hai máy.

---

## 3. Chạy các peer

Mở terminal trong thư mục **`src/`** của repo trên từng máy.

**Máy Windows — Quan (Terminal 1):**

```powershell
python main.py --name Quan --tcp-port 5001 --bcast 192.168.56.255
```

**Máy Ubuntu — Minh:**

```bash
python3 main.py --name Minh --tcp-port 5002 --bcast 192.168.56.255
```

**Máy Windows — Huy (Terminal 2, dùng khi test 3 peer & unread):**

```powershell
python main.py --name Huy --tcp-port 5003 --bcast 192.168.56.255
```

Mỗi máy sẽ hiện dòng thông báo lắng nghe TCP/UDP và dấu nhắc `>`. Nếu chạy từ **thư mục gốc repo**, thay `main.py` bằng `src/main.py`.

**Giải thích tham số:**
- `--name`: Nickname hiển thị (không chứa ký tự `|` hoặc ký tự điều khiển).
- `--tcp-port`: Cổng TCP Server mở trên máy để nhận kết nối chat P2P (đồng thời được quảng bá trong gói `HELLO`).
- `--bcast`: Địa chỉ nhận broadcast UDP.

---

## 4. Các lệnh CLI

| Lệnh | Tác dụng |
|---|---|
| `/list` | Xem danh sách peer kèm STT, IP, TCP port, trạng thái và số tin chưa đọc `(unread)` |
| `/chat <name\|number>` | Mở (hoặc chuyển sang) phòng chat TCP với peer được chọn; hiển thị lịch sử tin nhắn gần đây |
| `<văn bản bất kỳ>` | Gửi tin nhắn UTF-8 tới đối tác đang hiển thị ở dấu nhắc `You -> <Tên>>` |
| `/leave` | Gửi gói `BYE` và đóng cuộc trò chuyện hiện tại |
| `/status online` | Đổi trạng thái của chính mình thành `online` |
| `/status away` | Đổi trạng thái của chính mình thành `away` |
| `/help` | Hiển thị danh sách lệnh |
| `/quit` | Gửi `BYE` tới các kết nối đang mở, dừng toàn bộ thread và thoát |

Ví dụ luồng hoạt động khi **Quan chat với Minh**: Quan nhập `/chat Minh` → TCP kết nối tới `192.168.56.104:5002` → hai bên trao đổi gói `HI` → dấu nhắc của Quan đổi thành `You -> Minh>` → Quan nhập tin nhắn → đóng gói `MSG|<byte_len>\n<UTF-8>` gửi qua TCP → màn hình Minh in `[HH:MM] [Quan]: <nội dung>`.

---

## 5. Test cases và kết quả đã ghi nhận

| ID | Cách kiểm tra | Kỳ vọng | Kết quả |
|---|---|---|---|
| M3-01 | Quan gõ `/list`, sau đó gõ `/chat Minh` | Kết nối TCP thành công, đổi dấu nhắc sang `You -> Minh>` | PASS |
| M3-02 | Nhắn tin tiếng Việt có dấu hai chiều giữa Quan và Minh | Hiển thị đúng dấu UTF-8, đúng thứ tự, kèm giờ gửi `[HH:MM]` | PASS |
| M3-03 | Gửi đoạn văn tiếng Việt dài (> 700 byte) | `_recv_exact` gom đủ số byte theo header, không bị cắt mất chữ | PASS |
| M3-04 | Nhồi 2 frame `MSG\|5\nhelloMSG\|11\nChào Minh!` gửi liền 1 lần | `recv_frame` tách chính xác thành 2 tin nhắn riêng biệt (chống dính gói) | PASS |
| M3-05 | Minh đang `/chat Huy`; Quan `/chat Minh` và gửi 2 tin nhắn | Minh nhận thông báo `(1 unread)`, `(2 unread)`; khi gõ `/chat Quan` thì hiện đủ 2 tin cũ và `unread` về `0` | PASS |
| M3-06 | Quan và Minh cùng gõ `/chat` tới nhau tại cùng một thời điểm | Quy tắc so sánh `(ip, tcp_port)` giữ lại đúng **1** kết nối duy nhất | PASS |
| M3-07 | Quan gõ `/leave`, sau đó kết nối lại `/chat Minh` | Minh nhận thông báo `Quan left the chat.`; kết nối lại vẫn xem được lịch sử phiên chạy | PASS |
| M3-08 | Tắt ngang cửa sổ terminal của 1 peer khi đang chat | Peer còn lại tự thoát phiên chat về dấu nhắc `>` mà không crash | PASS |
| M3-09 | Dùng `nc 192.168.56.1 5001` và gửi chuỗi rác `abc` | Server phát hiện sai header `HI\|...`, đóng ngay socket rác; ứng dụng vẫn chạy bình thường | PASS |
| M3-10 | Wireshark lọc `tcp.port == 5002` và mở `Follow > TCP Stream` | Thấy rõ bắt tay 3 bước `SYN`, `SYN-ACK`, `ACK` và khung dữ liệu `HI`, `MSG\|<len>`, `BYE` | PASS |

**Lưu ý khi kiểm thử:**
- Lịch sử tin nhắn trong `ChatState` được lưu trên RAM theo phiên chạy hiện tại: nếu một peer `/leave` rồi `/chat` lại thì vẫn còn lịch sử, nhưng nếu `/quit` thoát hẳn chương trình rồi mở lại thì bộ nhớ phiên mới sẽ bắt đầu từ rỗng.
- Khi 1 peer tắt ngang không qua `/quit`, tầng TCP báo ngắt kết nối ngay lập tức, còn thông báo `is offline` ở tầng UDP sẽ xuất hiện sau khoảng 10 giây tính từ gói `HELLO` cuối cùng.

---

## 6. Kiểm tra bằng Wireshark

Trên Windows, chọn đúng interface **`Ethernet 2` (VirtualBox Host-only)** rồi áp dụng Display Filter:

1. **Bắt tay 3 bước TCP (Three-way Handshake):**

```text
tcp.port == 5002
```

Quan sát 3 gói mở đầu kết nối giữa `192.168.56.1` và `192.168.56.104`: `[SYN]`, `[SYN, ACK]`, `[ACK]`.

2. **Nội dung khung bản tin ứng dụng (`Follow > TCP Stream`):**
   - Chuột phải vào một gói `[PSH, ACK]` bất kỳ trong luồng chat → chọn **Follow → TCP Stream**:

```text
HI|Quan|5001
HI|Minh|5002
MSG|17
Hi bờ rồ Minh
MSG|11
Hi bro Quan
BYE
```

*(Lưu ý: chuỗi `"Hi bờ rồ Minh"` gồm 13 ký tự nhưng header ghi `MSG|17` do các ký tự tiếng Việt có dấu chiếm 3 byte/ký tự trong bảng mã UTF-8).*

---

## 7. Lỗi thường gặp

| Hiện tượng | Cần kiểm tra |
|---|---|
| `Failed to connect ...: timed out` | **Windows Defender Firewall** đang chặn kết nối TCP Inbound trên card Host-only (`Public` profile); cần mở rule cho phép cổng TCP `5000-5010` và UDP `9999` |
| `Connection refused` | Peer đích chưa khởi chạy `main.py` hoặc nhập sai cổng TCP |
| Không gõ được tiếng Việt có dấu trong Ubuntu VM | Tắt bộ gõ tiếng Việt ở Windows (`E`) và cài/chuyển sang `ibus-unikey` (`vi`) trực tiếp bên trong Ubuntu |
| Chữ `[You]:` hơi chìm trên nền xanh PowerShell | Dùng mã màu hồng sáng (`\033[95m`) thay cho xanh dương (`\033[94m`) trong `cli.py` |

**Không tắt toàn bộ Firewall** để thử nghiệm; chỉ mở rule cho đúng dải cổng thử nghiệm của đồ án.

---

## 8. Demo với hai laptop thật

Khi chuyển từ Windows + Ubuntu VM sang **hai laptop thật**, vẫn chạy cùng 7 file và cùng quy trình. Đổi `--bcast` theo subnet thực tế và kiểm tra Firewall; nếu Wi-Fi trường/quán bật **client isolation** chặn giao tiếp ngang hàng giữa các thiết bị, có thể dùng **Hotspot 4G từ điện thoại** cho hai laptop kết nối vào để demo ổn định.

**Checkpoint M3:** Hai/ba peer kết nối chat TCP ổn định, hỗ trợ tiếng Việt UTF-8, tin nhắn dài, đếm `unread` đa phòng, xử lý ngoại lệ crash/gói rác an toàn và có đầy đủ ảnh minh chứng Wireshark.
