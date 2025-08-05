import base64
import boto3
import json
import logging
import pickle
import requests
import os
from re import search

from lambda_function import send_sla_data


def send_message(message, serviceID):
    try:
        with open("/tmp/services.txt", "a+") as f:
            mylist = f.read().splitlines() 
            services = []
            for line in mylist:
                services.append(line)
            if serviceID not in services:
                print(services)
                print("no match")
                with open("/tmp/services.txt", "a") as myfile:
                    myfile.write(serviceID+"\n")
                    slack_webhook_url = "https://hooks.chat.com/TA4JH1Q0H/"
                    response = requests.post(
                        slack_webhook_url, data=json.dumps(message),
                        headers={'Content-Type': 'application/json'}
                    )
                    if response.status_code != 200:
                        raise ValueError(
                            'Request to slack returned an error %s, the response is:\n%s'
                            % (response.status_code, response.text)
                        )
            else:
                print('service already exists in file')
    except Exception as e:
        # handle all other slack errors
        print(e.args)


def process(data):
    hyp = data['hyperscaler']
    monthlyUptimePercentage = data['monthlyUptimePercentage']
    serviceID = data['serviceID']
    try:
        print("Trying SLA DB")
        headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
        url = f'https://sladb/sla/{hyp}/projectname/{serviceID}'
        response = requests.get(url, headers=headers).json()
        if response['data']:
            for service in response['data']:
                # check if multiple sla configs returned, json contains sla_discounts and service_title so has to be > 2
                if (len(service['sla_discounts'])) > 2:
                    print("Error multiple configurations returned for simple sla")
                    msg = "Simple SLA - {} service for {} returning multiple configurations".format(serviceID, hyp)
                    logging.info(msg)
                    slackmsg = {"text": msg}
                    send_message(slackmsg, serviceID)
                else:
                    slaDiscountList = service['sla_discounts']['discount_data']
                    discount_logic(slaDiscountList, monthlyUptimePercentage, data)
        else:
            print("Simple SLA", serviceID, "not found")
    except ValueError as e:
        # if service not found in index, send error to slack
        print("SLA DB service not found")
        msg = "Simple SLA - {} service for {} not found".format(serviceID, hyp)
        logging.info(msg)
        slackmsg = {"text": msg}
        send_message(slackmsg, serviceID)
    except Exception as e:
        # handle all other errors, send error to slack
        print("SLA DB Failed")
        print(e.args)
        msg = "Simple SLA - {} service for {} error".format(serviceID, hyp)
        logging.info(msg)
        slackmsg = {"text": msg}
        send_message(slackmsg, serviceID)
        try:
            print("SLA DB Failed, using S3 Backup")
            s3_client = boto3.client(service_name='s3')
            response = s3_client.get_object(Bucket='sla-db-data', Key=f'{hyp}-sla-data.pkl')
            body = response['Body'].read()
            sla_data = pickle.loads(body)
            find_sla_item = next(item for item in sla_data if search(data['service'], item['sla_name']))
            slaDiscountList = [b for a in find_sla_item['sla_discounts'] for b in a['discount_data']]
            discount_logic(slaDiscountList, monthlyUptimePercentage, data)
        except Exception as e:
            # s3 backup failed, send error to slack
            msg = "S3 Backup Failed"
            logging.info(msg)
            print(e.args)
            slackmsg = {"text": msg}
            send_message(slackmsg, serviceID)


def discount_logic(slaDiscountList, monthlyUptimePercentage, data):
    serviceCreditList = []
    for uptime in slaDiscountList:
        if monthlyUptimePercentage < uptime['uptime_less_than']:
            print(uptime['service_credit'])
            serviceCreditList.append(uptime['service_credit'])
    if serviceCreditList:
        print(max(serviceCreditList))
        data['resourceName'] = 'simpleSla'
        data['slaCreditAvailable'] = 'Yes'
        data['slaCredit'] = str(max(serviceCreditList))+'%'
        send_sla_data(json.dumps(data))
