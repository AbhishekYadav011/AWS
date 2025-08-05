import boto3
import json

from botocore.exceptions import ClientError

from lambda_function import send_sla_data


def process(json_event, secret):
    print("Inside EC2 file")
    if json_event['resourceName'] != "AWS_ACCOUNT":
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
        ec2Client = session.client("ec2", region_name=json_event["region"])
        autoscalingclient = session.client('autoscaling', region_name=json_event["region"])
        autoscalingclientResponse = autoscalingclient.describe_auto_scaling_instances(
            InstanceIds=[json_event['resourceName']])
        json_event['partOfAutoScalingGroup'] = 'Yes'
        if not autoscalingclientResponse['AutoScalingInstances']:
            json_event['partOfAutoScalingGroup'] = 'No'
            print('No autoscaling group')
        try:
            reservations = ec2Client.describe_instances(InstanceIds=[json_event['resourceName']]).get("Reservations")
            for reservation in reservations:
                # declaring all the variables
                for instance in reservation["Instances"]:
                    availabilityZone = instance["Placement"]["AvailabilityZone"]
                    if instance["InstanceId"] == json_event["resourceName"]:
                        # check Instace-Level SLA only
                        if json_event["monthlyUptimePercentage"] < float(99.5):
                            print("EC2 SLA credit available")
                            json_event["slaCreditAvailable"] = "Yes"
                            if float(99) < json_event["monthlyUptimePercentage"] < float(99.5):
                                json_event["slaCredit"] = "10%"
                                send_sla_data(json.dumps(json_event))
                            if float(95) < json_event["monthlyUptimePercentage"] < float(99):
                                json_event["slaCredit"] = "30%"
                                send_sla_data(json.dumps(json_event))
                            if json_event["monthlyUptimePercentage"] < float(95):
                                json_event["slaCredit"] = "100%"
                                send_sla_data(json.dumps(json_event))
        except ClientError as e:
            print("Unexpected error: %s" % e.response['Error']['Message'])
