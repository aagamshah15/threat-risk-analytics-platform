import io
import boto3
from botocore.client import Config

def s3_client(endpoint: str, access_key: str, secret_key: str):
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )

def put_bytes(client, bucket: str, key: str, data: bytes, content_type: str):
    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=io.BytesIO(data),
        ContentType=content_type
    )

