# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3

s3_client = boto3.client("s3")


def get_file_content(bucket_name, file_key):
    """
    Gets the content of a file from a S3 bucket.

    Args:
        bucket_name (string): The S3 bucket name.
        file_key (string): The S3 file key.

    Returns:
        The content of the file.
    """
    response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
    object_content = response["Body"].read().decode("utf-8")

    return object_content


def list_files(bucket, prefix=""):
    """
    Lists all files in a S3 bucket with a given prefix.

    Args:
        bucket (string): The S3 bucket name.
        prefix (string): The S3 prefix to list.

    Returns:
        A list of files.
    """
    response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
    return response["Contents"]


def list_sub_folders(bucket, prefix=""):
    """
    Lists all sub folders in a S3 bucket with a given prefix.

    Args:
        bucket (string): The S3 bucket name.
        prefix (string): The S3 prefix to list.

    Returns:
        A list of subfolders.
    """
    response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix, Delimiter="/")

    if "CommonPrefixes" in response:
        return [d["Prefix"] for d in response["CommonPrefixes"]]
    return []


def delete_s3_prefix(bucket, prefix):
    """
    Deletes all objects in a S3 bucket with a given prefix.

    Args:
        bucket (string): The S3 bucket name.
        prefix (string): The S3 prefix to delete.

    Returns:
        None.
    """
    try:
        print(f"Deleting all objects with prefix '{prefix}' in bucket '{bucket}'...")
        objects_to_delete = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        for obj in objects_to_delete.get("Contents", []):
            s3_client.delete_object(Bucket=bucket, Key=obj["Key"])
        print(
            f"All objects with prefix '{prefix}' in bucket '{bucket}' has been deleted."
        )
    except Exception as e:
        print(f"An error occurred: {e}")
