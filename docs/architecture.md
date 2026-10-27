# Architecture — DRAFT, chưa duyệt/triển khai

## 1. Yêu cầu kiến trúc từ đề

- P2P: **mọi máy chạy cùng chương trình**, đều có khả năng nhận và tạo TCP connections.
- UDP cho discovery/status (mỗi 3s, timeout 10s).
- TCP cho chat và file. UI không bị block khi nhận tin/gửi file.
- Có concurrency và shared-data synchronization (§5.1).

## 2. Sơ đồ logic đề xuất

```text
        Machine A / Python 3                Machine B / Python 3
     ┌────────────────────────┐          ┌────────────────────────┐
     │ CLI ⇄ App/State        │          │ App/State ⇄ CLI        │
     │   │                    │          │                    │   │
     │ UDP discovery/registry │<--UDP--->│ UDP discovery/registry │
     │   │                    │          │                    │   │
     │ TCP acceptor/connector │<--TCP--->│ TCP acceptor/connector │
     │   │      │             │          │             │      │   │
     │  Chat   File transfer  │          │ File transfer   Chat  │
     └────────────────────────┘          └────────────────────────┘
```

**Đây không phải network topology vật lý.** UDP broadcast thường đi trong cùng broadcast domain; máy có thể kết nối qua router/AP LAN. Firewall, Wi-Fi isolation và OS ảnh hưởng khả năng liên lạc.

## 3. Module dependency đề xuất

```text
__main__ -> app/config
app -> cli, discovery, peer_registry, connections, chat, file_transfer, state
chat -> protocol + connections + peer_registry snapshot
file_transfer -> protocol + connections + local file system
cli -> app command dispatcher (không trực tiếp thao tác socket)
discovery -> protocol (UDP parse) -> peer_registry
```

Tránh `discovery <-> chat` import vòng; điều phối qua `app` hoặc interface/callback được nhóm thống nhất.

## 4. Thread model (§5.1): điểm nhóm cần thiết kế

| Nhiệm vụ | Chờ gì? | Ai quản lý? | Dữ liệu shared? |
|---|---|---|---|
| Main | input | A/App | active partner, command results |
| UDP broadcaster | timer 3s | A | status, local port |
| UDP listener | recvfrom | A | peer registry |
| TCP acceptor | accept | B | connection registry |
| TCP receivers | recv on connection | B | histories, unread, UI events |
| File sender per transfer | file/socket IO | C | progress UI; active peer ref |

### Lock plan — CHƯA CHỐT

- Peer registry lock: **A**; lock càng ngắn càng tốt, tạo snapshot rồi thả lock.
- Chat history/unread lock: **B**; thống nhất thứ tự lock với A.
- Console output lock hoặc prompt toolkit patch: **A**.
- File transfers/progress: **C**; không lấy screen lock trong lúc chờ socket/file IO.
- App shutdown signal: **shared**; xác định vòng đời thread và sockets.

Không mặc định daemon threads giải quyết shutdown sạch. Chỉ chốt sau khi thiết kế và thử thực tế.

## 5. Quyết định cần duyệt chung trước khi code

- [ ] Username và peer identity (đặc biệt tên trùng).
- [ ] UDP port, TCP port chọn theo từng instance, địa chỉ broadcast.
- [ ] `PeerSnapshot` fields và thread-safe access.
- [ ] Wire frames và `read_exact`, giới hạn frame.
- [ ] Multiple connections do cả hai peer cùng chủ động mở.
- [ ] Chat và file truyền trên same/different TCP connection.
- [ ] Ai sở hữu `active_partner`, lịch sử chat, unread.
- [ ] Chuyển tiếp UI events và redraw.
- [ ] Graceful shutdown `/leave`, `/quit`.
- [ ] Test thực tế 2 máy và các hạn chế firewall.

Sau khi chốt, ghi decision ID vào [`decisions.md`](decisions.md), mở PR sửa tài liệu và mời mọi owner review.

## 6. Báo cáo sử dụng gì từ tài liệu này?

Khi **đã triển khai thật**, chuyển sơ đồ logic thành sơ đồ module/luồng đúng code; giải thích dữ liệu dùng chung, synchronized access và hoạt động concurrency. Không dùng hình DRAFT như một kết quả hoàn thành.
