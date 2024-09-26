import sys, tempfile, os, argparse
from subprocess import call

try:
    from ._utils import llm_json_api, json_reply_parser, run_cmd
except ImportError:
    from _utils import llm_json_api, json_reply_parser, run_cmd


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

Or to create a file named "tmp.file" under "/root/" dir and write "123" in it, you can use Create File tool:

{
    "tool_name": "Create File",
    "input": "/root/tmp.file:123"
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


def create_file(data: str):
    # FIXME
    name, context = data[:data.find(":")], data[data.find(":") + 1:]
    # TODO: check the file path to avoid some security issues
    with open(name, "w+") as fp:
        fp.write(context)


def read_tempfile_input(base_str: str):
    with tempfile.NamedTemporaryFile(suffix=".tmp") as tf:
        tf.write(str.encode(base_str))
        tf.flush()
        call(["vim", tf.name])
        tf.seek(0)
        return tf.read().decode()


def ai_qe_demo(server_ip, server_port, case, mock=False):
    next_instruction = ""
    history = ""
    while True:
        history, reply = llm_json_api(server_ip, server_port,
                                      PROMPT % case, next_instruction, history)
        data = json_reply_parser(reply)
        tool_name, input = data["tool_name"], data["input"]
        if mock:
            print(data["input"])
        if tool_name == "Case Result":
            print(f"Case Result: {input}")
            print(f"History: {history}")
            next_instruction = "\nTool output: ok"
            break
        elif tool_name == "Step Result":
            next_instruction = "\nTool output: ok"
        elif tool_name == "CMD":
            try:
                if mock:
                    output = read_tempfile_input(input)
                else:
                    _, output = run_cmd(input)
                next_instruction = f"\nTool output: {output}"
            except FileNotFoundError:
                # TODO: give more clearly error
                next_instruction = "\nTool output: invalid input"
        elif tool_name == "Create File":
            if not mock:
                create_file(input)
            next_instruction = "\nTool output: ok"
        elif tool_name == "Search":
            raise

    return input, history


if __name__ == "__main__":
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
        parser.add_argument(
            "--mock", "-m", dest="mock",
            help="Mock commands execution",
            action='store_true'
        )
        return parser.parse_args()

    def read_file(path: str) -> str:
        with open(path) as fp:
            return fp.read()

    args = parse_args()
    case = read_file(args.case_file)
    ai_qe_demo(args.server_ip, args.server_port, case, args.mock)
