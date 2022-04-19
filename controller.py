from flask import Flask, render_template, request
import flask_ask
import database
import email_notification
from dbconn import user_info_table, logger
import math
import json

from directives import *



"""
    Helper functions
"""

def digitToOrdinal(i):
    d = {"1": "first", "2": "second", "3": "third", "4": "fourth", "5": "fifth", "6": "sixth", "7": "seventh", "8th": "eighth", "9th": "nineth"}
    i = str(i)
    if i not in d.keys():
        return "%d%s"
    return d[i]

def ordinalToDigit(ord):
    d = {"first": "1","second": "2", "third": "3", "fourth": "4", "fifth": "5", "sixth": "6", "seventh": "7"}
    if ord not in d.keys():
        return None
    return d[ord]

questionNumberOrdinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(math.floor(n/10)%10!=1)*(n%10<4)*n%10::4])

"""
    Account Linking
"""
"""
    Authorize users using access token
"""
def accountLinking(session, jsonRequest):
    req = jsonRequest.json
    if "accessToken" in req["context"]["System"]["user"].keys():
        res = database.get_user_info_from_cognito(req)
        if res.status_code == 200:
            # access token valid
            res = res.json()
            email = res["email"]
            username = res["username"]
            response = database.get_user_info(username)
            if "Item" not in response:
                valid = database.add_new_user(username, email)
            session.attributes["user_custom_id"] = username
            session.attributes["username"] = username
            # Pin removed so does not matter
            session.attributes["login_attempts"] = 0
            session.attributes["auth"] = True
            return True
        else:
            # access token invalid
            return False
    else:
        # no access token provided
        return False



"""
    Home and greet
"""
def navigate_home(session, item = None):
    try:
        # if NO user info is passed, fetch it from database 
        if item is None:
            response = database.get_user_info(session.attributes["user_custom_id"])
            item = response["Item"]

        incomplete_count = len(item["INCOMPLETE"])
        incomplete_survey = item["INCOMPLETE"]
        complete_survey = item["COMPLETE"]
        linked = item["LINKED"]

        complete_s_id = set({})
        for sur_id in complete_survey:
            complete_s_id.add(sur_id)

        incomplete_s_id = set({})
        for sur_id in incomplete_survey:
            incomplete_s_id.add(sur_id)

        # fetch all surveys
        all_survey = database.get_preferred_survey(session.attributes["user_custom_id"])

        final_list_survey = []
        for survey in all_survey["Items"]:
            if survey["S_ID"] in linked:
                final_list_survey.append(survey)

        new_survey_count = 0
        for survey in final_list_survey:
            if (survey["S_ID"] not in complete_s_id) and (survey["S_ID"] not in incomplete_s_id):
                new_survey_count += 1

        session.attributes["user_state"] = "HOME"
        greet = render_template("dashboard_stats")
        # You have {} incomplete survey and {} Invited survey. Which survey would you like to take?
        greet = greet.format(new_survey_count, incomplete_count)
        return greet
    except Exception as ae:
        logger.exception(ae)
        return render_template("except") + " navigate home 2"

"""
    Survey Type validation
"""
def getSurveyType(session, survey_type):
    try:
        valid_survey_type = {
            "new survey": "new survey",
            "new surveys": "new survey",
            "new": "new survey",
            "invited survey": "new survey",
            "first one": "new survey",
            "former": "new survey",
            "incomplete survey": "incomplete survey",
            "incomplete surveys": "incomplete survey",
            "incomplete": "incomplete survey",
            "latter": "incomplete survey",
            "remaining survey": "incomplete survey",
            "second one": "incomplete survey",
        }

        if survey_type.lower() in valid_survey_type.keys():
            return True, valid_survey_type[survey_type]
        else:
            return False, ""
    except Exception as ae:
        logger.exception(ae)
        return True, render_template("except") + " survey type"

