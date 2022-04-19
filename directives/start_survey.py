
"""
    Start survey
"""
def start_survey_directive(attributes, speech, card_string):
    if card_string == "":
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
                "slotToElicit": "survey_option",
                "updatedIntent": {
                "name": "StartSurveyIntent",
                "confirmationStatus": "NONE",
                "slots": {
                    "survey_option": {
                    "name": "survey_option",
                    "confirmationStatus": "NONE"
                    },
                        }
                        }
                    }
                    ]
                }
            }
            
    return {
        "version": "1.0",
        "sessionAttributes": attributes,
        "response": {
            "outputSpeech": {
            "type": "PlainText",
            "text": speech
            },
            "card": {
				"type": "Simple",
				"title": "Choose one survey (say option number)",
				"content": card_string
			},
            "shouldEndSession": False,
            "directives": [
            {
                "type": "Dialog.ElicitSlot",
                "slotToElicit": "survey_option",
                "updatedIntent": {
                "name": "StartSurveyIntent",
                "confirmationStatus": "NONE",
                "slots": {
                    "survey_option": {
                    "name": "survey_option",
                    "confirmationStatus": "NONE"
                    },
                }
                }
            }
            ]
        }
    }

"""
    Confirmation to start survey
"""
def confirm_start_survey_directive(attributes, speech, survey_option):
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
                "slotToElicit": "survey_option",
                "updatedIntent": {
                "name": "StartSurveyIntent",
                "confirmationStatus": "NONE",
                "slots": {
                    "survey_option": {
                    "name": "survey_option",
                    "value": survey_option,
                    "confirmationStatus": "CONFIRMED"
                    },
                }
                }
            }
            ]
        }
    }
