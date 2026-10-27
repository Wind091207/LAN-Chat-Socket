# Report Plan — 5–10 trang (chưa viết báo cáo hoàn chỉnh)

**Nguồn bắt buộc:** `LAN_Chat_Socket_Project.docx` §7 yêu cầu báo cáo **5–10 trang** gồm **architecture, thread model, protocol format, problems faced and solutions**. Báo cáo phải mô tả **cái nhóm đã xây dựng và kiểm thử**, không chép lại nguyên seminar.

## Dàn ý mục tiêu 8–9 trang (điều chỉnh trang bìa/tài liệu tham khảo theo yêu cầu giảng viên)

| Mục | Nội dung bắt buộc/chứng cứ gợi ý | Người soạn đầu | Nguồn dữ liệu thực |
|---|---|---|---|
| 1. Introduction | Bài toán, P2P, UDP vs TCP, công nghệ Python3, phạm vi | Cả ba | DOCX §1–2, `decisions.md` |
| 2. Architecture | Peer vừa client vừa server, module diagram, data flow | Cả ba | `architecture.md`, PR tích hợp |
| 3. UDP Discovery & Status | Broadcast 3s, peer table, timeout 10s, `/list`, `/status` | **A** | code A, T-UDP-01..04 |
| 4. TCP Chat / Many Peers | `/chat`, `/leave`, full-duplex, unread count, connection lifecycle | **B** | code B, T-TCP-01..03 |
| 5. App Protocol / Framing | Spec **đã chốt**, header type+length, read exact, UTF-8, handling bad frames | **B**, A/C duyệt | `protocol.md`, T-PROTO-* |
| 6. Thread Model + UI | Main, broadcaster/listener, acceptor/receiver, file thread; locks, input redraw | **A+B** | code, T-UI-*, T-RACE-01 |
| 7. File Transfer | `/send`, metadata, progress, downloads, concurrent chat, incomplete file | **C** | code C, T-FILE-*, T-ERR-03 |
| 8. Tests + Wireshark | Test matrix tóm tắt; ảnh UDP broadcast và TCP SYN/SYN-ACK/ACK | **C gom**, A/B chụp | `testing.md`, `evidence/` |
| 9. Difficulties, Solutions, Conclusion | Lỗi **đã thực sự gặp**, biện pháp, đánh giá giới hạn, kết luận | **Cả ba** | `devlog.md`, issues, fixes |

> Đây là **bố cục đề xuất**, không phải mẫu báo cáo bắt buộc từ giảng viên. Báo cáo phải gói trong **5–10 trang** theo yêu cầu; cần xác nhận trang bìa/phụ lục có được tính vào giới hạn hay không nếu giảng viên có hướng dẫn bổ sung.

## Checklist nghiệm thu báo cáo

- [ ] 5–10 trang, trình bày rõ tên đề tài/nhóm/công nghệ.
- [ ] Đúng **kiến trúc đã code** (không nói server trung tâm khi app P2P).
- [ ] Có sơ đồ **threads / concurrency** và lock shared state.
- [ ] Có **wire format được nhóm chốt** với type/length, receiver đọc đủ bytes.
- [ ] Có mô tả đầy đủ discovery 3s, timeout 10s, online/away, full-duplex, unread, file/progress/downloads/UI.
- [ ] Có **khó khăn thực tế** và cách giải quyết có nguồn từ devlog/test.
- [ ] Có tóm tắt kết quả tests trên **hai máy**, không giả mạo Passed.
- [ ] Có bằng chứng/giải thích **UDP broadcast** và **TCP three-way handshake** (ảnh Wireshark cũng là deliverable riêng).
- [ ] Những chức năng chưa đạt phải được ghi thành limitation, không hứa đã xong.
- [ ] Cả ba đọc bản cuối, reviewer khác người viết phần đó kiểm tra.

## Thu tư liệu vào report theo milestone

| Mốc | Tài liệu cần thu ngay | Đưa vào report |
|---|---|---|
| M0 | Architecture sơ bộ, decisions, contract | Introduction/Architecture sau khi chốt |
| M1 | Lệnh chạy TCP/UDP, vấn đề setup | Phương pháp và khó khăn setup |
| M2 | Peer screenshots, UDP Wireshark, timeout tests | Discovery, networking evidence |
| M3 | Protocol final, message framing tests, TCP handshake | TCP Chat/Protocol |
| M4 | Input preserve, file progress, saved file evidence | UI/File |
| M5 | Failure matrix, tests 2 máy, 10-minute demo | Validation/Conclusion |

## Không thuộc báo cáo hoặc không nên lạm dụng

- Không sao chép toàn bộ code vào báo cáo 5–10 trang; ưu tiên sơ đồ, pseudocode nhỏ, test result.
- Không ghi “đã thành công” nếu vẫn có `NOT RUN` hoặc lỗi chưa giải quyết.
- Không tạo thêm yêu cầu HTTP/Web server/database ngoài đề.
