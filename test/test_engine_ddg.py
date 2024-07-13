import sys
sys.path.append("./src")

from src.engines.ddg import DDG
from utils.utils import set_logger


if __name__ == "__main__":

    import os
    from uuid import uuid4
    from hashlib import md5

    logger = set_logger()
    fake_responses = ['true']
    agent = None
    query1 = "What is a metric tensor?"
    query2 = "Trump Biden debates June 2024 in news"
    max_results = 20

    # saving the query results
    # each result into a single text file
    save_fld = os.path.join(os.getcwd(), *("data",str(uuid4())))
    os.makedirs(save_fld, exist_ok=True)

    # runnig the actual query
    ddg = DDG(agent=agent, max_results=max_results)
    ans = ddg.invoke(query2)

    for res in ans:
        fname = md5(ans[res]['text'].encode('utf-8')).hexdigest() + ".txt"
        fname = os.path.join(save_fld, fname)
        msg = f"URL: {res}\n============\nResults:\n{ans[res]['text']}"
        with open(fname, 'w') as f:
            f.write(msg)

    #for res in ans:
    #    print(res)
    #    print(f"\t{ans[res]['text']}")
    #    print("============================================")
    #    print("============================================")
    #    print("============================================")
    #    print("============================================")
    #    print("============================================")

