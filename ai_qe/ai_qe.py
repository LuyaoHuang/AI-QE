import argparse
from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

try:
    from ._utils import run_cmd
except ImportError:
    from _utils import run_cmd


def create_file(file_path: str, data: str) -> str:
    """Create a file which path is file_path and write data in this file"""
    with open(file_path, "w+") as fp:
        fp.write(data)
    return "success"


def run_shell_cmd(cmd_line: str) -> str:
    """Run shell command and return output"""
    _, ret = run_cmd(cmd_line)
    return ret


class TestResultResponse(BaseModel):
    """Respond to the user in this format."""

    test_result: str = Field(description="Test Result")


def ai_qe_agent(model_name: str, case: str) -> (TestResultResponse, str):
    model = ChatOllama(model=model_name, temperature=0)
    agent = create_react_agent(model, tools=[create_file, run_shell_cmd],
                               response_format=TestResultResponse,
                               prompt="You are a helpful AI assistant, you are an agent capable of using a variety of tools to test a software.")
    response = agent.invoke(
        {"messages": [{"role": "user",
                       "content": f"Run this test case and report test result: {case}"}]}
    )

    history = ""
    if "messages" in response:
        for msg in response["messages"]:
            history += f"{msg.pretty_repr()}\n"
    return response['structured_response'], history


if __name__ == "__main__":
    from config import Config


    def parse_args():
        parser = argparse.ArgumentParser(
            description="AI-QE demo"
        )
        parser.add_argument(
            "--server-ip", "-s", dest="server_ip",
            help="Ollama server IP address",
            type=str, required=True
        )
        parser.add_argument(
            "--server-port", "-p", dest="server_port",
            help="Ollama server Port number",
            default=11434,
            type=int,
        )
        parser.add_argument(
            "--model", "-m", dest="model",
            help="Model name of LLM",
            default="jacob-ebey/phi4-tools",
            type=str,
        )
        parser.add_argument(
            "--test-case", "-t", dest="case_file",
            help="Path to the test case file",
            type=str, required=True
        )
        return parser.parse_args()

    def read_file(path: str) -> str:
        with open(path) as fp:
            return fp.read()


    args = parse_args()
    Config.load_from_args(args)
    case = read_file(args.case_file)
    _, ret = ai_qe_agent(args.model, case)
    print(ret)
