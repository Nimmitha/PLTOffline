import sys
import requests

def post_to_slack(message_text="default message"):

    url = 'https://hooks.slack.com/services/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'
    text = {"text": message_text}

    result = requests.post(url, json=text)
    return result.text

if __name__ == "__main__":
    message_text = "Hello World"
    result = post_to_slack(message_text)
    print(result)