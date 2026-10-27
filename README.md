# LAN Chat & File Sharing — Socket Programming (Python 3)

> **Trạng thái: PLANNING — chưa có ứng dụng hoàn chỉnh và chưa có tính năng nào được xác nhận chạy.**
>
> **Nguồn yêu cầu duy nhất để nghiệm thu:** `LAN_Chat_Socket_Project.docx` (5 trang, đặc biệt §3–§9). Các slide, code demo và kiến trúc trong repo là tài liệu tham khảo hoặc đề xuất triển khai, **không thay thế đề gốc**.

## 1. Mục tiêu và phạm vi

Nhóm **3 sinh viên** xây dựng ứng dụng **peer-to-peer (P2P)** trên mạng LAN/Wi-Fi: **mỗi máy chạy cùng một chương trình và vừa có thể chủ động kết nối TCP, vừa lắng nghe kết nối đến**. Phần hiện diện/trạng thái sử dụng **UDP**; chat và truyền file dùng **TCP**.

- **Ngôn ngữ đã chốt:** Python 3; giao tiếp qua `socket` chuẩn của Python (native Socket API).
- **Giao diện:** ưu tiên console để triển khai ban đầu; đề **cho phép console hoặc GUI**, nhóm cần ghi quyết định cuối cùng trong [`docs/decisions.md`](docs/decisions.md).
- **Hệ điều hành và phiên bản Python tối thiểu:** chưa chốt/kiểm thử; không mặc định mọi máy đều tương thích.
- **Môi trường thử:** có thể chạy nhiều instance trên một máy để phát triển; **demo cuối phải chạy trên ít nhất 2 máy** theo §7.
- **Không thuộc yêu cầu bắt buộc:** HTTP/Web server, database, login, mã hóa đầu cuối, group-chat broadcast, GUI đồ họa phức tạp. Chỉ thêm khi đã hoàn thành phần lõi và nhóm thống nhất.

**Điểm bắt đầu:** đọc [Bản đồ yêu cầu](docs/requirements.md) → [Trách nhiệm từng module](docs/modules.md) → [Kiến trúc](docs/architecture.md) → [Đặc tả protocol (DRAFT)](docs/protocol.md) → [Test plan](docs/testing.md).

## 2. Rubric chính thức — 100 điểm (§8)

| Hạng mục | Điểm | Người điều phối chính | Cách xác nhận |
|---|---:|---|---|
| UDP discovery, online list, status | **15** | A | UDP presence, timeout, `/list`, `/status` + Wireshark |
| TCP chat: bất kỳ lúc nào, nhiều peer | **20** | B | Hai chiều, đa peer, unread, chuyển đối tác |
| File transfer + progress | **15** | C | File nhận đầy đủ, % đúng, chat không bị chặn |
| Console input không bị phá **hoặc GUI** | **15** | A | Nhận tin trong lúc nhập, văn bản đang gõ không mất |
| Protocol design & message framing | **10** | B (A/C duyệt) | Đặc tả wire format, đọc đủ bytes, xử lý frame phân mảnh |
| Error handling & stability | **10** | C điều phối; **A/B/C tự xử lý lỗi module mình** | Test disconnect, timeout, malformed frame, file dở, lệnh sai |
| Report | **10** | **Cả ba** | Báo cáo 5–10 trang, đủ các phần §7 |
| Demo & code quality | **5** | **Cả ba** | Demo 10 phút trên ≥2 máy; giải thích được hệ thống |
| **Tổng** | **100** | | |

> Điểm ở đây là **rubric nhóm**, không phải điểm phân bổ cá nhân. Owner là người chịu trách nhiệm giao tính năng; reviewer là người kiểm tra PR và bằng chứng trước khi merge.

## 3. Danh sách chức năng bắt buộc (§3–§5)

### 3.1. UDP Discovery & Status — A

- [ ] **UDP-01** Broadcast presence **mỗi 3 giây** tới UDP port cố định (ví dụ 9999).
- [ ] **UDP-02** Lắng nghe UDP trên port đó; lưu **name, IP, TCP port, status** của peer.
- [ ] **UDP-03** Peer không phát hiện được trong **10 giây** sẽ bị loại khỏi danh sách.
- [ ] **UDP-04** Thông báo khi peer online hoặc offline.
- [ ] **STATUS-01** Cho phép `online` / `away`, gửi status trong presence và hiển thị trên `/list`.

### 3.2. TCP Chat — B

