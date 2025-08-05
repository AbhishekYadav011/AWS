import boto3
import json

from botocore.exceptions import ClientError
from lambda_function import send_sla_data


def process(json_event, secret):
    print("Inside S3 file")
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

    s3Client = session.client("s3")
    list_buckets = s3Client.list_buckets()
    try:
        for bucket in list_buckets["Buckets"]:
            if s3Client.get_bucket_location(Bucket=bucket['Name'])['LocationConstraint'] == json_event["region"]:
                objects = s3Client.list_objects_v2(Bucket=bucket["Name"])
                json_event["bucketName"] = (bucket["Name"])
                if objects["KeyCount"] > 0:
                    for obj in objects["Contents"]:
                        objectKey = obj["Key"]
                        storageClass = obj["StorageClass"]
                        if storageClass == "INTELLIGENT_TIERING" or storageClass == "STANDARD_IA" or storageClass == "ONEZONE_IA" or storageClass == "GLACIER_IR":
                            # print("S3 SLA Calculation for S3 Intelligent-Tiering, S3 Standard-Infrequent Access, S3 One Zone-Infrequent Access, and S3 Glacier Instant Retrieval")
                            if float(98) <= json_event["monthlyUptimePercentage"] < float(99):
                                json_event["slaCreditAvailable"] = "Yes"
                                json_event["slaCredit"] = "10%"
                                json_event["objectName"] = objectKey
                                send_sla_data(json.dumps(json_event))
                            elif float(95) <= json_event["monthlyUptimePercentage"] < float(98):
                                json_event["slaCreditAvailable"] = "Yes"
                                json_event["slaCredit"] = "25%"
                                json_event["objectName"] = objectKey
                                send_sla_data(json.dumps(json_event))
                            else:
                                json_event["slaCreditAvailable"] = "Yes"
                                json_event["slaCredit"] = "100%"
                                json_event["objectName"] = objectKey
                                send_sla_data(json.dumps(json_event))
                        else:
                            if float(99) <= json_event["monthlyUptimePercentage"] < float(99.9):
                                json_event["slaCreditAvailable"] = "Yes"
                                json_event["slaCredit"] = "10%"
                                json_event["objectName"] = objectKey
                                send_sla_data(json.dumps(json_event))
                            elif float(95) <= json_event["monthlyUptimePercentage"] < float(99):
                                json_event["slaCreditAvailable"] = "Yes"
                                json_event["slaCredit"] = "25%"
                                json_event["objectName"] = objectKey
                                send_sla_data(json.dumps(json_event))
                            else:
                                json_event["slaCreditAvailable"] = "Yes"
                                json_event["slaCredit"] = "100%"
                                json_event["objectName"] = objectKey
                                send_sla_data(json.dumps(json_event))
    except ClientError as e:
        print("Unexpected error: %s" % e.response['Error']['Message'])