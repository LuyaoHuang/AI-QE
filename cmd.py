#!/usr/bin/env python3
import argparse
import sys
import random

from ai_qe.exceptions import InvalidInput
from ai_qe.config import Config
from ai_qe import AIQE


def parse_args():
    parser = argparse.ArgumentParser(
        description="AI-QE demo command line tool"
    )
    parser.add_argument(
        "--request", "-r", dest="request_str",
        help="Natural language request for cases generation",
        type=str,
    )
    parser.add_argument(
        "--template-yaml", "-t", dest="yaml_path",
        help="Path to the template yaml file for cases generation",
        type=str,
    )
    parser.add_argument(
        "--test-case", "-c", dest="test_cases",
        help="Path to test cases raw files",
        type=str, nargs='+',
    )
    parser.add_argument(
        "--case-number", "-n", dest="case_num",
        help="Random pick up request number test cases",
        type=int,
    )
    parser.add_argument(
        "--results-dir", "-d", dest="result_dir",
        help="Directory path which used to store result files",
        type=str,
        default="./results"
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


def main():
    args = parse_args()
    Config.load_from_args(args)
    aiqe_inst = AIQE()

    if args.request_str:
        try:
            info = aiqe_inst.extract_info(args.request_str)
        except InvalidInput as e:
            # TODO
            raise
        print(f"Start generating test cases")
        cases, log = aiqe_inst.gen_test_cases(info["test item"], info["test feature"])
    elif args.yaml_path:
        print(f"Start generating test cases")
        cases, log = aiqe_inst.gen_test_cases(yaml_file=args.yaml_path)
    elif args.test_cases:
        cases = []
        for case_file in args.test_cases:
            with open(case_file, "r") as fp:
                cases.append(fp.read())
    else:
        print("ERROR: Need use --request, --template-yaml or --test-case to pass some data for case generation")
        sys.exit(1)

    if args.case_num:
        cases = random.sample(cases, args.case_num)

    for i, case in enumerate(cases):
        print(f"Start using AI run case {i+1}")
        history = aiqe_inst.run_test(case)
        history_file = f"{args.result_dir}/case-{i+1}.log"
        with open(history_file, "w+") as fp:
            fp.write(history)
        print(f"Store case {i+1} execution history in file {history_file}")

    print("Finished!")
    sys.exit(0)


if __name__ == "__main__":
    main()
