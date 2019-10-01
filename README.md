# SRE LS API Project


# Initial Setup

### Infrastructure - First Layer
As required, this project uses ec2 instances as base plataform to run a API service.

**Terraform  (v0.12.9)** is the tool used to provide infrastructure layer.
All terraform code is placed into *terraform* directory located on this project, and must run from _terraform/aws_ directory.
The result of running this code is a creation of a ElasticLoadBalancer, a EC2 instance and Security Group configurations.

The AWS credentials is configured as environment variables on the machine running terraform. (AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY)

General network configurations are located in **"vpc.tf"** file.

To access the ELB, we have a security group that allows all input traffic on ELB HTTP:80.

To access the API service hosted on EC2 instance, we have a security group with ELB and EC2 instance as members. The API
service is exposed on port 8000, which is consumed only by ELB. For instance access i also have created a SSH rule.

Sequence of commands to create the project infrastructre:

```
root@server: terraform init
root@server: terraform apply -auto-approve
```

After running a terraform apply script, it will give to us the DNS name of the created ELB. 
We can also run a terraform output command to get this information.
```
root@server: terraform output
elb_dnd = default-elb-1595027718.us-east-1.elb.amazonaws.com
```

To remove all resources created by terraform, run:
``
terraform destroy -auto-approve
``

### API - Second Layer

The API service is configured based on provided Swagger 2.0 file specification.
As required is based on docker running a Tornado as web server application.

To create the API service, we **must** provide a **.env** file containing 3 variables:
* AWS_ACCESS_KEY_ID=key
* AWS_SECRET_ACCESS_KEY=secret
* API_TOKEN=token

The API_TOKEN is used as requirement - http basic authentication (base64 encoded user:password).
Using the ec2 instance created using terraform, we can deploy aplication running the **builder.sh** script 
locate on _external_scripts_ directory of this project.
The default location of .env file is **/root/.env**. If you need to change, just edit the builder script.

Running the builder script will download and deploy the API using the latest code from git repository on master branch.

```
[root@ip-172-31-20-14 ~]# ./builder 
Removing API directory
Cloning into 'API'...
remote: Enumerating objects: 56, done.
remote: Counting objects: 100% (56/56), done.
remote: Compressing objects: 100% (36/36), done.
remote: Total 56 (delta 13), reused 48 (delta 10), pack-reused 0
Unpacking objects: 100% (56/56), done.
lsapi
Sending build context to Docker daemon  244.7kB
Step 1/8 : FROM python:3.7-alpine
 ---> 39fb80313465
Step 2/8 : LABEL maintainer="rodrigo@datastack.com.br"
 ---> Using cache
 ---> 1b67f3952808
Step 3/8 : WORKDIR /usr/src/app
 ---> Using cache
 ---> 9cb9ea078ad5
Step 4/8 : RUN apk update && apk add --no-cache tzdata libc-dev build-base libexecinfo-dev openblas-dev python3-dev gcc g++ freetype freetype-dev
 ---> Using cache
 ---> cce61bb9892c
Step 5/8 : RUN rm -f /etc/localtime && ln -s /usr/share/zoneinfo/America/Sao_Paulo
 ---> Using cache
 ---> af8f03926389
Step 6/8 : ONBUILD COPY . .
 ---> Using cache
 ---> 9b4da6645436
Step 7/8 : ONBUILD RUN pip install --no-cache-dir -r requirements.txt
 ---> Using cache
 ---> 8b3d003e9d8d
Step 8/8 : CMD ["python", "run.py"]
 ---> Using cache
 ---> de75ca206624
Successfully built de75ca206624
Successfully tagged lsapi:onbuild
Sending build context to Docker daemon  244.7kB
Step 1/1 : FROM lsapi:latest
 ---> 97b2ea0f04a8
Successfully built 97b2ea0f04a8
Successfully tagged lsapi:latest
af24c6ea45a094159901085f44355dc3bec82740d02415b9a70c9cacfbb84256
```

For response messages a dictionary as **_{'message': response}_** is returned, where the response value is in the
format specified by Swagger 2.0 document, used as rule to construct this API.

Here a response example:
```
curl -H "Authorization: Basic TOKEN" http://default-elb-1595027718.us-east-1.elb.amazonaws.com/elb/default-elb
{"message": [{"instanceId": "i-0592fe5ccee879f04", "instanceType": "t2.micro", "launchDate": "2019-10-01T18:54:000000Z"}]}
```
And API logs output:
```buildoutcfg
[root@ip-172-31-20-14 ~]# docker logs -f lsapi
[01/10/2019 10:55:47 PM] [    INFO] --- health checking (base.py:29)
[01/10/2019 10:55:47 PM] [    INFO] --- 200 GET /healthcheck (172.31.27.132) 1.19ms (web.py:2246)
[01/10/2019 10:55:47 PM] [    INFO] --- health checking (base.py:29)
[01/10/2019 10:55:47 PM] [    INFO] --- 200 GET /healthcheck (172.31.31.100) 0.81ms (web.py:2246)

```

For initial stress test, i was able to measure capacity using the **wrk** tool.
```
Running 30s test @ http://default-elb-1595027718.us-east-1.elb.amazonaws.com/elb/default-elb
  12 threads and 12 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     1.13s   154.44ms   1.99s    91.26%
    Req/Sec     0.04      0.19     1.00     96.13%
  310 requests in 30.05s, 140.17KB read
  Socket errors: connect 0, read 0, write 0, timeout 1
Requests/sec:     10.31
Transfer/sec:      4.66KB

```
As the ec2 instance is a micro instance, it works well for low traffic. When we increase the requests we start to have 
**SurgeQueueLengt**. Its a important metric on ELB that shows the backend is taking too long to respond and the ELB start to hold on requests.