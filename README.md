# LAN Chat & File Sharing

Đồ án Socket Programming — nhóm **3 sinh viên**, sử dụng **Python 3**.

## Mục tiêu

Xây dựng ứng dụng **Peer-to-Peer (P2P)** hoạt động trong cùng mạng LAN/Wi-Fi. Mỗi máy chạy cùng một chương trình, có thể tìm các máy khác, nhắn tin trực tiếp và gửi/nhận file mà không cần máy chủ chat trung tâm.

- **UDP:** tìm peer và cập nhật trạng thái online/away.
- **TCP:** nhắn tin và truyền file.
- **Concurrency:** nhận tin và truyền file mà không làm ứng dụng bị chặn.
- **Giao diện:** ưu tiên console; đề gốc cho phép console hoặc GUI.

## Tình trạng

**Planning — chưa triển khai hoặc xác nhận hoàn thành bất kỳ tính năng nào.**

## Yêu cầu và thang điểm

Xem **[REQUIREMENTS.md](REQUIREMENTS.md)** để biết toàn bộ yêu cầu, các lệnh, 5 milestones, sản phẩm phải nộp và rubric **100 điểm**.

Nguồn quy định chính thức: `LAN_Chat_Socket_Project.docx` do giảng viên cung cấp. Nếu có khác biệt, **đề gốc được ưu tiên**.

## Kế hoạch phát triển

1. **Milestone 1:** TCP echo và UDP send/receive.
2. **Milestone 2:** UDP discovery, danh sách online, `/list`, `/status`.
3. **Milestone 3:** TCP chat hai chiều, framing, đa kết nối, `/chat`, `/leave`.
4. **Milestone 4:** Nhận tin trong lúc nhập và gửi file có tiến độ.
5. **Milestone 5:** Xử lý lỗi, kiểm thử, báo cáo, Wireshark và demo.

## Nhóm và cách làm việc

- **Thành viên A:** UDP discovery, trạng thái và giao diện console.
- **Thành viên B:** TCP chat, kết nối và giao thức/framing.
- **Thành viên C:** File transfer, kiểm thử và phối hợp xử lý lỗi.
- **Cả ba:** duyệt giao thức chung, kiểm thử tích hợp, viết báo cáo và chuẩn bị vấn đáp.

Phân vai là **đề xuất ban đầu**, nhóm sẽ xác nhận người phụ trách và reviewer trước khi code.

## Cài đặt và chạy

**Chưa có ứng dụng hoàn chỉnh để chạy.** Lệnh cài đặt, chạy và kiểm thử sẽ được bổ sung sau khi nhóm tự kiểm tra thành công. Xem **[SetUp.md](SetUp.md)** để chuẩn bị Python, Git, VS Code, Wireshark và cài các thư viện dự kiến sử dụng.
