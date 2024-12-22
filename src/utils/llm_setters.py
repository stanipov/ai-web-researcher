import logging
logger = logging.getLogger(__name__)

from langchain_openai.chat_models import ChatOpenAI
from langchain_groq import ChatGroq

try:
    from langchain_ollama import ChatOllama
    ollama_aoi_d = False
except ModuleNotFoundError as E:
    logger.warning("langchain_ollama is not installed; using drop-in replacement")
    ollama_aoi_d = True

from typing import Dict, List
from langchain_core.runnables.base import Runnable

class LLMWrapper:
    """
    TODO
        - add support of more parameters for a "native" support of Ollama as these
        go typically to model_kwargs of API model
    """
    def __init__(self):
        self.ollama_aoi_d = ollama_aoi_d
        self.ollama_base_url = "http://localhost:11434/v1"
        self.ollama_api = "ollama"
        self.__mandatory_fields = ['type', 'api_key', 'model_name']
        self.__supported_services = ['openai', 'groq', 'ollama']
        self.__supported_srv_types = ['api', 'local']


    def set_llm(self, config: Dict[str, str]) -> Runnable:

        for fld in self.__mandatory_fields:
            assert fld in config, f"{fld} is mandatory field!"
        if "api" in config['type'].lower() and 'local' in config['type'].lower():
            assert len(config['type'].split(':')) == 2, f"\"type\" field must be follow <api/local>:<service name> format, got {config['type']}"
        tp, srv_name = config['type'].lower().split(':')
        assert tp in self.__supported_srv_types, f"Supported types are \"{', '.join(self.__supported_srv_types)}\", got {tp}"
        assert srv_name in self.__supported_services, f"Supported services are \"{', '.join(self.__supported_services)}\", got {srv_name}"

        if tp == 'api':
            assert config['api_key'] is not None and config['api_key']!= '', f"API key can't be empty for an API model!"
        api_key = config['api_key']

        assert config['model_name'] is not None and config['model_name'] != '', f"Model name can't be empty!"
        model_name = config['model_name']

        min_req_interval = config.get('retry_sleep', 0)
        req_timeout = config.get('req_timeout', None)
        max_retries = config.get('max_retries', 1)
        temperature = config.get('temperature', 0)
        model_kw = config.get('model_kw', None)
        max_tokens = config.get('max_tokens', None)

        # ollama specific paramters
        # default values come from
        # # https://python.langchain.com/v0.2/api_reference/ollama/chat_models/langchain_ollama.chat_models.ChatOllama.html
        ol_keep_alive = model_kw.get('keep_alive', None)
        ol_num_ctx = model_kw.get('num_ctx', 2048)
        ol_num_predict = model_kw.get('num_predict', None)
        ol_repeat_last_n = model_kw.get('repeat_last_n', 64)
        ol_repeat_penalty = model_kw.get('repeat_penalty', None)
        ol_top_p = model_kw.get('top_p', None)

        llm = None

        if tp == "api":
            if srv_name == 'openai':
                logger.info("Setting OpenAI model")
                llm = ChatOpenAI(
                    model=model_name,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=req_timeout,
                    max_retries=max_retries,
                    model_kwargs = model_kw
                )
            if srv_name == 'groq':
                logger.info("Setting Groq model")
                llm = ChatGroq(model=model_name,
                               temperature=temperature,
                               max_tokens=max_tokens,
                               timeout=req_timeout,
                               max_retries=max_retries,
                               model_kwargs = model_kw)
        if tp == "local":
            if srv_name == 'ollama':
                if self.ollama_aoi_d:
                    logger.info("Using Ollama as OpenAI drop-in replacement")
                    llm =  ChatOpenAI(api_key=self.ollama_api,
                                      base_url=self.ollama_base_url,
                                      model=model_name,
                                      temperature=temperature,
                                      max_tokens=max_tokens,
                                      timeout=req_timeout,
                                      max_retries=max_retries,
                                      model_kwargs=model_kw)
                else:
                    logger.info("Using dedicated langchain's client")
                    llm = ChatOllama(model=model_name,
                                     temperature=temperature,
                                     keep_alive=ol_keep_alive,
                                     num_ctx=ol_num_ctx,
                                     num_predict=ol_num_predict,
                                     repeat_last_n=ol_repeat_last_n,
                                     repeat_penalty=ol_repeat_penalty,
                                     top_p=ol_top_p)

        return llm
