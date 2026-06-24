# SRS — Optimization Rules Engine

> **Dành cho:** Dev, Tech Lead
> **Phạm vi:** Phase 2 — Logic tối ưu hàng ngày (C1–C5) + Holiday Mode
> **PRD gốc:** `docs/PRD-SmartAds-v2.md §2.4`
> **Phụ thuộc:** `SRS-Campaign-Engine.md` (state machine, data model)

---

## 1. Tổng quan

Optimization Engine chạy **1 lần mỗi ngày dương lịch** cho từng chiến dịch đang ở state STABLE hoặc HERO. Engine đánh giá metrics từ TikTok API và ra tối đa **1 quyết định thay đổi** (tăng/giảm ROI hoặc ngân sách) cho mỗi chiến dịch.

**Ràng buộc bất biến:**
- Không chạy trong 72h đầu tiên (state = WARMING) — ngoại trừ các Exception ở SRS-Fraud-Inventory.md.
- Tối đa 1 thay đổi (ROI hoặc budget) trên 1 chiến dịch trong 1 ngày dương lịch.
- Không bao giờ cho daily_budget vượt MDB.
- Không bao giờ để tổng budget tất cả camp vượt MDB của Seller.

---

## 2. Chu kỳ chạy

### 2.1 Thời điểm

Engine chạy mỗi ngày dương lịch theo lịch cố định (đề xuất: 23h30 VN time). Logic đánh giá dựa trên dữ liệu của **ngày hôm đó** (00:00–23:59).

**Xử lý khi API TikTok không phản hồi lúc chạy:**
- Retry trong cửa sổ 30 phút (23h30 → 00h00).
- Nếu vẫn fail: bỏ qua đêm đó, giữ nguyên config. Alert nội bộ ZZP + thông báo Seller.

### 2.2 Điều kiện để chạy trên 1 chiến dịch

Chiến dịch được xét tối ưu khi TẤT CẢ điều kiện sau đều đúng:
```
campaign_state.state IN (STABLE, HERO)
AND now() > campaign_state.warming_ends_at    ← đã qua 72h
AND campaign_state.last_optimized_date != today()   ← chưa được tối ưu hôm nay
AND oauth_tokens.status = ACTIVE              ← kết nối TikTok còn hiệu lực
```

### 2.3 Dữ liệu đầu vào

Trước khi chạy logic, lấy metrics từ TikTok:
```
GET /gmv_max/report/get/
Params:
  campaign_id = {tiktok_campaign_id}
  date_range  = today (00:00–23:59)
  metrics     = [cost, gross_revenue, roi, orders, daily_budget]

Biến cục bộ:
  cost_today      = cost (VND đã tiêu trong ngày)
  roi_actual      = roi (số blended TikTok báo cáo)
  roi_target      = campaign_state.roi_target
  daily_budget    = campaign_state.daily_budget  (DB)
  max_daily_budget = campaign_state.max_daily_budget (MDB)
```

---

## 3. Thứ tự đánh giá và ra quyết định

> Engine chạy theo thứ tự ưu tiên. Khi đã ra 1 quyết định → dừng, không đánh giá thêm (vì tối đa 1 lần/ngày).

```
Bước 1: Kiểm tra tổng ngân sách (EX-5 - xem SRS-Fraud-Inventory)
  → Nếu tổng tất cả camp >= MDB: dừng toàn bộ, không tối ưu gì

Bước 2: Kiểm tra điều kiện chạy (§2.2)
  → Không thỏa: bỏ qua chiến dịch này

Bước 3: Đánh giá C1 (Giảm ROI)
  → Nếu thỏa: thực hiện, cập nhật last_optimized_date, DỪNG

Bước 4: Đánh giá C2 (Tăng ROI)
  → Nếu thỏa: thực hiện, cập nhật last_optimized_date, DỪNG

Bước 5: Đánh giá C4 (Tăng Budget)
  → Nếu thỏa: thực hiện, cập nhật last_optimized_date, DỪNG

Bước 6: Đánh giá C3 (Hero Product Split)
  → Nếu thỏa: thực hiện (tách camp mới), DỪNG

Bước 7: Đánh giá C5 (Video Revival)
  → Nếu thỏa: thực hiện (tạo camp revival mới), DỪNG

Bước 8: Không có quyết định → ghi log "no_action", DỪNG
```

