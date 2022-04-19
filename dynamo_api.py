from flask import Blueprint, request, jsonify, Response
import database as db
import json
import decimal

db_api = Blueprint('db_api', __name__)

# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        if isinstance(o, set):  #<---resolving sets as lists
            return list(o)
        return super(DecimalEncoder, self).default(o)



######################################
############ USER TABLE  #############
######################################
@db_api.route('/get_user_info/<userId>', methods=['GET'])
def get_user_info(userId):
    try:
        response = db.get_user_info(userId)
        return json.dumps((response), indent=4, cls=DecimalEncoder)
    except Exception as ae:
        return Response("Flask server error: " + str(ae), status=400)


@db_api.route('/add_user', methods=['POST'])
def post_user_info():
    try:
        data = request.get_json()
        uid = str(data['user_id'])
        email = str(data['email_id'])
        response = db.add_new_user(uid, email)
        return jsonify(True)
    except Exception as ae:
        return Response("Flask server error: " + str(ae), status=400)  


@db_api.route('/get_user_surveys/<userId>', methods=['GET'])
def get_preferred_survey(userId):
    try:
        response = db.get_preferred_survey(userId)    
        return json.dumps((response), indent=4, cls=DecimalEncoder)
    except Exception as ae:
        return Response("Flask server error: " + str(ae), status=400)


# Add incomplete survey in user profile
@db_api.route('/add_incomplete_in_user_profile', methods=['POST'])
def add_incomplete_in_user_profile():
    try:
        data = request.get_json()
        user_id = data['user_id']
        survey_id = data['survey_id']
        
        res = db.get_survey_info(survey_id)
        survey_name = res["Item"]["NAME"]

        u_info = db.get_user_info(user_id)
        in_survey = u_info["Item"]["INCOMPLETE"] 
        in_survey[survey_id] = survey_name
        
        response = db.update_user_table_survey(user_id, in_survey)    
        return jsonify(True)
    except Exception as ae:
        return Response("Flask server error: " + str(ae), status=400)


# Add complete survey in user profile
# this will remove from incomplete listing and put it complete listing
@db_api.route('/add_complete_in_user_profile', methods=['POST'])
def add_complete_in_user_profile():
    try:
        data = request.get_json()
        user_id = data['user_id']
        survey_id = data['survey_id']
        
        res = db.get_survey_info(survey_id)
        survey_name = res["Item"]["NAME"]

        u_info = db.get_user_info(user_id)

        # remove from incomplete listing
        in_survey = u_info["Item"]["INCOMPLETE"] 
        in_survey.pop(survey_id, None)

        # put in complete listing
        com_survey = u_info["Item"]["COMPLETE"]
        com_survey[survey_id] = survey_name
        
        response = db.update_user_table_survey(user_id, in_survey, com_survey)    
        return jsonify(True)
    except Exception as ae:
        return Response("Flask server error: " + str(ae), status=400)


######################################
############ SURVEY TABLE  #############
######################################
@db_api.route('/get_all_surveys', methods=['GET'])
def get_all_survey_info(userId):
    try:
        response = db.get_all_survey_info()
        return json.dumps((response), indent=4, cls=DecimalEncoder)
    except Exception as ae:
        return Response("Flask server error: " + str(ae), status=400)


@db_api.route('/get_survey_info/<surveyId>', methods=['GET'])
def get_survey_info(surveyId):
    try:
        response = db.get_survey_info(surveyId)
        return json.dumps((response), indent=4, cls=DecimalEncoder)
    except Exception as ae:
        return Response("Flask server error: " + str(ae), status=400)





######################################
############ OPEN SURVEY TABLE  #############
######################################

@db_api.route('/get_open_survey_info/<surveyId>', methods=['GET'])
def get_open_survey_info(surveyId):
    try:
        response = db.get_open_survey_info(surveyId)
        return json.dumps((response), indent=4, cls=DecimalEncoder)
    except Exception as ae:
        return Response("Flask server error: " + str(ae), status=400)


@db_api.route('/add_open_survey_feedback', methods=['POST'])
def add_open_survey_complete():
    try:
        data = request.get_json()
        sid = str(data['survey_id'])
        feedback = json.loads(json.dumps(data['feedback']))
        response = db.add_open_survey_complete(sid, feedback)
        return jsonify(True)
    except Exception as ae:
        return Response("Flask server error: " + str(ae), status=400)




#########################################
############ INCOMPLETE TABLE #############
#########################################

@db_api.route('/add_incomplete_record', methods=['POST'])
def add_record_incomplete_table():
    try:
        data = request.get_json()
        user_id = data['user_id']
        survey_id = data['survey_id']
        response = db.add_record_incomplete_table(user_id, survey_id)    
        return jsonify(True)
    except Exception as ae:
        return Response("Flask server error: " + str(ae), status=400)



@db_api.route('/get_incomplete_record/user/<user_id>/survey/<survey_id>', methods=['GET'])
def get_record_incomplete_table(user_id, survey_id):
    try:
        response = db.get_record_incomplete_table(user_id, survey_id)    
        return json.dumps((response), indent=4, cls=DecimalEncoder)
    except Exception as ae:
        return Response("Flask server error: " + str(ae), status=400)


@db_api.route('/update_incomplete_record', methods=['PUT'])
def update_record_incomplete_table():
    try:
        data = request.get_json()
        user_id = data['user_id']
        survey_id = data['survey_id']
        feedback = json.loads(json.dumps(data['feedback']))
        response = db.update_incomplete_table(user_id, survey_id, feedback)    
        return jsonify(True)
    except Exception as ae:
        return Response("Flask server error: " + str(ae), status=400)



@db_api.route('/delete_incomplete_record', methods=['DELETE'])
def delete_record_incomplete_table():
    try:
        data = request.get_json()
        user_id = data['user_id']
        survey_id = data['survey_id']
        response = db.delete_record_incomplete_table(user_id, survey_id)    
        return jsonify(True)
    except Exception as ae:
        return Response("Flask server error: " + str(ae), status=400)


######################################
############ COMPLETE TABLE  #############
######################################


@db_api.route('/add_complete_record', methods=['POST'])
def add_record_survey_complete():
    try:
        data = request.get_json()
        user_id = data['user_id']
        survey_id = data['survey_id']
        feedback = json.loads(json.dumps(data['feedback']))
        response = db.add_record_survey_complete(user_id, survey_id, feedback)    
        return jsonify(True)
    except Exception as ae:
        return Response("Flask server error: " + str(ae), status=400)

