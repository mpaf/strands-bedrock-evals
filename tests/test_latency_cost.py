import boto3
import time
import json
import os
filename = os.path.splitext(os.path.basename(__file__))[0]


bedrock = boto3.client('bedrock-runtime')

profile_ids = []
pricing_map = {}
with open('tests/inference_profile_ids.jsonl', 'r') as f:
    for line in f:
        data = json.loads(line)
        profile_ids.append(data['inference_profile_id'])
        pricing_map[data['inference_profile_id']] = {
            'input_cost': data['input_token_cost'],
            'output_cost': data['output_token_cost']
        }

results = []

query = "Write a short poem about clouds"

for profile_id in profile_ids:
    try:
        start_time = time.time()
        first_token_time = None
        
        response = bedrock.converse_stream(
            modelId=profile_id,
            messages=[{"role": "user", "content": [{"text": query}]}]
        )
        
        output_text = ""
        for event in response['stream']:
            if 'contentBlockDelta' in event:
                if first_token_time is None:
                    first_token_time = time.time()
                output_text += event['contentBlockDelta']['delta']['text']
            elif 'metadata' in event:
                metadata = event['metadata']
                usage = metadata['usage']
                
        end_time = time.time()
        
        ttft = first_token_time - start_time if first_token_time else 0
        total_time = end_time - start_time
        tokens_per_sec = usage['outputTokens'] / (end_time - first_token_time) if first_token_time else 0
        
        pricing = pricing_map.get(profile_id, {'input_cost': 0, 'output_cost': 0})
        total_cost = (usage['inputTokens'] * pricing['input_cost']) + (usage['outputTokens'] * pricing['output_cost'])
        
        results.append({
            'profile_id': profile_id,
            'ttft': round(ttft, 3),
            'tokens_per_sec': round(tokens_per_sec, 2),
            'total_time': round(total_time, 3),
            'input_tokens': usage['inputTokens'],
            'output_tokens': usage['outputTokens'],
            'input_text': query,
            'output_text': output_text,
            'total_cost': round(total_cost, 6)
        })
        
        print(f"✓ {profile_id}: TTFT={ttft:.3f}s, TPS={tokens_per_sec:.2f}, Total={total_time:.3f}s, Cost=${total_cost:.6f}")
        
    except Exception as e:
        print(f"✗ {profile_id}: {str(e)}")

with open(f'results/{filename}_results.json', 'w') as f:
    json.dump(results, f, indent=2)
