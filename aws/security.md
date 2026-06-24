Cloudtrail

management event

data event

insight event

retention default 90 days -> log  s3 bucket for longterm retention -> analyze using athena 

---

Cloudtrail + Event Bridge -> intercep api call

User delete table using Delete Table API Call -> Dynamo DB -> Cloudtrail
-> Amazon Event Bridge -> SNS (alert)

---

```
Solution Architect : Delivery to S3
Cloudtrail (every 5 minutes) 
    
    -> (SSE-S3 (default) or SS3-KMS) S3 -> (lifecycle policy) -> Glacier
    
    -> use S3 Event to fire event to SQS, SNS, Lambda
```

but you can have cloudtrail directly into SNS using Delivery Notification -> SQS,Lambda


S3 Enhancement:
- Enable versioning
- MFA delete protection
- S3 lifecycle policies
- S3 object lock
- SSE-S3, SSE-KMS encryption
- Feature perform Cloudtrail Log File Integrity validation
(SHA 256 for hashing and signing)

---

Solution Architect:
Cloudtrail can have multi account, multi region logging

---


Solution Architect:
Alert for API calls

cloudtrail (stream to) CW log -> metric filter -> CW alarm -> SNS

---
Solution Architect:
Organization Trail

---

Overall, Clourtrail may take up to 15mins to deliver events
- Event bridge 
    - can be trigger for any api call in cloudtrail
    - the fastest, most reactive way

- Cloud trail delivery in cloudwatch logs 
    - events are streams
    - can perform a metric filter to analyze occurrences and anomalies 
- Cloud trail delivery in aws S3:
    - events are deliver in every 5 mins
    - Possibility of analyzing logs integrity, deliver cross account, longterm storage

---
AWS KMS (Key management service)

encryption key
manage keys
fully integrate with IAM
Seamlessly integrated into:

    - Amazon EBS: Encrypt volumes 
    - S3; server side ecryption of object
    - Redshift:  encryption of data
    - RDS; encryption of data
    - SSM: parameter store
    - ect.

KSM Keys are regional, can only be used in the region they are created in

---

Type of keys:

Symmetric Keys: (AES-256 Key)
- first offering of kms, single encrytion key use to encrypt and decrypt
- aws service integrate with ksm using symmetric keys
- necessary for envelop encryption
- you never get access to KMS key unencrypted (must call via KMS API to use)

Asymmetric Keys: (RSA and ECC key pairs)
- public (encrypt key) and private (decrypt key) pair
- used for Encrypt/Decrypt or Sign/Verify operations
- public key is downloadable, but you cant access the Private Key unencrypted
- use case: encryption outside aws by users who cant call the kms api

---
Type of KMS Keys:

Customer Managed Keys:
- create, manage and use, can be enable and disable
- possibility of rotation policy (new key generated every year, old key preserved)
- can **add** a key policy (resource policy) & audit in cloudtrail
- leverage for envelop encyption

AWS managed keys:
- Used by AWS services (s3/elb/redshift)
- Manage by aws (automatically rotated every 1 year)
- can **view** key policy (resource policy) & audit in cloudtrail
 
AWS Owned Keys;
- created by aws, use by some aws services to protect for resources
- use in multiple aws accounts, but they are not in your aws account
- cannot view, track, use, or audit


---
AWS Key Material Origin
- identifies the source of the key material in the KMS Key
- cant be change after creation
- KMS (AWS_KMS)
- External (EXTERNAL) you import
- Custom Key Store (AWS_CLOUDHSM)

---
Secret manager - sharing accross account

- there is no way using Resource Access Manager (RAM)
- instead using attach resource-based policy to the secret
- or share using KMS policy 

--- 
SSL/TLS
DNSSEC
Diffie-Hellman

---
S3 Object Lock & Glacier Vault Lock

S3 Object Lock
- Adopt a WORM (write one read many) model
- Block an object version deletion for a specific amount of time

Glacier Lock
- Adopt a WORM
- Lock the policy for future edits (can no longer be changed)

---

S3 Access Point

Simplify security management for S3 buckets

Each access point has:

- its own DNS name(internet origin or VPC origin)
    - ec2 -> vpc endpoint -> access point (vpc origin) -> s3 bucket
    - access point có hỗ trợ multi region, nếu các bucket replication giữa các region -> s3 multi-region access point sẽ routing đến region có latency thấp nhất -> có hỗ trợ fail over
- an access point policy (similar to bucket policy) - manage security as scale

---

