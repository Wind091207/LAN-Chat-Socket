# Learning map — học đúng phần phục vụ từng module

**Thứ tự ưu tiên:** DOCX đề gốc → demo giảng viên có nội dung đã đọc → tài liệu Python chính thức. Tên file giảng viên dùng làm chỉ dấu; **không chép nguyên source demo vào sản phẩm**, nhất là code cũ Python 2 hoặc client–server tập trung.

## Core — cả ba học trước M1

| Học gì | Tài liệu được cung cấp | Tài liệu chính thức |
|---|---|---|
| TCP/UDP và socket lifecycle | `HDLT_Socket.pdf` (5 trang), `Seminar_Socket Programming.pdf` pp. 3–12, `PythonNetBinder.pdf` phần Network Fundamentals | [Python Socket Programming HOWTO](https://docs.python.org/3/howto/sockets.html) |
| TCP echo/client–server | `01_client.py` / `01_server.py`, `02_client.py` / `02_server.py`; seminar pp. 13–16 | [socket library](https://docs.python.org/3/library/socket.html) |
| Bytes, `recv`, partial IO | `PythonNetBinder.pdf` *Partial Reads/Writes*, *Data Reassembly*, seminar pp. 7–9 | [Socket HOWTO](https://docs.python.org/3/howto/sockets.html) |
| Thread, lock | Seminar pp. 17–24; `Demo_CSocket_thread` chỉ tham khảo C++ | [threading](https://docs.python.org/3/library/threading.html) |

## A — UDP & UI (đề §3.1, §3.2, §4.3)

- `udp_broadcast_demo.py`: xem `SO_BROADCAST`, `SO_REUSEADDR`, `sendto`, `recvfrom`, cách chạy 3 terminal; **chưa có registry + timeout + `/list`**.
- `HDLT_Socket.pdf` pp. 4–5: luồng UDP không connection.
- `option_a_prompt_toolkit.py`: `PromptSession`, `patch_stdout` và fake receiver (không có mạng thật).
- `option_b_manual_redraw.py`: buffer + `screen_lock`, `msvcrt.getwch` (Windows) / `termios` (Unix); fake receiver.
- `chat_redraw.cpp`: ý tưởng tương tự bằng C++; không bắt buộc dùng C++ trong sản phẩm Python.
- Python docs: [socket](https://docs.python.org/3/library/socket.html), [threading](https://docs.python.org/3/library/threading.html), [`time.monotonic`](https://docs.python.org/3/library/time.html#time.monotonic).

**A phải tự trả lời:** vì sao UDP phù hợp discovery; làm sao nhận biết peer offline 10s; thread nào truy cập peer table; UI nhận event khi đang gõ mà không làm hỏng buffer.

## B — TCP Chat & Protocol (đề §3.3, §5.1, §5.2)

- `Seminar_Socket Programming.pdf` pp. 8–9: API và `socket`/`bind`/`listen`/`accept`/`connect`/`sendall`/`recv`.
- Seminar pp. 13–16: chat 1-1 theo lượt (**chưa đủ**); pp. 17–24: thread-per-client, 1-server-n-clients (**khác P2P**).
- `02_client.py`, `02_server.py`: chat luân phiên; phân tích vì sao chưa full-duplex.
- `03_client.py`, `03_server.py`: concurrency nhiều client; không bê nguyên server tập trung.
- `PythonNetBinder.pdf` (2010) phần *Partial Reads/Writes*, *Sending All Data*, *Data Reassembly*, *Timeouts*; chú ý nhiều ví dụ kiểu Python 2.
- Python docs: [socket](https://docs.python.org/3/library/socket.html), [Socket HOWTO](https://docs.python.org/3/howto/sockets.html), [threading](https://docs.python.org/3/library/threading.html).

**B phải tự trả lời:** vì sao TCP cần framing; `recv()` trả về ít hơn length phải làm gì; accepted socket khác listening socket; 2 peer đồng thời connect thế nào; active/unread state thuộc ai.

## C — File & QA (đề §3.4, §5.3, §7)

- DOCX §3.4, §5.2–5.3 (mỗi byte file phải đến đúng và có cleanup khi lỗi).
- `Gioithieu_Huongdan_DoAnSocket.pdf`: ví dụ file connection riêng, `%` progress, test lỗi mất mạng.
- `PythonNetBinder.pdf`: partial writes/reads, timeout, data reassembly.
- Python docs: [pathlib](https://docs.python.org/3/library/pathlib.html), [binary file I/O](https://docs.python.org/3/tutorial/inputoutput.html#reading-and-writing-files), [hashlib](https://docs.python.org/3/library/hashlib.html) (dùng cho test so sánh file), [threading](https://docs.python.org/3/library/threading.html).
- C cần hiểu protocol do B thiết kế và cách A nhận transfer events để hiển thị.

**C phải tự trả lời:** nếu progress 100% nhưng file phía nhận thiếu bytes thì sao; tạo file tạm/xóa dở thế nào; vì sao file IO không được chặn chat; test lỗi giữa mạng ra sao.

## File tham khảo bổ sung, không bắt buộc cho sản phẩm

| File/bộ | Vai trò đúng |
|---|---|
| `webclient.txt`, `socketMicrosoft.txt` | HTTP GET đơn giản / Microsoft Winsock, học thêm |
| `Demo_CSocket_thread` | MFC CSocket/`CreateThread`, bài học client–server C++ |
| `Seminar-Socket.ppt` | API CSocket MFC và bài toán socket C++ |
| `06 - Web Server.pdf`, `SLIDES_12_HTTP.pdf` | HTTP/Web; **không phải tính năng LAN Chat phải xây dựng** |
| `References.txt` | Link học thêm; đánh giá độ mới trước khi dùng |
| Thư mục `SocketProject_NonBlocking`, `BasicThread`, `ParameterThread`, ... trong ảnh | **Chỉ biết tên thư mục, chưa có mã nguồn để phân tích** |

## Quy tắc khi học

Học 1 API → chạy một demo nhỏ → giải thích bằng lời → viết test → ghi 4–8 dòng vào `docs/devlog.md`. Đừng sao chép toàn bộ lecture vào repository; ghi điều **ảnh hưởng tới thiết kế hoặc lỗi của chính nhóm**.