- [ ] **CHAT-01** `/chat <name|number>` chọn peer online và mở TCP connection.
- [ ] **CHAT-02** Gửi **mỗi dòng một message**, nhiều dòng tùy ý; **có thể gửi bất kỳ lúc nào**.
- [ ] **CHAT-03** Tin đến hiển thị **ngay khi người dùng đang gõ**.
- [ ] **CHAT-04** Tin từ người **không phải active partner** được lưu và báo **unread count**; chuyển sang họ có thể đọc tin.
- [ ] **CHAT-05** Quản lý được **nhiều peer đồng thời**, không chỉ một cặp chat tuần tự.

### 3.3. TCP File Transfer — C

- [ ] **FILE-01** `/send <file>` gửi file cho **active chat partner** bằng TCP.
- [ ] **FILE-02** Hiển thị **progress (%)**.
- [ ] **FILE-03** Lưu file nhận trong **`downloads/`**.
- [ ] **FILE-04** Chat **vẫn hoạt động** trong khi truyền file (sender ở luồng/cơ chế đồng thời riêng).

### 3.4. Lệnh giao diện (§4.1) — A điều phối CLI, các owner thực hiện nghiệp vụ

- [ ] `/list` — số thứ tự, tên, IP, trạng thái (A).
- [ ] `/chat <name|number>` — kết nối/chuyển chat (B).
- [ ] `<any text>` — nhắn cho người đang chat (B).
- [ ] `/send <file>` — gửi file (C).
- [ ] `/leave` — kết thúc chat hiện tại (B).
- [ ] `/status <online|away>` — trạng thái UDP (A).
- [ ] `/help` — tất cả lệnh, hướng dẫn lỗi nhập (A).
- [ ] `/quit` — đóng chương trình an toàn (A/B/C tích hợp).

### 3.5. Yêu cầu kỹ thuật (§4.3, §5)

- [ ] **UI-01** Tin đến không xóa hỏng văn bản đang gõ: xóa dòng, in tin, vẽ lại dòng nhập hoặc chọn GUI tương đương.
- [ ] **UI-02** Có đồng bộ thao tác in console giữa các thread.
- [ ] **THREAD-01** Có các tác vụ main input, UDP broadcaster/listener, TCP acceptor, receivers và file sender (hoặc mô hình đồng thời khác được đề cho phép); shared peer list, histories, unread counters được đồng bộ.
- [ ] **PROTO-01** **Tự thiết kế** application-layer protocol, không mặc định copy ví dụ `HELLO|...`, `MSG|...`, `FILE|...`, `BYE|` là bắt buộc.
- [ ] **PROTO-02** TCP framing có header cho biết **loại và độ dài** dữ liệu; receiver **lặp `recv()` đến khi đủ byte**; phân biệt byte UTF-8 với ký tự.
- [ ] **ERR-01** Peer đóng kết nối/crash → báo lỗi và đưa về prompt phù hợp.
- [ ] **ERR-02** Kết nối tới peer vừa offline → báo lỗi, không crash.
- [ ] **ERR-03** File không tồn tại hoặc truyền bị gián đoạn → báo lỗi và **xóa file dở**.
- [ ] **ERR-04** Lệnh không hợp lệ → thông báo/hướng dẫn ngắn.

**Danh sách ID chi tiết, cách test và trạng thái:** [`docs/requirements.md`](docs/requirements.md). Checkbox trong README chỉ là **tổng quan**; việc hoàn thành phải có test/evidence trong docs, không tick chỉ vì đã push code.

## 4. Module dự kiến, owner & reviewer

> **Chưa tạo mã nguồn của các module này.** Tên file là gợi ý cấu trúc để chia việc; các public interface chỉ chốt sau khi ba người duyệt hợp đồng dữ liệu.

| Module `src/lanchat/` | Owner | Reviewer | Chức năng / phạm vi | Cần học từ đâu |
|---|---|---|---|---|
| `discovery.py` | A | C | UDP send/listen, presence mỗi 3s, online/offline events | `udp_broadcast_demo.py`, `HDLT_Socket.pdf`, Seminar PDF pp. 10–12 |
| `peer_registry.py` | A | C | Bảng peer, `last_seen`, timeout 10s, online/away, `/list` data | Đề §3.1–3.2, `udp_broadcast_demo.py` |
| `cli.py` | A | C | Nhập và phân luồng lệnh; redraw, print lock, `/help` | `option_a_prompt_toolkit.py`, `option_b_manual_redraw.py`, `chat_redraw.cpp`, đề §4.1–4.3 |
| `protocol.py` | B | A + C | Đóng/giải frame, định dạng wire, read-exactly, validation | Đề §5.2; `PythonNetBinder.pdf` phần partial reads/data reassembly; Python Socket HOWTO |
| `connections.py` | B | A | TCP listen/accept/connect, peer identification, lifecycle, connection map | Seminar PDF pp. 8–9, 17–24; `02_client.py`/`02_server.py` |
| `chat.py` | B | A | MSG send/receive, full duplex, active partner, history, unread, `/chat`, `/leave` | Seminar PDF pp. 13–24, `03_server.py` (tham khảo concurrency, **khác P2P**) |
| `file_transfer.py` | C | B | `/send`, metadata/chunk, file thread, progress, downloads, file dở | Đề §3.4, §5.2–5.3; `PythonNetBinder.pdf` phần data reassembly / partial write |
| `app.py`, `state.py`, `config.py` | A+B+C | Cross-review | Ghép module, trạng thái dùng chung, cấu hình, startup/shutdown | Đề §5.1; [`docs/architecture.md`](docs/architecture.md) |
| `__main__.py` | Cả ba | Cross-review | Điểm chạy ứng dụng và xử lý tham số khởi động (đề có ví dụ `--name`, `--port` trong hint) | `argparse`, đề §4.2, §9 |

