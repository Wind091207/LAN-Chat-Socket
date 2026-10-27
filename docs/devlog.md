# Engineering Devlog — nhật ký kỹ thuật cho báo cáo

> Mỗi người tự ghi sau buổi học/code/test, ưu tiên sự thật: việc đã làm, điều chưa làm, lỗi và bằng chứng. Không dùng để chép lại lý thuyết từ slide.

## Mẫu ghi (copy cho mỗi buổi / mỗi PR)

```markdown
### YYYY-MM-DD — A/B/C — [Module / Issue #...]

**Related requirement IDs:**
**Branch / Commit / PR:**
**Study/reference used:** (tên tài liệu, trang/mục)

**Implemented or investigated:**
- ...

**Decision / Reason:**
- ...

**Problems observed:**
- ...

**What fixed it / Evidence:**
- ... (nếu chưa sửa, ghi PENDING)

**Tests run:**
- T-...: NOT RUN / PASS / FAIL (môi trường)

**Next action / Blockers:**
- ...
```

## Quy tắc tối giản để không quá tải

- Mỗi PR nên có ít nhất một entry hoặc link tới Issue ghi lại tiến độ/kiểm thử.
- Lỗi quan trọng (firewall, UTF-8 length, fragmented `recv`, race condition, disconnect, partial files) ghi lại ngay khi gặp.
- Không cần ghi từng dòng code; chỉ ghi **vì sao**, **thử thế nào**, **kết quả là gì**.
- Khi viết báo cáo, rút nội dung có bằng chứng từ devlog và testing; tránh kể những khó khăn chưa thực sự gặp.

## Nhật ký thật của nhóm

_Chưa có entry; sẽ thêm sau khi bắt đầu làm việc._
