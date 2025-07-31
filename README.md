# AI-QE

AI-QE is a tool designed to enhance quality assurance processes by leveraging Large Language Models (LLMs). It automates and streamlines testing workflows through two core functions:

1.  **Test Case Generation**: Utilizes a framework to automatically generate comprehensive test cases, ensuring broad coverage and efficiency in identifying potential issues.
2.  **Test Case Execution and Summarization**: Leverages the tool-calling capabilities of LLMs to execute these generated (or user-provided) test cases and provide summarized results, facilitating quick insights into software performance and reliability.

## Table of Contents

*   [Installation](#installation)
    *   [Python Dependencies](#python-dependencies)
    *   [Virtualization Tools (Optional)](#virtualization-tools-optional)
    *   [Setting up an LLM](#setting-up-an-llm)
        *   [Using Ollama](#using-ollama)
        *   [Using Gemini Models](#using-gemini-models)
        *   [Using Claude Models](#using-claude-models)
*   [Usage](#usage)
    *   [Running the Web Interface](#running-the-web-interface)
    *   [Running via Command Line](#running-via-command-line)
*   [Command-Line Arguments](#command-line-arguments)
*   [Set Log Level](#set-log-level)

## Installation

This section covers how to set up AI-QE and its dependencies.

### Python Dependencies

First, install the required Python packages:

```bash
$ pip install -r requirements.txt
```

### Virtualization Tools (Optional)

If you plan to use the demo codes that test `libvirt` RNG features, you will need to install virtualization-related packages.

```bash
$ sudo dnf install -y libvirt qemu-kvm
$ sudo systemctl start virtqemud virtnetworkd
```

### Setting up an LLM

AI-QE supports local Ollama models, Google's Gemini models, and Claude models via Google Vertex AI. Choose the setup that best fits your needs.

#### Using Ollama

This option allows you to run LLM inference locally, which is ideal if you have local GPU resources.

1.  **Hardware Requirements**: Ensure you have a host, VM, or container with an NVIDIA GPU and the CUDA toolkit installed for optimal performance.
2.  **Install Ollama**: Follow the instructions on the [Ollama GitHub repository](https://github.com/ollama/ollama?tab=readme-ov-file#linux) to install it.
3.  **Pull a Tool-Calling Model**: Pull a model that supports tool calling, such as `jacob-ebey/phi4-tools`:

    ```bash
    $ ollama pull jacob-ebey/phi4-tools
    ```

4.  **Configure Ollama Host (Optional, for network access)**: If you need to access Ollama from another machine, configure `OLLAMA_HOST` in its service file. For example, add `Environment="OLLAMA_HOST=0.0.0.0"` to `/etc/systemd/system/ollama.service` and restart the service:

    ```bash
    # cat /etc/systemd/system/ollama.service |grep Environment
    Environment="OLLAMA_HOST=0.0.0.0"
    # systemctl daemon-reload
    # systemctl restart ollama.service
    ```

#### Using Gemini Models

If you prefer to use Google's Gemini models, you only need an API key. This option does not require local GPU setup.

1.  **Obtain a GEMINI_API_KEY**: Get your API key from the Google AI Studio or Google Cloud Console.
2.  **Set Environment Variable**: Before running `ai-qe`, set your `GEMINI_API_KEY` environment variable:

    ```bash
    $ export GEMINI_API_KEY=YOUR_API_KEY_HERE
    ```
    (Replace `YOUR_API_KEY_HERE` with your actual key.)

#### Using Claude Models

Claude models are supported through Google Vertex AI, providing access to Anthropic's Claude models via Google Cloud infrastructure.

1.  **Set up Google Cloud Project**: Ensure you have a Google Cloud project with Vertex AI enabled.
2.  **Configure Authentication**: Set up authentication for Google Cloud (e.g., using service account credentials or `gcloud auth application-default login`).
3.  **Set Environment Variables**: Before running `ai-qe`, set the required environment variables:

    ```bash
    $ export ANTHROPIC_VERTEX_PROJECT_ID=your-gcp-project-id
    $ export CLOUD_ML_REGION=your-preferred-region
    ```
    (Replace `your-gcp-project-id` with your actual Google Cloud project ID and `your-preferred-region` with your preferred region, e.g., `us-central1`.)

4.  **Install Required Dependencies**: Ensure you have the necessary packages installed:

    ```bash
    $ pip install langchain_google_vertexai anthropic
    ```

## Usage

AI-QE can be run either through a web-based Gradio interface or directly from the command line.

### Running the Web Interface

This starts a local web server, allowing you to interact with AI-QE via your browser.

*   **With Ollama**: Specify your Ollama server's IP address.

    ```bash
    $ ./ai-qe -w -s {ollama_server_ip}
    ```
    Now, open your browser and access `http://localhost:7860` to use the demo.

*   **With Gemini**: Ensure `GEMINI_API_KEY` is set and specify the model.

    ```bash
    $ export GEMINI_API_KEY=XXXXXXXX
    $ ./ai-qe -w -m gemini-2.5-flash
    ```
    Then, open your browser and access `http://localhost:7860`.

*   **With Claude**: Ensure environment variables are set and specify the Claude model.

    ```bash
    $ export ANTHROPIC_VERTEX_PROJECT_ID=your-gcp-project-id
    $ export CLOUD_ML_REGION=your-preferred-region
    $ ./ai-qe -w -m claude-3-5-sonnet@20241022
    ```
    Then, open your browser and access `http://localhost:7860`.

### Running via Command Line

This allows for direct execution of test case generation and execution.

*   **Generate&Execute Test Cases (Ollama Example)**: This command will generate and execute 2 test cases related to the `rng` device hotplug with `rng` and `memory` features.

    ```bash
    $ ./ai-qe -r "generate test case test rng device hotplug with rng and memory feature" -s {ollama_server_ip} -n 2
    ```

*   **Execute Manual Test Cases (Ollama Example)**: You can pass one or more manual test case files for AI-QE to execute.

    ```bash
    $ ./ai-qe -s {ollama_server_ip} -c case1.txt -c case2.txt
    ```

*   **Execute Manual Test Cases (Gemini Example)**: Using Gemini models.

    ```bash
    $ export GEMINI_API_KEY=XXXXXXXX
    $ ./ai-qe -m gemini-2.5-flash -c case1.txt -c case2.txt
    ```

*   **Execute Manual Test Cases (Claude Example)**: Using Claude models.

    ```bash
    $ export ANTHROPIC_VERTEX_PROJECT_ID=your-gcp-project-id
    $ export CLOUD_ML_REGION=your-preferred-region
    $ ./ai-qe -m claude-3-5-sonnet@20241022 -c case1.txt -c case2.txt
    ```

## Command-Line Arguments

Here's a quick reference for common `ai-qe` arguments:

*   `-r "{prompt}"`, `--request "{prompt}"`: Natural language request for test case generation.
*   `-t {path}`, `--template-yaml {path}`: Path to a template YAML file for test case generation.
*   `-c {file}`, `--test-case {file}`: Path(s) to raw test case files for execution (can be used multiple times).
*   `-n {num}`, `--case-number {num}`: Randomly pick up `num` test cases to run (used with `-r` or `-t`).
*   `-d {path}`, `--results-dir {path}`: Directory path to store result files (default: `./results`).
*   `-s {ip}`, `--server-ip {ip}`: Ollama server IP address (required for Ollama).
*   `-p {port}`, `--server-port {port}`: Ollama server Port number.
*   `-m {model_name}`, `--model {model_name}`: LLM model name (e.g., `gemini-2.5-flash`, `jacob-ebey/phi4-tools`, `claude-3-5-sonnet@20241022`).
*   `-f {path}`, `--config-yaml {path}`: Path to a configuration YAML file.
*   `-l {level}`, `--log-level {level}`: Set the logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`; default: `WARNING`).
*   `-w`, `--web`: Run the web interface (starts a Gradio server).
*   `--use-vertex-ai`: Use Vertex AI for Gemini models (default: False).

## Set Log Level

To control the verbosity of the output when using the command line, use the `--log-level` option. Available levels are `DEBUG`, `INFO`, `WARNING`, `ERROR`, and `CRITICAL`. The default level is `WARNING`.

Example:

```bash
$ ./ai-qe -r "generate test case" --log-level DEBUG
```
