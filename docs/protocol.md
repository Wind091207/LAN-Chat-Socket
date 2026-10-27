# Application-layer Protocol — DRAFT (chưa phải giao thức đã chốt)

**Nguồn ràng buộc:** `LAN_Chat_Socket_Project.docx` §5.2: nhóm **tự thiết kế giao thức**; UDP presence là datagram; TCP stream cần **message type + length**, receiver phải đọc **đúng số byte**. Các mẫu `HELLO|...`, `MSG|...`, `FILE|...`, `BYE|` trong DOCX chỉ là **ví dụ**.

## 1. Mục tiêu giao thức

- Peer giới thiệu username, TCP listen port, status qua UDP.
- TCP receiver biết một frame thuộc loại nào và dài bao nhiêu byte.
- Cho phép text UTF-8, gồm dấu tiếng Việt, không nhầm số ký tự với byte.
- Có thông điệp/tiến trình nhận diện đầu kết nối để mapping đúng peer.
- Có phương pháp truyền file và đóng chat; báo lỗi/timeout hợp lý.
- Có giới hạn kích thước/header và validation để tránh crash, treo, file traversal.

## 2. Các message type cần cả nhóm quyết định

| Message | Transport | Dữ liệu cốt lõi | Chốt wire format? |
|---|---|---|---|
| PRESENCE / HELLO | UDP | username, TCP port, online/away | **TBD** |
| IDENTITY / HI (nếu chọn) | TCP | định danh peer | **TBD** |
| MSG | TCP | text bytes + length | **TBD** |
| FILE | TCP | filename, length, raw file bytes | **TBD** |
| BYE / close | TCP | end-chat signal | **TBD** |
| ACK / ERROR (nếu nhóm bổ sung) | TCP | completion/error info | **TBD — không bắt buộc** |

## 3. Checklist phải có trước khi nhóm viết network parser

- [ ] Quy tắc nhận diện peer và username trùng.
- [ ] UDP datagram bytes/string encoding, delimiter/escaping, port range, malformed handling.
- [ ] TCP header chính xác: version, type, payload length, cách xác định header hoàn chỉnh.
- [ ] Binary integer encoding hoặc text delimiter, maximum payload, size validation.
- [ ] Length của `MSG` là **UTF-8 bytes**, không phải number of Python Unicode characters.
- [ ] `read_exact(n)` **lặp `recv()`** tới khi đủ bytes hoặc lỗi/EOF; giữ lại extra bytes đúng cách nếu cần.
- [ ] Phân tách nhiều frame trong một TCP stream.
- [ ] FILE metadata, tên file an toàn, giới hạn size, chunking, connection riêng hay chung.
- [ ] Cách đóng chat (`/leave`), end-of-stream và xử lý partial file.
- [ ] Quy tắc duplicate simultaneous TCP connections.
- [ ] Người review A/B/C cùng ký duyệt (trong PR và `decisions.md`).

## 4. Vấn đề TCP framing bắt buộc giải thích trong report

`sendall(frame_a); sendall(frame_b)` **không bảo đảm** hai lần `recv()` riêng biệt. Receiver có thể nhận một phần `frame_a`, cả hai frame dính nhau hoặc frame bị cắt theo nhiều chunk. Parser phải phục hồi chính xác dựa trên header và số byte, không dựa vào kích thước mỗi `recv()`.

## 5. Những quyết định có thể cân nhắc (KHÔNG bắt buộc)

- File trên một TCP connection riêng để chat vẫn hoạt động.
- Khởi đầu dùng length-prefix framing thay vì delimiter-only để xử lý văn bản có ký tự đặc biệt.
- File tạm `.part` rồi rename khi nhận hoàn tất, xóa khi lỗi.
- Max frame length và allowed filename policy.
- ACK sau khi receiver xác nhận lưu file thành công.

**Tuyệt đối không biến gợi ý thành requirement mới khi đối chiếu đề.**

## 6. Bảng định dạng cuối cùng (điền sau khi duyệt)

| Field | Type / byte order | Size | Validation |
|---|---|---|---|
| `...` | TBD | TBD | TBD |

Kèm ví dụ bytes hexdump/encoded frames, sequence diagram và test vectors thực tế khi đã chốt.
