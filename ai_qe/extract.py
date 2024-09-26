import requests
import json

try:
    from .config import Config
    from ._utils import llm_json_api, json_reply_parser
except ImportError:
    from config import Config
    from _utils import llm_json_api, json_reply_parser


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


def extract_info(user_input: str) -> dict:
    _, reply = llm_json_api(Config.llm_server_ip,
                            Config.llm_server_port,
                            PROMPT,
                            "\nUser: " + user_input,
                            max_tokens=500)
    return json_reply_parser(reply)


if __name__ == "__main__":
    INPUT = "I want you show me some test cases that test cpu hotplug in CPU and memory feature."
    print(f"User: {INPUT}\nAI: {extract_info(INPUT)}")
    INPUT = "Generate test cases focus on disk hotplug and disk hot-unplug functions which belong to disk and snapshot feature."
    print(f"User: {INPUT}\nAI: {extract_info(INPUT)}")
    INPUT = "test items are NBD migration, TLS. features are migration, remote access"
    print(f"User: {INPUT}\nAI: {extract_info(INPUT)}")
    INPUT = "Help me generate some test cases that test hotplug rng device in Rng device and Memory feature"
    print(f"User: {INPUT}\nAI: {extract_info(INPUT)}")
