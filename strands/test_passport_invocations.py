#!/usr/bin/env python3
"""
Test invocations for passport agent via agentcore invoke
"""

import json
import subprocess
import sys

# Test cases for passport agent
test_cases = [
    {
        "name": "basic_passport_analysis",
        "payload": {"prompt": "Can you analyze my passport picture?"}
    },
    {
        "name": "specific_customer_liene", 
        "payload": {"prompt": "I'm LIENE, please analyze my passport"}
    },
    {
        "name": "specific_customer_christian",
        "payload": {"prompt": "My name is Christian, can you extract the fields from my passport?"}
    },
    {
        "name": "specific_customer_birute",
        "payload": {"prompt": "I am Birute and need passport analysis"}
    },
    {
        "name": "credit_request_context",
        "payload": {"prompt": "I need to apply for credit, can you help me with my passport verification?"}
    },
    {
        "name": "invalid_customer",
        "payload": {"prompt": "My name is John, please analyze my passport"}
    },
    {
        "name": "general_inquiry",
        "payload": {"prompt": "What information can you extract from passport documents?"}
    },
    {
        "name": "random_customer_retrieval",
        "payload": {"prompt": "I forgot my name, can you help me find it and analyze my passport?"}
    },
    {
        "name": "adapting to the language",
        "payload": {"prompt": "Hi, I'm Liene. Based on my document, what is my Nationality? Please answer in the language used in my nation"}
    }
]

def run_test(test_case):
    """Run a single test case"""
    print(f"\n{'='*50}")
    print(f"Running test: {test_case['name']}")
    print(f"Prompt: {test_case['payload']['prompt']}")
    print(f"{'='*50}")
    
    try:
        # Convert payload to JSON string
        payload_json = json.dumps(test_case['payload'])
        
        # Run agentcore invoke command
        cmd = ['agentcore', 'invoke', payload_json]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        print(f"Exit code: {result.returncode}")
        if result.stdout:
            print(f"Output:\n{result.stdout}")
        if result.stderr:
            print(f"Error:\n{result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("Test timed out after 60 seconds")
    except Exception as e:
        print(f"Error running test: {e}")

def main():
    """Run all test cases"""
    print("Starting passport agent test invocations...")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}/{len(test_cases)}")
        run_test(test_case)
        
        # # Ask user if they want to continue
        # if i < len(test_cases):
        #     response = input("\nPress Enter to continue to next test, or 'q' to quit: ")
        #     if response.lower() == 'q':
        #         break
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    main()