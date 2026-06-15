SSTable: Sorted String Table - SSTable là một trong những khái niệm quan trọng nhất của LSM Tree.

LSM-Tree được thiết kế để tối ưu write. Memtable -> Flush -> SSTable. SSTable luôn sort theo primary key 
Thực tế secondary index trên LSM-Tree không hoạt động -> DB sẽ tạo ra một hidden table 
BTree có thể tạo index trên mọi cột -> như tốc độ write sẽ chậm hơn LSM tree vì phải update rất nhiều index -> mỗi index có thể là một page

---

Imcoming write  

-> 1.1 write to memtable (RAM, fast) -> 2 Flush to SSTable (Once the memtable reaches a certain size) -> 3 Compaction (A background process called compaction periodically merges these files, removing duplicates and deleted entries)
-> 1.2 write to WAL (Disk, for durability )

---

LSM 

Negative Impact on Reads

When you query for a specific key, the database must check multiple places:

First, the memtable: Is the data in the current in-memory buffer?

Then, immutable memtables: Any memtables waiting to be flushed?

Finally, all SSTables on disk: Starting from the newest (most likely to have recent data) and working backwards

---
AWS Cloudtrail

là dịch vụ audit log của AWS, dùng để ghi lại ai đã làm gì, khi nào, từ đâu, trên tài nguyên AWS nào.

CloudWatch = hệ thống đang chạy thế nào -> mornitoring
CloudTrail = ai đã thay đổi hệ thống -> audit

---
STS 

STS (Security Token Service) là dịch vụ cấp temporary credentials (thông tin xác thực tạm thời).

---

Cách để cấp quyền access cho 3rd party aws account

- 3rd party aws account id
- an external ID (secret btw you and 3rd party) - you define it
- define permission in IAM

---

Identity Federation (IF)

Cấp quyền cho user ở ngoài aws có thể access các resource của aws

Example những khách hàng có hệ thống identity system riêng (eg, Active Directory)

Hoặc web, mobile device cần access các resource của aws.

IF thiết lập 1 trust relationship với Identity Provider, User login vào IdP và nhận được temporary credential để access vào AWS. (STSAssumeRoleWithSAML API)

Nếu là web identity federation (google, facebook, bất kì web app nào có chuẩn OpenID Connect Compatible IdP) -> STSAssumeRoleWithWebIdentity API


Nếu có AWS Cognito , thay vì dùng web identity token để call STS bằng STSAssumeRoleWithWebIdentity API
thì sau khi đăng nhập thành công và có web identity token -> dùng WIT để call qua Cognito để lấy Cognito Token -> từ đó call qua STS 
để lấy credential

Cognito support MFA,anonymous user, data synchronization.

---

AWS Directory Service -> giải quyết bài toán access vào onpremise AD từ aws

AWS Managed Microsoft AD ->
    Tạo AD ở AWS, tự tạo và manage user
    Maintain trust connection với onpremise AD
    One-way trust hoặc Two-way trust


AWS AD Connector
    Proxy LDAP/Kerberos
    AWS chuyển request xác thực về On-Prem.
    User được manage trên onpremis ad



Simple AD -> AD compatible api (Samba)
 Simple AD phù hợp cho: Small business, Test environment, Dev environment












