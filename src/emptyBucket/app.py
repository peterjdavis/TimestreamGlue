import cfnresponse
import boto3
import logging
import json
import os

logging.getLogger().setLevel(logging.INFO)

session = boto3.Session()

bucket_name = os.environ['TargetBucket']

def lambda_handler(event, context):
    logging.info('RequestType = ' + event.get('RequestType'))
    if event.get('RequestType') == 'Create':
        logging.info('This is the event: ' + json.dumps(event))
        responseData = {}
        responseData['message'] = "Nothing to do on create"
        logging.info('Sending %s to cloudformation', responseData['message'])
        cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData)
    elif event.get('RequestType') == 'Delete':
        responseData = {}
        responseData['message'] = "Emptying the S3 Bucket: " + bucket_name
        logging.info('Sending %s to cloudformation', responseData['message'])
        try:
            empty_bucket()
            cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData)
        except Exception as e:
            responseData['message'] = str(type(e))
            logging.error('Exception encountered: %s', responseData['message'])
            cfnresponse.send(event, context, cfnresponse.FAILED, responseData)
    else:
        logging.error('Unknown operation: %s', event.get('RequestType'))

def empty_bucket():
    logging.info('About to delete the files in S3 bucket ' + bucket_name)
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)
    response = bucket.objects.all().delete()