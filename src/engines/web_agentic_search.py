import logging
from typing import List, Dict, Union
from engines.ddg import DDG
from agents.summarizers import SimpleSummarizer
from string import punctuation
from utils.utils import count_words


class WebAgentSearch:
    def __init__(self,
                 agent: SimpleSummarizer,
                 web_engine,
                 summ_length: float = 0.3,
                 summ_abs_len: int = 900) -> None:
        self.logger = logging.getLogger('WebAgentSearch')
        self.agent = agent
        self.engine = web_engine
        self.punkt = set(punctuation)
        self.summ_len = summ_length  # relative length
        self.summ_abs_max = summ_abs_len  # absolute maximal length of the summary

    def summarize(self, query: Dict[str, Union[str, int, float]]) -> Dict[str, str]:
        return self.agent.invoke(query)

    def invoke(self, query) -> Dict[str, str]:
        self.logger.info(f'Searching "{query}"')
        search_results = self.engine.invoke(query)
        for url in search_results:
            raw_txt_word_cnt = count_words(search_results[url]['text'], self.punkt)
            agent_query = {
                "query": query,
                "text": search_results[url]['text'],
                "num_words": min(int(raw_txt_word_cnt * self.summ_len), self.summ_abs_max)
            }
            self.logger.info(f"Input: {raw_txt_word_cnt}, target: {agent_query['num_words']}, url: {url}")
            sum_url = self.summarize(agent_query)
            search_results[url]['relevant'] = sum_url['relevant']
            search_results[url]['summary'] = sum_url['summary']
            search_results[url]['query'] = query
            search_results[url]['text_count'] = raw_txt_word_cnt
            search_results[url]['summ_count'] = count_words(sum_url['summary'], self.punkt)

        return search_results
