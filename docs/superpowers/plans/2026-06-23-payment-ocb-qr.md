# Kế hoạch triển khai — Thanh toán OCB QR (SaaS)

> **Cho agent/worker:** BẮT BUỘC dùng skill subagent-driven-development (khuyến nghị) hoặc executing-plans để thực hiện từng task. Các bước dùng checkbox (`- [ ]`) để theo dõi.

**Mục tiêu:** Triển khai end-to-end thanh toán đăng ký/gia hạn gói SaaS qua OCB VietQR trên Website, đối soát webhook bất đồng bộ và tự động kích hoạt subscription.

**Kiến trúc:** Microservice/module payment NestJS + PostgreSQL + worker BullMQ. Webhook ingest nhanh; `ReconcileWorker` khớp `orderCode` + `amount`, chuyển `PAID`, ghi ledger audit, gọi `SubscriptionService`. BE enforce hết hạn 15 phút và `MANUAL_REVIEW` cho thanh toán trễ ([ADR 0004](../adr/0004-payment-ocb-async-reconciliation.md)).

**Tech stack:** TypeScript, NestJS, Prisma (hoặc Drizzle), PostgreSQL, BullMQ + Redis, Vitest/Jest, Zod. Frontend: app Web ZZP hiện có (giả định Next.js) — checkout + polling.

**Spec:** [2026-06-23-payment-reconciliation-design.md](../superpowers/specs/2026-06-23-payment-reconciliation-design.md)  
**PRD:** [thanhtoan.md](../../thanhtoan.md) · **Sơ đồ:** [payment-flow.md](../../payment-flow.md)  
**Spike OCB (chặn prod):** [2026-06-23-ocb-integration-spike.md](../superpowers/specs/2026-06-23-ocb-integration-spike.md)

---

## Bản đồ file (greenfield)

```
services/payment/
  package.json
  prisma/schema.prisma
  src/
    main.ts
    app.module.ts
    config/ocb.config.ts
    common/auth/seller-context.guard.ts
    modules/
      packages/packages.controller.ts
      packages/package-pricing.service.ts
      payments/payments.controller.ts
      payments/payment.service.ts
      payments/dto/create-payment-order.dto.ts
      payments/payment-order.repository.ts
      ocb/ocb.client.ts
      ocb/ocb.client.mock.ts
      webhooks/ocb-webhook.controller.ts
      webhooks/ocb-signature.guard.ts
      reconcile/reconcile.processor.ts
      reconcile/reconcile.service.ts
      reconcile/reason-codes.ts
      ledger/ledger.service.ts
      subscriptions/subscription.service.ts
      jobs/expiry.job.ts
      audit/audit-log.service.ts
  test/
    unit/reconcile.service.spec.ts
    unit/payment.service.spec.ts
    integration/webhook-reconcile.spec.ts
apps/web/   (hoặc đường dẫn frontend ZZP hiện có)
  src/app/pricing/page.tsx
  src/app/checkout/[orderId]/page.tsx
  src/lib/payment-api.ts
```

Điều chỉnh đường dẫn cho khớp cấu trúc repo ZZP thực tế khi tích hợp.

---

## Task 1: Scaffold service payment + schema DB

**File:**
- Tạo: `services/payment/package.json`, `services/payment/prisma/schema.prisma`, `services/payment/src/main.ts`

- [ ] **Bước 1: Khởi tạo NestJS + Prisma**

```bash
cd services/payment
npm init -y
npm install @nestjs/common @nestjs/core @nestjs/platform-express @nestjs/bullmq bullmq ioredis @prisma/client zod
npm install -D prisma typescript vitest @types/node
npx prisma init
```

- [ ] **Bước 2: Định nghĩa schema Prisma** (`prisma/schema.prisma`)

