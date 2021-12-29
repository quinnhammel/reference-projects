#!/usr/bin/env python3

import time
import boto3
# this code is based from other code online. 

# set following constants (all caps)...
REGION_NAME = 'us-east-2'

WORKING_DIRECTORY = '/home/ubuntu/crypto-store/src'

COMMAND = """
    python3 shopify_order_processing.py
    """
INSTANCE_ID = "private instance id goes here"

#NOTE: we assume that EC2 instance is already running. 
#TODO: consider changing this?
def run_command():
    client = boto3.client('ssm', region_name=REGION_NAME)

    time.sleep(10)  # I had to wait 10 seconds to "send_command" find my instance 

    cmd_response = client.send_command(
        InstanceIds=[INSTANCE_ID],
        DocumentName='AWS-RunShellScript',
        DocumentVersion="1",
        TimeoutSeconds=300,
        MaxConcurrency="1",
        CloudWatchOutputConfig={'CloudWatchOutputEnabled': True},
        Parameters={
            'commands': [COMMAND],
            'executionTimeout': ["300"],
            'workingDirectory': [WORKING_DIRECTORY],
        },
    )

    command_id = cmd_response['Command']['CommandId']
    time.sleep(1)  # Again, I had to wait 1s to get_command_invocation recognises my command_id

    retcode = -1
    while True:
        output = client.get_command_invocation(
            CommandId=command_id,
            InstanceId=INSTANCE_ID,
        )

        # If the ResponseCode is -1, the command is still running, so wait 5 seconds and try again
        retcode = output['ResponseCode']
        if retcode != -1:
            print('Status: ', output['Status'])
            print('StdOut: ', output['StandardOutputContent'])
            print('StdErr: ', output['StandardErrorContent'])
            break

        print('Status: ', retcode)
        time.sleep(5)

    print('Command finished successfully') # Actually, 0 means success, anything else means a fail, but it didn't matter to me
    return retcode


def lambda_handler(event, context):
    retcode = run_command()

    return retcode