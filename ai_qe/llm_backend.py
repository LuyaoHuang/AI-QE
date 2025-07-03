import os
import logging

try:
    from .config import Config
except ImportError:
    from config import Config


def prepare_llm(model_name):
    if model_name.startswith("gemini"):
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError:
            logging.error("Need install langchain_google_genai before use it")
            raise

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Cannot find GEMINI_API_KEY in env")

        llm = ChatGoogleGenerativeAI(
            model= model_name,
            temperature=1.0,
            max_retries=2,
            google_api_key=api_key,
        )
    else:
        try:
            from langchain_ollama import ChatOllama
        except ImportError:
            logging.error("Need install langchain_ollama before use it")
            raise

        # If not set OLLAMA_HOST, use default config
        if not os.environ['OLLAMA_HOST']:
            os.environ['OLLAMA_HOST'] = f"http://{Config.llm_server_ip}:{Config.llm_server_port}"
        llm = ChatOllama(model=model_name, temperature=0)
    logging.info(f"Load {model_name} LLM")
    return llm
