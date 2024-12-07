import logging
from typing import List, Dict, Union, Optional

from IPython.utils.openpy import read_py_url

from utils.utils import count_words
import time
from hashlib import md5
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSearchTool:
    def __int__(self, scraper, summarizer,
                frac2sum:float=0.3,
                hard_sum_th:int=700,
                min_txt_len:int=200,
                sum_num_retries:int=1,
                api_retry_time:int=3
                ):
        """
        Wrapper to perform a query search and summarize the results.
        """
        if scraper is not None:
            self.scraper = scraper
        else:
            logger.error(f"Scraper can't be None!")
            return -1
        self.summarizer = summarizer
        self.frac2sum = frac2sum
        self.hard_sum_th = hard_sum_th
        self.min_txt_len = min_txt_len
        self.sum_num_retries = sum_num_retries
        self.api_retry_time = api_retry_time

    def scrape_query(self, query: str) -> Dict[str, str]:
        """
        Scrapes data for a query
        """

        # check the inputs
        if query is None:
            logger.warning(f"Query can't be None!")
            return None
        if query == "":
            logger.warning(f"Query can't be empty string!")
            return None

        _ok = True
        search_results = {}
        t_start = time.time()
        logger.info(f"Query: \"{query}\"")

        try:
            search_results = self.scraper.invoke(query)
        except Exception as e:
            logger.error(f"Query: {query} failed with \"{e}\"")
            _ok = False

        if _ok:
            # add some metadata:
            for url in search_results:
                search_results[url]['text_count'] = count_words(search_results[url]['text'])
                search_results[url]['query'] = query
                search_results[url]['summ_count'] = ''
                search_results[url]['summary'] = ""
                search_results[url]['id'] = md5(query.encode('utf-8', errors='replace')).hexdigest()
                search_results[url]['ts'] = datetime.utcnow().timestamp()

            logger.info(f"Finished scraping in {time.time() - t_start:.1f} seconds")

        return search_results

    def scrape_queries(self, queries: List[str]) -> Dict[str, str]:
        """
        Scrapes queries in a list
        """
        if type(queries) != list:
            logger.error(f"Queries must be type List[str], got {type(queries)}")
            return None
        results = {}
        for q in queries:
            r = self.scrape_query(q)
            results.update(r)
        return results

    def summarize_search_results(self, results:Dict[str, str]) -> Dict[str, str]:
        """
        Summarizes all scraped results

        """
        for idx, url in enumerate(results):
            text_count = results[url]['text_count']
            if text_count > self.min_txt_len:
                logger.info(f"Summarizing: {idx+1}/{len(results)}.")
                msg = {
                    "query": results[url]['query'],
                    "text": results[url]['text'],
                    "num_words": min(int(text_count * self.frac2sum), self.hard_sum_th)
                }
                sum_url = self.summarizer.summarize(msg,
                                                    num_retries=self.sum_num_retries,
                                                    api_retry_time=self.api_retry_time)
                if sum_url is not None:
                    results[url]['summary'] = sum_url['summary']
                    results[url]['summ_count'] = sum_url['summ_count']

        return results