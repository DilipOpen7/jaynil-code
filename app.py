from flask import Flask, render_template, request, jsonify
from flask_ask import Ask, statement, question, session, delegate, models
import decimal
import boto3
import json
import requests
import time

### Importing required python files
import controller
import database
from dbconn import logger
from directives import *

from dynamo_api import db_api


"""
    Initialize application
"""
application = Flask(__name__)
ask = Ask(application, "/innovation")
application.register_blueprint(db_api, url_prefix='/api')


"""
    Home page for OpenEyes survey -> https://openeyessurvey.com/
"""
@application.route('/')
def homepage():
    return render_template("index.html")

"""
    Cookie policy
"""
@application.route('/cookie-policy')
def cookie_policy():
    return render_template("cookie-policy.html")


"""
    Terms of Use
"""
@application.route('/terms-of-use')
def terms_of_use():
    return render_template("terms-of-use.html")

"""
    Privacy policy
"""
@application.route('/privacy-policy')
def privacy_policy():
    return render_template("privacy-policy.html")



###########################################################################
################## INTENTS --->
###########################################################################
@ask.on_session_started
def new_session():
    session.attributes["auth"] = False
    session.attributes["question_asked"] = False
    session.attributes["progress"] = -1
    session.attributes["survey_type"] = None
    session.attributes["login_attempts"] = 0
    session.attributes["change_question_no"] = None
    session.attributes["user_state"] = "INTRO"


"""
    Welcome intent. 
"""
@ask.launch
def start_skill():
    welcome_message = render_template('Main_Intro_RPC')
    session.attributes["last_message"] = render_template("i_said") + " " + welcome_message
    return jsonify(open_survey_directive(session.attributes, welcome_message))
    

"""
    Navigate to Home Intent
"""
@ask.intent('HomeIntent')
def homeIntent():
    # CHECK ACCOUNT LINKING 
    if not controller.accountLinking(session, request):
        return statement(render_template("Act_Not_Linked_Welcome")).link_account_card()
    if session.attributes["auth"]:
        greet = controller.navigate_home(session)
        session.attributes["last_message"] = render_template("i_said") + " " + greet
        return jsonify(survey_type_directive(session.attributes, greet))
        # return question(greet)
    else:
        if not controller.accountlinking(session, request):
            return statement(render_template("act_not_linked_welcome")).link_account_card()

"""
    Survey type Intent
"""
@ask.intent("SurveyTypeIntent")
def get_survey_type(survey_type):
    # CHECK ACCOUNT LINKING 
    if not controller.accountLinking(session, request):
            return statement(render_template("Act_Not_Linked_Welcome")).link_account_card()
    if session.attributes["auth"]:
        req = request.json
        confirmation_slot = req['request']['intent']['slots']['survey_type']['confirmationStatus']

        # Check survey type slot validation
        valid, survey_type =  controller.getSurveyType(session, survey_type)

        if not valid:
            session.attributes['user_state'] = "SURVEY_TYPE"
            speech = "Please provide a valid survey type. Say new survey or incomplete survey."
            session.attributes["last_message"] = render_template("i_said") + " " + speech
            return jsonify(survey_type_directive(session.attributes, speech))

        # Ask for survey type confirmation
        if confirmation_slot == "NONE":
            session.attributes['user_state'] = "SURVEY_TYPE_CONFIRM_INTENT"
            session.attributes['survey_type_confirm'] = survey_type
            speech = 'Do you want me to open {}s?'.format(survey_type)
            ssml_speech = "<speak><amazon:emotion name='excited' intensity='low'>Do you want me to open {}s?</amazon:emotion></speak>".format(survey_type)
            session.attributes["last_message"] = render_template("i_said") + " " + speech
            return jsonify(confirm_survey_type_directive(session.attributes, ssml_speech, survey_type))
            
        confirmation_intent = req['request']['intent']['confirmationStatus']
        # survey type confirmed
        if confirmation_intent == "DENIED":
            session.attributes['user_state'] = "SURVEY_TYPE"
            speech = "Okay, which survey do you want to start? New survey or incomplete survey?"
            session.attributes["last_message"] = render_template("i_said") + " " + speech
            return jsonify(survey_type_directive(session.attributes, speech))

        # survey type confirmed by user
        if confirmation_intent == "CONFIRMED":
            del session.attributes['survey_type_confirm']
            # print("survey Type: ", survey_type)
            if survey_type == "new survey":
                speech, card_string = controller.newSurvey(session)
            else:
                speech, card_string = controller.incompleteSurvey(session)
            session.attributes['user_state'] = "START_SURVEY"
            session.attributes["last_message"] = render_template("i_said") + " " + speech
            return jsonify(start_survey_directive(session.attributes, speech, card_string))
        
        return question("I think I am lost. Please say Home to start again.")
    
    else:
        if not controller.accountlinking(session, request):
            return statement(render_template("act_not_linked_welcome")).link_account_card()
    
        
        

"""
    Intent for new survey
"""
@ask.intent("ShowNewSurvey")
def show_new_survey():
    # CHECK ACCOUNT LINKING 
    if not controller.accountLinking(session, request):
            return statement(render_template("Act_Not_Linked_Welcome")).link_account_card()
    if session.attributes["auth"]:
        speech, card_string = controller.newSurvey(session)
        session.attributes["last_message"] = render_template("i_said") + " " + speech
        # return question(speech)
        return jsonify(start_survey_directive(session.attributes, speech, card_string))
    else:
        if not controller.accountlinking(session, request):
            return statement(render_template("act_not_linked_welcome")).link_account_card()
    

