from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

try:
    from .config import Config
except ImportError:
    from config import Config


class TestObjects(BaseModel):
    test_item: list[str] = Field(description="Function list user want to test")
    test_feature: list[str] = Field(description="Function area list user want to test")


SYSTEM_PROMPT = """You are a helpful AI assistant that can help user to extract information in the content. You need extract "test item" and "test feature" in user offered sentence.
Here "test_item" means the key software function user want to test and "test_feature" means the software function area user want to test.
And here is an example:

example_user: Give me some test cases focus on NBD migration function in the migration feature.
example_assistant: {{"test_item": ["NBD migration"], "test_feature": ["migration"]}}

And if there is no "test item" in users input, you can leave it empty. For example:
example_user: I want you test memory feature.
example_assistant: {{"test_item": [], "test_feature": ["memory"]}}
"""


def extract_info(user_input: str) -> dict:
    llm = ChatOllama(model=Config.model, temperature=0)
    structured_llm = llm.with_structured_output(TestObjects)
    prompt = ChatPromptTemplate.from_messages([("system", SYSTEM_PROMPT), ("human", "{input}")])
    few_shot_structured_llm = prompt | structured_llm
    ret = few_shot_structured_llm.invoke(user_input)
    return {"test item": ret.test_item, "test feature": ret.test_feature}


if __name__ == "__main__":
    INPUT = "I want you show me some test cases that test cpu hotplug in CPU and memory feature."
    print(f"User: {INPUT}\nAI: {extract_info(INPUT)}")
    INPUT = "Generate test cases focus on disk hotplug and disk hot-unplug functions which belong to disk and snapshot feature."
    print(f"User: {INPUT}\nAI: {extract_info(INPUT)}")
    INPUT = "test items are NBD migration, TLS. features are migration, remote access"
    print(f"User: {INPUT}\nAI: {extract_info(INPUT)}")
    INPUT = "Help me generate some test cases that test hotplug rng device in Rng device and Memory feature"
    print(f"User: {INPUT}\nAI: {extract_info(INPUT)}")
