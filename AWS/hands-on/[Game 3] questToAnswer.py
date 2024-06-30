# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Review Summary: MIT-0
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import boto3
import json
import os


BEDROCK_REGION_NAME=os.environ.get('BEDROCK_REGION_NAME', 'us-west-2')

bedrock_runtime = boto3.client(
    service_name='bedrock-runtime',
    region_name=BEDROCK_REGION_NAME
)

MODEL_ID = 'anthropic.claude-3-sonnet-20240229-v1:0'


def handler(event, context):
    print(event)

    user_prompt = event['body']['user_prompt']

    system_prompt = """글에서 설명된 문제를 해결해서, 답변과 풀이과정을 설명합니다."""

    body = {
        "system": system_prompt,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_prompt

                    }
                ]
            }
        ],
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096
    }

    response = bedrock_runtime.invoke_model(
        modelId=MODEL_ID,
        contentType='application/json',
        accept='application/json',
        body=json.dumps(body)
    )
    print(response)

    response_body = json.loads(response.get('body').read())
    print(response_body)

    output = response_body['content'][0]['text']
    print(output)

    return {
        'statusCode': 200,
        'body': output
    }
