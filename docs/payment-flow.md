```mermaid
sequenceDiagram
    title ZZP SaaS Payment QR trên Web

    participant Seller
    participant ZZP_Web
    participant ZZP_Backend
    participant OCB

    note over Seller,ZZP_Web: Mục tiêu: Seller mua gói SaaS theo tháng hoặc theo năm, thanh toán bằng QR OCB hiển thị trực tiếp trên Website.

    %% ── Phase 1: Xem bảng giá ──
    Seller->>ZZP_Web: Mở trang bảng giá SaaS
    ZZP_Web->>ZZP_Backend: GET /saas/packages
    note over ZZP_Backend: PackagePricingService: lấy gói ACTIVE + price plan monthly/yearly
    ZZP_Backend-->ZZP_Web: 200 packages (packageId, pricePlanId, billingCycle, unitAmount, currency)
    ZZP_Web-->Seller: Hiển thị gói Monthly 600k và Yearly 7.2m

    %% ── Phase 2: Tạo đơn + QR ──
    Seller->>ZZP_Web: Chọn gói và bấm "Đăng ký gói SaaS"
    ZZP_Web->>ZZP_Backend: POST /payments/orders
    note over ZZP_Web,ZZP_Backend: Headers: Authorization, Idempotency-Key, X-Request-ID<br/>Body: packageId, pricePlanId, subscriptionAction, paymentMethod=OCB_QR

    note over ZZP_Backend: Auth: verify token → sellerId<br/>Idempotency: sellerId + idempotencyKey<br/>Validate package + pricePlan ACTIVE<br/>Tính amount server-side (600k / 7.2m)<br/>INSERT payment_orders (CREATED), snapshot, subscription_preview<br/>Audit: PAYMENT_ORDER_CREATED

    ZZP_Backend->>OCB: POST Generate QR (orderCode, amount, description)
    note over OCB: VietQR dynamic — amount + orderCode trong description<br/>Secret/key OCB chỉ ở server

    alt OCB QR failed
        OCB-->ZZP_Backend: error / timeout
        note over ZZP_Backend: UPDATE order status=QR_CREATE_FAILED<br/>Audit: QR_CREATE_FAILED
        ZZP_Backend-->ZZP_Web: 503 payment_unavailable
        ZZP_Web-->Seller: Lỗi hệ thống thanh toán — thử lại
    else OCB QR success
        OCB-->ZZP_Backend: qrPayload, qrImageUrl, ocbReferenceId
        note over ZZP_Backend: UPDATE order status=WAITING_PAYMENT, expires_at=now+15m<br/>Audit: QR_GENERATED
        ZZP_Backend-->ZZP_Web: 201 order + QR + subscriptionPreview
        ZZP_Web-->Seller: Hiển thị QR + số tiền + orderCode + countdown 15 phút
    end

    %% ── Phase 3: Thanh toán + polling ──
    note over Seller,OCB: Seller quét QR trên Web (app ngân hàng / MoMo hỗ trợ VietQR)
    Seller->>OCB: Quét QR và chuyển khoản

    loop Mỗi 3–5s trong lúc chờ
        ZZP_Web->>ZZP_Backend: GET /payments/orders/{orderId}/status
        note over ZZP_Backend: Verify token + order ownership (sellerId)
        ZZP_Backend-->ZZP_Web: WAITING_PAYMENT | PAID | EXPIRED | MANUAL_REVIEW
        ZZP_Web-->Seller: Cập nhật UI tương ứng
    end

    %% ── Phase 4: Webhook + đối soát async ──
    OCB->>ZZP_Backend: POST /webhooks/ocb/payment
    note over ZZP_Backend: Verify X-OCB-Signature + timestamp<br/>INSERT bank_webhook_events (transactionId UNIQUE)<br/>Duplicate transactionId → 200 ACK, bỏ qua<br/>Mới → enqueue reconcile_payment → 200 ACK nhanh

    note over ZZP_Backend: ReconcileWorker (async):<br/>Lock webhook + order FOR UPDATE<br/>Extract orderCode + amount từ description

    alt Đối soát thất bại
        note over ZZP_Backend: Lý do: không tìm thấy order, sai amount, order EXPIRED/CANCELLED/PAID<br/>UPDATE status=MANUAL_REVIEW + reason_code<br/>Audit: RECONCILIATION_FAILED<br/>Alert BD/Kế toán (email/Slack)
        ZZP_Backend-->OCB: 200 ACK
    else orderCode + amount khớp, order WAITING_PAYMENT, chưa hết hạn
        note over ZZP_Backend: UPDATE order status=PAID<br/>INSERT payment_state_transitions<br/>Ledger: CREDIT entry (audit, chống double-credit)<br/>SubscriptionService: activateOrExtend (NEW/RENEW)<br/>Audit: PAYMENT_PAID, SUBSCRIPTION_ACTIVATED
        ZZP_Backend-->OCB: 200 ACK
    end

    %% ── Phase 5: Kết quả cuối ──
    ZZP_Web->>ZZP_Backend: GET /payments/orders/{orderId}/status
    ZZP_Backend-->ZZP_Web: Trạng thái cuối

    alt PAID + subscription ACTIVE
        ZZP_Web-->Seller: "Thanh toán thành công. Gói SaaS đã được kích hoạt."
    else MANUAL_REVIEW
        ZZP_Web-->Seller: "Thanh toán cần được kiểm tra thêm. Liên hệ hỗ trợ."
        note over ZZP_Backend: BD/Kế toán review raw webhook + reason_code
    else EXPIRED
        ZZP_Web-->Seller: "Giao dịch đã hết hạn. Vui lòng tạo đơn mới."
        note over ZZP_Backend: ExpiryJob: WAITING_PAYMENT + expires_at < now → EXPIRED<br/>Webhook muộn sau EXPIRED → MANUAL_REVIEW (không auto-activate)
    else WAITING_PAYMENT
        ZZP_Web-->Seller: Tiếp tục hiển thị QR + countdown
    end
```

