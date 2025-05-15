from .ai_qe import ai_qe_agent
from .exceptions import InvalidInput
from .config import Config
from .extract import extract_info
from .search import search_item
from ._utils import load_func_data, load_module_data
from .case_generator import gen_cases, call_deptest


class AIQE(object):
    """ Demo AI-QE class with some basic method
    """
    def __init__(self):
        self._module_list = [(i["name"], i["doc"]) for i in load_module_data(Config.test_item_modules,
                                                                             Config.test_item_dir)]
        self._test_item_list = [(i["name"], i["doc"]) for i in load_func_data(Config.test_item_modules,
                                                                              Config.test_item_dir)]

    def extract_info(self, user_msg):
        """ Extract information from user input message
        """
        data = extract_info(user_msg)
        if not data:
            raise InvalidInput("Cannot extract information from this msg: " + user_msg)
        rets = {"test item": [], "test feature": []}
        for value in data["test item"]:
            tmp = self.search_item(value, self._test_item_list)
            if not tmp.get("item_name"):
                raise InvalidInput(f"Cannot find matched test item for '{value}'")
            rets["test item"].append(tmp["item_name"])
        for value in data["test feature"]:
            tmp = self.search_item(value, self._module_list)
            if not tmp.get("item_name"):
                raise InvalidInput(f"Cannot find matched feature for '{value}'")
            rets["test feature"].append(tmp["item_name"])
        return rets

    def search_item(self, string, item_list):
        """ Use AI search matched item
        """
        return search_item(string, item_list)

    def gen_test_cases(self, test_items=None, features=None, yaml_file=None):
        """ Use case generator tool to generate test case
        """
        if test_items and features:
            return gen_cases(test_items, features)
        elif yaml_file:
            with open(yaml_file, "r") as fp:
                yaml_str = fp.read()
            return call_deptest(yaml_str)
        else:
            raise InvalidInput("Need pass test_items + features or yaml_file")

    def run_tests(self, test_cases):
        """ Use AI to execute test cases
        """
        rets = []
        for case in test_cases:
            history = self.run_test(case)
            rets.append((case, history,))
        return rets

    def run_test(self, test_case):
        """ Use AI to execute test case
        """
        return ai_qe_agent(Config.model, test_case)
