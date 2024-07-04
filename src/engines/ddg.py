from base_engine import BaseEngine
from langchain_community.tools import DuckDuckGoSearchResults
from base_engine import BaseEngine, engine_ainvoke
import asyncio
import re
import logging
from typing import List, Dict, Required, Optional

from utils.utils import set_logger

class DDG(BaseEngine):
    def __init__(self, llm: Required,
                 agent_task: Required[str],
                 max_results: Optional[int]=20,
                 sys_prompt: Optional[str]=""):

        self.logger = set_logger()
        self.llm = llm
        self.engine = DuckDuckGoSearchResults(num_results=max_results)
        self.__sys_prt = sys_prompt
        self.__matcher = re.compile(r'\[([^\]]+)\]')

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

        pass

    def __validate(self, result):
        pass

    def invoke(self, query):
        raw_response_str = asyncio.run(engine_ainvoke(self.engine, query))
        response = self.__parse_response(raw_response_str)
        if self.llm:
            pass
        return response





