"""
    Pin Directive
"""
def pin_directive(attributes, speech):
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
                "slotToElicit": "pin",
                "updatedIntent": {
                "name": "PinIntent",
                "confirmationStatus": "NONE",
                "slots": {
                    "pin": {
                    "name": "pin",
                    "confirmationStatus": "NONE"
                    },
                }
                }
            }
            ]
        }
    }


"""
    Confirm pin directive
"""
def confirm_pin_directive(attributes, speech, pin_no):
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
                "slotToElicit": "pin",
                "updatedIntent": {
                "name": "PinIntent",
                "confirmationStatus": "NONE",
                "slots": {
                    "pin": {
                    "name": "pin",
                    "value": pin_no,
                    "confirmationStatus": "CONFIRMED"
                    },
                }
                }
            }
            ]
        }
    }