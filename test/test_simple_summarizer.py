import sys
sys.path.append("./src")

from utils.utils import set_logger
from agents.summarizers import SimpleSummarizer


def load_txt(fname):
    indat = []
    with open(fname, 'r') as f:
        for line in f:
            indat.append(line.replace('\n', ''))

    return ''.join(indat)


if __name__ == "__main__":
    import os
    from langchain_openai.chat_models import ChatOpenAI

    logger = set_logger()

    src_fld = "/home/sf/data/py_proj/2024/web-researcher/test/data/simple_summarizer"

    ollama_model = "llama3:8b-instruct-q8_0"
    llm = ChatOpenAI(api_key="ollama", model=ollama_model, base_url="http://localhost:11434/v1", temperature=0)

    logger.info(f"Testing the summarizer agent. Input data in {src_fld}")
    logger.info(f"Testing on 2 relevant topics (extract1.txt and extract2.txt)")
    logger.info(f"Offopic text: 'offtopic.txt'")
    logger.info(f"Original query: 'query.txt'")

    logger.info(f"Using {ollama_model} for as agent LLM")
    logger.info("Setting the agent")

    val_msgs = {
        'system': "You are an expert at reading texts and identification if their contetnts are relevant to user question.",
        "task": "Please, decide if this search result:\n{text} is relevant to this user question:\n{query}." + \
                """If the text contains relevant information to the user query, return 'true'. 
                If the text is not relevant to the user question, return 'false.'
                Return a single word, 'true' or 'false' based on the instructions above as a valid JSON with a single key 'relevant' and no premable or explaination.
                """
    }

    system_prompt_summ = "You are Harvard MBA analyst. You are master at understanding what user wants. " + \
                         "You are master at understanding web scraped pages. Your task is to extract and summarize information relecant to the user query." + \
                         "You provide only text. You are not allowed to repeat or rephase the task or this prompt. You are not allowed to write 'I am', 'I am not allowed', etc." + \
                         "Your response MUST be approximately as long as the input text."

    task_message_summ = "Please provide a concies summary of the following text:\n{text}\n\nThe summary shall answer this user question: {query}." + \
                        " The summary shall be very detailed and long. Your work is very valuable, please be very responsible." + \
                        " Finally, provide a text you would be proud to present to your boss." + \
                        "Never start with a premable or explaination."

    summ_msgs = {
        'system': system_prompt_summ,
        "task": task_message_summ}

    agent = SimpleSummarizer(val_msgs=val_msgs, sum_msgs=summ_msgs, llm=llm)

    logger.info("Loading the data")
    files = os.listdir(src_fld)
    logger.info(f"Found: \"{'; '.join(files)}\"")
    query = ''
    topics = {}
    offtopic = {}

    for file in files:
        if 'query' in file:
            query = load_txt(os.path.join(src_fld, file))
        if "extract" in file:
            topics[file] = load_txt(os.path.join(src_fld, file))
        if 'offtopic' in file:
            offtopic[file] = load_txt(os.path.join(src_fld, file))

    print("Testing offtopic summarization")
    for topic in offtopic:

        test_query = {
            "query": query,
            "text": offtopic[topic]
        }
        print(f"***********\nSummarizing: {topic}\nQuery: {query}")
        ans = agent.invoke(test_query)
        print(f"Summary:\n{ans['summary']}")

    print("Testing the relevant summarization")
    for topic in topics:

        test_query = {
            "query": query,
            "text": topics[topic]
        }
        print(f"***********\nSummarizing: {topic}\nQuery: {query}")
        ans = agent.invoke(test_query)
        print(ans.keys())
        print(f"Summary:\n{ans['summary']}")

