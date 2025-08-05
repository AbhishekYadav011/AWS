import json
import boto3
from botocore.exceptions import ClientError
from lambda_function import send_sla_data

def process(json_event,secret):
    print("Inside Opensearch service")
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
        opensearchClient = session.client("opensearch", region_name=json_event["region"])
        '''To get the name of opesearch domain name'''
        opensearchDomainName = opensearchClient.list_domain_names(EngineType='OpenSearch')
        for domainname in opensearchDomainName['DomainNames']:
            print(domainname['DomainName'])
            json_event['resourceName'] = domainname['DomainName']
            domainconfigresponse = opensearchClient.describe_domain_config(DomainName=domainname['DomainName'])
            '''To get the configuration details of opensearch domain ex: number of az '''
            azcount = domainconfigresponse['DomainConfig']['ClusterConfig']['Options']['ZoneAwarenessConfig'][
                'AvailabilityZoneCount']
            if azcount > 1:
                print("azcount is greater than one:", azcount)
                if float(99.0) < json_event["monthlyUptimePercentage"] < float(99.9):
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
        