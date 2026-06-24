**AWS Detective** là dịch vụ **điều tra (investigation) và phân tích nguyên nhân gốc rễ (root cause analysis)** của các sự cố bảo mật trên AWS.

Nếu:

* **GuardDuty** trả lời: *"Có vấn đề rồi!"*
* **Security Hub** trả lời: *"Đây là danh sách cảnh báo!"*
* **Detective** trả lời: *"Chuyện gì đã xảy ra? Ai làm? Bắt đầu từ đâu?"*

---

## Ví dụ dễ hiểu

Giả sử GuardDuty báo:

```text
UnauthorizedAccess:IAMUser/AnomalousBehavior
Severity: High
```

Bạn biết:

✅ Có chuyện bất thường

Nhưng chưa biết:

❌ User nào?

❌ Từ IP nào?

❌ Đã truy cập resource nào?

❌ Bị ảnh hưởng bao nhiêu EC2?

❌ Chuyện bắt đầu từ khi nào?

---

Detective sẽ tự động dựng đồ thị điều tra:

```text
IAM User A
    ↓
Login từ IP Nga
    ↓
Assume Role Admin
    ↓
List S3 Buckets
    ↓
Download Customer Data
    ↓
Launch EC2
```

Bạn không cần tự mò hàng triệu dòng CloudTrail.

---

# Detective lấy dữ liệu từ đâu?

Detective thu thập và liên kết dữ liệu từ:

* CloudTrail
* VPC Flow Logs
* GuardDuty Findings
* EKS Audit Logs
* IAM
* EC2 metadata

Nó xây dựng một **behavior graph**.

---

## Behavior Graph là gì?

Thay vì xem log dạng text:

```text
12:00 Login
12:05 ListBucket
12:06 GetObject
```

Detective tạo quan hệ:

```text
User
  ↓
IP Address
  ↓
Role
  ↓
EC2
  ↓
S3 Bucket
```

Giống như Neo4j hoặc Graph Database.

---

## Ví dụ thực tế

### Case 1: IAM bị hack

GuardDuty:

```text
Credential Compromise
```

Detective:

```text
User: admin
First Seen: 09:00
Source IP: 1.2.3.4
Country: Russia
Affected Resources:
- S3
- EC2
- IAM
```

---

### Case 2: EC2 bị malware

GuardDuty:

```text
Backdoor Detected
```

Detective:

```text
EC2 i-12345
    ↓
Connected to Malicious IP
    ↓
Downloaded Payload
    ↓
Started Process
```

Bạn thấy được chuỗi sự kiện.

---

## Detective vs GuardDuty

| GuardDuty         | Detective          |
| ----------------- | ------------------ |
| Phát hiện         | Điều tra           |
| Alert             | Root Cause         |
| Có gì bất thường? | Vì sao bất thường? |
| Real-time         | Forensics          |

Ví dụ:

```text
GuardDuty:
EC2 talking to malware IP
```

Detective:

```text
EC2
 ↓
Downloaded file X
 ↓
Opened port 4444
 ↓
Connected malware IP
```

---

## Detective vs CloudTrail

CloudTrail:

```text
10 triệu dòng log
```

Detective:

```text
Timeline
Graph
Relationships
```

CloudTrail là log.

Detective là công cụ phân tích log.

---

## Detective vs Security Hub

| Security Hub       | Detective             |
| ------------------ | --------------------- |
| Dashboard findings | Investigation         |
| Tổng hợp cảnh báo  | Phân tích nguyên nhân |
| SOC Dashboard      | Forensics Tool        |

Thường dùng chung:

```text
GuardDuty
     ↓
Security Hub
     ↓
Detective
```

---

## Luồng chuẩn trong doanh nghiệp

```text
CloudTrail
VPC Flow Logs
GuardDuty
      ↓
 Security Hub
      ↓
   Detective
      ↓
 SOC Team
```

Ví dụ:

1. GuardDuty phát hiện EC2 đáng ngờ.
2. Security Hub hiển thị Finding.
3. Security Engineer bấm **Investigate in Detective**.
4. Detective mở:

   * Timeline
   * User liên quan
   * IP liên quan
   * Resource liên quan
   * Hành vi trước và sau sự cố

---

# Khi nào nên dùng Detective?

Detective rất hữu ích khi:

* Có nhiều AWS Account.
* Cần điều tra incident nhanh.
* Có SOC/Security Team.
* Muốn giảm thời gian phân tích CloudTrail.

Nếu GuardDuty là **camera báo động**, thì Detective giống **camera ghi hình + công cụ tua lại toàn bộ vụ việc** để biết chính xác điều gì đã xảy ra.

Một cách nhớ nhanh bộ Security AWS:

```text
GuardDuty  -> Phát hiện tấn công
Inspector  -> Tìm lỗ hổng
Macie      -> Tìm dữ liệu nhạy cảm
Config     -> Kiểm tra cấu hình
Detective  -> Điều tra sự cố
SecurityHub-> Trung tâm cảnh báo
FirewallMgr-> Quản lý firewall
```

Đây là bộ dịch vụ thường xuất hiện cùng nhau trong các kiến trúc DevSecOps và AWS Security Specialty.
