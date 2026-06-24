# SRS — Fraud Protection & Inventory Engine

> **Dành cho:** Dev, Tech Lead
> **Phạm vi:** Phase 2 — Các exception xử lý real-time (EX-1 đến EX-6) + Panic Switch + Sync kho
> **PRD gốc:** `docs/PRD-SmartAds-v2.md §2.5`
> **Phụ thuộc:** `SRS-Campaign-Engine.md` (state machine, data model)

---

## 1. Tổng quan

Protection Engine xử lý **real-time**, không theo lịch ngày. Các exception này được phép kích hoạt **bất kỳ lúc nào**, kể cả trong 72h đầu đang đóng băng của Optimization Engine.

**Kiến trúc:** Event-driven. Các trigger đến từ:
- Webhook từ TikTok Shop (đơn hàng mới, đơn hủy)
- Polling tồn kho từ TikTok Shop API (mỗi 15 phút)
- Polling báo cáo GMV Max từ TikTok Business API (mỗi 15 phút)
- Hành động thủ công của Seller (Panic Switch)

---

## 2. Data Models bổ sung

### 2.1 Buyer Blacklist

```
zzp_buyer_blacklist:
- id                  : uuid     : PK
- shop_id             : string   : FK → shops
- tt_buyer_id         : string   : TikTok Buyer ID (định danh người mua)
- consecutive_cancels : integer  : số lần hủy liên tiếp hiện tại
- blocked_at          : datetime : null nếu chưa bị chặn; có giá trị nếu đã chặn
- last_cancel_at      : datetime : thời điểm lần hủy gần nhất
- last_success_at     : datetime : thời điểm đơn thành công gần nhất (reset đếm)

Index: (shop_id, tt_buyer_id) UNIQUE
```

### 2.2 Cancel Rate Tracking

```
cancel_rate_tracker:
- campaign_id         : uuid     : FK → campaign_state
- tracking_date       : date     : ngày theo dõi
- total_orders_24h    : integer  : tổng đơn trong 24h
- cancelled_orders_24h: integer  : số đơn bị hủy trong 24h
- cancel_rate         : decimal  : cancelled / total
- critical_triggered_at: datetime : thời điểm vào CRITICAL (null nếu chưa)
```

### 2.3 Inventory Snapshot

```
inventory_snapshot:
- product_id          : string   : TikTok Shop product ID
- shop_id             : string   : FK
- quantity_initial    : integer  : số lượng lúc ZZP bắt đầu quản lý camp
- quantity_current    : integer  : số lượng hiện tại (cập nhật mỗi 15 phút)
- low_stock_notified_at: datetime : thời điểm đã gửi cảnh báo sắp hết (null nếu chưa)
- last_synced_at      : datetime : lần sync gần nhất
```

---

## 3. EX-1 — Chặn Buyer Bùng Đơn (Real-time)

**Mục đích:** Ngăn khách hàng đặt đơn rồi hủy nhiều lần liên tiếp, gây tốn tiền quảng cáo và ảnh hưởng điểm shop.

### 3.1 Trigger

```
Khi: TikTok Shop webhook nhận sự kiện đơn hàng hủy
  order.cancel_type = "BUYER_CANCEL"   ← Khách tự hủy (không phải shop hủy)
  order.source = "ADS"                 ← Đơn đến từ quảng cáo (không phải organic)
```

### 3.2 Logic đếm liên tiếp

```
buyer = zzp_buyer_blacklist.find_or_create(shop_id, tt_buyer_id)

buyer.consecutive_cancels += 1
buyer.last_cancel_at = now()
buyer.save()

Nếu buyer.consecutive_cancels >= 10:    ← N = 10 (đã chốt)
  → Kích hoạt chặn buyer (§3.3)
```

**Reset đếm khi đơn thành công:**
```
Khi: TikTok Shop webhook nhận sự kiện đơn hàng thành công (order.status = COMPLETED)
  buyer = zzp_buyer_blacklist.find(shop_id, tt_buyer_id)
  Nếu có:
    buyer.consecutive_cancels = 0
    buyer.last_success_at = now()
    buyer.save()
```

### 3.3 Hành động chặn buyer

```
buyer.blocked_at = now()
buyer.save()

Với mỗi campaign của shop đang ở state != PAUSED:
  POST /exclusion_audience/update/
  {
    advertiser_id: {advertiser_id},
    campaign_id: {tiktok_campaign_id},
    buyer_ids: ["{tt_buyer_id}"]
  }

Ghi log: { event: "BUYER_BLOCKED", buyer_id, shop_id, consecutive_cancels: 10 }
Thông báo Seller: in-app "Đã tự động chặn 1 khách hàng bùng đơn"
```

