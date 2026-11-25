# LAN Chat & File Sharing (Socket Programming)

<div align="center">
  <img src="YOUR_BANNER_URL" width="100%" />

  <p><strong>Ứng dụng nhắn tin P2P và truyền file trong mạng nội bộ (LAN/Wi-Fi) bằng Python Socket API (UDP Broadcast & TCP Unicast)</strong></p>
</div>

## Overview

**LAN Chat & File Sharing** là ứng dụng giao tiếp ngang hàng (P2P) hoạt động trong mạng cục bộ mà không cần máy chủ trung tâm. Mỗi nút (peer) vừa đóng vai trò Server lắng nghe kết nối, vừa là Client chủ động kết nối tới các máy khác.

Dự án giải quyết các bài toán cốt lõi của lập trình mạng:
* **Tự động khám phá & đồng bộ trạng thái:** Sử dụng **UDP Broadcast** (`port 9999`) để phát hiện người dùng mới và cập nhật trạng thái `online` / `away` theo thời gian thực.
* **Truyền tin tin cậy & chống dính gói (Framing):** Sử dụng **TCP Unicast** kết hợp header độ dài byte UTF-8 để đảm bảo thông điệp không bị cắt xén hay dính liền trên dòng byte liên tục.
* **Truyền file không chặn luồng chat:** Tách kết nối và luồng gửi file riêng biệt để người dùng vẫn nhắn tin bình thường khi đang truyền tệp dung lượng lớn.
* **Giao diện không đè dòng nhập:** Ứng dụng `prompt_toolkit` và cơ chế khóa luồng (`threading.Lock`) giúp tin nhắn đến hoặc tiến độ file không làm mất dòng chữ đang gõ.

### Nhóm thực hiện
* **[Họ và tên 1]** – [MSSV]
* **[Họ và tên 2]** – [MSSV]

## Features

* **Milestone 1 – Khám phá peer & Trạng thái hiện diện (UDP):**
  * Broadcast gói tin `HELLO|<name>|<tcp_port>|<status>` mỗi **3 giây** trên cổng `9999`, tự động lọc bỏ gói tin do chính mình phát ra.
  * Quản lý danh sách peer (`tên`, `IP`, `cổng TCP`, `trạng thái`); tự động xóa và báo `offline` nếu quá **10 giây** không nhận được gói `HELLO` mới.
  * Đổi trạng thái `online` / `away` qua lệnh `/status` và phát cập nhật tức thì qua UDP.
* **Milestone 2 – Nhắn tin đa peer & Framing (TCP):**
  * Duy trì tối đa một kết nối TCP cho mỗi cặp peer và định danh khi mở kết nối bằng gói `HI|<name>|<tcp_port>|`.
  * Đóng khung tin nhắn theo số byte UTF-8 (`MSG|<length>|<utf-8 text>`) để chống dính gói / cắt gói TCP.
  * Lưu lại tin nhắn từ peer không phải đối tác hiện tại và hiển thị số tin chưa đọc (`unread`).
* **Milestone 3 – Truyền file song song & Tiến độ (TCP):**
  * Gửi file (`/send <file>`) trên một kết nối TCP và luồng riêng biệt, không làm chặn luồng chat.
  * Hiển thị `%` tiến độ theo từng mốc (`25%`, `50%`, `75%`, `100%`).
  * Lưu file nhận được vào thư mục `downloads/` (ghi qua file tạm `.part`, đổi tên khi hoàn tất và xóa file dở nếu mất kết nối).
* **Milestone 4 – Giao diện Console TUI & Xử lý lỗi:**
  * Giao diện chia cột bằng `prompt_toolkit` (có chế độ fallback CLI cơ bản) kèm `threading.Lock` bảo vệ màn hình, giữ nguyên dòng chữ đang gõ khi có tin đến.
  * Hỗ trợ đầy đủ bộ lệnh `/list`, `/chat`, `/send`, `/leave`, `/status`, `/help`, `/quit` cùng `/clear` xóa lịch sử cục bộ của phòng hiện tại.
  * Xử lý ổn định 5 tình huống lỗi: chat với người vừa offline, peer tắt ngang không gửi `BYE|`, mất mạng giữa lúc gửi file, gói tin sai định dạng, và sai lệnh/file không tồn tại.

