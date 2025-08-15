import tempfile
import yaml
import copy
import os
import re

try:
    from ._utils import run_cmd
    from .config import Config
except ImportError:
    from _utils import run_cmd
    from config import Config


def split_case(case_file: str) -> list:
    with open(case_file) as fp:
        data = fp.read()

    cases = []
    case_content = ""
    for line in data.splitlines():
        match = re.match("======== case ([0-9]+) ========", line)
        if match:
            if case_content:
                cases.append(case_content)
                case_content = ""
        else:
            case_content += f"{line}\n"

    if case_content:
        cases.append(case_content)
    return cases


def call_deptest(temp_yaml: str) -> tuple[list, str]:
    """ Call deptest with the given temp_yaml file, return a tuple of (cases, log)."""
    tmp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, dir="./test_items/", mode='w') as tmp_file:
            tmp_file.write(temp_yaml)
            tmp_file_path = tmp_file.name
        ret_code, log = run_cmd(f"deptest --template {tmp_file_path}")
        if ret_code != 0:
            raise Exception(log)
        case_file_path = "test_items/case0.file-case"
        return split_case(case_file_path), log
    finally:
        if tmp_file_path and os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)


def build_yaml(test_items: list, features: list) -> str:
    base_data = {
        "name": "tmp case",
        "test_objs": [],
        "modules": ["vm_basic"],
        "doc-modules": ["vm_basic_doc"],
    }

    for item in test_items:
        # TODO: impove case generator
        base_data["test_objs"].append(re.sub(r"(.*)_doc.(.*)", r"\1.\2", item))
    for feature in features:
        base_data["modules"].append(re.sub(r"(.*)_doc", r"\1", feature))
        base_data["doc-modules"].append(feature)
    final_params = copy.deepcopy(Config.case_gen_params)
    final_params["case"].append(base_data)
    return yaml.dump(final_params)


def gen_cases(test_items, features):
    return call_deptest(build_yaml(test_items, features))


if __name__ == "__main__":
    print(gen_cases(["rng_doc.live_attach_rng_device"], ["rng_doc", "memory_doc"]))
