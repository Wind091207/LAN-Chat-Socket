# Milestone 2 — Hướng dẫn chạy và kiểm thử

## 1. Chuẩn bị

- Mỗi peer có Python 3 và cùng phiên bản mã nguồn với **4 file** trong `src/`: `main.py`, `cli.py`, `udp_discovery.py`, `peer_registry.py`.
- Hai peer phải liên lạc được qua cùng mạng LAN/Host-only và cho phép nhận UDP port **9999**.
- Ví dụ thử nghiệm đã thực hiện: **Windows (Quan) + Ubuntu VirtualBox (Minh)**.
- Nếu dùng VirtualBox: **Adapter 1 = NAT** (Internet, clone GitHub), **Adapter 2 = Host-only Adapter** (trao đổi HELLO với Windows).

**Không cần chạy A/B/C riêng:** chỉ chạy `main.py` trên **mỗi máy**. Các thread sẽ tự được khởi động.

## 2. Xác định IP và broadcast

Trên Windows, mở PowerShell:

```powershell
ipconfig
```

Trên Ubuntu:

```bash
ip -4 addr
```

Ví dụ mạng Host-only khi kiểm thử:

| Máy | IPv4 | Vai trò |
|---|---|---|
| Windows | `192.168.56.1/24` | Quan |
| Ubuntu VM | `192.168.56.104/24` | Minh |
| Địa chỉ broadcast | `192.168.56.255` | Đích gửi HELLO |

**Quan trọng:** Các IP trên là ví dụ từ lần thử của nhóm; nếu subnet khác, phải thay địa chỉ `--bcast` phù hợp. Không dùng `127.0.0.1` để kiểm thử giao tiếp hai máy.

## 3. Chạy hai peer

Mở terminal trong thư mục **`src/`** của repo trên từng máy.

**Máy Windows — Quan:**

```powershell
python main.py --name Quan --tcp-port 5001 --bcast 192.168.56.255
```

**Máy Ubuntu — Minh:**

```bash
python3 main.py --name Minh --tcp-port 5002 --bcast 192.168.56.255
```

Mỗi máy sẽ hiện dòng khởi động và dấu nhắc `>`. Nếu chạy từ **thư mục gốc repo**, thay `main.py` bằng `src/main.py`.

**Giải thích tham số:** `--name` là nickname; `--tcp-port` mới chỉ được quảng bá trong HELLO (chưa mở TCP Chat); `--bcast` là địa chỉ nhận broadcast UDP.

## 4. Các lệnh CLI

| Lệnh | Tác dụng |
|---|---|
| `/list` | Xem peer C đang lưu trong Registry |
| `/status away` | Đổi trạng thái của chính mình thành `away`; A gửi trong HELLO tiếp theo |
| `/status online` | Đổi trạng thái của chính mình thành `online` |
| `/help` | Hiện các lệnh |
| `/quit` | Thoát CLI, yêu cầu dừng các thread và đóng socket |

Ví dụ khi **Quan đổi trạng thái**: Quan nhập `/status away` → A máy Quan gửi `HELLO|Quan|5001|away` → C máy Minh cập nhật → B máy Minh in `Quan is now away`.

## 5. Test cases và kết quả đã ghi nhận

| ID | Cách kiểm tra | Kỳ vọng | Kết quả |
|---|---|---|---|
| M2-01 | Chạy hai peer, không tự nhập HELLO | Mỗi bên hiện `... is online` | PASS |
| M2-02 | Nhập `/list` trên hai máy | Hiện đúng tên, IP, port, trạng thái | PASS |
| M2-03 | Quan nhập `/status away`, rồi `/status online` | Minh thấy hai lần đổi trạng thái | PASS |
| M2-04 | Cho Minh `/quit`, chờ quá 10 giây kể từ HELLO cuối | Quan báo Minh offline, `/list` không còn Minh | PASS |
| M2-05 | Khởi động lại Minh | Quan báo Minh online trở lại | PASS |
| M2-06 | Để yên hai bên khoảng 20–30 giây rồi `/list` | Vẫn có peer; không in `online` mỗi 3 giây | PASS (xác nhận thủ công) |
| M2-07 | Wireshark lọc `udp.port == 9999` | Bắt được HELLO của cả hai IP, chu kỳ ~3 giây | PASS |
| M2-08 | Cho **cả hai cùng `--name Quan --tcp-port 5001`** nhưng khác IP | Hai máy vẫn thấy nhau trong `/list` | PASS (sau khi sửa self-filter) |

**Lưu ý về M2-04:** Timeout được tính từ **HELLO cuối cùng**, không tính từ lúc nhấn `/quit`. Thread C kiểm tra theo chu kỳ nên thông báo offline có thể xuất hiện muộn hơn mốc 10 giây một chút.

## 6. Kiểm tra bằng Wireshark

Trên Windows, chọn đúng interface **VirtualBox Host-only** rồi áp dụng Display Filter:

```text
udp.port == 9999
```

Gói tin kỳ vọng:

```text
192.168.56.1   -> 192.168.56.255   HELLO|Quan|5001|online
192.168.56.104 -> 192.168.56.255   HELLO|Minh|5002|online
```

Chọn một gói, mở phần **Data** để thấy payload. Lưu ảnh cho thấy **Source, Destination, UDP port và nội dung HELLO**. Trong bài test trùng tên/port, cả hai payload đều có thể là `HELLO|Quan|5001|online`; phân biệt hai máy qua **IP nguồn**.

## 7. Lỗi thường gặp

| Hiện tượng | Cần kiểm tra |
|---|---|
| Hai máy không thấy nhau | IP, subnet và `--bcast`; có Host-only Adapter; UDP 9999 không bị Firewall chặn |
| Ubuntu không `git clone` được | Adapter NAT và DNS/Internet của máy ảo |
| Wireshark không thấy HELLO | Đã chọn đúng interface Host-only và filter `udp.port == 9999` chưa |
| `/list` có peer rồi mất | Kiểm tra HELLO còn gửi liên tục và `last_seen` được cập nhật không |
| Trùng tên + port bị bỏ qua | Kiểm tra cả hai máy đã cập nhật phiên bản `udp_discovery.py` sửa self-filter chưa |

**Không tắt toàn bộ Firewall** để thử nghiệm; chỉ cho phép Python/UDP 9999 trên mạng thử nghiệm khi thật sự cần.

## 8. Demo với hai laptop thật

Khi chuyển từ Windows + Ubuntu VM sang **hai laptop cùng Wi-Fi**, vẫn chạy cùng 4 file và cùng quy trình. Đổi `--bcast` theo subnet Wi-Fi thực tế, kiểm tra Firewall; một số Wi-Fi có thể bật **client isolation** khiến hai thiết bị không trao đổi trực tiếp được. Không dùng IP `192.168.56.x` của VirtualBox cho mạng Wi-Fi thật.

**Checkpoint M2:** Hai peer tự phát hiện nhau, `/list` và `/status` hoạt động, peer offline sau timeout, có ảnh Wireshark. Ghi lại kết quả kiểm thử thực tế của hai laptop khi demo chính thức.
