import boto3

# Initialize the S3 client using environment credentials
s3 = boto3.client('s3')


def upload_to_s3(file, bucket, region, access_key=None, secret_key=None):
    """
    Uploads an image file to the configured AWS S3 bucket and returns the public URL.

    Args:
        file (FileStorage): The uploaded image file from the request.

    Returns:
        str: Publicly accessible S3 URL of the uploaded image.

    Raises:
        RuntimeError: If AWS credentials are missing or the upload fails.
    """
    import uuid

    import boto3
    from werkzeug.utils import secure_filename

    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region
    ) if access_key and secret_key else boto3.Session()

    s3 = session.client('s3')

    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    key = f"fruit-images/{unique_filename}"  # <--- use your prefix here

    s3.upload_fileobj(file, bucket, key, ExtraArgs={"ACL": "public-read"})
    return f"https://{bucket}.s3.{region}.amazonaws.com/{key}"
