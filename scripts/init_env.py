#!/usr/bin/env python3

import json
import os

import boto3


def write_env_file(
    secret_id: str = "fruitstore/db_credentials", region: str = "us-east-1"
):
    client = boto3.client("secretsmanager", region_name=region)
    secret = client.get_secret_value(SecretId=secret_id)
    secrets_dict = json.loads(secret["SecretString"])

    with open(".env", "w") as f:
        for key, value in secrets_dict.items():
            f.write(f"{key}={value}\n")


if __name__ == "__main__":
    write_env_file()