"""
    Intent for old survey
"""
@ask.intent("ShowIncompleteSurvey")
def show_incomplete_survey():
    # CHECK ACCOUNT LINKING 
    if not controller.accountLinking(session, request):
            return statement(render_template("Act_Not_Linked_Welcome")).link_account_card()

    if session.attributes["auth"]:
        speech, card_string = controller.incompleteSurvey(session)
        session.attributes["last_message"] = render_template("i_said") + " " + speech
        # return question(speech)
        return jsonify(start_survey_directive(session.attributes, speech, card_string))
    else:
        if not controller.accountlinking(session, request):
            return statement(render_template("act_not_linked_welcome")).link_account_card()


"""
    Intent to start survey 
"""
@ask.intent("StartSurveyIntent")
def start_survey(survey_option):
    # CHECK ACCOUNT LINKING 
    if not controller.accountLinking(session, request):
            return statement(render_template("Act_Not_Linked_Welcome")).link_account_card()

    if session.attributes["auth"]:
        req = request.json
        confirmation_slot = req['request']['intent']['slots']['survey_option']['confirmationStatus']

        if not survey_option.isnumeric():
            survey_option = controller.ordinalToDigit(survey_option)
            if  survey_option == None:
                session.attributes['user_state'] = "START_SURVEY"
                speech = "Please choose a valid option. Say new survey or incomplete survey."
                return jsonify(start_survey_directive(session.attributes, speech, session.attributes["card_string"]))

        # Out of bounds option
        if int(survey_option) > len(session.attributes["survey_mapping"]):
            session.attributes['user_state'] = "START_SURVEY"
            speech = "Please choose a valid option. Say new survey or incomplete survey."
            return jsonify(start_survey_directive(session.attributes, speech, session.attributes["card_string"]))


        # Ask for survey option confirmation
        if confirmation_slot == "NONE":
            session.attributes['user_state'] = "START_SURVEY_CONFIRM_INTENT"
            session.attributes['survey_type_confirm'] = survey_option

            # Get survey name from survey mapping
            survey_name = session.attributes['survey_mapping'][survey_option]["name"]
            speech = 'Do you want me to start {}?'.format(survey_name)
            # ssml_speech = "<speak><amazon:emotion name='excited' intensity='low'>Do you want me to start {}s?</amazon:emotion></speak>".format(survey_type)
            session.attributes["last_message"] = render_template("i_said") + " " + speech
            return jsonify(confirm_start_survey_directive(session.attributes, speech, survey_option))
            

        confirmation_intent = req['request']['intent']['confirmationStatus']
        # survey option confirmed
        if confirmation_intent == "DENIED":
            session.attributes['user_state'] = "START_SURVEY"
            speech = "Okay, please tell me survey option from your Alexa app."
            session.attributes["last_message"] = render_template("i_said") + " " + speech
            return jsonify(start_survey_directive(session.attributes, speech, session.attributes["card_string"]))

        
        if confirmation_intent == "CONFIRMED":
            speech = controller.startSurvey(session, survey_option)
            session.attributes["last_message"] = render_template("i_said") + " " + speech

            del session.attributes['card_string']
            del session.attributes['survey_mapping']
            del session.attributes['survey_type_confirm']

            # if survey complete but review left
            if session.attributes["user_state"] == "SURVEY_COMPLETE":
                return jsonify(prompt_review_intent(session.attributes, speech, ""))

            return question(speech)
    else:
        if not controller.accountlinking(session, request):
            return statement(render_template("act_not_linked_welcome")).link_account_card()

    




@ask.intent("OpenSurveyIntent")
def open_survey_intent(o_survey_id):
    req = request.json
    confirmation_slot = req['request']['intent']['slots']['o_survey_id']['confirmationStatus']

    # Survey Id not provided
    if o_survey_id == None:
        session.attributes['user_state'] = "O_SURVEY_ID"
        speech = "Okay. Please tell me the survey ID."
        return jsonify(open_survey_directive(session.attributes, speech))

    """
        --- REMOVE SURVEY ID CONFIRMATION ---
        Commented for RPC 
    """

    # # Ask for survey id confirmation
    # if confirmation_slot == "NONE":
    #     session.attributes['user_state'] = "O_SURVEY_ID_CONFIRM_INTENT"
    #     session.attributes["confirm_o_survey_id"] = o_survey_id
    #     speech = "Just for confirmation, is your survey id {}?".format(o_survey_id)
    #     # ssml_speech = "<speak>{}</speak>".format(speech)
    #     session.attributes["last_message"] = render_template("i_said") + " " + speech
    #     return jsonify(confirm_open_survey_directive(session.attributes, speech, o_survey_id))
    
    # confirmation_intent = req['request']['intent']['confirmationStatus']
    # # Survey id not confirmed
    # if confirmation_intent == "DENIED":
    #     session.attributes['user_state'] = "O_SURVEY_ID"
    #     speech = "Okay, please tell me your survey id."
    #     return jsonify(open_survey_directive(session.attributes, speech))
    
    # # survey id confirmed by user
    # if confirmation_intent == "CONFIRMED":
    #     del session.attributes["confirm_o_survey_id"]
    #     instructions_for_new_survey = controller.startOpenSurvey(session, request, o_survey_id)
    #     # instructions_for_new_survey = "<speak><amazon:emotion name='excited' intensity='low'>{}</amazon:emotion></speak>".format(instructions_for_new_survey)
    #     session.attributes["last_message"] = render_template("i_said") + " " + instructions_for_new_survey
    #     if session.attributes["o_survey_id_attempts"] < 3:
    #         return jsonify(open_survey_directive(session.attributes, instructions_for_new_survey))
    #     else:
    #         return statement(instructions_for_new_survey)

    """
        ---END---
    """

    session.attributes['user_state'] = "O_SURVEY_ID"
    instructions_for_new_survey = controller.startOpenSurvey(session, request, o_survey_id)
    session.attributes["last_message"] = render_template("i_said") + " " + instructions_for_new_survey
    if session.attributes["o_survey_id_attempts"] < 3:
        return jsonify(open_survey_directive(session.attributes, instructions_for_new_survey))
    else:
        return statement(instructions_for_new_survey)




