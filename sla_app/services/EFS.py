import boto3
import json

from botocore.exceptions import ClientError

from lambda_function import send_sla_data


def process(json_event, secret):
    print("Inside EFS file")
    accessId = secret.get('support_access')
    accessKey = secret.get('support_secret')
    stsClient = boto3.client('sts', aws_access_key_id=accessId,
                             aws_secret_access_key=accessKey, region_name="us-east-1",
                             endpoint_url="https://sts.us-east-1.amazonaws.com")

    accountId = json_event['accountID']
    role = stsClient.assume_role(RoleArn=f'arn:aws:iam::{accountId}:role/MsCrossAccountReadandSupportRole',
                                 RoleSessionName='switchedRole')
    credentials = role['Credentials']
    awsAccessKeyId = credentials['AccessKeyId']
    awsSecretAccessKey = credentials['SecretAccessKey']
    awsSessionToken = credentials['SessionToken']
    session = boto3.session.Session(
        aws_access_key_id=awsAccessKeyId,
        aws_secret_access_key=awsSecretAccessKey,
        aws_session_token=awsSessionToken)
    efsClient = session.client("efs", region_name=json_event["region"])
    try:
        fileSystems = efsClient.describe_file_systems().get("FileSystems")
        for fileSystem in fileSystems:
            if("AvailabilityZoneId" in fileSystem):
                #FS is one Zone Filesystem 
                if float(99) < json_event["monthlyUptimePercentage"] < float(99.9):
                    json_event["slaCreditAvailable"] = "Yes"
                    json_event["slaCredit"] = "10%"
                    send_sla_data(json.dumps(json_event))
                if float(95) < json_event["monthlyUptimePercentage"] < float(99):
                    json_event["slaCreditAvailable"] = "Yes"
                    json_event["slaCredit"] = "30%"
                    send_sla_data(json.dumps(json_event))
                if json_event["monthlyUptimePercentage"] < float(95):
                    json_event["slaCreditAvailable"] = "Yes"
                    json_event["slaCredit"] = "100%"
                    send_sla_data(json.dumps(json_event))
            else :
                #FS is Standard Filesystem 
                if float(99) < json_event["monthlyUptimePercentage"] < float(99.99):
                    json_event["slaCreditAvailable"] = "Yes"
                    json_event["slaCredit"] = "10%"
                    send_sla_data(json.dumps(json_event))
                if float(95) < json_event["monthlyUptimePercentage"] < float(99):
                    json_event["slaCreditAvailable"] = "Yes"
                    json_event["slaCredit"] = "30%"
                    send_sla_data(json.dumps(json_event))
                if json_event["monthlyUptimePercentage"] < float(95):
                    json_event["slaCreditAvailable"] = "Yes"
                    json_event["slaCredit"] = "100%"
                    send_sla_data(json.dumps(json_event))
    except ClientError as e:
        print("Unexpected error: %s" % e.response['Error']['Message'])