## Prerequisites

Trước khi chạy chương trình, đảm bảo máy tính đã cài đặt:
* **Python 3.10** trở lên (Windows / Linux / macOS)
* Thư viện giao diện terminal **`prompt_toolkit`**
* Kết nối cùng một mạng **LAN / Wi-Fi** (mở quyền truy cập mạng Private/LAN trên Firewall cho Python để nhận gói UDP cổng `9999` và kết nối TCP)

## Installation

1. **Clone repository:**
```bash
git clone [https://github.com/username/lan-chat-socket.git](https://github.com/username/lan-chat-socket.git)
cd lan-chat-socket
```

2. **Cài đặt thư viện phụ thuộc:**
```bash
pip install prompt_toolkit
```

## Usage

Chạy chương trình trên ít nhất 2 máy cùng mạng LAN (hoặc mở nhiều cửa sổ terminal trên cùng một máy với cổng TCP khác nhau):

**Trên Máy 1 (ví dụ: Quan – TCP port 5000):**
```bash
python src/main.py --name Quan --port 5000
```

**Trên Máy 2 (ví dụ: Minh – TCP port 6000):**
```bash
python src/main.py --name Minh --port 6000
```
*(Nếu phiên bản của nhóm nhập tên và cổng từ bàn phím sau khi khởi chạy, dùng lệnh `python src/main.py` và nhập theo hướng dẫn trên màn hình).*

### Bảng lệnh hỗ trợ

| Lệnh / Phím tắt | Ý nghĩa |
| :--- | :--- |
| `/list` | Hiển thị danh sách online: số thứ tự, tên, IP, trạng thái và số tin chưa đọc |
| `/chat <tên \| số>` | Mở chat với peer được chọn (kết nối TCP) |
| `<văn bản>` | Gửi tin nhắn cho đối tác hiện tại |
| `/send <file>` | Gửi file cho đối tác hiện tại trên luồng TCP riêng |
| `/leave` | Đóng cuộc chat hiện tại (gửi `BYE\|` và chuyển phòng sang Read-Only) |
| `/status <online \| away>` | Đổi trạng thái hiện diện và phát qua UDP (hỗ trợ `/online`, `/away`) |
| `/clear` | Xóa lịch sử trò chuyện của phòng hiện tại trên máy cục bộ |
| `/help` | Xem danh sách lệnh |
| `/quit` hoặc `Ctrl + Q` | Ngừng phát `HELLO`, gửi `BYE\|` trên các kết nối đang mở và thoát |
| `Ctrl + B` | Ẩn/hiện thanh danh sách peer bên trái (hoặc click chuột trực tiếp) |

## Example

Minh họa kịch bản giao tiếp và kiểm thử thực tế giữa các peer:

```text
# 1. Khám phá peer & đổi trạng thái (UDP)
 [System] Minh (192.168.1.12:6000) is online
 [System] Minh is now AWAY

# 2. Mở kết nối chat & nhắn tin hai chiều (TCP Framing)
> /chat Minh
 [Joined] Connected to Minh (192.168.1.12:6000) — Type /leave to exit
 [Chat] [You]: Chào Minh, sẵn sàng demo chưa?
 [Chat] [Minh]: Rồi! Gửi mình slide nhé

# 3. Gửi file song song không chặn chat
> /send slides.pdf
 [File] 'slides.pdf' -> Minh: [########--------] 50%
 [Chat] [You]: Ok, đang gửi rồi đó
 [File] Sent 'slides.pdf' (2,516,582 bytes) to Minh.

# 4. Kết thúc cuộc trò chuyện
> /leave
 [System] Left chat with Minh (192.168.1.12:6000).
```