"""
    new survey
"""
def newSurvey(session):
    try:
        all_survey = database.get_preferred_survey(session.attributes["user_custom_id"])
        user_info = database.get_user_info(session.attributes["user_custom_id"])
        complete_survey = user_info["Item"]["COMPLETE"]
        incomplete_survey = user_info["Item"]["INCOMPLETE"]
        # complete_survey:  {'101': 'ATS', '102': 'ATS2'}
        
        # Surveys Linked to user
        linked = user_info["Item"]["LINKED"]

        final_list_survey = []
        for survey in all_survey["Items"]:
            if survey["S_ID"] in linked:
                final_list_survey.append(survey)


        complete_s_id = set({})
        for sur_id in complete_survey:
            complete_s_id.add(sur_id)
        incomplete_s_id = set({})
        for sur_id in incomplete_survey:
            incomplete_s_id.add(sur_id)
        
        card_string = "Here are some new surveys for you.\n"
        speech = render_template("new_survey")+"\n"
        survey_found = False
        survey_mapping = {}
        i = 0
        for survey in final_list_survey:
            if (survey["S_ID"] not in complete_s_id) and (survey["S_ID"] not in incomplete_s_id):
                survey_found = True
                
                card_string += " "
                card_string += str(i+1) + ") "
                card_string += survey["NAME"]
                card_string += "\n"
                if i < 3:
                    speech += " "
                    speech += str(i+1) + ") "
                    speech += survey["NAME"]
                    speech += ", "
                # survey options to store in session
                survey_mapping[i+1] = {"name": survey["NAME"], "id": survey["S_ID"]}
                i = i + 1

        if survey_found:
            speech = speech[:-2] + ". " # remove comma and add period
            speech += render_template("check_app_for_more_survey")
            card_string += "(Please speak one option)"
        else:
            speech = render_template("no_new_survey")
            card_string = ""
        
        session.attributes["survey_type"] = "NEW"
        session.attributes["user_state"] = "NEW_SURVEY"
        session.attributes["survey_mapping"] = survey_mapping
        session.attributes["card_string"] = card_string
        return speech, card_string

    except Exception as ae:
        logger.exception(ae)
        return render_template("except") + " new survey", ""



"""
    incomplete survey
"""
def incompleteSurvey(session):
    try:
        user_info = database.get_user_info(session.attributes["user_custom_id"])
        incomplete_survey = user_info["Item"]["INCOMPLETE"]
    
        if len(incomplete_survey) == 0:
            return render_template("no_incomplete_survey"), ""


        card_string = "You have following incomplete survey:\n"
        speech = render_template("incomplete_survey")+"\n"
        i = 0
        survey_mapping = {}
        for s_id, s_name in incomplete_survey.items():
            card_string += " "
            card_string += str(i+1) + ") "
            card_string += s_name
            card_string += "\n"
            if i < 3:
                speech += " "
                speech += str(i+1) + ") "
                speech += s_name
                speech += ", "
            survey_mapping[i+1] = { "name": s_name, "id": s_id }

            i = i + 1
            

        speech = speech[:-2] + ". "
        speech += render_template("check_app_for_more_survey")
        
        card_string += "(Please speak one option)"
        #return speech, card_string, survey_mapping
        
        session.attributes["survey_type"] = "OLD"
        session.attributes["user_state"] = "OLD_SURVEY"
        session.attributes["survey_mapping"] = survey_mapping
        session.attributes["card_string"] = card_string
        return speech, card_string
    except Exception as ae:
        logger.exception(ae)
        return render_template("except") + " incomplete survey", ""


def getMandatoryQuestion(res):
    questions = res["Item"]["QUESTIONS"]
    mandatory_questions = 0
    for ques in questions:
        if "optional" in ques.keys():
            if not ques["optional"]:
                mandatory_questions += 1
        else:
            mandatory_questions += 1
    return mandatory_questions


