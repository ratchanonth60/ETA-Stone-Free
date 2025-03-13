import boto3
from django.conf import settings

sns = boto3.client(
    "sns",
    region_name=settings.AWS_EMAIL_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
)

ses = boto3.client(
    "ses",
    region_name=settings.AWS_EMAIL_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
)

sesv2 = boto3.client(
    "sesv2",
    region_name=settings.AWS_EMAIL_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
)


def send_email(to, subject, body):
    response = ses.send_email(
        Destination={"ToAddresses": [to]},
        Message={
            "Body": {"Text": {"Charset": "UTF-8", "Data": body}},
            "Subject": {"Charset": "UTF-8", "Data": subject},
        },
        Source=settings.DEFAULT_FROM_EMAIL,
    )
    return response


def send_email_v2(to, subject, body):
    response = sesv2.send_email(
        Destination={"ToAddresses": [to]},
        Content={
            "Simple": {
                "Body": {"Text": {"Charset": "UTF-8", "Data": body}},
                "Subject": {"Charset": "UTF-8", "Data": subject},
            }
        },
        FromEmailAddress=settings.DEFAULT_FROM_EMAIL,
    )
    return response
