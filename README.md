# AI-QE Demo

This is a demo project of AI-QE.

AI-QE is a AI based project that use LLM to help QE execute manual test cases.

## Prepare a LLM with text-generation-webui

1. Prepare a host/vm/container which have NVIDIA GPU and CUDA toolkit

2. Install [text-generation-webui](https://github.com/oobabooga/text-generation-webui)

3. Following the [document](https://github.com/oobabooga/text-generation-webui#downloading-models) to download a Mistral based (model_type is mistral in config.json) LLM from [HuggingFace](https://huggingface.co/spaces/HuggingFaceH4/open_llm_leaderboard)

4. Start text-generation-webui server with option --listen and --api to enable API interface
```
$ python server.py --model NeuralMarcoro14-7B --listen --api
```

## Install Requirements

1. First install python requirements
```
$ pip install -r requirements.txt
```

2. If you want to use demo codes to test libvirt RNG feature, you need install virt related rpms
```
$ sudo dnf install -y libvirt qemu-kvm
$ sudo systemctl start virtqemud virtnetworkd
```

## Run Demo APP

```
$ python app.py -s {text_generation_webui_server_ip}
```

Now you can open your browser and access http://localhost:7860 to see the demo.
