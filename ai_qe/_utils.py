import os
import importlib
import sys
import subprocess
import inspect


def load_modules(modules_list: list, module_path: str='.') -> object:
    """ Use importlib to load python modules
    """
    cmd_folder = os.path.realpath(module_path)
    sys.path.insert(0, cmd_folder)
    for module in modules_list:
        yield importlib.import_module(module)


def load_func_data(file_list: list, dir_path: str) -> object:
    """ Get function name and document then format them to dict list
    """
    for module in load_modules(file_list, dir_path):
        for _, func in inspect.getmembers(module, inspect.isfunction):
            yield {"name": f"{module.__name__}.{func.__name__}",
                   "doc": func.__doc__}


def load_module_data(file_list: list, dir_path: str) -> object:
    """ Use load_modules() function to load function and formate it to dict list
    """
    for module in load_modules(file_list, dir_path):
        yield {"name": module.__name__,
               "doc": module.__doc__}


def run_cmd(cmd_line: str) -> (int, str):
    """ Use subprocess to run shell command
    """
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
