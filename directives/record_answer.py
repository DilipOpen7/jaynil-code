
######## Deprecated #######
def record_answer_directive(attributes, speech):
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
                "slotToElicit": "rating",
                "updatedIntent": {
                "name": "RecordAnswer",
                "confirmationStatus": "NONE",
                "slots": {
                    "rating": {
                    "name": "rating",
                    "confirmationStatus": "NONE"
                    },
                }
                }
            }
            ]
        }
    }