# PRD — Flow thanh toán SaaS (OCB QR)

| Property              | Value                                                                 |
| --------------------- | --------------------------------------------------------------------- |
| **Trạng thái**        | `In Review`                                                           |
| **Owner (PM)**        | @Tuan Tran                                                            |
| **Tech lead**         | @tuan.vo                                                              |
| **Phiên bản**         | v2                                                                    |
| **Ngày tạo**          | Jun 21, 2026                                                          |
| **Cập nhật lần cuối** | Jun 23, 2026                                                          |
| **Link liên quan**    | [payment-flow.md](./payment-flow.md) · [Design spec](./docs/superpowers/specs/2026-06-23-payment-reconciliation-design.md) · [Implementation plan](./docs/superpowers/plans/2026-06-23-payment-ocb-qr.md) · [Figma] · [Ticket/Jira] |

> **Quy ước:** ô `[CẦN LÀM RÕ]` = chưa chốt, **không được tự đoán** khi implement.

---

# TẦNG 1 — BỐI CẢNH

_Ai cũng đọc được. Trả lời câu hỏi: "Tại sao làm cái này?"_

## 1.1 TL;DR

Tính năng này giới thiệu luồng thanh toán QR OCB tự động trên Website cho Nhà bán hàng (Seller) của ZZP. Khi Seller chọn gói SaaS (tháng/năm) và bấm đăng ký, hệ thống tạo payment order, gọi OCB gen mã VietQR (số tiền + mã đơn hàng đã điền sẵn) và hiển thị QR trực tiếp trên Web.

Mục tiêu là mang lại trải nghiệm đăng ký/gia hạn gói SaaS liền mạch, tức thì cho Seller và tự động hóa đối soát thanh toán cho ZZP, loại bỏ chi phí vận hành thủ công và sai sót.

Tài liệu kỹ thuật chi tiết: [payment-flow.md](./payment-flow.md)

## 1.2 Vấn đề

- **Đối với Seller:** Trải nghiệm thanh toán hiện tại đòi hỏi sao chép số tài khoản, nhập thủ công số tiền và nội dung chuyển khoản — tốn thời gian, dễ sai sót. Thời gian chờ duyệt đơn thủ công khiến Seller không dùng được dịch vụ ngay, đặc biệt ngoài giờ hành chính.
- **Đối với ZZP:** Đối soát thủ công tốn nguồn lực BD/Kế toán, dễ sai sót (duyệt nhầm, kích hoạt nhầm) và khó scale.
- **Hậu quả nếu không làm:** Seller bỏ dở giao dịch; ZZP gánh chi phí vận hành cao, rủi ro sai sót và chậm kích hoạt dịch vụ.

## 1.3 Đối tượng người dùng

| Persona                         | Là ai                                                         | Mục tiêu (Job-to-be-done)                              | Pain point chính                                                                                    |
| ------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------ | --------------------------------------------------------------------------------------------------- |
| Nhà bán hàng (Seller)           | Người dùng muốn đăng ký/gia hạn gói SaaS trên ZZP             | Thanh toán nhanh, chính xác, kích hoạt gói ngay        | Quy trình phức tạp, dễ sai; phải chờ duyệt thủ công; không thanh toán được ngoài giờ hành chính   |
| Nhân viên nội bộ (BD, Kế toán) | Người đối soát thanh toán và kích hoạt dịch vụ cho Seller     | Đối soát chính xác, tự động; giảm tác vụ thủ công      | Tốn thời gian check sao kê, ảnh bill; áp lực độ chính xác; không có thời gian cho việc chiến lược |

## 1.4 Định nghĩa "Done"

- Seller hoàn tất thanh toán gói SaaS và nhận kích hoạt/gia hạn gói tự động qua QR OCB hiển thị trên Web.
- Backend tự động tạo QR OCB, đối soát webhook bất đồng bộ và kích hoạt subscription thành công.
- BD/Kế toán không còn đối soát thủ công cho giao dịch khớp tự động; chỉ xử lý case `MANUAL_REVIEW`.

## 1.5 Phạm vi (Scope)

### Trong phạm vi (Sẽ làm)

