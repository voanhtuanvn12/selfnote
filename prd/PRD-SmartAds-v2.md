# PRD — ZZP Smart Ads: Tự động hoá Quảng cáo GMV Max

| Trường | Giá trị |
|---|---|
| **Trạng thái** | `In Review` |
| **Owner (PM)** | Tuan Tran |
| **Tech lead** | Vo Anh Tuan |
| **Phiên bản** | v2 |
| **Cập nhật lần cuối** | 2026-06-11 |
| **Nguồn flowchart** | SmartAds Optimization.drawio.png (đã xác nhận) |
| **Tài liệu kỹ thuật** | SRS-Campaign-Engine · SRS-Optimization-Rules · SRS-Fraud-Inventory |

> **Quy ước đọc file này:**
> - **Tầng 1 và 2** dành cho PM, Business Owner, Stakeholder — không có jargon kỹ thuật.
> - **Tầng 3** dành cho Dev và Tech Lead — chỉ ghi tổng quan, chi tiết xem file SRS tương ứng.
> - **Phase 1 vs Phase 2 (kỹ thuật):** bảng đối chiếu ngắn trong [SRS-Campaign-Engine.md — §0](SRS-Campaign-Engine.md) và [SmartAds-Phase1-Backlog.md — §1.1](SmartAds-Phase1-Backlog.md#p1-p2-srs-matrix); tránh nhầm *toàn bộ* hành trình §2.1 là nghiệm thu Phase 1.
> - Checkbox `- [ ]` vừa là yêu cầu vừa là tracking tiến độ.

---

# TẦNG 1 — BỐI CẢNH

## 1.1 Tóm tắt

ZZP Smart Ads là một hệ thống giúp Seller tự động chạy quảng cáo TikTok Shop dạng GMV Max — loại quảng cáo hiệu quả nhất để tăng doanh số — mà không cần Seller hiểu kỹ thuật quảng cáo.

Hệ thống tự nhận diện sản phẩm bán chạy, tận dụng kho video KOC từ tính năng SAM, tự điều chỉnh ngân sách và mức ROI để tối đa GMV trong giới hạn ngân sách Seller đặt ra — đồng thời tự bảo vệ Seller khỏi các rủi ro như hàng hết kho, khách bùng đơn, và lỗi thanh toán.

**Điều ZZP cam kết tuyệt đối:**
- Không bao giờ tiêu vượt ngân sách Seller đặt.
- Không bao giờ tự đụng vào các chiến dịch Seller đã tự tạo trên TikTok.
- Không thu hộ, nạp hộ tiền quảng cáo cho Seller.

## 1.2 Vấn đề

| Nhóm Seller | Vấn đề gặp phải | Hậu quả |
|---|---|---|
| **Seller mới** | Không biết cách thiết lập chiến dịch GMV Max, không biết đặt ROI bao nhiêu cho lãi, không biết nên đặt ngân sách bao nhiêu để tiết kiệm nhưng vẫn đạt mục tiêu doanh số. | Bỏ phí kho video KOC từ SAM; không có doanh số từ quảng cáo |
| **Seller có kinh nghiệm** | Không có thời gian theo dõi chiến dịch 24/7; muốn tự động theo công thức riêng | Chi phí cơ hội cao; lỡ window tối ưu |
| **ZZP (platform)** | Video KOC đầu ra từ SAM không được tận dụng làm input quảng cáo. Seller trên nền tảng không có công cụ tự động hóa để tối ưu doanh thu từ nguồn tạo doanh thu chính là TikTok Ads. | Giảm giá trị của SAM; Seller không thấy ROI từ platform |

## 1.3 Đối tượng người dùng

| Persona | Là ai | Mục tiêu | Pain point chính |
|---|---|---|---|
| **Seller mới** | Chưa từng chạy GMV Max | Có doanh số mà không cần học kỹ thuật quảng cáo | Không biết đặt ROI và ngân sách bao nhiêu; sợ lỗ vì không hiểu cơ chế |
| **Seller có kinh nghiệm** | Đã biết tối ưu nhưng bận | Hệ thống tự vận hành theo công thức của mình | Không có thời gian theo dõi camp 24/7; không được cảnh báo kịp thời |

## 1.4 Mục tiêu & Chỉ số thành công

**North Star: Tổng GMV mang về cho Seller qua các chiến dịch do ZZP quản lý.**

> Chọn GMV vì: GMV là chỉ số Seller trực tiếp cảm nhận được và so sánh được với việc tự chạy quảng cáo. Đây là lý do Seller ở lại dùng ZZP. 
> - ROI - Return On Investment là tỷ suất hoàn vốn dựa trên chi phí đầu tư được tính với công thức: ROI = Lợi nhuận ròng/ Chi phí

> - Chỉ số này thường được tính dựa trên bức tranh tổng thể của shop vì cần biết Lợi nhuận ròng → đồng nghĩa với việc cần biết COGS  Cost of Goods Sold (COGS) hay Giá vốn hàng bán, là tổng các chi phí trực tiếp phát sinh để tạo ra hoặc mua vào các sản phẩm đã được bán ra trong một kỳ kế toán -> TikTok không yêu cầu nhập thông tin này nên nói là ROI thì không đúng. Tiktok đang lấy GMV dựa trên các đơn phát sinh từ ads và cả các đơn tự nhiên (không đến từ Ad)

> - Nếu chỉ nói riêng trong việc chạy ads, định nghĩa thường được dùng là ROAS (Return on Ads Spend) = Doanh thu của các đơn hàng từ Ads/ Chi phí Ads 


Ký hiệu dùng nhất quán toàn doc: 
-ROI_target: mức ZZP set trên TikTok
-ROI_actual: mức TikTok báo cáo về
-ROI_real: mức ROI internal ZZP tự đo, không thông báo cho Seller.
-MDB (Max Daily Budget) = Mức trần ngân sách hệ thống do seller nhập vào. Hệ thống tuyệt đối không được can thiệp. `Budget_initial = Ngân sách khởi tạo campaign mới`
- DB_Actual: Số tiền quảng cáo đã tiêu
- DB_Campaign: ngân sách ngày của chiến dịch, được thay đổi do hệ thống ZZP.

| Nhóm | Chỉ số | Mục tiêu |
|---|---|---|
| **Kết quả** | GMV từ các camp ZZP quản lý (tăng trưởng % theo tháng) | Chốt sau pilot |
| **Kết quả** | % camp giữ được ROI_actual ≥ ROI hòa vốn (không lỗ tiền ads) | Chốt sau pilot |
| **Adoption** | % Seller kết nối TikTok Ads thành công trong ngày đầu | ≥ 80% |
| **Adoption** | Tỷ lệ giữ chân Seller sau 30 ngày (D30 Retention) | Chốt sau pilot |
| **Vận hành** | Tỷ lệ lệnh tối ưu chạy đúng mỗi ngày | ≥ 99% |
| **Guardrail (BẮT BUỘC)** | Số lần chiến dịch tiêu vượt ngân sách Seller đặt | **= 0** |
| **Guardrail (BẮT BUỘC)** | Số lần hệ thống tự sửa/tắt camp Seller đã có | **= 0** |

## 1.5 Phạm vi

### Phase 1 — Nền tảng (TikTok Parity)

> Mục tiêu: Seller kết nối TikTok Ads vào ZZP, tạo và xem chiến dịch GMV Max ngay trong ZZP mà không cần rời sang TikTok Ads Manager.

> **Đối chiếu SRS:** OAuth, `cost_table`, tạo camp lần đầu (20% MDB, ROAS hòa vốn), dashboard đọc báo cáo = **Phase 1** — [SRS-Campaign-Engine §0–§4.3](SRS-Campaign-Engine.md).

- [ ] Kết nối tài khoản TikTok Ads qua luồng đăng nhập chính thức (OAuth)
- [ ] Hệ thống tự tính và gợi ý mức ROI phù hợp dựa trên chi phí sản phẩm (COGS, phí ship, hoa hồng KOC...) — dữ liệu tự đồng bộ từ ZZP - Bảng chi phí Brand
- [ ] Tạo chiến dịch GMV Max dạng Target ROI cho tất cả sản phẩm và tất cả video KOC
- [ ] Dashboard xem hiệu suất chiến dịch (GMV, chi phí, ROI, số đơn) ngay trong ZZP
- [ ] Ngân sách khởi tạo = 20% ngân sách ngày tối đa Seller đặt (tự động, an toàn)

*(Tất cả SP / tất cả video = mặc định SRS Phase 1; wizard **CUSTOMIZED** vẫn thuộc Phase 1 nếu PM chọn — xem [ADR 0001](adr/0001-smartads-phase1-tiktok-create-payload.md), [SmartAds-Phase1-Backlog §1.1](SmartAds-Phase1-Backlog.md#p1-p2-srs-matrix).)*

### Phase 2 — Tự động tối ưu (ZZP Layer)

> Mục tiêu: Hệ thống tự vận hành, tối ưu, và bảo vệ Seller 24/7.

> **Đối chiếu SRS:** chuyển trạng thái sau warming theo Optimization, Hero, tự inject creative SAM, Protection — **Phase 2+** — [SRS-Campaign-Engine §4.2](SRS-Campaign-Engine.md) + [SRS-Optimization-Rules](SRS-Optimization-Rules.md) / [SRS-Fraud-Inventory](SRS-Fraud-Inventory.md) (Tầng 3).

- [ ] Tự động điều chỉnh (tăng/giảm) ROI và ngân sách mỗi ngày. Trong đó: Tăng/Giảm ROI: 1 lần/chiến dịch/ngày. Tăng/Giảm Ngân sách: 1 lần/chiến dịch/ngày
- [ ] Tự phát hiện sản phẩm bán chạy và tách ra chiến dịch riêng (Hero Campaign)
- [ ] Tự hồi sinh video từng chạy tốt nhưng đang chững
- [ ] Tự chặn khách hàng bùng đơn (mặc định: chặn sau 10 lần hủy liên tiếp).Level campaign. Level Shop → 10/30/50/Vĩnh viễn. 
- [ ] Tự dừng chiến dịch khi hàng hết kho, tự cảnh báo khi sắp hết
- [ ] Tự điều chỉnh chiến dịch trong các ngày sale lớn (6.6, 7.7, giữa tháng...)  theo quy định của TikTok, tạm dừng các rule bên ZZP.
- [ ] Chế độ Max Delivery cho các ngày càn quét traffic
- [ ] Bảo vệ tổng ngân sách: không cho phép tổng chi tiêu vượt ngân sách ngày Seller đặt
- [ ]  Hệ thống quét liên tục mỗi giờ nhưng action vào lượt quét lúc 23h. Nếu có trường hợp không có kịch bản nào được tính tới > hệ thống cần log lại và thông báo đề điều chỉnh kịch bản.
Trong trường hợp rơi vào lúc 23h (trùng với chu kỳ action), hệ thống vẫn cần log lại, thông báo và không action, để tự Tiktok chạy và tiếp tục kiểm tra vào 24h kế tiếp.



### Ngoài phạm vi (KHÔNG làm)

- [ ] Không hỗ trợ Livestream Ads — chỉ Video Ads
- [ ] Không thu hộ / nạp hộ tiền quảng cáo cho Seller
- [ ] Không tự tắt hoặc sửa các chiến dịch Seller đã tự tạo trên TikTok
- [ ] Custom mode (Seller tự set tham số) — để Phase tương lai

## 1.6 Phụ thuộc & Rủi ro

**Phụ thuộc kỹ thuật:**
- TikTok Business API: đăng nhập, tạo/sửa chiến dịch GMV Max, quản lý danh sách chặn khách
- TikTok Shop API: danh sách sản phẩm, lịch sử đơn hàng, tồn kho
- ZZP SAM: nguồn cấp video KOC. (Phase tương lai)
- ZZP service nội bộ: bảng chi phí sản phẩm (COGS, phí, hoa hồng)

**Rủi ro cần kiểm chứng sớm:**

| Rủi ro | Cách kiểm chứng | Mức độ |
|---|---|---|
| API TikTok có cho phép ZZP đọc + ghi ROI, ngân sách của camp do ZZP tạo không? | Test với sandbox API | Cao |
| API TikTok có trả về `Cancel_Type` để phân biệt loại hủy đơn không? | Xem API docs Shop Center | Cao |
| API TikTok có cho phép đẩy Buyer ID vào Exclusion List không? | Xem API docs Audience | Trung bình |

## 1.7 Quy tắc bất biến (Business Rules)

> Đây là những nguyên tắc **không bao giờ được vi phạm**, bất kể tình huống nào.

- [ ] **BR-1 — Không đụng tiền Seller:** ZZP không thu hộ, không nạp hộ. Seller tự nạp tiền vào TikTok Ads. ZZP chỉ dùng API để cấu hình và tối ưu chiến dịch.

- [ ] **BR-2 — Không đụng camp Seller đã có:** Mọi chiến dịch Seller tự tạo trên TikTok Ads trước khi dùng ZZP luôn được giữ nguyên. ZZP chỉ quản lý các chiến dịch do ZZP tạo ra.

- [ ] **BR-3 — Chỉ Video Ads:** Không chạy Livestream Ads ở giai đoạn này.

- [ ] **BR-4 — Không vượt ngân sách tổng:** Tổng chi tiêu của tất cả chiến dịch ZZP quản lý không được vượt ngân sách ngày tối đa (MDB) Seller đặt. Khi chạm ngưỡng, hệ thống dừng tăng ngân sách và dừng tách chiến dịch mới.

- [ ] **BR-5 — Tối đa 1 lần điều chỉnh/chiến dịch/ngày:** Mỗi chiến dịch chỉ được điều chỉnh (tăng/giảm) ROI và Ngân sách 1 lần trong 1 ngày (tính theo ngày dương lịch 00:00–23:59). Không được đổi đi đổi lại trong ngày. Ví dụ: Tăng ROI và Giảm ROI cùng ngày. Tăng ROI và Giảm Ngân sách cùng ngày.
- [ ] **BR-6 — ROI = số blended của TikTok:** Hệ thống dùng con số ROI mà TikTok báo cáo (bao gồm cả đơn tự nhiên + đơn từ quảng cáo) để ra mọi quyết định. Đây là số Seller nhìn thấy trên TikTok nên nhất quán với trải nghiệm của họ.

---

# TẦNG 2 — HÀNH VI

## 2.1 Hành trình của Seller (User Journey)

### Seller mới lần đầu dùng Smart Ads

Nhãn **(P1)** = nghiệm thu Phase 1 theo [SRS-Campaign-Engine §0](SRS-Campaign-Engine.md). **(P2)** = Phase 2 / Optimization / SAM pipeline.

```
Vào ZZP → Smart Ads Center                                                    [P1]
    ↓
Bấm "Kết nối tài khoản TikTok Ads"                                            [P1]
    ↓
Đăng nhập TikTok (cửa sổ TikTok mở ra, đăng nhập và cho phép)                  [P1]
    ↓
Quay lại ZZP — trạng thái: Đã kết nối ✓                                        [P1]
    ↓
Bước 1: Xem danh sách sản phẩm (ZZP tự lấy từ shop)
        → Mặc định chọn tất cả sản phẩm (hoặc CUSTOMIZED nếu PM/backlog)      [P1]
    ↓
Bước 2: Xem gợi ý ngân sách & ROI
        → ZZP tự tính dựa trên chi phí sản phẩm của shop                        [P1]
        → Seller điều chỉnh nếu muốn                                         [P1]
    ↓
Bước 3: Xem Creative Pool (video KOC từ SAM đã có sẵn)                        [P1: xem pool / gắn video thủ công theo wizard]
        → Hệ thống tự thêm video mới từ SAM vào chiến dịch                      [P2 — SRS §4.3 bước 3]
    ↓
Bấm "Bắt đầu chạy"                                                            [P1]
    ↓
Chiến dịch tạo xong — bắt đầu giai đoạn 72h đầu tiên (WARMING / báo cáo)       [P1 hiển thị + đồng bộ TikTok; tối ưu sau 72h = P2]
```

**Ghi chú:** Nếu copy sản phẩm thương mại nói "tự động mọi thứ" end-to-end, hiểu đó là **tầm nhìn** sau Phase 1; contract kỹ thuật Phase 1 nằm trong SRS §0 và backlog §1.1.

## 2.2 Các tình huống (User Stories)

- [ ] **US-1:** Là Seller mới, tôi muốn kết nối TikTok Ads và bấm chạy với cấu hình gợi ý, để có chiến dịch GMV Max hoạt động ngay mà không cần hiểu kỹ thuật quảng cáo.

- [ ] **US-2:** Là Seller, tôi muốn ZZP tự điều chỉnh ngân sách và ROI mỗi ngày, để chiến dịch luôn ở trạng thái tối ưu mà tôi không cần theo dõi thủ công.

- [ ] **US-3:** Là Seller, tôi muốn hệ thống tự phát hiện sản phẩm bán chạy và tập trung ngân sách vào đó, để tối đa GMV từ sản phẩm đang có momentum.

- [ ] **US-4:** Là Seller, tôi muốn hệ thống tự dừng quảng cáo khi hàng hết kho và cảnh báo tôi trước khi hết, để không tốn tiền quảng cáo cho sản phẩm không có hàng giao.

- [ ] **US-5:** Là Seller, tôi muốn hệ thống tự chặn những khách bùng đơn, để tránh bị tấn công hủy đơn làm giảm điểm shop và tiêu phí quảng cáo.

## 2.3 Tiêu chí nghiệm thu (Acceptance Criteria)

**US-1 — Onboarding:**
- [ ] **AC-1.1:** Cho trước Seller đã kết nối TikTok Ads và shop có ít nhất 1 video KOC, khi Seller bấm "Bắt đầu chạy", hệ thống tạo 1 chiến dịch GMV Max Target ROI với tất cả sản phẩm và tất cả video KOC, ngân sách khởi tạo = 20% ngân sách ngày Seller đặt.
- [ ] **AC-1.2:** ROI_target được đặt = ROAS hòa vốn tính từ bảng chi phí của shop (không dùng mặc định TikTok).

**US-2 — Tự động tối ưu:**
- [ ] **AC-2.1:** Trong 72h đầu, hệ thống KHÔNG thay đổi ROI hay ngân sách (ngoại trừ các tình huống khẩn cấp ở §2.4).
- [ ] **AC-2.2:** Sau 72h, hệ thống chỉ thực hiện tối đa 1 lần điều chỉnh (ROI hoặc ngân sách) trên mỗi chiến dịch trong 1 ngày dương lịch.
- [ ] **AC-2.3:** Khi budget thực tế < 20% daily budget → hệ thống giảm ROI tối đa 15%.
- [ ] **AC-2.4:** Khi 50% ≤ budget thực tế ≤ 80% daily budget → hệ thống tăng ROI tối đa 20%.
- [ ] **AC-2.5:** Khi ROI_actual ≥ ROI_target → hệ thống tăng ngân sách tối đa 20%.

**US-3 — Hero Campaign:**
- [ ] **AC-3.1:** Khi 1 sản phẩm đạt ≥ 20 đơn hàng, hệ thống tạo chiến dịch Hero riêng với ngân sách = daily budget chiến dịch đó × 120%, đồng thời xóa sản phẩm đó khỏi chiến dịch gốc và giảm ngân sách chiến dịch gốc tối đa 20%.

**US-4 — Quản lý kho:**
- [ ] **AC-4.1:** Khi tồn kho 1 sản phẩm ≤ 30% số lượng ban đầu HOẶC ≤ 30 đơn vị, hệ thống cảnh báo Seller và giảm ngân sách chiến dịch 10%.
- [ ] **AC-4.2:** Khi tồn kho = 0, hệ thống tạm dừng chiến dịch ngay lập tức và thông báo Seller.

**US-5 — Chặn bùng đơn:**
- [ ] **AC-5.1:** Khi 1 người mua hủy đơn liên tiếp 10 lần (đơn thành công ở giữa sẽ reset đếm), hệ thống tự động chặn người đó khỏi toàn bộ chiến dịch của shop.

## 2.4 Hành vi tự động của hệ thống (Phase 2)

> Giải thích ngắn gọn cho PM/BO — chi tiết kỹ thuật xem `SRS-Optimization-Rules.md` và `SRS-Fraud-Inventory.md`.

### Giai đoạn 72h đầu tiên (Warming up)

Sau khi tạo chiến dịch, hệ thống cần 72h để "học" hành vi mua sắm. Trong thời gian này:
- Hệ thống **không thay đổi ROI hay ngân sách** để tránh làm nhiễu quá trình học.
- Chỉ xử lý các tình huống khẩn cấp (khách bùng đơn, thanh toán lỗi, tỷ lệ hủy cao).

### Sau 72h — Tối ưu hàng ngày

Mỗi ngày (tính theo lịch 00:00–23:59), hệ thống đánh giá từng chiến dịch và ra tối đa 1 quyết định:

| Tình huống | Hệ thống làm gì |
|---|---|
| Chiến dịch tiêu < 20% ngân sách ngày | Giảm ROI để thu hút nhiều người mua hơn (tối đa 15% mỗi lần) |
| Chiến dịch tiêu 50–80% ngân sách ngày | Tăng ROI để chọn lọc người mua có chất lượng cao hơn (tối đa 20%) |
| ROI thực tế đang tốt hơn mục tiêu | Tăng ngân sách để tận dụng đà (tối đa 20%) |
| Sản phẩm đạt ≥ 20 đơn hàng | Tách ra chiến dịch Hero riêng, tập trung ngân sách vào đó |
| Video từng tốt nhưng 48h không có đơn | Tạo chiến dịch thử nghiệm nhỏ (100k/ngày) để kiểm tra lại |

### Bảo vệ tổng ngân sách

Khi tổng chi tiêu của tất cả chiến dịch chạm ngưỡng ngân sách ngày Seller đặt: hệ thống **tự động đóng băng**, không tách thêm chiến dịch mới, không tăng thêm ngân sách nào.

### Các ngày sale lớn (6.6, 7.7, giữa tháng, ngày lương...)

Hệ thống tự nhận biết và giảm ROI_target xuống 20% để chiến dịch có thể tiếp cận nhiều người mua hơn, phù hợp với hành vi mua sắm tăng đột biến trong ngày sale.

## 2.5 Các tình huống khẩn cấp (Xử lý ngay, không chờ 24h)

| Tình huống | Hệ thống làm gì | Thông báo Seller |
|---|---|---|
| Khách hàng hủy đơn liên tiếp ≥ 10 lần | Tự động chặn khách đó khỏi tất cả chiến dịch | Có (in-app) |
| Thanh toán TikTok Ads bị lỗi | Tạm dừng chiến dịch + hiển thị link nạp tiền TikTok | Có (pop-up đỏ) |
| Tỷ lệ hủy đơn ≥ 25% tổng số đơn của toàn campaign VÀ ≥ 10 đơn bị hủy. | thông báo để Seller tự quyết định | Có (Push + SMS) |
| Hàng sắp hết (≤ 30% ban đầu hoặc ≤ 30 sản phẩm) | Giảm ngân sách 10% + cảnh báo sắp hết hàng | Có (Push) |
| Tổng ngân sách tất cả camp đạt MDB | Đóng băng — không tách camp, không tăng ngân sách | Có (in-app + Push) |
| Kết nối TikTok hết hạn | Dừng tối ưu (camp vẫn chạy trên TikTok), hiển thị cảnh báo | Có (Banner + Email) |
| Seller bấm "Dừng khẩn cấp" | Tạm dừng tất cả chiến dịch ngay lập tức | — |
| Hàng hết kho hoàn toàn (= 0) | Tạm dừng chiến dịch ngay + thông báo | Có (Push) |

## 2.6 Vòng đời chiến dịch

Mô tả **end-to-end** (vision). Phần sau **72h warming** — ổn định tối ưu hàng ngày, Hero, tự pause theo kho — chủ yếu thuộc **Phase 2** (PRD §1.5 Phase 2; SRS §4.2). Phase 1 vẫn có thể hiển thị nhãn trạng thái + báo cáo read-only.

```
[Khởi tạo]
     ↓ Seller bấm "Bắt đầu chạy"
[72h đầu tiên - Warming up]
     ↓ Sau 72h (không có sự cố)
[Ổn định - Tối ưu hàng ngày]
     ↓ Sản phẩm đạt ≥ 20 đơn
[Hero Campaign] ← Camp mới, song song với camp gốc
     ↓ (bất kỳ lúc nào)
[Tạm dừng] ← Hàng hết / Seller bấm dừng / Thanh toán lỗi
     ↓ Hàng về / Seller bật lại
[Ổn định - tiếp tục]
```

**Lưu ý quan trọng về Hero Campaign:**
- Khi tách Hero, sản phẩm đó được **xóa khỏi chiến dịch gốc** và chuyển sang chiến dịch Hero mới.
- Chiến dịch gốc giảm ngân sách (tối đa 20%, tối thiểu còn 200.000đ/ngày).
- Chiến dịch Hero bắt đầu lại từ đầu chu kỳ 72h.

## 2.7 Chính sách thông báo

| Mức độ | Loại sự kiện | Kênh |
|---|---|---|
| Khẩn cấp | Tỷ lệ hủy đơn cao (≥ 25%), Tạm dừng khẩn | Push notification + SMS |
| Quan trọng | Hàng sắp hết kho, Tổng ngân sách đạt MDB, Kết nối hết hạn | Push notification |
| Thông thường | Tối ưu ROI/ngân sách hàng ngày, Tách Hero Campaign | In-app notification |

---

# TẦNG 3 — KỸ THUẬT (Tổng quan)

> Chi tiết đầy đủ xem các file SRS. Phần này chỉ ghi kiến trúc tổng thể.

## 3.1 Kiến trúc tổng thể

Hệ thống gồm 3 thành phần chính:

**1. Campaign Engine** (xem [`SRS-Campaign-Engine.md`](SRS-Campaign-Engine.md))

- **Phase 1:** Onboarding OAuth; `cost_table` + ROAS hòa vốn; tạo camp GMV Max lần đầu; đọc/sync campaign + báo cáo dashboard — SRS §0–§4.5.
- **Phase 2+:** State machine đầy đủ sau warming, nhánh Hero/Revival, pipeline creative SAM — SRS §4.2–§4.3 bước 3.

**2. Optimization Engine** (xem `SRS-Optimization-Rules.md`) — **Phase 2**
- Logic tối ưu hàng ngày (C1–C5): tăng/giảm ROI, tăng ngân sách, Hero split, video revival
- Chạy theo chu kỳ ngày dương lịch 00:00–23:59
- Ràng buộc: tối đa 1 thay đổi/chiến dịch/ngày
- Holiday mode tự động

**3. Protection Engine** (xem `SRS-Fraud-Inventory.md`) — **Phase 2**
- Real-time: chặn buyer bùng đơn (N=10), xử lý thanh toán lỗi, cảnh báo tỷ lệ hủy
- Bảo vệ ngân sách: tổng ngân sách ≤ MDB
- Sync tồn kho: cảnh báo sắp hết hàng, tạm dừng khi kho = 0

## 3.2 Nguồn dữ liệu

| Nguồn | Dữ liệu lấy |
|---|---|
| TikTok Business API | Tạo/sửa chiến dịch, ROI_actual, chi phí, đơn hàng, exclusion list |
| TikTok Shop API | Sản phẩm, tồn kho, lịch sử đơn hàng, Cancel_Type |
| ZZP SAM | Video KOC (creative pool) |
| ZZP service nội bộ | Chi phí sản phẩm: COGS, phí vận chuyển, hoa hồng KOC |

## 3.3 Yêu cầu phi chức năng

- **Bảo mật:** Không lưu thông tin thẻ/thanh toán của Seller. Chỉ lưu OAuth token (mã hóa).
- **Độ tin cậy:** Các lệnh real-time (EX-1 đến EX-6) phải xử lý trong vòng 1 phút kể từ khi phát hiện.
- **Idempotency:** Hệ thống chạy lại không tạo Hero 2 lần hay tăng ROI 2 lần trong cùng 1 ngày.
- **Xử lý lỗi:** Khi API TikTok không phản hồi → retry 30 phút, nếu vẫn lỗi thì giữ nguyên config và thông báo Seller.

## 3.4 Thứ tự build

**Phase 1:**
- [ ] **P1-T1** Bảng chi phí + engine tính ROI hòa vốn → nền tảng cho suggestion ROI
- [ ] **P1-T2** OAuth onboarding TikTok Ads (kết nối, lưu token, refresh)
- [ ] **P1-T3** Tạo chiến dịch GMV Max: chọn sản phẩm / video (ALL hoặc CUSTOMIZED theo backlog), set ROI/budget; **không** bắt buộc tự động inject video SAM (Phase 2 — SRS §4.3 bước 3)
- [ ] **P1-T4** Dashboard: hiển thị số liệu GMV Max từ TikTok API

**Phase 2:**
- [ ] **P2-T1** State machine chiến dịch + chu kỳ monitoring 24h
- [ ] **P2-T2** Optimization engine: C1–C5 (tăng/giảm ROI, tăng budget, Hero split, video revival)
- [ ] **P2-T3** Protection engine: EX-1–EX-6 (buyer block, cancel alert, inventory sync)
- [ ] **P2-T4** Holiday mode
- [ ] **P2-T5** Test toàn bộ guardrail (không vượt ngân sách, không đụng camp Seller)

---

## Changelog

| Ngày | Phiên bản | Thay đổi |
|---|---|---|
| 2026-06-11 | v2 | Đồng bộ nhãn Phase 1 / Phase 2 với SRS-Campaign-Engine §0; làm rõ hành trình §2.1 và P1-T3 vs SAM auto-inject; Tầng 3 gắn Phase cho từng engine |
| 2026-06-07 | v2 | Rewrite từ Demo PRD.md; cập nhật theo flowchart mới: Hero split xóa camp gốc, monitoring theo ngày dương lịch, budget khởi tạo 20% MDB, N=10, North Star = GMV |

## References

- [SRS-Campaign-Engine.md](SRS-Campaign-Engine.md) — §0: Phase 1 vs Phase 2 (Campaign Engine)
- [SmartAds-Phase1-Backlog.md](SmartAds-Phase1-Backlog.md#p1-p2-srs-matrix) — §1.1: cùng ma trận, góc nhìn task P1-BE / P1-FE
- TikTok — *Cách xem báo cáo chiến dịch GMV Max* (tháng 3/2026): ROI = Doanh thu gộp / Chi phí (blended organic + paid). https://ads.tiktok.com/help/article/how-to-see-reporting-for-your-product-gmv-max-campaign?lang=vi
- Flowchart: SmartAds Optimization.drawio.png (đã xác nhận với product owner 2026-06-07)
- Phân tích chi tiết flowchart: `docs/superpowers/specs/flowchart-analysis-smartads.md`
