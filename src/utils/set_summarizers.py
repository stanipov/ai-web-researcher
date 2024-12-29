# logging
import logging
from typing import Dict, Any

from langchain_community.tools.playwright.utils import run_async
from langchain_core.runnables.base import Runnable
logger = logging.getLogger(__name__)

from src.agents.summarizers import PlainSummarizer
from src.utils.defaults import scraped_page_cleanup


"""
        "summarization_props":{
            "name": "simple",
            "task_prompt": "v1",
            "sum_num_retries": 1,
            "frac2sum": 0.3,
            "min_txt_len": 200,
            "max_txt_len": 9000,
            "max_summ_len_abs": 800,
            "max_len_to_sum": 5000,
        },
        "data": {
            # will save as parquet
            "save_dir": os.getenv('data_dump_dst'),
            "error_dump_dir": "/ext4/proj/2024/ai-web-researcher/experiments/dump"
        }
"""
MANDATORY_KEYS = {
    'summarization_props': {
        'name': ['simple']
    }
}

class SummarizerInit:
    def __init__(self, *args, **kwargs):
        """
        Nothing to pass yet
        """
        pass

    def set_summarizer(self, config: Dict[str, Any], llm: Runnable) -> Runnable:

        for entry in MANDATORY_KEYS:
            if entry not in config:
                msg = f"Missing mandatory entry {entry}"
                logger.error(msg)
                raise KeyError(msg)
            for key in MANDATORY_KEYS[entry]:
                if config[entry][key].lower() not in MANDATORY_KEYS[entry][key]:
                    msg = f"Value for \"{key}\" is not recognized. Allowed values: \"{', '.join(MANDATORY_KEYS[entry][key])}\""
                    logger.error(msg)
                    raise ValueError(msg)

        summarizer = None
        if config['summarization_props']['name'].lower() == 'simple':
            task_v = config['summarization_props'].get('task_prompt', 'v1').lower()
            if task_v in scraped_page_cleanup:
                summ_msg = scraped_page_cleanup[task_v]
            else:
                msg = f"Prompt version is not recognized! Got {task_v}, allowed: {', '.join(list(scraped_page_cleanup.keys()))}"
                logger.error(msg)
                raise KeyError(msg)

            if 'data' in config:
                error_dump_dir = config['data'].get('error_dump_dir', None)
            summarizer = PlainSummarizer(summ_msg, llm, error_dump_dir)

        return summarizer