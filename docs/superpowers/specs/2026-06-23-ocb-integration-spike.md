# Checklist Spike Tích hợp OCB

| Thuộc tính | Giá trị |
| ---------- | ------- |
| **Trạng thái** | Chưa bắt đầu — điền khi chạy UAT |
| **Thiết kế** | [2026-06-23-payment-reconciliation-design.md](./2026-06-23-payment-reconciliation-design.md) |
| **Owner** | @tuan.vo |
| **Môi trường** | OCB UAT / sandbox |

Chạy checklist này **trước** khi triển khai logic đối soát webhook lên production. Ghi kết quả vào cột **Kết quả**; đính kèm bằng chứng (screenshot, log request/response) ở cột **Bằng chứng**.

---

## Điều kiện tiên quyết

- [ ] Tài khoản merchant OCB đã cấp cho ZZP UAT
- [ ] API credentials (client id/secret hoặc cert) lưu trong secrets manager
- [ ] Webhook URL đã đăng ký: `POST https://<uat-host>/webhooks/ocb/payment`
- [ ] Tài khoản Seller test trên ZZP UAT
- [ ] Log sink cho raw request/response OCB (ẩn secret)

---

## Các bài test spike

| # | Câu hỏi | Cách test | Tiêu chí pass | Kết quả | Bằng chứng |
| - | ------- | --------- | ------------- | ------- | ---------- |
| 1 | QR gen có echo `orderCode` trong `description` webhook không? | Tạo đơn → chuyển đúng số tiền → capture body webhook | `description` hoặc `content` chứa cùng `orderCode` với đơn | | |
| 2 | Seller thanh toán được bằng **app OCB**, **MoMo**, **app NH khác**? | Quét cùng QR bằng 3 app | Ít nhất OCB + một app khác chuyển thành công | | |
| 3 | Độ trễ webhook sau khi thanh toán thành công? | Đo từ UI ngân hàng báo thành công đến khi nhận webhook | Ghi p50/p95; mục tiêu phase 1 dưới 30s | | |
| 4 | Sai số tiền — webhook thế nào? | Cố ý chuyển ±1 VND | Webhook về; amount ≠ đơn → đối soát → MANUAL_REVIEW | | |
| 5 | Thanh toán 2 lần cùng QR? | Thử chuyển lần 2 trên cùng QR | Webhook thứ 2 bỏ qua hoặc MANUAL_REVIEW; không kích hoạt subscription 2 lần | | |
| 6 | Thanh toán sau **>15 phút**? | Đợi đơn EXPIRED trên DB ZZP rồi mới chuyển | Ghi: tiền có vào không? payload webhook? có orderCode không? | | |
| 7 | Có API hủy/vô hiệu QR không? | Đọc tài liệu OCB + gọi thử nếu có | Ghi API hoặc xác nhận "không hỗ trợ" | | |
| 8 | `expiresAt` trong request gen QR OCB? | Gửi field expiry tùy chọn; so sánh hành vi | Ghi OCB có tôn trọng TTL tùy chỉnh không | | |
| 9 | Cơ chế chữ ký webhook? | Verify chữ ký với payload test OCB | Ghi thuật toán, tên header, dung sai thời gian | | |
| 10 | API tra cứu giao dịch theo orderId? | Gọi API reconcile/query nếu có trong tài liệu | Ghi endpoint cho fallback poll phase 2 | | |

---

## Mẫu ghi kết quả (copy cho từng test)

```markdown
### Test N: <tiêu đề>
- **Ngày:**
- **Người test:**
- **Kết quả:** PASS | FAIL | PARTIAL
- **Ghi chú:**
- **Mẫu webhook (đã ẩn thông tin nhạy cảm):**
```json
{}
```
```

---

## Phê duyệt

| Vai trò | Tên | Ngày | Đã duyệt |
| ------- | --- | ---- | -------- |
| Tech lead | | | [ ] |
| PM | | | [ ] |

Sau khi phê duyệt, chép kết luận vào [ADR 0004](../../adr/0004-payment-ocb-async-reconciliation.md) và cập nhật mục 10 của design spec nếu có thay đổi quyết định.
