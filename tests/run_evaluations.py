#!/usr/bin/env python3
import boto3
import json
import uuid

bedrock = boto3.client('bedrock')
sts = boto3.client('sts')
s3 = boto3.client('s3')

ACCOUNT_ID = sts.get_caller_identity()['Account']
BUCKET_NAME = f"genai-evaluation-migration-bucket-{ACCOUNT_ID}"
ROLE_NAME = "BedrockEvaluationRole"
S3_KEY = "eval-dataset.jsonl"
REGION= boto3.Session().region_name

role_arn = f"arn:aws:iam::{ACCOUNT_ID}:role/{ROLE_NAME}"
eval_dataset_location = {"s3Uri": f"s3://{BUCKET_NAME}/{S3_KEY}"}
output_data_config = {"s3Uri": f"s3://{BUCKET_NAME}/eval-results/"}

eval_prompts_filename = 'tests/eval-dataset.jsonl'

# Upload dataset
data = [{"prompt": "Write a short poem about clouds", "referenceResponse": "Clouds are the best"}]

# create this in jsonl format
with open(eval_prompts_filename, 'w') as f:
    for item in data:
        f.write(json.dumps(item) + '\n')

s3.upload_file(eval_prompts_filename, BUCKET_NAME, S3_KEY)
print(f"✓ Uploaded dataset to s3://{BUCKET_NAME}/{S3_KEY}")

# Load inference profiles
profile_ids = []
with open('tests/inference_profile_ids.jsonl', 'r') as f:
    for line in f:
        data = json.loads(line)
        profile_ids.append(data['inference_profile_id'])

print(f"Loaded {len(profile_ids)} inference profiles\n")

results = []

for profile_id in profile_ids:
    try:
        short_id = profile_id.replace('us.', '').replace('-v1:0', '').replace('.', '-')
        job_name = f"{short_id}-{uuid.uuid4().hex[:4]}"
        
        # Determine if it's an inference profile (starts with "us.") or a model ID
        if profile_id.startswith('us.'):
            model_arn = f"arn:aws:bedrock:{REGION}:{ACCOUNT_ID}:inference-profile/{profile_id}"
        else:
            model_arn = profile_id  # Use model ID directly

        response = bedrock.create_evaluation_job(
            jobName=job_name,
            roleArn=role_arn,
            evaluationConfig={
                "automated": {
                    "datasetMetricConfigs": [
                        {
                            "taskType": "Generation",
                            "dataset": {
                                'name': 'custom',
                                'datasetLocation': eval_dataset_location,
                            },
                            "metricNames": ["Builtin.Accuracy", "Builtin.Robustness", "Builtin.Toxicity"]
                        }
                    ]
                }
            },
            inferenceConfig={
                "models": [
                    {
                        "bedrockModel": {
                            "modelIdentifier": model_arn
                        }
                    }
                ]
            },
            outputDataConfig=output_data_config
        )
        results.append({
            'profile_id': profile_id,
            'status': 'success',
            'job_arn': response['jobArn']
        })
        print(f"✓ {profile_id}: {response['jobArn']}")
    except Exception as e:
        results.append({
            'profile_id': profile_id,
            'status': 'failed',
            'error': str(e)
        })
        print(f"✗ {profile_id}: {str(e)}")

# Summary
successful = sum(1 for r in results if r['status'] == 'success')
failed = sum(1 for r in results if r['status'] == 'failed')

print(f"\n{'='*60}")
print(f"Successful: {successful}")
print(f"Failed: {failed}")
print(f"{'='*60}")