```prisma
enum PaymentOrderStatus {
  CREATED
  WAITING_PAYMENT
  PAID
  EXPIRED
  CANCELLED
  MANUAL_REVIEW
  QR_CREATE_FAILED
}

enum WebhookEventStatus {
  RECEIVED
  PROCESSED
  FAILED
}

model PaymentOrder {
  id                    String   @id @default(uuid())
  sellerId              String
  packageId             String
  pricePlanId           String
  orderCode             String   @unique
  amount                BigInt
  currency              String   @default("VND")
  status                PaymentOrderStatus
  expiresAt             DateTime
  paidAt                DateTime?
  paidAmount            BigInt?
  bankTransactionId     String?
  matchedWebhookEventId String?
  qrPayload             String?
  qrImageUrl            String?
  ocbReferenceId        String?
  idempotencyKey        String
  createdAt             DateTime @default(now())
  snapshot              PaymentOrderSnapshot?
  subscriptionPreview   SubscriptionPreview?
  stateTransitions      PaymentStateTransition[]
  @@unique([sellerId, idempotencyKey])
}

model PaymentOrderSnapshot {
  id              String @id @default(uuid())
  paymentOrderId  String @unique
  paymentOrder    PaymentOrder @relation(fields: [paymentOrderId], references: [id])
  packageName     String
  billingCycle    String
  durationMonths  Int
  unitAmount      BigInt
  finalAmount     BigInt
  pricingVersion  String
}

model SubscriptionPreview {
  id                 String @id @default(uuid())
  paymentOrderId     String @unique
  paymentOrder       PaymentOrder @relation(fields: [paymentOrderId], references: [id])
  action             String
  periodStartPreview DateTime
  periodEndPreview   DateTime
}

model BankWebhookEvent {
  id              String @id @default(uuid())
  provider        String @default("OCB")
  transactionId   String @unique
  amount          BigInt
  currency        String
  description     String
  rawPayload      Json
  signatureValid  Boolean
  status          WebhookEventStatus
  receivedAt      DateTime @default(now())
}

model PaymentStateTransition {
  id             String @id @default(uuid())
  paymentOrderId String
  paymentOrder   PaymentOrder @relation(fields: [paymentOrderId], references: [id])
  fromStatus     PaymentOrderStatus
  toStatus       PaymentOrderStatus
  reasonCode     String?
  createdAt      DateTime @default(now())
}

model PaymentLedger {
  id              String @id @default(uuid())
  sellerId        String
  paymentOrderId  String
  webhookEventId  String
  entryType       String @default("CREDIT")
  amount          BigInt
  source          String @default("OCB_QR_PAYMENT")
  createdAt       DateTime @default(now())
}
```

- [ ] **Bước 3: Chạy migration**

```bash
npx prisma migrate dev --name init_payment_tables
```

Kỳ vọng: file migration SQL được tạo, bảng tồn tại trên Postgres local.

- [ ] **Bước 4: Commit**

```bash
git add services/payment
git commit -m "feat(payment): scaffold service and payment schema"
```

---

## Task 2: API bảng giá gói

**File:**
- Tạo: `services/payment/src/modules/packages/packages.controller.ts`
- Tạo: `services/payment/src/modules/packages/package-pricing.service.ts`
- Test: `services/payment/test/unit/package-pricing.service.spec.ts`

- [ ] **Bước 1: Viết test fail trước**

```typescript
import { describe, it, expect } from 'vitest';
import { PackagePricingService } from '../../src/modules/packages/package-pricing.service';

describe('PackagePricingService', () => {
  it('returns only ACTIVE packages with ACTIVE price plans', async () => {
    const svc = new PackagePricingService(/* mock repo */);
    const result = await svc.getActivePackagesAndPricePlans();
    expect(result.every((p) => p.status === 'ACTIVE')).toBe(true);
  });
});
```

- [ ] **Bước 2: Chạy test — kỳ vọng FAIL**

```bash
npm run test -- test/unit/package-pricing.service.spec.ts
```

- [ ] **Bước 3: Implement `GET /saas/packages`**

Trả về đúng shape trong design spec:

```typescript
// packages.controller.ts
@Get('saas/packages')
listPackages() {
  return this.packagePricingService.getActivePackagesAndPricePlans();
}
```

Seed hai gói trong migration hoặc seed script: tháng `600000` VND, năm `7200000` VND.

- [ ] **Bước 4: Chạy test — kỳ vọng PASS**

- [ ] **Bước 5: Commit**

```bash
git commit -m "feat(payment): add GET /saas/packages"
```

---

## Task 3: Tạo payment order + idempotency

**File:**
- Tạo: `services/payment/src/modules/payments/payments.controller.ts`
- Tạo: `services/payment/src/modules/payments/payment.service.ts`
- Tạo: `services/payment/src/modules/payments/dto/create-payment-order.dto.ts`
- Test: `services/payment/test/unit/payment.service.spec.ts`

- [ ] **Bước 1: Viết test idempotency fail trước**

