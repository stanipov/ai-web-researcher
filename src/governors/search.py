from src.agents.web_search_tool import WebSearchTool
import os
import json
import logging
from uuid import uuid4
from datetime import datetime, timezone

from src.governors.base_classes import BaseSearchGvt
from src.utils.llm_setters import  LLMWrapper
from src.utils.scraper_setters import ScraperInit
from src.utils.set_summarizers import SummarizerInit
from src.utils.config import validate_global_config

logger = logging.getLogger(__name__)

class WebSearchGvt(BaseSearchGvt):
    def __init__(self, config):

        cfg_ok = validate_global_config(config)
        if cfg_ok:
            logger.info("Config contains non-empty entries")
        else:
            logger.error("Config is incorrect, check it!")
            raise ValueError("Config is incorrect, check it!")

        frac2sum = config['summarization_props']['frac2sum']
        min_txt_len = config['summarization_props']['min_txt_len']
        max_txt_len = config['summarization_props']['max_txt_len']
        sum_num_retries = config['summarization_props']['sum_num_retries']
        max_summ_len_abs = config['summarization_props']['max_summ_len_abs']
        api_retry_time = config['llm']['retry_sleep']

        # set the output location
        save_dst = config['data']['save_dir']
        # this is where the tool will save raw results
        tmp_working_dir = os.path.join(save_dst, *('tmp', 'search'))
        logger.info(f"Results will be saved to {save_dst}")
        logger.info(f"Temporal results will be saved in \"{tmp_working_dir}\"")
        err_dump = config['data']['error_dump_dir']
        logger.info(f"Error results will be dumped in \"{err_dump}\"")

        logger.info('Setting the LLM')
        llm_setter = LLMWrapper()
        llm = llm_setter.set_llm(config['llm'])
        if llm is None:
            logger.error(f"Could not set LLM!")
            raise ValueError(f"Could not set LLM!")
        logger.info('LLM is set')

        # scraper
        logger.info("Setting the scraper")
        scraper_setter = ScraperInit()
        scraper = scraper_setter.set_scrapper(config)
        if scraper is None:
            logger.error(f"Could not set scraper!")
            raise ValueError(f"Could not set scraper!")
        logger.info("Scraper is set")

        # Summarizer
        logger.info("Setting the summarizer")
        SummInit = SummarizerInit()
        summarizer = SummInit.set_summarizer(config, llm)
        if summarizer is None:
            logger.error(f"Could not set summarizer!")
            raise ValueError(f"Could not set summarizer!")
        logger.info("Summarizer is set")

        # WebSearchTool
        logger.info("Setting the WebSearchTool")
        self.search_tool = WebSearchTool(scraper=scraper,
                                    summarizer=summarizer,
                                    frac2sum=frac2sum,
                                    hard_sum_th=max_summ_len_abs,
                                    min_txt_len=min_txt_len,
                                    max_txt_len=max_txt_len,
                                    sum_num_retries=sum_num_retries,
                                    api_retry_time=api_retry_time)
        if self.search_tool is None:
            logger.error(f"Could not set search_tool!")
            raise ValueError(f"Could not set search_tool!")
        logger.info("WebSearchTool is set")
