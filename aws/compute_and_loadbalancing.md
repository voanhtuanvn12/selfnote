
EC2 instance

- R: application need alot of RAM
- C: need good CPU
- M: balance (think "medium")
- I: need good local I/O (instance storage / databases)
- G: need alot of GPU (machine learning/video rendering,..)

- t2/t3: burstable instances (up to a capacity)
- t2/t3 - unlimited: unlimited burst

ec2instances.info
---

EC2 - placement groups

- Control the EC2 instance placement strategy using placement group
- group strategies:
    - cluster: cluster instance in a low-latency group in a single AZ
        - very fast, low latency 
        - if rack fail, then all fail
        - note: choose instance type has **Enhanced Networking**
        - use case:
            - big data job
            - low latency apps, high network throuhput
    - spread: spreads instance accross underlying hardware (max 7 instances/group/AZ ) - idea for critical applications - do not have a hardware failure
        - can span accros multi AZ
        - reduced risk or simultaneous failure
        - ec2 instance are on different hardware
        - but limited 7 instances/group/AZ
        - use case:
            - app with high availibility
    - partitions: spread instance across many different partition within an AZ . Scales upto 100s of EC2 instance per group (Hadoop, Cassandra, Kafka)
        - up to 7 partition per AZ
        - up to 100s of EC2 instance
        - a partition do not share rack (different hardware)
        - the partition failure will effect instance on that partition, but not for others
        - use case:
            - HDFS, cassandra, Hbase, Kafka
- you can move a instance into or out a placement group
    - need to stop instance first
    - use cli modify-instance-placement
    - then start instance

---

Instance Launch Type
- On demand 
- Spot instance
- Reserved (min 1year):
    - reserved instances: long workload
    - convertible reserved instances: long workload with flexible instances
    - highest to lower discount:  all upfront payment, partial upfront payment, no Update
- Dedicated Instance: no other customer 
- Dedicated Host: Book an entire physical server, control instance placement

---

EC2 Graviton

là các máy chủ ảo (EC2) sử dụng bộ vi xử lý dựa trên kiến trúc ARM tự thiết kế bởi AWS. Chúng được thiết kế để mang lại hiệu suất cao với chi phí thấp hơn (giảm tới 20% - 40% chi phí/hiệu năng so với các dòng máy x86) và tiết kiệm điện năng

Support Linux OS: amazon linux 2, redhat, SUSE, ubuntu
Not support window

Graviton 2: 40% better price performance over comparable 5th generation x86 instance
Graviton 3: 3x better than graviton 2
Use case: app server, microservice, HPC, CPU-base ML, video encoding, gaming, memories cache.

---

EC2 Include metric:
- CPU: CPU Utilization + Credit Usage/ Balance
- Network: network in/out 
- Status check:
    - Instance status: ec2 vm
    - System status: physical hardware
- Disk: read/write ops/bytes
- **RAM is not included in EC2 metric**


---

EC2 instance recovery:
- Status check:
    - instance status 
    - system status

- Recovery: same private/public/elastic/ip/metadata placement

---

HPC (High performance computing)

- Data management and transfer
    - AWS Direct Connect:
        - move GB/s of data to the cloud, over a private network
    - Snowball:
        - move PB of data to the cloud
    - AWS datasync:
        - move large amount of data btw on premise and S3, EFS, FSx for window

- Compute and networking:
    - EC2 instances:
        - CPU,GPU optimized
        - Spot instances/ Spot fleets for cost saving + Auto scaling
    - EC2 placement group:
        - Cluster for good network performance (fast talk to each others, low latency, 10Gbps network)
    - EC2 Enhanced Networking: (SR-IOV)
        - Higher bandwidth, higher PPS (packet per second), lower latency
        - Option 1:
            - Elastic Network Adapter (ENA) upto 100Gbps
        - Option 2:
            - Intel 82599VF up to 10Gbps - Legacy

    - Elastic Fabric Adapter (EFA)
        - improve ENA for HCP, only for linux 

- Storage:
    - instance-attach storage:
        - EBS: scale up to 256000 IOPS with IO2 Block Express
        - Instance Store: scale to million of IOPS, linked to EC2 instance, low latency, can lose it if we lose our instance
    - Network storage:
        - S3: large blob, not a file system
        - EFS: scale IOPS based on total size, or use provisioned IOPS
        - FSx for Lustre: 
            - HPC optimized distributed file system, milions of IOPS
            - Backed by S3

    - EFS hỗ trợ Read Many / Write Many (RWX - ReadWriteMany), đây là một trong những điểm khác biệt lớn nhất so với EBS.
        - Write cùng một file thì vẫn phải xử lý: file locking, coordination, race condition. EFS không tự merge dữ liệu cho bạn.
    - EBS = ReadWriteOnce (RWO)
    - EFS = ReadWriteMany (RWX)


- Automation and Oschestration
    - AWS batch
        - support multiple node-parrallel jobs, which enables you run single jobs that can span multiple EC2 instance
        - easily schedule jobs and launch EC2 instance accordingly

    - Parallel Cluster
        - open source cluster management tool to deploy HPC on AWS
        - configured with text files
        - automate creation of VPC, Subnet, cluster type and instance types.

---

Auto Scaling Group - Dynamic Scaling Policies

- Target tracking scaling
    - Most simple and easy to setup
- Simple/Step Scaling
    - when cloudwatch alarm is triggered (example CPU > 70%), then add 2 units
    - when cloudwatch alarm is triggered (example CPU < 30%), then add remove 1
- Schedule action:
    - Anticipate a scaling base on known usage patterns
    - Example: increase the min cap to 10 at 5pm on Fri.

Auto Scaling Group - Predictive Scaling 
- Preductive scaling:
    - continuously forcast load and schedule scaling ahead

Good metric to scale 
- CPUUtilization
- RequestCountPerTarget
- Average Network In/Out
- Any custom metrics

Auto Scaling - Good to know
- Spot Fleet support 
- Lifecyle Hooks:
    - perform action:
        - before an instance is in service
        - before it is terminate
        - example: cleanup, log extraction, special health check

- To upgrade an AMI, must update the laugh configuration/template
    - then terminate instance manually (Cloudformation can help)
    - or use EC2 instance Refresh or Auto Scaling


Auto scaling - Instance refresh
- Goal: update launch template -> then re-creating all ec2
- for this we can use the native feature of Instance Refresh
- Setting minimum of healthy percent.
- Specify warmup time (how long until the instance is ready to use)
- Scaling process:
    - Launch: add new ec2
    - Terminate: remove ec2
    - Healthcheck: 
    - ReplaceUnhealthy
    - AZRebalance
    - AlarmNotification























