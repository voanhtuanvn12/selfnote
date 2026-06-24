# Smart Ads Engine — Flow: Chạy Toàn Bộ Video Cho Sản Phẩm Đã Chọn

> **Nguồn:** Trích xuất từ `SmartAds_Final.drawio`
> **Scope:** Bắt đầu từ node "Chạy toàn bộ video cho sản phẩm đã chọn" (sau bước "Xác nhận khởi tạo")
> **Cập nhật:** 2026-06-11

---

## Mục lục

1. [Quy ước thuật ngữ](#1-quy-ước-thuật-ngữ)
2. [Tổng quan flow](#2-tổng-quan-flow)
3. [Phase 0 — Khởi tạo ngân sách & tạo campaign](#3-phase-0--khởi-tạo-ngân-sách--tạo-campaign)
4. [Phase 1 — 72h Learning (Target ROI)](#4-phase-1--72h-learning-target-roi)
5. [Phase 2 — Vòng lặp tối ưu mỗi 24h (Target ROI)](#5-phase-2--vòng-lặp-tối-ưu-mỗi-24h-target-roi)
6. [Ma trận quyết định ROI × DB](#6-ma-trận-quyết-định-roi--db)
7. [Tách camp Hero](#7-tách-camp-hero)
8. [Critical Monitor (chạy song song mọi lúc)](#8-critical-monitor-chạy-song-song-mọi-lúc)
9. [Pseudocode đầy đủ](#9-pseudocode-đầy-đủ)
10. [Điểm còn mở — cần xác nhận](#10-điểm-còn-mở--cần-xác-nhận)

---

## 1. Quy ước thuật ngữ

| Ký hiệu | Ý nghĩa |
|---|---|
| **MDB** | Max Daily Budget — mức trần ngân sách do seller nhập. **Hệ thống tuyệt đối không được chỉnh.** |
| **Budget_initial** | Ngân sách ngày khởi tạo campaign: **lần đầu (Phase 0)** = 40%/20% × MDB + sàn 200k; **tách camp do video "chết" trong Phase 2** = `MDB × 50%` (xem [Kiểm tra 1](#5-phase-2--vòng-lặp-tối-ưu-mỗi-24h-target-roi)) |
| **DB_campaign** | Ngân sách ngày của chiến dịch, do hệ thống ZZP thay đổi |
| **DB_actual** | Số tiền quảng cáo thực tế đã tiêu trong ngày |
| **ROI_target** | ROI tối thiểu seller mong muốn (min = 2) |
| **ROI_actual** | ROI thực tế đo được từ campaign |
| **GMV_daily** | Doanh thu ngày (không phải tích lũy) |

**Ví dụ minh hoạ:**
- Seller nhập MDB = 5.000.000đ
- Budget_initial = 5.000.000 × 20% = 1.000.000đ (vì MDB ≥ 2 triệu)
- Thực tế ads tiêu 700k → DB_actual = 700.000đ
- ROI tốt → hệ thống tăng DB_campaign 20%: 1.000.000 × 1.2 = 1.200.000đ

---

## 2. Tổng quan flow

```
[Xác nhận khởi tạo]
        │
        ▼
[Chạy toàn bộ video cho sản phẩm đã chọn]
        │
        ▼
[Tính Budget_initial]
        │
        ▼
[Mode: Target ROI — learning 72h]  ─────────────────────────►  [CRITICAL Monitor]
        │                                                              │ (song song, mọi lúc)
        │ chờ 72h
        ▼
[Mốc 72h]
        │
        │  ƯU TIÊN 1: Kiểm tra Hero Product trước
        │
        ├── Có sản phẩm >= 20 đơn? ──► ĐÚNG ──► [Tách camp Hero] ──► [24h learning]
        │                                                                      │
        │                                                         [Vòng lặp 24h — Phase 2]
        │
        │  ƯU TIÊN 2: Đánh giá ROI_actual & DB_actual
        │  (DB_actual là trục quyết định chính)
        │
        ├── DB < Budget_initial ──────────────────────────────►  [Giảm ROI_target 15%]
        │   (cả ROI thấp lẫn ROI tốt)                                    │
        │                                                    Check GMV_daily = 0?
        │                                             GMV>0 ──► [Vòng lặp 24h — Phase 2]
        │                                             GMV=0 (3 ngày liên tiếp) ──► [PAUSE CAMP]
        │
        └── DB ≥ Budget_initial ─┬── ROI thấp ──► [Giảm ngân sách 20%] ──► [Vòng lặp 24h — Phase 2]
                                 └── ROI tốt  ──► [Tăng ngân sách 20%] ──► [Vòng lặp 24h — Phase 2]
                                                                                    │
                                                                                    ▼
                                                                   [Phase 2 — tối ưu mỗi 24h]
                                                                       (Target ROI trên TikTok; xem mục 5)
```

---

## 3. Phase 0 — Khởi tạo ngân sách & tạo campaign

### Công thức Budget_initial

```
IF MDB < 2.000.000:
    Budget_initial = MDB × 40%
ELSE:
    Budget_initial = MDB × 20%

Budget_initial = MAX(Budget_initial, 200.000đ)   // sàn tối thiểu
```

### Tạo campaign

- 1 campaign duy nhất chứa **tất cả video** của các sản phẩm đã chọn
- **Mode trên TikTok: Target ROI** (ROAS bid / `ROI_target` theo seller). TikTok GMV Max **không** dùng chế độ Max Delivery cho luồng này.
- **72h đầu:** ZZP **không** áp ma trận điều chỉnh ROI×DB hàng ngày (Phase 2) — chỉ quan sát; đây là **cửa sổ learning**, không phải đổi sang mode API khác.
- Đồng thời: khởi động **CRITICAL Monitor** chạy song song

---

## 4. Phase 1 — 72h Learning (Target ROI)

> **Không có điều chỉnh ma trận Phase 2 nào trong 72h này.** Chỉ quan sát. Campaign vẫn là **Target ROI** trên TikTok. CRITICAL Monitor là ngoại lệ duy nhất được can thiệp.

Sau 72h, hệ thống đánh giá đồng thời **ROI_actual** và **DB_actual**:

### Kiểm tra Hero Product trước (ưu tiên cao nhất tại 72h)

Trước khi đánh giá ROI/DB, hệ thống kiểm tra Hero Product:

- **Có sản phẩm ≥ 20 đơn?** → Tách camp Hero → vào Phase 2 (Target ROI; hero có **24h learning** trước khi chạy vòng 24h đầy đủ — [mục 7](#7-tách-camp-hero))

Nếu không có Hero Product → tiếp tục đánh giá ROI × DB bên dưới.

---

**DB_actual là trục quyết định chính**, ROI_actual quyết định tăng hay giảm budget khi DB đủ lớn:

### Nhánh A — DB_actual < Budget_initial
*(cả hai trường hợp ROI thấp và ROI tốt đều ra kết quả giống nhau)*

1. Giảm ROI_target 15%: `ROI_target_mới = ROI_target × (1 - 15%)`
2. Kiểm tra **GMV_daily = 0?**
   - **GMV > 0**: → vào Phase 2 (vòng 24h)
   - **GMV = 0**: → kiểm tra bộ đếm ngày liên tiếp
     - Chưa đủ 3 ngày: Giảm ROI 15% tiếp, chờ ngày sau, lặp lại check
     - Đủ 3 ngày liên tiếp: **PAUSE CAMP**, thông báo seller

> **Lưu ý:** Bộ đếm ngày liên tiếp tính từ ngày đầu chạy, không phải từ mốc 72h.

### Nhánh B — DB_actual ≥ Budget_initial

| ROI_actual | Hành động | Công thức |
|---|---|---|
| `1.0 < ROI_actual ≤ ROI_target × 0.7` (ROI thấp) | Giảm DB_campaign 20% | `DB_campaign (hôm sau) = DB_campaign (hôm nay) × (1 - 20%)` |
| `ROI_actual > ROI_target × 0.7` (ROI tốt) | Tăng DB_campaign 20% | `DB_campaign (hôm sau) = DB_campaign (hôm nay) × 1.2` |

→ Sau đó: **vào Phase 2** (vòng 24h / ma trận ROI×DB; không qua GMV check)

---

## 5. Phase 2 — Vòng lặp tối ưu mỗi 24h (Target ROI)

> **Chu kỳ:** Mỗi ngày lịch (00:00 – 23:59), **không phải** rolling 24h từ lúc chỉnh sửa.
> **Giới hạn:** Mỗi campaign chỉ được thay đổi **tối đa 1 lần / ngày**.

Mỗi ngày hệ thống thực hiện **4 kiểm tra** theo thứ tự:

### Thứ tự ưu tiên xử lý trong 1 ngày

Nếu cùng 1 ngày xảy ra nhiều trigger, hệ thống xử lý **tuần tự** theo thứ tự ưu tiên:

| Ưu tiên | Kiểm tra | Ghi chú |
|---|---|---|
| **1 (cao nhất)** | Video "chết" | → Critical; tách camp — **MDB×50%**, **Target ROI** ngay |
| **2** | Hero Product xuất hiện | → tách camp Hero |
| **3 (thấp nhất)** | ROI thấp → tổ hợp ROI_actual × DB_actual | → điều chỉnh ROI/budget |

### Kiểm tra 1 (ưu tiên cao nhất) — Video "chết"

**Điều kiện:** Video từng đạt ≥ 20 đơn hàng, nhưng 48h gần nhất không có đơn mới

**Hành động:** Nhảy sang nhánh Critical → tách các video này ra thành 1 campaign mới, **Target ROI** trên TikTok và **vào vòng lặp tối ưu 24h ngay** (không chờ cửa sổ learning 24h như Hero, không chờ 72h như camp gốc). Dừng xử lý các kiểm tra còn lại trong ngày.

**Ngân sách khởi tạo (`Budget_initial`)** cho campaign mới này **trong vận hành (Phase 2):**

- `Budget_initial = MDB × 50%` (cùng mức khởi tạo ngân sách ngày với [Hero camp — mục 7](#7-tách-camp-hero); khác chỗ Hero có **24h learning** trước khi chạy `runOneDayCycle` đầy đủ).

> **Khác Phase 0:** Campaign **đầu tiên** khi khởi tạo sản phẩm vẫn dùng công thức 40%/20% + sàn 200k ([mục 3](#3-phase-0--khởi-tạo-ngân-sách--tạo-campaign)); chỉ bước **tách camp do video "chết"** dùng `MDB × 50%` và Target ROI ngay.

### Kiểm tra 2 — Hero Product

**Điều kiện:** Có 1 sản phẩm bất kỳ trong campaign đạt ≥ 20 đơn hàng

**Hành động:** Tách campaign Hero (xem [mục 7](#7-tách-camp-hero))

> **Lưu ý quan trọng:** Camp Hero **không được tách thêm** hero camp nữa. Tối đa 2 tầng camp.

### Kiểm tra 3 (ưu tiên thấp nhất) — Tổ hợp ROI_actual × DB_actual

Chỉ thực hiện khi không có video chết và không có hero product trong ngày hôm đó.

Xem [Ma trận quyết định](#6-ma-trận-quyết-định-roi--db)

### Kiểm tra 4 — GMV = 0

**Điều kiện:** Doanh thu ngày hôm đó = 0

| Bộ đếm ngày liên tiếp GMV = 0 | Hành động |
|---|---|
| Chưa đủ 3 ngày | Giảm ROI_target 15%, reset check ngày hôm sau |
| Đủ 3 ngày liên tiếp | **PAUSE CAMP**, thông báo seller |
| GMV > 0 | Reset bộ đếm về 0 |

---

## 6. Ma trận quyết định ROI × DB

> **Chỉ áp dụng tại mốc 24h** (Phase 2 — Target ROI mode).
> Mốc 72h có logic riêng, xem [Phase 1](#4-phase-1--72h-learning-target-roi).

Threshold so sánh DB_actual là `DB_campaign × 0.5` (nửa ngân sách campaign hiện tại), không phải MDB.

### ROI thấp — `1.0 < ROI_actual ≤ ROI_target × 0.7`

| DB_actual | Hành động | Công thức |
|---|---|---|
| `< DB_campaign × 0.5` | Giảm ROI_target 15% | `ROI_target_mới = ROI_target × (1 - 15%)` |
| `DB_campaign×0.5 ≤ DB_actual < MDB` | Tăng ROI_target 15% **+** Giảm DB_campaign 20% | `ROI_target_mới = ROI_target × 1.15` / `DB_mới = DB × 0.8` |
| `= MDB` | Giảm DB_campaign 50% | `DB_mới = DB_campaign × (1 - 50%)` |

### ROI tốt — `ROI_actual > ROI_target × 0.7`

| DB_actual | Hành động | Công thức |
|---|---|---|
| `< DB_campaign × 0.5` | Giảm ROI_target 15% | `ROI_target_mới = ROI_target × (1 - 15%)` |
| `DB_campaign×0.5 ≤ DB_actual < MDB` | Tăng DB_campaign 20% | `DB_mới = DB_campaign × 1.2` |
| `= MDB` | Tăng ROI_target 15% | `ROI_target_mới = ROI_target × 1.15` |

**Ràng buộc chung:**
- DB_campaign mới tối thiểu = 200.000đ/ngày
- Tổng DB_campaign của **tất cả** các camp không được vượt MDB

---

## 7. Tách camp Hero

```
Trigger: 1 sản phẩm trong camp đạt >= 20 đơn
         VÀ camp hiện tại không phải hero camp (max 2 tầng)

Bước 1 — Xử lý camp gốc:
  - Gỡ hero product khỏi camp gốc
  - Giảm ngân sách camp gốc tối đa 20%
  - Ngân sách mới tối thiểu = 200.000đ/ngày

Bước 2 — Tạo Hero Camp:
  - Videos: tất cả video của hero product
  - daily_budget = MDB × 50%
  - mode = TARGET ROI (ROAS bid = ROI_target; TikTok không dùng Max Delivery)
  - is_hero_camp = TRUE  (chặn tách tầng 3)

Bước 3 — Hero Camp lifecycle:
  - **24h learning:** Target ROI trên TikTok; ZZP không chạy ma trận ROI×DB hàng ngày (giống tinh thần Phase 1 nhưng cửa sổ 24h)
  - Sau 24h: vào **vòng lặp 24h** đầy đủ (Phase 2)
```

---

## 8. Critical Monitor (chạy song song mọi lúc)

> Critical monitor **bắt đầu ngay khi campaign được tạo**, không chờ 72h.
> Đây là **ngoại lệ** được phép can thiệp ngay cả trong giai đoạn đóng băng 72h.

### C1 — Chặn khách hủy đơn
```
Trigger: Số đơn bị hủy đạt ngưỡng seller đã cài (optional setting)
Action:  Chặn các khách hàng có hành vi hủy đơn
```

### C2 — Tỷ lệ hủy đơn cao
```
Trigger: Tỷ lệ hủy >= 25% tổng đơn campaign
         VÀ số lượng đơn hủy >= 10
Action:  Pause campaign + Thông báo seller quyết định
```

### C3 — Tồn kho thấp
```
Trigger: Số lượng bất kỳ sản phẩm nào trong camp:
           <= 30% số lượng ban đầu
           HOẶC <= 30 sản phẩm tuyệt đối
Action:  Giảm ngân sách campaign 10%
         Ngân sách mới tối thiểu = 200.000đ/ngày
         Thông báo seller
```

### C4 — Tổng ngân sách chạm MDB
```
Trigger: Tổng DB_campaign của TẤT CẢ các camp >= MDB
Action:  Dừng tách camp mới
         Dừng tăng ngân sách bất kỳ camp nào
         Đóng băng tổng ngân sách = MDB
         Thông báo seller
```

### C5 — Vấn đề thanh toán
```
Loại tài khoản:
  Trả trước (Ads Manager):
    - Trừ tiền real-time
    - ZZP kiểm tra số dư sau mỗi lần trừ
    - Hết tiền / lỗi thẻ:
        + Nếu camp vẫn đang chạy → cảnh báo + thông báo seller
        + Nếu camp đã dừng       → thông báo seller

  Trả sau (TikTok Seller Center):
    - TikTok tự khấu trừ từ doanh thu shop / ví shop
    - Trigger thanh toán: chạm ngưỡng HOẶC đến ngày thanh toán
    - ZZP kiểm tra số dư sau khi TikTok trừ
```

---

## 9. Pseudocode đầy đủ

```pseudocode
// ================================================================
// ZZP SMART ADS ENGINE
// Entry: Chạy toàn bộ video cho sản phẩm đã chọn
// ================================================================

CONSTANTS:
  MIN_BUDGET_INITIAL = 200_000   // VND
  MIN_BUDGET_DAILY   = 200_000   // VND


// ================================================================
// ENTRY POINT
// ================================================================
FUNCTION runAllVideos(products, MDB, ROI_target, settings):

  // --- Tính Budget_initial ---
  IF MDB < 2_000_000:
    budget_initial = MDB * 0.40
  ELSE:
    budget_initial = MDB * 0.20
  budget_initial = MAX(budget_initial, MIN_BUDGET_INITIAL)

  // --- Tạo campaign ---
  campaign = createCampaign(
    videos        = getAllVideosOf(products),
    daily_budget  = budget_initial,
    mode          = TARGET_ROI,
    roi_target    = ROI_target,
    is_hero_camp  = FALSE
  )

  // --- Critical monitor chạy song song ngay lập tức ---
  startCriticalMonitor(campaign, MDB, settings)  // async, không block

  // --- Phase 1: 72h learning ---
  run72hLearningPhase(campaign, MDB, ROI_target, budget_initial)


// ================================================================
// PHASE 1: 72H LEARNING
// ================================================================
FUNCTION run72hLearningPhase(campaign, MDB, ROI_target, budget_initial):

  waitUntil(campaign.startTime + 72h)

  // ---- ƯU TIÊN 1: Kiểm tra Hero Product trước ----
  heroProduct = findProductWithOrders(campaign, minOrders = 20)
  IF heroProduct != NULL:
    splitHeroCampaign(heroProduct, campaign, ROI_target, MDB)
    startDailyOptimizationLoop(campaign, ROI_target, MDB)
    RETURN

  // ---- ƯU TIÊN 2: Đánh giá ROI × DB ----
  ROI_actual = campaign.getROILast72h()
  DB_actual  = campaign.getSpendLast72h()

  // DB_actual là trục quyết định chính
  IF DB_actual < budget_initial:
    // Nhánh A: chi tiêu thấp → nới ROI target (cả ROI tốt lẫn ROI thấp)
    ROI_target = ROI_target * 0.85
    campaign.setROITarget(ROI_target)
    checkZeroGMVAndContinue(campaign, ROI_target, MDB, zeroDayCount = 0)

  ELSE:
    // Nhánh B: chi tiêu đủ → ROI quyết định tăng hay giảm budget
    IF ROI_actual > ROI_target * 0.7:
      // ROI tốt → tăng ngân sách
      new_budget = MIN(campaign.daily_budget * 1.20, MDB)
    ELSE:
      // ROI thấp → giảm ngân sách
      new_budget = campaign.daily_budget * 0.80

    campaign.setDailyBudget(MAX(new_budget, MIN_BUDGET_DAILY))
    startDailyOptimizationLoop(campaign, ROI_target, MDB)


// ================================================================
// ZERO GMV CHECK
// (dùng chung ở 72h và vòng lặp hàng ngày)
// ================================================================
FUNCTION checkZeroGMVAndContinue(campaign, ROI_target, MDB, zeroDayCount):

  IF campaign.getTodayGMV() > 0:
    campaign.resetZeroDayCounter()
    startDailyOptimizationLoop(campaign, ROI_target, MDB)
    RETURN

  zeroDayCount += 1

  IF zeroDayCount >= 3:
    campaign.pause()
    notifySeller("PAUSE: 3 ngày liên tiếp GMV = 0")
    RETURN

  // Chưa đủ 3 ngày → giảm ROI target, chờ ngày hôm sau
  ROI_target = ROI_target * 0.85
  campaign.setROITarget(ROI_target)
  waitUntil(nextMidnight())
  checkZeroGMVAndContinue(campaign, ROI_target, MDB, zeroDayCount)


// ================================================================
// PHASE 2: VÒNG LẶP 24H
// ================================================================
FUNCTION startDailyOptimizationLoop(campaign, ROI_target, MDB):
  WHILE campaign.isActive():
    waitUntil(nextMidnight())  // 00:00 mỗi ngày lịch
    IF NOT campaign.isActive(): BREAK
    runOneDayCycle(campaign, ROI_target, MDB)


FUNCTION runOneDayCycle(campaign, ROI_target, MDB):

  IF campaign.hasChangedToday(): RETURN  // Max 1 thay đổi/ngày/camp

  // ================================================================
  // THỨ TỰ ƯU TIÊN:
  //   1. Video "chết"  → tách camp MDB×50% + Target ROI, dừng các bước còn lại
  //   2. Hero Product  → tách camp Hero
  //   3. ROI × DB      → điều chỉnh ROI / budget
  // ================================================================

  // ---- ƯU TIÊN 1: Video "chết" (cao nhất) ----
  deadVideos = getDeadVideos(campaign)
  IF deadVideos.isNotEmpty():
    splitDeadVideoCampaign(deadVideos, campaign, ROI_target, MDB)
    RETURN  // Dừng — không xử lý thêm trong ngày này

  // ---- ƯU TIÊN 2: Hero Product ----
  IF NOT campaign.isHeroCamp():  // Tối đa 2 tầng camp
    heroProduct = findProductWithOrders(campaign, minOrders = 20)
    IF heroProduct != NULL:
      splitHeroCampaign(heroProduct, campaign, ROI_target, MDB)
      RETURN  // Dừng — không xử lý thêm trong ngày này

  // ---- ƯU TIÊN 3: Tổ hợp ROI_actual × DB_actual (thấp nhất) ----
  ROI_actual = campaign.getTodayROI()
  DB_actual  = campaign.getTodaySpend()
  adjustRoiAndBudget(campaign, ROI_actual, ROI_target, DB_actual, MDB)

  // ---- GMV = 0 check (độc lập, không phụ thuộc thứ tự trên) ----
  IF campaign.getTodayGMV() == 0:
    count = campaign.incrementZeroDayCounter()
    IF count >= 3:
      campaign.pause()
      notifySeller("PAUSE: 3 ngày liên tiếp GMV = 0")
    ELSE:
      ROI_target = ROI_target * 0.85
      campaign.setROITarget(ROI_target)
  ELSE:
    campaign.resetZeroDayCounter()


// ================================================================
// ĐIỀU CHỈNH ROI + BUDGET (ma trận 24h)
// ================================================================
// Threshold: DB_campaign × 0.5 (nửa ngân sách campaign hiện tại)
FUNCTION adjustRoiAndBudget(campaign, ROI_actual, ROI_target, DB_actual, MDB):

  db_low_threshold = campaign.daily_budget * 0.5   // DB_campaign × 0.5

  IF ROI_actual > ROI_target * 0.7:   // --- ROI TỐT ---

    IF DB_actual < db_low_threshold:
      // Chi tiêu thấp → nới ROI target
      campaign.setROITarget(ROI_target * 0.85)

    ELSE IF DB_actual < MDB:          // DB_campaign×0.5 ≤ DB_actual < MDB
      // Chi tiêu vừa → tăng ngân sách
      new_budget = campaign.daily_budget * 1.20
      campaign.setDailyBudget(MIN(new_budget, MDB))

    ELSE:                             // DB_actual = MDB
      // Chạm trần → tăng ROI target (siết lại để giảm chi tiêu)
      campaign.setROITarget(ROI_target * 1.15)

  ELSE:                               // --- ROI THẤP ---

    IF DB_actual < db_low_threshold:
      // Chi tiêu thấp → nới ROI target
      campaign.setROITarget(ROI_target * 0.85)

    ELSE IF DB_actual < MDB:          // DB_campaign×0.5 ≤ DB_actual < MDB
      // Chi tiêu vừa nhưng ROI không đạt → tăng ROI target + giảm ngân sách
      campaign.setROITarget(ROI_target * 1.15)
      new_budget = campaign.daily_budget * 0.80
      campaign.setDailyBudget(MAX(new_budget, MIN_BUDGET_DAILY))

    ELSE:                             // DB_actual = MDB
      // Chạm trần + ROI kém → giảm mạnh ngân sách
      new_budget = campaign.daily_budget * 0.50
      campaign.setDailyBudget(MAX(new_budget, MIN_BUDGET_DAILY))


// ================================================================
// TÁCH CAMP HERO
// ================================================================
FUNCTION splitHeroCampaign(heroProduct, parentCampaign, ROI_target, MDB):

  // Gỡ khỏi camp gốc
  parentCampaign.removeProduct(heroProduct)
  new_parent_budget = parentCampaign.daily_budget * 0.80
  parentCampaign.setDailyBudget(MAX(new_parent_budget, MIN_BUDGET_DAILY))

  // Tạo hero camp
  heroCampaign = createCampaign(
    videos        = getAllVideosOf(heroProduct),
    daily_budget  = MDB * 0.50,
    mode          = TARGET_ROI,
    roi_target    = ROI_target,
    is_hero_camp  = TRUE
  )

  // 24h learning: không gọi runOneDayCycle; sau đó vào Phase 2
  waitUntil(heroCampaign.startTime + 24h)
  startDailyOptimizationLoop(heroCampaign, ROI_target, MDB)


// ================================================================
// TÁCH CAMP CHO VIDEO "CHẾT"
// (video từng >=20 đơn nhưng 48h không có đơn mới)
// ================================================================
FUNCTION splitDeadVideoCampaign(deadVideos, parentCampaign, ROI_target, MDB):
  // MDB×50%; vào vòng 24h ngay (không chờ 24h learning như Hero)
  budget = MDB * 0.50

  newCamp = createCampaign(
    videos        = deadVideos,
    daily_budget  = budget,
    mode          = TARGET_ROI,
    roi_target    = ROI_target,
    is_hero_camp  = FALSE
  )
  parentCampaign.removeVideos(deadVideos)
  startDailyOptimizationLoop(newCamp, ROI_target, MDB)


// ================================================================
// CRITICAL MONITOR (async, event-driven)
// ================================================================
FUNCTION startCriticalMonitor(campaign, MDB, settings):

  ON cancelledOrders.count >= settings.cancelBlockThreshold:
    blockBadCustomers(campaign)

  ON (cancelRate >= 0.25 AND cancelledOrders.count >= 10):
    campaign.pause()
    notifySeller("Tỷ lệ đơn hủy cao")

  ON (anyProduct.stock <= anyProduct.initialStock * 0.30
      OR anyProduct.stock <= 30):
    new_budget = campaign.daily_budget * 0.90
    campaign.setDailyBudget(MAX(new_budget, MIN_BUDGET_DAILY))
    notifySeller("Tồn kho thấp — đã giảm budget 10%")

  ON totalBudgetAllCampaigns() >= MDB:
    freezeAllBudgets(cap = MDB)
    stopCreatingNewCampaigns()
    notifySeller("Đạt ngưỡng MDB — đóng băng tổng ngân sách")

  ON paymentFailed OR balanceDepleted:
    IF anyCampaignStillRunning():
      notifySeller("Lỗi thanh toán — kiểm tra tài khoản")
    ELSE:
      notifySeller("Tất cả camp đã dừng do lỗi thanh toán")


// ================================================================
// HELPERS
// ================================================================
FUNCTION calculateBudgetInitial(MDB):
  IF MDB < 2_000_000:
    budget = MDB * 0.40
  ELSE:
    budget = MDB * 0.20
  RETURN MAX(budget, MIN_BUDGET_INITIAL)

FUNCTION getDeadVideos(campaign):
  RETURN [v FOR v IN campaign.videos
            IF v.lifetimeOrders >= 20 AND v.ordersPast48h == 0]

FUNCTION findProductWithOrders(campaign, minOrders):
  FOR product IN campaign.products:
    IF product.ordersInCampaign >= minOrders:
      RETURN product
  RETURN NULL
```

---

## 10. Điểm còn mở — cần xác nhận

Các điểm dưới đây chưa được làm rõ hoàn toàn từ diagram và cần brainstorm thêm trước khi dev implement:

### ✅ Q1 — Ma trận ROI × DB khi ROI thấp — ĐÃ XÁC NHẬN

Khi `1.0 < ROI_actual ≤ ROI_target × 0.7` + `DB_actual = MDB`:
→ **Giảm ROI_target 15% + Giảm DB_campaign 50%**
`DB_campaign (hôm sau) = DB_campaign (hôm nay) × (1 - 50%)`

> Vẫn còn mở: ROI thấp + `MDB×0.7 ≤ DB < MDB` → có giảm budget không?

### ✅ Q2 — Budget & mode của camp "video chết" — ĐÃ XÁC NHẬN

Campaign mới sau khi tách video "chết" trong vận hành: **`Budget_initial = MDB × 50%`**, **Target ROI** trên TikTok và **vòng 24h ngay**. Chi tiết: [Phase 2 — Kiểm tra 1](#5-phase-2--vòng-lặp-tối-ưu-mỗi-24h-target-roi).

### ✅ Q3 — Hero camp learning period — ĐÃ XÁC NHẬN

Hero camp: **24h learning** (Target ROI trên TikTok; ZZP chưa chạy ma trận ROI×DB hàng ngày), sau đó vòng 24h đầy đủ. Camp gốc: **72h learning** tương tự trước mốc đánh giá đầu tiên.

### ❓ Q4 — Mode "Custom"

Tại bước "Chọn chế độ", có nhánh `ZZP Auto Pilot` và `Custom`. Flow `Custom` đi đâu? Trong diagram không thể hiện nhánh tiếp theo của `Custom`.

### ✅ Q5 — Thứ tự ưu tiên trong 1 ngày — ĐÃ XÁC NHẬN

Xử lý **tuần tự**, ưu tiên từ cao xuống thấp. Khi trigger ưu tiên cao hơn xảy ra → dừng, không xử lý các bước còn lại trong ngày:

1. **Video "chết"** → Critical; camp mới **MDB×50%**, **Target ROI** ngay
2. **Hero Product xuất hiện** → tách camp Hero
3. **Tổ hợp ROI_actual × DB_actual** → điều chỉnh ROI / budget

---

*File này được tạo tự động từ phân tích file `SmartAds_Final.drawio` — cập nhật khi có thêm xác nhận từ team.*