---

## 4. Chi tiết từng rule

### C1 — Giảm ROI

**Mục đích:** Khi chiến dịch không cắn tiền (tiêu ít hơn kỳ vọng), giảm ROI để thu hút nhiều người mua hơn (máy TikTok dễ phân phối hơn).

**Điều kiện (thỏa 1 trong 2):**
```
(A) cost_today < 0.20 * daily_budget
    (Tiêu dưới 20% ngân sách ngày)

(B) 1.0 <= roi_actual < 0.70 * roi_target
    (Tiêu tốt nhưng ROI thực tế quá thấp so với mục tiêu)
```

**Hành động:**
```
new_roi = roi_target * (1 - 0.15)      ← Giảm tối đa 15%
new_roi = max(new_roi, ROAS_be)        ← Không giảm xuống dưới hòa vốn

Gọi: PUT /campaign/gmv_max/update/
  { roas_bid: new_roi }

Cập nhật:
  campaign_state.roi_target = new_roi
  campaign_state.last_optimized_date = today()
  campaign_state.last_optimized_at = now()
```

**Kiểm tra thêm sau C1:**
```
Nếu (tong_tien_da_tieu_tich_luy >= MDB AND orders_today == 0):
  → PAUSE CAMP (campaign_state.state = PAUSED, paused_reason = BUDGET_CAP_NO_GMV)
  → Thông báo Seller
```

---

### C2 — Tăng ROI

**Mục đích:** Khi chiến dịch đang tiêu tốt ở mức vừa phải, tăng ROI để chọn lọc người mua chất lượng cao hơn và tăng lợi nhuận.

**Điều kiện (cả 2 phải đúng):**
```
(A) 0.50 * daily_budget <= cost_today <= 0.80 * daily_budget
    (Tiêu trong khoảng 50%–80% ngân sách ngày)
```

**Hành động:**
```
new_roi = roi_target * (1 + 0.20)      ← Tăng tối đa 20%

Gọi: PUT /campaign/gmv_max/update/
  { roas_bid: new_roi }

Cập nhật campaign_state tương tự C1
```

---

### C3 — Hero Product Split

**Mục đích:** Khi 1 sản phẩm có đà tốt (≥ 20 đơn), tập trung ngân sách vào sản phẩm đó bằng chiến dịch riêng.

**Điều kiện:**
```
Tồn tại product_id trong campaign sao cho:
  sum(orders) của product_id trong camp >= 20
```

**Dữ liệu cần thêm:**
```
GET /gmv_max/report/get/
  dimensions = [product_id]
  metrics    = [orders]
  date_range = toàn bộ lịch sử từ activated_at đến nay
→ Tìm product_id có tổng orders >= 20
```

**Hành động:**

Bước 1 — Tạo Hero Campaign:
```
POST /campaign/gmv_max/create/
{
  campaign_name: "ZZP-Hero-{product_name}-{YYYYMMDD}",
  budget: campaign_state.daily_budget * 1.20,  ← 120% DB hiện tại
  roas_bid: campaign_state.roi_target,          ← Kế thừa ROI từ camp gốc
  product_source: "CUSTOMIZED_PRODUCTS",
  product_ids: ["{hero_product_id}"]
}

Lưu campaign_state:
  campaign_type = HERO
  parent_campaign_id = {id camp gốc}
  state = WARMING          ← Bắt đầu lại 72h
  activated_at = now()
  warming_ends_at = now() + 72h
  daily_budget = {120% DB}
```

Bước 2 — Xóa sản phẩm Hero khỏi camp gốc:
```
POST /campaign/gmv_max/update/
{
  campaign_id: {camp gốc tiktok_campaign_id},
  excluded_product_ids: ["{hero_product_id}"]
}
```

