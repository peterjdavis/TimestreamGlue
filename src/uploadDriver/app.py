import cfnresponse
import boto3
import logging
import requests
import json
import os

logging.getLogger().setLevel(logging.INFO)

session = boto3.Session()

JDBC_driver_path = os.environ['TimestreamJDBCDriverPath']
JDBC_driver_filename = os.environ['TimestreamJDBCDriverFileName']
target_bucket = os.environ['TargetBucket']

def lambda_handler(event, context):
    if event.get('RequestType') == 'Create':
        logging.info('This is the event: ' + json.dumps(event))
        responseData = {}
        responseData['message'] = "About to get the Timestream JDBC Driver"
        logging.info('Sending %s to cloudformation', responseData['message'])
        try: 
            prepareJDBCDriver()
            cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData)
        except Exception as e:
            responseData['message'] = str(type(e))
            logging.error('Exception encountered: %s', responseData['message'])
            cfnresponse.send(event, context, cfnresponse.FAILED, responseData)
    elif event.get('RequestType') == 'Delete':
        responseData = {}
        responseData['message'] = "Deleting the custom resource"
        logging.info('Sending %s to cloudformation', responseData['message'])
        try:
            deleteJDBCDriver()
            cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData)
        except Exception as e:
            responseData['message'] = str(type(e))
            logging.error('Exception encountered: %s', responseData['message'])
            cfnresponse.send(event, context, cfnresponse.FAILED, responseData)    
    else:
        logging.error('Unknown operation: %s', event.get('RequestType'))

def prepareJDBCDriver():
    getJDBCDriver()
    uploadJDBCDriver()

def getJDBCDriver():
    logging.info('About to download the driver')
    url = JDBC_driver_path + JDBC_driver_filename
    try:
        r = requests.get(url, allow_redirects=True)
        r.raise_for_status()
    except requests.HTTPError as e:
        logging.error('Exception: %s', e)
        raise requests.HTTPError
        
    open('/tmp/' + JDBC_driver_filename, 'wb').write(r.content)

def uploadJDBCDriver():
    logging.info('About to upload the driver')
    s3 = session.client('s3')
    try:
        s3.upload_file('/tmp/' + JDBC_driver_filename, target_bucket, JDBC_driver_filename)
        logging.info('Upload Successful')
    except FileNotFoundError:
        logging.error("The file was not found")

def deleteJDBCDriver():
    logging.info('About to delete the driver')
    s3 = session.client('s3')
    s3.delete_object(Bucket=target_bucket, Key=JDBC_driver_filename)
