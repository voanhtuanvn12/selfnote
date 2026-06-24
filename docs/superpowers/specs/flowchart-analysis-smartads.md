# Phan tich Flowchart — SmartAds Optimization

> Nguon: SmartAds Optimization.drawio.png + xac nhan truc tiep tu product owner.
> Day la ban cuoi da duoc xac nhan — dung lam nguon chinh de viet PRD va SRS.

---

## LUU Y: FLOWCHART vs PRD GOC (Demo PRD.md)

Flowchart moi hon. Co 3 diem thay doi — flowchart la nguon dung:

| # | PRD goc | Flowchart moi (DUNG) |
|---|---|---|
| 1 | Hero split: giu nguyen san pham o camp goc (BR-4) | Hero split: XOA hero khoi camp goc, giam budget camp goc |
| 2 | Batch chay luc 23h30 | Monitoring theo ngay duong lich 00:00-23:59, toi da 1 lan thay doi/camp/ngay |
| 3 | Budget khoi tao: [CAN LAM RO] | Budget khoi tao = MDB x 20% |

---

## TONG QUAN CAU TRUC

Flowchart chia lam 4 vung chinh:

| Vung | Noi dung |
|---|---|
| A — Onboarding | Vao ZZP → tao campaign → chon mode |
| B — Exception / CRITICAL | Cac truong hop ngoai le co the vuot dong bang 72h |
| C — Optimization Logic | Logic chinh: dieu chinh ROI, ngan sach, Hero split |
| D — Actions & Notifications | Goi TikTok API + thong bao Seller |

---

## VUNG A — ONBOARDING FLOW

```
[Vao trang ZZP]
      |
[Authorize TikTok Ads Account]
      |
[Da co campaign ZZP?]
   Co /    \ Chua
     |      |
[Tiep tuc]  [Tao campaign moi]
              |
         [Ngan sach ngay toi da (MDB)]
              |
         [Suggest ROI tu Bang chi phi ZZP]
         (data da sync tu service noi bo ZZP,
          Seller co the chinh hoac giu nguyen)
              |
         [Bat tinh nang ZZP hay khong?]
           /         \
         Khong        Co
          |            |
       [Custom]    [Chon san pham]
       (chua lam)       |
                [Creative Pool]
                (tu SAM: toan bo video KOC cua shop)
                        |
                [Spinner / Confirm]
                        |
                [Chay toan bo SP + toan bo video]
                Ngan sach khoi tao = MDB x 20%
```

**Chi tiet:**

### A1. Authorize TikTok Ads
- Luong OAuth chinh thuc TikTok Business API
- Sau khi xong: trang thai "Connected" tren ZZP

### A2. Suggest ROI
- ZZP lay data chi phi tu service noi bo (COGS, phi ship, hoa hong KOC...)
- Tinh ROAS hoa von = Gia ban / Lai gop truoc ads
- Hien thi so goi y, Seller co the chinh tay truoc khi launch

### A3. Custom mode (CHUA LAM)
- "Phuong an thay the" = Custom = Seller quan ly campaign tren TikTok Ads nhu binh thuong
- ZZP khong ap autopilot, khong tu dong gi
- Day la Phase tuong lai, KHONG nam trong Phase 1 hoac Phase 2 hien tai

### A4. Chon san pham
- Mac dinh chon tat ca san pham trong TikTok Shop
- Sync real-time tu TikTok Shop API

### A5. Creative Pool (tu SAM)
- Buoc nay nam NGAY SAU chon san pham
- Lay toan bo video KOC tu he thong SAM cua shop
- Phase 1 Autopilot: chay TOAN BO san pham va TOAN BO video (khong loc)

### A6. Ngan sach khoi tao
- He thong tu dong dat: Ngan sach = MDB x 20%
- Vi du: Seller dat max 1.000.000d/ngay → camp chay voi 200.000d/ngay luc dau

---

## VUNG B — EXCEPTION / CRITICAL (Co the vuot dong bang 72h)

> Day la cac truong hop ngoai le xay ra bat ky luc nao (ke ca trong 72h dau bi dong bang).
> Khi gap cac truong hop nay, he thong DUOC PHEP hanh dong ngay, khong can doi het 72h.

