# LAN Chat & File Sharing

**Ứng dụng nhắn tin ngang hàng (P2P) và truyền file trong mạng LAN/Wi-Fi, xây dựng bằng Python Socket API.**

Sử dụng **UDP Broadcast** để khám phá peer và cập nhật trạng thái, **TCP** để nhắn tin và truyền file trực tiếp giữa các máy.

## Overview

Mỗi máy chạy ứng dụng là một peer: vừa lắng nghe kết nối TCP đến, vừa có thể chủ động kết nối tới peer khác. Ứng dụng không cần máy chủ trung tâm.

### Features

- **Peer Discovery & Presence (UDP):** Broadcast thông tin `HELLO` mỗi 3 giây qua UDP port `9999`; peer không còn gửi thông tin trong hơn 10 giây sẽ được đánh dấu offline.
- **TCP Chat:** Nhắn tin hai chiều, quản lý phiên chat theo peer và lưu số tin nhắn chưa đọc.
- **Message Framing:** Header chứa độ dài payload UTF-8 theo byte, giúp bên nhận tách đúng từng thông điệp trên TCP stream.
- **File Transfer:** Mỗi lần gửi file sử dụng một kết nối TCP riêng và một worker thread riêng; hiển thị tiến độ theo các mốc 25%, 50%, 75% và 100%.
- **Terminal UI:** Giao diện tương tác với `prompt_toolkit`; khi không có terminal tương tác hoặc thư viện không khả dụng, ứng dụng dùng CLI fallback.
- **Local Chat History:** Lưu lịch sử theo peer trên máy đang chạy ứng dụng.

## Team

- **Vũ Thanh Phong** — 25120219
- **Nguyễn Hoàng Huy** — 25120193
- **Nguyễn Vũ Nhật Quang** — 25120225

## Prerequisites

- Python **3.10 or newer**.
- Hai hoặc nhiều máy trong cùng mạng LAN/Wi-Fi để kiểm thử thực tế.
- Cho phép Python nhận kết nối TCP và gói UDP broadcast trong firewall của hệ điều hành.
- Các thư viện Python được liệt kê trong `requirements.txt`.

> Khuyến nghị chạy thử trên hai máy tính cùng mạng. Một số mạng Wi-Fi khách có thể bật client isolation và chặn các thiết bị liên lạc trực tiếp.

## Installation

Clone repository:

```bash
git clone https://github.com/Wind091207/LAN-Chat-Socket.git
cd LAN-Chat-Socket
```

Tạo và kích hoạt virtual environment.

**Windows (PowerShell):**

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Cài dependency:

```bash
python -m pip install -r requirements.txt
```

Chi tiết thiết lập môi trường phát triển có trong [SetUp.md](SetUp.md).

## Run

Chạy lệnh từ **thư mục gốc của repository**.

**Máy 1:**

```bash
python src/main.py --name Quan --tcp-port 5000
```

**Máy 2:**

```bash
python src/main.py --name Minh --tcp-port 6000
```

Mỗi instance cần một TCP port riêng. Mặc định ứng dụng broadcast tới `255.255.255.255:9999`; có thể chỉ định địa chỉ broadcast khác bằng tham số `--bcast`.

Sau khi hai peer khởi động, dùng `/list` để kiểm tra các peer được phát hiện. Mở firewall cho Python nếu hai máy không nhìn thấy hoặc không kết nối được với nhau.

## Commands

| Command | Description |
|---|---|
| `/list` | Hiển thị peer đã phát hiện, địa chỉ, trạng thái và số tin chưa đọc. |
| `/chat <name|number>` | Mở hoặc tiếp tục chat với peer theo tên hoặc số thứ tự trong danh sách. |
| `<message>` | Gửi tin nhắn tới peer đang chat. |
| `/send <file_path>` | Gửi file tới peer đang chat trên kết nối TCP riêng. Đặt đường dẫn trong dấu ngoặc kép nếu có khoảng trắng. |
| `/status online` | Chuyển trạng thái sang online. |
| `/status away` | Chuyển trạng thái sang away. |
| `/online`, `/away` | Lệnh tắt tương ứng của hai lệnh status trên. |
| `/leave` | Rời phiên chat hiện tại và quay về Lobby. Lịch sử phòng vẫn được giữ ở chế độ chỉ đọc; dùng `/chat <name>` để chat lại. |
| `/clear` | Xóa lịch sử và số tin chưa đọc của phòng đang xem trên máy hiện tại. Thao tác này cũng cập nhật dữ liệu lịch sử local. |
| `/help` | Hiển thị hướng dẫn lệnh. |
| `/quit` | Thoát ứng dụng và đóng các kết nối đang mở. |

