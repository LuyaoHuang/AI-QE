import argparse
import yaml
import logging


class Config(object):
    llm_server_ip = "0.0.0.0"
    llm_server_port = 11434
    model = "jacob-ebey/phi4-tools"
    verbose = False
    use_vertex_ai = False

    # Default test item modules - can be overridden in config YAML
    test_item_modules = ["memory_doc", "rng_doc", "vm_basic_doc"]
    test_item_dir = "./test_items/"
    case_gen_params = {
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
    remote_execution = {
        "enabled": False,
        "host": "",
        "port": 22,
        "username": "",
        "key_file": "",
        "password": "",
        "remote_work_dir": "/tmp/ai-qe-remote",
        "sync_files": True
    }

    @classmethod
    def load_from_yaml(cls, yaml_file: str):
        logging.info(f"Config loaded from {yaml_file}")
        with open(yaml_file, 'r') as file:
            data = yaml.safe_load(file)

        for key, value in data.items():
            if hasattr(cls, key):
                expected_type = type(getattr(cls, key))

                # Special handling for nested dict configs
                if key in ["case_gen_params", "remote_execution"] and isinstance(value, dict):
                    setattr(cls, key, value)
                    logging.debug(f"Update config {key}={value}")
                # Verify the value type
                elif isinstance(value, expected_type) or (expected_type is str and isinstance(value, (str, int))):
                    setattr(cls, key, value)
                    logging.debug(f"Update config {key}={value}")
                else:
                    logging.warning(f"Type mismatch for {key}: Expected {expected_type}, got {type(value)}")

    @classmethod
    def load_from_args(cls, args: argparse.Namespace):
        logging.info("Config loaded from arguments")
        if args.server_ip:
            cls.llm_server_ip = args.server_ip
            logging.debug(f"Update config llm_server_ip={args.server_ip}")
        if args.server_port:
            cls.llm_server_port = args.server_port
            logging.debug(f"Update config llm_server_port={args.server_port}")
        if args.model:
            cls.model = args.model
            logging.debug(f"Update config model={args.model}")
        if args.use_vertex_ai:
            cls.use_vertex_ai = args.use_vertex_ai
            logging.debug(f"Update config use_vertex_ai={args.use_vertex_ai}")
        if hasattr(args, 'remote_host') and args.remote_host:
            cls.remote_execution["enabled"] = True
            cls.remote_execution["host"] = args.remote_host
            logging.debug(f"Update config remote_execution host={args.remote_host}")
        if hasattr(args, 'remote_user') and args.remote_user:
            cls.remote_execution["username"] = args.remote_user
            logging.debug(f"Update config remote_execution username={args.remote_user}")