S3 Object lambda
```
Client
  ↓ GET object
S3 Object Lambda access point
  ↓
Redacting lambda function
  ↓
Support S3 Access point
  ↓
S3 Bucket
  ↓
Lambda xử lý dữ liệu
  ↓
Trả kết quả đã biến đổi
Client
```
thay vì 
```
Client
  ↓
S3
  ↓
File gốc
```
có khả năng transform và che giấu data 

redact

resize

watermark

---
AWS Shield Standard
- free
- protect againt DDOS (Distributed Denied-of-Service)

AWS Shield Advanced:
- 24/7 premium DDOS protection

AWS WAF:
- filter specific request based on rules

Cloudfront and Route 53
- availability protection using global edge network
- combined with AWS Shield, provides DDOS attack mitigation at the edge


Be ready to scale - leverage AWS Auto scaling

Separate static resource (S3/cloudfront) from dynamic ones (ec2/alb)

---
AWS WAF (Web application firewall)

- Protect on layer 7
- Deploy on ALB
- Deploy on API Gateway
- Deploy on cloudfront
- Deploy on AppSync (protect your graphql apis)
- WAF is not for DDoS protection
- define WEB ACL (Web access controll list)
- Rule actions: count|allow|block|CAPTCHA|Challenge


Về phần logging

có thể gửi traffic loggin đến:
- cloudwatch logs
- aws s3 bucket (5min interval)
- aws kinesis data firehose - limited by firehose quota ->
    - aws s3
    - aws redshift
    - aws opensearch
    - ...
---

Solution Architect - Enhance Cloudfront Origin Security with AWS WAF & AWS Secret Manager

Users -> AWS WAF (WACL) -> Cloudfront -> Custom http header (X-Origin-Verify: xxx) -> WAF (filtering rule) -> ALB -> EC2


Custom http header có thể được set auto-rotate ở aws secret manager -> lambda function invoke -> update aws cloudfront

```
Secrets Manager
      ↓
Generate New Secret
      ↓
Update CloudFront Header
      ↓
Update WAF Validation Rule
      ↓
Deploy
      ↓
Delete Old Secret
```

---

AWS Firewall Manager



Giả sử công ty có:

AWS Organization
```
├── Security Account
├── Shared Services
├── Production
├── Staging
├── Dev
└── Data Platform
```
Mỗi account có:

ALB
CloudFront
API Gateway
VPC
EC2

Nếu không dùng Firewall Manager:

Bạn phải vào từng account:

Prod
  → tạo WAF

Staging
  → tạo WAF

Dev
  → tạo WAF

Hoặc:

20 account
100 ALB
50 CloudFront

rất khó quản lý.

Firewall Manager

Cho phép Security Team quản lý tập trung:

Security Account
      ↓
Firewall Manager
      ↓
Áp policy cho toàn bộ organization

Ví dụ:

Mọi CloudFront phải có WAF

Firewall Manager tự động:

CloudFront A
CloudFront B
CloudFront C

gắn WAF.

Ngay cả khi account mới được tạo bởi:

AWS Control Tower

Firewall Manager cũng tự áp dụng.


----

Blocking IP 

- NACL ở tầng public subnet
-> Security group ở tần ec2
-> Firewall ở tầng software

With ALB
- NACL ở tầng public subnet
-> ALB Security Group (public subnet)
-> EC2 Security Group (private subnet)

With NLB
- NACL ở tầng public subnet
-> NLB Security Group (public subnet)
-> EC2 Security Group (private subnet)

Sau đó có thể apply AWS WAF ở tầng NLB hoặc ALB


Nêu có dùng cloudfront thì k cần dùng NACL -> vì nó trỏ thẳng đến NLB và ALB. đây là mô hình ALB - Cloufront & WAF

---

AWS Inspector (EC2,Image ECR, Lambda)

- automated security assessment
- for ec2 instance
    - leverage aws system manager (SSM) agent
- for containter image push to ECR
- for lambda function
- reporting & integration with AWS Security Hub
- send findings to aws event bridge
---

AWS Config là gì

AWS Config là dịch vụ giúp bạn:

> Ghi lại toàn bộ cấu hình (configuration) của tài nguyên AWS
Theo dõi ai đã thay đổi gì và khi nào
Kiểm tra compliance (tuân thủ) theo các rule

Hiểu đơn giản, nếu CloudTrail là:

> Ai làm gì?

thì AWS Config là:

> Tài nguyên hiện đang được cấu hình như thế nào?
Và đã thay đổi như thế nào theo thời gian?
So sánh với CloudTrail

Ví dụ một Dev sửa Security Group.

CloudTrail

Cho biết:

User: dev-a

Action:
AuthorizeSecurityGroupIngress