"""
    start survey
""" 
def startSurvey(session, survey_option):
    try:
        session.attributes["user_state"] = "SURVEY_INPROGRESS"
        survey_id = session.attributes['survey_mapping'][survey_option]["id"]
        survey_name = session.attributes['survey_mapping'][survey_option]["name"]
        session.attributes["survey_id"] = survey_id
        session.attributes["survey_name"] = survey_name


        u_inf = database.get_user_info(session.attributes["user_custom_id"])
        # Check survey already completed or not.
        com_survey = u_inf["Item"]["COMPLETE"]
        if survey_id in com_survey.keys():
            return render_template("already_completed")

        # User directly speaks survey name 
        if session.attributes["survey_type"] is None:
            in_survey = u_inf["Item"]["INCOMPLETE"]
            if survey_id in in_survey.keys():
                session.attributes["survey_type"] == "OLD"
            else:
                session.attributes["survey_type"] == "NEW"

    
        # New survey
        if session.attributes["survey_type"] == "NEW":

            # set incomplete table
            database.add_record_incomplete_table(session.attributes["user_custom_id"], session.attributes["survey_id"])
        

            # set incomplete in user_data table
            u_info = database.get_user_info(session.attributes["user_custom_id"])
            
            
            in_survey = u_info["Item"]["INCOMPLETE"] 
            in_survey[session.attributes["survey_id"]] = survey_name

            # update incomplete surveys in user table
            database.update_user_table_survey(session.attributes["user_custom_id"], in_survey)
            
            res = database.get_survey_info(session.attributes["survey_id"])

            # Prepare attributes for survey
            session.attributes["progress"] = 1
            session.attributes["survey_name"] = survey_name
            session.attributes["mandatory_questions"] = getMandatoryQuestion(res)
            session.attributes["total_questions"] = len(res["Item"]["QUESTIONS"])
            session.attributes["optional_message"] = res["Item"]["OPTIONAL_MESSAGE"]
            session.attributes["complete_message"] = res["Item"]["COMPLETE_MESSAGE"]
            session.attributes["attempted"] = []

        
            instruction = "Alright, let's begin " + survey_name + ". " + res["Item"]["DESCRIPTION"] + " "
            instruction += render_template('instructions_for_new_survey', total_questions= session.attributes["total_questions"])
            
            return instruction
            
        else:
            #incomplete survey 
            response = database.get_record_incomplete_table(session.attributes["user_custom_id"], session.attributes["survey_id"])
                    
            if "Item" in response.keys():
                # response["Item"]["FEEDBACK"] = ast.literal_eval(response["Item"]["FEEDBACK"]) # Convert str repr of list to list type
                response["Item"]["FEEDBACK"] = response["Item"]["FEEDBACK"]
                item = response["Item"]
            else:
                item = {"FEEDBACK": []}
            
            res = database.get_survey_info(session.attributes["survey_id"])

            # Prepare attributes to start survey
            progress = len(item["FEEDBACK"]) + 1
            question_left = len(res["Item"]["QUESTIONS"]) + 1 - progress
            session.attributes["progress"] = progress
            session.attributes["survey_name"] = survey_name
            session.attributes["mandatory_questions"] = getMandatoryQuestion(res)
            session.attributes["total_questions"] = len(res["Item"]["QUESTIONS"])
            session.attributes["optional_message"] = res["Item"]["OPTIONAL_MESSAGE"]
            session.attributes["complete_message"] = res["Item"]["COMPLETE_MESSAGE"]
            # copy previous responses
            session.attributes["attempted"] = item["FEEDBACK"]
            instruction = "Alright, let's continue with " + survey_name + ". " + res["Item"]["DESCRIPTION"] + " "
            instruction += "You have {} question left. ".format(question_left) 

            if session.attributes["progress"] > session.attributes["mandatory_questions"]:
                instruction += " All these questions are optional. Please say Yes, to proceed, otherwise say No, to complete the survey."
            else:
                # instruction += render_template("instructions_for_incomplete_survey")
                instruction += " Okay?"
            if question_left == 0:
                session.attributes["user_state"] = "SURVEY_COMPLETE"
                return render_template("prompt_survey_review")
                
            return instruction
    except Exception as ae:
            logger.exception(ae)
            return render_template("except") + " start survey"



