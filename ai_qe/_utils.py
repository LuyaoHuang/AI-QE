import os
import importlib
import sys
import inspect


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
