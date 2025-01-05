import logging
from typing import List, Dict, Union, Optional

from src.utils.utils import count_words
import time
from hashlib import md5
from datetime import datetime

logger = logging.getLogger(__name__)

class WebSearchTool:
    def __init__(self,
                scraper,
                summarizer,
                frac2sum:float=0.3,
                hard_sum_th:int=700,
                min_txt_len:int=200,
                max_txt_len:int=5000,
                sum_num_retries:int=1,
                api_retry_time:int=3,
                ):
        """
        Wrapper to perform a query search and summarize the results.
        scraper: a class instance that scrapes an url. It must support at least invoke method.
        """
        if scraper is not None:
            self.scraper = scraper
        else:
            logger.error(f"Scraper can't be None!")
            return None

        self.summarizer = summarizer
        self.frac2sum = frac2sum
        self.hard_sum_th = hard_sum_th
        self.min_txt_len = min_txt_len
        self.sum_num_retries = sum_num_retries
        self.api_retry_time = api_retry_time
        self.max_txt_len = max_txt_len

    async def ascrape_query(self, query: str) -> Dict[str, str]:
        """
        Async scrape of data for a query
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
            search_results = await self.scraper.ainvoke(query)
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
                search_results[url]['model_name'] = self.summarizer.model_name
                search_results[url]['headless'] = self.scraper.loader.is_headless()

            logger.info(f"Finished scraping in {time.time() - t_start:.1f} seconds")

        return search_results

    def scrape_query(self, query: str) -> Dict[str, str]:
        """
        Sync scrape of a query results
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
        Sync scrape of queries in a list
        """
        if type(queries) != list:
            logger.error(f"Queries must be type List[str], got {type(queries)}")
            return None
        results = {}
        for q in queries:
            r = self.scrape_query(q)
            results.update(r)
        return results

    async def ascrape_queries(self, queries: List[str]) -> Dict[str, str]:
        """
        Async scrape of queries in a list
        """
        if type(queries) != list:
            logger.error(f"Queries must be type List[str], got {type(queries)}")
            return None
        results = {}
        for q in queries:
            r = await self.ascrape_query(q)
            results.update(r)
        return results

    def summarize_search_results(self, results:Dict[str, str]) -> Dict[str, str]:
        """
        Summarizes all scraped results
        """
        if results is not None:
            for idx, url in enumerate(results):
                text_count = results[url]['text_count']
                if text_count > self.min_txt_len and text_count <= self.max_txt_len:
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
                    else:
                        logger.warning(f"Summarization has failed, skipping")

                    logger.info(f"Waiting {self.api_retry_time} sec")
                    time.sleep(self.api_retry_time)
                else:
                    logger.warning(f"Too short or too long for summarization (got ~{text_count} words), passing")


            return results

        else: # nothing to summarize
            return None