
"""
    Start review while survey in progress
"""
def start_review_directive(attributes, speech, card_string):
    if card_string == "":
        return {
        "version": "1.0",
        "sessionAttributes": attributes,
        "response": {
            "outputSpeech": {
            "type": "SSML",
            "ssml": f"<speak>{speech}</speak>"
            },
            "shouldEndSession": False,
            }
        }
            
    return {
        "version": "1.0",
        "sessionAttributes": attributes,
        "response": {
            "outputSpeech": {
            "type": "SSML",
            "ssml": f"<speak>{speech}</speak>"
            },
            "card": {
				"type": "Simple",
				"title": "Review your responses",
				"content": card_string
			},
            "shouldEndSession": False,
        }
    }

"""
    Prompt user to review after survey completion
"""

def prompt_review_intent(attributes, speech, card_string):
    if card_string == "":
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
                    "slotToElicit": "prompt_review",
                    "updatedIntent": {
                    "name": "PromptReviewIntent",
                    "confirmationStatus": "NONE",
                    "slots": {
                        "prompt_review": {
                        "name": "prompt_review",
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
            "type": "SSML",
            "ssml": f"<speak>{speech}</speak>"
            },
            "card": {
				"type": "Simple",
				"title": "Review your responses",
				"content": card_string
			},
            "shouldEndSession": False,
            "directives": [
            {
                "type": "Dialog.ElicitSlot",
                "slotToElicit": "prompt_review",
                "updatedIntent": {
                "name": "PromptReviewIntent",
                "confirmationStatus": "NONE",
                "slots": {
                    "prompt_review": {
                    "name": "prompt_review",
                    "confirmationStatus": "NONE"
                    },
                }
                }
            }
            ]
        }
    }