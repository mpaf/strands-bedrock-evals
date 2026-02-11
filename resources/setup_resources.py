#!/usr/bin/env python3
import boto3
import json

s3 = boto3.client('s3', region_name=boto3.Session().region_name)
iam = boto3.client('iam', region_name=boto3.Session().region_name)
sts = boto3.client('sts', region_name=boto3.Session().region_name)

ACCOUNT_ID = sts.get_caller_identity()['Account']
BUCKET_NAME = f"genai-evaluation-migration-bucket-{ACCOUNT_ID}"
ROLE_NAME = "BedrockEvaluationRole"

# Create S3 bucket
try:
    s3.create_bucket(
        Bucket=BUCKET_NAME,
        CreateBucketConfiguration={'LocationConstraint': boto3.Session().region_name}
    ) if boto3.Session().region_name != 'us-east-1' else s3.create_bucket(Bucket=BUCKET_NAME)
    print(f"✓ Created bucket: {BUCKET_NAME}")
except s3.exceptions.BucketAlreadyOwnedByYou:
    print(f"✓ Bucket already exists: {BUCKET_NAME}")

# Create IAM role
trust_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "bedrock.amazonaws.com"},
        "Action": "sts:AssumeRole"
    }]
}

role_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
            "Resource": [f"arn:aws:s3:::{BUCKET_NAME}/*", f"arn:aws:s3:::{BUCKET_NAME}"]
        },
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream",
                "bedrock:CreateModelInvocationJob",
                "bedrock:StopModelInvocationJob",
                "bedrock:GetProvisionedModelThroughput",
                "bedrock:GetInferenceProfile",
                "bedrock:ListInferenceProfiles",
                "bedrock:GetImportedModel",
                "bedrock:GetPromptRouter",
                "sagemaker:InvokeEndpoint"
            ],
            "Resource": [
                f"arn:aws:bedrock:*:{ACCOUNT_ID}:inference-profile/*",
                f"arn:aws:bedrock:*:{ACCOUNT_ID}:provisioned-model/*",
                f"arn:aws:bedrock:*:{ACCOUNT_ID}:imported-model/*",
                f"arn:aws:bedrock:*:{ACCOUNT_ID}:application-inference-profile/*",
                f"arn:aws:bedrock:*:{ACCOUNT_ID}:default-prompt-router/*",
                f"arn:aws:sagemaker:*:{ACCOUNT_ID}:endpoint/*",
                "arn:aws:bedrock:*::foundation-model/*",
                "arn:aws:bedrock:*::marketplace/model-endpoint/all-access"
            ]
        }
    ]
}

try:
    role = iam.create_role(
        RoleName=ROLE_NAME,
        AssumeRolePolicyDocument=json.dumps(trust_policy)
    )
    role_arn = role['Role']['Arn']
    print(f"✓ Created role: {role_arn}")
except iam.exceptions.EntityAlreadyExistsException:
    role_arn = f"arn:aws:iam::{ACCOUNT_ID}:role/{ROLE_NAME}"
    print(f"✓ Role already exists: {role_arn}")

iam.put_role_policy(
    RoleName=ROLE_NAME,
    PolicyName='BedrockS3Access',
    PolicyDocument=json.dumps(role_policy)
)
print(f"✓ Updated role policy")