### EX-1 — Chan khach hang bung don (Real-time)
- **Khi:** Don Ads bi huy voi Cancel_Type = BUYER_CANCEL
- Dem lien tiep theo tung buyer (don thanh cong → reset dem)
- **Khi buyer dat N lan lien tiep** (mac dinh N=2):
  → Luu tt_buyer_id vao blacklist
  → Goi API day vao Exclusion Audience List cua camp

### EX-2 — Thanh toan loi (Real-time)
- **Khi:** API TikTok tra FINANCIAL_REASON hoac SUSPENDED_BALANCE
- **Thi:** Tam dung campaign + Pop-up do + link ve trang nap tien TikTok Ads

### EX-3 — Ti le don huy cao CRITICAL (Real-time)
- **Khi:** Ti le don huy >= 25% / tong don chien dich
  **VA** So don huy >= 10
- **Thi:** Tam dung campaign + Thong bao Seller de Seller tu quyet dinh

> Khac voi PRD goc: PRD goc chi "canh bao, van chay" — flowchart moi la "TAM DUNG + thong bao cho seller quyet dinh"

### EX-4 — Du bao het hang (Real-time) — Phase 2
- **Khi:** So luong 1 san pham bat ky trong camp:
  <= 30% so luong ban dau
  HOAC <= 30 san pham
- **Thi (Phase 2):** Dung tinh nang du bao het hang de canh bao truoc cho Seller
- **Thi (ngay lap tuc):** Giam ngan sach 10%

### EX-5 — Tran ngan sach tong the (Real-time)
- **Khi:** Tong ngan sach tat ca cac camp >= MDB (ngan sach ngay Seller dat)
- **Thi:**
  - Ngung tach camp moi
  - Ngung tang budget bat ky camp nao
  - Dong bang tong ngan sach thiet lap = MDB
  - Thong bao Seller

### EX-6 — Budget mot camp >= 80% DB (Real-time)
- **Khi:** Budget thuc te cua 1 camp >= 80% daily budget cua camp do
- **Neu camp chua chay >= 72h (EX-6.1):**
  → Tang budget (toi da 20%/lan, hang ngay)
- **Neu camp da chay >= 72h (EX-6.2):**
  → Kiem tra: ROI thuc te < 50% ROI target?
    - Co: Giam ngan sach camp 20%/lan
    - Khong: Tang budget (toi da 20%/lan, hang ngay)

---

## VUNG C — OPTIMIZATION LOGIC CHINH

> Toan bo logic nay chay sau 72h dau tien (tru cac ngoai le o Vung B).
> Chu ky: moi 24h theo ngay duong lich (00:00 - 23:59).
> Rang buoc: Toi da 1 lan thay doi (tang/giam ROI hoac ngan sach) tren moi camp trong 1 ngay.

### Khoi tao
```
Chay toan bo san pham + toan bo video
Ngan sach = MDB x 20%
→ Bat dau theo doi (72h dau: chi EX-1 den EX-6 hoat dong)
```

### C1 — Giam ROI (Logic 1)
**Khi xay ra 1 trong 2:**
- Budget thuc te < 20% daily budget (DB)
- HOAC: `1.0 < ROI_actual <= ROI_target x 0.7`

**Thi:** Giam ROI (toi da 15%/lan, hang ngay)

**Ket thuc dong (check them):**
- Neu `Tong tien da tieu >= MDB` VA `GMV = 0` → **PAUSE CAMP**

---

### C2 — Tang ROI (Logic 2)
**Khi:** `50% DB <= Budget thuc te <= 80% DB`

**Thi:** Tang ROI (toi da 20%/lan, hang ngay)

---

### C3 — Hero Product Split (Logic 3)
**Khi:** >= 20 don hang / 1 san pham

**Thi:**
1. Tao camp moi (Hero Camp): Ngan sach = DB x 120%
2. **Xoa san pham Hero khoi camp goc** (KHAC PRD GOC)
3. Giam ngan sach camp goc: toi da 20%/lan, toi thieu 200.000d/ngay
4. Camp moi: bat lai flow 72h
5. Camp goc: monitoring moi 24h

---

### C4 — Tang Budget (Logic 4)
**Khi:** `ROI_actual >= ROI_target`

