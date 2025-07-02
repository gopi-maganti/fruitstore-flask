import os
import uuid
from typing import str

import boto3
from botocore.exceptions import NoCredentialsError
from werkzeug.datastructures import FileStorage

# Initialize the S3 client using environment credentials
s3 = boto3.client('s3')
BUCKET_NAME = os.getenv('S3_BUCKET_NAME')


def upload_image_to_s3(file: FileStorage) -> str:
    """
    Uploads an image file to the configured AWS S3 bucket and returns the public URL.

    Args:
        file (FileStorage): The uploaded image file from the request.

    Returns:
        str: Publicly accessible S3 URL of the uploaded image.

    Raises:
        RuntimeError: If AWS credentials are missing or the upload fails.
    """
    try:
        from werkzeug.utils import secure_filename

        filename: str = secure_filename(file.filename)
        unique_name: str = f"{uuid.uuid4().hex}_{filename}"

        s3.upload_fileobj(
            file,
            BUCKET_NAME,
            unique_name,
            ExtraArgs={
                'ACL': 'public-read',
                'ContentType': file.content_type
            }
        )

        image_url: str = f"https://{BUCKET_NAME}.s3.amazonaws.com/{unique_name}"
        return image_url

    except NoCredentialsError:
        raise RuntimeError("AWS credentials not found.")
    except Exception as e:
        raise RuntimeError(f"S3 Upload Failed: {str(e)}")
