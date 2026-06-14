Cách để connect vào on-premise AD
- Thông qua aws managed microsoft AD
- phải có 1 direct connection (DX) hoặc là vpn connection
- Setup 3 dạng forest trust:
    - One-way trust: AWS -> On-premise
    - One-way trust: On-premise -> AWS
    - Two-way trust: AWS <-> on-premise

---

Solution Architecture: Active Directory Replication

- You may want to create a "replica of your AD on EC2" in the cloud to minimize latency of in case DX or VPN goes down
- Establish trust bw AWS Manage Microsoft AD and EC2

---
AD connector

is a proxy to redirect req to your AD, no caching capability -> only proxy 

---
Simple AD 

Support joining EC2, manage users and group
Not support MFA, RDS SQL servers, AWS SSO
User 500-5000
Powered by Samba 4, comp. with microsoft AD
lower cost, low scale, basic AD compatible or LDAP compatibility
No trust relationship

---
AWS Organization
Root Organization Unit (OU)
```
Manage Accout 
    OU Dev
        Member accounts
    OU Prod
        Member account
        OU HR

```

`OrganizationAccountAccessRole`
- Automatically create on member account with aws organization, but manually created if you invite an existing member account
- Grant full permission in member account to administrator manange account
- Use to perform admin task in the member account (eg. create IAM user)

---

Muti account strategies 
One account per dev/test/prod,...org
Use taging 
Enable cloudtrail
Send cloudwatch log to central loging account

---

AWS organization features
Consolidate billing feature cross all account - single payment

---

Service Control Policy (SCP)

define allow list, block list for IAM actions
applied at OU or Account level
not apply to management account
applied to all Users and Roles in the account, include Root user 
not affect the service-linked roles

----

AWS Identiy Center (successor to aws sigle sign-on)
- one login for all your :
    - aws account in aws ou
    - bussiness cloud applications
    - SAML2.0-enabled apps
    - ec2 windown instances

----

AWS Control Tower 
- Easy way to setup and govern a secure and compliant multi-account AWS environment based on best practices.

- Account factory
    - Automates account provisioning and deployment

- Guardrails level
    - mandatory
    - strongly recommended
    - elective 

---

AWS Resource Access Manager (RAM)
- chia sẻ (share) tài nguyên AWS giữa nhiều AWS Account hoặc nhiều Organization Account mà không cần copy hoặc tạo lại tài nguyên đó

- share aws resources that you own with other aws account 
- share with any account or with your org
- avoid resource duplicatiop
- VPC Subnet 
    - allow to have all the resource launch in the same subnet
    - must be from the same aws org
    - can't share default security group and defaul vpc
    - participant can manage their own resources in there
    - participant can't view, mod, del resources that belong to other participant or the owner.
- Transit gateway 
- Route 53 (Resolver Rule, DNS Firewall Rule Group)
- License manager configuration
- Aurora DB cluster 
- ACM Private Certification Authority
- Code build project
- EC2 
- AWS Glue (Catalog, Database, Table)
- AWS Netword firewall policies
- AWS Resource group
- System manager incident manager (contact, response Plans)
- AWS Outposts (Outpost, Site)



- Managed Prefix List:
    - a set of one or more CIDR blocks
    - make it easier to configure and mantain SG and route table
    - customer-managed prefix list
        - set of CIDR that you define 
        - can share with other aws account and aws org
        - update many SG at once
    - aws managed prefix list
        - set of CIDR for aws service
        - cant create/update/del/share

- Route 53 Outbound resolver
    - help to scale forwarding rules to your dns in case you have multiple accounts and VPC  



---



































---

