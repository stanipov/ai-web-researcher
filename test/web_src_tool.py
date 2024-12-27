import sys
from web_search_tool import WebSearchTool
sys.path.append("./src")

import os
from datetime import datetime, timezone
from src.utils.utils import set_logger
from dotenv import load_dotenv

def make_data_dst(cwd):
    save_dst = os.path.join(cwd, datetime.utcnow().strftime("%Y-%m-%d"))
    os.makedirs(save_dst, exist_ok=True)
    return save_dst

from src.governors.search import WebSearchGvt

import asyncio

if __name__ == "__main__":
    import pickle
    load_dotenv()
    logger = set_logger()

    srch_gov_config = {
        "summarization_props":{
            "name": "simple", # only supported
            "task_prompt": "v1", # only supported
            "sum_num_retries": 1,
            "frac2sum": 0.3,
            "min_txt_len": 200,
            "max_txt_len": 9000,
            "max_summ_len_abs": 800,
            "max_len_to_sum": 5000,
        },

        "llm": {
            "type": "api:openai", # local:ollama, api:groq, i.e. <local/api>.<service name>
            "api_key": os.getenv('OAI'),
            "model_name": "gpt-4o-mini", #"llama-3.1-8b-instant",
            "retry_sleep": 1,
            "req_timeout": 240,
            "temperature": 0.5,
            "model_kw": None
        },

        "scrape": {
            "loader": "chromium",  # only supported
            "ext_path": os.getenv('chrome_ext_pass'),
            "headless": False,
            "cookie_btns": None,  # ['Accept All', 'Accept', 'Allow', 'Allow All', 'Consent', 'OK', 'Continue'], #list or None
            "user_agent": None, # "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)", # str or None
            "proxy": None, # Dict[str, str] or none, read: https://playwright.dev/python/docs/network#http-proxy

        },
        "search_engine": {
            "name": "ddg",  # only supported
            "region": "wt-wt",  # not used for now, def "wt-wt" -- no region specified
            "time":  "m", #  "d",  # None as default, options: d, w, m, y
            "max_results": 25,
            "search_source": 'news',  # news, text
            "safe_search": "off",
            "timeout": 30 # in sec, def 10 sec
        },

        "data": {
            "save_dir": os.getenv('save_dir'),
            "error_dump_dir": os.getenv('error_dump_dir'),
        }

    }

    query = "What to expect from Trump administration 2025?"
    query = "Trump and China"

    wb_tool = WebSearchGvt(srch_gov_config)
    ans = asyncio.run(wb_tool.ascrape(query))

    logger.info('Saving the scrape results')
    wb_tool.write(ans, 'scrape')

    logger.info("Summarizing the results")
    s_ans = wb_tool.summarize(ans)

    wb_tool.write(s_ans, 'final')
    logger.info("Saving everything")