Bước 3 — Giảm ngân sách camp gốc:
```
new_budget_goc = daily_budget_goc * (1 - 0.20)     ← Giảm tối đa 20%
new_budget_goc = max(new_budget_goc, 200_000)       ← Tối thiểu 200.000đ/ngày

PUT /campaign/gmv_max/update/
  { campaign_id: {gốc}, budget: new_budget_goc }

Cập nhật campaign_state camp gốc:
  daily_budget = new_budget_goc
  last_optimized_date = today()
```

**Guardrail trước khi tạo Hero:**
```
Kiểm tra: tong_budget_tat_ca_camp + (DB_goc * 1.20) > MDB ?
  → Nếu có: KHÔNG tạo Hero Camp, ghi log "hero_blocked_budget_cap"
  → Thông báo Seller: "Sản phẩm X đủ điều kiện Hero nhưng ngân sách tổng đã đạt giới hạn"
```

---

### C4 — Tăng Budget

**Mục đích:** Khi chiến dịch đang chạy hiệu quả (ROI tốt hơn mục tiêu), tăng ngân sách để tận dụng đà.

**Điều kiện:**
```
roi_actual >= roi_target
```

**Hành động:**
```
new_budget = daily_budget * (1 + 0.20)    ← Tăng tối đa 20%

Guardrail: tong_budget_tat_ca_camp_sau_tang > MDB ?
  → Nếu có: new_budget = MDB - tong_budget_cac_camp_khac
  → Nếu new_budget <= daily_budget: không tăng, ghi log

PUT /campaign/gmv_max/update/
  { budget: new_budget }

Cập nhật campaign_state tương tự C1
```

---

### C5 — Video Revival

**Mục đích:** Hồi sinh video từng có hiệu quả tốt nhưng đang chững — thử lại với ngân sách nhỏ.

**Điều kiện:**
```
Tồn tại video_id trong campaign sao cho:
  - Tổng orders của video đó từ trước đến nay >= 20
  - VÀ orders của video trong 48h gần nhất = 0
  - VÀ campaign_state.state = STABLE (không áp cho HERO hoặc WARMING)
```

**Dữ liệu cần thêm:**
```
GET /gmv_max/report/get/
  dimensions = [video_id]
  date_range = 48h gần nhất
  metrics    = [orders]
→ Tìm video_id có orders_48h = 0 nhưng tổng lịch sử >= 20
```

**Hành động:**

Bước 1 — Tạo Revival Campaign:
```
POST /campaign/gmv_max/create/
{
  campaign_name: "ZZP-Revival-{video_id}-{YYYYMMDD}",
  budget: 100_000,          ← 100.000đ/ngày cố định
  roas_bid: roi_target,     ← Kế thừa từ camp gốc
  product_source: "ALL_PRODUCTS",
  video_source: "CUSTOMIZED_VIDEOS",
  video_ids: ["{revival_video_id}"]
}

Lưu campaign_state:
  campaign_type = REVIVAL
  parent_campaign_id = {camp gốc}
  state = WARMING
  activated_at = now()
  warming_ends_at = now() + 72h
  daily_budget = 100_000
```

Bước 2 — Thông báo Seller:
```
Nội dung: "Video [tên/ID] từng đạt {X} đơn nhưng đã 48h không có đơn mới.
           ZZP đang chạy thử lại với ngân sách 100.000đ/ngày."
Kênh: In-app notification
```

Camp gốc: tiếp tục monitoring mỗi 24h, không bị ảnh hưởng.

---

## 5. Holiday Mode

**Mục đích:** Giảm ROI_target trong các ngày sale lớn để máy TikTok phân phối rộng hơn, tận dụng traffic cao.

### 5.1 Danh sách ngày sale (tự động nhận biết)

```
holiday_schedule (cấu hình bởi ZZP, không phải Seller):
- Ngày cố định hàng năm: 1/1, 14/2, 8/3, 30/4, 1/5, 2/9
- Ngày sale TikTok định kỳ: 6.6, 7.7, 8.8, 9.9, 10.10, 11.11, 12.12
- Giữa tháng hàng tháng: ngày 15 mỗi tháng
- Ngày lương về: ngày 5 và ngày 25 mỗi tháng
```

