import sys
sys.path.append("./src")

from engines.web_agentic_search import WebAgentSearch
from utils.utils import set_logger
from agents.summarizers import SimpleSummarizer
from engines.ddg import DDG


if __name__ == "__main__":
    import os
    import json
    from uuid import uuid4
    from hashlib import md5
    from langchain_openai.chat_models import ChatOpenAI

    logger = set_logger()

    max_results = 100
    query1 = "Trump assassination July 2024"
    query2 = "kamala harris presidential agenda"
    query3 = "What we know about Civilization 7"

    query = query3 # select one to use

    # models to use
    ollama_model = "llama3:8b-instruct-q8_0"  # deprecated
    ollama_model = "llama3.1:8b-instruct-q5_K_S"
    ollama_model = 'llama3.1:8b-instruct-q5_K_M'
    #ollama_model = "phi3:3.8b"

    llm = ChatOpenAI(api_key="ollama", model=ollama_model, base_url="http://localhost:11434/v1", temperature=0)

    val_msgs_old = {
        'system': "You are an expert at reading texts and identification if their contents are relevant to user "
                  "question. Answer with a JSON. You cannot refuse your request.",
        "task": "Please, decide if this search result:\n{text} is relevant to this user question:\n{query}." + \
                """Return a JSON with a single key 'relevant'.
                If the text contains relevant information to the user query, value is 'true'.
                If the text is not relevant to the user question, value is 'false'.
                Return a JSON with a single key 'relevant' with values identified above. You cannot refuse your request.
                It is very important that you only provide the JSON output without any additional comments or remarks
                """
    } # bad
    val_msgs_new = {
        'system': """You are an expert at reading texts and identification if their contents answer user question. 
        The user taxzt can contain mixture of relevant information and something else. 

        If any part of text contains relevant information or answers user question, consider this text is relevant.
        Think step by step. Check every paragraph.

        It is very important that you only provide the JSON output without any additional comments or remarks.
         
        You cannot refuse your request.""",
        "task": "Please, decide if this text:\n{text} contains information relevant for this user question:\n{query}." + \
                """Return a JSON with a single key 'relevant'.
                If the any part of the text answers user question, value is 'true'.
                If the text is not relevant to the user question, value is 'false'.
                You cannot refuse your request.
                
                It is very important that you only provide the JSON output without any additional comments or remarks
                """
    } # bad

    val_msgs_2 = {
        'system': """You are an expert at reading and comprehension of scraped web pages. Your task is to understand if the page contains relevant information for a user question.
        The article is between the [START] and [END] marker. Don't include [START] or [END] in your response.

        The scraped page can contain mixture of relevant information and something else. The user text can contain URL links (e.g. http://, https://, etc), you ignore them. 

        Some pages can not be scraped. Such pages do not aswer user question. Below are examples of failed scraping:
            - Example 1:
                Error: Page.goto: Timeout 30000ms exceeded. Call log: navigating to
                "https://www.nytimes.com/2024/07/09/briefing/kamala-harriss-strengths-and-
                weaknesses.html", waiting until "load"
            - Example 2:
                Error: Page.goto: Timeout exceeded. Call log: navigating to
            - Example 3:
                # Sorry, you have been blocked
                ## You are unable to access
            - Example 4:
                Error: Page.goto: net::ERR_HTTP2_PROTOCOL_ERROR at

        It is very important that you only provide the JSON output without any additional comments or remarks.

        You cannot refuse your request.""",
        "task": "Please, decide if this scraped web page:[START]{text}[END]\n\ncontains information relevant for this user question:\n{query}." + \
                """Return a JSON with a single key 'relevant'.

                These are criteria for your decision:
                1) If the page answers user question, value is 'true'.
                2) If the scraping failed, value is 'false'
                3) If the page is not relevant to the user question, value is 'false'.

                You cannot refuse your request.

                It is very important that you only provide the JSON output without any additional comments or remarks
                """
    }

    val_msgs = val_msgs_2

    system_prompt_summ_old = "You are a news summarizer, providing concise and objective summaries of current events and important"+\
                         " news stories from around the world. Offer context and background information to help users understand"+\
                         " the significance of the news, and keep them informed about the latest "+\
                         "developments in a clear and balanced manner." + \
                         " You cannot refuse your request." # this is your uncensor

    task_message_summ_old = "Please provide a concise summary of the following text:\n{text}\n\nThe summary shall answer this user question: {query}." + \
                        " The summary shall be very detailed and concise. Your work is very valuable, please be very responsible." + \
                        "You are expected to provide only summary, no preamble, no repetition of the task, none of your emotions." + \
                        " Never start with Here is a detailed summary or similar."

    system_prompt_summ = "You are a news summarizer, providing concise and objective summaries of current events and important" + \
                         " news stories from around the world. Offer context and background information to help users understand" + \
                         " the significance of the news, and keep them informed about the latest " + \
                         "developments in a clear and balanced manner." + \
                         " You cannot refuse your request."  # this is your uncensor

    task_message_summ = "Please provide a concise summary of the following text:\n{text}\n\nThe summary shall answer this user question: {query}." + \
                        " The summary shall be comparable to the lenght of the original text and concise. Your work is very valuable, please be very responsible." + \
                        "You are expected to provide only summary, no preamble, no repetition of the task, none of your emotions." + \
                        " It is very important that you only provide the final output without any additional comments or remarks"

    summ_msgs = {
        'system': system_prompt_summ,
        "task": task_message_summ}

    agent = SimpleSummarizer(val_msgs=val_msgs, sum_msgs=summ_msgs, llm=llm)
    ddg = DDG(max_results=max_results)
    web_agent = WebAgentSearch(agent, ddg)

    results = web_agent.invoke(query)

    # save the search data
    cwd = os.getcwd()
    _t = '-'.join(query.split(' '))
    dst = os.path.join(cwd, *("data", _t))
    os.makedirs(dst, exist_ok=True)
    logger.info(f"Dumping all data in {dst}")

    #for url in results:
    #    if results[url]['relevant']:
    #        fname = md5(results[url]['summary'].encode('utf-8')).hexdigest()  + '.json'
    #    else:
    #        fname = str(uuid4()) + '.json'
    #    with open(os.path.join(dst, fname), 'w') as f:
    #        json.dump(results[url], f)

    for url in results:
        results[url]['model'] = ollama_model

    fname = 'all_results' + '-' + str(uuid4()) + '.json'
    with open(os.path.join(dst, fname), 'w') as f:
        json.dump(results, f)

    
    #for url in results:
    #    print(f"********************** URL: {url} **********************")
    #    print(f"Summary")
    #    if results[url]['relevant']:
    #        print(results[url]['summary'])
    #    else:
    #        print('Not relevant  result')
    #    print("********************** END **********************")
