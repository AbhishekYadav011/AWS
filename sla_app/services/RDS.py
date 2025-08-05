import boto3
import json

from botocore.exceptions import ClientError
from lambda_function import send_sla_data


def process(json_event, secret):
    print("Inside RDS file")
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

    rdsClient = session.client("rds", region_name=json_event["region"])
    listDbInstances = rdsClient.describe_db_instances()
    try:
        for instance in listDbInstances["DBInstances"]:
            # declaring all the variables
            dbInstanceName = instance["DBInstanceIdentifier"]
            dbInstanceResourceId = instance["DbiResourceId"]
            dbInstanceMultiAz = instance["MultiAZ"]
            if dbInstanceMultiAz is True:
                print("RDS SLA Calculation")
                if float(99) < json_event["monthlyUptimePercentage"] < float(99.95):
                    json_event["dbInstanceName"] = dbInstanceName
                    json_event["dbInstanceResourceId"] = dbInstanceResourceId
                    json_event["slaCreditAvailable"] = "Yes"
                    json_event["slaCredit"] = "10%"
                    send_sla_data(json.dumps(json_event))
                if float(95) < json_event["monthlyUptimePercentage"] < float(99):
                    json_event["dbInstanceName"] = dbInstanceName
                    json_event["dbInstanceResourceId"] = dbInstanceResourceId
                    json_event["slaCreditAvailable"] = "Yes"
                    json_event["slaCredit"] = "25%"
                    send_sla_data(json.dumps(json_event))
                if json_event["monthlyUptimePercentage"] < float(95):
                    json_event["dbInstanceName"] = dbInstanceName
                    json_event["dbInstanceResourceId"] = dbInstanceResourceId
                    json_event["slaCreditAvailable"] = "Yes"
                    json_event["slaCredit"] = "100%"
                    send_sla_data(json.dumps(json_event))

    except ClientError as e:
        print("Unexpected error: %s" % e.response['Error']['Message'])
