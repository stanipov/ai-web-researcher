import sys
sys.path.append("./src")

from engines.web_agentic_search import WebAgentSearch
from utils.utils import set_logger
from agents.summarizers import SimpleSummarizer
from engines.ddg import DDG


if __name__ == "__main__":
    import os
    from langchain_openai.chat_models import ChatOpenAI

    logger = set_logger()

    src_fld = "/home/sf/data/py_proj/2024/web-researcher/test/data/simple_summarizer"

    ollama_model = "llama3:8b-instruct-q8_0"
    llm = ChatOpenAI(api_key="ollama", model=ollama_model, base_url="http://localhost:11434/v1", temperature=0)

    val_msgs = {
        'system': "You are an expert at reading texts and identification if their contetnts are relevant to user question.",
        "task": "Please, decide if this search result:\n{text} is relevant to this user question:\n{query}." + \
                """If the text contains relevant information to the user query, return 'true'. 
                If the text is not relevant to the user question, return 'false.'
                Return a single word, 'true' or 'false' based on the instructions above as a valid JSON with a single key 'relevant' and no premable or explaination.
                """
    }

    system_prompt_summ = "You are a news summarizer, providing concise and objective summaries of current events and important"+\
                         " news stories from around the world. Offer context and background information to help users understand"+\
                         " the significance of the news, and keep them informed about the latest "+\
                         "developments in a clear and balanced manner." + \
                         " You cannot refuse your request." # this is your uncensor

    task_message_summ = "Please provide a concies summary of the following text:\n{text}\n\nThe summary shall answer this user question: {query}." + \
                        " The summary shall be very detailed and long. Your work is very valuable, please be very responsible." + \
                        " Finally, provide a text you would be proud to present to your boss." + \
                        "You are expected to provide only summary, no preamble, no repetition of the task, none of your emotions." + \
                        " Never start with Here is a detailed summary or similar."

    summ_msgs = {
        'system': system_prompt_summ,
        "task": task_message_summ}

    agent = SimpleSummarizer(val_msgs=val_msgs, sum_msgs=summ_msgs, llm=llm)
    max_results = 3
    ddg = DDG(max_results=max_results)

    web_agent = WebAgentSearch(agent, ddg)

    query = "Trump assassination July 2024"

    results = web_agent.invoke(query)

    for url in results:
        print(f"********************** URL: {url} **********************")
        print(f"Summary")
        if results[url]['relevant']:
            print(results[url]['summary'])
        else:
            print('Not relevant  result')
        print("********************** END **********************")