"""
    start open survey
"""
def startOpenSurvey(session, request, survey_id):
    try:
        if not survey_id.isnumeric():
            session.attributes["o_survey_id_attempts"] = 1
            return "You gave me invalid survey id. Survey id should be a number. Please tell me your survey id again."

        res = database.get_open_survey_info(survey_id)

        # Verify survey Id 
        if 'Item' not in res.keys():
            if "o_survey_id_attempts" not in session.attributes.keys():
                session.attributes["o_survey_id_attempts"] = 1
            else:
                session.attributes["o_survey_id_attempts"] += 1
            return render_template("o_invalid_survey_id_{}_attempt".format(
                digitToOrdinal(session.attributes["o_survey_id_attempts"])
                )).format(survey_id)
        else:
            session.attributes["o_survey_id_attempts"] = 1

        # Prepare attributes to start survey
        session.attributes["user_state"] = "OPEN_SURVEY_INPROGRESS"
        session.attributes["survey_id"] = survey_id
        session.attributes["progress"] = 1
        survey_name = res["Item"]["NAME"]
        survey_des = res["Item"]["DESCRIPTION"]
        time = res["Item"]["TIME"]
        session.attributes["survey_name"] = survey_name
        session.attributes["attempted"] = []
        session.attributes["mandatory_questions"] = getMandatoryQuestion(res)
        session.attributes["total_questions"] = len(res["Item"]["QUESTIONS"])
        session.attributes["optional_message"] = res["Item"]["OPTIONAL_MESSAGE"]
        session.attributes["complete_message"] = res["Item"]["COMPLETE_MESSAGE"]


        """
            --- Short Survey intro ---
            Commented for RPC 
        """
        # instruction = "Alright, let's begin " + survey_name + ". " + survey_des + " "
        # instruction += render_template('instructions_for_new_survey', total_questions= session.attributes["total_questions"])
        """
            --END--
        """

        instruction = f"Let's begin {time} survey about {session.attributes['survey_name']}. Okay?"
        return instruction

    except Exception as ae:
        logger.exception(ae)
        return render_template("except") + " start open survey"


"""
    next question
"""
def nextQuestion(session):
    try:
        progress = session.attributes["progress"]
        if progress < 0:
            return render_template("fallback1")  
        survey_id = session.attributes["survey_id"]
    
        if session.attributes["user_state"] == "OPEN_SURVEY_INPROGRESS":
            ques = database.get_open_survey_question(survey_id, progress)
        elif session.attributes["user_state"] == "SURVEY_INPROGRESS":
            ques = database.get_survey_question(survey_id, progress)
        else:
            # LOL, how did you reach here?
            return ""    
        
        # storing the current question in the session so that it can reused later, without retrieving from the database
        session.attributes["current_question"] = ques
        session.attributes["question_asked"] = True
        return ques
    except Exception as ae:
        logger.exception(ae)
        return render_template("except") + " next question"



