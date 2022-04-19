import aws_credentials
import logging

LOG_FILENAME = "logs"
logging.basicConfig(filename=LOG_FILENAME,format='%(asctime)s %(message)s', filemode='w')
logger=logging.getLogger()
logger.setLevel(logging.DEBUG)

try:
    session1 = aws_credentials.get_session()
    # model source
    dynamodb = session1.resource('dynamodb')

    # model objects
    user_info_table = dynamodb.Table('USER_INFO')
    survey_table = dynamodb.Table('SURVEY')
    complete_table = dynamodb.Table('COMPLETE_SURVEY')
    incomplete_table = dynamodb.Table('INCOMPLETE_SURVEY')
    open_survey_table = dynamodb.Table('OPEN_SURVEY')
    open_survey_response_table = dynamodb.Table('OPEN_SURVEY_RESPONSE')

except Exception as ae:
    logger.exception(ae)
        
def get_user_info_table():
    return dynamodb.Table('USER_INFO')

def get_survey_table():
    return dynamodb.Table('SURVEY')

def get_complete_table():
    return dynamodb.Table('COMPLETE_SURVEY')

def get_incomplete_table():
    return dynamodb.Table('INCOMPLETE_SURVEY')

def get_open_survey_table():
    return dynamodb.Table('OPEN_SURVEY')

def get_open_survey_response_table():
    return dynamodb.Table('OPEN_SURVEY_RESPONSE')