##############################################
# RECORD ANSWERS
##############################################

def changeAnswers(session, feedback, question_no):
    valid, res = controller.recordAnswer(session, feedback, question_no)
    if not valid:
        record_direc = controller.getRecordAnswerDirective(session, res)
        return jsonify(record_direc(session.attributes, res))

    session.attributes["change_question_no"] = None

    if session.attributes["user_state"] == "SURVEY_COMPLETE" or session.attributes["user_state"] == "OPEN_SURVEY_COMPLETE":
        res = f"Alright, I have updated your response to, {feedback}. If you want to review your responses, say Review, otherwise say Done to complete the survey."
        session.attributes["last_message"] = render_template("i_said") + " " + res
        return jsonify(prompt_review_intent(session.attributes, res, ""))
    else: # survey in progress
        res = f"Alright, I have updated your response to, {feedback}. "
        res += "Ready for next question? "
        session.attributes["last_message"] = render_template("i_said") + " " + res
        return question(res)


def submitSurvey(session):
    # Add to database
    if session.attributes["progress"] > 1:
        controller.surveyComplete(session)
    
    if session.attributes["auth"]:
        if session.attributes["user_state"] == "SURVEY_COMPLETE":
            if len(session.attributes["complete_message"]) > 0:
                res = "You have answered all the questions. "
                res += session.attributes["complete_message"] + " Say, Go to Home, for new survey. Otherwise, say Stop to close this survey."
            else:
                res = render_template("prompt_complete_in_survey")
        else:
            res = "Okay, I have closed the {}. Let me take you to your dashboard. Don't worry. Your current survey has been saved. ".format(session.attributes["survey_name"])
    
    elif session.attributes["user_state"] == "OPEN_SURVEY_COMPLETE":
        if len(session.attributes["complete_message"]) > 0:
                res = "You have answered all the questions. "
                res += session.attributes["complete_message"] + " To continue answering more surveys, tell me another survey ID. Otherwise, say Stop to close this survey."
        else:
            res = render_template("o_survey_complete")
    else:
        if session.attributes["progress"] > 1:
            res = "Your feedback has been submitted. To continue answering more surveys, tell me another survey ID. Otherwise, say Stop to close this survey."
        else:
            res = "I have closed the survey. To continue answering more surveys, tell me another survey ID. Otherwise, say Stop to close this survey."

    # Reset session vars
    controller.resetSurveySessionAttributes(session)
    return res


def recordFeedback(session, feedback):

    # if user wants to change the feedback
    if session.attributes["change_question_no"] is not None:
        return changeAnswers(session, feedback, session.attributes["change_question_no"])

    # if survey in progress
    if session.attributes["user_state"] == "OPEN_SURVEY_INPROGRESS" or \
        session.attributes["user_state"] == "SURVEY_INPROGRESS":
        valid, res = controller.recordAnswer(session, feedback)

        # Invalid rating, ask rating again
        if not valid:
            ques = session.attributes["current_question"]
            record_direc = controller.getRecordAnswerDirective(session, ques)
            return jsonify(record_direc(session.attributes, res))

        # if survey is now complete
        if session.attributes["user_state"] == "OPEN_SURVEY_COMPLETE" or session.attributes["user_state"] == "SURVEY_COMPLETE":
            
            """
                --- REMOVE Review Prompt ---
                Commented for RPC 
            """
            # return jsonify(prompt_review_intent(session.attributes, res, ""))
            """
                ---END---
            """
            
            # Submit survey
            res = submitSurvey(session)
            return question(res)
            

        """
            --- REMOVE next question Prompt ---
            Commented for RPC 
        """

        # Prompt next question
        # session.attributes["last_message"] = render_template("i_said") + " " + res
        # return jsonify(prompt_next_question(session.attributes, res))

        """
            --- END ---
        """

        ques = controller.nextQuestion(session)
        res = controller.getQuestionSpeech(session, ques)
        res = "<audio src='soundbank://soundlibrary/ui/gameshow/amzn_ui_sfx_gameshow_neutral_response_01'/>" + res
        session.attributes["last_message"] = render_template("i_said") + " " + res
        record_direc = controller.getRecordAnswerDirective(session, ques)
        return jsonify(record_direc(session.attributes, res))