"""
    record answer
"""
def recordAnswer(session, feedback, progress=None):
    
    try:
        ########## INVITED SURVEYS ###############
        if session.attributes["user_state"] == "SURVEY_INPROGRESS" or session.attributes["user_state"] == "SURVEY_COMPLETE": 

            # Change feedback of an attempted question
            if progress is not None:
                # progress validation
                if progress < 0:
                    return True, render_template("fallback1") 

                # Get question from attempted question
                ques = session.attributes["attempted"][progress-1]["question"]

                # Check for feedback validation according to question type
                valid, res = feedbackValidation(ques, feedback)
                
                if not valid:
                    return False, res

                # Change feedback of an attempted question by updating the attempted
                # update attempted
                session.attributes["attempted"][progress-1]["feedback"] = feedback
                return True, ""


            # When survey in progress
            if progress is None:
                progress = session.attributes["progress"]
                
                # progress validation
                if progress < 0:
                    return True, render_template("fallback1") 

                # Get question from session
                ques = session.attributes["current_question"]

                # Check for feedback validation according to question type
                valid, res = feedbackValidation(ques, feedback)

                if not valid:
                    return False, res

                # Converting to string to avoid "Object of type 'Decimal' is not JSON serializable"
                attempt = {"question_no": str(progress), "question": ques, "feedback": str(feedback)}

                # Handle first response
                if "attempted" not in session.attributes.keys():
                    session.attributes["attempted"] = [attempt]

                # After first response
                else:
                    session.attributes["attempted"].append(attempt)

            
            # Check for survey completion
            if session.attributes["progress"] == session.attributes["total_questions"]:
                database.update_incomplete_table(session.attributes["user_custom_id"], session.attributes["survey_id"], json.loads(json.dumps(session.attributes["attempted"])))
                

                session.attributes["user_state"] = "SURVEY_COMPLETE"
                session.attributes["current_question"] = None
                session.attributes["question_asked"] = False
                res = f"You answered {feedback}. "
                res += render_template("prompt_survey_review")
                return True, res

            else:
            
                # Update incomplete table 
                database.update_incomplete_table(session.attributes["user_custom_id"], session.attributes["survey_id"], json.loads(json.dumps(session.attributes["attempted"])))
                

                # Remove the question from session
                session.attributes["current_question"] = None
                # Update the progress
                session.attributes['progress'] += 1
                session.attributes["question_asked"] = False
                # Built response
                res = f"You answered {feedback}. <break time='1s'/>"

                # Optional questions started. Prompt user to continue or submit
                if session.attributes['progress'] == session.attributes['mandatory_questions'] + 1:
                    res += session.attributes["optional_message"]
                    return True, res

                res += "Are you ready for next question? "
            return True, res



        ######################################################
        ########## OPEN SURVEYS ############
        ######################################################

        elif session.attributes["user_state"] == "OPEN_SURVEY_INPROGRESS" or session.attributes["user_state"] == "OPEN_SURVEY_COMPLETE":
           
            
            # Change feedback of an attempted question
            if progress is not None:
                # progress validation
                if progress < 0:
                    return True, render_template("fallback1") 

                # Get question from attempted question
                ques = session.attributes["attempted"][progress-1]["question"]

                # Check for feedback validation according to question type
                valid, res = feedbackValidation(ques, feedback)
                
                if not valid:
                    return False, res

                # Change feedback of an attempted question by updating the attempted
                # update attempted
                session.attributes["attempted"][progress-1]["feedback"] = feedback
                return True, ""

                
            # When survey in progress
            if progress is None:
                progress = session.attributes["progress"]
                
                # progress validation
                if progress < 0:
                    return True, render_template("fallback1") 

                # Get question from session
                ques = session.attributes["current_question"]

                # Check for feedback validation according to question type
                valid, res = feedbackValidation(ques, feedback)

                if not valid:
                    return False, res

                # Converting to string to avoid "Object of type 'Decimal' is not JSON serializable"
                attempt = {"question_no": str(progress), "question": ques, "feedback": str(feedback)}

                # Handle first response
                if "attempted" not in session.attributes.keys():
                    session.attributes["attempted"] = [attempt]

                # After first response
                else:
                    session.attributes["attempted"].append(attempt)




            # Check for survey completion
            if session.attributes["progress"] == session.attributes["total_questions"]:
            
                session.attributes["user_state"] = "OPEN_SURVEY_COMPLETE"
                session.attributes["current_question"] = None
                session.attributes["question_asked"] = False

                # res = f"You answered, {feedback}. <break time='1s'/>"
                res = render_template("prompt_o_survey_review")
                return True, res
            
            else:
                # Remove the question from session
                session.attributes["current_question"] = None

                # Update the progress
                session.attributes['progress'] += 1

                session.attributes["question_asked"] = False
                
                # Build response
                # res = f"You answered {feedback}. "
                
                # Optional questions started
                if session.attributes['progress'] == session.attributes['mandatory_questions'] + 1:
                    res += session.attributes["optional_message"]
                    return True, res
                
                res = "Are you ready for next question? "
                return True, res
        else:
            return True, render_template("fallback1")

    except Exception as ae:
        logger.exception(ae)
        return True, render_template("except") + " record answer"
    