```typescript
it('returns same order when idempotency key repeats', async () => {
  const key = 'idem-001';
  const a = await paymentService.createSaasPaymentOrder(dto, sellerContext, key);
  const b = await paymentService.createSaasPaymentOrder(dto, sellerContext, key);
  expect(a.id).toBe(b.id);
  expect(a.orderCode).toBe(b.orderCode);
});
```

- [ ] **Bước 2: Implement `createSaasPaymentOrder`**

1. Tra `sellerId + idempotencyKey` — trả đơn cũ nếu đã tồn tại
2. Validate `packageId` + `pricePlanId` qua PackagePricingService
3. Tính `amount` ở server (không tin client)
4. Sinh `orderCode` ví dụ `ZZP-${yyyyMMdd}-${randomBase32}`
5. Transaction: insert order `CREATED`, snapshot, subscription_preview, audit `PAYMENT_ORDER_CREATED`
6. Gọi OCB client (Task 4) **ngoài** transaction
7. Thành công → `WAITING_PAYMENT`, `expiresAt = now + 15m`

- [ ] **Bước 3: Controller `POST /payments/orders`**

Bắt buộc header: `Authorization`, `Idempotency-Key`. Body validate bằng Zod:

```typescript
const CreatePaymentOrderSchema = z.object({
  packageId: z.string().uuid(),
  pricePlanId: z.string().uuid(),
  subscriptionAction: z.enum(['NEW', 'RENEW']),
  targetSubscriptionId: z.string().uuid().nullable(),
  paymentMethod: z.literal('OCB_QR'),
  clientReference: z.string().nullable().optional(),
});
```

- [ ] **Bước 4: Chạy test — PASS**

- [ ] **Bước 5: Commit**

```bash
git commit -m "feat(payment): create order with idempotency and snapshots"
```

---

## Task 4: OCB client (mock + adapter thật)

**File:**
- Tạo: `services/payment/src/modules/ocb/ocb.client.ts`
- Tạo: `services/payment/src/modules/ocb/ocb.client.mock.ts`
- Tạo: `services/payment/src/config/ocb.config.ts`

- [ ] **Bước 1: Định nghĩa interface**

```typescript
export interface OcbGenerateQrRequest {
  orderCode: string;
  amount: number;
  currency: 'VND';
  description: string;
  expiresAt: Date;
}

export interface OcbGenerateQrResponse {
  qrPayload: string;
  qrImageUrl: string;
  ocbReferenceId: string;
}

export interface OcbClient {
  generateQr(req: OcbGenerateQrRequest): Promise<OcbGenerateQrResponse>;
}
```

- [ ] **Bước 2: Mock client cho dev local**

Trả chuỗi VietQR tĩnh; log request để debug.

- [ ] **Bước 3: HTTP client thật**

POST endpoint OCB từ tài liệu spike; ký request theo spec OCB; lưu raw request/response trên đơn; timeout 10s.

- [ ] **Bước 4: Chọn qua env `OCB_CLIENT=mock|live`**

- [ ] **Bước 5: Commit**

```bash
git commit -m "feat(payment): OCB QR client with mock adapter"
```

---

## Task 5: Endpoint polling trạng thái đơn

**File:**
- Sửa: `services/payment/src/modules/payments/payments.controller.ts`

- [ ] **Bước 1: `GET /payments/orders/:orderId/status`**

- Verify Bearer token → `sellerId`
- Load order; **403 nếu `order.sellerId !== sellerId`**
- Join trạng thái subscription nếu `PAID`
- Trả `{ status, orderCode, amount, expiresAt, subscription?: { status, periodEnd } }`

- [ ] **Bước 2: Integration test kiểm tra quyền sở hữu đơn**

- [ ] **Bước 3: Commit**

```bash
git commit -m "feat(payment): add order status polling endpoint"
```

---

## Task 6: Ingest webhook OCB

**File:**
- Tạo: `services/payment/src/modules/webhooks/ocb-webhook.controller.ts`
- Tạo: `services/payment/src/modules/webhooks/ocb-signature.guard.ts`

- [ ] **Bước 1: `POST /webhooks/ocb/payment`**

1. Đọc raw body (bắt buộc cho verify chữ ký)
2. `OcbSignatureGuard` validate `X-OCB-Signature` + cửa sổ timestamp
3. Parse `transactionId`, `amount`, `description`, `currency`
4. Insert `bank_webhook_events` — unique violation → audit `DUPLICATE_WEBHOOK_IGNORED`, return 200
5. Enqueue job `reconcile_payment` với `eventId`
6. Return 200 ngay

