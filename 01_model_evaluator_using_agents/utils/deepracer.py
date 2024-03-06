# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import time
from urllib.parse import urlparse

import requests
import s3
from boto3.session import Session
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest


def deepracer(
    method_name, params, region="us-east-1", credentials=Session().get_credentials()
):
    """
    Call the Deepracer service API.

    Args:
        method_name (string): The name of the method to call.
        params (dict): The parameters to pass to the method.
        region (string): The region to call the Deepracer API in.
        credentials (boto3.credentials.Credentials): The credentials to use to authenticate with the Deepracer API.

    Returns:
        dict: The response from the Deepracer API.

    Example:
        >>> deepracer('ListModels', {'MaxResults': 100, 'ModelType': 'REINFORCEMENT_LEARNING'})
    """

    endpoint = f"https://deepracer-prod.{region}.amazonaws.com/"

    headers = {
        "content-type": "application/x-amz-json-1.1",
        "x-amz-target": f"AwsSilverstoneCloudService.{method_name}",
        "host": urlparse(endpoint).hostname,
    }

    data = json.dumps(params)
    request = AWSRequest(method="POST", url=endpoint, data=data, headers=headers)

    sigv4 = SigV4Auth(credentials, "deepracer", region)
    sigv4.add_auth(request)

    prepped = request.prepare()

    response = requests.post(prepped.url, headers=prepped.headers, data=data)

    return response.json()


def list_models(max_results=100) -> list:
    """
    Lists the models in the Deepracer account.

    Args:
        max_results (int): The maximum number of models to return.

    Returns:
        list: A list of models.

    Example:
        >>> list_models()
        [{'ModelArn': 'arn:aws:deepracer:us-east-1:123456789012:model/my-model', 'ModelName': 'my-model'}]
    """
    response = deepracer(
        "ListModels",
        {
            "MaxResults": max_results,
            "ModelType": "REINFORCEMENT_LEARNING",
        },
    )

    return response["Models"]


def get_model_arn_from_model_name(model_name: str) -> str:
    """
    Returns the model with the specified name.

    Args:
        model_name (string): The name of the model to return.

    Returns:
        string: model ARN

    Example:
        >>> def get_model_arn_from_model_name(model_name)
    """
    models = list_models()
    for model in models:
        if model["ModelName"].strip() == model_name.strip():
            return model["ModelArn"]

    raise FileNotFoundError(f"could not find model file with name {model_name}")


def copy_model_to_s3(model_name, target_s3_bucket, role_arn):
    """
    Returns the URL of the model artifact.

    Args:
        model_arn (string): The ARN of the model.

    Returns:
        string: The URL of the model artifact.

    Example:
        >>> get_model_url('arn:aws:deepracer:us-east-1:123456789012:model/my-model')
        's3://my-bucket/my-model/artifacts'
    """

    model_arn = get_model_arn_from_model_name(model_name)

    current_utc_timestamp = int(time.time())
    model_s3_prefix = f"{model_name}/{current_utc_timestamp}"
    response = deepracer(
        "GetAssetUrl",
        {
            "Arn": model_arn,
            "AssetType": "S3_PKG_MODEL_LOGS",
            "ModelArtifactsS3Bucket": target_s3_bucket,
            "ModelArtifactsS3Prefix": model_s3_prefix,
            "RoleArn": role_arn,
        },
    )

    wait_for_model_status(model_arn, "READY", 300)

    return model_s3_prefix


def copy_model_to_s3_if_model_does_not_exist(model_name, target_s3_bucket, role_arn):
    model_folders = s3.list_sub_folders(target_s3_bucket, f"{model_name}")
    for model_folder in model_folders:
        if model_name in model_folder:
            export_folders = s3.list_sub_folders(target_s3_bucket, model_folder)

            # Get latest download based on when the export was done
            newest_timestamp = 0
            for export_folder in export_folders:
                export_timestamp = export_folder.split("/")[-2]
                if int(export_timestamp) > int(newest_timestamp):
                    newest_timestamp = export_timestamp
            return f"{model_folder}{newest_timestamp}"

    return copy_model_to_s3(model_name, target_s3_bucket, role_arn)


def get_track_name_and_description_from_arn(track_arn):
    """
    Returns the name and description of a track.

    Args:
        track_arn (string): The ARN of the track.

    Returns:
        dict: The name and description of the track.

    Example:
        >>> get_track_name_and_description_from_arn('arn:aws:deepracer:us-east-1:123456789012:track/my-track')
        {'Name': 'my-track', 'Description': 'My Track', 'Difficulty': 'MEDIUM', 'DifficultyRange': '100>x>1'}
    """
    response = deepracer(
        "GetTrack",
        {"TrackArn": track_arn},
    )
    if "Track" in response:
        track = response["Track"]

        return {
            key: track[key]
            for key in track.keys()
            & {
                "TrackName",
                "TrackDescription",
                "TrackDifficulty",
            }
        }

    return "unknown"


