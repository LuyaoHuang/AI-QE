import gradio as gr
import argparse

from ai_qe.exceptions import InvalidInput
from ai_qe.config import Config
from ai_qe import AIQE


MSG_GEN_CASES = "I have updated generated test cases below. You can view the generated test case's content by select one in the 'View Test Cases Steps' dropdown component. BTW, if you want me to run the test cases, you can first select test cases in the 'Select Test Cases' dropdown component and then click'Run Selected Cases' button"
MSG_FINISH_RUN = "Test finished, you can check results by select the case name in the 'View Test Results' dropdown component."


def parse_args():
    parser = argparse.ArgumentParser(
        description="AI-QE demo"
    )
    parser.add_argument(
        "--server-ip", "-s", dest="server_ip",
        help="ollama server IP address",
        type=str,
    )
    parser.add_argument(
        "--server-port", "-p", dest="server_port",
        help="ollama server Port number",
        type=int,
    )
    parser.add_argument(
        "--model", "-m", dest="model",
        help="LLM model name",
        type=str,
    )
    return parser.parse_args()


args = parse_args()
Config.load_from_args(args)

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
            results[case] = ai_qe_inst.run_test(case_datas[case])
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
