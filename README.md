# AI-QE Demo

This is a small demo of AI-QE project, see this [document](https://docs.google.com/document/d/14junFERydMKpUXIzCqAaHExIuNCk8jvDuziGIT2hQ9o/edit) to know more about it

## Prepare a LLM with text-generation-webui

1. Prepare a host/vm/container which have NVIDIA GPU and CUDA toolkit

2. Install [text-generation-webui](https://github.com/oobabooga/text-generation-webui)

3. Following the [document](https://github.com/oobabooga/text-generation-webui#downloading-models) to download a Mistral based (model_type is mistral in config.json) LLM from [HuggingFace](https://huggingface.co/spaces/HuggingFaceH4/open_llm_leaderboard)

4. Start text-generation-webui server with option --listen and --api to enable API interface
```
$ python server.py --model NeuralMarcoro14-7B --listen --api
```

## Try the Demo

Now you can run ai-qe.py to use LLM execute a test case
```
$ python3.9 ai-qe.py -s {text_generation_webui_server_ip} -t example_case.txt
```
