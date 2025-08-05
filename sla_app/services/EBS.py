import boto3
import json
from botocore.exceptions import ClientError
from lambda_function import send_sla_data


def process(json_event, secret):
    print("Inside EBS file")
    if json_event['resourceName'] != "AWS_ACCOUNT":
        accessId = secret.get('support_access')
        accessKey = secret.get('support_secret')
        stsClient = boto3.client('sts', aws_access_key_id=accessId,
                                 aws_secret_access_key=accessKey, region_name="us-east-1",
                                 endpoint_url="https://sts.us-east-1.amazonaws.com")
        accountID = json_event['accountID']
        role = stsClient.assume_role(RoleArn=f'arn:aws:iam::{accountID}:role/MsCrossAccountReadandSupportRole',
                                     RoleSessionName='switchedRole')
        credentials = role['Credentials']
        awsAccessKeyId = credentials['AccessKeyId']
        awsSecretAccessKey = credentials['SecretAccessKey']
        awsSessionToken = credentials['SessionToken']
        session = boto3.session.Session(
            aws_access_key_id=awsAccessKeyId,
            aws_secret_access_key=awsSecretAccessKey,
            aws_session_token=awsSessionToken)
        ec2Client = session.client("ec2", region_name=json_event["region"])
        try:
            paginator = ec2Client.get_paginator('describe_volumes')
            response_iterator = paginator.paginate()
            for page in response_iterator:
                for volume in page['Volumes']:
                    print(volume['VolumeId'])
                    print(volume['AvailabilityZone'])
                    if volume['VolumeId'] == json_event['resourceName']:
                        if float(99.0) < json_event["monthlyUptimePercentage"] < float(99.9):
                            json_event["slaCreditAvailable"] = "Yes"
                            json_event["slaCredit"] = "10%"
                            print(json_event)
                            send_sla_data(json.dumps(json_event))
                        elif float(95.0) < json_event["monthlyUptimePercentage"] < float(99.0):
                            json_event["slaCreditAvailable"] = "Yes"
                            json_event["slaCredit"] = "30%"
                            print(json_event)
                            send_sla_data(json.dumps(json_event))
                                
                        elif json_event["monthlyUptimePercentage"] < float(95):
                            json_event["slaCreditAvailable"] = "Yes"
                            json_event["slaCredit"] = "100%"
                            print(json_event)
                            send_sla_data(json.dumps(json_event))
                            
                        

        except ClientError as e:
            print("Unexpected error: %s" % e.response['Error']['Message'])

    else:
        if float(99.0) < json_event["monthlyUptimePercentage"] < float(99.9):
            json_event["slaCreditAvailable"] = "Yes"
            json_event["slaCredit"] = "10%"
            print(json_event)
            send_sla_data(json.dumps(json_event))
        elif float(95.0) < json_event["monthlyUptimePercentage"] < float(99.0):
            json_event["slaCreditAvailable"] = "Yes"
            json_event["slaCredit"] = "30%"
            print(json_event)
            send_sla_data(json.dumps(json_event))
                                
        elif json_event["monthlyUptimePercentage"] < float(95):
            json_event["slaCreditAvailable"] = "Yes"
            json_event["slaCredit"] = "100%"
            print(json_event)
            send_sla_data(json.dumps(json_event))
