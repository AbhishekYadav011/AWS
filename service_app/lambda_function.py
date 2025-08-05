import base64
import boto3
import datetime
import json
import requests
import sapifiedregion
import socket

import dateutil.parser as parser

from utils.octobusclouddb import project_details


def lambda_handler(event, context):
    secret = get_secrets()
    lambda_function(secret)


# time encoder class
class DatetimeEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return super(DatetimeEncoder, obj).default(obj)
        except TypeError:
            return str(obj)


def get_secrets():
    print('Inside Secrets')
    secret_name = "test"
    region_name = "us-east-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    get_secret_value_response = client.get_secret_value(
        SecretId=secret_name
    )
    if 'SecretString' in get_secret_value_response:
        secret = get_secret_value_response['SecretString']
    else:
        decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
    secret = json.loads(secret)
    return secret


def lambda_function(secret):
    healthDns = socket.gethostbyname_ex('global.health.amazonaws.com')
    (current_endpoint, global_endpoint, ip_endpoint) = healthDns
    healthActiveList = current_endpoint.split('.')
    healthActiveRegion = healthActiveList[1]
    endPointUrl = "https://" + current_endpoint
    session = boto3.Session(aws_access_key_id=secret.get('access'), aws_secret_access_key=secret.get('secret'))

    awsHealth = session.client('health', region_name=healthActiveRegion,
                               endpoint_url=endPointUrl)
    # describing the events for org with filter as 7 days and status as open and closed
    eventPaginator = awsHealth.get_paginator('describe_events_for_organization')
    eventsPages = eventPaginator.paginate(filter={
        'lastUpdatedTime':
            {
                'from': (datetime.datetime.now() - datetime.timedelta(minutes=5))
            }
        ,
        'eventStatusCodes': ['open','closed'],
        # 'services':['EC2']
    })
    # getting the events
    for eventsPage in eventsPages:
        for event in eventsPage['events']:
            json_event = json.loads(json.dumps(event, cls=DatetimeEncoder))
            json_event['hyperscaler'] = 'aws'
            json_event['org'] = 'Master'
            json_event['trackingID'] = json_event['arn']
            del json_event['arn']
            json_event['status'] = json_event['statusCode']
            del json_event['statusCode']
            json_event['title'] = json_event['eventTypeCode'].replace("_", " ")
            del json_event['eventTypeCode']
            startTime = json_event["startTime"]
            lastUpdateTime = json_event["lastUpdatedTime"]
            startTimeParser = parser.parse(startTime)
            lastUpdateTimeParser = parser.parse(lastUpdateTime)
            json_event["startTime"] = startTimeParser.isoformat().split("+")[0] + "Z"
            json_event["lastUpdatedTime"] = lastUpdateTimeParser.isoformat().split("+")[0] + "Z"
            startTimeEvent = datetime.datetime.strptime(startTime[:19], '%Y-%m-%d %H:%M:%S')
            # filtering data with issue and account_specific
            if event.get("eventTypeCategory") == "issue":
                # json_event['level'] = json_event['eventTypeCategory']
                json_event['level'] = "Issue"
                if event.get("eventScopeCode") == "ACCOUNT_SPECIFIC":
                    # passing the arn to find affected accounts from org
                    accountIDsjson = json.loads(
                        json.dumps(awsHealth.describe_affected_accounts_for_organization(eventArn=event.get('arn')),
                                   cls=DatetimeEncoder))
                    # getting the values for the accountID from cloudDB
                    for accountID in accountIDsjson["affectedAccounts"]:
                        json_event["accountID"] = accountID
                        json_event['name'], json_event['lob'], json_event['environment'] = project_details(accountID,
                                                                                                           secret.get('elkapikey_euw4'))
                        description = json.loads(json.dumps(awsHealth.describe_event_details_for_organization(
                            organizationEventDetailFilters=[
                                {
                                    'eventArn': event['arn'],
                                    'awsAccountId': accountID
                                },
                            ]
                        ), cls=DatetimeEncoder))
                        json_event['datacenter'], json_event[
                            'geo_location'] = sapifiedregion.datacenter_name(json_event['region'], secret)
                        if len(description['successfulSet']) != 0:
                            json_event['communication'] = description['successfulSet'][0]['eventDescription'][
                                'latestDescription']
                        delete_octobus_entries(json_event['trackingID'], json_event["accountID"])
                        json_event['impactedResources'] = f"https://endpoint_url/s/c0030-home/app/discover#/view/b951b080-e418-11ed-b857-0f3b537ea62c?_g=(filters:!(),refreshInterval:(pause:!f,value:10000),time:(from:now-1y%2Fd,to:now))&_a=(columns:!(hyperscaler.keyword,environment.keyword,name.keyword,lob.keyword,resourceName.keyword,title.keyword,service.keyword,datacenter.keyword,accountID.keyword,org.keyword,trackingID.keyword,startTime),filters:!(),grid:(columns:(occurredTime:(width:210),summary.keyword:(width:100))),hideChart:!f,index:f5f1178d-29ed-49b6-8532-fa3e48766099,interval:auto,query:(language:kuery,query:'accountID.keyword%20:%20%22{json_event['accountID']}%22%20and%20trackingID.keyword%20:%20%22{json_event['trackingID']}%22%20'),sort:!())"
                            
                        if event.get("statusCode") != "closed":
                            send_data(json.dumps(json_event))

                        # filtering the events with statucode equal to closed which has endtime
                        else:
                            endTime = json_event["endTime"]
                            endTimeParser = parser.parse(endTime)
                            endTimeStampStr = endTimeParser.strftime('%Y-%m-%d %H:%M:%S')
                            json_event["endTime"] = endTimeParser.isoformat().split("+")[0] + "Z"
                            # calculating the no. of hours the issue persisted
                            endTimeEvent = datetime.datetime.strptime(endTimeStampStr[:19],
                                                                      '%Y-%m-%d %H:%M:%S')
                            impactDuration = (endTimeEvent - startTimeEvent).__str__()
                            json_event["impactDuration"] = impactDuration
                            send_data(json.dumps(json_event))
                else:
                    # json_event['level'] = json_event['eventTypeCategory']
                    json_event['level'] = "Issue"
                    json_event['name'] = 'All'
                    json_event['lob'] = 'All'
                    json_event['environment'] = 'All'
                    json_event["accountID"] = 'All'
                    json_event['datacenter'] = 'global'
                    del json_event['eventTypeCategory']
                    delete_octobus_global_entries(json_event['trackingID'])
                    send_data(json.dumps(json_event))


