
"""
    Open survey directives
"""
def open_survey_directive(attributes, speech):
    return {
        "version": "1.0",
        "sessionAttributes": attributes,
        "response": {
            "outputSpeech": {
            "type": "PlainText",
            "text": speech
            },
            "shouldEndSession": False,
            "directives": [
            {
                "type": "Dialog.ElicitSlot",
                "slotToElicit": "o_survey_id",
                "updatedIntent": {
                "name": "OpenSurveyIntent",
                "confirmationStatus": "NONE",
                "slots": {
                    "o_survey_id": {
                    "name": "o_survey_id",
                    "confirmationStatus": "NONE"
                    },
                }
                }
            }
            ]
        }
    }

"""
    Confirm open survey id
"""

def confirm_open_survey_directive(attributes, speech, survey_id):
    return {
        "version": "1.0",
        "sessionAttributes": attributes,
        "response": {
            "outputSpeech": {
            "type": "PlainText",
            "text": speech
            },
            "shouldEndSession": False,
            "directives": [
            {
                "type": "Dialog.ConfirmIntent",
                "slotToElicit": "o_survey_id",
                "updatedIntent": {
                "name": "OpenSurveyIntent",
                "confirmationStatus": "NONE",
                "slots": {
                    "o_survey_id": {
                    "name": "o_survey_id",
                    "value": survey_id,
                    "confirmationStatus": "CONFIRMED"
                    },
                }
                }
            }
            ]
        }
    }