import boto3
import json
import os
import uuid
import time

MODEL_ID = 'anthropic.claude-3-sonnet-20240229-v1:0'
BUCKET_NAME = os.environ.get('BUCKET_NAME')

s3 = boto3.client('s3')
transcribe = boto3.client('transcribe')


def lambda_handler(event, context):
    print(event)

    # (1) Read speech file
    audio_name = event['body']['name']

    # (2) Anaylze speech
    job_name = str(uuid.uuid4())

    src = f's3://{BUCKET_NAME}/videos/{audio_name}'
    dst = f's3://{BUCKET_NAME}/analyze_results/'

    transcribe.start_call_analytics_job(
        CallAnalyticsJobName=job_name,
        Media={
            'MediaFileUri': f's3://{BUCKET_NAME}/videos/{audio_name}'
        },
        OutputLocation=f's3://{BUCKET_NAME}/analyze_results/',
        Settings={
            'LanguageOptions': ['en-US']
        },
        ChannelDefinitions=[
            {
                'ChannelId': 0,
                'ParticipantRole': 'AGENT'
            },
            {
                'ChannelId': 1,
                'ParticipantRole': 'CUSTOMER'
            }
        ]
    )

    # (3) Get Analyze Results
    response = transcribe.get_call_analytics_job(
        CallAnalyticsJobName=job_name
    )

    status = response['CallAnalyticsJob']['CallAnalyticsJobStatus']
    while status == 'QUEUED' or status == 'IN_PROGRESS':
        print('CallAnalyticsJob in progress...')
        response = transcribe.get_call_analytics_job(
            CallAnalyticsJobName=job_name
        )
        status = response['CallAnalyticsJob']['CallAnalyticsJobStatus']
        time.sleep(10)

    print('AnalyticsJob is completed.')

    print(response)

    # TODO implement
    return {
        'statusCode': 200,
        'body': 'temp'
    }
