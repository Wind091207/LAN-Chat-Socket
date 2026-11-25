# LAN Chat & File Sharing

Ứng dụng **Peer-to-Peer (P2P) Chat & File Sharing** chạy trên Python 3, dành cho các máy tính kết nối cùng mạng LAN/Wi-Fi. Mỗi máy chạy một peer độc lập; các peer tự tìm thấy nhau qua UDP và giao tiếp trực tiếp qua TCP, không cần máy chủ chat trung tâm.

## Tính năng

- **Peer discovery:** UDP broadcast bản tin `HELLO` định kỳ để phát hiện peer và cập nhật trạng thái `online` / `away`.
- **Danh sách peer:** hiển thị peer đã phát hiện; peer hết hạn được loại khỏi danh sách sau timeout.
- **TCP chat:** kết nối trực tiếp giữa các peer, hỗ trợ nhiều phiên chat và nhận tin ở luồng nền.
- **Chat history:** lưu lịch sử hội thoại và số tin chưa đọc vào file JSON cục bộ.
- **File transfer:** gửi/nhận file qua TCP, hiển thị tiến độ gửi, kiểm tra tên file và dọn file tạm nếu truyền thất bại.
- **Console UI:** giao diện tương tác sử dụng `prompt_toolkit` khi môi trường terminal hỗ trợ; có console fallback khi không khả dụng.

## Yêu cầu

- Python **3.10 trở lên**.
- Các máy chạy ứng dụng cần kết nối cùng mạng LAN/Wi-Fi và cho phép lưu lượng UDP broadcast cùng TCP qua firewall.
- `pip` để cài dependency.

## Cài đặt

Clone repository và đi vào thư mục dự án:

```bash
git clone https://github.com/Wind091207/LAN-Chat-Socket.git
cd LAN-Chat-Socket
```

Tạo virtual environment và cài thư viện:

```bash
python -m venv .venv
```

Windows (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
```

Windows (Git Bash) hoặc Linux/macOS:

```bash
source .venv/Scripts/activate   # Windows Git Bash
# hoặc: source .venv/bin/activate  # Linux/macOS
```

Cài dependency:

```bash
python -m pip install -r requirements.txt
```

## Chạy ứng dụng

Chạy lệnh từ **thư mục gốc repository**. Mỗi máy cần một nickname và một TCP port riêng.

Peer thứ nhất:

```bash
python src/main.py --name Alice --tcp-port 5001
```

Peer thứ hai (trên máy khác hoặc một terminal khác):

```bash
python src/main.py --name Bob --tcp-port 5002
```

Hai peer cần ở cùng mạng LAN/Wi-Fi. UDP discovery mặc định dùng broadcast address `255.255.255.255` và port `9999`. Có thể chỉ định broadcast address khác bằng `--bcast`:

```bash
python src/main.py --name Alice --tcp-port 5001 --bcast 192.168.1.255
```

Xem các tham số:

```bash
python src/main.py --help
```

## Lệnh trong ứng dụng

| Lệnh | Chức năng |
|---|---|
| `/list` | Hiển thị peer đã phát hiện và thông tin tin nhắn chưa đọc. |
| `/status online` | Đặt trạng thái của peer hiện tại thành online. |
| `/status away` | Đặt trạng thái của peer hiện tại thành away. |
| `/chat <name\|number>` | Mở hoặc tiếp tục chat với peer theo tên hoặc số thứ tự trong danh sách. |
| `/send <file_path>` | Gửi file cho peer đang chat. |
| `/clear` | Xóa lịch sử phòng chat hiện tại trên máy của mình. |
| `/leave` | Rời phiên chat hiện tại; có thể vào lại bằng `/chat`. |
| `/help` | Hiển thị hướng dẫn lệnh. |
| `/quit` | Thoát ứng dụng. |
| `<text>` | Gửi nội dung tin nhắn đến peer đang chat. |

Đường dẫn file trong `/send` được tính từ **thư mục làm việc hiện tại** (thông thường là thư mục gốc repository khi chạy theo hướng dẫn trên).

## Dữ liệu runtime

Các thư mục sau được tạo trong thư mục làm việc khi ứng dụng chạy và không được commit lên Git:

- `data/`: lưu lịch sử chat dạng JSON theo nickname và TCP port.
- `downloads/`: lưu các file nhận được.

## Cấu trúc repository

```text
LAN-Chat-Socket/
├── .gitignore
├── README.md
├── requirements.txt
└── src/
    ├── chat_state.py
    ├── cli.py
    ├── console_ui.py
    ├── file_receiver.py
    ├── file_transfer.py
    ├── main.py
    ├── peer_registry.py
    ├── protocol.py
    ├── tcp_transport.py
    └── udp_discovery.py
```

## Ghi chú mạng

- `--tcp-port` phải nằm trong khoảng `1–65535` và không được bị chương trình khác chiếm dụng trên máy đó.
- UDP discovery dùng port `9999`; các peer phải nhận được UDP broadcast trên mạng LAN.
- Firewall của hệ điều hành có thể yêu cầu cho phép Python nhận kết nối TCP và UDP trên mạng Private.
- Không nên chạy nhiều peer trên cùng một máy với cùng TCP port.

## Kiểm tra nhanh

1. Chạy ít nhất hai peer trên cùng LAN/Wi-Fi với nickname và TCP port khác nhau.
2. Dùng `/list` để kiểm tra hai peer đã phát hiện nhau.
3. Dùng `/chat <name|number>` rồi gửi tin nhắn hai chiều.
4. Dùng `/send <file_path>` để thử truyền file; kiểm tra file nhận trong `downloads/`.
5. Thử `/status away`, `/status online`, `/leave` và `/quit`.

Việc chạy được trên một máy không thay thế cho kiểm thử tích hợp trên ít nhất hai máy trong mạng LAN thực tế.