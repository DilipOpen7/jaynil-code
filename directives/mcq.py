def record_mcq_directive(attributes, speech):
    return {
        "version": "1.0",
        "sessionAttributes": attributes,
        "response": {
            "outputSpeech": {
            "type": "SSML",
            "ssml": f"<speak>{speech}</speak>"
            },
            "shouldEndSession": False,
            "directives": [
            {
                "type": "Dialog.ElicitSlot",
                "slotToElicit": "mcq_option",
                "updatedIntent": {
                "name": "RecordMCQ",
                "confirmationStatus": "NONE",
                "slots": {
                    "mcq_option": {
                    "name": "mcq_option",
                    "confirmationStatus": "NONE"
                    },
                }
                }
            }
            ]
        }
    }