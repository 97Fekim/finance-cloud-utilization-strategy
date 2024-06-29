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
BUCKET_NAME = os.environ.get('BUCKET_NAME')
MEDIA_CONVERT_ROLE = os.environ.get('MEDIA_CONVERT_ROLE')


s3 = boto3.client('s3')
transcribe = boto3.client('transcribe')

def handler(event, context):
    print(event)

    # ASIS: Video
    # TOBE: Image
    audio_name = event['body']['name']
    print("==============event_dict==============")
    print(audio_name)
    job_name = str(uuid.uuid4())

    transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        LanguageCode='en-US',
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
    print("====================================response====================================")
    print("====================================response====================================")
    print(response)
    print("====================================response====================================")
    print("====================================response====================================")

    temp = []
    for transcript in content['results']['transcripts']:
        temp.append(transcript['transcript'])

    transcripts = ' '.join(temp)

    response = {
        "transcripts": transcripts
    }

    return {
        'statusCode': 200,
        'body': json.dumps(response)
    }
