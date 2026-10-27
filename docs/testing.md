# Test Plan & Evidence — DRAFT

**Đề gốc:** `LAN_Chat_Socket_Project.docx` §3–§7. **Tất cả test chưa chạy.** Không đổi `NOT RUN` thành `PASS` nếu chưa có kết quả thực tế.

## 1. Cách ghi một test

```text
Test ID:
Requirements:
Owner / Reviewer:
Date / Version / Commit:
Machine 1 (OS, Python, IP):
Machine 2 (OS, Python, IP):
Network (LAN/Wi-Fi, firewall):
Preconditions:
Steps:
Expected:
Actual:
Result: NOT RUN | PASS | FAIL | BLOCKED
Evidence: evidence/... or GitHub Issue/PR link
Defect issue if FAIL:
```

## 2. Test matrix

| ID | Related requirements | Kịch bản kiểm thử | Điều kiện PASS | Executor | Status |
|---|---|---|---|---|---|
| T-M1-TCP | M1 | Echo server/client trên localhost rồi giữa hai máy | Nhận đúng dữ liệu, lỗi connection được xử lý | B | NOT RUN |
| T-M1-UDP | M1 | UDP send/receive giữa hai chương trình | Datagram nhận đúng và biết sender | A | NOT RUN |
| T-UDP-01 | UDP-01/02/03/05, CONC-02/03, PROTO-02 | Hai máy chạy cùng app, bật Wireshark UDP | HELLO đúng nhịp ~3s, peer hiện với đúng name/IP/port/status | A | NOT RUN |
| T-UDP-02 | UDP-04/06 | Đóng app peer B, A tiếp tục chạy | Sau ~10s không có presence, peer B biến mất và thông báo offline | A | NOT RUN |
| T-UDP-03 | STATUS-01/02/03, CMD-06 | B chuyển online → away → online | A thấy status mới trong list, payload presence phù hợp | A | NOT RUN |
| T-UDP-04 | UDP-03 | 3 peer chạy cùng LAN, thử restart peer | Danh sách không bị nhân bản vô cớ; cập nhật hợp lý theo identity policy | A | NOT RUN |
| T-TCP-01 | CHAT-01/02/03, CMD-02/03, CONC-04/05 | Hai peer nhắn nhiều dòng **mà không chờ lượt** | Cả hai gửi/nhận ngay, từng message đúng nội dung | B | NOT RUN |
| T-TCP-02 | CHAT-05/06/07 | Ba peer: A đang chat B, C nhắn A | A vẫn chat B; tin của C có unread; chuyển sang C xem được tin | B | NOT RUN |
| T-TCP-03 | CHAT-01, CMD-05 | `/chat` và `/leave`, thử kết nối đồng thời 2 phía | Kết nối/bỏ chat đúng contract, không double bất thường | B | NOT RUN |
| T-PROTO-01 | PROTO-01/03/04 | Cố tình chia một frame thành nhiều lần gửi/nhận | Reassemble đủ số byte, nội dung/length chính xác | B | NOT RUN |
| T-PROTO-02 | PROTO-03/04 | Gửi hai frames nối nhau trong một stream | Receiver parse đúng **hai** messages | B | NOT RUN |
| T-PROTO-03 | PROTO-03/04 | UTF-8: tiếng Việt, ký tự nhiều byte | UTF-8 round-trip chính xác, không cắt giữa mã Unicode | B | NOT RUN |
| T-PROTO-04 | ERR-01/PROTO-03 | Header sai, length âm/quá lớn, connection đóng nửa chừng | Từ chối/đóng kết nối lỗi; ứng dụng vẫn chạy | B | NOT RUN |
| T-UI-01 | UI-01/02/04, CHAT-04 | Đang gõ nửa dòng thì peer gửi tin | Tin hiện ngay; dòng gõ và con trỏ không bị xóa mất | A | NOT RUN |
| T-UI-02 | UI-03 | Tin chat + UDP notification + progress tới gần đồng thời | Không chồng lấn console / crash | A | NOT RUN |
| T-FILE-01 | FILE-01/02/03, PROTO-04 | Gửi một file, so sánh file gốc và downloads | Progress hiển thị; file chính xác byte/size/hash | C | NOT RUN |
| T-FILE-02 | FILE-04, CONC-06 | Gửi file đủ lớn, hai peer tiếp tục nhắn tin trong lúc chuyển | Tin chat đến ngay, file vẫn hoàn chỉnh | C | NOT RUN |
| T-FILE-03 | FILE-03 | File tên tiếng Việt/đã tồn tại hoặc size 0 (theo policy nhóm) | Xử lý nhất quán theo spec, không ghi ra ngoài downloads | C | NOT RUN |
| T-FILE-04 | FILE-01/03 | Gửi file từ path hợp lệ, metadata filename đặc biệt | Không path traversal hoặc ghi đè trái policy | C | NOT RUN |
| T-ERR-01 | ERR-01 | Đóng cửa sổ/crash peer đang chat | Thông báo mất kết nối, về prompt hoặc trạng thái phù hợp | B | NOT RUN |
| T-ERR-02 | ERR-02 | Peer vừa offline nhưng còn trong `/list`, thử `/chat` | Refused/timeout được báo rõ, không crash | B | NOT RUN |
| T-ERR-03 | ERR-03 | `/send` file thiếu hoặc ngắt mạng giữa transfer | Báo lỗi; phần file dở bị xóa | C | NOT RUN |
| T-ERR-04 | ERR-04 | `/chta`, `/status foo`, `/send` sai | Short help, không crash | A | NOT RUN |
| T-ERR-05 | CMD-08 | `/quit` trong khi các thread đang chờ hoặc đang chat | Đóng socket/process sạch theo chiến lược nhóm | A+B+C | NOT RUN |
| T-RACE-01 | CONC-07 | Nhiều peer online/offline/chat liên tục, đọc shared snapshots | Không exception, race hoặc unread count sai | A+B | NOT RUN |
| T-CLI-01 | CMD-01..08 | Test toàn bộ 8 lệnh và văn bản thường | Đúng cách nhập/đúng nghiệp vụ mỗi lệnh | A+B+C | NOT RUN |
| T-WS-UDP | SUB-03 | Wireshark trên NIC khi 2 máy gửi presence | Screenshot rõ src/dst IP, UDP port, payload | A | NOT RUN |
| T-WS-TCP | SUB-03 | Bắt TCP connection khi `/chat` | Screenshot thấy **SYN, SYN-ACK, ACK** | B | NOT RUN |
| T-DEMO | SUB-04 | Rehearsal 10 phút với ≥2 máy | Toàn bộ luồng demo chạy đúng, thời lượng phù hợp | A+B+C | NOT RUN |

