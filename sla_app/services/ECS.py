import boto3
import json
from botocore.exceptions import ClientError
from lambda_function import send_sla_data


def process(json_event, secret):
    print("Inside Elastic Container Service")
    del json_event['resourceName']
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

    try:
        ecsClient = session.client("ecs", region_name='us-east-2')
        clusterList = ecsClient.list_clusters()['clusterArns']
        for clusterarn in clusterList:
            taskArnsList = ecsClient.list_tasks(cluster=clusterarn)['taskArns']
            tasksList = ecsClient.describe_tasks(cluster=clusterarn, tasks=taskArnsList)['tasks']
            availabilityZoneList = list(set([az['availabilityZone'] for az in tasksList]))
            if len(availabilityZoneList) > 1:
                json_event['resourceName'] = clusterarn
                if json_event['monthlyUptimePercentage'] < float(99.99):
                    print("Service Credit - is applicable for Multi-az")
                    json_event['slaCreditAvailable'] = 'Yes'
                    if float(99) < json_event['monthlyUptimePercentage'] < float(99.99):
                        json_event['slaCredit'] = '10%'
                        send_sla_data(json.dumps(json_event))
                    if float(95) < json_event['monthlyUptimePercentage'] < float(99):
                        json_event['slaCredit'] = '25%'
                        send_sla_data(json.dumps(json_event))
                    else:
                        json_event['slaCredit'] = '100%'
                        send_sla_data(json.dumps(json_event))
            else:
                for taskArn in taskArnsList:
                    json_event['resourceName'] = taskArn
                    if json_event['monthlyUptimePercentage'] < float(99.5):
                        json_event['slaCreditAvailable'] = 'Yes'
                        if float(99) < json_event['monthlyUptimePercentage'] < float(99.5):
                            json_event['slaCredit'] = '10%'
                            send_sla_data(json.dumps(json_event))
                        if float(95) < json_event['monthlyUptimePercentage'] < float(99):
                            json_event['slaCredit'] = '25%'
                            send_sla_data(json.dumps(json_event))
                        else:
                            json_event['slaCredit'] = '100%'
                            send_sla_data(json.dumps(json_event))
    except ClientError as e:
        print("Unexpected error: %s" % e.response['Error']['Message'])