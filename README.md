# 💬 LAN Chat & File Sharing (Socket Programming)

<div align="center">
  <p><strong>🚀 Ứng dụng nhắn tin P2P và truyền file trong mạng nội bộ (LAN/Wi-Fi) bằng Python Socket API — UDP Broadcast và TCP Unicast</strong></p>
</div>

## 📖 Overview

**LAN Chat & File Sharing** là ứng dụng giao tiếp ngang hàng (Peer-to-Peer) hoạt động trong cùng mạng LAN/Wi-Fi mà không cần máy chủ chat trung tâm. Mỗi máy chạy một peer độc lập, vừa lắng nghe kết nối TCP đến, vừa có thể chủ động kết nối tới peer khác.

Dự án triển khai các nội dung chính của Socket Programming:

- **UDP Discovery:** broadcast định kỳ để các peer tự phát hiện nhau và đồng bộ trạng thái online/away.
- **TCP Chat:** kết nối trực tiếp giữa các peer, sử dụng framing dựa trên độ dài byte UTF-8 để phân tách thông điệp.
- **TCP File Transfer:** gửi file qua kết nối TCP riêng và luồng nền, không dùng chung socket chat.
- **Concurrent Console UI:** nhận tin nhắn và cập nhật tiến độ truyền file trong khi người dùng tiếp tục nhập lệnh.

### 👥 Nhóm thực hiện

- **Vũ Thanh Phong** – 25120219
- **Nguyễn Hoàng Huy** – 25120193
- **Nguyễn Vũ Nhật Quang** – 25120225

## ✨ Features

### 🛰️ Peer Discovery & Presence (UDP)

- Broadcast bản tin theo định dạng:

  ~~~text
  HELLO|<name>|<tcp_port>|<status>
  ~~~

- Gửi định kỳ mỗi **3 giây** qua UDP port **9999**; broadcast address mặc định là **255.255.255.255**.
- Tự loại bỏ bản tin do chính peer phát ra.
- Quản lý danh sách peer gồm nickname, IP, TCP port và trạng thái.
- Peer được đánh dấu offline và loại khỏi danh sách khi không nhận được HELLO mới trong hơn **10 giây**.
- Hỗ trợ chuyển trạng thái bằng /status online, /status away hoặc lệnh tắt /online, /away. Trạng thái mới được gửi trong chu kỳ HELLO tiếp theo.

### 💬 Peer-to-Peer Chat (TCP)

- Mở hoặc tiếp tục phiên chat với peer được chọn bằng tên hoặc số thứ tự.
- Khi thiết lập kết nối, hai peer trao đổi thông tin định danh bằng header:

  ~~~text
  HI|<name>|<tcp_port>\n
  ~~~

- Tin nhắn được đóng khung theo số byte UTF-8. Header có dạng:

  ~~~text
  MSG|<length>\n
  <raw UTF-8 payload>
  ~~~

  Trong đó, &lt;length&gt; là số byte của payload, không phải số ký tự. Bên nhận đọc đúng số byte đã khai báo để tránh hiện tượng dính gói hoặc cắt gói TCP.
- Có thể giữ các phiên chat với nhiều peer; mỗi peer chỉ duy trì tối đa một kết nối chat, kể cả khi hai bên chủ động kết nối gần như đồng thời.
- Lưu lịch sử tin nhắn và số tin chưa đọc theo từng peer trên máy cục bộ.
- Nếu đang ở trạng thái AWAY và gửi tin nhắn, ứng dụng tự chuyển trạng thái về ONLINE.

### 📁 File Transfer (TCP)

- Gửi file bằng /send <file_path> qua **một kết nối TCP riêng** và một sender thread riêng; phiên chat không dùng chung socket truyền file.
- Header truyền file có dạng:

  ~~~text
  FILE|<sender_name>|<filename>|<size>\n
  <raw file bytes>
  ~~~

- Bên gửi hiển thị tiến độ tại các mốc **25%, 50%, 75% và 100%**.
- Bên nhận lưu file vào thư mục downloads/; dữ liệu được ghi vào file tạm .part và chỉ đổi sang tên file chính thức sau khi nhận đủ nội dung.
- Nếu quá trình truyền bị gián đoạn, file tạm chưa hoàn chỉnh sẽ được dọn dẹp.
- Kiểm tra tên file để ngăn path traversal và tránh ghi đè file đã tồn tại.
- Sau khi lưu file thành công, bên nhận gửi phản hồi FILE_OK để bên gửi xác nhận kết quả.

### 🎨 Console TUI & Error Handling

