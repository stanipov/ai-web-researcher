import sys
sys.path.append("./src")

from engines.ddg import DDG
from utils.utils import set_logger


if __name__ == "__main__":

    import os
    import asyncio
    from uuid import uuid4
    from hashlib import md5

    logger = set_logger()
    fake_responses = ['true']
    query1 = "What is a metric tensor?"
    query2 = "Trump Biden debates June 2024 in news"
    query2 = "Trump assassination in Pennsylvania"
    max_results = 4

    # saving the query results
    # each result into a single text file
    save_fld = os.path.join(os.getcwd(), *("data", str(uuid4())))
    os.makedirs(save_fld, exist_ok=True)

    # running the actual query
    ddg = DDG(max_results=max_results)
    ans = ddg.invoke(query1)

    print(ans.keys())


    for res in ans:
        fname = md5(ans[res]['text'].encode('utf-8')).hexdigest() + ".txt"
        fname = os.path.join(save_fld, fname)
        msg = f"URL: {res}\n============\nResults:\n{ans[res]['text']}"
        with open(fname, 'w') as f:
            f.write(msg)