# Cải tiến từ Milestone 2 sang Milestone 3 (`src/cli.py`)

Tài liệu tóm tắt các nâng cấp của **Module CLI & Chat Interface (`src/cli.py`)** khi chuyển từ giai đoạn khám phá mạng ngang hàng (Milestone 2) sang giai đoạn nhắn tin trực tiếp qua TCP (Milestone 3).

---

## 1. So sánh Tổng quan

| Tiêu chí | Milestone 2 (UDP Discovery) | Milestone 3 (TCP Chat & CLI) |
| :--- | :--- | :--- |
| **Chức năng chính** | Chỉ hiển thị danh sách peer online và đổi trạng thái cá nhân. | Bổ sung đầy đủ luồng kết nối, nhắn tin 1-1 qua TCP và quản lý hội thoại. |
| **Lệnh hỗ trợ** | `/list`, `/status`, `/help`, `/quit` | Giữ nguyên 4 lệnh M2 + bổ sung `/chat <name\|number>`, `/leave` và gửi tin nhắn trực tiếp. |
| **Xử lý văn bản thường** | Báo lỗi *"Unknown command"* với mọi chuỗi không khớp lệnh. | Chuỗi không bắt đầu bằng `/` được gửi trực tiếp thành tin nhắn tới đối tác đang chat. |
| **Thông báo sự kiện** | Chỉ thông báo `online`, `offline`, `status_changed`. | Bổ sung hiển thị tin nhắn đến trực tiếp, đếm tin chưa đọc (`unread`) và thông báo rời phòng chat. |
| **Tích hợp API** | Chỉ gọi `PeerRegistry` và `UDPDiscovery`. | Tích hợp thêm `TCPManager` (`connect_peer`, `send_message`, `leave_chat`) và `ChatState`. |

---

## 2. Chi tiết các Cải tiến chính

1. **Quản lý phiên trò chuyện (`/chat` và `/leave`):**
   * **`/chat <name|number>`:** Hỗ trợ chọn người nhận linh hoạt theo **tên** (không phân biệt hoa/thường) hoặc **số thứ tự** hiển thị trong `/list`. Tự động rời phòng chat cũ nếu đang trò chuyện với người khác, thiết lập kết nối TCP mới, đánh dấu đã đọc (`mark_as_read`) và tải lại lịch sử tin nhắn (`get_history`).
   * **`/leave`:** Ngắt phiên trò chuyện hiện tại thông qua `leave_chat()`, đặt lại đối tác hiện tại về `None` và đưa dấu nhắc nhập liệu về trạng thái chờ mặc định (`> `).

2. **Nhắn tin trực tiếp & Phân biệt cú pháp lệnh:**
   * Cập nhật dấu nhắc động (`[PartnerName]> `) giúp nhận biết rõ người đang trò chuyện.
   * Văn bản không có tiền tố `/` được gửi thẳng qua `send_message(peer_id, text)` và lưu vào lịch sử qua `add_message()`. Các chuỗi bắt đầu bằng `/` nhưng sai tên lệnh sẽ được báo lỗi cú pháp rõ ràng.

3. **Hiển thị tin nhắn & Thông báo tin chưa đọc (Unread):**
   * **Trong phòng chat:** Tin nhắn từ đối tác hiện tại được in trực tiếp lên màn hình ngay khi nhận và tự động cập nhật trạng thái đã đọc.
   * **Ngoài phòng chat:** Khi có tin nhắn từ một peer khác không nằm trong phiên chat hiện tại, luồng nền `_show_events` lập tức thông báo số lượng tin chưa đọc (`get_unread_count`), đồng thời hiển thị nhãn `(X unread)` bên cạnh tên peer trong lệnh `/list`.

4. **Bảo toàn tính năng & An toàn đa luồng (Thread-safety):**
   * Giữ nguyên toàn bộ hoạt động của các lệnh `/list`, `/status`, `/help`, `/quit` từ Milestone 2.
   * Sử dụng `threading.Lock` để đồng bộ trạng thái đối tác đang chat (`partner_id`, `partner_name`) giữa luồng nhập liệu chính và luồng nhận sự kiện nền.