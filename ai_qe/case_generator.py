import tempfile
import yaml
import copy
import os
import re

try:
    from ._utils import run_cmd
except ImportError:
    from _utils import run_cmd

# TODO
BASE_PARAM = {
    "params": {
        "test_case": True,
        "full_matrix": True,
        "guest_name": "vm1",
        "guest_xml": "guest.xml",
        "mist_rules": "split",
        "max_cases": 30,
        "drop_env": 10,
        "cleanup": True,
        "rng_model": "virtio",
        "curmem": 1048576,
    },
    "case": []
}


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


def call_deptest(temp_yaml: str) -> (list, str):
    cases = []
    try:
        tmp_file = tempfile.NamedTemporaryFile(delete=False, dir="./test_items/")
        with open(tmp_file.name, "w") as fp:
            fp.write(temp_yaml)
        ret_code, log = run_cmd(f"deptest --template {tmp_file.name}")
        if ret_code != 0:
            raise Exception(log)
        return split_case("test_items/case0.file-case"), log
    finally:
        os.remove(tmp_file.name)


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
    final_params = copy.deepcopy(BASE_PARAM)
    final_params["case"].append(base_data)
    return yaml.dump(final_params)


def gen_cases(test_items, features):
    return call_deptest(build_yaml(test_items, features))


if __name__ == "__main__":
    print(gen_cases(["rng_doc.live_attach_rng_device"], ["rng_doc", "memory_doc"]))