@ask.intent("RecordMCQ")
def record_mcq(mcq_option):
    return recordFeedback(session, mcq_option)
        


@ask.intent("RecordDescriptive")
def record_descriptive(descriptive_answer):
    return recordFeedback(session, descriptive_answer)



@ask.intent("RecordRating")
def record_descriptive(ratings):
    return recordFeedback(session, ratings)




"""
    Intent to record answer for a given question.
"""
@ask.intent("RecordAnswer")
def record_answer(rating):
    if session.attributes["user_state"] == "OPEN_SURVEY_INPROGRESS":
        valid, res = controller.recordAnswer(session, rating)

        # if survey is now complete
        if session.attributes["user_state"] == "OPEN_SURVEY_COMPLETE":
            return jsonify(prompt_review_intent(session.attributes, res, ""))

        # Invalid rating, ask rating again
        if not valid:
            return jsonify(record_answer_directive(session.attributes, res))

        session.attributes["last_message"] = render_template("i_said") + " " + res
        # return question(res)
        return jsonify(prompt_next_question(session.attributes, res))

    # CHECK ACCOUNT LINKING 
    if not controller.accountLinking(session, request):
        return statement(render_template("Act_Not_Linked_Welcome")).link_account_card()
        
    if session.attributes["auth"]:
        valid, res = controller.recordAnswer(session, rating)

        # if survey is now complete
        if session.attributes["user_state"] == "SURVEY_COMPLETE":
            return jsonify(prompt_review_intent(session.attributes, res, ""))

        # Invalid rating, ask rating again
        if not valid:
            return jsonify(record_answer_directive(session.attributes, res))

        session.attributes["last_message"] = render_template("i_said") + " " + res
        #return question(res)
        return jsonify(prompt_next_question(session.attributes, res))
    else:
        if not controller.accountlinking(session, request):
            return statement(render_template("act_not_linked_welcome")).link_account_card()




##########################################
### REVIEW AND CHANGE REPSONSE
##########################################


@ask.intent("ReviewIntent")
def review_intent():
    req = request.json
    confirmation_status = req['request']['intent']['confirmationStatus']
    if confirmation_status == "CONFIRMED":
        res, card_string = controller.reviewSurvey(session)
        session.attributes["last_message"] = render_template("i_said") + " " + res
        return jsonify(start_review_directive(session.attributes, res, card_string))
    else:
        if session.attributes["user_state"] == "SURVEY_INPROGRESS" or \
            session.attributes["user_state"] == "OPEN_SURVEY_INPROGRESS":
            ques = session.attributes["current_question"]
            res = "I thought I misunderstood you. Let's back to where we are. "

            res += controller.getQuestionSpeech(session, ques)
            session.attributes["last_message"] = render_template("i_said") + " " + res
            record_direc = controller.getRecordAnswerDirective(session, ques)
            return jsonify(record_direc(session.attributes, res))

            # if just started
        elif session.attributes["user_state"] == "INTRO":
                res = "I thought I misunderstood you. Let's back to where we are. Do you have a survey ID?"
                session.attributes["last_message"] = render_template("i_said") + " " + res
                return question(res)
            # user is authenticated
        elif session.attributes["auth"]:
                res = "I thought I misunderstood you. Let's back to where we are. Say, Home to explore surveys."
                session.attributes["last_message"] = render_template("i_said") + " " + res
                return question(res)
  
    return question("I cannot start the review right now. ")
    

@ask.intent("PromptReviewIntent")
def prompt_review(prompt_review):
    
    prompt_review = prompt_review.lower()
    valid_responses = {
        "please review": "review",
        "review": "review",
        "alexa review": "review",
        "alexa please review": "review",
        "done": "done",
        "change": "change",
        "please change": "change",
        "alexa please change": "change",
        "alexa change": "change",
    }

    if prompt_review not in valid_responses.keys():
        res = "Please say, Review, to review your responses, or say Done, to complete the survey."
        session.attributes["last_message"] = render_template("i_said") + " " + res
        return jsonify(prompt_review_intent(session.attributes, res, ""))

    if valid_responses[prompt_review] == "review":
        res, card_string = controller.reviewSurvey(session)
        session.attributes["last_message"] = render_template("i_said") + " " + res
        return jsonify(prompt_review_intent(session.attributes, res, card_string))
    
    if valid_responses[prompt_review] == "done":
        res = submitSurvey(session)
        return question(res)
    

    if valid_responses[prompt_review] == "change":
        res = "Alright, please tell me the question number for which you want to change your response?"
        session.attributes["last_message"] = render_template("i_said") + " " + res
        return jsonify(change_response_directive_question_no(session.attributes, res))

    # should not reach here
    return question("Say Home to start again")



