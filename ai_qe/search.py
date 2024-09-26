import requests
import json

from .config import Config


PROMPT = """[INST]You are a helpful AI assistant that can help user to find matched item in a item list based on the given description from user.
And here is a item list which include item name and description:
%s

User will input a string and you must find the matched item based on the item name and description.
And you must reply a json format message which is a json dictionary include "item_name" and "item_desc". For example:

User: yyyyy
Assistant: {
    "item_name": "xxx",
    "item_desc": "xxxxxxx"
}

If you think there is no matched item in item list, you must return empty string as the value of "item_name" and "item_desc", like this:
Assistant: {
    "item_name": "",
    "item_desc": ""
}
[/INST]"""


def text_generation_webui_api(server_ip: str, server_port: int,
                              instruction: str, old_context: str = "") -> (str, str):
    data = old_context

    if instruction:
        data += instruction

    # Avoid LLM gernerate user input
    data += "\nAssistant: {"


    response = requests.post(f"http://{server_ip}:{server_port}/v1/completions", json={
        "prompt": data,
        "max_tokens": 500,
    }).json()

    reply = response["choices"][0]["text"]
    # TODO: only accept 1 json, remove it later
    reply = reply[:reply.find("}") + 1]
    return data + reply, reply


def ai_reply_parser(reply: str) -> (str, str):
    reply = "{" + reply
    data = reply[:reply.find("}") + 1]
    json_data = json.loads(data)
    return json_data


def _build_item_list(item_list: list) -> str:
    ret = ""
    for name, desc in item_list:
        ret += f"{name}: {desc}\n"
    return ret


def search_item(user_input: str, item_list: list) -> dict:
    # TODO: use fast search method? PostgresML?
    _, reply = text_generation_webui_api(Config.llm_server_ip, Config.llm_server_port,
                                         "\nUser: " + user_input,
                                         PROMPT % _build_item_list(item_list))
    ret = ai_reply_parser(reply)
    print(user_input)
    print(item_list)
    print(ret)
    return ret
    # return ai_reply_parser(reply)


if __name__ == "__main__":
    from _utils import load_func_data, load_module_data
    item_list = []
    for data in load_func_data(['memory_doc', 'rng_doc', 'vm_basic_doc'], './test_items/'):
        item_list.append((data["name"], ' '.join(data["doc"].split())))
    print(item_list)

    INPUT = "memory hotplug"
    print(f"User: {INPUT}\nAI: {search_item(INPUT, item_list)}")
    INPUT = "live change memory"
    print(f"User: {INPUT}\nAI: {search_item(INPUT, item_list)}")
    INPUT = "rng hotplug"
    print(f"User: {INPUT}\nAI: {search_item(INPUT, item_list)}")
    INPUT = "cpu hotplug"
    print(f"User: {INPUT}\nAI: {search_item(INPUT, item_list)}")
    INPUT = "make vm running"
    print(f"User: {INPUT}\nAI: {search_item(INPUT, item_list)}")

    item_list = []

    for data in load_module_data(['memory_doc', 'rng_doc', 'vm_basic_doc'], './test_items/'):
        item_list.append((data["name"], ' '.join(data["doc"].split())))
    print(item_list)

    INPUT = "memory"
    print(f"User: {INPUT}\nAI: {search_item(INPUT, item_list)}")
    INPUT = "rng"
    print(f"User: {INPUT}\nAI: {search_item(INPUT, item_list)}")
    INPUT = "cpu hotplug"
    print(f"User: {INPUT}\nAI: {search_item(INPUT, item_list)}")
    INPUT = "make vm running"
    print(f"User: {INPUT}\nAI: {search_item(INPUT, item_list)}")
    INPUT = "start guest"
    print(f"User: {INPUT}\nAI: {search_item(INPUT, item_list)}")
