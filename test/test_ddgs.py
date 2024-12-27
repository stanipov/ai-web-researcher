from duckduckgo_search import DDGS


class DuckDuckGoWrapper:
    def __init__(self, source, region="wt-wt", safesearch="off", max_results=5, timeout=10):
        """
        Initializes the DuckDuckGoWrapper.

        :param source: Source type ('text' or 'news').
        :param region: Region code (default 'wt-wt').
        :param safesearch: Safe search level ('on', 'moderate', or 'off'). Default is 'off'.
        :param max_results: Maximum number of results to return (default 5).
        :param timeout - int - Timeout value for the HTTP client. Defaults to 10.
        """
        if source not in ('text', 'news'):
            raise ValueError("source must be 'text' or 'news'")

        self.source = source
        self.region = region
        self.safesearch = safesearch
        self.max_results = max_results
        self.timeout = timeout
        self.engine = DDGS(timeout=timeout)

    def run(self, query):
        """
        Searches DuckDuckGo based on the query and source type.

        :param query: The search query string.
        :return: List of search results.
        """
        if self.source == 'text':
            return list(self.engine.text(keywords=query, region=self.region, safesearch=self.safesearch, max_results=self.max_results))
        elif self.source == 'news':
            return list(self.engine.news(keywords=query, region=self.region, safesearch=self.safesearch, max_results=self.max_results))


# Example usage:
if __name__ == "__main__":
    # Initialize the wrapper
    wrapper = DuckDuckGoWrapper(source='news', region='us-en', safesearch='moderate', max_results=3)

    # Run a search
    results = wrapper.run("OpenAI GPT")

    # Print results
    for result in results:
        print(result)