---

## 4. EX-2 — Thanh Toán Lỗi (Real-time)

**Mục đích:** Xử lý khi TikTok Ads không có đủ số dư để chạy quảng cáo.

### 4.1 Trigger

```
Khi: Phát hiện campaign trả về lỗi từ TikTok API:
  error_code IN ["FINANCIAL_REASON", "SUSPENDED_BALANCE", "INSUFFICIENT_BALANCE"]
```

Phát hiện qua:
- Response lỗi khi gọi update campaign
- Polling trạng thái campaign (`/campaign/gmv_max/info/`) mỗi 15 phút

### 4.2 Hành động

```
campaign_state.state = PAUSED
campaign_state.paused_reason = PAYMENT_FAILED
campaign_state.paused_at = now()
(Không gọi API pause — TikTok đã tự dừng do lỗi tài chính)

Hiển thị Seller:
  Pop-up màu đỏ: "Tài khoản TikTok Ads của bạn không đủ số dư.
                  Vui lòng nạp tiền để chiến dịch tiếp tục chạy."
  Button: "Nạp tiền ngay" → link đến trang thanh toán TikTok Ads
  
Thông báo: Push notification + email
```

---

## 5. EX-3 — Tỷ Lệ Hủy Đơn Cao — CRITICAL (Real-time)

**Mục đích:** Phát hiện sớm tấn công đặt/hủy ảo (click fraud) và đưa ra cảnh báo để Seller quyết định.

### 5.1 Trigger

```
Khi: (polling mỗi 15 phút)
  cancelled_orders_24h / total_orders_24h >= 0.25   ← ≥ 25%
  VÀ cancelled_orders_24h >= 10                     ← Đủ mẫu thống kê
```

### 5.2 Hành động

```
cancel_rate_tracker.critical_triggered_at = now()
campaign_state.state = PAUSED
campaign_state.paused_reason = CANCEL_RATE
campaign_state.paused_at = now()

Gọi API: POST /campaign/status/update/
  { status: "DISABLE" }    ← Tạm dừng trên TikTok

Thông báo Seller:
  Kênh: Push notification + SMS (khan cap)
  Nội dung: "CẢNH BÁO: Tỷ lệ hủy đơn chiến dịch [tên] vượt 25% trong 24h
             ({X} đơn hủy / {Y} tổng đơn). Chiến dịch đã tạm dừng.
             Đây có thể là dấu hiệu bị tấn công đặt/hủy ảo.
             Bấm để xem chi tiết và quyết định tiếp tục hay dừng hẳn."
  Action: Seller chọn "Tiếp tục chạy" hoặc "Dừng hẳn"

Nếu Seller chọn "Tiếp tục chạy":
  campaign_state.state = STABLE (hoặc WARMING nếu < 72h)
  Gọi API: POST /campaign/status/update/ { status: "ENABLE" }
```

**Lưu ý:** EX-3 tạm dừng camp và yêu cầu Seller xác nhận, khác với PRD gốc chỉ cảnh báo.

---

## 6. EX-4 — Dự Báo Hết Hàng (Real-time) — Phase 2

**Mục đích:** Cảnh báo sớm khi hàng sắp hết để Seller có thời gian nhập thêm.

### 6.1 Trigger

```
Khi: (polling tồn kho mỗi 15 phút)
  quantity_current <= 0.30 * quantity_initial   ← Còn ≤ 30% so với ban đầu
  HOẶC quantity_current <= 30                   ← Tuyệt đối còn ≤ 30 sản phẩm

  VÀ inventory_snapshot.low_stock_notified_at IS NULL   ← Chưa thông báo lần nào
```

### 6.2 Hành động

```
inventory_snapshot.low_stock_notified_at = now()

Giảm ngân sách campaign 10%:
  new_budget = daily_budget * 0.90
  PUT /campaign/gmv_max/update/ { budget: new_budget }
  campaign_state.daily_budget = new_budget

Thông báo Seller:
  Kênh: Push notification
  Nội dung: "Sản phẩm [tên] sắp hết hàng ({quantity_current} còn lại).
             Ngân sách chiến dịch đã giảm 10% để tránh quảng cáo khi hết hàng.
             Bấm để nhập thêm hàng."
```

**Khi hàng được nhập thêm (quantity_current tăng trở lại):**
```
inventory_snapshot.low_stock_notified_at = null   ← Reset để có thể cảnh báo lại
(Ngân sách không tự tăng lại — Seller tự điều chỉnh hoặc Optimization Engine xử lý)
```

