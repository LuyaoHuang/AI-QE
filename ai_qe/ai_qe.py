"""
AI-QE Agent Module

This module implements an AI-powered automated testing agent that can execute test cases
step by step using Large Language Models (LLMs) and various tools. The agent uses
LangChain and LangGraph to create a conversational workflow that can:

1. Parse test cases into sequential steps
2. Execute each step using available tools (file creation, shell commands)
3. Make decisions about the next action based on LLM responses
4. Continue until all test steps are completed

Key Components:
- AgentState: Maintains conversation history and test case progression
- Tool functions: create_file() and run_shell_cmd() for test execution
- Workflow nodes: llm_call, tool_call, next_step for orchestrating the testing process
- Command-line interface for running test cases with specified LLM models

Dependencies:
    - langchain_core: For LLM integration and tool management
    - langgraph: For building the agent workflow graph
    - Custom modules: _utils (command execution), llm_backend (LLM preparation)
"""

import argparse
import logging
import re

from langchain_core.tools import tool
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated, List, Union

from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

try:
    from ._utils import run_cmd
    from .llm_backend import prepare_llm
except ImportError:
    from _utils import run_cmd
    from llm_backend import prepare_llm


@tool
def create_file(file_path: str, data: str) -> str:
    """
    Create a file at the specified path and write data to it.

    This tool allows the AI agent to create files during test execution,
    which is useful for generating test artifacts, configuration files,
    or any other files required by the test case.

    Args:
        file_path (str): The absolute or relative path where the file should be created
        data (str): The content to write to the file

    Returns:
        str: "success" if the file was created successfully

    Raises:
        IOError: If the file cannot be created or written to
    """
    with open(file_path, "w+") as fp:
        fp.write(data)
    return "success"


@tool
def run_shell_cmd(cmd_line: str) -> str:
    """
    Execute a shell command and return its output.

    This tool enables the AI agent to run system commands as part of test execution,
    allowing for setup, cleanup, verification, and other operations that require
    interaction with the operating system.

    Args:
        cmd_line (str): The shell command to execute

    Returns:
        str: The output from the command execution (stdout)

    Note:
        Uses the run_cmd utility function from _utils module which handles
        command execution and error handling.
    """
    _, ret = run_cmd(cmd_line)
    return ret


class AgentState(TypedDict):
    """
    State management for the AI-QE agent workflow.

    This class defines the state structure that is passed between different nodes
    in the agent workflow graph. It maintains the conversation history and tracks
    progress through test case steps.

    Attributes:
        messages (Annotated[list, add_messages]): List of conversation messages
            including system messages, human messages, and tool messages. The
            add_messages annotation enables automatic message aggregation.
        case_steps (list[str]): List of individual test steps parsed from the
            test case. Each step represents one action to be performed.
        cur_step (int): Index of the current step being executed (0-based).
            Used to track progress through the test case.
    """
    messages: Annotated[list, add_messages]
    case_steps: list[str]
    cur_step: int