@ask.intent("ChangeResponseIntent")
def change_response_intent(question_no, new_response):

    valid_user_states = ["SURVEY_INPROGRESS", "OPEN_SURVEY_INPROGRESS", "SURVEY_COMPLETE", "OPEN_SURVEY_COMPLETE"]
    if session.attributes["user_state"] in valid_user_states:
        if "attempted" not in session.attributes.keys() or len(session.attributes["attempted"]) == 0:
            session.attributes["attempted"] = []
            return question("You have started giving the {}. But you haven't answered any questions. If you want to continue giving survey, say continue. ".format(session.attributes["survey_name"]))
            
        if question_no == None:
            res = "Which question number do you want to change?"
            session.attributes["last_message"] = render_template("i_said") + " " + res
            return jsonify(change_response_directive_question_no(session.attributes, res))

        if not question_no.isnumeric() or int(question_no) <= 0:
            res = "Please tell me correct question number? If you need to check your responses, please say Review."
            session.attributes["last_message"] = render_template("i_said") + " " + res
            return jsonify(change_response_directive_question_no(session.attributes, res))

        question_no = int(question_no)

        if question_no > len(session.attributes["attempted"]):
            res = "Please tell me the correct question number. If you need to check your responses, please say Review."
            session.attributes["last_message"] = render_template("i_said") + " " + res
            return jsonify(change_response_directive_question_no(session.attributes, res))

        # Question number is valid ->
        ques = session.attributes["attempted"][question_no-1]["question"]
        ans = session.attributes["attempted"][question_no-1]["feedback"]
        res = "Got it! The question number {} was, {}. ".format(question_no, ques["question"])
        if session.attributes["attempted"][question_no-1]["question"]["type"] == "MCQ":
            options = session.attributes["attempted"][question_no-1]["question"]["options"]
            option = int(session.attributes["attempted"][question_no-1]["feedback"])
            res += "You answered, {}. ".format(options[option-1])
            res += "The options are, "
            for i in range(len(ques["options"])):
                res += f" <break time='1s'/>Option {i+1}, {ques['options'][i]}. "
            res += render_template("mcq_question")
        elif session.attributes["attempted"][question_no-1]["question"]["type"] == "DESCRIPTIVE":
            res += "You answered, {}. ".format(session.attributes["attempted"][question_no-1]["feedback"])
            res += render_template("desc_question")

        elif session.attributes["attempted"][question_no-1]["question"]["type"] == "RATING":
            res += "You answered, {}. ".format(session.attributes["attempted"][question_no-1]["feedback"])
            res += render_template("rating_question")

        res += " Now, please tell me your new response."
        session.attributes["last_message"] = render_template("i_said") + " " + res
        record_direc = controller.getRecordAnswerDirective(session, ques)
        session.attributes["change_question_no"] = question_no
        return jsonify(record_direc(session.attributes, res))

    else:
        return render_template("no_ongoing_survey")



#####################################
### Stop survey
#####################################
"""
    Stop the current survey
"""
@ask.intent("StopSurvey")
def stop_survey():
    req = request.json
    confirmation_status = req['request']['intent']['confirmationStatus']
    if confirmation_status == "CONFIRMED":
        if session.attributes["auth"] and (session.attributes["user_state"] == "SURVEY_INPROGRESS" or session.attributes["user_state"] == "SURVEY_COMPLETE"):
            if session.attributes["progress"] > session.attributes["mandatory_questions"]:
                # Survey review
                res  = render_template("prompt_survey_review")
                return jsonify(prompt_review_intent(session.attributes, res, ""))
            else:
                # Save to incomplete 
                ques = "Okay, I have closed the {}. Let me take you to your dashboard. Don't worry. Your current survey has been saved. ".format(session.attributes["survey_name"])
                ques += " Say, Go to Home, for new survey. Otherwise, say Stop to close this survey."
                session.attributes["last_message"] = render_template("i_said") + " " + ques
                controller.resetSurveySessionAttributes(session)
                return question(ques)

        elif session.attributes["user_state"] == "OPEN_SURVEY_INPROGRESS" or session.attributes["user_state"] == "OPEN_SURVEY_COMPLETE":
            """
                --- REMOVE Review Prompt ---
                Commented for RPC 
            """
            # # Survey review
            # if session.attributes["progress"] > session.attributes["mandatory_questions"]:
            #     res = "Okay, now if you want to review your responses, say Review, otherwise say done to complete the survey."
            # else:
            #     res  = render_template("prompt_survey_review")
            # return jsonify(prompt_review_intent(session.attributes, res, ""))
            """
                --- END ---
            """

            res = submitSurvey(session)
            return question(res)

        else:
            session.attributes["last_message"] = render_template("i_said") + " " + render_template("prompt_stop_out_survey")
            return question(render_template("prompt_stop_out_survey"))
            
    else:
        res = render_template("prompt_stop_by_mistake_in_survey") + " "
        if session.attributes["user_state"] == "OPEN_SURVEY_INPROGRESS" or session.attributes["user_state"] == "SURVEY_INPROGRESS":
            res += "The question is, "
            ques = controller.nextQuestion(session)
            res += controller.getQuestionSpeech(session, ques)
            session.attributes["last_message"] = render_template("i_said") + " " + res
            record_direc = controller.getRecordAnswerDirective(session, ques)
            return jsonify(record_direc(session.attributes, res))
        else:
            ques = "What do you want to do?"
        session.attributes["last_message"] = render_template("i_said") + " " + ques
        return question(ques)


@ask.intent("StopCancelEnd")
def stop_cancel_end():
    if session.attributes['user_state'] == "SURVEY_INPROGRESS" or session.attributes['user_state'] == "OPEN_SURVEY_INPROGRESS":
        speech = "Are you sure you want to close the survey?"
        return jsonify(confirm_stop_survey_directive(session.attributes, speech))
        
    return statement(render_template("session_close_no_auth"))



