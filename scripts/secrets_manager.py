import json

import boto3


def create_secret():
    secret_name = "fruitstore/db_credentials"
    region_name = "us-east-1"

    secret_value = {
        "DB_USER": "fruituser",
        "DB_PASS": "SuperSecurePass123",
        "DB_HOST": "fruitstore-cluster.cluster-c69cq4mcm794.us-east-1.rds.amazonaws.com",
        "DB_NAME": "fruitstore",
    }

    client = boto3.client("secretsmanager", region_name=region_name)

    try:
        client.create_secret(Name=secret_name, SecretString=json.dumps(secret_value))
        print("✅ Secret created.")
    except client.exceptions.ResourceExistsException:
        print("⚠️ Secret exists. Updating...")
        client.put_secret_value(
            SecretId=secret_name, SecretString=json.dumps(secret_value)
        )
        print("✅ Secret updated.")


create_secret()