---

## 7. EX-5 — Bảo Vệ Tổng Ngân Sách (Real-time + Batch)

**Mục đích:** Đảm bảo tổng ngân sách tất cả chiến dịch không vượt MDB Seller đặt.

### 7.1 Điều kiện kiểm tra

```
tong_daily_budget_tat_ca_camp = SUM(campaign_state.daily_budget)
  WHERE seller_id = {seller_id}
  AND state NOT IN (PAUSED)
```

### 7.2 Khi nào kiểm tra

- Trước mỗi hành động tăng ngân sách (C4) trong Optimization Engine
- Trước mỗi hành động tạo camp mới (C3 Hero, C5 Revival)
- Realtime khi nhận webhook đơn hàng mới (phòng trường hợp budget drift)

### 7.3 Hành động

```
Nếu tong_daily_budget_tat_ca_camp >= seller.max_daily_budget:
  → Không thực hiện hành động đang chờ (tạo camp / tăng budget)
  → Đóng băng tổng ngân sách:
      Với mỗi camp đang STABLE/HERO:
        campaign_state.budget_frozen = true
  → Thông báo Seller:
      Kênh: In-app + Push
      Nội dung: "Tổng ngân sách tất cả chiến dịch đã đạt giới hạn ngày {MDB}đ.
                 Hệ thống đã tạm dừng tăng ngân sách và tách chiến dịch mới."
```

---

## 8. EX-6 — Budget Một Camp ≥ 80% Daily Budget (Real-time)

**Mục đích:** Điều chỉnh ngân sách khi 1 camp đang tiêu gần đến mức budget ngày của nó, phân biệt theo thời gian chạy.

### 8.1 Trigger

```
Khi: (polling mỗi 15 phút)
  cost_today >= 0.80 * campaign_state.daily_budget
```

### 8.2 Logic phân nhánh

**Nhánh EX-6.1 — Camp chưa đủ 72h:**
```
Nếu now() < campaign_state.warming_ends_at:
  → Đây là ngoại lệ được vượt đóng băng 72h
  new_budget = daily_budget * (1 + 0.20)   ← Tăng tối đa 20%
  
  Guardrail EX-5:
    Nếu tong_budget_sau_tang > MDB: new_budget = MDB - tong_camp_khac
    Nếu new_budget <= daily_budget: không tăng, ghi log

  PUT /campaign/gmv_max/update/ { budget: new_budget }
  campaign_state.daily_budget = new_budget
```

**Nhánh EX-6.2 — Camp đã chạy >= 72h:**
```
Nếu now() >= campaign_state.warming_ends_at:
  Kiểm tra ROI:
  roi_actual = [lấy từ API báo cáo]
  
  Nếu roi_actual < 0.50 * roi_target:
    → ROI quá thấp, không nên tăng budget
    new_budget = daily_budget * (1 - 0.20)   ← Giảm 20%
    new_budget = max(new_budget, 200_000)     ← Tối thiểu 200.000đ
    PUT /campaign/gmv_max/update/ { budget: new_budget }
    campaign_state.daily_budget = new_budget
    Ghi log: { rule: "EX-6.2_DECREASE", reason: "low_roi" }
    
  Ngược lại (roi_actual >= 0.50 * roi_target):
    → ROI đủ tốt, tăng ngân sách tiếp
    new_budget = daily_budget * (1 + 0.20)
    [Áp Guardrail EX-5 tương tự EX-6.1]
    PUT /campaign/gmv_max/update/ { budget: new_budget }
    campaign_state.daily_budget = new_budget
    Ghi log: { rule: "EX-6.2_INCREASE", reason: "good_roi" }
```

---

## 9. Panic Switch

**Mục đích:** Cho phép Seller dừng tất cả chiến dịch ngay lập tức khi cần.

### 9.1 Trigger

```
Seller bấm nút "Dừng khẩn cấp" (Panic Switch) trên ZZP dashboard
```

### 9.2 Hành động

```
Với mỗi campaign của seller đang ở state != PAUSED:
  POST /campaign/status/update/
  { campaign_id: {tiktok_campaign_id}, status: "DISABLE" }
  
  campaign_state.state = PAUSED
  campaign_state.paused_reason = MANUAL
  campaign_state.paused_at = now()

Sau khi tất cả camp đã pause:
  Hiển thị: "Tất cả {N} chiến dịch đã được tạm dừng lúc {HH:mm}."
```