- [ ] **Bước 2: Test `transactionId` trùng trả 200 không enqueue job 2 lần**

- [ ] **Bước 3: Commit**

```bash
git commit -m "feat(payment): OCB webhook ingest with signature verify"
```

---

## Task 7: Worker đối soát (core)

**File:**
- Tạo: `services/payment/src/modules/reconcile/reconcile.processor.ts`
- Tạo: `services/payment/src/modules/reconcile/reconcile.service.ts`
- Tạo: `services/payment/src/modules/reconcile/reason-codes.ts`
- Test: `services/payment/test/unit/reconcile.service.spec.ts`

- [ ] **Bước 1: Viết test fail trước**

```typescript
describe('ReconcileService', () => {
  it('marks PAID when orderCode and amount match WAITING_PAYMENT before expiry', async () => { /* ... */ });
  it('marks MANUAL_REVIEW with LATE_PAYMENT when order EXPIRED', async () => { /* ... */ });
  it('marks MANUAL_REVIEW with AMOUNT_MISMATCH when amounts differ', async () => { /* ... */ });
  it('ignores duplicate PAID transition', async () => { /* ... */ });
});
```

- [ ] **Bước 2: Implement `reconcile(eventId)`**

```typescript
async reconcile(eventId: string): Promise<void> {
  await this.db.$transaction(async (tx) => {
    const event = await tx.bankWebhookEvent.findUniqueOrThrow({ where: { id: eventId } });
    const orderCode = extractOrderCode(event.description);
    if (!orderCode) return this.fail(tx, event, null, 'INVALID_DESCRIPTION');

    const order = await tx.paymentOrder.findUnique({ where: { orderCode } });
    if (!order) return this.fail(tx, event, null, 'ORDER_NOT_FOUND');

    if (BigInt(event.amount) !== order.amount) return this.fail(tx, event, order, 'AMOUNT_MISMATCH');
    if (order.status === PaymentOrderStatus.PAID) return; // idempotent
    if (order.status === PaymentOrderStatus.EXPIRED || order.status === PaymentOrderStatus.CANCELLED)
      return this.fail(tx, event, order, 'LATE_PAYMENT');
    if (order.status !== PaymentOrderStatus.WAITING_PAYMENT)
      return this.fail(tx, event, order, 'ORDER_NOT_WAITING');
    if (new Date() > order.expiresAt)
      return this.fail(tx, event, order, 'ORDER_EXPIRED');

    await this.transition(tx, order, PaymentOrderStatus.PAID);
    await this.ledgerService.createEntry(tx, order, event);
    await this.subscriptionService.activateOrExtend(tx, order);
    await tx.bankWebhookEvent.update({ where: { id: eventId }, data: { status: 'PROCESSED' } });
  });
}
```

- [ ] **Bước 3: Đăng ký BullMQ processor `reconcile_payment`**

- [ ] **Bước 4: Khi fail → `MANUAL_REVIEW` + alert stub (log/Slack webhook env)**

- [ ] **Bước 5: Chạy test — PASS**

- [ ] **Bước 6: Commit**

```bash
git commit -m "feat(payment): async reconcile worker with MANUAL_REVIEW paths"
```

---

## Task 8: Kích hoạt subscription

**File:**
- Tạo: `services/payment/src/modules/subscriptions/subscription.service.ts`

- [ ] **Bước 1: `activateOrExtend(paymentOrder)`**

- Load snapshot `durationMonths`
- **NEW:** `periodStart = paidAt`, `periodEnd = paidAt + durationMonths`
- **RENEW:** `periodStart = currentPeriodEnd`, `periodEnd = currentPeriodEnd + durationMonths`
- Upsert `seller_subscriptions` (có thể ở DB dùng chung — gọi service hiện có hoặc cùng schema)
- Insert `subscription_events` audit

- [ ] **Bước 2: Unit test gói tháng (+1 tháng) và năm (+12 tháng)**

- [ ] **Bước 3: Commit**

```bash
git commit -m "feat(payment): subscription activateOrExtend after PAID"
```

---

## Task 9: Job hết hạn đơn

**File:**
- Tạo: `services/payment/src/modules/jobs/expiry.job.ts`

- [ ] **Bước 1: Cron mỗi phút**

