import requests
import json

try:
    from .config import Config
    from ._utils import llm_json_api, json_reply_parser
except ImportError:
    from config import Config
    from _utils import llm_json_api, json_reply_parser


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


def _build_item_list(item_list: list) -> str:
    ret = ""
    for name, desc in item_list:
        ret += f"{name}: {desc}\n"
    return ret


def search_item(user_input: str, item_list: list) -> dict:
    # TODO: use fast search method? PostgresML?
    _, reply = llm_json_api(Config.llm_server_ip, Config.llm_server_port,
                            PROMPT % _build_item_list(item_list),
                            "\nUser: " + user_input,
                            max_tokens=500)
    return json_reply_parser(reply)


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