- Dùng **prompt_toolkit** để hiển thị giao diện terminal chia khu vực log, input và danh sách peer khi thư viện có sẵn và terminal hỗ trợ tương tác.
- Có chế độ console fallback khi prompt_toolkit không khả dụng hoặc chương trình chạy trong terminal không tương tác.
- Cập nhật giao diện từ các luồng nền thông qua event queue và khóa đồng bộ, hạn chế việc thông báo đến làm hỏng dòng nhập.
- Hỗ trợ xem lại lịch sử phòng chat, phân biệt phòng đang chat và phòng Read-Only sau khi rời phiên.
- Xử lý các trường hợp như peer ngắt kết nối, kết nối tới peer không còn online, dữ liệu giao thức sai định dạng, file không tồn tại và truyền file bị gián đoạn.

## 📋 Prerequisites

Trước khi chạy chương trình, máy tính cần có:

- 🐍 **Python 3.10 trở lên** (Windows, Linux hoặc macOS).
- 🧩 **pip** để cài dependency.
- 🌐 Kết nối cùng mạng LAN/Wi-Fi với các peer còn lại.
- 🔥 Cho phép Python giao tiếp qua firewall trên mạng Private/LAN: UDP port **9999** cho discovery và TCP port do người dùng cấu hình cho chat/file transfer.

Dependency hiện tại được ghim trong requirements.txt:

~~~text
prompt_toolkit==3.0.53
~~~

## 🛠️ Installation

1. **Clone repository:**

   ~~~bash
   git clone https://github.com/Wind091207/LAN-Chat-Socket.git
   cd LAN-Chat-Socket
   ~~~

2. **Tạo virtual environment:**

   ~~~bash
   python -m venv .venv
   ~~~

3. **Kích hoạt môi trường ảo:**

   Windows PowerShell:

   ~~~powershell
   .venv\Scripts\Activate.ps1
   ~~~

   Windows Git Bash:

   ~~~bash
   source .venv/Scripts/activate
   ~~~

   Linux/macOS:

   ~~~bash
   source .venv/bin/activate
   ~~~

4. **Cài dependency:**

   ~~~bash
   python -m pip install -r requirements.txt
   ~~~

## 🚀 Usage

Chạy lệnh từ **thư mục gốc repository**. Mỗi peer cần nickname và TCP port hợp lệ. Tham số đúng theo chương trình là **--tcp-port** (không phải --port).

**💻 Peer 1 (ví dụ: Quan):**

~~~bash
python src/main.py --name Quan --tcp-port 5000
~~~

**💻 Peer 2 (ví dụ: Huy):**

~~~bash
python src/main.py --name Huy --tcp-port 6000
~~~

Hai máy cần nằm trong cùng mạng LAN/Wi-Fi và không bị firewall chặn lưu lượng cần thiết. Nếu cần chỉ định broadcast address khác, dùng --bcast:

~~~bash
python src/main.py --name Quan --tcp-port 5000 --bcast 192.168.1.255
~~~

Xem đầy đủ tham số:

~~~bash
python src/main.py --help
~~~

Các tham số được hỗ trợ:

| Tham số | Bắt buộc | Mô tả |
|---|:---:|---|
| --name | Có | Nickname hiển thị của peer. Không được để trống hoặc chứa ký tự phân cách/control character. |
| --tcp-port | Có | Cổng TCP lắng nghe cho chat và nhận file, trong khoảng 1–65535. |
| --bcast | Không | Địa chỉ UDP broadcast; mặc định là 255.255.255.255. |

## ⌨️ Commands

| Lệnh / Phím tắt | Chức năng |
|---|---|
| /list | Hiển thị các peer đã phát hiện, địa chỉ, trạng thái và số tin chưa đọc. |
| /chat &lt;name&#124;number&gt; | Mở hoặc tiếp tục chat với peer theo nickname hoặc số thứ tự. |
| &lt;text&gt; | Gửi tin nhắn đến peer đang chat. |
| /send &lt;file_path&gt; | Gửi file đến peer đang chat qua kết nối TCP riêng. Có thể đặt đường dẫn trong dấu nháy nếu chứa khoảng trắng. |
| /status online | Chuyển trạng thái hiện diện thành ONLINE. |
| /status away | Chuyển trạng thái hiện diện thành AWAY. |
| /online hoặc /away | Lệnh tắt để đổi trạng thái. |
| /clear | Xóa lịch sử của phòng đang xem hoặc phòng chat hiện tại trên máy cục bộ. |
| /leave | Gửi BYE, đóng phiên chat hiện tại và đưa phòng đó về chế độ Read-Only; dùng /chat để tham gia lại. |
| /help | Hiển thị danh sách lệnh. |
| /quit | Thoát ứng dụng. |
| Ctrl+Q hoặc Ctrl+C | Thoát giao diện TUI; quá trình dừng ứng dụng sẽ đóng các kết nối đang mở. |
| Ctrl+B | Ẩn/hiện thanh danh sách peer trong giao diện TUI. |

