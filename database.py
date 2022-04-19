from flask import Flask, render_template, request, abort
from flask_ask import statement
from boto3.dynamodb.conditions import Key, Attr
import boto3
import aws_credentials
import yaml
import requests
import json
import functools
import uuid 

from dbconn import user_info_table, survey_table, complete_table, incomplete_table, open_survey_table, open_survey_response_table, logger



"""
    Get user info from cognito
"""
def get_user_info_from_cognito(req):
    accessToken = req["context"]["System"]["user"]["accessToken"]
    url = aws_credentials.USERINFO_ENDPOINT
    header = {
        "authorization": "Bearer " + accessToken
        }
    res = requests.get(url, headers=header)
    return res
    
"""
    Get Survey ID
"""
def get_user_survey_id(u_id, s_id):
    return str(u_id)+str(s_id)


"""
    Get User Info
"""
def get_user_info(id):
    id = str(id)
    response = user_info_table.get_item(
        Key={
            'USER_ID': id
        }
    )
    return response


"""
    Add new user
"""
def add_new_user(id, email):
    try:
        user_info_table.put_item(
            Item = {
                'USER_ID': id,
                'EMAIL': email,
                'COMPLETE': {},
                'INCOMPLETE': {},
                'OPT_OUT': {},
                'NAME': id,
                'PIN' : "1234",
                'LINKED': {},
            }
        )
        return True
    except Exception as ae:
        print(ae)
        logger.exception(ae)
        return False


"""
    Get Survey Info.
"""
def get_all_survey_info():
    response = survey_table.scan()
    return response

"""
    Get Preferred Surveys
"""
def get_preferred_survey(user_custom_id):
    user_info = get_user_info(user_custom_id)
    opt_out = user_info["Item"]["OPT_OUT"]
    fe = []
    if len(opt_out) > 0:
        for keyword in opt_out:
            fe.append(~Attr('KEYWORDS').contains(keyword))
        
        filterExpr = functools.reduce(lambda a,b : a & b, fe)
    
        response = survey_table.scan(
            FilterExpression = filterExpr        
        )
        return response
    else:
        return get_all_survey_info()
    

"""
    Get Survey Info
"""
def get_survey_info(id):
    id = str(id)
    response = survey_table.get_item(
        Key={
            'S_ID': id
        }
    )
    return response


"""
    Get question from DB
"""
def get_survey_question(survey_id, index):
    id = str(survey_id)
    index = int(index) - 1
    response = survey_table.get_item(
        Key={
            'S_ID': id
        }
    )
    item = response["Item"]
    question = item["QUESTIONS"][index]
    return question


"""
    Get Open Survey Info
"""
def get_open_survey_info(id):
    id = str(id)
    response = open_survey_table.get_item(
        Key={
            'OS_ID': id
        }
    )
    return response


"""
    Get open survey question from DB
"""
def get_open_survey_question(survey_id, index):
    id = str(survey_id)
    index = int(index) - 1
    response = open_survey_table.get_item(
        Key={
            'OS_ID': id
        }
    )
    item = response["Item"]
    question = item["QUESTIONS"][index]
    return question


"""
    Add record in incomplete table
"""
def add_record_incomplete_table(user_id, survey_id):
    user_survey_id = get_user_survey_id(user_id, survey_id)
    incomplete_table.put_item(Item={
        'I_ID': user_survey_id,
        'U_ID': user_id,
        'S_ID': survey_id,
        'FEEDBACK': [],
    })


"""
    Get record from incomplete table
"""
def get_record_incomplete_table(user_id, survey_id):
    user_survey_id = get_user_survey_id(user_id, survey_id)
    res = incomplete_table.get_item(
            Key={
                'I_ID':user_survey_id
            }
        )

    return res


"""
    add attempted questions in incomplete table
"""
def update_incomplete_table(user_id, survey_id, attempted):
    
    user_survey_id = get_user_survey_id(user_id, survey_id)
   
    incomplete_table.put_item(Item={
        'I_ID': user_survey_id,
        'U_ID': user_id,
        'S_ID': survey_id,
        'FEEDBACK': attempted 
    })


"""
    delete record from incomplete table
"""
def delete_record_incomplete_table(user_id, survey_id):
    user_survey_id = get_user_survey_id(user_id, survey_id)
     # Empty incomplete table
    incomplete_table.delete_item(Key={
                    'I_ID': user_survey_id
                })        
        

"""
    add survey to complete table
"""
def add_record_survey_complete(user_id, survey_id, attempted):
    user_survey_id = get_user_survey_id(user_id, survey_id)
    # Make entry in complete table
    complete_table.put_item(Item={
                'C_ID': user_survey_id,
                'U_ID': user_id,
                'S_ID': survey_id,
                'FEEDBACK': attempted,
            })





"""
    update user table surveys
"""
def update_user_table_survey(user_id, incomplete, complete=None):
    if complete is None:
        user_info_table.update_item(
                Key={
                    'USER_ID': user_id
                },
                UpdateExpression="set INCOMPLETE = :q",
                ExpressionAttributeValues={
                    ':q': incomplete,
                },
                ReturnValues="UPDATED_NEW"
            )
    else:
        user_info_table.update_item(
                Key={
                    'USER_ID': user_id
                },
                UpdateExpression="set INCOMPLETE = :val1, COMPLETE = :val2",
                ExpressionAttributeValues={
                    ':val1': incomplete,
                    ':val2': complete,
                },
                ReturnValues="UPDATED_NEW"  
            )




"""
    add completed survey in open survey table
"""
def add_open_survey_complete(survey_id, attempted):
    open_survey_response_table.put_item(Item={
        'OSR_ID': str(uuid.uuid1()),
        'OS_ID': survey_id,
        'FEEDBACK': attempted,
    })