Khi giao diện TUI đang hoạt động:

- `Ctrl + B`: Ẩn/hiện thanh peer.
- `Ctrl + Q`: Thoát ứng dụng.
- Có thể chọn peer trong thanh bên để xem lịch sử; cần dùng `/chat <name>` để bắt đầu hoặc tiếp tục phiên chat.

Nếu ứng dụng đang ở CLI fallback, dùng `/quit` để thoát.

## Quick Test

1. Khởi chạy hai peer trên hai máy cùng mạng.
2. Dùng `/list` để xác nhận hai peer đã phát hiện nhau.
3. Thử `/status away` và kiểm tra trạng thái ở máy còn lại.
4. Dùng `/chat Minh` (hoặc tên peer tương ứng) rồi gửi tin nhắn hai chiều.
5. Trong lúc chat, dùng `/send <file_path>`; kiểm tra file nhận được trong thư mục `downloads/`.
6. Thử `/leave`, `/chat <name>` để vào lại phòng và `/quit` để thoát.

## Protocol Summary

README chỉ tóm tắt các loại bản tin chính; phần mô tả thiết kế và cơ chế framing chi tiết thuộc báo cáo đồ án.

| Transport | Frame | Purpose |
|---|---|---|
| UDP | `HELLO|<name>|<tcp_port>|<status>` | Quảng bá sự hiện diện của peer. |
| TCP | `HI|<name>|<tcp_port>\n` | Định danh peer khi thiết lập kết nối chat. |
| TCP | `MSG|<byte_length>\n<payload>` | Header cho biết số byte UTF-8 cần đọc tiếp. |
| TCP | `BYE\n` | Báo kết thúc phiên chat. |
| TCP | `FILE|<sender_name>|<filename>|<size>\n<raw_bytes>` | Header metadata theo sau bởi đúng số byte dữ liệu file. |
| TCP | `FILE_OK\n` | Xác nhận bên nhận đã lưu file thành công. |

Mỗi file được truyền trên một TCP connection riêng. Tên file nhận được được kiểm tra trước khi lưu; dữ liệu đang truyền được ghi vào file tạm `.part`, sau đó mới chuyển thành file hoàn chỉnh. Kết nối truyền file chỉ được xem là hoàn tất khi bên gửi nhận được `FILE_OK`.

## Runtime Data

Khi chạy từ thư mục gốc repository, ứng dụng sử dụng:

- `data/`: lịch sử chat local dạng JSON, tách theo tên và TCP port của instance.
- `downloads/`: file nhận từ peer.

Các thư mục này được tạo khi cần và không cần commit dữ liệu cá nhân lên Git.

## Project Structure

```text
LAN-Chat-Socket/
├── src/
│   ├── chat_state.py
│   ├── cli.py
│   ├── console_ui.py
│   ├── file_receiver.py
│   ├── file_transfer.py
│   ├── main.py
│   ├── peer_registry.py
│   ├── protocol.py
│   ├── tcp_transport.py
│   └── udp_discovery.py
├── milestones/
├── requirements.txt
├── REQUIREMENTS.md
├── SetUp.md
├── GithubTutorial.md
└── README.md
```

## Troubleshooting

**Không thấy peer trong `/list`:**

- Kiểm tra hai máy có cùng mạng LAN/Wi-Fi hay không.
- Kiểm tra firewall có cho phép Python nhận UDP broadcast trên port `9999` không.
- Kiểm tra router/access point có bật client isolation hay không.

**Không kết nối được TCP:**

- Xác nhận peer đích vẫn đang chạy.
- Kiểm tra IP và TCP port hiển thị trong `/list`.
- Cho phép kết nối TCP qua firewall trên máy nhận.

**Không gửi/nhận được file:**

- Kiểm tra đường dẫn file ở máy gửi.
- Kiểm tra quyền ghi vào thư mục `downloads/`.
- Nếu kết nối bị ngắt giữa chừng, file tạm chưa hoàn chỉnh sẽ được dọn dẹp bởi bên nhận.

**Không hiển thị giao diện TUI:**

- Cài dependency bằng `python -m pip install -r requirements.txt`.
- Chạy trong terminal tương tác có stdin/stdout TTY. Nếu điều kiện này không đáp ứng, chương trình sử dụng CLI fallback.

## Project Documents

- [SetUp.md](SetUp.md) — hướng dẫn chuẩn bị môi trường.
- [REQUIREMENTS.md](REQUIREMENTS.md) — yêu cầu và phạm vi đồ án.