- Hiển thị bảng giá gói SaaS (monthly/yearly) trên Website
- Tạo payment order qua API (idempotency, tính amount server-side)
- Gọi API OCB gen VietQR dynamic (số tiền + `orderCode`)
- Hiển thị QR, số tiền, `orderCode` và countdown 15 phút trên Web
- Polling trạng thái đơn (`WAITING_PAYMENT`, `PAID`, `EXPIRED`, `MANUAL_REVIEW`)
- Xử lý webhook OCB (verify signature, lưu raw payload)
- Đối soát bất đồng bộ: khớp `orderCode` + `amount` → kích hoạt/gia hạn gói SaaS
- Chuyển case lỗi sang `MANUAL_REVIEW` + cảnh báo BD/Kế toán
- Timeout đơn hàng sau 15 phút (BE-authoritative expiry)

### Ngoài phạm vi (KHÔNG làm lần này)

- Gửi QR qua Zalo ZNS hoặc SMS
- Thu thập/xác thực SĐT riêng cho luồng thanh toán
- Hỗ trợ ngân hàng khác ngoài OCB
- Ví điện tử/thẻ tín dụng trực tiếp _(Seller vẫn có thể quét VietQR bằng MoMo nếu OCB hỗ trợ)_
- Hoàn tiền, hủy đơn tự động phức tạp
- Nạp ví nội bộ _(phase 1 chỉ đăng ký/gia hạn gói SaaS)_

## 1.6 Giả định & Phụ thuộc

**Giả định**

- Seller đã đăng nhập ZZP (Bearer token) khi thanh toán
- Seller có app ngân hàng hoặc ví (MoMo, v.v.) hỗ trợ quét VietQR
- API OCB hoạt động ổn định và webhook đầy đủ để đối soát
- `orderCode` là duy nhất và được embed trong `description` khi gen QR

**Phụ thuộc**

- Tích hợp API OCB (gen QR + webhook)
- Hệ thống gói SaaS và subscription của ZZP
- Queue/worker cho đối soát async (xem [payment-flow.md](./payment-flow.md))

**Rủi ro cao nhất & cách kiểm chứng sớm**

| Rủi ro | Cách kiểm chứng |
| ------ | --------------- |
| Đối soát tự động khớp sai → kích hoạt nhầm/thiếu | Pilot nhóm Seller nhỏ; đối chiếu thủ công song song; alert sớm cho giao dịch không khớp |

## 1.7 Quy tắc nghiệp vụ & bất biến

| ID   | Quy tắc |
| ---- | ------- |
| BR-1 | Mỗi QR phải chứa chính xác **Số tiền** và **Mã đơn hàng** duy nhất cho một giao dịch |
| BR-2 | Gói SaaS chỉ được kích hoạt khi webhook OCB khớp hoàn toàn (**orderCode** + **amount**) |
| BR-3 | Seller phải đăng nhập; `sellerId` lấy từ token, không tin dữ liệu từ client |
| BR-4 | Không tạo QR nếu Seller chưa chọn gói hợp lệ hoặc API OCB lỗi |

---

# TẦNG 2 — YÊU CẦU

_Đây là phần quan trọng nhất._

## 2.1 User Stories

| ID   | Story |
| ---- | ----- |
| US-1 | Là Seller, tôi muốn thanh toán nhanh bằng QR để không cần nhập thủ công thông tin chuyển khoản |
| US-2 | Là Seller, tôi muốn thấy QR ngay trên Website để quét và thanh toán mà không cần chuyển sang app khác |
| US-3 | Là Seller, tôi muốn gói SaaS được kích hoạt/gia hạn ngay sau thanh toán thành công, không chờ duyệt thủ công |
| US-4 | Là BD/Kế toán, tôi muốn hệ thống tự động đối soát để tôi tập trung vào công việc chiến lược |

## 2.2 Tiêu chí nghiệm thu (Acceptance Criteria)

### AC-1.1 — Hiển thị bảng giá SaaS

- **Given:** Seller đã đăng nhập và mở trang bảng giá
- **When:** Trang tải xong
- **Then:** Hiển thị các gói SaaS (monthly/yearly) với giá chính xác từ backend

