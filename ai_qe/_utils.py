import os
import importlib
import sys
import subprocess
import inspect
import requests
import json


def load_modules(modules_list: list, module_path: str='.') -> object:
    cmd_folder = os.path.realpath(module_path)
    sys.path.insert(0, cmd_folder)
    for module in modules_list:
        yield importlib.import_module(module)


def load_func_data(file_list: list, dir_path: str) -> object:
    for module in load_modules(file_list, dir_path):
        for _, func in inspect.getmembers(module, inspect.isfunction):
            yield {"name": f"{module.__name__}.{func.__name__}",
                   "doc": func.__doc__}


def load_module_data(file_list: list, dir_path: str) -> object:
    for module in load_modules(file_list, dir_path):
        yield {"name": module.__name__,
               "doc": module.__doc__}


def llm_json_api(server_ip: str, server_port: int, prompt: str,
                 instruction: str, old_context: str = "", max_tokens: int = 8000) -> (str, str):
    if old_context:
        input_str = old_context
    else:
        input_str = prompt

    if instruction:
        input_str += instruction

    # TODO: this is for json api
    input_str += "\nAssistant: {"


    response = requests.post(f"http://{server_ip}:{server_port}/v1/completions", json={
        "prompt": input_str,
        "max_tokens": max_tokens,
    }).json()

    reply = response["choices"][0]["text"]
    # TODO: only accept 1 json
    json_reply = "{" + reply[:reply.find("}") + 1]
    full_reply = input_str + reply[:reply.find("}") + 1]
    return full_reply, json_reply


def json_reply_parser(data: str) -> (str, str):
    #TODO: remove it
    data = data.replace("\n", " ")
    try:
        return json.loads(data)
    except:
        print(data)
        raise


def run_cmd(cmd_line: str) -> (int, str):
    cmd_list = cmd_line.split()
    if cmd_list[0] in ('$', '#'):
        cmd_list = cmd_list[1:]
    # FIXME
    result = subprocess.run(cmd_line.split(),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    # TODO
    output = result.stdout.decode('utf-8')
    error = result.stderr.decode('utf-8')
    return result.returncode, output + error