## Ánh xạ module (chi tiết triển khai)

Diagram trên dùng **4 actor** ở tầng hệ thống. Khi triển khai, `ZZP_Backend` tách thành các module sau:

| Module | Trách nhiệm |
| --- | --- |
| PaymentAPI | REST: danh sách gói, đơn hàng, trạng thái |
| AuthService | Xác thực Bearer token → sellerContext |
| PackagePricingService | Kiểm tra gói + price plan ACTIVE |
| PaymentService | Tạo đơn, idempotency, gọi OCB gen QR |
| WebhookAPI | Nhận webhook OCB, verify chữ ký |
| Queue + ReconcileWorker | Đối soát async: khớp orderCode + amount |
| LedgerService | Ghi CREDIT bất biến, chống cộng tiền 2 lần |
| SubscriptionService | activateOrExtend sau PAID |
| PaymentDB | payment_orders, bank_webhook_events, snapshots, ledger, subscriptions |
| AuditLog | Sự kiện PAYMENT_ORDER_CREATED, QR_GENERATED, PAYMENT_PAID, … |
| ExpiryJob | Cron: WAITING_PAYMENT quá 15p → EXPIRED |

## Bề mặt API

| Method | Path | Mục đích |
| --- | --- | --- |
| GET | `/saas/packages` | Danh sách gói SaaS + price plan |
| POST | `/payments/orders` | Tạo đơn + gen QR OCB |
| GET | `/payments/orders/{orderId}/status` | Poll trạng thái cho Web |
| POST | `/webhooks/ocb/payment` | Nhận biến động số dư từ OCB |

## Trạng thái đơn hàng

`CREATED` → `WAITING_PAYMENT` → `PAID` | `EXPIRED` | `CANCELLED` | `MANUAL_REVIEW` | `QR_CREATE_FAILED`
