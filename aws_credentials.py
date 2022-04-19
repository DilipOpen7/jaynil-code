import boto3
import logging


def get_session():
    session1 = boto3.Session(profile_name='default')
    return session1

def get_ses_client():
    client = boto3.client(service_name = 'ses', region_name = 'us-east-1', aws_access_key_id = 'AKIAYM2WHP5AXK2MU3OY', aws_secret_access_key = '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')
    return client

USER_POOL_DOMAIN = "https://openeyessurvey.auth.us-east-1.amazoncognito.com/"
USERINFO_ENDPOINT = USER_POOL_DOMAIN + '/oauth2/userInfo'