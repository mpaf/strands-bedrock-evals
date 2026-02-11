from strands import Agent, tool
from strands.models import BedrockModel
from strands.telemetry import StrandsTelemetry
import requests
import logging
import boto3
import random
from bedrock_agentcore.runtime import BedrockAgentCoreApp
import os

app = BedrockAgentCoreApp()

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

bedrock_client = boto3.client('bedrock-runtime', region_name="us-east-1")

# Create a Bedrock model instance
bedrock_model = BedrockModel(
    model_id="global.anthropic.claude-sonnet-4-5-20250929-v1:0",
)


@tool
def analyze_passport_pic(name: str) -> str:
    '''A tool that analyses a passport picture
    given a name of the customer, the agent downloads the picture and applies multi-modal analysis'''
    
    name = name.upper()
    if name not in ['LIENE', 'BIRUTE', 'CHRISTIAN']:
        raise ValueError(f"Could not find a passport with your name: {name}")

    logging.info(f"Analyzing passport picture for {name}...")

    URL_map = {
        'LIENE': "https://upload.wikimedia.org/wikipedia/commons/b/b6/LR_Pases_3._lapa.jpg",
        'BIRUTE': "https://upload.wikimedia.org/wikipedia/commons/8/89/LR_pasas_data_page.jpg",
        'CHRISTIAN': "https://upload.wikimedia.org/wikipedia/commons/c/c5/Chris-pasaporte.jpg"
    }

    # download the image from the URL into a byte array and invoke the model
    response = requests.get(URL_map[name], headers={'User-Agent': 'Mozilla/5.0'}, allow_redirects=True)
    image_bytes = response.content
    logger.info(f"Downloaded image, size: {len(image_bytes)} bytes")

    try:
        # Call model directly with image
        response = bedrock_client.converse(
            modelId=bedrock_model.get_config()['model_id'],
            messages=[{
                "role": "user",
                "content": [
                    {"image": {"format": "jpeg", "source": {"bytes": image_bytes}}},
                    {"text": "Extract the fields from the passport pic"}
                ]
            }]
        )
    except Exception as e:
        logger.error(f"Error calling Bedrock model: {e}")
        raise e
    
    logger.info(f"Image analysis successful")
    return f"Analysis of passport image: {response['output']['message']['content'][0]['text']}"

@tool
def retrieve_customer_name() -> str:
    '''Retrieves the customer name from the database when not provided by user'''

    # return a random name from the list
    return random.choice(['LIENE', 'CHRISTIAN', 'BIRUTE'])

my_agent = Agent(
    name='my_agent',
    system_prompt=(
        "You are an agent specialized in credit requests. "
        "Use tools to gather information and provide personalized information."
        "Always explain your reasoning and cite sources when possible."
    ),
    model=bedrock_model,
    tools=[retrieve_customer_name, analyze_passport_pic],
    callback_handler=None
)

@app.entrypoint
def invoke(payload):

    response = my_agent(payload.get("prompt"))

    return str(response)

if __name__ == "__main__":

    app.run()