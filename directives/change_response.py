
"""
    Change Response Intent: ask for question number
"""

def change_response_directive_question_no(attributes, speech):
    return {
        "version": "1.0",
        "sessionAttributes": attributes,
        "response": {
            "outputSpeech": {
            "type": "SSML",
            "ssml": f'<speak>{speech}</speak>'
            },
            "shouldEndSession": False,
            "directives": [{
                "type": "Dialog.ElicitSlot",
                "slotToElicit": "question_no",
                "updatedIntent": {
                    "name": "ChangeResponseIntent",
                    "slots": {
                        "question_no": {
                            "name": "question_no",
                            "confirmationStatus": "NONE",
                        },
                        "new_response": {
                            "name": "new_response",
                            "confirmationStatus": "NONE",
                        }
                    }
                }
            }]
        }
    }


def change_response_directive_new_response(attributes, speech, question_no):
    return {
        "version": "1.0",
        "sessionAttributes": attributes,
        "response": {
            "outputSpeech": {
            "type": "PlainText",
            "text": speech
            },
            "shouldEndSession": False,
            "directives": [{
                "type": "Dialog.ElicitSlot",
                "slotToElicit": "new_response",
                "updatedIntent": {
                    "name": "ChangeResponseIntent",
                    "slots": {
                        "question_no": {
                            "name": "question_no",
                            "confirmationStatus": "NONE",
                            "value": question_no
                        },
                        "new_response": {
                            "name": "new_response",
                            "confirmationStatus": "NONE",
                        }
                    }
                }
            }]
        }
    }
