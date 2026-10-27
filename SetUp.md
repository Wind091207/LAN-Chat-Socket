# Thiết lập môi trường — LAN Chat & File Sharing

Tài liệu chuẩn bị **môi trường phát triển cho cả 5 milestone** của đồ án Socket Programming (nhóm 3 người, Python 3, Windows).

> Đây là hướng dẫn cài đặt, **không phải** danh sách yêu cầu đồ án. Để xem các chức năng bắt buộc và thang điểm 100, đọc [REQUIREMENTS.md](REQUIREMENTS.md).
>
> Các phiên bản thư viện dưới đây là lựa chọn ban đầu của nhóm, **chưa được xác nhận đã kiểm thử thành công trên cả ba máy**.

## 1. Phần mềm cần chuẩn bị

| Phần mềm | Dùng để làm gì? | Khi nào cần? |
|---|---|---|
| **Python 3** (khuyến nghị cùng phiên bản trên cả ba máy) | Chạy ứng dụng Socket | Ngay từ Milestone 1 |
| **Visual Studio Code** và extension **Python** của Microsoft | Viết, chạy, debug Python | Ngay từ Milestone 1 |
| **Git** | Clone, commit, push và làm việc nhóm qua GitHub | Ngay từ đầu |
| **Wireshark + Npcap** (Windows) | Quan sát UDP broadcast và bắt TCP three-way handshake làm minh chứng | Muộn nhất trước giai đoạn kiểm thử cuối; có thể cài sớm |

Kiểm tra Windows Firewall khi chạy chương trình trên **hai máy trong cùng LAN/Wi-Fi**. Có thể cần cho phép Python nhận kết nối tại các cổng do nhóm sử dụng.

Không cần cài Docker, WSL, Flask, Django, database, C++, Visual Studio C++ hoặc PyInstaller để đáp ứng đề gốc.

## 2. Thư viện Python cần cài thêm

Đa số chức năng dùng thư viện **có sẵn trong Python** như `socket`, `threading`, `time`, `struct`, `queue`, `json`, `pathlib`, `hashlib`, `logging`, `unittest`.

Hai thư viện ngoài **dự kiến** dùng xuyên suốt dự án:

| Thư viện | Phiên bản nhóm dự kiến | Mục đích |
|---|---|---|
| `prompt_toolkit` | `3.0.53` | Giao diện console: tiếp nhận tin đến mà không làm mất phần văn bản đang gõ (phương án A của đề) |
| `pytest` | `9.1.1` | Viết và chạy kiểm thử tự động, thuận tiện cho kiểm thử TCP/UDP và các chức năng |

**Lưu ý:** Đề không bắt buộc hai thư viện này. Nếu nhóm chọn tự quản lý bàn phím bằng `msvcrt` (phương án B), có thể không dùng `prompt_toolkit`. Nếu dùng `unittest` có sẵn thì không cần `pytest`.

## 3. Thiết lập một lần trên mỗi máy (Windows)

Mở Terminal trong thư mục repository `LAN-Chat-Socket`.

**Bước 1 — Kiểm tra Python và Git**

```powershell
py -3 --version
git --version
```

**Bước 2 — Tạo môi trường ảo cho project**

```powershell
py -3 -m venv .venv
```

**Bước 3 — Cài thư viện bằng pip trong môi trường ảo**

Vì đây là tài liệu Markdown `SetUp.md`, **không dùng** `pip install -r SetUp.md`. Cài trực tiếp:

```powershell
.\.venv\Scripts\python.exe -m pip install prompt_toolkit==3.0.53 pytest==9.1.1
```

Câu lệnh chạy được mà **không cần kích hoạt** môi trường ảo. Nếu chỉ làm Milestone 1 (TCP echo và UDP send/receive), không cần cài thêm thư viện nào; `socket` đã có trong Python.

**Bước 4 — Kiểm tra môi trường**

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest --version
.\.venv\Scripts\python.exe -c "import socket, prompt_toolkit; print('Môi trường Python OK')"
```

Nếu nhóm dùng VS Code, vào **Python: Select Interpreter** và chọn `.venv\Scripts\python.exe`.

Thư mục `.venv/` đã được loại khỏi Git nhờ `.gitignore`. Mỗi thành viên tự tạo môi trường trên máy mình, không push thư viện đã cài lên GitHub.

## 4. Mỗi milestone sử dụng những gì?

| Milestone | Nền tảng / công cụ |
|---|---|
| **1. TCP echo, UDP send/receive** | Python `socket`; không cần thư viện ngoài |
| **2. UDP discovery, online/away** | `socket`, `time`, `threading` (đều có sẵn) |
| **3. TCP chat, nhiều peer, framing** | `socket`, `threading`, `struct`, `queue`, `json` (đều có sẵn) |
| **4. Console và file transfer** | `prompt_toolkit` theo phương án A; `pathlib`, `hashlib` và file I/O có sẵn |
| **5. Kiểm thử, báo cáo, demo** | `pytest` (tùy chọn), `unittest` có sẵn, Wireshark + Npcap cài riêng |

**Không cần** `pip install socket`, `pip install threading` hoặc `pip install os`.

## 5. Lưu ý khi làm việc nhóm

- Thống nhất phiên bản Python sử dụng và thử các lệnh trên **cả ba máy**.
- Chỉ thay đổi thư viện/phiên bản sau khi cả nhóm thống nhất; nếu đổi cần cập nhật tài liệu này.
- Mỗi người tự chạy và kiểm thử Milestone 1 trước khi ghi vào README rằng chương trình đã hoạt động.
- Bắt gói Wireshark cho UDP broadcast và TCP SYN → SYN-ACK → ACK theo yêu cầu tại [REQUIREMENTS.md](REQUIREMENTS.md).

**Tài liệu chính thức:** `LAN_Chat_Socket_Project.docx`. Đề yêu cầu Socket API gốc, không chỉ định phải dùng thư viện giao diện hoặc kiểm thử cụ thể.
