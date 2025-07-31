import os
import logging

try:
    from .config import Config
except ImportError:
    from config import Config


def prepare_llm(model_name):
    if model_name.startswith("gemini"):
        if Config.use_vertex_ai:
            try:
                from langchain_google_vertexai import ChatVertexAI
                from google.oauth2.service_account import Credentials
                import vertexai
            except ImportError:
                logging.error("Need install langchain_google_vertexai before use it")
                raise

            auth_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if not auth_file:
                raise ValueError("Cannot find GOOGLE_APPLICATION_CREDENTIALS in env")
            project_name = os.getenv("GOOGLE_CLOUD_PROJECT")
            if not project_name:
                raise ValueError("Cannot find GOOGLE_CLOUD_PROJECT in env")
            location = os.getenv("GOOGLE_CLOUD_LOCATION")
            if not location:
                raise ValueError("Cannot find GOOGLE_CLOUD_LOCATION in env")
            credentials = Credentials.from_service_account_file(auth_file)
            vertexai.init(project=project_name, location=location, credentials=credentials)
            llm = ChatVertexAI(
                model=model_name,
                temperature=1.0,
                max_retries=2,
            )
        else:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
            except ImportError:
                logging.error("Need install langchain_google_genai before use it")
                raise

            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("Cannot find GEMINI_API_KEY in env")

            llm = ChatGoogleGenerativeAI(
                model=model_name,
                temperature=1.0,
                max_retries=2,
                google_api_key=api_key,
            )
    elif model_name.startswith("claude"):
        try:
            from langchain_google_vertexai.model_garden import ChatAnthropicVertex
        except ImportError:
            logging.error("Need install langchain_google_vertexai and anthropic before use it")
            raise

        project_name = os.getenv("ANTHROPIC_VERTEX_PROJECT_ID")
        if not project_name:
            raise ValueError("Cannot find ANTHROPIC_VERTEX_PROJECT_ID in env")

        location = os.getenv("CLOUD_ML_REGION")
        if not location:
            raise ValueError("Cannot find CLOUD_ML_REGION in env")

        llm = ChatAnthropicVertex(
            model_name=model_name,
            project=project_name,
            location=location,
            temperature=1.0,
            max_retries=2,
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