"""
    Handle sign out
"""
@ask.intent("SignOut")
def sign_out():
    req = request.json
    confirmation_status = req['request']['intent']['confirmationStatus']
    if confirmation_status == "CONFIRMED":
        if session.attributes["auth"]:
            if session.attributes["user_state"] == "SURVEY_INPROGRESS":
                stat = render_template("survey_sign_out")
                return statement(stat)
            else:
                stat = render_template("prompt_sign_out")
                return statement(stat)
        else: 
            exit_message = "OpenEyes survey will miss you. Thank you for taking out the survey. Bye"
            return statement(exit_message)
    else:
        ques = render_template("prompt_stop_by_mistake_in_survey") + " "
        if session.attributes["user_state"] == "SURVEY_INPROGRESS" or session.attributes["user_state"] == "OPEN_SURVEY_INPROGRESS":
            ques = controller.nextQuestion(session)
            res = controller.getQuestionSpeech(session, ques)
            session.attributes["last_message"] = render_template("i_said") + " " + res
            record_direc = controller.getRecordAnswerDirective(session, ques)
            return jsonify(record_direc(session.attributes, res))
        else:
            ques += "What do you want to do? You can say Home, to explore new surveys."
        session.attributes["last_message"] = render_template("i_said") + " " + ques
        return question(ques)





##################################
## OPT In/Out
##################################

"""
    Opt-out of a category or keyword
"""
@ask.intent("OptOutIntent")
def opt_out(keyword):
    # CHECK ACCOUNT LINKING 
    if not controller.accountLinking(session, request):
        return statement(render_template("Act_Not_Linked_Welcome")).link_account_card()

    if session.attributes["auth"]:    
        req = request.json
        confirmation_status = req['request']['intent']['confirmationStatus']
        if confirmation_status == "CONFIRMED":
            if session.attributes["auth"]:
                # TODO: Handle each case differently
                if session.attributes["user_state"] == "SURVEY_INPROGRESS":
                    # survey in progress
                    res = controller.optOut(session, keyword)
                else:
                    # outside survey
                    res = controller.optOut(session, keyword)
                    session.attributes["last_message"] = render_template("i_said") + " " + res       
                return question(res)
        else:
            session.attributes["last_message"] = render_template("i_said") + " " + render_template("prompt_opt_out_by_mistake")
            return question(render_template("prompt_opt_out_by_mistake"))
    else:
        if not controller.accountlinking(session, request):
            return statement(render_template("act_not_linked_welcome")).link_account_card()


"""
    Opt-in to a category or keyword
"""
@ask.intent("OptInIntent")
def opt_in(keyword):
    # CHECK ACCOUNT LINKING 
    if not controller.accountLinking(session, request):
        return statement(render_template("Act_Not_Linked_Welcome")).link_account_card()

    if session.attributes["auth"]:
        req = request.json
        confirmation_status = req['request']['intent']['confirmationStatus']
        if confirmation_status == "CONFIRMED":
            if session.attributes["auth"]:
                res = controller.optIn(session, keyword)  
                session.attributes["last_message"] = render_template("i_said") + " " + res    
                return question(res)
        else:
            session.attributes["last_message"] = render_template("i_said") + " " + render_template("prompt_opt_in_by_mistake")
            return question(render_template("prompt_opt_in_by_mistake"))
    else:
        if not controller.accountlinking(session, request):
            return statement(render_template("act_not_linked_welcome")).link_account_card()







@ask.intent('PinIntent')
def pin_intent(pin):
    # CHECK ACCOUNT LINKING 
    if not controller.accountLinking(session, request):
            return statement(render_template("Act_Not_Linked_Welcome")).link_account_card()

    # REMOVING PIN
    # Redirect user to home
    return question("Please say Home, to explore different survey")


    ### USING PIN ALONG WITH COGNITO FOR AUTH
    if pin == None:
        session.attributes['user_state'] = "PIN"
        speech = "Please tell me your 4 digit pin number."
        session.attributes["last_message"] = render_template("i_said") + " " + speech
        return jsonify(pin_directive(session.attributes, speech))

    pin = str(pin)
    req = request.json
    confirmation_slot = req['request']['intent']['slots']['pin']['confirmationStatus']

    if not pin.isnumeric():
        speech = session.attributes["username"]+ ". Pin should be a four digit number. Please tell me your four digit pin number."
        return jsonify(pin_directive(session.attributes, speech))

    # Ask for Pin confirmation
    if confirmation_slot == "NONE":
        session.attributes['user_state'] = "PIN_CONFIRM_INTENT"
        session.attributes['confirm_pin'] = pin
        speech = 'Just for confirmation, is your pin {}?'.format(pin)
        ssml_speech = "<speak>Just for confirmation, <amazon:effect name='whispered'>is your pin {}?</amazon:effect></speak>".format(pin)
        session.attributes["last_message"] = render_template("i_said") + " " + speech
        return jsonify(confirm_pin_directive(session.attributes, ssml_speech, pin))
        
    confirmation_intent = req['request']['intent']['confirmationStatus']
    # Pin not confirmed
    if confirmation_intent == "DENIED":
        session.attributes['user_state'] = "PIN"
        speech = "Okay, please tell me your 4 digit pin number."
        session.attributes["last_message"] = render_template("i_said") + " " + speech
        return jsonify(pin_directive(session.attributes, speech))

    # Pin confirmed by user
    if confirmation_intent == "CONFIRMED":
        auth, res = controller.userPin(session, pin)
        # Pin valid
        if auth:
            del session.attributes['confirm_pin']
            session.attributes['user_state'] = "SURVEY_TYPE"
            session.attributes["last_message"] = render_template("i_said") + " " + res
            return jsonify(survey_type_directive(session.attributes, res))
        # Pin invalid
        elif session.attributes["login_attempts"] < 3:
            session.attributes['user_state'] = "PIN"
            session.attributes["last_message"] = render_template("i_said") + " " + res
            return jsonify(pin_directive(session.attributes, res))
        else:
            session.attributes["last_message"] =render_template("i_said") + " " + res
            return statement(res)

















