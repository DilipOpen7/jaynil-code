def prompt_next_question(attributes, speech):
    return {
        "version": "1.0",
        "sessionAttributes": attributes,
        "response": {
            "outputSpeech": {
            "type": "SSML",
            "ssml": f"<speak><audio src='soundbank://soundlibrary/ui/gameshow/amzn_ui_sfx_gameshow_neutral_response_01'/>{speech}</speak>"
            },
            "shouldEndSession": False,
            "type": "_DEFAULT_RESPONSE"
        }
    }
