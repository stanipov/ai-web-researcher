import sys
sys.path.append("./src")

from src.engines.ddg import DDG
import asyncio
from langchain_community.llms.fake import FakeListLLM
from utils.utils import set_logger


if __name__ == "__main__":
    logger = set_logger()
    fake_responses = ['true']
    llm = FakeListLLM(responses=fake_responses)
    task = 'task'
    query = "What is a metric tensor?"


    ddg = DDG(llm, task)
    ans = ddg.invoke(query)

    #for res in ans:
    #    print(res)
    #    print(f"\t{ans[res]['short_sumamry']}")

