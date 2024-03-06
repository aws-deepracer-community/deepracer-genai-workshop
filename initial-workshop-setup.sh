#!/bin/bash

set -xa

if [$1 == ""]; then
  echo "Please provide bucket name and re-run the script in the format ./initial-workshop-setup.sh bucket_name"
  exit
fi

BUCKET_NAME=$1
shift

aws s3 mb s3://${BUCKET_NAME} --region us-east-1
aws s3 cp source s3://${BUCKET_NAME}/custom_resources --exclude "*.yaml" --recursive
aws cloudformation deploy --stack-name sgdomainanduser --parameter-overrides MyAssetsBucketName=$BUCKET_NAME MyAssetsBucketPrefix="" --template-file source/SGDomainAndUserOwnAccount.yaml --capabilities CAPABILITY_IAM --region us-east-1
echo "Pre-requisites are complete, you can now continue with the workshop"