**Chi tiết từng module:** [`docs/modules.md`](docs/modules.md), gồm input/output, contract phải chốt, test, nguồn học và bằng chứng cho báo cáo.

## 5. Milestones chính thức (§6) và định nghĩa hoàn thành

| Milestone | Phạm vi | Checkpoint **trong đề** | Tài liệu phải cập nhật |
|---|---|---|---|
| **M1** | TCP echo client/server; UDP send/receive | Demo được **cả hai chương trình** | `docs/devlog.md`, `docs/testing.md` |
| **M2** | UDP discovery, online list, `/list`, `/status` | Peer hiện/mất trên **2+ máy** | `docs/protocol.md` (UDP), `docs/architecture.md`, README sau test |
| **M3** | TCP chat, `/chat`, `/leave`, framing, thread hoặc select/poll | Hai người chat **hai chiều** | `docs/protocol.md` (TCP), `docs/modules.md`, `docs/testing.md` |
| **M4** | Nhận tin lúc đang gõ; file transfer + progress | **Gửi file trong lúc chat** | `docs/testing.md`, README sau test, bằng chứng |
| **M5** | Xử lý lỗi, testing, report, demo | **Nộp bài cuối** | Report, Wireshark, README cách cài/chạy/test |

**Trước M1 (hoạt động quản lý nội bộ, KHÔNG phải milestone của đề):** duyệt requirements, kiến trúc và bản protocol DRAFT, tạo repo, giao owner/reviewer.

## 6. Sản phẩm phải nộp (§7)

- [ ] **Source code + README**: hướng dẫn **install, run, test** (chỉ thêm hướng dẫn đã kiểm thử).
- [ ] **Report 5–10 trang**: kiến trúc, mô hình thread, giao thức, khó khăn và giải pháp.
- [ ] **Wireshark screenshots**: gói **UDP broadcast** và **TCP three-way handshake (SYN/SYN-ACK/ACK)**, kèm giải thích ngắn.
- [ ] **Live demo 10 phút** trên **ít nhất 2 máy tính**.

Đề cho phép **test nhiều instance trên một máy** khi phát triển (§9) nhưng **không thay thế** điều kiện demo hai máy (§7).

## 7. Tài liệu ghi chép và trách nhiệm cập nhật

| Tệp | Dùng để làm gì? | Quy tắc cập nhật |
|---|---|---|
| [`docs/requirements.md`](docs/requirements.md) | Traceability: requirement → owner → test → evidence → PR → report | Owner cập nhật, reviewer xác nhận |
| [`docs/modules.md`](docs/modules.md) | Chức năng từng module + interface giữa A/B/C + tài liệu học | Người sở hữu module; thay đổi giao diện cần cả nhóm duyệt |
| [`docs/architecture.md`](docs/architecture.md) | P2P architecture, shared state, thread model | Cả ba duyệt trước M2/M3 |
| [`docs/protocol.md`](docs/protocol.md) | Bản đặc tả wire format và cách parser | B viết DRAFT; A/C duyệt; đổi format cần PR chung |
| [`docs/decisions.md`](docs/decisions.md) | Log các quyết định, lý do, lựa chọn khác | Người đề xuất ghi khi quyết định thay đổi |
| [`docs/testing.md`](docs/testing.md) | Test plan, kết quả, thiết bị, evidence | Người chạy test ghi kết quả thật |
| [`docs/devlog.md`](docs/devlog.md) | Nhật ký làm việc, lỗi thực tế, giải pháp | Mỗi người sau mỗi buổi/PR |
| [`docs/team.md`](docs/team.md) | Member/owner/reviewer, cách review, branch policy | Cả nhóm thống nhất |
| [`docs/report-plan.md`](docs/report-plan.md) | Dàn ý 5–10 trang, gom tư liệu từ mỗi module | Cả nhóm viết; C điều phối hợp nhất |

