# SRS — Campaign Engine

| Trường | Giá trị |
|--------|---------|
| **Độc giả** | Dev, Tech Lead |
| **PRD gốc** | [PRD-SmartAds-v2.md](PRD-SmartAds-v2.md) §3.1 |
| **Phiên bản** | v1.3 · 2026-06-11 |
| **Đặc tả tối ưu (canonical)** | [SmartAds-RunAllVideos-Flow.md](SmartAds-RunAllVideos-Flow.md) — tóm tắt SRS tại [§4.6](#46-runallvideos--đặc-tả-tối-ưu-canonical) |

---

## 0. Cách đọc tài liệu này

**Mục tiêu:** mô tả *Campaign Engine* trong ZZP — OAuth TikTok, bảng chi phí + ROI hòa vốn, vòng đời chiến dịch GMV Max, và mapping API nội bộ ↔ TikTok.

**Luồng tối ưu mới nhất:** Toàn bộ phase khởi tạo ngân sách, learning 72h, vòng 24h, Hero, video “chết”, Critical Monitor và ma trận ROI×DB được **đặc tả đầy đủ** trong [SmartAds-RunAllVideos-Flow.md](SmartAds-RunAllVideos-Flow.md). SRS mục [§4.6](#46-runallvideos--đặc-tả-tối-ưu-canonical) **tích hợp tóm tắt** để dev đọc một nơi; khi lệch chi tiết, **ưu tiên RunAllVideos**.

**Hai lớp thời gian (tránh nhầm lẫn):**

| Chủ đề | Phase 1 (TikTok Parity) | Phase 2+ (Optimization / nâng cao) |
|--------|-------------------------|-------------------------------------|
| OAuth, `cost_table`, gợi ý ROI | Có — triển khai đầy đủ | Giữ nguyên / mở rộng |
| Tạo camp GMV Max lần đầu (`create`) | Có — **payload mặc định** theo mục [§4.3](#43-tạo-chiến-dịch-gmv-max--phase-1) (ADR 0001) | **RunAllVideos Phase 0** — `Budget_initial` 40%/20% + sàn 200k khi align create: [§4.6](#46-runallvideos--đặc-tả-tối-ưu-canonical) |
| Vòng đời RunAllVideos (learning 72h, Target ROI, vòng 24h, Hero, Revival, video chết, Critical Monitor) | Không bắt buộc P1; có thể stub trong DB/UI | **Canonical** [SmartAds-RunAllVideos-Flow.md](SmartAds-RunAllVideos-Flow.md) — SRS [§4.6](#46-runallvideos--đặc-tả-tối-ưu-canonical) |
| Tự động thêm video KOC (SAM → TikTok) | Không bắt buộc P1 | [§4.3 bước 3](#bước-3--tự-động-thêm-video-phase-2--tương-lai) |

**Payload tạo camp (SRS §4.3 vs RunAllVideos Phase 0):** mặc định Phase 1 **create** trên TikTok vẫn theo **20% MDB** + `roas_bid` như [§4.3](#43-tạo-chiến-dịch-gmv-max--phase-1) và [ADR 0001](adr/0001-smartads-phase1-tiktok-create-payload.md). Khi PM chốt **align create với RunAllVideos**, `budget` gửi TikTok = **Budget_initial** theo công thức [§4.6](#46-runallvideos--đặc-tả-tối-ưu-canonical). Wizard có thể dùng `CUSTOMIZED` sản phẩm/video khi backlog yêu cầu.

**Mode TikTok:** Luồng ZZP Auto dùng **Target ROI** (ROAS bid) — không dùng Max Delivery cho campaign chính; cửa sổ “learning” là **chính sách ZZP** (không ma trận Phase 2 trong 72h/24h), không đổi sang mode API khác — chi tiết [RunAllVideos §3–4](SmartAds-RunAllVideos-Flow.md#3-phase-0--khởi-tạo-ngân-sách--tạo-campaign).

**Chiến dịch seller tạo sẵn trên TikTok (chỉ đọc / sync):** không nằm trong bảng state “tối ưu ZZP”; xem [ADR 0002](adr/0002-smartads-external-campaign-mirror.md).

**Backlog dev Phase 1 (ticket P1-BE / P1-FE):** [SmartAds-Phase1-Backlog.md — §1.1](SmartAds-Phase1-Backlog.md#p1-p2-srs-matrix) (cùng ma trận P1 vs P2, góc nhìn task).

---

### Mục lục

1. [Tổng quan module](#1-tổng-quan-module)  
2. [Bảng chi phí & engine ROI](#2-bảng-chi-phí--engine-tính-roi)  
3. [Onboarding OAuth TikTok Ads](#3-onboarding-oauth-tiktok-ads)  
4. [Quản lý chiến dịch GMV Max](#4-quản-lý-chiến-dịch-gmv-max)  
   - [4.6 RunAllVideos — đặc tả tối ưu (canonical)](#46-runallvideos--đặc-tả-tối-ưu-canonical)
5. [Yêu cầu phi chức năng](#5-yêu-cầu-phi-chức-năng)  
6. [Test cases](#6-test-cases)

---

## 1. Tổng quan module

Campaign Engine chịu trách nhiệm:

1. Onboarding OAuth TikTok Ads  
2. Bảng chi phí theo sản phẩm + công thức **ROAS hòa vốn** (đồng bộ cách đo với TikTok — xem ghi chú [§2.2](#22-công-thức-tính-roi))  
3. Tạo và theo dõi vòng đời chiến dịch GMV Max (state + sync với TikTok)  
4. **RunAllVideos / Optimization Engine** — đặc tả đầy đủ ngoài SRS tại [SmartAds-RunAllVideos-Flow.md](SmartAds-RunAllVideos-Flow.md); tóm tắt trong SRS [§4.6](#46-runallvideos--đặc-tả-tối-ưu-canonical)  
5. State machine (nền tảng DB/API; phần “thông minh” gắn Phase 2)  
6. Mapping endpoint nội bộ ZZP ↔ TikTok Business API  

---

## 2. Bảng chi phí & engine tính ROI

### 2.1 Data model: `cost_table`

Một hàng **một** `product_id` (TikTok Shop).

| Cột | Kiểu | Nguồn / ý nghĩa |
|-----|------|-----------------|
| `product_id` | string | ID sản phẩm TikTok Shop |
| `gia_ban` (P) | decimal (VND) | Sync TikTok Shop API |
| `cogs` | decimal | ZZP nội bộ (bắt buộc) |
| `phi_san_pct` | decimal | ZZP theo ngành (vd. `0.06` = 6%) |
| `phi_thanh_toan_pct` | decimal | ZZP (vd. `0.02` = 2%) |
| `hoa_hong_koc_pct` | decimal | Thiết lập affiliate shop |
| `phi_ship_seller` | decimal (VND) | ZZP nội bộ |
| `phi_dong_goi` | decimal (VND) | ZZP nội bộ |

**Quan hệ:** `1 product_id` → tối đa `1` hàng `cost_table`.

### 2.2 Công thức tính ROI

**Lãi gộp trước quảng cáo (CM)** — dùng làm *cơ sở* cho ngưỡng đặt giá thầu ROAS trên TikTok:

```
CM = P
   - cogs
   - P × (phi_san_pct + phi_thanh_toan_pct + hoa_hong_koc_pct)
   - phi_ship_seller
   - phi_dong_goi
```

**ROAS hòa vốn** (gợi ý `roas_bid` / `roi_target` ban đầu khi `CM > 0`):

```
ROAS_be = P / CM
```

**Ví dụ số:** `P = 200.000`, `cogs = 120.000`, tổng % phí trên P = `0.06 + 0.02 + 0.20`, `ship = 13.000`, `gói = 4.000`  
→ `CM = 200k − 120k − 56k − 13k − 4k = 7.000` → `ROAS_be ≈ 200.000 / 7.000 ≈ 28.6`.

> **Ghi chú từ vựng:** Trên TikTok Seller, “ROI” thường là **Doanh thu gộp / Chi phí Ads** (blended organic + paid) — tức **ROAS**, không phải ROI lợi nhuận kế toán. ZZP dùng cùng hướng để UI và API TikTok **không** nói hai kiểu khác nhau. Cột `cost_table` + `ROAS_be` phục vụ **ngưỡng hòa vốn đơn hàng** trước ads; báo cáo camp vẫn đọc `roi` từ TikTok như [§4.5](#45-dashboard-phase-1).

### 2.3 API nội bộ: Cost Table

| Method | Path | Kết quả |
|--------|------|---------|
| GET | `/api/v1/smart-ads/cost-table?shop_id={id}` | Danh sách theo shop |
| GET | `/api/v1/smart-ads/cost-table/{product_id}` | Một sản phẩm |
| GET | `/api/v1/smart-ads/roi-suggestion?product_id={id}` | `{ product_id, roas_breakeven, cm_per_order, suggested_roi_target }` |

---

## 3. Onboarding OAuth TikTok Ads

### 3.1 Luồng OAuth (happy path)

1. Seller chọn **Kết nối TikTok Ads** trên ZZP.  
2. ZZP redirect tới TikTok:  
   `https://business-api.tiktok.com/portal/auth?app_id={APP_ID}&redirect_uri={CALLBACK}&state={csrf_token}`  
3. Seller đăng nhập TikTok và cấp quyền.  
4. TikTok redirect về ZZP: `?code={auth_code}&state={csrf_token}`.  
5. Backend đổi `code` → `access_token` + `refresh_token`.  
6. Lưu token **đã mã hóa**, gắn `seller_id`.  
7. Gọi TikTok (vd. thông tin advertiser) để lấy `advertiser_id` + tên hiển thị.  
8. Trạng thái UI: **Đã kết nối**.

### 3.2 Scopes cần xin

| Scope | Việc dùng trên ZZP |
|-------|-------------------|
| `advertiser_management` | Đọc ad account |
| `campaign_management` | Tạo / sửa / xóa campaign |
| `reporting` | GMV Max report (ROI, cost, orders, …) |
| `onsite_commerce_store` | Danh sách sản phẩm shop |
| `audience_management` | Exclusion audience (Phase sau nếu cần) |

### 3.3 Bảng `oauth_tokens`

| Cột | Ý nghĩa |
|-----|---------|
| `seller_id` | FK seller |
| `advertiser_id` | TikTok Ad Account ID |
| `access_token` | Mã hóa (AES-256) |
| `refresh_token` | Mã hóa (AES-256) |
| `expires_at` | Hết hạn access |
| `refresh_exp_at` | Hết hạn refresh |
| `status` | `ACTIVE` \| `EXPIRED` \| `REVOKED` |

**Refresh chủ động:** trước khi `access_token` hết hạn (gợi ý **~5 phút**), job/scheduler refresh bằng `refresh_token`.

**Khi refresh thất bại / refresh hết hạn / thu hồi:** `status = EXPIRED`; dừng job tối ưu (nếu đã có); **không** tự pause campaign trên TikTok; hiển thị banner + kênh thông báo (theo [ADR 0003](adr/0003-smartads-phase1-notifications.md)).

### 3.4 API nội bộ: OAuth

| Method | Path | Hành vi |
|--------|------|---------|
| GET | `/api/v1/smart-ads/oauth/connect?seller_id={id}` | Trả URL redirect TikTok |
| GET | `/api/v1/smart-ads/oauth/callback?code=&state=` | Đổi code, lưu DB, redirect về ZZP |
| GET | `/api/v1/smart-ads/oauth/status?seller_id={id}` | `{ connected, advertiser_id, account_name, expires_at }` |
| DELETE | `/api/v1/smart-ads/oauth/disconnect?seller_id={id}` | Xóa / vô hiệu token, dừng job tối ưu nếu có |

---

## 4. Quản lý chiến dịch GMV Max

### 4.1 Data model: `campaign_state`

| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| `id` | uuid | PK nội bộ ZZP |
| `seller_id` | string | FK |
| `advertiser_id` | string | TikTok ad account |
| `tiktok_campaign_id` | string, **nullable** | `null` = nháp chưa publish; sau `create` TikTok thì gán ID |
| `state` | enum | `INIT` \| `WARMING` \| `STABLE` \| `HERO` \| `PAUSED` |
| `campaign_type` | enum | `MAIN` \| `HERO` \| `REVIVAL` |
| `parent_campaign_id` | uuid, nullable | Camp Hero/Revival trỏ về camp gốc |
| `roi_target` | decimal | ROI/ROAS mục tiêu đang set (đồng bộ TikTok khi có) |
| `daily_budget` | decimal (VND) | Ngân sách ngày **hiện tại** trên TikTok / mirror |
| `max_daily_budget` | decimal (VND) | **MDB** seller cấu hình — trần |
| `activated_at` | datetime | Kích hoạt / tạo trên TikTok |
| `warming_ends_at` | datetime | Gợi ý: `activated_at + 72h` |
| `last_optimized_at` | datetime | Phase 2: Optimization Engine |
| `last_optimized_date` | date | Phase 2: tối đa 1 lần tối ưu / ngày (nếu áp dụng) |
| `paused_at` | datetime, nullable | |
| `paused_reason` | string | `OUT_OF_STOCK` \| `PAYMENT_FAILED` \| `CANCEL_RATE` \| `MANUAL` \| `BUDGET_CAP` |

**Quan hệ:** một seller có **nhiều** `campaign_state`. Unique `(advertiser_id, tiktok_campaign_id)` khi `tiktok_campaign_id` không null.

Các cột **ownership / sync** (camp ZZP vs camp seller trên TikTok) nằm trong [ADR 0002](adr/0002-smartads-external-campaign-mirror.md) và backlog P1 — không thu nhỏ vào bảng trên để SRS vẫn đọc được như “schema cốt lõi”.

### 4.2 State machine

```text
[INIT]
   │  Seller “Bắt đầu chạy” → TikTok create thành công
   ▼
[WARMING]     ← ~72h đầu: **Target ROI** trên TikTok; ZZP **không** chạy ma trận tối ưu 24h (learning — [RunAllVideos Phase 1](SmartAds-RunAllVideos-Flow.md#4-phase-1--72h-learning-target-roi))
   │  Đủ điều kiện thời gian / policy Optimization (Phase 2)
   ▼
[STABLE]      ← Optimization Engine — vòng lặp 24h / ma trận ROI×DB ([RunAllVideos Phase 2](SmartAds-RunAllVideos-Flow.md#5-phase-2--vòng-lặp-tối-ưu-mỗi-24h-target-roi))
   │  Sản phẩm đạt ngưỡng đơn (vd. ≥ 20) — tách Hero / Revival (Phase 2)
   ▼
[HERO]        ← State có thể gắn **campaign_type** `HERO` hoặc nhánh revival; MAIN có thể vẫn STABLE — chi tiết [§4.6](#46-runallvideos--đặc-tả-tối-ưu-canonical)

Bất kỳ state → [PAUSED] khi:
  • Hết kho (`OUT_OF_STOCK`)
  • Thanh toán lỗi (`PAYMENT_FAILED`)
  • Tỷ lệ hủy cao sau xác nhận seller (`CANCEL_RATE`)
  • Seller dừng tay (`MANUAL`)
  • Chạm trần ngân sách (`BUDGET_CAP`)

[PAUSED] → [STABLE]: kho phục hồi / seller “Bật lại” (tuỳ policy TikTok + ZZP)
```

**Phase 1:** bắt buộc lưu đúng `state`, `activated_at`, `warming_ends_at` sau khi tạo camp; chuyển `WARMING` → `STABLE` có thể **theo thời gian + sync TikTok** nếu Optimization Engine chưa sẵn sàng. Khi Engine bật, căn cứ mốc **72h** và ma trận sau learning theo [§4.6](#46-runallvideos--đặc-tả-tối-ưu-canonical). Các nhánh Hero / Revival / tách camp là **Phase 2** trừ khi PM gộp scope.

### 4.3 Tạo chiến dịch GMV Max — Phase 1

> **Liên kết RunAllVideos:** Ngân sách ngày lúc **create** trong SRS dưới đây là **20% MDB** (ADR 0001). Luồng tối ưu đầy đủ dùng **Budget_initial** 40%/20% + sàn 200k cho lần chạy “Run all videos” — xem [§4.6](#46-runallvideos--đặc-tả-tối-ưu-canonical).

**Kích hoạt:** Seller hoàn tất wizard và bấm **Bắt đầu chạy** (sau OAuth).

#### Bước 1 — Gọi TikTok tạo campaign

`POST /campaign/gmv_max/create/` (TikTok) — thân tin đại diện:

```json
{
  "advertiser_id": "{advertiser_id}",
  "campaign_name": "ZZP-SmartAds-{shop_name}-{YYYYMMDD}",
  "budget": "{max_daily_budget × 0.20}",
  "budget_mode": "BUDGET_MODE_DAY",
  "roas_bid": "{roas_breakeven_from_cost_table}",
  "product_source": "ALL_PRODUCTS",
  "video_source": "ALL_VIDEOS",
  "promotion_type": "PRODUCT_SALE"
}
```

- **`budget`:** **20%** `max_daily_budget` (MDB) — ngân sách ngày gửi TikTok lúc tạo.  
- **`product_source` / `video_source`:** mặc định SRS như trên; nếu wizard dùng tập con sản phẩm/video → đổi sang `CUSTOMIZED` + payload tương ứng (backlog / PM).  
- Tên campaign trên TikTok nên có tiền tố **`ZZP`** để sync phân biệt camp do ZZP tạo (xem ADR 0002).

#### Bước 2 — Ghi `campaign_state` (ZZP)

Sau khi TikTok trả `campaign_id`:

- `state = WARMING`  
- `activated_at = now()`  
- `warming_ends_at = now() + 72h`  
- `roi_target` = ROAS hòa vốn đã dùng  
- `daily_budget` = **20% × MDB** (khớp bước 1)

#### Bước 3 — Tự động thêm video (Phase 2 / tương lai)

Khi SAM sinh video KOC mới, pipeline tối ưu có thể gọi:

`POST /campaign/gmv_max/creative/update/` với `{ "action": "ADD", "video_ids": ["..."] }`.

**Không** coi đây là tiêu chí nghiệm thu bắt buộc Phase 1 trừ khi PM gộp scope.

### 4.4 TikTok API mapping

**Campaign GMV Max**

| TikTok API | Method | Mục đích | ZZP (gợi ý path) |
|------------|--------|----------|------------------|
| `/campaign/gmv_max/create/` | POST | Tạo campaign | `POST /api/v1/smart-ads/campaigns` (hoặc `…/publish`) |
| `/campaign/gmv_max/update/` | POST | ROI, budget, … | `PATCH /api/v1/smart-ads/campaigns/{id}` |
| `/campaign/status/update/` | POST | Pause / Resume / Delete | `POST /api/v1/smart-ads/campaigns/{id}/status` |
| `/gmv_max/campaign/get/` | GET | Danh sách | `GET /api/v1/smart-ads/campaigns` |
| `/campaign/gmv_max/info/` | GET | Chi tiết | `GET /api/v1/smart-ads/campaigns/{id}` |

**Sản phẩm**

| TikTok API | Method | ZZP |
|------------|--------|-----|
| `/store/product/get/` | GET | `GET /api/v1/smart-ads/products` |

**Video / creative**

| TikTok API | Method | ZZP |
|------------|--------|-----|
| `/gmv_max/video/get/` | GET | `GET /api/v1/smart-ads/videos` |
| `/campaign/gmv_max/creative/update/` | POST | `POST /api/v1/smart-ads/campaigns/{id}/creatives` |

**Báo cáo**

| TikTok API | Method | ZZP |
|------------|--------|-----|
| `/gmv_max/report/get/` | GET | `GET /api/v1/smart-ads/reports` |

**Metrics thường dùng** (dashboard + tín hiệu Phase 2):

| Field | Ý nghĩa ngắn |
|-------|----------------|
| `cost` | Chi phí ads đã tiêu |
| `gross_revenue` | GMV / doanh thu gộp (blended) |
| `roi` | `gross_revenue / cost` (ROAS TikTok) |
| `orders` | Số đơn |
| `conversion_rate` | Tỷ lệ chuyển đổi |
| `video_play_2s`, `video_play_6s`, `video_watched_25_pct` … | Chất lượng video |

### 4.5 Dashboard (Phase 1)

ZZP đọc `/gmv_max/report/get/` (qua lớp proxy) và map:

| UI | Nguồn |
|----|--------|
| GMV | `gross_revenue` |
| Chi phí Ads | `cost` |
| ROI thực tế | `roi` |
| Số đơn | `orders` |
| Chi phí / đơn | `cost / orders` (tránh chia cho 0) |
| Trạng thái camp | `campaign_state.state` + trạng thái TikTok nếu cần |
| Ngân sách hôm nay | `daily_budget` / đồng bộ TikTok |
| ROI đang set | `roi_target` |

### 4.6 RunAllVideos — đặc tả tối ưu (canonical)

**Nguồn đầy đủ:** [SmartAds-RunAllVideos-Flow.md](SmartAds-RunAllVideos-Flow.md) (flow mới nhất: thuật ngữ, sơ đồ, Phase 0–2, ma trận ROI×DB, Hero, video “chết”, Critical Monitor, pseudocode). **Mục SRS này chỉ tóm tắt** để Campaign Engine đọc cùng với §4.1–4.5; khi mâu thuẫn chi tiết, **ưu tiên RunAllVideos**.

#### Nền tảng TikTok

- Campaign GMV Max luôn **Target ROI** (`roas_bid` / `ROI_target`). **Không** dùng Max Delivery cho campaign chính (giới hạn nền tảng).
- **Learning 72h / 24h (Hero)** = cửa sổ ZZP **không** áp ma trận điều chỉnh hàng ngày (Phase 2); không đổi “mode” API khác.

#### Bản đồ phase ↔ `campaign_state` / thời gian

| RunAllVideos | Ý nghĩa | Gợi ý map DB / sync |
|----------------|---------|---------------------|
| **Phase 0** | Tính `Budget_initial`, tạo camp (tất cả video đã chọn), bật Critical Monitor | Sau `create`: `state = WARMING`, `warming_ends_at = activated_at + 72h`, `daily_budget` = ngân sách đã gửi TikTok |
| **Phase 1** | 72h learning — chỉ quan sát (+ Critical Monitor) | Giữ `WARMING` đến hết cửa sổ; không tăng/giảm theo ma trận §4.6 dưới |
| **Phase 2** | Tối đa **1** thay đổi ROI hoặc budget / campaign / ngày lịch; thứ tự 4 kiểm tra | `STABLE` (hoặc tiếp tục tối ưu); `last_optimized_date`; cập nhật `daily_budget` / `roi_target` qua `gmv_max/update` |

#### Ngân sách ngày khởi tạo (`Budget_initial`)

- **Campaign đầu (Phase 0):** `MDB × 40%` nếu `MDB < 2.000.000đ`; `MDB × 20%` nếu `MDB ≥ 2.000.000đ`; **sàn** `MAX(..., 200.000đ)`.
- **So với §4.3:** SRS Phase 1 mặc định gửi **20% MDB** ([ADR 0001](adr/0001-smartads-phase1-tiktok-create-payload.md)). Khi sản phẩm chạy **RunAllVideos** và PM chốt align create → dùng công thức trên cho field `budget` lúc `create`.
- **Camp tách video “chết”** (Phase 2): khởi tạo **50% × MDB**, Target ROI, vào vòng 24h **ngay** — điều kiện & hành động: RunAllVideos §5 Kiểm tra 1.
- **Camp Hero:** khởi tạo **50% × MDB**; **24h learning** rồi vòng 24h — RunAllVideos §7.

#### Phase 2 — thứ tự ưu tiên trong một ngày (tuần tự)

1. Video “chết” (≥20 đơn lịch sử, 48h không đơn mới) → nhánh Critical, tách camp; **dừng** các kiểm tra còn lại trong ngày.  
2. Hero product (≥20 đơn) → tách Hero (`campaign_type = HERO`, tối đa 2 tầng).  
3. Ma trận **ROI_actual × DB_actual** (threshold `DB_campaign × 0.5`, …) — RunAllVideos §6.  
4. GMV ngày = 0 (bộ đếm 3 ngày → pause) — RunAllVideos §5 Kiểm tra 4.

#### Critical Monitor

Chạy **song song** từ lúc tạo campaign; được phép can thiệp (tồn kho, hủy đơn, trần MDB tổng, thanh toán, …) kể cả trong learning — RunAllVideos §8.

#### `campaign_type` / tách camp

- `MAIN` \| `HERO` \| `REVIVAL` (camp hồi sinh / tách từ video chết); `parent_campaign_id` khi là camp con.

---

## 5. Yêu cầu phi chức năng

- **Bảo mật token:** AES-256 trước khi lưu DB; không log plaintext.  
- **Idempotency tạo camp:** retry không được tạo duplicate — kiểm tra `tiktok_campaign_id` / `idempotency-key` trước khi gọi TikTok lần 2.  
- **429:** exponential backoff; log mỗi lần bị throttle.  
- **Lỗi mạng / 5xx:** retry tối đa **3** lần, backoff **1s → 5s → 15s**; sau đó log + alert nội bộ (có thể persist — backlog).

---

## 6. Test cases

| ID | Scenario | Kỳ vọng | Ghi chú phase |
|----|----------|---------|----------------|
| CE-01 | OAuth full flow | Token DB, `ACTIVE`, `advertiser_id` đúng | P1 |
| CE-02 | Refresh token hết hạn | `EXPIRED`, dừng job tối ưu, thông báo seller | P1 |
| CE-03 | Tạo camp: budget TikTok | `budget` = **20% MDB** | P1 |
| CE-04 | Tạo camp: ROAS | `roas_bid` = `ROAS_be` từ `cost_table` | P1 |
| CE-05 | Retry tạo camp | Một camp TikTok; không duplicate | P1 |
| CE-06 | `WARMING` → `STABLE` | Đúng policy thời gian / sync đã chốt | P1 tối thiểu |
| CE-07 | Pause khi hết kho | Pause trong SLA đã chốt (vd. ≤ 1 phút) | Tuỳ P1/P2 |
| CE-08 | Video KOC mới → inject | Creative update đúng API | Phase 2 nếu bật |
| CE-09 | Sync `cost_table` | `ROAS_be = P/CM` khớp [§2.2](#22-công-thức-tính-roi) | P1 |
| CE-10 | RunAllVideos Phase 0: `Budget_initial` | Nếu align create: `budget` = 40%/20% + sàn 200k theo MDB | Phase 2 / PM chốt |

---

*Tài liệu làm việc trong repo; khi ADR 0001/0002 đổi trạng thái Accepted, cập nhật đoạn §0, §4.3 và §4.6 cho khớp contract đã ký.*
