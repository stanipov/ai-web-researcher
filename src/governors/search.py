from src.agents.web_search_tool import WebSearchTool
import os
import json
import logging
from uuid import uuid4
from datetime import datetime, timezone

from src.governors.base_classes import BaseSearchGvt
from src.utils.llm_setters import  LLMWrapper
from src.agents.summarizers import PlainSummarizer
from src.scrapers.ddg import DDG_Scraper
from src.scrapers.loaders import ExtChromiumLoader


logger = logging.getLogger(__name__)

class WebSearchGvt(BaseSearchGvt):
    def __int__(self, config):
        llm_setter = LLMWrapper()
        llm = LLMWrapper.set_llm(config['llm'])

        max_results = config['search_engine']['max_results']
        frac2sum = config['summarization_props']['frac2sum']
        min_txt_len = config['summarization_props']['min_txt_len']
        max_txt_len = config['summarization_props']['max_txt_len']
        sum_num_retries = config['summarization_props']['sum_num_retries']
        api_retry_time = config['llm']['retry_sleep']
        max_summ_len_abs = config['summarization_props']['max_summ_len_abs']
        llm_timeout = config['llm']['req_timeout']
        path_to_extension = config['scrape']['ext_path']
        coockie_btns = config['scrape']['cookie_btns']
        headless_scrape = config['scrape']['headless']


        pass
