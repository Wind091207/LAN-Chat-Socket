# Quy Trình Làm Việc Nhóm Với Git

## 1. Tải project về máy (chỉ làm lần đầu)

Sau khi được mời làm collaborator và chấp nhận lời mời, mở Git Bash/Terminal tại nơi muốn lưu project:

```bash
git clone https://github.com/Wind091207/LAN-Chat-Socket.git
cd LAN-Chat-Socket
```

Đã clone rồi thì không cần clone hoặc `git init` lại.

## 2. Cập nhật code mới nhất

Trước khi làm một nhiệm vụ mới, quay về nhánh `main` và lấy bản mới nhất từ GitHub:

```bash
git checkout main
git pull origin main
```

Nếu đang sửa file dở, nhớ commit hoặc lưu lại trước khi chuyển nhánh. Không nên kéo code khi còn thay đổi dễ gây xung đột.

## 3. Quản lý nhánh (Branch)

Không code trực tiếp trên `main`. Mỗi tính năng/nhiệm vụ làm trên một nhánh riêng.

- Xem nhánh trên máy: `git branch`
- Xem cả nhánh trên GitHub: `git branch -a`
- Tạo và chuyển sang nhánh mới: `git checkout -b <tên_nhánh>`
- Chuyển sang nhánh đã có: `git checkout <tên_nhánh>`

Ví dụ:

```bash
git checkout -b feature/m1-tcp-echo
```

`feature/m1-tcp-echo` chỉ là tên nhánh, không phải đường dẫn thư mục.

## 4. Lưu và đẩy code lên GitHub (Push)

Sau khi làm xong một phần và đã tự chạy thử:

```bash
git status
git add .
git diff --cached
git commit -m "feat: add TCP echo"
git push -u origin feature/m1-tcp-echo
```

- `git status`: xem file nào đã thay đổi.
- `git add .`: chọn các thay đổi để commit. Nhớ kiểm tra, tránh đưa nhầm `.venv`, file cá nhân hoặc tài liệu không được phép chia sẻ.
- `git diff --cached`: xem lại những gì sắp commit.
- `git commit -m "..."`: lưu một mốc thay đổi trên máy.
- `git push -u origin <tên_nhánh>`: đẩy nhánh đó lên GitHub. `-u` thường chỉ cần ở lần push đầu của nhánh; các lần sau có thể dùng `git push`.

Nếu chỉ muốn thêm một file, có thể dùng `git add milestones/Milestone1/tcp_server.py` thay vì `git add .`.

## 5. Gộp code bằng Pull Request (PR)

- Push xong thì vào GitHub của nhóm.
- Bấm **Compare & pull request** (hoặc vào tab **Pull requests → New pull request**).
- Chọn `base: main` và `compare: tên_nhánh_của_mình`.
- Ghi ngắn đã làm gì, đã test ra sao.
- Người khác đọc code, kiểm tra rồi mới chọn **Merge pull request**.

**Push** chỉ đưa code lên nhánh của mình. **Merge** mới đưa thay đổi vào `main`.

Trong lúc chưa có đủ thành viên, nhóm trưởng có thể tự kiểm tra rồi merge; sau này nên để người khác review.

## 6. Sau khi merge xong

Về máy, đồng bộ `main` rồi mới bắt đầu nhiệm vụ tiếp theo:

```bash
git checkout main
git pull origin main
```

Có thể xóa nhánh cũ trên máy sau khi merge:

```bash
git branch -d feature/m1-tcp-echo
```

Làm chức năng mới thì tạo nhánh mới từ `main`, không tiếp tục code trên nhánh cũ.

## 7. Tên hiện trên GitHub sau khi merge

Ví dụ:

- `Merge pull request #1 from Wind091207/docs/milestone1-init`: GitHub tự đặt tên cho **merge commit** của PR số 1, gộp nhánh `docs/milestone1-init` từ tài khoản `Wind091207`.
- `docs: initialize Milestone 1`: tên commit/nội dung PR khi mình tạo README của Milestone 1.

Đây **không phải tên thư mục**. Thư mục vẫn là `milestones/Milestone1/`.

---

**Nhớ:** trước khi code thì cập nhật `main` → tạo nhánh → code/test → commit → push → PR → review/merge → cập nhật lại `main`.