### AC-1.2 — Tạo đơn và hiển thị QR trên Web

- **Given:** Seller chọn gói và bấm "Đăng ký gói SaaS"
- **When:** Backend tạo order và OCB trả QR thành công
- **Then:** Web hiển thị QR + số tiền + `orderCode` + countdown 15 phút

### AC-1.3 — Polling trạng thái trong lúc chờ

- **Given:** Order đang ở trạng thái `WAITING_PAYMENT`
- **When:** Seller chưa thanh toán xong
- **Then:** Web polling `GET /payments/orders/{id}/status` mỗi 3–5s và giữ UI chờ

### AC-1.4 — Kích hoạt gói SaaS tự động

- **Given:** Seller quét QR trên Web và chuyển khoản thành công
- **When:** OCB gửi webhook và đối soát khớp `orderCode` + `amount`
- **Then:** Order → `PAID`, gói SaaS `ACTIVE`/extended, Web hiển thị thành công

## 2.3 Luồng người dùng (User Flow)

Luồng chính — **4 actor:** Seller, ZZP_Web, ZZP_Backend, OCB

1. Seller mở trang bảng giá SaaS trên Website ZZP
2. ZZP_Web gọi `GET /saas/packages` → hiển thị gói monthly/yearly
3. Seller chọn gói và bấm **"Đăng ký gói SaaS"**
4. ZZP_Web gọi `POST /payments/orders` (Bearer token, Idempotency-Key)
5. ZZP_Backend: validate gói, tính amount, tạo `payment_order`, gọi OCB gen QR
6. ZZP_Web hiển thị QR + số tiền + `orderCode` + countdown 15 phút
7. Seller quét QR bằng app ngân hàng/ví (MoMo nếu hỗ trợ VietQR) và chuyển khoản
8. Trong lúc chờ: ZZP_Web polling `GET /payments/orders/{id}/status`
9. OCB gửi webhook → ZZP_Backend verify, lưu event, enqueue đối soát async
10. ReconcileWorker khớp `orderCode` + `amount`:
    - **IF** khớp và order còn `WAITING_PAYMENT`, chưa hết hạn → `PAID` → kích hoạt/gia hạn gói SaaS
    - **ELSE** → `MANUAL_REVIEW` + alert BD/Kế toán
11. ZZP_Web polling nhận `PAID` → hiển thị _"Thanh toán thành công. Gói SaaS đã được kích hoạt."_

Sơ đồ chi tiết: [payment-flow.md](./payment-flow.md)

## 2.4 Trường hợp biên & Lỗi

| Tình huống | Hệ thống phải làm gì | Thông báo cho người dùng |
| ---------- | -------------------- | ------------------------ |
| OCB gen QR lỗi/timeout | `QR_CREATE_FAILED`, ghi audit log | "Hệ thống thanh toán đang gặp sự cố. Vui lòng thử lại sau." |
| Webhook không khớp order (sai `orderCode` hoặc `amount`) | `MANUAL_REVIEW` + `reason_code` + alert BD/Kế toán | "Thanh toán cần được kiểm tra thêm. Liên hệ hỗ trợ." |
| Seller đóng trình duyệt khi đang chờ | Order vẫn `WAITING_PAYMENT`; thanh toán xong vẫn đối soát; quay lại Web hiển thị trạng thái order gần nhất | _(không có nếu đã đóng tab)_ |
| Hết 15 phút chưa thanh toán | ExpiryJob: `WAITING_PAYMENT` → `EXPIRED` | "Giao dịch đã hết hạn. Vui lòng tạo đơn mới." |
| Thanh toán sau khi order đã `EXPIRED` | Không auto-activate; `MANUAL_REVIEW` (late payment) | "Thanh toán cần được kiểm tra thêm. Liên hệ hỗ trợ." |
| Seller double-click "Đăng ký" | Idempotency-Key → trả order cũ, không tạo trùng | Giữ nguyên QR đang hiển thị |
| Webhook trùng `transactionId` | Ignore duplicate, ACK 200 | Không đổi UI |
| Seller muốn hủy giao dịch đang chờ | Nút "Hủy đơn" → `CANCELLED` `[CẦN LÀM RÕ UX]` | "Giao dịch đã bị hủy." |

