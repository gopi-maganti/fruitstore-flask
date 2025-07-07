import json

import boto3
from botocore.exceptions import ClientError


def get_db_credentials(secret_name: str, region_name: str = "us-east-1") -> dict:
    """
    Fetches database credentials stored in AWS Secrets Manager.

    Parameters
    ----------
    secret_name : str
        The name of the secret in AWS Secrets Manager.
    region_name : str, optional
        AWS region where the secret is stored.

    Returns
    -------
    dict
        A dictionary containing dbname, username, password, host, and port.
    """
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    try:
        response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise RuntimeError(f"Error retrieving secret: {e}")

    secret = response.get('SecretString')
    if not secret:
        raise RuntimeError("Secret string is empty or missing.")

    try:
        return json.loads(secret)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse secret JSON: {e}")
