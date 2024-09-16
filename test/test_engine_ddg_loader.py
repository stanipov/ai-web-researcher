import sys
sys.path.append("./src")

from engines.ddg import DDG_Scraper
from engines.loaders import ExtChromiumLoader
from utils.utils import set_logger
import asyncio


if __name__ == "__main__":

    import os
    import asyncio
    from uuid import uuid4
    from hashlib import md5

    logger = set_logger()

    path_to_extension = "/ext4/software/browser/bpwc"

    query1 = "What is a metric tensor?"
    query2 = "Trump Biden debates June 2024 in news"
    query2 = "Trump assassination in Pennsylvania"
    max_results = 10

    loader = ExtChromiumLoader(ext_path=path_to_extension, headless=True)

    # running the actual query
    ddg = DDG_Scraper(loader, max_results=max_results)
    ans = asyncio.run(ddg.ainvoke(query2))

    print(ans.keys())

    print('\n***********************************************************************\n')
    for i,url in enumerate(ans):
        print(f"{i} -- URL: {url}")
        print(f"Sample: {ans[url]['text'][0:100]}\n{'*'*80}\n")