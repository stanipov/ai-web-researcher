import os
import logging
import asyncio
import copy
from typing import Dict

from pandas.io.formats.info import frame_sub_kwargs
from sqlalchemy.util import await_only

from governors.base_classes import BaseSearchGvt
from utils.llm_setters import  LLMWrapper
from utils.scraper_setters import ScraperInit
from utils.set_summarizers import SummarizerInit
from utils.config import validate_global_config
from utils.data_writers import DaskWriter
from src.agents.web_search_tool import WebSearchTool

logger = logging.getLogger(__name__)

class WebSearchGvt(BaseSearchGvt):
    def __init__(self, config):

        self.__allowed_kinds = ['scrape', 'final', 'all']
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

        # Saving
        logger.info("Setting the savers")
        self.__writer_all = None # saves all data including summaries
        self.__writer_scrape = None # saves intermediary results from scraping: if summary fails, you still want your data saved
        __cfg_all = copy.copy(config['data'])
        __cfg_int = copy.copy(config['data'])
        __cfg_all['save_dir'] = config['data'].get('save_dir', os.getcwd())
        __cfg_all['save_dir'] = os.path.join(__cfg_all['save_dir'], 'final')
        __cfg_int['save_dir'] = config['data'].get('save_dir', os.getcwd())
        __cfg_int['save_dir'] = os.path.join(__cfg_int['save_dir'], 'scrape')

        try:
            self.__writer_all = DaskWriter(__cfg_all)
            logger.info("DataWriter for the final data is set")
        except Exception as e:
            logger.warning(e)
            logger.warning("Could not set the DataWriter for the final data, continue without!")

        try:
            self.__writer_scrape = DaskWriter(__cfg_int)
            logger.info("DataWriter for scrape data is set")
        except Exception as e:
            logger.warning(e)
            logger.warning("Could not set the DataWriter for scrape data, continue without!")


    async def ascrape(self, query: str) -> Dict[str, str]:
        """
        Async scrape data for a query
        """
        if type(query) != str:
            logger.error(f"Query is expected to be a string type, got {type(query)}")
            return None
        return await self.search_tool.ascrape_query(query)

    def scrape(self, query: str) -> Dict[str, str]:
        """
        A sync wrapper to scrape synchronously the query
        """
        if type(query) != str:
            logger.error(f"Query is expected to be a string type, got {type(query)}")
            return None
        return asyncio.run(self.search_tool.ascrape_query(query))

    def write(self, data: Dict, kind: str) -> None:
        """
        Saves data
        :param data: Dict[str, str] - input data to save
        :parm kind: required! - defines if this is the final data or a scrape
                    allowed: "scrape" and "final"/"all"
        """

        if kind not in self.__allowed_kinds:
            logger.error(f"Data kind is not recognised, got \"{kind}\", expected \"{', '.join(self.__allowed_kinds)}\"")
        else:
            if kind == 'scrape':
                if self.__writer_scrape is not None:
                    try:
                        self.__writer_scrape.write(data)
                    except Exception as e:
                        logger.error(f"Error during saving \"{kind}\": \"{e}\"")
                else:
                    logger.warning(f"Can't save \"{kind}\" as the writer is not set!")
            if kind == 'final' or kind == 'all':
                if self.__writer_all is not None:
                    try:
                        self.__writer_all.write(data)
                    except Exception as e:
                        logger.error(f"Error during saving \"{kind}\": \"{e}\"")
                else:
                    logger.warning(f"Can't save \"{kind}\" as the writer is not set!")

    def read(self, kind:str):
        """
        :parm kind: required! - defines if this is the final data or a scrape
                    allowed: "scrape" and "final"/"all"
        """
        ans = None
        if kind not in self.__allowed_kinds:
            logger.error(f"Data kind is not recognised, got \"{kind}\", expected \"{', '.join(self.__allowed_kinds)}\"")
        else:
            if kind == 'scrape':
                if self.__writer_scrape is not None:
                    try:
                        ans = self.__writer_scrape.read()
                    except Exception as e:
                        logger.error(f"Could not read data of \"{kind}\", got: \"{e}\"")
            if kind == 'final' or kind == 'all':
                if self.__writer_all is not None:
                    try:
                        ans = self.__writer_all.read()
                    except Exception as e:
                        logger.error(f"Could not read data of \"{kind}\", got: \"{e}\"")
        return ans

    def summarize(self, data: Dict[str, str]) -> Dict[str, str]|None:
        """
        Summarizes the data

        :param data -- scraped data
        """
        ans = None
        try:
            ans = self.search_tool.summarize_search_results(data)
        except Exception as e:
            logger.error(f"Could not summarize the data with error \"{e}\"")
        return ans