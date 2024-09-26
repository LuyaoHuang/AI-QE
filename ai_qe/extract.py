import requests
import json

from .config import Config


PROMPT = """[INST]You are a helpful AI assistant that can help user to extract information in the content. You can extract "test item" and "test feature" in user offered sentence.
Here "test item" means the key software function user want to test and "test feature" means the software function area user want to test. Your work is extract "test item" and "test feature" to json format.
And here is an example:

User: Give me some test cases focus on NBD migration function in the migration feature.
Assistant: {
    "test item": ["NBD migration"],
    "test feature": ["migration"]
}

And if there is no "test item" in users input, you can leave it empty. For example:
User: I want you test memory feature.
Assistant: {
    "test item": [],
    "test feature": ["memory"]
}

If user input doesn't have any information related to "test item" and "test feature", you must reply an empty json like this:

User: Have a nice day!
Assistant: {}

[/INST]
"""


def text_generation_webui_api(server_ip: str, server_port: int,
                              instruction: str, old_context: str = "") -> (str, str):
    if old_context:
        data = old_context
    else:
        data = PROMPT

    if instruction:
        data += instruction

    # Avoid LLM gernerate user input
    data += "\nAssistant: {"


    response = requests.post(f"http://{server_ip}:{server_port}/v1/completions", json={
        "prompt": data,
        "max_tokens": 500,
    }).json()

    reply = response["choices"][0]["text"]
    # TODO: only accept 1 json
    reply = reply[:reply.find("}") + 1]
    return data + reply, reply


def ai_reply_parser(reply: str) -> (str, str):
    reply = "{" + reply
    data = reply[:reply.find("}") + 1]
    json_data = json.loads(data)
    return json_data


def extract_info(user_input: str) -> dict:
    _, reply = text_generation_webui_api(Config.llm_server_ip,
                                         Config.llm_server_port,
                                         "\nUser: " + user_input)
    return ai_reply_parser(reply)


if __name__ == "__main__":
    INPUT = "I want you show me some test cases that test cpu hotplug in CPU and memory feature."
    print(f"User: {INPUT}\nAI: {extract_info(INPUT)}")
    INPUT = "Generate test cases focus on disk hotplug and disk hot-unplug functions which belong to disk and snapshot feature."
    print(f"User: {INPUT}\nAI: {extract_info(INPUT)}")
    INPUT = "test items are NBD migration, TLS. features are migration, remote access"
    print(f"User: {INPUT}\nAI: {extract_info(INPUT)}")
    INPUT = "Help me generate some test cases that test hotplug rng device in Rng device and Memory feature"
    print(f"User: {INPUT}\nAI: {extract_info(INPUT)}")
