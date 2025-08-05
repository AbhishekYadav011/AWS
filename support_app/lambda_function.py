import base64
import botocore
import boto3
import json
import logging
import requests

from ast import literal_eval
from utils.octobusclouddb import project_details

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(name)s:%(funcName)s:%(lineno)d:%(message)s',
                    )


def lambda_handler(event, context):
    secret = get_secrets()
    # Get Access Keys for svc-mc-projectname-readsupport and create an STS client using those credentials
    iam_user_access_key_id, iam_user_secret_key_id = secret.get('support_access'), secret.get('support_secret')
    sts_client = boto3.client(
        service_name='sts',
        aws_access_key_id=iam_user_access_key_id,
        aws_secret_access_key=iam_user_secret_key_id
    )
    # Unpack CloudTrail event that was published via SNS Topic
    sns_message = event['Records'][0]['Sns']['Message']
    cloudtrail_event = literal_eval(sns_message)
    # Just get the important info that we'll need to use later to get the Support Case
    acc_id = cloudtrail_event['userIdentity']['accountId']
    support_event_type = cloudtrail_event['eventName']
    region = cloudtrail_event['awsRegion']
    logging.info(cloudtrail_event)
    if support_event_type in ['AddCommunicationToCase', 'ResolveCase']:
        support_case_id = cloudtrail_event['requestParameters']['caseId']
    else:
        if 'responseElements' in cloudtrail_event:
            support_case_id = cloudtrail_event['responseElements']['caseId']
        else:
            logging.info("No Response Elements in the triggering CloudTrail Event. No Case ID exists.")
    if support_case_id:
        # Use account ID we pulled from CT Event to generate credentials into account.
        role_switch_creds = generate_target_account_access(acc_id, sts_client)
        logging.info("Getting support case event details for {}".format(support_case_id))
        support_case_info = get_support_case(role_switch_creds, region, support_case_id)
        logging.info(support_case_info)
        if support_case_info is not None:
            if 'Enterprise Support for new AWS Account' in support_case_info['subject']:
                logging.info("Support event is related to enabling Ent Support for new AWS account and is not needed.")
            else:
                logging.info("Processing event info to be suitable for Octobus/Projectname")
                processed_support_event = process_support_event(support_case_info, acc_id)
                send_event(processed_support_event)


def get_secrets():
    secret_name = "test"
    region_name = "us-east-2"
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    if 'SecretString' in get_secret_value_response:
        secret = get_secret_value_response['SecretString']
    else:
        decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
    secret = json.loads(secret)
    return secret


def generate_target_account_access(acc, client):
    credentials = client.assume_role(
        RoleArn='arn:aws:iam::{}:role/MsCrossAccountReadandSupportRole'.format(acc),
        RoleSessionName='ProjectnameScrapeSupportCaseInformation'
    )
    return credentials


def get_support_case(credentials, region, case_id):
    support_client = boto3.client(
        service_name='support',
        region_name=region,
        aws_access_key_id=credentials['Credentials']['AccessKeyId'],
        aws_secret_access_key=credentials['Credentials']['SecretAccessKey'],
        aws_session_token=credentials['Credentials']['SessionToken']
    )
    try:
        describe_case = support_client.describe_cases(caseIdList=[case_id])
        return describe_case['cases'][0]
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'SubscriptionRequiredException':
            logging.info("AWS Account lacks Premium/Enterprise Support and as such we cannot describe the Support Case.")
        else:
            logging.error(e)
        return None


def process_support_event(support_event, acc_id):
    secret = get_secrets()
    processed_event = json.loads(json.dumps(support_event))
    processed_event['name'], processed_event['lob'], processed_event['environment'] = project_details(acc_id,
                                                                                                     secret.get('elkapikey_euw4'))
    processed_event['hyperscaler'] = 'aws'
    processed_event['accountID'] = acc_id
    processed_event['title'] = support_event['subject']
    del processed_event['subject']
    processed_event['severity'] = support_event['severityCode']
    del processed_event['severityCode']
    processed_event['supportTicketId'] = support_event['displayId']
    del processed_event['displayId']
    processed_event['issueType'] = support_event['serviceCode']
    del processed_event['serviceCode']
    communicationsCount = len(processed_event['recentCommunications']['communications']) - 1
    processed_event['description'] = processed_event['recentCommunications']['communications'][communicationsCount]['body']
    communications = processed_event['recentCommunications']['communications']
    del processed_event['recentCommunications']
    processed_event['recentCommunications'] = getCommunications(communications)
    processed_event['contactDetails'] = support_event['submittedBy']
    del processed_event['submittedBy']
    processed_event['createdDate'] = support_event['timeCreated'][:19] + 'Z'
    del processed_event['timeCreated']
    processed_event['supportTicketStatus'] = support_event['status']
    del processed_event['status']
    logging.info("Processed Event: {}".format(processed_event))
    delete_existing_record(processed_event['supportTicketId'])
    return json.dumps(processed_event)


def getCommunications(communications):
    returnCommunications = ''
    for communication in communications :
        submittedBy = communication['submittedBy']
        body = communication['body']
        timeCreated = communication['timeCreated']
        returnCommunications = returnCommunications + "submittedBy: " + submittedBy + "\ntimeCreated: " +timeCreated + "\nBody: " + body +"\n-----------------------------\n\n\n"
    return returnCommunications


def send_event(event):
    logging.info("Attempting to send event.")
    url_list = [
        "https://endpoint_url/c0030/log/hyperscaler_supporttickets"
    ]
    for url in url_list:
        headers = {'Content-type': 'application/json'}
        results = requests.post(url, data=event, headers=headers)
        logging.info(results.status_code)
        logging.info(results.content)


def delete_existing_record(ticketId):
    secret = get_secrets()
    endpoints = {
        'euw4': {
            'url': 'https://endpoint_url/c0030_log_hyperscaler_supporttickets/_delete_by_query',
            'api_key': secret.get('elkapikey_euw4')
        }
    }
    for endpoint in endpoints.keys():
        api_headers = {'Authorization': endpoints[endpoint]['api_key'], 'Content-Type': 'application/json'}
        delete_query = {
            "query": {
                "match": {
                    "supportTicketId": ticketId
                }
            }
        }
        response = requests.post(endpoints[endpoint]['url'], headers=api_headers, json=delete_query)
        print(f"delete api response for {ticketId}:", response.status_code)
