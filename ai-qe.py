#!/usr/bin/env python

import requests
import subprocess
import json
import argparse


PROMPT = """[INST] You are a helpful AI assistant, you are an agent capable of using a variety of tools to test a software. Here are a few of the tools available to you:

- CMD: the command line tool should be used when you want to run a shell command and make sure this tool returns your answer to the `output` variable.
- Create File: the command line tool should be used when you want to write some data in a local file.
- Step Result: the step result tool must be used to set a test step's result: Pass or Fail. You must use this when you finished one step's testing.
- Case Result: the case result tool must be used to set a test case's status: Pass or Fail. You must use this when you finished all the steps in one case.

To use these tools you must always respond in JSON format containing `"tool_name"` and `"input"` key-value pairs.
For example, to run the example test case, "step 1: # echo $HOME Expected Result 1: /root" you need to use the CMD tool like so:

{
    "tool_name": "CMD",
    "input": "echo $HOME"
}

Or to create a file named 123.file and write "456" in it, you can use Create File tool:

{
    "tool_name": "Create File",
    "input": "123.file: 456"
}

Remember, when you have test all the steps in one test case, you can use Case Result tool to set the result:

{
    "tool_name": "Case Result",
    "input": "Pass"
}

If test case have more than one step, you must make sure all the steps have been executed.
Let's get started. The first test case is as follows.
%s
[/INST]"""


def text_generation_webui_api(server_ip: str, server_port: int, input_data: str,
                              instruction: str, old_context: str = "") -> (str, str):
    if old_context:
        data = old_context
    else:
        data = PROMPT % input_data

    if instruction:
        data += instruction

    data += "\nAssistant: {"


    response = requests.post(f"http://{server_ip}:{server_port}/v1/completions", json={
        "prompt": data,
        "max_tokens": 8000,
    }).json()

    reply = response["choices"][0]["text"]
    # TODO: only accept 1 json
    reply = reply[:reply.find("}") + 1]
    return data + reply, reply


def run_cmd(cmd_line: str) -> (int, str):
    cmd_list = cmd_line.split()
    if cmd_list[0] in ('$', '#'):
        cmd_list = cmd_list[1:]
    # FIXME
    result = subprocess.run(cmd_line.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # TODO
    output = result.stdout.decode('utf-8')
    error = result.stderr.decode('utf-8')
    return result.returncode, output + error


def ai_reply_parser(reply: str) -> (str, str):
    reply = "{" + reply
    data = reply[:reply.find("}") + 1]
    print(data)
    json_data = json.loads(data)
    return json_data["tool_name"], json_data["input"]


def create_file(data: str):
    # FIXME
    name, context = data[:data.find(":")], data[data.find(":") + 1:]
    with open(f"{name}", "w+") as fp:
        fp.write(context)


def read_file(path: str) -> str:
    with open(path) as fp:
        return fp.read()


def main():
    args = parse_args()
    case = read_file(args.case_file)
    next_instruction = ""
    history = ""
    while True:
        history, reply = text_generation_webui_api(args.server_ip, args.server_port,
                                                   case, next_instruction, history)
        tool_name, input = ai_reply_parser(reply)
        if tool_name == "Case Result":
            print(f"Case Result: {input}")
            print(f"History: {history}")
            next_instruction = "\nTool output: ok"
            break
        elif tool_name == "Step Result":
            next_instruction = "\nTool output: ok"
        elif tool_name == "CMD":
            try:
                _, output = run_cmd(input)
                next_instruction = f"\nTool output: {output}"
            except FileNotFoundError:
                next_instruction = "\nTool output: incorret input"
        elif tool_name == "Create File":
            create_file(input)
            next_instruction = "\nTool output: ok"
        elif tool_name == "Search":
            raise


def parse_args():
    parser = argparse.ArgumentParser(
        description="AI-QE demo"
    )
    parser.add_argument(
        "--server-ip", "-s", dest="server_ip",
        help="text-generation-webui server IP address",
        type=str, required=True
    )
    parser.add_argument(
        "--server-port", "-p", dest="server_port",
        help="text-generation-webui server Port number",
        default=5000,
        type=int,
    )
    parser.add_argument(
        "--test-case", "-t", dest="case_file",
        help="Path to the test case file",
        type=str, required=True
    )

    return parser.parse_args()


if __name__ == "__main__":
    main()
