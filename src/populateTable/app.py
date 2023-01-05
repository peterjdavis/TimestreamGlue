import cfnresponse
import boto3
import logging
import random
import time
import json
import os

logging.getLogger().setLevel(logging.INFO)

session = boto3.Session()
write_client = session.client('timestream-write')

db_name = os.environ['DbName']
table_name = os.environ['TableName']
record_count = os.environ['RecordCount']

def lambda_handler(event, context):
    if event.get('RequestType') == 'Create':
        logging.info('This is the event: ' + json.dumps(event))
        responseData = {}
        responseData['message'] = "About to populate the Timestream DB"
        logging.info('Sending %s to cloudformation', responseData['message'])
        try:
            populate_timestream()
            cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData)
        except Exception as e:
            responseData['message'] = str(type(e))
            logging.error('Exception encountered: %s', responseData['message'])
            cfnresponse.send(event, context, cfnresponse.FAILED, responseData)
    elif event.get('RequestType') == 'Delete':
        responseData = {}
        responseData['message'] = "Deleting the custom resource - nothing to do"
        logging.info('Sending %s to cloudformation', responseData['message'])
        cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData)
    else:
        logging.error('Unknown operation: %s', event.get('RequestType'))

def populate_timestream():
    logging.info('Going to populate %s records', record_count)
    for x in range(int(record_count)):
        write_record()

def write_record():
    current_time = _current_milli_time()
    dimensions = [
        {'Name': 'region', 'Value': 'us-east-1'},
        {'Name': 'az', 'Value': 'az' + str(int(random.random() * 3))},
        {'Name': 'hostname', 'Value': 'host' + str(int(random.random() * 1000))}
    ]

    common_attributes = {
        'Dimensions': dimensions,
        'MeasureValueType': 'DOUBLE',
        'Time': current_time
    }
    
    cpu_utilization = {
        'MeasureName': 'cpu_utilization',
        'MeasureValue': str(random.random() * 100)
    }

    memory_utilization = {
        'MeasureName': 'memory_utilization',
        'MeasureValue': str(random.random() * 100)
    }

    records = [cpu_utilization, memory_utilization]

    try:
        result = write_client.write_records(DatabaseName=db_name, TableName=table_name,
                                           Records=records, CommonAttributes=common_attributes)
        logging.debug("WriteRecords Status: [%s]" % result['ResponseMetadata']['HTTPStatusCode'])
    except write_client.exceptions.RejectedRecordsException as err:
        _print_rejected_records_exceptions(err)
    except write_client.exceptions.ResourceNotFoundException as err:
        logging.error("Error - Going to retry: " + str(err))
        time.sleep(0.5)
        result = write_client.write_records(DatabaseName=db_name, TableName=table_name,
                                    Records=records, CommonAttributes=common_attributes)
        logging.info('Have retried after the exception')
    except Exception as err:
        logging.error("Error:" + str(err))
        raise err

# @staticmethod
def _current_milli_time():
    return str(int(round(time.time() * 1000)))

# @staticmethod
def _print_rejected_records_exceptions(err):
    logging.error("RejectedRecords: " + str(err))
    for rr in err.response["RejectedRecords"]:
        logging.error("Rejected Index " + str(rr["RecordIndex"]) + ": " + rr["Reason"])
        if "ExistingVersion" in rr:
            logging.error("Rejected record existing version: ", rr["ExistingVersion"])