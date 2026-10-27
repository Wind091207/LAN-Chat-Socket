# Architecture Decision Log — DRAFT

## DEC-001 — Chọn ngôn ngữ

- **Status:** ACCEPTED (nhóm đã chốt với đại diện nhóm)
- **Decision:** Python 3, dùng `socket` chuẩn của Python cho networking.
- **Reason:** Đề cho phép; nhiều demo Python liên quan; tập trung đạt yêu cầu P2P/TCP/UDP.
- **Open:** phiên bản Python tối thiểu/OS đã test và dependency UI cần được ba thành viên xác nhận.
- **Source:** `LAN_Chat_Socket_Project.docx` mục thông tin đầu đề.

## DEC-002 — Giao diện

- **Status:** PROPOSED — cần cả ba xác nhận.
- **Proposal:** console cho bản đầu, cân nhắc `prompt_toolkit` để preserve line khi đang gõ.
- **Alternatives:** manual redraw, GUI.
- **Constraint:** đề §4.3, UI 15 điểm.
- **Evidence/Test:** T-UI-01, T-UI-02, chưa test.

## DEC-003 — Transport

- **Status:** REQUIRED BY ASSIGNMENT.
- **Decision:** UDP cho discovery/status, TCP cho chat/file.
- **Source:** đề §1, §3.1–3.4.

## DEC-004 — Giao thức ứng dụng / Framing

- **Status:** OPEN — **chưa chốt schema**.
- **Owner:** B, A/C review.
- **Questions:** wire type, header, length encoding, max size, UTF-8, identity, bad frames, file routing.
- **Reference:** `docs/protocol.md`; đề §5.2.

## DEC-005 — Chia connection file và chat

- **Status:** PROPOSED.
- **Proposal:** file dùng TCP connection riêng (giúp chat không bị chặn).
- **Alternative:** multiplex frame file/message trên cùng stream với cơ chế chia chunk và synchronization.
- **Constraint:** đề §3.4 chat còn hoạt động trong lúc gửi file.
- **Test:** T-FILE-02.

## Mẫu ghi quyết định mới

```markdown
## DEC-00N — Tên quyết định

- Status: PROPOSED | ACCEPTED | SUPERSEDED
- Owner / Reviewers:
- Date:
- Assignment requirement (§...):
- Problem:
- Options considered:
- Decision:
- Why:
- Impacted modules/contract:
- Verification/test:
- PR / Issue:
```

**Không xóa quyết định cũ khi đổi.** Đánh `SUPERSEDED` và trỏ tới quyết định thay thế để viết phần *Problems Faced & Solutions* sau này.
