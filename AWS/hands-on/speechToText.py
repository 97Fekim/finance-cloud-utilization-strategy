# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Video Shortform: MIT-0
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

# ASIS: 비디오 → 텍스트 → 텍스트
# TOBE: 오디오 → 텍스트

import boto3
import json
import os
import uuid
import time

MODEL_ID = 'anthropic.claude-3-sonnet-20240229-v1:0'
BEDROCK_REGION_NAME=os.environ.get('BEDROCK_REGION_NAME', 'us-west-2')
BUCKET_NAME = os.environ.get('BUCKET_NAME')
MEDIA_CONVERT_ROLE = os.environ.get('MEDIA_CONVERT_ROLE')

bedrock_runtime = boto3.client(
    service_name='bedrock-runtime',
    region_name=BEDROCK_REGION_NAME
)

s3 = boto3.client('s3')
transcribe = boto3.client('transcribe')


def get_response(user_prompt, system_prompt):
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

    # Run Bedrock API
    response = bedrock_runtime.invoke_model(
        modelId=MODEL_ID,
        contentType='application/json',
        accept='application/json',
        body=json.dumps(body)
    )

    response_body = json.loads(response.get('body').read())
    output = response_body['content'][0]['text']

    return output


def handler(event, context):
    print(event)

    # ASIS: Video
    # TOBE: Image
    audio_name = json.loads(event['body'])['name']
    job_name = str(uuid.uuid4())

    transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        LanguageCode='ko-KR',
        MediaFormat='mp3',
        Media={
            'MediaFileUri': f's3://{BUCKET_NAME}/videos/{audio_name}'
        },
        OutputBucketName=BUCKET_NAME,
        OutputKey=f'subtitles/{job_name}/output.json',
        Subtitles={
            'Formats': ['vtt']
        }
    )

    response = transcribe.get_transcription_job(
        TranscriptionJobName=job_name
    )

    status = response['TranscriptionJob']['TranscriptionJobStatus']
    while status == 'QUEUED' or status == 'IN_PROGRESS':
        print('Transcription in progress...')
        response = transcribe.get_transcription_job(
            TranscriptionJobName=job_name
        )
        status = response['TranscriptionJob']['TranscriptionJobStatus']
        time.sleep(10)

    print('Transcription is completed.')

    # 내용 요약 작업 수행
    object_key = f'subtitles/{job_name}/output.json'

    response = s3.get_object(Bucket=BUCKET_NAME, Key=object_key)
    content = json.loads(response['Body'].read().decode('utf-8'))

    temp = []
    for transcript in content['results']['transcripts']:
        temp.append(transcript['transcript'])

    transcripts = ' '.join(temp)

    user_prompt = f"<script>{transcripts}</script>"

    system_prompt = """
당신은 비디오 자막 스크립트의 요약 작업을 합니다.
<script> 에는 비디오에서 추출한 자막 스크립트가 있습니다.
<script> 에서 주요 키워드 10개를 추출하고, 요약을 만듭니다.
답변은 JSON 형식으로 출력합니다.
JSON 형식:
{    
    "요약": "요약",
    "주요 키워드": ["키워드", ...]
}

Respond only in korean.
Skip the preamble.
You must respond in a valid JSON format.
You must not wrap JSON response in backticks, markdown, or in any other way, but return it as plain text.
"""
    summary_text = get_response(user_prompt, system_prompt)
    print(summary_text)

    summarization = json.loads(summary_text)

    # 스크립트 요약 작업 수행
    # been deleted

    response = {
        "summary": summarization,
    }

    return {
        'statusCode': 200,
        'body': json.dumps(response)
    }
