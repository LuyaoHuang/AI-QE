

class Config(object):
    llm_server_ip = "10.73.179.159" # FIXME
    llm_server_port = 5000

    # FIXME
    test_item_modules = ["memory_doc", "rng_doc", "vm_basic_doc"]
    test_item_dir = "./test_items/"

    @classmethod
    def load_from_yaml(cls, yaml_file: str):
        pass
