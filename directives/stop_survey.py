
"""
    Confirmation to stop survey
"""
def confirm_stop_survey_directive(attributes, speech):
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
                "updatedIntent": {
                "name": "StopSurvey",
                "confirmationStatus": "NONE",
                }
            }
            ]
        }
    }