############### Built-ins ################

"""
    Intent to proceed survey when user gives affirmation.
"""
@ask.intent("AMAZON.YesIntent")
def next_question():
    # START OPEN SURVEYS ?
    if session.attributes["user_state"] == "INTRO":
        speech = render_template("o_ask_survey_id_first")
        # ssml_speech = "<speak><amazon:emotion name='excited' intensity='low'>{}</amazon:emotion></speak>".format(speech)
        session.attributes["last_message"] = render_template("i_said") + " " + speech
        return jsonify(open_survey_directive(session.attributes, speech))

    # USER GIVING OPEN SURVEY
    if session.attributes["user_state"] == "OPEN_SURVEY_INPROGRESS":
        ques = controller.nextQuestion(session)
        res = controller.getQuestionSpeech(session, ques)
        session.attributes["last_message"] = render_template("i_said") + " " + res
        record_direc = controller.getRecordAnswerDirective(session, ques)
        return jsonify(record_direc(session.attributes, res))

    if session.attributes["user_state"] == "OPEN_SURVEY_COMPLETE":
        speech = "To continue giving more surveys, say Open Surveys. Otherwise, say Stop to close this survey."
        session.attributes["last_message"] = render_template("i_said") + " " + speech
        return question(speech)

    # USER GIVING INVITED SURVEY

    # CHECK ACCOUNT LINKING 
    if not controller.accountLinking(session, request):
            return statement(render_template("Act_Not_Linked_Welcome")).link_account_card()

    if session.attributes["auth"]:    
        if session.attributes["user_state"] == "SURVEY_INPROGRESS":
            ques = controller.nextQuestion(session)
            res = controller.getQuestionSpeech(session, ques)
            session.attributes["last_message"] = render_template("i_said") + " " + res
            record_direc = controller.getRecordAnswerDirective(session, ques)
            return jsonify(record_direc(session.attributes, res))
            
        else:
            # return question("I think I misunderstood. "+ session.attributes["last_message"])
            return question("Yes, I am listening.")
    else:
        if not controller.accountlinking(session, request):
            return statement(render_template("act_not_linked_welcome")).link_account_card()

        
"""
    Intent to cancel survey if user says NO.
"""
@ask.intent("AMAZON.NoIntent")
def no_intent():
    # CHECK ACCOUNT LINKING 
    if session.attributes["user_state"] == "INTRO":
        if not controller.accountLinking(session, request):
            return statement(render_template("Act_Not_Linked_Welcome")).link_account_card()


        # ASKING FOR PIN
        # Account Linked
        # speech = 'Hello ' + session.attributes["username"] + ". In order to proceed, please provide me with your 4 digit pin number."
        # session.attributes["last_message"] = render_template("i_said") + " " + speech
        # return jsonify(pin_directive(session.attributes, speech))

        # WITHOUT PIN
        greet = "Welcome back. Thank you for using OpenEyes Survey System. Let's begin. I see "
        greet += controller.navigate_home(session)
        session.attributes['user_state'] = "SURVEY_TYPE"
        session.attributes["last_message"] = render_template("i_said") + " " + greet
        return jsonify(survey_type_directive(session.attributes, greet))

    elif session.attributes['user_state'] == "OPEN_SURVEY_INPROGRESS" or session.attributes['user_state'] == 'SURVEY_INPROGRESS':       
        if session.attributes["progress"] > session.attributes["mandatory_questions"]:
            speech = "Are you sure you want to submit the survey?"
        else:
            speech = "Are you sure you want to close the survey?"
        return jsonify(confirm_stop_survey_directive(session.attributes, speech))

    else:
        bye_text = 'I am not sure what you mean. Please say Home, to start again.'
        return question(bye_text)