**Lưu ý:** Seller tự bật lại từng camp hoặc tất cả qua ZZP dashboard.

---

## 10. Sync Tồn Kho — Kho = 0

**Mục đích:** Tự động dừng chiến dịch khi hàng hết hoàn toàn, tránh TikTok tính phí ads cho click không có hàng giao.

### 10.1 Trigger

```
Khi: (polling tồn kho mỗi 15 phút)
  quantity_current = 0 với sản phẩm đang có trong campaign
```

### 10.2 Hành động

```
Với campaign chứa sản phẩm hết hàng:
  POST /campaign/status/update/
  { status: "DISABLE" }
  
  campaign_state.state = PAUSED
  campaign_state.paused_reason = OUT_OF_STOCK
  campaign_state.paused_at = now()

Thông báo Seller:
  Kênh: Push notification
  Nội dung: "Sản phẩm [tên] đã hết hàng. Chiến dịch [tên] đã tạm dừng.
             Lưu ý: Tạm dừng quảng cáo sẽ ảnh hưởng đến thuật toán TikTok
             khi bạn mở lại sau này.
             Bấm để nhập thêm hàng và khởi động lại chiến dịch."
```

**Khi hàng về (quantity_current > 0) và Seller muốn bật lại:**
```
Seller bấm "Bật lại chiến dịch" trên ZZP
→ POST /campaign/status/update/ { status: "ENABLE" }
→ campaign_state.state = STABLE (hoặc WARMING nếu Seller muốn reset 72h)
```

---

## 11. Polling & Event Architecture

### 11.1 Polling schedule

| Dữ liệu | Nguồn | Tần suất | Mục đích |
|---|---|---|---|
| Tồn kho sản phẩm | TikTok Shop API | Mỗi 15 phút | EX-4, EX kho=0 |
| Đơn hàng mới/hủy | TikTok Shop webhook | Real-time | EX-1 (buyer cancel) |
| Trạng thái campaign | TikTok Business API | Mỗi 15 phút | EX-2 (payment fail) |
| Metrics ROI, cost | TikTok Business API | Mỗi 15 phút | EX-3, EX-6 |
| Cancel rate 24h | Tính từ dữ liệu polling | Mỗi 15 phút | EX-3 |

### 11.2 Webhook từ TikTok Shop

TikTok Shop cần được cấu hình để gửi webhook khi:
- Đơn hàng được đặt (`order.created`)
- Đơn hàng bị hủy (`order.cancelled`) — cần `cancel_type` trong payload
- Đơn hàng hoàn thành (`order.completed`)

---

## 12. Test cases

| ID | Scenario | Expected |
|---|---|---|
| FI-01 | Buyer hủy đơn lần 1 | consecutive_cancels = 1, không bị chặn |
| FI-02 | Buyer hủy liên tiếp 10 lần | Buyer bị chặn, đẩy vào Exclusion List tất cả camp |
| FI-03 | Buyer hủy 9 lần, có 1 đơn thành công, rồi hủy 1 lần nữa | consecutive_cancels = 1 (đã reset), không bị chặn |
| FI-04 | API trả FINANCIAL_REASON | Campaign → PAUSED, pop-up đỏ, Push + email Seller |
| FI-05 | Cancel rate 30%, 15 đơn hủy | EX-3: camp pause, Push + SMS Seller |
| FI-06 | Cancel rate 30%, chỉ 5 đơn hủy | Không kích hoạt (< 10 đơn, không đủ mẫu) |
| FI-07 | Tồn kho giảm từ 100 → 25 | EX-4: cảnh báo, giảm ngân sách 10%, Push Seller |
| FI-08 | Tồn kho = 0 | Campaign → PAUSED ngay, Push Seller kèm cảnh báo thuật toán |
| FI-09 | Tổng budget tất cả camp = MDB | EX-5: dừng mọi tăng budget và tạo camp mới |
| FI-10 | Camp tiêu 80% DB, còn trong 72h | EX-6.1: tăng budget 20% |
| FI-11 | Camp tiêu 80% DB, đã qua 72h, ROI_actual = 30% ROI_target | EX-6.2: giảm budget 20% |
| FI-12 | Camp tiêu 80% DB, đã qua 72h, ROI_actual = 80% ROI_target | EX-6.2: tăng budget 20% |
| FI-13 | Seller bấm Panic Switch | Tất cả camp → PAUSED trong ≤ 60 giây |
| FI-14 | EX-6.1 nhưng tăng sẽ vượt MDB | Budget cắt tại MDB - tong_camp_khac |

---

*Phiên bản: v1 | 2026-06-07*
