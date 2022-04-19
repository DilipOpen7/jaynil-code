import smtplib
import aws_credentials 
import boto3
from coreapi import codecs
import codecs
from bs4 import BeautifulSoup
import re

def get_tables(ID):

    
    session1 = aws_credentials.get_session()
    dynamodb = session1.resource('dynamodb')
    global notification_log_table, user_info_table, survey_info_table, email_templates_table
    notification_log_table = dynamodb.Table('NOTIFICATION_LOG')
    user_info_table = dynamodb.Table('USER_INFO')
    email_templates_table = dynamodb.Table('TEMPLATES')
    survey_info_table = dynamodb.Table('SURVEY')
    
def get_user_info(ID):

    response = user_info_table.get_item(
        Key={
            'USER_ID':ID 
        }
    )
    global user_info
    
    user_info = response["Item"]
    return user_info

def create_log_user(ID, user_info):
    notification_log_table.put_item(Item={
                        'USER_ID': ID,
                        'EMAIL': user_info["EMAIL"],
                        'LOGS':[]
    })

def log_notification(ID, subject, survey_name, survey_ID, message, result):
    response = notification_log_table.get_item(
        Key={
            'USER_ID':ID 
        }
    )
    items = response["Item"]
    logs = items["LOGS"]
    
    if survey_ID==None:
        survey_ID='Not Required'
        survey_name='Not Required'
    
    info = dict()
    info["subject"] = subject
    info["survey_name"] = survey_name
    info["survey_ID"] = survey_ID
    info["message"] = message
    info["sent_history"] = result

    logs.append(info)
 
    response = notification_log_table.update_item(
            Key={
                'USER_ID': ID
            },
            UpdateExpression="set LOGS = :q",
            ExpressionAttributeValues={
                ':q': logs,
            },
            ReturnValues="UPDATED_NEW"
    )

def notification_log(ID, receiver, subject, survey_name, survey_ID, message, result):

    notification_log_info = notification_log_table.get_item(
        Key={
            'USER_ID':ID 
        }
    )
    if "Item" not in notification_log_info:
        create_log_user(ID, user_info)
        log_notification(ID, subject, survey_name, survey_ID, message, result)
    else:
        log_notification(ID, subject, survey_name, survey_ID, message, result)

def get_survey_info(survey_ID):
    try:
        response = survey_info_table.get_item(
            Key={
                'S_ID': survey_ID 
            }
        )
        
        items = response['Item']
        survey_name = items['NAME']

        return survey_name

    except Exception as ae:
        print(ae)

def get_mail_template(type1):
    try:
        response = email_templates_table.get_item(
            Key={
                'TYPE': type1 
            }
        )
        items = response['Item']
        subject = items['SUBJECT']
        message = items['MESSAGE']

        return subject, message

    except Exception as ae:
        print(ae)

def send_mail(ID, type1, survey_ID=None):

    try:
        senderusername = "AKIAYM2WHP5A24TCFZEO"
        password = "BIE00elyRfmrUBjJTiC9JCxAyHCUrluxkzfmdRcCWNi/"
        sender = "support@openeyessurvey.com"
        get_tables(ID)
        user_info = get_user_info(ID)
        receiver = user_info["EMAIL"]
        if survey_ID!=None:
            survey_name = get_survey_info(survey_ID)
        else:
            survey_name = 'Not Required'
        

        path = "templates/"
        if type1 == "login":
            file = codecs.open(path + "AI - Successful SignIn.html", "r", "utf-8")
            data = file.read()
            
            soup = BeautifulSoup(data, features="lxml")
            target = soup.find_all(text=re.compile(r'FirstNameOfTheUser'))
            for v in target:
                v.replace_with(v.replace('FirstNameOfTheUser',receiver))
            data = str(soup)
            
        elif type1 == "signup":
            file = codecs.open(path + "AI - Sign Up.html", "r", "utf-8")
            data = file.read()

        elif type1 == "activity":
            file = codecs.open(path + "AI - Suspicious Activity.html", "r", "utf-8")
            data = file.read()

            soup = BeautifulSoup(data, features="lxml")
            target = soup.find_all(text=re.compile(r'FirstNameOfTheUser'))
            for v in target:
                v.replace_with(v.replace('FirstNameOfTheUser',receiver))

            data = str(soup)

        elif type1 == "completed":
            file = codecs.open(path + "AI - Survey Completed.html", "r", "utf-8")
            data = file.read()
            
            soup = BeautifulSoup(data, features="lxml")
            target = soup.find_all(text=re.compile(r'FirstNameOfTheUser'))
            for v in target:
                v.replace_with(v.replace('FirstNameOfTheUser',receiver))
            
            target = soup.find_all(text=re.compile(r'Survey Name'))
            for v in target:
                v.replace_with(v.replace('Survey Name',survey_name))

            data = str(soup)

        elif type1 == "incomplete":
            file = codecs.open(path + "AI - Survey InComplete.html", "r", "utf-8")
            data = file.read()

        elif type1 == "optin":
            file = codecs.open(path + "AI - OptIn.html", "r", "utf-8")
            data = file.read()

            soup = BeautifulSoup(data, features="lxml")
            target = soup.find_all(text=re.compile(r'FirstNameOfTheUser'))
            for v in target:
                v.replace_with(v.replace('FirstNameOfTheUser',receiver))
    
            data = str(soup)

        elif type1 == "optout":
            file = codecs.open(path + "AI - Opt Out.html", "r", "utf-8")
            data = file.read()

            soup = BeautifulSoup(data, features="lxml")
            target = soup.find_all(text=re.compile(r'FirstNameOfTheUser'))
            for v in target:
                v.replace_with(v.replace('FirstNameOfTheUser',receiver))
    
            data = str(soup)


        
        mail_data = get_mail_template(type1)
        client = aws_credentials.get_ses_client()
        result = client.send_email(
            Source=sender,
            Destination={
                'ToAddresses': [
                    receiver,
                ],
            },
            Message={
                'Subject': {
                    'Data': mail_data[0],
                    'Charset': 'utf-8'
                },
                'Body': {
                    'Html': {
                        'Data': data,
                        'Charset': 'utf-8'
                    }
                }
            }
        )
        notification_log(ID, receiver, mail_data[0], survey_name, survey_ID, mail_data[1], result)
    except Exception as ae:
        print(ae)

if __name__ == "__main__":
    send_mail('1011', 'completed', survey_ID='101')