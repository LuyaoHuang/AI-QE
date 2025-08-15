import os
import importlib
import sys
import subprocess
import inspect
import shlex
import logging


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


def run_cmd(cmd_line: str, timeout: int = 60, cwd: str = None) -> tuple[int, str]:
    """ Use subprocess to run shell command with improved error handling

    Args:
        cmd_line: Command line string to execute
        timeout: Timeout in seconds (default: 60)
        cwd: Working directory for command execution (default: None)

    Returns:
        Tuple of (return_code, output_string)
    """
    try:
        # Handle command prefixes like $ or #
        cmd_line = cmd_line.strip()
        if cmd_line.startswith(('$', '#')):
            cmd_line = cmd_line[1:]

        # Use shlex.split() for proper handling of quotes and spaces
        cmd_list = shlex.split(cmd_line)

        logging.debug(f"Executing command: {cmd_list}")

        # Run command with timeout and proper error handling
        result = subprocess.run(
            cmd_list,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            cwd=cwd,
            text=True,  # Use text mode instead of bytes
            encoding='utf-8',
            errors='replace'  # Handle encoding errors gracefully
        )

        # Combine stdout and stderr
        output = result.stdout + result.stderr

        if result.returncode != 0:
            logging.warning(f"Command failed with return code {result.returncode}: {cmd_line}")

        return result.returncode, output
    except subprocess.TimeoutExpired:
        error_msg = f"Command timed out after {timeout} seconds: {cmd_line}"
        logging.error(error_msg)
        return -1, error_msg
    except FileNotFoundError:
        error_msg = f"Command not found: {cmd_line}"
        logging.error(error_msg)
        return -1, error_msg
    except Exception as e:
        error_msg = f"Error executing command '{cmd_line}': {str(e)}"
        logging.error(error_msg)
        return -1, error_msg