def feedbackValidation(ques, feedback):
    if ques["type"] == "MCQ":
        if not feedback.isnumeric():
            invalid_opt = render_template('invalid_mcq_option')
            return False, invalid_opt           

        feedback = int(feedback)
        if feedback < 1 or feedback > len(ques['options']):
            invalid_rating = render_template("invalid_mcq_option")
            return False, invalid_rating

    if ques["type"] == "DESCRIPTIVE":
        if type(feedback) != str or len(feedback) == 0:
            invalid_answer = render_template('invalid_desc_answer')
            return False, invalid_answer
        
    if ques["type"] == "RATING":
        if not feedback.isnumeric():
            invalid_rating = render_template("invalid_rating_scale")
            return False, invalid_rating

        feedback = int(feedback)
        if feedback < 1 or feedback > 5:
            invalid_rating = render_template("invalid_rating_scale")
            return False, invalid_rating

    # feedback valid
    return True, ""



def getQuestionSpeech(session, ques):
    # res = f"Question {session.attributes['progress']}, <break time='1s'/>"
    res = ""
    if ques["type"] == 'MCQ':
        res += ques["question"]
        res += "<break time='1s'/>"
        res += " " + ques['rule'] + " "
        res += "<break time='1s'/>"
        for i in range(len(ques["options"])):
            res += f" <break time='1s'/>Option {i+1}, {ques['options'][i]}. "
        res += "<break time='1s'/>"
        res += " " + ques['rule'] + " "
        return res

    if ques["type"] == "DESCRIPTIVE":
        res += ques["question"]
        res += "<break time='1s'/>"
        res += " " + ques['rule']
        res += "<audio src='soundbank://soundlibrary/ui/gameshow/amzn_ui_sfx_gameshow_countdown_loop_32s_full_01'/>"
        res += "<break time='1s'/>"
        res += "Please provide your answer. "
        return res

    if ques["type"] == "RATING":
        res += " " + ques['rule'] + " "
        res += "<break time='1s'/> " 
        res += ques["question"]
        return res



def getRecordAnswerDirective(session, ques):
    
    if ques["type"] == "MCQ":
        return mcq.record_mcq_directive
    elif ques["type"] == "DESCRIPTIVE":
        return descriptive.record_descriptive_directive
    elif ques["type"] == "RATING":
        return rating.record_rating_directive


def surveyComplete(session):

    if session.attributes["user_state"] == "SURVEY_COMPLETE" or session.attributes["user_state"] == "SURVEY_INPROGRESS": 
        # put data to complete table
        attempted = json.loads(json.dumps(session.attributes["attempted"]))
        database.add_record_survey_complete(session.attributes["user_custom_id"], session.attributes["survey_id"], attempted)
        
        # Empty incomplete table
        database.delete_record_incomplete_table(session.attributes["user_custom_id"], session.attributes["survey_id"])
        
        # Update user table
        u_info = database.get_user_info(session.attributes["user_custom_id"])
        
        
        in_survey = u_info["Item"]["INCOMPLETE"] 
        in_survey.pop(session.attributes["survey_id"], None)
        
        com_survey = u_info["Item"]["COMPLETE"]
        com_survey[session.attributes["survey_id"]] = session.attributes["survey_name"]
        
        # Update user table surveys 
        database.update_user_table_survey(session.attributes["user_custom_id"], in_survey, com_survey)
        
        # email notifications working?
        email_notification.send_mail(session.attributes["user_custom_id"], "completed",session.attributes["survey_id"])

    elif session.attributes["user_state"] == "OPEN_SURVEY_COMPLETE" or session.attributes["user_state"] == "OPEN_SURVEY_INPROGRESS":

        # Make entry in complete table
        attempted = json.loads(json.dumps(session.attributes["attempted"]))
        database.add_open_survey_complete(session.attributes["survey_id"], attempted)

        

