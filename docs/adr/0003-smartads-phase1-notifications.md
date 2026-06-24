# ADR 0003: Phase 1 — Phạm vi notification (P1-BE-22 / P1-BE-23)

- **Trạng thái:** Proposed (chờ PM chốt kênh & provider)
- **Ngày:** 2026-06-11
- **Phạm vi:** BE notification outbox + lịch sử seller; không bắt buộc hợp đồng SMS/Zalo ngay Phase 1

## Bối cảnh

Backlog định nghĩa **P1-BE-23** (bảng + API `seller_notifications`) và **P1-BE-22** (worker gửi SMS / Zalo OA / Email). Provider bên ngoài có thể chưa có hợp đồng hoặc sandbox sẵn trong sprint đầu.

## Quyết định (mặc định triển khai Phase 1)

**Phase 1 tối thiểu (bắt buộc trong scope task):**

1. **P1-BE-23:** Migration + `GET /api/v1/smart-ads/notifications` (phân trang) + `PATCH …/read`; producer ghi hàng `QUEUED` / `SENT` / `FAILED` cho sự kiện nội bộ (OAuth sắp hết hạn, publish camp fail, v.v.).

2. **P1-FE-11:** Trung tâm thông báo **in-app** đọc API trên.

3. **P1-BE-22:** Worker đọc queue; **mặc định env dev / staging:** gửi kênh **log + optional email dev** (cấu hình qua env). **Không** bật SMS / Zalo OA production cho đến khi có credential và PM bật feature flag.

**Phase 1.5 (sau khi có provider + PM):** bật kênh `SMS`, `ZALO_OA`, `EMAIL` production trong worker với template và rate limit; cập nhật ADR này thành **Accepted** với bảng kênh đã chốt.

## Hệ quả

- Sprint không bị chặn bởi vendor Zalo/SMS; vẫn có audit trail notification trong DB.
- Khi bật kênh thật: thêm biến môi trường, secret store, và test E2E theo kênh.

## Checklist PM

- [ ] Xác nhận Phase 1 chỉ in-app + log (mặc định ADR), **hoặc**
- [ ] Chỉ định kênh bắt buộc P1 (vd. email production) + provider + SLA.

## Tham chiếu

- [docs/SmartAds-Phase1-Backlog.md](../SmartAds-Phase1-Backlog.md) — P1-BE-22, P1-BE-23, P1-FE-11
