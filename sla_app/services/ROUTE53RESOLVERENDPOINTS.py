import boto3
import json
from lambda_function import send_sla_data
from botocore.exceptions import ClientError

def process(json_event, secret):
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
    try:
        route53client = session.resource('route53resolver', region_name=json_event["region"])
        response = route53client.list_resolver_endpoints()
        print(response['ResolverEndpoints'])
        for resolverEndpointId in response['ResolverEndpoints']:
            '''To get the total number of subnets for resolver endpoint'''
            subnetIdList = []
            print(resolverEndpointId['Id'])
            resolverId = resolverEndpointId['Id']
            '''To get the list of subnet of route53 resolver endpoint'''
            ipaddressresponse = route53client.list_resolver_endpoint_ip_addresses(ResolverEndpointId=resolverId)
            print(ipaddressresponse)
            for subnetIds in ipaddressresponse['IpAddresses']:
                print(subnetIds['SubnetId'])
                subnetIdList.append(subnetIds['SubnetId'])
            print(subnetIdList)
            ec2Client = session.client("ec2", region_name=json_event["region"])
            '''To get the list of Az ,method describe_subnets is used'''
            describeSubnetResponse = ec2Client.describe_subnets(SubnetIds=subnetIdList)
            print(describeSubnetResponse)
            azlist = []
            for azs in describeSubnetResponse['Subnets']:
                print(azs['AvailabilityZone'])
                azlist.append(azs['AvailabilityZone'])
            '''verify the final size of az list if its more than one than route53 resolver endpoint is multi-az'''
            print(azlist)
            if len(list(set(azlist))) > 1:
                print('multi-az configuration')
                if float(99) < json_event["monthlyUptimePercentage"] < float(99.99):
                    json_event["slaCreditAvailable"] = "Yes"
                    json_event["slaCredit"] = "10%"
                    print(json_event)
                    send_sla_data(json.dumps(json_event))
                elif float(95) < json_event["monthlyUptimePercentage"] < float(99):
                    json_event["slaCreditAvailable"] = "Yes"
                    json_event["slaCredit"] = "25%"
                    print(json_event)
                    send_sla_data(json.dumps(json_event))
                elif json_event["monthlyUptimePercentage"] < float(95):
                    json_event["slaCreditAvailable"] = "Yes"
                    json_event["slaCredit"] = "100%"
                    print(json_event)
                    send_sla_data(json.dumps(json_event))
            else:
                print('single az configuration')
                if float(99.0) < json_event["monthlyUptimePercentage"] < float(99.5):
                    json_event["slaCreditAvailable"] = "Yes"
                    json_event["slaCredit"] = "10%"
                    print(json_event)
                    send_sla_data(json.dumps(json_event))
                elif float(95.0) < json_event["monthlyUptimePercentage"] < float(99.0):
                    json_event["slaCreditAvailable"] = "Yes"
                    json_event["slaCredit"] = "25%"
                    print(json_event)
                    send_sla_data(json.dumps(json_event))
                elif json_event["monthlyUptimePercentage"] < float(95):
                    json_event["slaCreditAvailable"] = "Yes"
                    json_event["slaCredit"] = "100%"
                    print(json_event)
                    send_sla_data(json.dumps(json_event))
    except ClientError as e:
        print("Unexpected error: %s" % e.response['Error']['Message'])