"""
    Review survey
""" 
def reviewSurvey(session):
    try:
        valid_user_states = ["SURVEY_INPROGRESS", "OPEN_SURVEY_INPROGRESS", "SURVEY_COMPLETE", "OPEN_SURVEY_COMPLETE"]
        if session.attributes["user_state"] in valid_user_states:
            if "attempted" not in session.attributes.keys() or len(session.attributes["attempted"]) == 0:
                session.attributes["attempted"] = []
                return "You have started giving the {}. But you haven't answered any questions. If you want to continue giving survey, say continue.".format(session.attributes["survey_name"]), ""
            

            if len(session.attributes["attempted"]) > 0:
                card_string = "Survey name: "+ session.attributes["survey_name"] + "\n"
                card_string = "You have answered {} questions. ".format(len(session.attributes["attempted"])) + "\n"

                # response = "<speak>"
                response = "Alright. Let's review your answers for {}. ".format(session.attributes["survey_name"])
                response += "You have answered, {} questions. ".format(len(session.attributes["attempted"]))
                
                j = 0
                for i in range (len(session.attributes["attempted"])):
                    if j < 2:
                        # Question number
                        response += "<break time='1s'/> Question number {}, ".format(session.attributes["attempted"][i]["question_no"])
                        
                        
                        # Question
                        if type(session.attributes["attempted"][i]["question"]) == dict:
                            response += "{} ".format(session.attributes["attempted"][i]["question"]["question"])
                        if type(session.attributes["attempted"][i]["question"]) == str:
                            response += "{} ".format(session.attributes["attempted"][i]["question"])

                        # Feedback
                        if type(session.attributes["attempted"][i]["question"]) == dict:
                            if session.attributes["attempted"][i]["question"]["type"] == "MCQ":
                                options = session.attributes["attempted"][i]["question"]["options"]
                                option = int(session.attributes["attempted"][i]["feedback"])
                                response += "You answered, {}. ".format(options[option-1])
                            else:
                                response += "You answered, {}. ".format(session.attributes["attempted"][i]["feedback"])

                        if type(session.attributes["attempted"][i]["question"]) == str:
                            response += "You answered, {}. ".format(session.attributes["attempted"][i]["feedback"])


                    card_string += "Q{}) ".format(session.attributes["attempted"][i]["question_no"])                    
                    # Question
                    if type(session.attributes["attempted"][i]["question"]) == dict:
                        card_string += "{} \n".format(session.attributes["attempted"][i]["question"]["question"])
                    if type(session.attributes["attempted"][i]["question"]) == str:
                        card_string += "{} \n".format(session.attributes["attempted"][i]["question"])

                    # Feedback 
                    if type(session.attributes["attempted"][i]["question"]) == dict:
                        if session.attributes["attempted"][i]["question"]["type"] == "MCQ":
                            options = session.attributes["attempted"][i]["question"]["options"]
                            option = int(session.attributes["attempted"][i]["feedback"])
                            card_string += "You answered, {}. \n".format(options[option-1])
                        else:
                            card_string += "You answered, {}. \n".format(session.attributes["attempted"][i]["feedback"])

                    if type(session.attributes["attempted"][i]["question"]) == str:
                        card_string += "You answered, {}. \n".format(session.attributes["attempted"][i]["feedback"])
                        
                    
                    j = j + 1
                
                response += "<break time='1s'/> You can check all your responses in your Alexa app. "

                if session.attributes["user_state"] == "SURVEY_INPROGRESS" or session.attributes["user_state"] == "OPEN_SURVEY_INPROGRESS":
                    response += "If you want to continue giving survey, say Continue. "
                    response += "If you want to change your response to any question, say Change. "

                if session.attributes["user_state"] == "SURVEY_COMPLETE" or session.attributes["user_state"] == "OPEN_SURVEY_COMPLETE":
                    response += "I will wait for you until you review your answers. If you want to change your response to any question, say Change. "
                    response += "If you want to complete the survey, say Done."

                # response += "<break time='10s'/> <break time='10s'/> If you want to change your response to any question, say Change. If you want to complete the survey, say Done.</speak>"
                
                response += "<audio src='soundbank://soundlibrary/ui/gameshow/amzn_ui_sfx_gameshow_countdown_loop_32s_full_01'/>"
                response += "If you want to change your response to any question, say Change. If you want to complete the survey, say Done."

                card_string += "If you want to continue giving survey, say Continue. "
                card_string += "If you want to change your response to any question, say Change. "

                return response, card_string
        else:
            return render_template("no_ongoing_survey"), ""
    except Exception as ae:
        logger.exception(ae)
        return render_template("except") + " review survey",  ""
    



