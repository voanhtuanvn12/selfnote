# ADR 0002: Campaign do Seller tạo trên TikTok — mirror + read-only (BR-2)

- **Trạng thái:** Accepted
- **Ngày:** 2026-06-11
- **Phạm vi:** BE P1-BE-03, P1-BE-13, P1-BE-14, P1-BE-16; FE dashboard/chi tiết

## Bối cảnh

[PRD-SmartAds-v2.md](../PRD-SmartAds-v2.md) **BR-2:** ZZP không được sửa / tắt các chiến dịch Seller đã tự tạo trên TikTok; chỉ quản lý camp do ZZP tạo.

Seller cần **một dashboard** trong ZZP thấy toàn bộ GMV Max (camp ZZP + camp đã có trên TikTok).

## Quyết định

1. **Chỉ sync (mirror), không clone sang TikTok:** Định kỳ và/hoặc on-demand gọi TikTok **GET** (list + info campaign), **upsert** vào `campaign_state` (hoặc tương đương). Không gọi `POST /campaign/gmv_max/create/` để “nhập” camp seller.

2. **Phân loại trong DB:**
   - `ownership` = `ZZP_MANAGED` | `EXTERNAL_TIKTOK`
   - `zzp_mutable` = `true` chỉ khi `ZZP_MANAGED`
   - Nhận diện ZZP: `tiktok_campaign_id` khớp bản ghi do ZZP tạo **và/hoặc** `campaign_name` theo quy ước prefix **`ZZP`** (đã thống nhất trong backlog).

3. **Bảng `smart_ads_campaign_config`:** chỉ **1-1** với camp **ZZP_MANAGED**. Camp `EXTERNAL_TIKTOK` **không** có dòng config.

4. **API write:** mọi `PATCH` / `POST` status / creatives trả **403** nếu `ownership != ZZP_MANAGED` (middleware / domain guard — P1-BE-14).

5. **FE:** badge **“Tạo trên TikTok — chỉ xem”**; ẩn nút sửa / pause / gắn video qua ZZP khi `!zzp_mutable`. Reports có thể read-only theo PM.

## Hệ quả

- Job sync (P1-BE-13) phải idempotent upsert theo `(advertiser_id, tiktok_campaign_id)`.
- Test bắt buộc: không có đường write nào cho `EXTERNAL_TIKTOK`.

## Tham chiếu

- [docs/PRD-SmartAds-v2.md](../PRD-SmartAds-v2.md) — BR-2
- [docs/SmartAds-Phase1-Backlog.md](../SmartAds-Phase1-Backlog.md) — mục 2, P1-BE-03, 13, 14, 16
