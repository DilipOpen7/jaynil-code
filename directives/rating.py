def record_rating_directive(attributes, speech):
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
                "slotToElicit": "ratings",
                "updatedIntent": {
                "name": "RecordRating",
                "confirmationStatus": "NONE",
                "slots": {
                    "ratings": {
                    "name": "ratings",
                    "confirmationStatus": "NONE"
                    },
                }
                }
            }
            ]
        }
    }