**Nguồn tài liệu để học:** [`docs/learning-map.md`](docs/learning-map.md) (file demo giảng viên + tài liệu Python chính thức). Không mặc định đưa file giảng viên vào repo public.

## 8. Git/GitHub workflow thống nhất

1. Mỗi nhiệm vụ tạo **GitHub Issue** có `Requirement ID`, owner, reviewer, acceptance criteria và test ID.
2. Owner cập nhật từ `main`, tạo **feature branch**, ví dụ `feature/udp-discovery`.
3. Viết code + test + ghi vào `docs/devlog.md` và `docs/testing.md`; nếu đổi contract, cập nhật docs trong **cùng PR**.
4. Owner tự chạy test, `git status`, `git diff`, commit từng thay đổi có ý nghĩa rồi push branch.
5. Mở **Pull Request**, gắn Issue và ghi rõ test/evidence. Reviewer đọc code, so với **DOCX §3–§5**, yêu cầu sửa hoặc approve.
6. Chỉ merge vào `main` sau review và test; cập nhật README cho những tính năng **đã kiểm thử chạy**, không ghi tính năng dự định thành tính năng đã xong.

**Ma trận review:** A → B, B → C, C → A. Protocol/API dùng chung: A + B + C cùng duyệt.

**Ví dụ lệnh sau khi clone repository:**

```bash
git switch main
git pull origin main
git switch -c feature/udp-discovery
# tự thay đổi code/tài liệu và kiểm thử
git status
git diff
git add src/ docs/
git commit -m "feat: add UDP presence broadcaster"
git push -u origin feature/udp-discovery
```

Nếu chưa có `src/`, **đừng chạy `git add src/`**; thay bằng tên file đã thực sự tạo. Không commit file chưa hiểu hoặc chưa kiểm tra `git diff`.

**GitHub có thể tự tạo `.gitignore` khi chọn template `Python` trong lúc tạo repo.** Nếu đã có thì sửa **chính file đó**, không tạo bản thứ hai. Trong bộ tài liệu này cũng có `.gitignore` sẵn. `.gitignore` không tự bỏ theo dõi những file đã commit trước đó.

Xem quy định công việc nhóm trong [`docs/team.md`](docs/team.md); mẫu Issue và PR đã có trong `.github/`.

## 9. Cách cài, chạy và kiểm thử

> **Chưa có chương trình ứng dụng để chạy.** Phần này sẽ được thêm **sau khi M1/M2 đã chạy thật** trên môi trường nhóm, có lệnh chính xác, dependency được xác minh và kết quả test. Không tự khẳng định `python -m lanchat ...` hoạt động khi chưa có source.

Thông tin phải hoàn thiện trước khi nộp:

- [ ] Phiên bản Python và hệ điều hành **đã kiểm thử**.
- [ ] Cách cài dependency từ `requirements.txt` nếu có.
- [ ] Cách chạy peer A và peer B ở hai máy với username/TCP port khác nhau.
- [ ] Cách dùng tám lệnh giao diện.
- [ ] Cách chạy test và tái hiện các tình huống lỗi.
- [ ] Firewall, UDP broadcast, các giới hạn đã biết.

## 10. Việc đầu tiên của cả nhóm

- [ ] Điền tên ba người vào [`docs/team.md`](docs/team.md).
- [ ] Cả ba đọc **DOCX gốc** và duyệt [`docs/requirements.md`](docs/requirements.md).
- [ ] Chốt console/GUI, phiên bản Python, hệ điều hành demo trong [`docs/decisions.md`](docs/decisions.md).
- [ ] Viết bản nháp **protocol** và **shared data contract**, duyệt chung trước khi code độc lập.
- [ ] Tạo GitHub Issues M1; mỗi người chạy TCP/UDP demo nhỏ; ghi **đã thử / chưa thử** rõ ràng.
- [ ] Sau M1, làm M2 rồi M3/M4/M5 theo thứ tự và test liên tục.

---

**Tài liệu gốc được giảng viên cung cấp:** `LAN_Chat_Socket_Project.docx`; tài liệu tham khảo thêm gồm `Seminar_Socket Programming.pdf`, `Gioithieu_Huongdan_DoAnSocket.pdf`, `udp_broadcast_demo.py`, `option_a_prompt_toolkit.py`, `option_b_manual_redraw.py`, `chat_redraw.cpp`, `HDLT_Socket.pdf`, `PythonNetBinder.pdf`, `01_*` đến `03_*`, `Demo_CSocket_thread`, `Seminar-Socket.ppt`. Những thư mục chỉ biết qua ảnh **chưa được audit source code**.
