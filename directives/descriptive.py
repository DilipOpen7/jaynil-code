def record_descriptive_directive(attributes, speech):
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
                "slotToElicit": "descriptive_answer",
                "updatedIntent": {
                "name": "RecordDescriptive",
                "confirmationStatus": "NONE",
                "slots": {
                    "descriptive_answer": {
                    "name": "descriptive_answer",
                    "confirmationStatus": "NONE"
                    },
                }
                }
            }
            ]
        }
    }