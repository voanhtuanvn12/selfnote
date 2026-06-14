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
 






























