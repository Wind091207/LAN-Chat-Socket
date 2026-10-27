**Quy Trình Làm Việc Nhóm Với Git**

**1. Tải project về máy (Chỉ làm lần đầu)**
Mở Git Bash tại thư mục muốn lưu code và chạy lệnh:
`git clone https://github.com/Wind091207/LAN-Chat-Socket.git`

**2. Cập nhật code mới nhất**
Luôn chạy lệnh này trước khi bắt đầu code mỗi ngày để lấy bản code mới nhất từ chủ repo, tránh xung đột:
`git checkout main`
`git pull origin main`

**3. Quản lý nhánh (Branch)**
Tuyệt đối không code trực tiếp trên nhánh `main`. Mỗi người hoặc mỗi tính năng phải làm trên một nhánh riêng.
* Xem danh sách các nhánh hiện có trên máy: `git branch` 
* Xem toàn bộ nhánh (cả trên GitHub): `git branch -a`
* Tạo nhánh mới và chuyển sang nhánh đó luôn: `git checkout -b <tên_nhánh>` (VD: `git checkout -b update-ui`)
* Chuyển lại sang một nhánh đã có sẵn: `git checkout <tên_nhánh>`

**4. Lưu và đẩy code lên GitHub**
Sau khi code xong một phần, thực hiện tuần tự:
* Đưa file vào hàng đợi: `git add .`
* Đóng gói thay đổi: `git commit -m "Mô tả ngắn gọn tính năng vừa làm"`
* Đẩy nhánh của bạn lên mạng: `git push -u origin <tên_nhánh>`

**5. Gộp code (Pull Request)**
* Sau khi push nhánh lên GitHub, truy cập vào giao diện web của repo.
* Bấm nút **Compare & pull request** để yêu cầu gộp nhánh của bạn vào `main`.
* Đợi các thành viên khác kiểm tra (review) và xác nhận **Merge pull request**.
