# AI-QE

AI-QE is a tool designed for enhancing quality assurance processes. It comprises two core functions that streamline testing workflows. Firstly, it utilizes a case generator framework to automatically generate test cases, ensuring comprehensive coverage and efficiency in identifying potential issues. Secondly, AI-QE leverages the tool calling ability of Large Language Models (LLMs) to execute these test cases and provide summarized results, facilitating quick insights into software performance and reliability.

## Prepare a LLM with Ollama

1. Prepare a host/vm/container which have NVIDIA GPU and CUDA toolkit

2. Install [ollama](https://github.com/ollama/ollama?tab=readme-ov-file#linux)

3. Pull phi-4 model which enabled tool calling
```
# ollama pull jacob-ebey/phi4-tools
```

4. Add "OLLAMA_HOST=0.0.0.0" in /etc/systemd/system/ollama.service and restart service 
```
# cat /etc/systemd/system/ollama.service |grep Environment
Environment="OLLAMA_HOST=0.0.0.0"
# systemctl daemon-reload
# systemctl restart ollama.service
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

2 way to show the demo:

1. Use app.py to start a gradio sever
```
$ python app.py -s {ollama_server_ip}
```

Now you can open your browser and access http://localhost:7860 to see the demo.

2. Or use cmd.py to run it via command line
```
$ python cmd.py -r "generate test case test rng device hotplug with rng and memory feature" -s {ollama_server_ip} -n 2
```