### Kịch bản kiểm thử các nhánh lỗi
1. **Chat với người vừa offline:** Tắt Minh, Quan gõ ngay `/chat Minh` $\rightarrow$ báo lỗi kết nối, chương trình không crash.
2. **Peer crash giữa lúc chat:** Đóng ngang cửa sổ terminal của Minh không gửi `BYE|` $\rightarrow$ báo mất kết nối.
3. **Mất mạng khi đang gửi file:** Ngắt Wi-Fi lúc tiến độ đạt ~50% $\rightarrow$ hai bên báo lỗi, bên nhận tự động xóa file tạm `.part`.
4. **Gói sai định dạng:** Dùng `nc <IP> <PORT>` gửi chuỗi `"abc"` $\rightarrow$ đóng riêng kết nối không hợp lệ đó, chương trình vẫn chạy tiếp.
5. **Lệnh sai / File không tồn tại:** Gõ `/chta Minh` hoặc `/send khongco.pdf` $\rightarrow$ in trợ giúp ngắn / báo không tìm thấy file.

## Project Structure

```text
lan-chat-socket/
├── src/
│   ├── main.py             # Điểm khởi chạy chương trình, khởi tạo các luồng mạng & UI
│   ├── cli.py              # Xử lý lệnh người dùng, điều phối phòng chat & sự kiện
│   ├── console_ui.py       # Giao diện TUI chia cột (prompt_toolkit) & fallback CLI
│   ├── chat_state.py       # Quản lý lịch sử hội thoại cục bộ & bộ đếm tin chưa đọc
│   ├── udp_discovery.py    # Broadcast gói HELLO (3s) & lắng nghe peer qua UDP
│   ├── peer_registry.py    # Bảng lưu trữ peer online/away & kiểm tra timeout (10s)
│   ├── tcp_transport.py    # TCP server/client, framing HI/MSG/BYE & định tuyến FILE
│   ├── file_transfer.py    # Luồng gửi file TCP riêng biệt & báo cáo % tiến độ
│   └── file_receiver.py    # Nhận file vào downloads/, quản lý file tạm .part
├── downloads/              # Thư mục tự động tạo để lưu file nhận được từ peer
├── data/                   # Lưu lịch sử trò chuyện cục bộ dạng JSON theo từng peer
├── docs/                   # Báo cáo đồ án & ảnh chụp bắt gói Wireshark
├── README.md
└── LICENSE
```

## Configuration

* **Cổng mạng mặc định:**
  * **UDP Discovery:** Cổng cố định `9999` (broadcast tới `255.255.255.255`), chu kỳ gửi `3s`, thời gian hết hạn `10s`.
  * **TCP Chat & File:** Cấu hình linh hoạt qua tham số `--port` (ví dụ `5000`, `6000`) để chạy nhiều tiến trình trên cùng một máy hoặc nhiều máy khác nhau.
* **Đặc tả khung bản tin giao thức:**
  * UDP hiện diện: `HELLO|<name>|<tcp_port>|<status>`
  * TCP định danh kết nối: `HI|<name>|<tcp_port>|`
  * TCP tin nhắn: `MSG|<length>|<utf-8 text>` (với `<length>` là số byte UTF-8)
  * TCP truyền file: `FILE|<filename>|<size>|<raw bytes>` (mỗi file một kết nối TCP riêng)
  * TCP kết thúc chat: `BYE|`
* **Thư mục dữ liệu:** Chương trình tự động khởi tạo `downloads/` (lưu tệp tải về) và `data/` (lưu lịch sử chat cục bộ dạng JSON) ngay tại thư mục gốc khi chạy.

## Contributing

Mọi đóng góp, báo lỗi hoặc đề xuất cải tiến đều được hoan nghênh. Vui lòng tạo Issue hoặc gửi Pull Request trực tiếp trên repository của nhóm.

## License

This project is licensed under the MIT License.

<div align="center">
  <img src="YOUR_FOOTER_IMAGE_URL" width="280" />
</div>