def custom_agent(model_name: str, case: str) -> dict:
    """
    Create and execute a custom AI agent for automated test case execution.

    This function sets up a complete AI agent workflow using LangGraph that can:
    1. Parse test cases into individual steps
    2. Execute each step using available tools
    3. Make decisions about next actions based on LLM responses
    4. Continue until all test steps are completed

    The agent uses a state machine with three main nodes:
    - llm_call: LLM processes the current state and decides on actions
    - tool_call: Executes tools (file creation, shell commands) as needed
    - next_step: Advances to the next test step

    Args:
        model_name (str): Name of the LLM model to use (e.g., "jacob-ebey/phi4-tools")
        case (str): Test case content containing numbered steps to execute

    Returns:
        dict: Final agent state containing all messages and execution history

    Workflow:
        START -> llm_call -> [tool_call|next_step|END] -> llm_call -> ... -> END
    """
    llm = prepare_llm(model_name)
    # Augment the LLM with tools
    tools = [create_file, run_shell_cmd]
    tools_by_name = {tool.name: tool for tool in tools}
    llm_with_tools = llm.bind_tools(tools)

    # Workflow node definitions
    def llm_call(state: AgentState) -> dict:
        """
        Main LLM processing node that analyzes the current state and decides on actions.

        This node sends the current conversation state to the LLM, which can either:
        1. Call tools to perform actions (file creation, shell commands)
        2. Provide responses about the current test step
        3. Request to proceed to the next step

        Args:
            state (AgentState): Current agent state with messages and step information

        Returns:
            dict: Updated state with LLM response message
        """
        logging.info(f"Enter llm_call node and next message is: {state['messages'][-1]}")
        return {
            "messages": [
                llm_with_tools.invoke(
                    state["messages"]
                )
            ]
        }

    def next_step(state: AgentState) -> dict:
        """
        Advance to the next test step in the case.

        This node extracts the next step from the parsed test case and presents
        it to the LLM as a new human message. It also updates the current step
        counter to track progress.

        Args:
            state (AgentState): Current agent state

        Returns:
            dict: Updated state with next step message and incremented step counter
        """
        logging.info(f"Enter next_step node and next step is: {state['case_steps'][state['cur_step']]}")
        next_msg = HumanMessage(content=state["case_steps"][state["cur_step"]])
        return {"messages": [next_msg],
                "cur_step": state["cur_step"] + 1}

    def tool_node(state: AgentState) -> dict:
        """
        Execute tools requested by the LLM.

        This node processes tool calls made by the LLM, executes the requested
        tools (create_file, run_shell_cmd), and returns the results as tool
        messages that will be fed back to the LLM.

        Args:
            state (AgentState): Current agent state containing tool calls

        Returns:
            dict: Updated state with tool execution results
        """
        logging.info(f"Enter tool_node node and current tool calls: {state['messages'][-1].tool_calls}")
        result = []
        for tool_call in state["messages"][-1].tool_calls:
            tool = tools_by_name[tool_call["name"]]
            observation = tool.invoke(tool_call["args"])
            result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
        return {"messages": result}


    def should_continue(state: AgentState) -> str:
        """
        Decision function to determine the next workflow step.

        This function analyzes the current state and the last LLM response to decide
        what action should be taken next in the workflow. It implements the core
        logic for the agent's decision-making process.

        Decision logic:
        1. If LLM made tool calls -> Execute tools ("Action")
        2. If more test steps remain -> Advance to next step ("Next")
        3. Otherwise -> End the workflow (END)

        Args:
            state (AgentState): Current agent state with messages and step info

        Returns:
            str: Next action to take - "Action", "Next", or END
        """
        logging.info(f"Enter should_continue node")
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


def split_steps(case: str) -> list[str]:
    """
    Parse a test case into individual numbered steps.

    This function takes a test case written in a numbered format and splits it
    into individual steps that can be processed sequentially by the AI agent.

    Expected format:
        1.
        First step description

        2.
        Second step description

        ...

    Args:
        case (str): Raw test case content with numbered steps

    Returns:
        list[str]: List of formatted step strings, each prefixed with step number
                  and total count (e.g., "Step(1/3):\nFirst step description")

    Example:
        Input: "1.\nCreate a file\n\n2.\nRun a command\n"
        Output: ["Step(1/2):\nCreate a file\n", "Step(2/2):\nRun a command\n"]
    """
    steps = re.findall(r"\d+\.\n((?:.*?\n)*?)(?=\d+\.|\Z)", case, re.S)
    ret = []
    for i, step in enumerate(steps):
        ret.append(f"Step({i+1}/{len(steps)}):\n{step}")
    return ret


def ai_qe_agent(model_name: str, case: str) -> str:
    """
    Main entry point for the AI-QE agent.

    This function provides a simplified interface to the custom_agent function,
    executing a test case with the specified LLM model and returning a formatted
    history of all interactions.

    Args:
        model_name (str): Name of the LLM model to use for test execution
        case (str): Test case content with numbered steps to execute

    Returns:
        str: Complete conversation history including all messages between the
             agent, LLM, and tools, formatted for human readability

    Example:
        >>> result = ai_qe_agent("jacob-ebey/phi4-tools", test_case_content)
        >>> print(result)  # Shows complete test execution history
    """
    response = custom_agent(model_name, case)
    history = ""
    if "messages" in response:
        for msg in response["messages"]:
            history += f"{msg.pretty_repr()}\n"
    return history


if __name__ == "__main__":
    from config import Config


    def parse_args() -> argparse.Namespace:
        """
        Parse command-line arguments for the AI-QE agent.

        Returns:
            argparse.Namespace: Parsed command-line arguments including:
                - server_ip: Ollama server IP address (required)
                - server_port: Ollama server port (default: 11434)
                - model: LLM model name (default: "jacob-ebey/phi4-tools")
                - case_file: Path to test case file (required)
        """
        parser = argparse.ArgumentParser(
            description="AI-QE demo: Automated test case execution using AI agents"
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
