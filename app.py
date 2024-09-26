import gradio as gr

from ai_qe.ai_qe import ai_qe_demo
from ai_qe.config import Config
from ai_qe.extract import extract_info
from ai_qe.search import search_item
from ai_qe._utils import load_func_data, load_module_data
from ai_qe.case_generator import gen_cases


class InvalidInput(Exception):
    """ User give a invalid input
    """


class AIQE(object):
    def __init__(self):
        #TODO
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

    def gen_test_cases(self, test_items, features):
        """ Use case generator tool to generate test case
        """
        return gen_cases(test_items, features)

    def run_tests(self, test_cases):
        """ Use AI to execute test cases
        """
        rets = []
        for case in test_cases:
            result, history = self.run_test(case)
            ret.append((case, result, history,))
        return rets

    def run_test(self, test_case):
        """ Use AI to execute test case
        """
        return ai_qe_demo(Config.llm_server_ip, Config.llm_server_port, test_case)


MSG_GEN_CASES = "I have updated generated test cases below. You can view the generated test case's content by select one in the 'View Test Cases Steps' dropdown component. BTW, if you want me to run the test cases, you can first select test cases in the 'Select Test Cases' dropdown component and then click'Run Selected Cases' button"
MSG_FINISH_RUN = "Test finished, you can check results by select the case name in the 'View Test Results' dropdown component."


ai_qe_inst = AIQE()

with gr.Blocks() as demo:
    gr_cases = gr.State(dict())
    gr_results = gr.State(dict())

    with gr.Group():
        chatbot = gr.Chatbot()
        msg = gr.Textbox(label="Talk to AI-QE")
        # FIXME
        gr.Examples(examples=["generate test case test rng device hotplug with rng and memory feature"], inputs=msg)

    with gr.Group(visible=False) as group1:
        select_cases = gr.Dropdown(
            [], multiselect=True, label="Select Test Cases", interactive=True,
            info="Select test cases that you want to execute by AI-QE")
        submit = gr.Button("Run Selected Cases")

    with gr.Group(visible=False) as group2:
        display_case = gr.Dropdown(
            [], label="View Test Cases Steps",
            info="Chose test case want to view content")

        code = gr.Code(value="",
                       interactive=False,
                       label="case content",
                       show_label=True,
                       visible=False)

    label = gr.Label(label="Loader", visible=False)
    with gr.Group(visible=False) as group3:
        display_results = gr.Dropdown(
            [], label="View Test Results",
            info="Chose test case want to view results")
        result_log = gr.Code(value="",
                             interactive=False,
                             label="result content",
                             show_label=True,
                             visible=False)


    def user_input(msg, history):
        return "", history + [[msg, None]]

    def run_test(cases, case_datas, progress=gr.Progress()):
        results = {}
        for i, case in enumerate(cases):
            progress(i / len(cases), f"Running {case} ({i}/{len(cases)})...")
            _, results[case] = ai_qe_inst.run_test(case_datas[case])
        return results, gr.update(choices=results.keys(), value=None), gr.update("Loaded", visible=False), gr.update(visible=True)

    def show_group(x, y):
        return [gr.update(visible=True)] * x + [gr.update(visible=False)] * y

    def aiqe_reply(history):
        latest_msg = history[-1][0]
        dict_cases = {}
        try:
            info = ai_qe_inst.extract_info(latest_msg)
        except InvalidInput as e:
            # TODO: use LLM to tell user error
            history[-1][1] = f"ServerError: {e}"
            return history, dict_cases, gr.update(choices=dict_cases.keys(), value=None), gr.update(choices=dict_cases.keys(), value=None)

        cases, log = ai_qe_inst.gen_test_cases(info["test item"], info["test feature"])
        history[-1][1] = MSG_GEN_CASES
        for i, case in enumerate(cases):
            dict_cases[f"case {i+1}"] = case
        return history, dict_cases, gr.update(choices=dict_cases.keys(), value=None), gr.update(choices=dict_cases.keys(), value=None)

    def change_display_case(item, cases):
        if item:
            return gr.update(value=cases.get(item), label=item, visible=True)
        else:
            return gr.update(value="", label="case content", visible=False)

    def change_display_result(item, results):
        if item:
            return gr.update(value=results.get(item), label=item, visible=True)
        else:
            return gr.update(value="", label="result content", visible=False)

    def change_case_list():
        return gr.update(choices=["case1", "case2", "case3"], value=None)

    def chatbot_notify(msg, history):
        return history + [[None, msg]]


    msg.submit(user_input,
               [msg, chatbot],
               [msg, chatbot],
               queue=False).then(aiqe_reply,
                                 [chatbot],
                                 [chatbot, gr_cases, display_case, select_cases]).then(
                                    show_group, [gr.State(2), gr.State(0)], [group1, group2])
    display_case.change(change_display_case,
                        [display_case, gr_cases],
                        [code], queue=False)
    display_results.change(change_display_result,
                           [display_results, gr_results],
                           [result_log], queue=False)
    submit.click(show_group, [gr.State(1), gr.State(2)],
                 [label, group1, group2],
                 queue=False).then(
                     run_test, [select_cases, gr_cases],
                     [gr_results, display_results, label, group3]).then(
                         chatbot_notify, [gr.State(MSG_FINISH_RUN), chatbot], [chatbot])


demo.queue().launch(server_name="0.0.0.0")
