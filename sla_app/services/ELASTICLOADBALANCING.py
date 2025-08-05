import boto3
import json
from botocore.exceptions import ClientError
from lambda_function import send_sla_data

def process(json_event, secret):
    accountID = json_event['accountID']
    accessId = secret.get('support_access')
    accessKey = secret.get('support_secret')
    stsClient = boto3.client('sts', aws_access_key_id=accessId,
                             aws_secret_access_key=accessKey, region_name="us-east-1",
                             endpoint_url="https://sts.us-east-1.amazonaws.com")
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
    elb = session.client('elbv2', region_name=json_event["region"])
    try:
        lbs = elb.describe_load_balancers()
        for lb in lbs["LoadBalancers"]:
            '''azlist will differentiate b/w multi-az sla and single-az sla'''
            azlist = lb['AvailabilityZones']
            if len(azlist) > 1:
                print("multi-az load balancer")
                if float(99.0) < json_event["monthlyUptimePercentage"] < float(99.99):
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
            else:
                print("single az load balancer")
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
