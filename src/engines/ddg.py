from base_engine import BaseEngine
from langchain_community.tools import DuckDuckGoSearchResults
from base_engine import BaseEngine, engine_ainvoke
import asyncio
import re
import logging
from typing import List, Dict, Required, Optional
from langchain_community.document_transformers import Html2TextTransformer
from langchain_community.document_loaders import AsyncChromiumLoader


class DDG(BaseEngine):
    def __init__(self, agent: Optional=None,
                 max_results: Optional[int]=20,):

        self.logger = logging.getLogger('DDG-Engine')
        self.agent = agent
        self.engine = DuckDuckGoSearchResults(num_results=max_results)
        self.__matcher = re.compile(r'\[([^\]]+)\]')
        self.html2text = Html2TextTransformer()

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
        response = self.__matcher.findall(res)
        ans = {}
        for item in response:
            try:
                short_sum = self.snippet_m.findall(item)[0]
                title = self.title_m.findall(item)[0]
                url = self.url_m.findall(item)[0]
                ans[url] = {
                    "short_sumamry": short_sum,
                    "title": title
                }
            except Exception as e:
                msg = f"\"{e}\" while parsing: \"{item}\""
                self.logger.warning(msg)
        return ans

    def __load_urls(self, urls):
        loader = AsyncChromiumLoader(urls)
        html_chr_a = asyncio.run(loader.aload())
        self.logger.info("Converting HTML to text using html2text")
        ans = self.html2text.transform_documents(html_chr_a)
        self.logger.info("Done converting")
        return ans

    def __validate(self, result):
        pass

    def invoke(self, query):
        # get the search engine response
        raw_response_str = asyncio.run(engine_ainvoke(self.engine, query))
        response = self.__parse_response(raw_response_str)
        urls = list(response.keys())
        scraped_urls = self.__load_urls(urls)

        # add the scraped texts:
        for i,url in enumerate(urls):
            response[url]['text'] = scraped_urls[i].page_content

        return response