Time:
2026-06-14 10:00

=> Ai thực hiện.

AWS Config

Cho biết:

Trước:

22/tcp
source=10.0.0.0/8

Sau:

22/tcp
source=0.0.0.0/0

=> Chính xác cấu hình đã thay đổi như thế nào.

AWS Config ghi lại gì?

Ví dụ EC2:

Instance Type
Security Group
Subnet
Tags
IAM Role
EBS

Ví dụ S3:

Encryption
Bucket Policy
Public Access Block
Versioning

Ví dụ RDS:

Public Access
Backup
Storage
Engine Version

Mỗi lần thay đổi:

AWS Config
    ↓
Snapshot

được lưu lại.

---
AWS Managed Logs

```
Trong hệ sinh thái AWS, các loại log phổ biến là:

Dịch vụ	Log gì?
AWS CloudTrail	Ai thực hiện API nào
Amazon CloudWatch	Application logs, metrics
Amazon VPC Flow Logs	Network traffic của VPC
Elastic Load Balancing	Access logs của ALB/NLB
Amazon Route 53	DNS query logs
AWS WAF	Request bị block/allow
Amazon CloudFront	CDN access logs
```
---

**AWS GuardDuty** là dịch vụ **threat detection (phát hiện mối đe dọa)** được quản lý hoàn toàn bởi [AWS](https://aws.amazon.com?utm_source=chatgpt.com). Nó liên tục phân tích các log và sự kiện trong tài khoản AWS để phát hiện hành vi bất thường, tài khoản bị xâm nhập, malware hoặc hoạt động đáng ngờ.

### GuardDuty lấy dữ liệu từ đâu?

GuardDuty tự động phân tích nhiều nguồn dữ liệu như:

* **CloudTrail Management Events**

  * Ai đang gọi API AWS
  * Có API bất thường không

* **CloudTrail Data Events**

  * Truy cập S3 bất thường
  * Truy cập dữ liệu nhạy cảm

* **VPC Flow Logs**

  * Traffic mạng đi vào/ra EC2
  * Kết nối tới IP độc hại

* **DNS Logs**

  * EC2 truy vấn domain malware
  * Command & Control (C&C) server

* **EKS Audit Logs**

  * Hoạt động đáng ngờ trên Kubernetes

* **Runtime Monitoring**

  * Phân tích process đang chạy trên EC2, ECS, EKS

* **Malware Protection**

  * Quét EBS Volume tìm malware

---

## Ví dụ thực tế

### Case 1: AWS Access Key bị lộ

Hacker lấy được Access Key và gọi API từ Nga.

GuardDuty sẽ tạo finding:

> UnauthorizedAccess:IAMUser/ConsoleLogin

hoặc

> CredentialAccess:IAMUser/AnomalousBehavior

---

### Case 2: EC2 bị đào coin

EC2 đột nhiên:

* Kết nối tới mining pool
* CPU tăng đột biến

GuardDuty có thể phát hiện:

> CryptoCurrency:EC2/BitcoinTool.B!DNS

---

### Case 3: EC2 kết nối tới IP độc hại

EC2 gửi traffic tới IP nằm trong danh sách threat intelligence.

GuardDuty sinh finding:

> Backdoor:EC2/C&CActivity.B!DNS

---

### Case 4: S3 bị truy cập bất thường

Một IAM User chưa từng đọc bucket nhạy cảm nhưng đột nhiên download hàng loạt object.

GuardDuty phát hiện:

> Discovery:S3/AnomalousBehavior

---

## GuardDuty khác CloudTrail thế nào?

| CloudTrail                | GuardDuty                       |
| ------------------------- | ------------------------------- |
| Ghi log                   | Phân tích log                   |
| Cho biết chuyện gì xảy ra | Cho biết có đáng nghi hay không |
| Không có AI/ML            | Có ML và threat intelligence    |
| Người dùng tự điều tra    | Tự sinh cảnh báo                |

Ví dụ:

CloudTrail:

```json
{
  "eventName": "DeleteBucket"
}
```

GuardDuty:

```text
Potential account compromise detected
Severity: High
```

---

## GuardDuty khác AWS Config thế nào?

| AWS Config                 | GuardDuty                         |
| -------------------------- | --------------------------------- |
| Kiểm tra compliance        | Kiểm tra security threat          |
| S3 có bật encryption không | Có ai đang đánh cắp dữ liệu không |
| Security posture           | Threat detection                  |

---

## GuardDuty khác AWS Security Hub thế nào?

| GuardDuty          | Security Hub         |
| ------------------ | -------------------- |
| Sinh finding       | Tổng hợp finding     |
| Threat detection   | Dashboard trung tâm  |
| Một nguồn cảnh báo | Nhiều nguồn cảnh báo |

Thông thường:

```text
GuardDuty
    ↓
Security Hub
    ↓
SNS / Slack / Jira
```

---

## GuardDuty khác AWS Shield thế nào?

| GuardDuty           | Shield          |
| ------------------- | --------------- |
| Phát hiện tấn công  | Chống DDoS      |
| IAM compromise      | Network flood   |
| Malware             | SYN flood       |
| Threat intelligence | DDoS mitigation |

GuardDuty tập trung vào **"đã có kẻ xâm nhập chưa?"**

Shield tập trung vào **"có ai đang flood hệ thống không?"**

---

## Một kiến trúc doanh nghiệp thường gặp

```text
CloudTrail
VPC Flow Logs
DNS Logs
EKS Audit Logs
        ↓
    GuardDuty
        ↓
   Security Hub
        ↓
 EventBridge
        ↓
 SNS / Slack / Jira
```

Khi GuardDuty phát hiện sự cố:

1. Tạo Finding.
2. Đẩy vào Security Hub.
3. EventBridge bắt sự kiện.
4. Lambda tự động:

   * Disable IAM User
   * Isolate EC2
   * Tạo Jira Ticket
   * Gửi Slack Alert

Đây là mô hình SOC/SecOps rất phổ biến trên AWS.

### Chi phí

GuardDuty **không có phí cố định**. Bạn trả tiền theo:

* Số lượng CloudTrail events được phân tích.
* Lượng VPC Flow Logs.
* DNS logs.
* Runtime Monitoring.
* Malware Scan.

Với hệ thống production, GuardDuty thường là một trong những dịch vụ bảo mật có **chi phí khá hợp lý so với giá trị mang lại**, vì không cần tự xây dựng hệ thống SIEM hay threat detection.


---
Hình này mô tả **AWS Security Hub** như một trung tâm SOC (Security Operations Center) của AWS.

Thay vì vào từng service bảo mật để xem cảnh báo, Security Hub sẽ gom tất cả findings từ nhiều dịch vụ về một nơi.

```text
GuardDuty      -> phát hiện tấn công
Inspector      -> phát hiện lỗ hổng
Macie          -> phát hiện dữ liệu nhạy cảm
Config         -> phát hiện cấu hình sai
IAM Analyzer   -> phát hiện quyền public
Firewall Mgr   -> quản lý firewall
Health         -> sự cố AWS
Systems Manager-> compliance EC2
          ↓
      Security Hub
          ↓
     Findings Dashboard
```

---

# 1. Macie

Dịch vụ bảo vệ dữ liệu nhạy cảm trong S3.

Macie dùng ML để tìm:

* Thẻ tín dụng
* CMND/CCCD
* Số điện thoại
* Email
* API Key
* Password

Ví dụ:

```text
s3://customer-data/

customer.csv

name,email,credit_card
```

Macie phát hiện:

```text
Sensitive Data Found
Severity: High
```

### Dùng khi nào?

* Fintech
* Ngân hàng
* Healthcare
* SaaS chứa thông tin khách hàng

---

# 2. GuardDuty

Threat Detection Service.

Tự động phân tích:

* CloudTrail
* DNS Logs
* VPC Flow Logs
* EKS Logs

để phát hiện:

* Account bị hack
* EC2 bị malware
* Crypto mining
* Kết nối IP độc hại

Ví dụ:

```text
EC2 -> Russian IP
```

GuardDuty:

```text
Backdoor Detected
Severity: High
```

---

# 3. Inspector

Vulnerability Scanner.

Quét:

* EC2
* ECR Images
* Lambda

Tìm:

* CVE
* Package lỗi thời
* OpenSSL lỗi
* Log4j

Ví dụ:

```text
Ubuntu Server

OpenSSL 1.0
```

Inspector:

```text
CVE-2023-XXXX
Critical
```

---

# 4. AWS Config

Configuration Compliance.

Theo dõi toàn bộ thay đổi tài nguyên AWS.

Ví dụ:

```text
Security Group
```

Ban đầu:

```text
22 -> Internal Only
```

Ai đó đổi:

```text
22 -> 0.0.0.0/0
```

Config ghi lại:

```text
Who
When
What changed
```

---

### Config Rules

Có thể tạo rule:

```text
S3 phải bật encryption
```

hoặc

```text
RDS không được public
```

Vi phạm:

```text
NON_COMPLIANT
```

---

# 5. Firewall Manager

Quản lý firewall tập trung cho nhiều account.

Rất hữu ích khi dùng:

[AWS Organizations](https://aws.amazon.com/organizations/?utm_source=chatgpt.com)

Ví dụ:

```text
100 AWS Accounts
```

Muốn tất cả đều có:

* WAF
* Shield
* Security Groups chuẩn

Thay vì cấu hình từng account:

```text
Firewall Manager
      ↓
Deploy toàn bộ
```

---

# 6. IAM Access Analyzer

Phân tích IAM Policy.

Tìm:

* Public Access
* Cross Account Access
* Overly Permissive Policy

Ví dụ:

```json
{
  "Principal": "*"
}
```

Analyzer:

```text
Publicly Accessible
```

---

### Một ví dụ phổ biến

Bucket:

```text
customer-data
```

Policy:

```json
{
  "Principal": "*"
}
```

IAM Access Analyzer:

```text
External Access Found
```

---

# 7. Systems Manager (SSM)

Quản lý máy chủ tập trung.

Có thể:

### Run Command

```text
Chạy command trên 1000 EC2
```

Ví dụ:

```bash
sudo yum update
```

---

### Patch Manager

Tự vá lỗi OS.

Ví dụ:

```text
Windows Update
Ubuntu Security Update
```

---

### Session Manager

SSH vào EC2 mà không cần:

```text
SSH Key
Bastion Host
```

---

### Compliance

Kiểm tra:

```text
Máy nào chưa vá
Máy nào sai cấu hình
```

Kết quả đẩy vào Security Hub.

---

# 8. AWS Health

Theo dõi sự cố của AWS.

Ví dụ:

```text
RDS us-east-1 degraded
```

hoặc

```text
EC2 maintenance scheduled
```

Health báo:

```text
Resource impacted
```

---

# Security Hub Findings là gì?

Mỗi service gửi cảnh báo (Finding) về Security Hub.

Ví dụ:

### GuardDuty

```text
Crypto Mining
High
```

### Inspector

```text
Critical CVE
Critical
```

### Config

```text
S3 Public
Medium
```

Security Hub gom lại:

```text
Critical: 1
High: 3
Medium: 7
```

---

# Security Hub trong môi trường Enterprise

Thông thường kiến trúc sẽ là:

```text
Multi Account AWS

Account A
Account B
Account C
Account D

      ↓

GuardDuty
Inspector
Macie
Config
IAM Analyzer

      ↓

Security Hub

      ↓

EventBridge

      ↓

Lambda

      ↓

Slack / Jira / Email
```

Ví dụ:

```text
Inspector phát hiện CVE Critical
```

↓

```text
Security Hub Finding
```

↓

```text
EventBridge Rule
```

↓

```text
Tạo Jira Ticket
```

hoặc:

```text
Gửi Slack Alert
```

---

Nếu đi theo hướng **AWS Solution Architect hoặc DevSecOps**, bộ service này thường được hiểu theo nhóm:

| Service             | Chức năng                               |
| ------------------- | --------------------------------------- |
| GuardDuty           | Phát hiện tấn công (Threat Detection)   |
| Inspector           | Quét lỗ hổng (Vulnerability Management) |
| Macie               | Bảo vệ dữ liệu nhạy cảm (Data Security) |
| Config              | Compliance & Audit                      |
| IAM Access Analyzer | Kiểm tra quyền truy cập                 |
| Firewall Manager    | Quản lý Firewall tập trung              |
| Systems Manager     | Quản lý & vá máy chủ                    |
| Health              | Theo dõi sự cố AWS                      |
| Security Hub        | Trung tâm SOC gom toàn bộ findings      |

Đây chính là "bộ bảo mật chuẩn" mà rất nhiều doanh nghiệp AWS Enterprise triển khai.



---
CloudTrail can has 3 types of events ………………, ………………, and ………………
Management Event
Data Events
Cloudtrail Insight

---
KMS keys are region-specific

The choice "Use CloudHSM" is incorrect because CloudHSM is primarily designed for applications that require hardware security modules (HSMs) to manage cryptographic keys in a highly secure environment. While it can be used for key management, it does not directly provide the multi-region functionality that is needed for a Global DynamoDB table


Amazon GuardDuty phân tích các nguồn dữ liệu sau, NGOẠI TRỪ:

✅ GuardDuty phân tích:
```
AWS CloudTrail Management Events
AWS CloudTrail S3 Data Events
VPC Flow Logs
DNS Logs
EKS Audit Logs (nếu bật)
Runtime Monitoring (EC2, ECS, EKS nếu bật)
```
❌ AWS Config không phải là nguồn dữ liệu mà GuardDuty phân tích.








