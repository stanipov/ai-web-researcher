import logging
from typing import List, Dict, Required, Optional
from engines.ddg import DDG
from agents.summarizers import SimpleSummarizer

class WebAgentSearch:
    def __init__(self, agent: SimpleSummarizer, web_engine) -> None:
        self.logger = logging.getLogger('WebAgentSearch')
        self.agent = agent
        self.engine = web_engine

    def summarize(self, query: Dict[str, str]) -> Dict[str, str]:
        return self.agent.invoke(query)

    def invoke(self, query) -> Dict[str, str]:
        self.logger.info(f'Searching "{query}"')
        search_results = self.engine.invoke(query)
        for url in search_results:
            agent_query = {
                "query": query,
                "text": search_results[url]['text']
            }
            self.logger.info(f"Summarizing url: {url}")
            sum_url = self.summarize(agent_query)
            search_results[url]['relevant'] = sum_url['relevant']
            search_results[url]['summary'] = sum_url['summary']
            search_results[url]['query'] = query

        return search_results