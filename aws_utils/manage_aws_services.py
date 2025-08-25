import json
import os
import time

import boto3
import paramiko


# =====================================================
# Helper Functions
# =====================================================
def load_json_config(file_path="aws_config.json"):
    with open(file_path, "r") as file:
        return json.load(file)


def ssh_into_instance(ip, user, key_path):
    print(f"Attempting SSH into {ip} as {user}...")
    key_path = os.path.expanduser(key_path)
    k = paramiko.RSAKey.from_private_key_file(key_path)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(hostname=ip, username=user, pkey=k)
        stdin, stdout, stderr = ssh.exec_command(
            "echo 'Connected via SSH!' && uname -a"
        )
        print(stdout.read().decode())
        ssh.close()
    except Exception as e:
        print(f"SSH connection failed: {e}")


# =====================================================
# S3 Bucket Management
# =====================================================
def check_and_create_s3_bucket(s3_client, bucket_name, region):
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"✅ S3 bucket '{bucket_name}' already exists.")
    except s3_client.exceptions.ClientError:
        region = boto3.session.Session().region_name
        s3_client.create_bucket(
            Bucket=bucket_name, CreateBucketConfiguration={"LocationConstraint": region}
        )
        print(f"✅ Created S3 bucket: {bucket_name}")


# =====================================================
# AWS EC2 Instance Management
# =====================================================
def check_and_create_ec2_instance(ec2_client, ec2_resource, config):
    """
    Check if an EC2 instance with the specified name exists.
    If it exists, SSH into it. If it doesn't exist, create a new instance.
    If the instance is stopped, start it and SSH into it.

    Arguments:
    ec2_client -- Boto3 EC2 client
    ec2_resource -- Boto3 EC2 resource
    config -- Dictionary containing instance configuration

    Returns:
    None
    """

    name = config["name"]
    instances = ec2_client.describe_instances(
        Filters=[{"Name": "tag:Name", "Values": [name]}]
    )
    instance = None
    for reservation in instances["Reservations"]:
        for i in reservation["Instances"]:
            if i["State"]["Name"] in ["pending", "running", "stopped"]:
                instance = i
                break

    if instance:
        instance_id = instance["InstanceId"]
        ip = instance.get("PublicIpAddress")
        print(f"Found EC2 instance {name} ({instance_id})")

        if instance["State"]["Name"] != "running":
            ec2_client.start_instances(InstanceIds=[instance_id])
            ec2_client.get_waiter("instance_running").wait(InstanceIds=[instance_id])
            ip = ec2_client.describe_instances(InstanceIds=[instance_id])[
                "Reservations"
            ][0]["Instances"][0]["PublicIpAddress"]

        ssh_into_instance(ip, config["ssh_user"], config["ssh_key_path"])
    else:
        print(f"Creating new EC2 instance: {name}")
        new_instance = ec2_resource.create_instances(
            ImageId=config["ami_id"],
            InstanceType=config["instance_type"],
            KeyName=config["key_name"],
            MaxCount=1,
            MinCount=1,
            NetworkInterfaces=[
                {
                    "SubnetId": config["subnet_id"],
                    "DeviceIndex": 0,
                    "AssociatePublicIpAddress": True,
                    "Groups": config["security_group_ids"],
                }
            ],
            TagSpecifications=[
                {
                    "ResourceType": "instance",
                    "Tags": [{"Key": "Name", "Value": config["name"]}],
                }
            ],
        )[0]
        new_instance.wait_until_running()
        new_instance.reload()
        ssh_into_instance(
            new_instance.public_ip_address, config["ssh_user"], config["ssh_key_path"]
        )


# =====================================================
# AWS Secrets Management
# =====================================================
def check_and_create_secrets(secrets_client, secret_name, secret_value):
    """
    Check if a secret with the specified name exists in AWS Secrets Manager.
    If it exists, update the secret. If it doesn't exist, create a new secret.

    Arguments:
    secrets_client -- Boto3 Secrets Manager client
    secret_name -- Name of the secret to check/create
    secret_value -- Dictionary containing the secret values

    Returns:
    None
    """
    try:
        secrets_client.create_secret(
            Name=secret_name, SecretString=json.dumps(secret_value)
        )
        print("✅ Secret created.")
    except secrets_client.exceptions.ResourceExistsException:
        print("⚠️ Secret exists. Updating...")
        secrets_client.put_secret_value(
            SecretId=secret_name, SecretString=json.dumps(secret_value)
        )
        print("✅ Secret updated.")


# =====================================================
# RDS Management
# =====================================================
def check_and_create_rds_instance(rds_client, config):
    """
    Check if an RDS instance with the specified identifier exists.
    If it exists, print a message. If it doesn't exist, create a new RDS instance.

    Arguments:
    rds_client -- Boto3 RDS client
    config -- Dictionary containing RDS configuration

    Returns:
    None
    """
    db_id = config["db_identifier"]
    try:
        rds_client.describe_db_instances(DBInstanceIdentifier=db_id)
        print(f"✅ RDS instance '{db_id}' already exists.")
    except rds_client.exceptions.DBInstanceNotFoundFault:
        print(f"🚀 Creating RDS instance: {db_id}")
        rds_client.create_db_instance(
            DBInstanceIdentifier=db_id,
            AllocatedStorage=config["allocated_storage"],
            DBInstanceClass=config["db_instance_class"],
            Engine=config["engine"],
            MasterUsername=config["master_username"],
            MasterUserPassword=config["master_user_password"],
            DBName=config["db_name"],
            PubliclyAccessible=True,
        )
        rds_client.get_waiter("db_instance_available").wait(DBInstanceIdentifier=db_id)
        print("✅ RDS instance is ready.")


# =====================================================
# Cloudwatch Logs Management
# =====================================================
def check_and_create_cloudwatch_log_group(cloudwatch_client, log_group_name):
    """
    Check if a CloudWatch log group exists. If it doesn't exist, create it.

    Arguments:
    cloudwatch_client -- Boto3 CloudWatch client
    log_group_name -- Name of the log group to check/create

    Returns:
    None
    """
    try:
        cloudwatch_client.create_log_group(LogGroupName=log_group_name)
        print(f"✅ Created CloudWatch log group: {log_group_name}")
    except cloudwatch_client.exceptions.ResourceAlreadyExistsException:
        print(f"⚠️ CloudWatch log group '{log_group_name}' already exists.")