Các ca bổ sung như filename nguy hiểm, duplicate connection hoặc malformed header giúp tăng chất lượng; **không được tuyên bố đề bắt buộc đúng mọi test phụ**. Nội dung bắt buộc là hành vi trong các mục DOCX liên quan.

## 3. Wireshark evidence bắt buộc (§7)

- **UDP:** display filter ví dụ `udp.port == 9999` (cổng thực dùng có thể khác); phải chụp được gói broadcast presence.
- **TCP:** filter ví dụ `tcp.port == 5000` (đổi thành port thực). Phải thấy cả **SYN, SYN-ACK, ACK**. Nếu chỉ lọc `tcp.flags.syn == 1`, **ACK thuần** sẽ không hiện trong filter đó.
- Kèm chú thích địa chỉ IP, port, payload hoặc cờ TCP; lưu file ảnh trong `evidence/` **sau khi đã bắt thực tế**.
- Trong report, trình bày ngắn ý nghĩa của các gói; không lấy ảnh demo cũ làm kết quả của nhóm.

## 4. Nguồn lỗi và khó khăn cho report

Mỗi FAIL/BLOCKED nên tạo Issue có: dấu hiệu, cách tái hiện, giả thuyết, bằng chứng, hướng sửa, commit sửa và lần retest. Sau khi PASS, tổng hợp bài học ở `docs/devlog.md`, rồi viết phần *Problems Faced & Solutions* trong báo cáo.