def send_data(finaljson):
    url = "https://endpoint_url/c0030/log/hyperscaler_healthevents"
    headers = {'Content-type': 'application/json'}
    results = requests.post(url, data=finaljson, headers=headers)
    print(results.reason)
    print("Response:", finaljson)


def delete_octobus_entries(trackingId, accountID):
    secret = get_secrets()
    api_url = 'https://endpoint_url/c_log_hyperscaler_healthevents/_delete_by_query'
    my_headers = {'Authorization': secret.get('elkapikey_euw4'),
                  'Content-Type': 'application/json'}
    delete_query = {
        "query": {
            "bool": {
                "must": [
                    {"match": {
                        "trackingID.keyword": trackingId
                    }
                    },
                    {
                        "match": {
                            "accountID.keyword": accountID
                        }
                    }
                ]
            }
        }
    }
    response = requests.post(api_url, headers=my_headers, json=delete_query).json()
    print("delete response :", response)


def delete_octobus_global_entries(trackingId):
    secret = get_secrets()

    api_url = 'https://endpoint_url/c_log_hyperscaler_healthevents/_delete_by_query'
    my_headers = {'Authorization': secret.get('elkapikey_euw4'),
                  'Content-Type': 'application/json'}
    delete_query = {
        "query": {
            "match": {
                "trackingID.keyword": trackingId
            }
        }
    }
    response = requests.post(api_url, headers=my_headers, json=delete_query).json()
    print("delete response count:", response)
