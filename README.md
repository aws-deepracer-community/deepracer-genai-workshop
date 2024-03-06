# deepracer-genai-workshop
Community version of [AWS GenAI Workshop](https://catalog.us-east-1.prod.workshops.aws/workshops/d8a88732-5154-49ac-9725-033c0bc74029/en-US/10-aws-account-access) updated to support [DeepRacer for Cloud](https://github.com/aws-deepracer-community/deepracer-for-cloud) / [DeepRacer on the Spot](https://github.com/aws-deepracer-community/deepracer-on-the-spot) and AWS console models.

This workshop runs in us-east-1 region only.

## Costs

This workshop should only cost $2-5 to run, as long as you follow the cleanup steps at the end.  Note - one of the LLMs used is Claude Instant, offered through the AWS Marketplace by Anthropic.  The use of Cluade Instant may not be covered by AWS credits, however in testing this element only cost $0.10.

## Pre-requisites

### Configure AWS Account, Roles and S3 via a CloudFormation script

In order to run this workshop you should have the AWS CLI installed and be [authenticated to AWS](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html)

- run `git clone https://github.com/aws-deepracer-community/deepracer-genai-workshop.git`
- run `cd deepracer-genai-workshop`
- run `./initial-workshop-setup.sh <aws_bucket_name_to_create>`

### Configure Bedrock LLM Access

- In the AWS console, search for Amazon Bedrock, and select Amazon Bedrock from the list of services.
![bedrock-locate](readme-images/bedrock-locate.png)