**Thi:** Tang budget (toi da 20%/lan, hang ngay)

---

### C5 — Hoi sinh Video (Logic 5)
**Khi:**
- `Tong tien da tieu >= MDB VA GMV = 0` = SAI (van co don)
- VA video da tung >= 20 don nhung khong co don moi trong 48h

**Thi:**
1. Tach camp moi chi chua video nay: ngan sach = 100.000d/ngay
2. Camp moi: bat lai flow 72h
3. Camp goc: monitoring moi 24h

---

### Chu ky va rang buoc thay doi

```
Moi 24h THEO NGAY DUONG LICH: 00:00 - 23:59
(KHONG tinh tu thoi diem chinh sua, tinh theo ngay)

Tren moi camp:
- Chi duoc TANG hoac GIAM (ROI hoac ngan sach) TOI DA 1 LAN trong 1 ngay
- Khong duoc tang roi lai giam, hoac giam roi lai tang trong cung 1 ngay
```

---

## VUNG D — ACTIONS & NOTIFICATIONS

### D1. Goi TikTok API
Sau moi quyet dinh toi uu, he thong goi:
- `PUT /campaign/gmv_max/update/` → cap nhat ROI_target, daily_budget
- `POST /campaign/status/update/` → Pause/Resume campaign
- `POST /campaign/gmv_max/create/` → Tao camp Hero moi
- `POST /exclusion_audience/update/` → Chan buyer

### D2. Chinh sach thong bao Seller

| Su kien | Kenh | Do khan |
|---|---|---|
| Thay doi ROI/budget thuong ngay | In-app | Thap |
| Camp bi PAUSE (het hang, thanh toan) | Push notification | Cao |
| CRITICAL (EX-3, ti le huy cao) | Push + SMS | Khan cap |
| EX-5: dat tran ngan sach MDB | In-app + Push | Cao |
| EX-4: sap het hang (Phase 2) | In-app + Push | Trung binh |
| OAuth token het han | Banner + Email | Cao |

### D3. Khi OAuth token het han
- Dung moi optimization job cua Seller do
- **Khong tu pause campaign** (campaign van chay tren TikTok theo config cu)
- Hien banner "Ket noi TikTok da het han" + email/push
- Sau khi Seller re-auth: tiep tuc optimize binh thuong

### D4. API TikTok down
- Retry trong 30 phut
- Neu van fail: bo qua lan do, giu nguyen config cu
- Alert noi bo ZZP
- Thong bao Seller (da xac nhan: co thong bao Seller khi skip)

---

## TONG HOP: MAPPING LOGIC → RULES

| Logic | Ten | Loai | Chu ky |
|---|---|---|---|
| C1 | Giam ROI | Optimization | 24h / ngay duong lich |
| C2 | Tang ROI | Optimization | 24h / ngay duong lich |
| C3 | Hero Product Split | Scaling | 24h / ngay duong lich |
| C4 | Tang Budget | Scaling | 24h / ngay duong lich |
| C5 | Hoi sinh Video | Scaling | 24h / ngay duong lich |
| EX-1 | Chan buyer bung don | Bao ve | Real-time |
| EX-2 | Thanh toan loi | Bao ve | Real-time |
| EX-3 | Ti le huy cao (CRITICAL) | Bao ve | Real-time |
| EX-4 | Du bao het hang | Bao ve | Real-time (Phase 2) |
| EX-5 | Tran ngan sach tong the | Guardrail | Real-time |
| EX-6 | Budget camp >= 80% DB | Guardrail | Real-time |

---

## CAC QUYET DINH DA CHOT (khong con open question)

| # | Quyet dinh | Gia tri |
|---|---|---|
| 1 | N lan huy lien tiep thi chan buyer | **N = 10** (KHAC PRD goc N=2) |
| 2 | Noi ROI ngay le | Giam ROI_target **20%** trong ngay le, tu dong hoi phuc sau ngay le |
| 3 | Seller tu chinh % ngay le? | **Khong** — co dinh 20%, Seller khong chinh duoc |
| 4 | North Star | **GMV** |
| 5 | Pilot | La che do (toggle), **khong gioi han so Seller hay so ngay** |

---

*Cap nhat: 2026-06-07 | Da xac nhan voi product owner*