def resetSurveySessionAttributes(session):
    session.attributes["attempted"] = []
    session.attributes["user_state"] = ""
    session.attributes["survey_name"] = ""
    session.attributes["total_questions"] = 0
    session.attributes["survey_id"] = ""
    session.attributes["progress"] = -1
    session.attributes["mandatory_questions"] = -1
    session.attributes["optional_message"] = ""
    session.attributes["complete_message"] = ""
    session.attributes["change_question_no"] = None





"""
    opt out 
"""
def optOut(session, keyword):
    try:
        user_custom_id = session.attributes["user_custom_id"]
        response = database.get_user_info(user_custom_id)
        opt_out = set(response["Item"]["OPT_OUT"])
        opt_out.add(keyword)
        result = user_info_table.update_item(
            Key={
                'USER_ID': user_custom_id,
            },
            UpdateExpression="SET OPT_OUT = :i",
            ExpressionAttributeValues={
                ':i': opt_out,
            },
            ReturnValues="UPDATED_NEW"
        )

        email_notification.send_mail(session.attributes["user_custom_id"], "optout")
        return render_template("prompt_opt_out_category").format(keyword)
    except Exception as ae:
        logger.exception(ae)
        return render_template("except") + " opt out"
    
"""
    opt in
"""
def optIn(session, keyword):
    try:
        user_custom_id = session.attributes["user_custom_id"]
        response = database.get_user_info(user_custom_id)
        opt_in = set(response["Item"]["OPT_OUT"])
        opt_in.discard(keyword)
        if len(opt_in) == 0:
            opt_in = {}
        result = user_info_table.update_item(
            Key={
                'USER_ID': user_custom_id,
            },
            UpdateExpression="SET OPT_OUT = :i",
            ExpressionAttributeValues={
                ':i': opt_in,
            },
            ReturnValues="UPDATED_NEW"
        )

        email_notification.send_mail(session.attributes["user_custom_id"], "optin")
        return render_template("prompt_opt_in_category").format(keyword)
    except Exception as ae:
        logger.exception(ae)
        return render_template("except") + " opt in"



"""
    fallback
"""
def fallbackIntent():
    pass


"""
    stop 
"""
def stopIntent():
    pass

"""
    cancel
"""
def cancelIntent():
    pass


"""
    help
"""
def helpIntent():
    pass

"""
    home
"""
def navigateHomeIntent():
    pass






"""
    DEPRECATED 
    User id
"""
def userId(session, built_id):
    try:
        response = database.get_user_info(built_id)
        # print("response: ", response)
        if 'Item' in response.keys():
            session.attributes["user_custom_id"] = built_id
            session.attributes["login_attempts"]  = 0
            return render_template("user_ask_pin")
        else:
            session.attributes["login_attempts"] += 1
            return render_template("user_id_not_found{}".format(session.attributes["login_attempts"]))
    except Exception as ae:
        logger.exception(ae)
        return render_template("except") + " user id"



"""
    User pin
    @return: Boolean, Response Text
"""
def userPin(session, pin):
    try:
        if not pin.isnumeric():
            return False, "Pin should be a number. Please tell me your four digit pin number."
        
        if int(pin) < 1000 or int(pin) > 9999:
            return False, "Pin should be of four digits only. Please tell me your four digit pin number."

        
        id = session.attributes["user_custom_id"]
        response = database.get_user_info(id)
        
        item = response["Item"]
        correct_pin = item["PIN"]
        if correct_pin == pin:
            session.attributes["auth"] = True
            greet = "Welcome back. Thank you for using OpenEyes Survey System. Let's begin. I see "
            greet += navigate_home(session, item)
            
            # set user state
            session.attributes["login_attempts"] = 0

            email_notification.send_mail(id,type1="login")
            return True, greet
        else:
            session.attributes["login_attempts"] += 1
            if session.attributes["login_attempts"] == 3:
                email_notification.send_mail(id,type1="activity")
            return False, render_template("user_invalid_pin_{}_attempt".format(digitToOrdinal(session.attributes["login_attempts"]))).format(
                session.attributes["username"]
            )
    except Exception as ae:
            logger.exception(ae)
            return False, render_template("except") + " user pin"