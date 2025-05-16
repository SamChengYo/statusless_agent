from abc import ABC, abstractmethod
import os
import re
from dotenv import load_dotenv
import botocore

load_dotenv(override=True)

# S3
import boto3

# MinIO
from minio import Minio

class StorageOperate(ABC):
    @abstractmethod
    def upload_fileobj_return_url(self, fileobj, dest_path: str):
        pass

    @abstractmethod
    def upload_file_return_url(self, file_path: str, dest_path: str):
        pass

class S3StorageOperate(StorageOperate):
    def __init__(self, bucket_name: str):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("REGION_NAME")
        )

        # 🔥 自動修正 bucket name
        bucket_name = bucket_name.lower().replace("_", "-")
        if not re.fullmatch(r"[a-z0-9\-]{3,63}", bucket_name):
            raise ValueError(f"Invalid bucket name after normalization: '{bucket_name}'. Must be 3-63 characters with only a-z, 0-9, and '-'.")

        self.bucket_name = bucket_name

        # 🔥 確保 bucket 存在，否則創建
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except botocore.exceptions.ClientError as e:
            error_code = int(e.response['Error']['Code'])
            if error_code == 404:
                region = self.s3_client.meta.region_name
                create_cfg = {'LocationConstraint': region} if region != 'us-east-1' else {}
                self.s3_client.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration=create_cfg
                )
            else:
                raise

    def upload_fileobj_return_url(self, fileobj, dest_path: str):
        self.s3_client.upload_fileobj(
            Fileobj=fileobj,
            Bucket=self.bucket_name,
            Key=dest_path
        )
        region = self.s3_client.meta.region_name
        return f"https://{self.bucket_name}.s3.{region}.amazonaws.com/{dest_path}"

    def upload_file_return_url(self, file_path: str, dest_path: str):
        self.s3_client.upload_file(
            Filename=file_path,
            Bucket=self.bucket_name,
            Key=dest_path
        )
        region = self.s3_client.meta.region_name
        return f"https://{self.bucket_name}.s3.{region}.amazonaws.com/{dest_path}"


class MinioStorageOperate(StorageOperate):
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        secure: bool = False
    ):
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        self.bucket_name = bucket_name
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)

    def upload_fileobj_return_url(self, fileobj, dest_path: str):
        fileobj.seek(0)
        self.client.put_object(
            self.bucket_name,
            dest_path,
            data=fileobj,
            length=-1,
            part_size=10*1024*1024
        )
        scheme = 'https' if self.client._secure else 'http'
        return f"{scheme}://{self.client._endpoint_url}/{self.bucket_name}/{dest_path}"

    def upload_file_return_url(self, file_path: str, dest_path: str):
        with open(file_path, 'rb') as f:
            return self.upload_fileobj_return_url(f, dest_path)
