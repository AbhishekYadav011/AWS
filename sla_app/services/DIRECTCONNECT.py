import boto3
import json

from botocore.exceptions import ClientError

from lambda_function import send_sla_data


def process(json_event, secret):
    print("Inside Direct Connect file")
    print(json_event['resourceName'])
    if json_event['resourceName'] != "AWS_ACCOUNT":
        acessid = secret.get('support_access')
        accesskey = secret.get('support_secret')
        stsClient = boto3.client('sts', aws_access_key_id='acessid',
                                    aws_secret_access_key='accesskey', region_name="us-east-1",
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
        directconnectClient = session.client("directconnect", region_name=json_event['region'])
        try:
            connections = directconnectClient.describe_connections()
            resiliency_tag = ((connections['connections'])[0]connection['tags'][1])
            resiliency_tag_level = resiliency_tag['value']
            print(resiliency_tag_level)
            if resiliency_tag_level == "high":
                print("Multi-Site Non-Redundant SLA")
                if json_event['monthlyUptimePercentage'] < float(99.9):
                    json_event['resourceName'] = ((connections['connections'])[0]['connectionId'])
                    json_event['slaCreditAvailable'] = 'Yes'
                    if float(99) < json_event["monthlyUptimePercentage"] < float(99.9):
                        json_event["slaCredit"] = "10%"
                        send_sla_data(json.dumps(json_event))
                    if float(95) < json_event["monthlyUptimePercentage"] < float(99):
                        json_event["slaCredit"] = "25%"
                        send_sla_data(json.dumps(json_event))
                    if json_event["monthlyUptimePercentage"] < float(95):
                        json_event["slaCredit"] = "100%"
                        send_sla_data(json.dumps(json_event))
            if resiliency_tag_level == "max":
                print("Multi-Site Redundant SLA")
                if json_event['monthlyUptimePercentage'] < float(99.99):
                    json_event['resourceName'] = ((connections['connections'])[0]['connectionId'])
                    json_event['slaCreditAvailable'] = 'Yes'
                    if float(99) < json_event["monthlyUptimePercentage"] < float(99.99):
                        json_event["slaCredit"] = "10%"
                        send_sla_data(json.dumps(json_event))
                    if float(95) < json_event["monthlyUptimePercentage"] < float(99):
                        json_event["slaCredit"] = "25%"
                        send_sla_data(json.dumps(json_event))
                    if json_event["monthlyUptimePercentage"] < float(95):
                        json_event["slaCredit"] = "100%"
                        send_sla_data(json.dumps(json_event))
            else:
                print("Single Connection SLA")
                if json_event['monthlyUptimePercentage'] < float(95):
                    json_event['resourceName'] = ((connections['connections'])[0]['connectionId'])
                    json_event['slaCreditAvailable'] = 'Yes'
                    if float(92.5) < json_event["monthlyUptimePercentage"] < float(95):
                        json_event["slaCredit"] = "10%"
                        send_sla_data(json.dumps(json_event))
                    if float(90) < json_event["monthlyUptimePercentage"] < float(92.5):
                        json_event["slaCredit"] = "25%"
                        send_sla_data(json.dumps(json_event))
                    if json_event["monthlyUptimePercentage"] < float(90):
                        json_event["slaCredit"] = "100%"
                        send_sla_data(json.dumps(json_event))
        except ClientError as e:
            print("Unexpected error: %s" % e.response['Error']['Message'])
