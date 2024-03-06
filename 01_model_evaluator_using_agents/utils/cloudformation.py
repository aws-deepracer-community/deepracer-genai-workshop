# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3

cloudformation_client = boto3.client("cloudformation")


def get_stack_outputs(stack_name):
    try:
        response = cloudformation_client.describe_stacks(StackName=stack_name)
        stack_outputs = response["Stacks"][0]["Outputs"]
        return_values = {}
        for output in stack_outputs:
            return_values[output["OutputKey"]] = output["OutputValue"]

        return (
            return_values["DeepRacerModelExportBucketOutput"],
            return_values["DeepRacerCopyToS3RoleArn"],
        )

    except Exception as error:
        print(error)
        if error.response["Error"]["Code"] == "ValidationError":
            raise Exception(error.response["Error"]["Message"])
        else:
            raise Exception(error)
