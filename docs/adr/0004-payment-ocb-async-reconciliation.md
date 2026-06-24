# ADR 0004: Thanh toán OCB QR — Đối soát bất đồng bộ & thanh toán trễ

| Trạng thái | Accepted |
| ---------- | -------- |
| Ngày | 2026-06-23 |
| Người quyết định | @tuan.vo |
| Spec | [2026-06-23-payment-reconciliation-design.md](../superpowers/specs/2026-06-23-payment-reconciliation-design.md) |

## Bối cảnh

ZZP cần thu phí đăng ký/gia hạn gói SaaS tự động qua OCB VietQR trên Website. OCB gửi webhook khi có tiền vào; ZZP phải khớp thanh toán với đơn hàng và kích hoạt subscription mà không cần BD/Kế toán xử lý thủ công trên happy path.

Câu hỏi mở lúc brainstorm: đối soát đồng bộ hay bất đồng bộ, xử lý thanh toán sau khi hết hạn 15 phút, BE có thể tự enforce expiry khi OCB không hỗ trợ hay không.

## Quyết định

1. **Đối soát chạy bất đồng bộ** qua queue worker sau khi webhook ingest trả `200` nhanh.
2. **Chính sách thanh toán trễ:** nếu `payment_orders.status = EXPIRED` (hoặc `CANCELLED`) khi webhook khớp `orderCode` + `amount`, chuyển `MANUAL_REVIEW` với `reason_code: LATE_PAYMENT` — **không** tự động kích hoạt subscription.
3. **Hết hạn do BE quyết định:** `expires_at = created_at + 15 phút` trên đơn; `ExpiryJob` chuyển `WAITING_PAYMENT → EXPIRED` độc lập với TTL QR phía OCB.
4. **Khóa khớp:** `orderCode` (từ description webhook) + `amount` chính xác (VND integer); đơn phải `WAITING_PAYMENT` và `now() <= expires_at` mới auto `PAID`.

## Hệ quả

### Tích cực

- Endpoint webhook phản hồi nhanh; OCB retry an toàn.
- Không kích hoạt subscription nhầm trên đơn đã hết hạn.
- Lối xử lý vận hành rõ cho case biên qua `MANUAL_REVIEW`.

### Tiêu cực

- Cần hạ tầng queue (Redis/BullMQ hoặc tương đương).
- Eventual consistency: Seller có thể chờ vài giây sau khi ngân hàng báo thành công mới thấy `PAID` trên Web.
- BD/Kế toán phải xử lý `MANUAL_REVIEW` thủ công ở phase 1 (chưa có admin UI).

## Phương án đã xem xét

| Phương án | Bị loại vì |
| --------- | ---------- |
| Đối soát đồng bộ trong webhook handler | Lock DB, khó scale, lỗi chặn ACK |
| Auto-kích hoạt khi thanh toán trễ nếu khớp khóa | Rủi ro kích hoạt sai kỳ; user chọn phương án an toàn |
| Ghi ledger orphan không kích hoạt gói | Phức tạp hơn; hoãn phase 2 |

## Việc tiếp theo

- Hoàn thành [spike tích hợp OCB](../superpowers/specs/2026-06-23-ocb-integration-spike.md) trước credential production.
- Phase 2: admin UI xử lý `MANUAL_REVIEW` và poll API check-transaction tùy chọn.
