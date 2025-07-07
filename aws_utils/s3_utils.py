import boto3
import uuid
from werkzeug.utils import secure_filename

# Default S3 client for non-authenticated environments
s3 = boto3.client("s3")

def upload_to_s3(file, bucket, region, access_key=None, secret_key=None):
    """
    Uploads an image file to AWS S3 and returns the public URL.

    Args:
        file (FileStorage): The uploaded image file.
        bucket (str): Target S3 bucket.
        region (str): AWS region.
        access_key (str, optional): AWS Access Key.
        secret_key (str, optional): AWS Secret Key.

    Returns:
        str: Public URL of the uploaded file.

    Raises:
        RuntimeError: If upload fails.
    """
    try:
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        ) if access_key and secret_key else boto3.Session(region_name=region)

        s3_client = session.client("s3")

        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        key = f"fruit-images/{unique_filename}"

        s3_client.upload_fileobj(file, bucket, key, ExtraArgs={"ACL": "public-read"})

        return f"https://{bucket}.s3.{region}.amazonaws.com/{key}"

    except Exception as e:

        raise RuntimeError(f"Upload to S3 failed: {e}")
