#!/usr/bin/env python3
import boto3
import json

bedrock = boto3.client('bedrock')
s3 = boto3.client('s3')
sts = boto3.client('sts')

ACCOUNT_ID = sts.get_caller_identity()['Account']
BUCKET_NAME = f"genai-evaluation-migration-bucket-{ACCOUNT_ID}"

# List all evaluation jobs
response = bedrock.list_evaluation_jobs(maxResults=100)
jobs = response.get('jobSummaries', [])

results = []

for job in jobs:
    job_arn = job['jobArn']
    job_name = job['jobName']
    status = job['status']
    
    result = {
        'job_name': job_name,
        'job_arn': job_arn,
        'status': status,
        'creation_time': job.get('creationTime', '').isoformat() if job.get('creationTime') else None
    }
    
    # If completed, fetch results from S3
    if status == 'Completed':
        try:
            # Get job details for output location
            job_detail = bedrock.get_evaluation_job(jobIdentifier=job_arn)
            output_uri = job_detail.get('outputDataConfig', {}).get('s3Uri', '')
            job_name = job_detail.get('jobName')
            
            if output_uri:
                # Parse S3 URI
                bucket = output_uri.split('/')[2]
                prefix = '/'.join(output_uri.split('/')[3:]) + job_name
                
                # List objects in output location
                s3_response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
                if 'Contents' in s3_response:
                    result['output_files'] = [obj['Key'] for obj in s3_response['Contents'] if obj['Key'].endswith('.jsonl')]
        except Exception as e:
            result['error'] = str(e)
    
    results.append(result)


for result in results:
    if 'output_files' in result:
        for file_key in result['output_files']:
            obj = s3.get_object(Bucket=BUCKET_NAME, Key=file_key)
            content = obj['Body'].read().decode('utf-8')
            print(f"\n{'='*60}")
            print(f"File: {file_key}")
            print(f"{'='*60}")
            data = json.loads(content)
            print(json.dumps(data, indent=2))
# Summary
print(f"\n{'='*60}")
print(f"Total jobs: {len(results)}")
print(f"Completed: {sum(1 for r in results if r['status'] == 'Completed')}")
print(f"In Progress: {sum(1 for r in results if r['status'] == 'InProgress')}")
print(f"Failed: {sum(1 for r in results if r['status'] == 'Failed')}")
print(f"{'='*60}")
