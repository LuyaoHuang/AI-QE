from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

try:
    from .config import Config
except ImportError:
    from config import Config


class MatchItem(BaseModel):
    item_name: str = Field(description="Matched item name")
    item_desc: str = Field(description="Matched item description")


SYSTEM_PROMPT = """You are a helpful AI assistant that can help user to find matched item in a item list based on the given description from user.
And here is a item list which include item name and description:
%s

User will input a string and you must find the matched item based on the item name and description.
And you must reply a format message which is a json dictionary include "item_name" and "item_desc". For example:

User: yyyyy
Assistant: {{"item_name": "xxx", "item_desc": "xxxxxxx"}}

If you think there is no matched item in item list, you must return empty string as the value of "item_name" and "item_desc", like this:
User: yyyyy
Assistant: {{"item_name": "", "item_desc": ""}}"""


def _build_item_list(item_list: list) -> str:
    ret = ""
    for name, desc in item_list:
        ret += f"{name}: {desc}\n"
    return ret


def search_item(user_input: str, item_list: list) -> dict:
    llm = ChatOllama(model=Config.model, temperature=0)
    structured_llm = llm.with_structured_output(MatchItem)
    prompt = ChatPromptTemplate.from_messages([("system", SYSTEM_PROMPT % _build_item_list(item_list)), ("human", "{input}")])
    few_shot_structured_llm = prompt | structured_llm
    ret = few_shot_structured_llm.invoke(user_input)
    return {"item_name": ret.item_name, "item_desc": ret.item_desc}


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
