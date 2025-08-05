import boto3
import json
from botocore.exceptions import ClientError
from lambda_function import send_sla_data


def process(json_event, secret):
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
        networkClient = session.client("networkmanager", region_name='us-west-2')
        globalNetworkResponse = networkClient.describe_global_networks()
        print(globalNetworkResponse['GlobalNetworks'])
        for globalNetwork in globalNetworkResponse['GlobalNetworks']:
            print(globalNetwork['GlobalNetworkId'])
            json_event['resourceName'] = globalNetwork['GlobalNetworkId']
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
    except ClientError as e:
        print("Unexpected error: %s" % e.response['Error']['Message'])
