from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from src.scrapers.base_engine import BaseEngine, engine_ainvoke
import asyncio
import re
import logging
from typing import List, Dict, Required, Optional

logger = logging.getLogger(__name__)

class DDG_Scraper(BaseEngine):
    def __init__(self,
                 loader,
                 src_region: Optional[str] ="wt-wt",
                 src_intvl: Optional[str|None] = None,
                 resuts_sep: Optional[str] = "<::SRC_SEP::>",
                 src_source: Optional[str|None] = None,
                 safe_src: Optional[str] = 'off',
                 max_results: Optional[int] = 20) -> None:

        if src_region is None:
            src_region = "wt-wt"
        if src_region == "":
            src_region = "wt-wt"

        self.__ddg_wrapper = DuckDuckGoSearchAPIWrapper(region=src_region,
                                                        time=src_intvl,
                                                        max_results=max_results,
                                                        safesearch=safe_src)
        self.engine = DuckDuckGoSearchResults(api_wrapper=self.__ddg_wrapper,
                                              results_separator=resuts_sep,
                                              source=src_source)
        self.loader = loader
        self.results_sep = resuts_sep
        self.__matcher = re.compile(r'\[([^\]]+)\]')
        self.__matcher2 = re.compile(r"(?<=snippet: )(.*?)(?=, snippet: )")

        # set up RegEx matchers
        subs1 = "snippet: "
        subs2 = "., title:"
        self.snippet_m = re.compile(fr'{subs1}([^\]]+){subs2}')

        subs1 = "title: "
        subs2 = ", link: "
        self.title_m = re.compile(fr'{subs1}([^\]]+){subs2}')

        subs1 = "link: "
        subs2 = ""
        self.url_m = re.compile(fr'{subs1}([^\]]+){subs2}')

    def __parse_response(self, res) -> Dict[str, str]:
        """
        Parses the string response of the DDG search engine into
        a dictionary of results per each URL
        :param res:
        :return:
        """

        response = res.split(self.results_sep)

        ans = {}
        for item in response:
            try:
                short_sum = self.snippet_m.findall(item)[0]
                title = self.title_m.findall(item)[0]
                url = self.url_m.findall(item)[0]
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
        raw_response_str = asyncio.run(engine_ainvoke(self.engine, query))
        response = self.__parse_response(raw_response_str)
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
        raw_response_str = await engine_ainvoke(self.engine, query)
        response = self.__parse_response(raw_response_str)
        urls = list(response.keys())
        scraped_urls = await self.__aload_urls(urls)

        # add the scraped texts:
        for i, url in enumerate(urls):
            if url in scraped_urls.keys():
                response[url]['text'] = scraped_urls[url]
            else:
                response[url]['text'] = ''

        return response