Lưu ý:

- Lệnh /send sử dụng đường dẫn tương đối tính từ **thư mục làm việc hiện tại**. Khi chạy theo hướng dẫn ở trên, thư mục này là thư mục gốc repository.
- Khi đang xem phòng Read-Only, cần dùng /chat &lt;name&gt; để tham gia lại trước khi gửi tin nhắn hoặc file.
- Các phím tắt Ctrl+Q, Ctrl+C và Ctrl+B áp dụng cho giao diện TUI tương tác.

## 🧪 Suggested Test Flow

1. Chạy ứng dụng trên ít nhất hai máy cùng mạng LAN/Wi-Fi với nickname và TCP port phù hợp.
2. Chờ UDP discovery, sau đó dùng /list để kiểm tra peer xuất hiện.
3. Dùng /status away và /status online để kiểm tra cập nhật presence.
4. Dùng /chat &lt;name&#124;number&gt; ở hai phía rồi trao đổi tin nhắn hai chiều.
5. Khi đang chat, gửi một file bằng /send &lt;file_path&gt;; kiểm tra tiến độ ở bên gửi và file trong downloads/ ở bên nhận.
6. Dùng /leave để rời phiên, kiểm tra phòng Read-Only và dùng /chat để tham gia lại.
7. Thử các trường hợp lỗi: nhập sai lệnh, gửi file không tồn tại, peer đóng ứng dụng khi đang chat hoặc ngắt mạng trong lúc truyền file.

Để kiểm tra discovery và truyền dữ liệu trong môi trường thực tế, nên demo trên ít nhất hai máy tính trong cùng mạng LAN/Wi-Fi. Chạy nhiều terminal trên một máy không thay thế hoàn toàn cho kiểm thử mạng giữa các máy.

## ⚙️ Protocol & Network Configuration

### UDP Discovery

- Port: **9999** (cố định).
- Chu kỳ broadcast: **3 giây**.
- Peer timeout: **10 giây**.
- Bản tin:

  ~~~text
  HELLO|<name>|<tcp_port>|<status>
  ~~~

### TCP Chat

Các frame điều khiển kết thúc bằng newline:

| Frame | Định dạng thực tế | Mục đích |
|---|---|---|
| HI | HI&#124;&lt;name&gt;&#124;&lt;tcp_port&gt; + newline | Trao đổi nickname và TCP port khi bắt đầu kết nối. |
| MSG | MSG&#124;&lt;length&gt; + newline, sau đó là payload UTF-8 đúng &lt;length&gt; byte | Gửi tin nhắn văn bản. |
| BYE | BYE + newline | Kết thúc phiên chat. |

### TCP File Transfer

- Mỗi file dùng một kết nối TCP riêng.
- Header: FILE&#124;&lt;sender_name&gt;&#124;&lt;filename&gt;&#124;&lt;size&gt; + newline.
- Sau header là đúng &lt;size&gt; byte dữ liệu file.
- Phía nhận phản hồi FILE_OK + newline sau khi lưu file thành công.
- Kích thước file tối đa được giao thức cho phép là **1 GiB**.

### Runtime Data

Khi chạy chương trình từ thư mục gốc repository:

- data/: lưu lịch sử chat, số tin chưa đọc và tên peer dưới dạng JSON. Tên file được tạo theo nickname và TCP port của peer local.
- downloads/: lưu file nhận được từ các peer.
- Hai thư mục runtime này không cần commit lên GitHub.

## 📂 Project Structure

~~~text
LAN-Chat-Socket/
├── .gitignore
├── README.md
├── requirements.txt
└── src/
    ├── chat_state.py       # Lưu lịch sử chat và số tin chưa đọc
    ├── cli.py              # Xử lý lệnh, phòng chat và event queue
    ├── console_ui.py       # TUI prompt_toolkit và console fallback
    ├── file_receiver.py    # Nhận file, lưu downloads/ và dọn file .part
    ├── file_transfer.py    # Gửi file bằng TCP thread riêng, báo tiến độ
    ├── main.py             # Entry point, khởi tạo các module
    ├── peer_registry.py    # Quản lý peer và timeout
    ├── protocol.py         # Định nghĩa framing cho chat và file
    ├── tcp_transport.py    # TCP accept/connect, chat và định tuyến file
    └── udp_discovery.py    # UDP broadcast HELLO và nhận peer
~~~

## 🤝 Contributing

Mọi đóng góp, báo lỗi hoặc đề xuất cải tiến đều được hoan nghênh. Vui lòng tạo Issue hoặc gửi Pull Request trên repository của nhóm.