## 2.5 Yêu cầu nội dung & ngôn ngữ

- **Ngôn ngữ:** Tiếng Việt, Tiếng Anh
- Copy rõ ràng, ngắn gọn, tránh thuật ngữ kỹ thuật
- Thông báo lỗi phải hướng dẫn bước tiếp theo (thử lại, liên hệ hỗ trợ)

## 2.6 Logic hệ thống & Quy tắc tự động (IF / THEN)

### R-1 — Quy tắc tạo QR OCB

**KHI:** Seller chọn gói SaaS hợp lệ và bấm đăng ký trên Website

**THÌ:**

- Backend validate `package` + `pricePlan`, tính amount server-side
- Gọi OCB gen VietQR (`orderCode` + `amount` trong `description`)
- Trả QR về Web hiển thị

**Không được làm:** Tạo QR nếu package/pricePlan không `ACTIVE` hoặc OCB lỗi

### R-2 — Quy tắc đối soát tự động (async)

**KHI:** ZZP_Backend nhận webhook OCB hợp lệ

**THÌ:**

- Lưu `bank_webhook_events`, enqueue ReconcileWorker
- Worker khớp `orderCode` + `amount` với order `WAITING_PAYMENT`, chưa quá `expires_at`
- **IF khớp:** `PAID` → ledger + `activateOrExtend` subscription
- **ELSE:** `MANUAL_REVIEW` + alert nội bộ

**Không được làm:** Kích hoạt gói nếu không khớp chính xác; bỏ qua webhook không log

### R-3 — Quy tắc timeout đơn hàng chờ

**KHI:** Order đã tạo QR nhưng không nhận webhook thành công trong 15 phút

**THÌ:**

- Chuyển trạng thái → `EXPIRED`
- Thông báo hết hạn trên Website

**Không được làm:** Giữ `WAITING_PAYMENT` vô thời hạn; auto-activate khi webhook muộn sau `EXPIRED`

---

# TẦNG 3 — KIỂM THỬ & XÁC THỰC

## 3.1 Checklist kiểm thử

- [ ] Hiển thị bảng giá và tạo order SaaS
- [ ] Hiển thị QR + countdown trên Web
- [ ] Polling trạng thái order
- [ ] Thanh toán QR qua app ngân hàng / MoMo (UAT)
- [ ] Webhook OCB và đối soát async (khớp / không khớp / duplicate)
- [ ] Kích hoạt/gia hạn gói SaaS sau `PAID`
- [ ] Timeout 15 phút và late payment → `MANUAL_REVIEW`
- [ ] Lỗi API OCB (gen QR fail)
- [ ] Idempotency (double-click đăng ký)

## 3.2 Test Cases

| ID    | Mô tả | Kết quả mong đợi |
| ----- | ----- | ---------------- |
| TC-01 | Seller chọn gói monthly, thanh toán thành công qua QR trên Web | QR trên Web → quét & chuyển khoản → `PAID` → gói SaaS `ACTIVE` |
| TC-02 | Seller chọn gói yearly, double-click đăng ký | Idempotency trả 1 order → thanh toán → gói gia hạn 12 tháng |
| TC-03 | Seller chuyển khoản sai số tiền (webhook `amount` khác) | `MANUAL_REVIEW` + alert nội bộ → không auto-activate |
| TC-04 | Seller không thanh toán trong 15 phút | Order `EXPIRED` → Web hiển thị hết hạn → có thể tạo đơn mới |
| TC-05 | OCB gen QR lỗi | `503 payment_unavailable` → Seller thử lại |

---

# PHỤ LỤC

## Tài liệu tham khảo

- [x] Flow kỹ thuật: [payment-flow.md](./payment-flow.md)
- [ ] API Documentation: Ngân hàng OCB `[CẦN LÀM RÕ]`
- [ ] Tài liệu thiết kế UX/UI (Figma) `[CẦN LÀM RÕ]`
