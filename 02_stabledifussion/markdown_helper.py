# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0


def generate_s3_write_permission_for_sagemaker_role(role, iam_policy_name):
    role_name = role.split("/")[-1]
    url = "https://console.aws.amazon.com/iam/home#/roles/%s" % role_name
    text = "1. Go to IAM console to edit current SageMaker role: [%s](%s).\n" % (
        role_name,
        url,
    )
    text += "2. Next, go to the `Permissions tab` and click on `Attach Policy.` \n"
    text += "3. Search and select `{}` policy\n".format(iam_policy_name)
    return text