```typescript
await prisma.paymentOrder.updateMany({
  where: {
    status: 'WAITING_PAYMENT',
    expiresAt: { lt: new Date() },
  },
  data: { status: 'EXPIRED' },
});
// Đồng thời insert state_transitions từng đơn (find + loop để audit)
```

- [ ] **Bước 2: Test: đơn quá expiresAt chuyển EXPIRED**

- [ ] **Bước 3: Commit**

```bash
git commit -m "feat(payment): expiry job for WAITING_PAYMENT orders"
```

---

## Task 10: Luồng checkout Frontend

**File:**
- Tạo: `apps/web/src/lib/payment-api.ts`
- Tạo: `apps/web/src/app/pricing/page.tsx`
- Tạo: `apps/web/src/app/checkout/[orderId]/page.tsx`

- [ ] **Bước 1: Wrapper `payment-api.ts`**

```typescript
export async function getSaasPackages(token: string) {
  return fetch(`${API_BASE}/saas/packages`, { headers: { Authorization: `Bearer ${token}` } });
}

export async function createPaymentOrder(token: string, idempotencyKey: string, body: CreateOrderBody) {
  return fetch(`${API_BASE}/payments/orders`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Idempotency-Key': idempotencyKey,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });
}

export async function getOrderStatus(token: string, orderId: string) {
  return fetch(`${API_BASE}/payments/orders/${orderId}/status`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}
```

- [ ] **Bước 2: Trang bảng giá** — list gói, CTA tạo đơn với `crypto.randomUUID()` làm idempotency key

- [ ] **Bước 3: Trang checkout** — hiển thị `qr.imageUrl`, amount, `orderCode`, countdown từ `expiresAt`

- [ ] **Bước 4: Poll mỗi 4s** đến khi `PAID | EXPIRED | MANUAL_REVIEW | QR_CREATE_FAILED`

- [ ] **Bước 5: Copy UI từ PRD** ([thanhtoan.md](../../thanhtoan.md) mục 2.4)

- [ ] **Bước 6: Commit**

```bash
git commit -m "feat(web): SaaS pricing and OCB QR checkout with polling"
```

---

## Task 11: Integration test end-to-end (mock OCB)

**File:**
- Tạo: `services/payment/test/integration/webhook-reconcile.spec.ts`

- [ ] **Bước 1: Kịch bản happy path**

1. Tạo đơn qua API (mock OCB)
2. Giả lập webhook POST khớp orderCode + amount
3. Đợi worker
4. Assert order `PAID` và subscription active

- [ ] **Bước 2: Kịch bản thanh toán trễ**

1. Tạo đơn, set `expiresAt` quá khứ, status `EXPIRED`
2. Webhook khớp → `MANUAL_REVIEW`, subscription không đổi

- [ ] **Bước 3: Commit**

```bash
git commit -m "test(payment): e2e webhook reconcile happy and late paths"
```

---

## Task 12: Cổng spike OCB (trước production)

**File:**
- Cập nhật: [2026-06-23-ocb-integration-spike.md](../superpowers/specs/2026-06-23-ocb-integration-spike.md)

- [ ] Điền đủ 10 dòng spike kèm bằng chứng
- [ ] Nếu scheme chữ ký khác stub, cập nhật `OcbSignatureGuard`
- [ ] Chỉ bật `OCB_CLIENT=live` trên staging sau khi spike được phê duyệt
- [ ] Bổ sung kết luận spike vào [ADR 0004](../adr/0004-payment-ocb-async-reconciliation.md) nếu cần

---

## Checklist phủ spec

| Mục spec | Task |
| -------- | ---- |
| D1 SaaS subscription | Task 2, 3, 8, 10 |
| D3 Đối soát async | Task 6, 7 |
| D4 Thanh toán trễ MANUAL_REVIEW | Task 7 tests |
| D5 Hết hạn BE | Task 3, 9 |
| Hợp đồng API | Task 2, 3, 5, 6 |
| Mô hình dữ liệu | Task 1 |
| Polling frontend | Task 10 |
| Chữ ký bảo mật | Task 6 |
| Cổng spike OCB | Task 12 |

---

## Bàn giao thực thi

**Plan lưu tại:** `docs/superpowers/plans/2026-06-23-payment-ocb-qr.md`

**Hai cách thực thi:**

1. **Subagent-Driven (khuyến nghị)** — mỗi task một subagent mới, review giữa các task  
2. **Inline Execution** — chạy liên tục trong một session, checkpoint sau Task 7 (đối soát)

**Bạn chọn cách nào?**
