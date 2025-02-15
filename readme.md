# AI Agentic News Search Engine
# Overview
Let the AI agents to search and summarize news for you using your own LLM!

Provide your topic for which you want to get a news report, and the LLM powered agent will generate it for you by:
- drafting a plan for the report
- by calling a search engine and gathering the URLs
- by text scraping using the custom-made scraper
- and writing the report for you using agentic critic

The purpose of the custom scraper is to enable extensions to 
bypass soft paywalls, like [this](https://gitflic.ru/project/magnolia1234/bypass-paywalls-chrome-clean) 
for Chromium browser. 

The project is modular. Every component is built with idea that it performs a single task and 
provides an API calls for its actions. These components are stacked later together by a 
governing class tha drives them to perform higher level operations. 

Current implementation creates does the core function - calls a search engine, scrapes the data, cleans and 
summarizes the results, and saves them locally. Due to temporal inability to access my 24Gb GPU, I can't 
complete the report-writing part as it requires an LLM with a fairly large context window. 

Below is more detailed architecture description

# Main actions/classes
Below is description major steps and related classes.

## Data search and scraping
This is a compound action which is governed by a **WebSearchGvt** class. It is instantiated using own
JSON config. The class instance provides convenient wrappers over multiple components:
- search engine invocation
- the actual web scraping and conversion to a plain text
- summarization/clean-up using an LLM tools
- interface to save the data after each step and retrieve them
- logging and debugging helpers

### Search engine
The default search engine is DuckDuckGo due to its free nature. As my intention is to use this tool 
as some sort of local service providing regular reports/reviews for me on different topics, I do not
want to pay for API calls from the well known engines.

The code uses an unofficial Python client, but allows to search in a region, news specifically, date, etc.
I.e. handy for a service doing a news review for you.

The internals are fairly straightforward in the [ddg.py](src/scrapers/ddg.py).
- A wrapper for a DDG search client. Depending on a source, the client provides slightly different
output
- A scraper which governs the DDG search wrapper and uses a provided loader to obtain the texts

### Loader
This thing is what others might have named scraper. It uses Playwright to govern Chromium browser with extensions.
The whole point of writing this class was to be able to bypass some of the soft paywalls. Yes, I am cheap.

## Data clean up
### Summarizer
This module cleans and summarizes/shortens the scraped texts. Internally it utilizes a simple LangChain pipe.
I intentionally avoided using function calling or structured output as I wished to be able to use pretty much
any LLM.

The class is instantiated with a provided LLM client (LangChain runnable) and instructions 
for the text clean up. I keep naming in summarization since my first experiments, but in essence this is 
an HTML text clean up and shortening. The [defaults.py](src/utils/defaults.py) keeps some of the prompts I 
tried and found producing OK results with different LLMs. 

The prompts ask the LLM to produce a JSON formatted answer. 8b/7b models sometimes fail to produce a valid 
JSON output producing a plain text, thus [summarize()](summarizers.PlainSummarizer.summarize) method 
contains 2 strategies:
- it tries to parse the raw output which is often a plain text
- if no raw output was provided, it queries the LLM again (number of attempts is a parameter, default 1)

## Web searching 
The above classes are used in a compound class to perform the web search.

### WebSearchTool
This is a compound class that governs the Search Engine and the Summarizer. The higher-up governor will only 
send a query and receive data, no matter if it comes from a web scrape or RAG. 

This class abstracts all intermediate steps for searching for a query, data scraping, and text clean up. It 
provides convenient wrappers after all components are initialized. 

### Web Search Governor
This is another compound class. It combines and abstracts intermediate steps needed to scrape and summarize texts.
The class instantiates all the classes above, sends data and handles exceptions/errors produced by the "smaller" 
classes.

The class requires a config as a nested dictionary to instantiate all dependencies. 

See Examples section for examples on how to use it.


# Examples

## Web search
The WebSearchGvt described above provides an easy way to retrieve summarized and raw search results for a given query.
 
### Typical config
```commandline
srch_gov_config = {
        "summarization_props":{
            "name": "simple", # 'simple' is only available
            "task_prompt": "v2", # see deafaults.py for variants, 
                                 # but the latest is typically the best
            "sum_num_retries": 1, # number of retries if LLM produces unparseable output
            "frac2sum": 0.4, # not all task prompts use, maximal word count as a fracion 
                             # of word count of original text 
            "min_txt_len": 200, # minimal text lenght for summarization, 
                                # mainly used to filter out incorrect results 
                                # (such as  page not found, "your browser is blocked", etc.)
            "max_txt_len": 9000, # maximal word count of the input text for LLM 
                                 # clean-up/summarization (typically to avoid unresonably 
                                 # long gibberish or respect LLM's context window)
            "max_summ_len_abs": 900, # absolute word count for the cleaned text
        },

        "llm": {
            "type": "api:openai", # local:ollama, api:groq, 
                                  # i.e. follow the pattern <local/api>.<service name>
            "api_key": "ABCD123456789", # your API key,
            "model_name": "model-name", 
            "retry_sleep": 1, # delay between api calls, in seconds
            "req_timeout": 240, # maximal timeout in sec
            "temperature": 0.25, # temperature
            "model_kw": None # model keywords,
                             # If using Ollama, you can add these key:value pairs directly 
                             # (default value/type if not None):
                             # "keep_alive": None/int,
                             # "num_ctx": None/int,
                             # "num_predict": None/int,
                             # "repeat_last_n": 64/int,
                             # "repeat_penalty": None/float,
                             # "top_p": None/float            
        },

        "scrape": {
            "loader": "chromium",  # only supported browser
            "ext_path": </path/to/extension>, 
            "headless": False, # headless works, but not all pages are loaded
            "cookie_btns": ['Accept', 'Allow', 'Consent', 'OK', 'Continue'], 
                           #list or None, text on cockie consent button
            "user_agent": None, # str or None
            "proxy": None, # Dict[str, str] or none 
                           # read: https://playwright.dev/python/docs/network#http-proxy

        },
        "search_engine": {
            "name": "ddg",  # only supported
            "region": "wt-wt",  # not used for now, def "wt-wt" -- no region specified
            "time":  None, #  "d",  # None as default, options: d, w, m, y
            "max_results": 15,
            "search_source": 'text',  # news, text
            "safe_search": "off",
            "timeout": 30 # in sec, def 10 sec
        },

        "data": {
            "save_dir": </path/to/save>, 
            "error_dump_dir": </path/to/dump>, # if provided, some classes will dump 
                                               # Pickled objects which cause problems. 
        }

    }
```

### Typical usage
```commandline
from src.governors.search import WebSearchGvt
import asyncio

config = {...}

wb_tool = WebSearchGvt(config)
query = "Why is sky blue?"

# search for the query
ans = asyncio.run(wb_tool.ascrape(query))

# save your raw scraped data
wb_tool.write(ans, 'scrape')

# clean-up/summarize all scraped results 
s_ans = wb_tool.summarize(ans)

# save everything to another subfoled
wb_tool.write(s_ans, 'final')
```

## Requirements
- python >= 3.11
- Langchain
- playwright
- [duckduckgo-search](https://pypi.org/project/duckduckgo-search/)
- Langchain's Ollama, OpenAI, and GroQ clients