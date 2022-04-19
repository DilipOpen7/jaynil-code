
"""
    Ask for survey type: new survey/ incomplete survey
"""

def survey_type_directive(attributes, speech):
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
                "slotToElicit": "survey_type",
                "updatedIntent": {
                "name": "SurveyTypeIntent",
                "confirmationStatus": "NONE",
                "slots": {
                    "survey_type": {
                    "name": "survey_type",
                    "confirmationStatus": "NONE"
                    },
                }
                }
            }
            ]
        }
    }

"""
    Confirm survey type directive
"""
def confirm_survey_type_directive(attributes, speech, survey_type):
    return {
        "version": "1.0",
        "sessionAttributes": attributes,
        "response": {
            "outputSpeech": {
            "type": "SSML",
            "ssml": speech
            },
            "shouldEndSession": False,
            "directives": [
            {
                "type": "Dialog.ConfirmIntent",
                "slotToElicit": "survey_type",
                "updatedIntent": {
                "name": "SurveyTypeIntent",
                "confirmationStatus": "NONE",
                "slots": {
                    "survey_type": {
                    "name": "survey_type",
                    "value": survey_type,
                    "confirmationStatus": "CONFIRMED"
                    },
                }
                }
            }
            ]
        }
    }
