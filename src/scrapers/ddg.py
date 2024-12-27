
from src.scrapers.base_engine import BaseEngine, engine_ainvoke
import asyncio
import re
import logging
from typing import List, Dict, Required, Optional
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

class DuckDuckGoWrapper:
    def __init__(self,
                 source:str = 'text',
                 region: str="wt-wt",
                 safesearch: str="off",
                 max_results: int=5,
                 timelimit: str|None = None,
                 timeout: int=10):
        """
        Initializes the DuckDuckGoWrapper.

        :param source: Source type ('text' or 'news').
        :param region: Region code (default 'wt-wt').
        :param safesearch: Safe search level ('on', 'moderate', or 'off'). Default is 'off'.
        :param max_results: Maximum number of results to return (default 5).
        :param timeout - int - Timeout value for the HTTP client. Defaults to 10.
        """
        if source not in ('text', 'news'):
            logger.warning(f"Source must be 'text' or 'news'! Setting to \"text\"")
            source = 'text'

        __allowed_src = ['news','text']
        if type(source) == str:
            self.source = source.lower()
            if self.source not in __allowed_src:
                self.source = 'text'
        else:
            self.source = 'text'

        if type(timelimit) == str:
            if timelimit.lower() not in ['d', 'w', 'm', 'y']:
                timelimit = None
                logger.warning(f"Timelimit not recognized, setting to None. Allowed values: d, w, m, y")
        else:
            timelimit = None

        self.region = region
        self.safesearch = safesearch
        self.max_results = max_results
        self.timeout = timeout
        self.timelimit = timelimit
        self.engine = DDGS(timeout=timeout)

    def __unify_results(self, results:List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Unifies the output results from when source is "news" because
         the output date contains somewhat different keys

         :param results - List[Dict[str, str]] - list of dictionaries of results
        """

        ans = []
        for item in results:
            _t = {
                "title": f"{item['title']} @ {item['source']}",
                "body": item["body"],
                "href": item["url"]
            }
            ans.append(_t)

        return ans

    def run(self, query: str) -> List[Dict[str, str]]:
        """
        Searches DuckDuckGo based on the query and source type.

        :param query: The search query string.
        :return: List of search results.
        """
        if self.source == 'text':
            return list(self.engine.text(keywords=query,
                                         region=self.region,
                                         safesearch=self.safesearch,
                                         max_results=self.max_results,
                                         timelimit=self.timelimit))
        elif self.source == 'news':
            res = list(self.engine.news(keywords=query,
                                         region=self.region,
                                         safesearch=self.safesearch,
                                         max_results=self.max_results,
                                         timelimit=self.timelimit))
            return self.__unify_results(res)


class DDG_Scraper(BaseEngine):
    def __init__(self,
                 loader,
                 src_region: Optional[str] ="wt-wt",
                 src_intvl: Optional[str|None] = None,
                 src_source: Optional[str|None] = None,
                 safe_src: Optional[str] = 'off',
                 max_results: Optional[int] = 20,
                 timeout:int = 15) -> None:

        if src_region is None:
            src_region = "wt-wt"
        if src_region == "":
            src_region = "wt-wt"

        self.engine = DuckDuckGoWrapper(source=src_source,
                                        region=src_region,
                                        safesearch=safe_src,
                                        max_results=max_results,
                                        timeout=timeout,
                                        timelimit=src_intvl)

        self.loader = loader

    def __parse_response(self, res) -> Dict[str, str]:
        """
        Parses the string response of the DDG search engine into
        a dictionary of results per each URL
        :param res:
        :return:
        """


        ans = {}
        for item in res:
            try:
                short_sum = item['body']
                title = item['title']
                url = item['href']
                ans[url] = {
                    "short_summary": short_sum,
                    "title": title
                }
            except Exception as e:
                msg = f"\"{e}\" while parsing: \"{item}\""
                logger.warning(msg)
        return ans

    def __load_urls(self, urls):
        logger.info("Scraping the urls")
        ans = asyncio.run(self.loader.aload(urls))
        logger.info("Scraping is finished")
        return ans

    async def __aload_urls(self, urls):
        logger.info("Scraping the urls")
        ans = await self.loader.aload(urls)
        logger.info("Scraping is finished")
        return ans

    def __validate(self, result):
        pass

    def invoke(self, query):
        """
        :param query: str query to run the search engine
        :return: Dict[url] -> Dict{"short_summary", "title", "text"}
        """
        # get the search engine response
        #raw_response_str = asyncio.run(engine_ainvoke(self.engine, query))
        raw_response = self.engine.run(query)
        response = self.__parse_response(raw_response)
        urls = list(response.keys())
        scraped_urls = self.__load_urls(urls)

        # add the scraped texts:
        for i, url in enumerate(urls):
            if url in scraped_urls.keys():
                response[url]['text'] = scraped_urls[url]
            else:
                response[url]['text'] = ''

        return response

    async def ainvoke(self, query):
        raw_response = self.engine.run(query)
        response = self.__parse_response(raw_response)
        urls = list(response.keys())
        scraped_urls = await self.__aload_urls(urls)

        # add the scraped texts:
        for i, url in enumerate(urls):
            if url in scraped_urls.keys():
                response[url]['text'] = scraped_urls[url]
            else:
                response[url]['text'] = ''

        return response