### 5.2 Logic

**Khi** ngày hôm nay thuộc holiday_schedule:
```
Với mỗi campaign ở state STABLE hoặc HERO:
  holiday_roi = roi_target * (1 - 0.20)    ← Giảm 20%
  holiday_roi = max(holiday_roi, ROAS_be)  ← Không dưới hòa vốn

  Gọi API: PUT /campaign/gmv_max/update/
    { promotion_days: [today], roas_bid: holiday_roi }

Lưu: campaign_state.holiday_roi_override = holiday_roi
```

**Khi** ngày hôm sau không còn là ngày sale:
```
Với mỗi campaign có holiday_roi_override:
  PUT /campaign/gmv_max/update/
    { roas_bid: roi_target }   ← Khôi phục về ROI bình thường

  Xóa: campaign_state.holiday_roi_override = null
```

**Lưu ý:** Holiday Mode chạy trước các rule C1–C5 trong cùng ngày. Nếu đã áp Holiday Mode thì `last_optimized_date` = today() → C1–C5 không chạy thêm.

---

## 6. Logging & Monitoring

Mỗi lần engine chạy phải ghi log:

```
optimization_log:
- campaign_id         : uuid
- run_date            : date  (ngày dương lịch)
- rule_applied        : enum  (C1_DECREASE_ROI | C2_INCREASE_ROI | C3_HERO_SPLIT |
                               C4_INCREASE_BUDGET | C5_REVIVAL | HOLIDAY | NO_ACTION |
                               SKIPPED_WARMING | SKIPPED_ALREADY_OPTIMIZED |
                               BLOCKED_BUDGET_CAP | API_ERROR)
- old_roi             : decimal
- new_roi             : decimal  (null nếu không đổi ROI)
- old_budget          : decimal
- new_budget          : decimal  (null nếu không đổi budget)
- roi_actual_at_run   : decimal
- cost_at_run         : decimal
- error_message       : string   (null nếu thành công)
- created_at          : datetime
```

**Alert nội bộ** khi `rule_applied = API_ERROR` cho ≥ 5% campaigns trong 1 lần chạy.

---

## 7. Test cases

| ID | Scenario | Expected |
|---|---|---|
| OR-01 | Campaign ở WARMING → engine bỏ qua | log = SKIPPED_WARMING |
| OR-02 | Đã tối ưu hôm nay → engine bỏ qua | log = SKIPPED_ALREADY_OPTIMIZED |
| OR-03 | cost_today = 15% DB | C1 kích hoạt, roi_target giảm 15% |
| OR-04 | roi_actual = 0.5 × roi_target (trong [1.0, 0.7×]) | C1 kích hoạt |
| OR-05 | cost_today = 60% DB | C2 kích hoạt, roi_target tăng 20% |
| OR-06 | roi_actual = 1.1 × roi_target | C4 kích hoạt, budget tăng 20% |
| OR-07 | Product_A đạt 20 đơn | C3: Hero camp tạo, product_A xóa khỏi camp gốc, budget gốc giảm |
| OR-08 | C3 nhưng tổng budget sẽ vượt MDB | C3 bị block, log = BLOCKED_BUDGET_CAP, thông báo Seller |
| OR-09 | Video_X từng 25 đơn, 48h = 0 đơn | C5: Revival camp 100k tạo, thông báo Seller |
| OR-10 | Ngày 6.6 | Holiday Mode: roi giảm 20%, last_optimized_date set |
| OR-11 | Ngày 7.6 (sau 6.6) | Holiday roi khôi phục về roi_target bình thường |
| OR-12 | API TikTok không phản hồi | Retry 3 lần, log = API_ERROR, giữ nguyên config, alert nội bộ |
| OR-13 | new_roi sau giảm C1 < ROAS_be | new_roi = ROAS_be (không giảm dưới hòa vốn) |
| OR-14 | C4 nhưng new_budget > MDB | new_budget cắt tại (MDB - tong_camp_khac) |

---

*Phiên bản: v1 | 2026-06-07*