"""
    Repeat Question
"""
@ask.intent('AMAZON.RepeatIntent')
def repeat_intent():

    ############ OPEN SURVEY #########
    
    # ASK O Survey ID
    if session.attributes['user_state'] == "O_SURVEY_ID":
        # ssml_speech = "<speak>{}</speak>".format(session.attributes["last_message"])
        return jsonify(open_survey_directive(session.attributes, session.attributes["last_message"]))
    
    # ASK O SURVEY ID CONFIRM
    if session.attributes['user_state'] == "O_SURVEY_ID_CONFIRM_INTENT":
        # ssml_speech = "<speak>{}</speak>".format(session.attributes["last_message"])
        return jsonify(confirm_open_survey_directive(session.attributes, session.attributes["last_message"], session.attributes["confirm_o_survey_id"]))



    ######## OPEN SURVEY or USER SURVEY in progress #########

    if session.attributes['user_state'] == "OPEN_SURVEY_INPROGRESS" or session.attributes['user_state'] == "SURVEY_INPROGRESS":
        if "current_question" in session.attributes:
            ques = session.attributes["current_question"]
            res = controller.getQuestionSpeech(session, ques)
            session.attributes["last_message"] = render_template("i_said") + " " + res
            record_direc = controller.getRecordAnswerDirective(session, ques)
            return jsonify(record_direc(session.attributes, res))
        
        else:
            return question(session.attributes["last_message"])
        


    ############ PIN ##############

    # ASK PIN
    if session.attributes['user_state'] == "PIN":
        return jsonify(pin_directive(session.attributes, session.attributes["last_message"]))
    
    # ASK PIN CONFIRM
    if session.attributes['user_state'] == "PIN_CONFIRM_INTENT":
        ssml_speech = "<speak>{}</speak>".format(session.attributes["last_message"])
        return jsonify(confirm_pin_directive(session.attributes, ssml_speech, session.attributes["confirm_pin"]))
    
    return question(session.attributes["last_message"])

    
"""
    Default intent when Alexa does not know what to do.
"""
@ask.intent('AMAZON.FallbackIntent')
def fallback_intent():
    if session.attributes["user_state"] == "HOME":
        res = render_template("invalid_survey_type")
        return question(res)
    
    progress = session.attributes["progress"]
    if  progress > -1:
        if session.attributes["question_asked"] == True:
            ques = controller.nextQuestion(session)
            res = controller.getQuestionSpeech(session, ques)
            session.attributes["last_message"] = render_template("i_said") + " " + res
            record_direc = controller.getRecordAnswerDirective(session, ques)
            res = "I am not sure what you mean. " + res
            return jsonify(record_direc(session.attributes, res))
        
        else:
            res = "I am not sure what you mean. Please say Yes, to proceed or, say No, to close the survey."
            return question(res)
    else:
        return question("I am sorry! I am not sure what you mean.")


"""
    Stop Intent
"""
@ask.intent('AMAZON.StopIntent')
def stop_intent():
    if session.attributes['user_state'] == "SURVEY_INPROGRESS" or session.attributes['user_state'] == "OPEN_SURVEY_INPROGRESS":
        speech = "Are you sure you want to close the survey?"
        return jsonify(confirm_stop_survey_directive(session.attributes, speech))
    else:
        return statement(render_template("session_close_no_auth"))


"""
    Cancel Intent
"""
@ask.intent('AMAZON.CancelIntent')
def cancel_intent():
    if session.attributes['user_state'] == "SURVEY_INPROGRESS" or session.attributes['user_state'] == "OPEN_SURVEY_INPROGRESS":
        speech = "Are you sure you want to close the survey?"
        return jsonify(confirm_stop_survey_directive(session.attributes, speech))
    else:
        return statement(render_template("session_close_no_auth"))

"""
    Help Intent
"""
@ask.intent('AMAZON.HelpIntent')
def help_intent():
    session.attributes["last_message"] = render_template("i_said") + " " + render_template('help_instructions')
    return question(render_template('help_instructions'))


"""
    Navigate Home Intent (Default-built-in)
"""
@ask.intent('AMAZON.NavigateHomeIntent')
def navigate_home_intent():
    if session.attributes["auth"]:
        greet = controller.navigate_home(session=session)
        session.attributes["last_message"] = render_template("i_said") + " " + greet
        return question(greet)
    else:
        if not controller.accountlinking(session, request):
            return statement(render_template("act_not_linked_welcome")).link_account_card()



"""
    Session Ended Request
"""
@ask.session_ended
def session_ended():
    return "{}", 200




#################### DEPRECATED #######################

# """
#     Intent to authenticate user by getting the user id 
# """
# @ask.intent("UseridIntent")
# def authenticate_userid(n_one, n_two, n_three, n_four):
#     if not controller.accountLinking(request):
#         return statement(render_template("Act_Not_Linked_Welcome")).link_account_card()
#     req = request.json
#     confirmation_status = req['request']['intent']['confirmationStatus']
#     if confirmation_status == "CONFIRMED":
#         built_id = str(n_one)+str(n_two)+str(n_three)+str(n_four)
#         res = controller.userId(session, built_id)
#         if session.attributes["login_attempts"] < 3:
#             return question(res)
#         else:
#             return statement(res)
#     else:
#         return question(render_template("user_id2"))

    
# """
#     Intent to authenticate user by getting the pin
# """
# @ask.intent("UserPinIntent")
# def authenticate_userpin(pin_one, pin_two, pin_three, pin_four, pin_five):
#     req = request.json
#     confirmation_status = req['request']['intent']['confirmationStatus']
#     if confirmation_status == "CONFIRMED":
#         built_pin = str(pin_one)+str(pin_two)+str(pin_three)+str(pin_four)+str(pin_five)
#         res = controller.userPin(session, built_pin)
#         if session.attributes["login_attempts"] < 3:
#             session.attributes["last_message"] =render_template("i_said") + " " + res
#             return question(res)
#         else:
#             session.attributes["last_message"] =render_template("i_said") + " " + res
#             return statement(res)
#     else:
#         return question(render_template("user_pin2"))

"""
    Initial setup for the server.
"""
if __name__ == '__main__':

    # start server
    application.run(debug=True, port=8080, host='0.0.0.0')
