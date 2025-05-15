import argparse
import re

from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated, List, Union

from langgraph.graph import MessagesState
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, ToolMessage

try:
    from ._utils import run_cmd
except ImportError:
    from _utils import run_cmd


@tool
def create_file(file_path: str, data: str) -> str:
    """Create a file which path is file_path and write data in this file"""
    with open(file_path, "w+") as fp:
        fp.write(data)
    return "success"


@tool
def run_shell_cmd(cmd_line: str) -> str:
    """Run shell command and return output"""
    _, ret = run_cmd(cmd_line)
    return ret


class AgentState(TypedDict):
    # The list of previous messages in the conversation
    messages: Annotated[list, add_messages]

    # case steps
    case_steps: list[str]
    # current step in case steps
    cur_step: int


def custom_agent(model_name, case):
    llm = ChatOllama(model=model_name, temperature=0)
    # Augment the LLM with tools
    tools = [create_file, run_shell_cmd]
    tools_by_name = {tool.name: tool for tool in tools}
    llm_with_tools = llm.bind_tools(tools)

    # Nodes
    def llm_call(state: AgentState):
        """LLM decides whether to call a tool or not"""

        return {
            "messages": [
                llm_with_tools.invoke(
                    state["messages"]
                )
            ]
        }

    def next_step(state: AgentState):
        """Returns the next test step to LLM"""
        next_msg = HumanMessage(content=state["case_steps"][state["cur_step"]])
        # print(next_msg)
        return {"messages": [next_msg],
                "cur_step": state["cur_step"] + 1}


    def tool_node(state: AgentState):
        """Performs the tool call"""

        result = []
        for tool_call in state["messages"][-1].tool_calls:
            tool = tools_by_name[tool_call["name"]]
            observation = tool.invoke(tool_call["args"])
            result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
        return {"messages": result}


    # Conditional edge function to route to the tool node or end based upon whether the LLM made a tool call
    def should_continue(state: AgentState) -> str:
        """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""

        messages = state["messages"]
        last_message = messages[-1]
        # If the LLM makes a tool call, then perform an action
        if last_message.tool_calls:
            return "Action"
        # Perform Next step if there are more steps in the case
        if len(state["case_steps"]) > state["cur_step"]:
            return "Next"
        # Otherwise, we stop (reply to the user)
        return END


    # Build workflow
    agent_builder = StateGraph(AgentState)

    # Add nodes
    agent_builder.add_node("llm_call", llm_call)
    agent_builder.add_node("tool_call", tool_node)
    agent_builder.add_node("next_step", next_step)

    # Add edges to connect nodes
    agent_builder.add_edge(START, "llm_call")
    agent_builder.add_conditional_edges(
        "llm_call",
        should_continue,
        {
            # Name returned by should_continue : Name of next node to visit
            "Action": "tool_call",
            "Next": "next_step",
            END: END,
        },
    )
    agent_builder.add_edge("tool_call", "llm_call")
    agent_builder.add_edge("next_step", "llm_call")

    # Compile the agent
    agent = agent_builder.compile()

    # Draw graph
    # from langchain_core.runnables.graph import MermaidDrawMethod
    # agent.get_graph().draw_mermaid_png(output_file_path="./graph.png", draw_method=MermaidDrawMethod.PYPPETEER)

    # Invoke
    steps = split_steps(case)
    messages = [SystemMessage(content="You are a helpful AI assistant, you are an agent capable of using a variety of tools to test a software."),
                HumanMessage(content=f"Run this test case step by step and report test result after finished all the steps:\n{steps[0]}")]
    messages = agent.invoke({"messages": messages, "case_steps": steps, "cur_step": 1}, {"recursion_limit": 100})
    return messages


def split_steps(case):
    """Split test case into steps"""
    steps = re.findall(r"\d+.\n(.*?)(?=\d+\.|$)", case, re.S)
    ret = []
    for i, step in enumerate(steps):
        ret.append(f"Step({i+1}/{len(steps)}):\n{step}")
    return ret


def ai_qe_agent(model_name: str, case: str) -> str:
    """AI-QE agent"""
    response = custom_agent(model_name, case)
    history = ""
    if "messages" in response:
        for msg in response["messages"]:
            history += f"{msg.pretty_repr()}\n"
    return history


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
    ret = ai_qe_agent(args.model, case)
    print(ret)
