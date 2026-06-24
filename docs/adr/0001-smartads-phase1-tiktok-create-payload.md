# ADR 0001: Phase 1 — Payload tạo GMV Max (SRS Campaign Engine vs SmartAds RunAllVideos)

- **Trạng thái:** Proposed (chờ PM / Tech lead ký xác nhận)
- **Ngày:** 2026-06-11
- **Phạm vi:** Phase 1 TikTok Parity — `POST /campaign/gmv_max/create/` và ngân sách khởi tạo

## Bối cảnh

Hai nguồn tài liệu nội bộ mô tả khác nhau phần **tạo / khởi tạo** chiến dịch GMV Max:

1. **[SRS-Campaign-Engine.md](../SRS-Campaign-Engine.md)** (Phase 1 tạo camp): `budget` = **20%** `max_daily_budget` (MDB), `roas_bid` từ **ROAS hòa vốn**, `product_source` = `ALL_PRODUCTS`, `video_source` = `ALL_VIDEOS`, `promotion_type` = `PRODUCT_SALE`, `budget_mode` = `BUDGET_MODE_DAY` — nhấn mạnh **Target ROI** / parity cấu hình với tài liệu Campaign Engine.

2. **[SmartAds-RunAllVideos-Flow.md](../SmartAds-RunAllVideos-Flow.md)** (flow tối ưu): trên TikTok campaign luôn **Target ROI** (ROAS bid); **72h learning** là cửa sổ ZZP không áp ma trận Phase 2. Công thức **Budget_initial** khác SRS (vd. **40%** MDB nếu MDB &lt; 2.000.000đ, có sàn tối thiểu), sau đó vòng lặp 24h điều chỉnh ROI×DB.

[PRD-SmartAds-v2.md](../PRD-SmartAds-v2.md) Phase 1 yêu cầu parity TikTok và ngân sách khởi tạo an toàn; PRD không ghi chi tiết payload TikTok từng field.

## Quyết định (mặc định triển khai kỹ thuật cho đến khi PM đổi)

**Cho mã nguồn và contract API ZZP Phase 1, mặc định bám [SRS-Campaign-Engine.md](../SRS-Campaign-Engine.md)** cho lệnh tạo camp lần đầu trên TikTok:

- Ngân sách ngày gửi TikTok = **20% MDB** (theo SRS).
- `roas_bid` = **ROAS_be** từ cost table.
- `ALL_PRODUCTS` / `ALL_VIDEOS` như SRS Phase 1, trừ khi PM chọn CUSTOMIZED trong backlog wizard.

**[SmartAds-RunAllVideos-Flow.md](../SmartAds-RunAllVideos-Flow.md)** được coi là **đặc tả Phase 2 (Optimization Engine)** — Target ROI + learning 72h (chính sách ZZP), ma trận ROI×DB, `Budget_initial` 20%/40%, v.v. **không** tự động áp vào payload `create` Phase 1 cho đến khi có ADR sửa đổi hoặc PM chốt “một luồng thống nhất” gộp create + learning.

## Hệ quả

- BE có thể implement **P1-BE-09** ổn định theo SRS; FE wizard mô tả “Budget_initial / 20% MDB” nhất quán với SRS.
- Khi PM chọn **align với RunAllVideos** cho create: cập nhật ADR này (Accepted / Superseded), đồng bộ SRS snippet và test acceptance **P1-BE-09**.

## Checklist PM / Tech lead

- [ ] Xác nhận giữ mặc định SRS cho Phase 1 create, **hoặc**
- [ ] Chọn luồng RunAllVideos cho create (ghi rõ: `roas_bid` / Target ROI, % MDB, thời điểm bật ma trận 24h sau learning) và cập nhật tài liệu contract.

## Tham chiếu

- [docs/SRS-Campaign-Engine.md](../SRS-Campaign-Engine.md)
- [docs/SmartAds-RunAllVideos-Flow.md](../SmartAds-RunAllVideos-Flow.md)
- [docs/PRD-SmartAds-v2.md](../PRD-SmartAds-v2.md)
- [docs/SmartAds-Phase1-Backlog.md](../SmartAds-Phase1-Backlog.md) — P1-BE-09
