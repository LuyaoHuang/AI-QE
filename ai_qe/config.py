import argparse
import os


class Config(object):
    llm_server_ip = "0.0.0.0"
    llm_server_port = 5000
    model = "jacob-ebey/phi4-tools"

    # FIXME
    test_item_modules = ["memory_doc", "rng_doc", "vm_basic_doc"]
    test_item_dir = "./test_items/"

    @classmethod
    def load_from_yaml(cls, yaml_file: str):
        pass

    @classmethod
    def load_from_args(cls, args: argparse.Namespace):
        if args.server_ip:
            cls.llm_server_ip = args.server_ip
        if args.server_port:
            cls.llm_server_port = args.server_port
        if args.model:
            cls.model = args.model

        os.environ['OLLAMA_HOST'] = f"http://{cls.llm_server_ip}:{cls.llm_server_port}"