def list_tracks(max_results=100):
    """
    Lists the tracks in the Deepracer account.

    Args:
        max_results (int): The maximum number of tracks to return.

    Returns:
        list: A list of tracks.

    Example:
        >>> list_tracks()
        [{'TrackArn': 'arn:aws:deepracer:us-east-1:123456789012:track/my-track', 'TrackName': 'my-track'}]
    """
    return deepracer(
        "ListTracks",
        {
            "MaxResults": max_results,
        },
    )


def list_leaderboards(max_results, next_token=None):
    """
    Lists the leaderboards in the Deepracer account.

    Args:
        max_results (int): The maximum number of leaderboards to return.
        next_token (string): The token to use for the next page of results.

    Returns:
        list: A list of leaderboards.

    Example:
        >>> list_leaderboards(100)
        [{'LeaderboardArn': 'arn:aws:deepracer:us-east-1:123456789012:leaderboard/my-leaderboard', 'LeaderboardName': 'my-leaderboard'}]
    """
    params = {
        "MaxResults": max_results,
        "LeagueType": "VIRTUAL",
        "LeaderboardAccessRoles": ["ADMIN", "PARTICIPANT", "MODERATOR"],
    }

    if next_token != None:
        params["NextToken"] = next_token

    return deepracer("ListLeaderboards", params)


def list_leaderboard_submissions(leaderboard_arn):
    """
    Lists the submissions for a leaderboard.

    Args:
        leaderboard_arn (string): The ARN of the leaderboard.

    Returns:
        list: A list of submissions.

    Example:
        >>> list_leaderboard_submissions('arn:aws:deepracer:us-east-1:123456789012:leaderboard/my-leaderboard')

    """
    return deepracer(
        "ListLeaderboardSubmissions",
        {"LeaderboardArn": leaderboard_arn},
    )


def list_private_leaderboard_participants(leaderboard_arn, max_results=100):
    """
    Lists the participants in a private leaderboard.

    Args:
        leaderboard_arn (string): The ARN of the leaderboard.
        max_results (int): The maximum number of participants to return.

    Returns:
        list: A list of participants.

    Example:
        >>> list_private_leaderboard_participants('arn:aws:deepracer:us-east-1:123456789012:leaderboard/my-leaderboard', 100)
        [{'UserId': '123456789012', 'UserName': 'John Doe', 'UserEmail': 'XXXXXXXXXXXXXXXXXXXX'}]

    """
    return deepracer(
        "ListPrivateLeaderboardParticipants",
        {
            "MaxResults": max_results,
            "LeaderboardArn": leaderboard_arn,
            "LeaderboardAccessRoles": ["ADMIN", "PARTICIPANT"],
            "IncludeExtendedUserData": True,
        },
    )


def get_model_status(model_arn):
    """
    Returns the status of a model.

    Args:
        model_arn (string): The ARN of the model to get the status for.

    Returns:
        string: The status of the model. READY/CREATED/STOPPING/TRAINING/...

    Example:
        >>> get_model_status('arn:aws:deepracer:us-east-1:123456789012:model:my-model')
        'READY'
        >>> get_model_status('arn:aws:deepracer:us-east-1:123456789012:model:my-model')
        'TRAINING'
        >>> get_model_status('arn:aws:deepracer:us-east-1:123456789012:model:my-model')
        'CREATED'
        >>> get_model_status('arn:aws:deepracer:us-east-1:123456789012:model:my-model')
        'STOPPING'
    """

    response = deepracer("GetModel", {"ModelArn": model_arn})
    return response["Model"]["Status"]


def wait_for_model_status(model_arn, wanted_status, max_wait_time_s):
    """
    Waits for a model to reach a certain status.

    Args:
        model_arn (string): The ARN of the model to wait for.
        wanted_status (string): The status to wait for.
        max_wait_time_s (int): The maximum time to wait in seconds for the wanted_status.

    Returns:
        string: The status of the model. READY/CREATED/STOPPING/TRAINING/...

    Example:
        >>> wait_for_model_status('arn:aws:deepracer:us-east-1:123456789012:model:my-model', 'READY', 590)
        'READY'
        >>> wait_for_model_status('arn:aws:deepracer:us-east-1:123456789012:model:my-model', 'TRAINING', 590)
        'TRAINING'
        >>> wait_for_model_status('arn:aws:deepracer:us-east-1:123456789012:model:my-model', 'CREATED', 590)
        'CREATED'
    """
    status = get_model_status(model_arn)
    start_time = time.time()
    elapsed_time = 0

    while (wanted_status != status) and (max_wait_time_s > elapsed_time):
        time.sleep(10)
        status = get_model_status(model_arn)
        elapsed_time = time.time() - start_time
        print(
            f"Waiting for status: {wanted_status}, current status: {status}, elapsed time: {elapsed_time}, max wait time: {max_wait_time_s}"
        )

    return status
