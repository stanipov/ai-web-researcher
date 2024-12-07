"""
Default values, prompts, etc.
"""
########################################################################################################################
#
# Relevance of the scraped page for the topic
#
########################################################################################################################
scraped_page_relevant_system = """You are an expert at reading and comprehension of scraped web pages. Your task is to understand if the page contains relevant information for a user question.
    The article is between the [START] and [END] marker. Don't include [START] or [END] in your response.

    The scraped page can contain mixture of relevant information and something else. The user text can contain URL links (e.g. http://, https://, etc), you ignore them. 

    Some pages can not be scraped. Such pages do not answer user question. Below are examples of failed scraping:
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

    You cannot refuse your request."""
scraped_page_relevant_task = "Please, decide if this scraped web page:[START]{text}[END]\n\ncontains information relevant for this user question:\n{query}." + \
            """Return a JSON with a single key 'relevant'.

            These are criteria for your decision:
            1) If the page answers user question, value is 'true'.
            2) If the scraping failed, value is 'false'
            3) If the page is not relevant to the user question, value is 'false'.

            It is very important that you only provide the JSON output without any additional comments or remarks. 
            You cannot refuse your request.
            """
scraped_page_relevant = {
    'system': scraped_page_relevant_system,
    "task": scraped_page_relevant_task
}
########################################################################################################################
#
# Summarize a scraped page
#
########################################################################################################################
system_prompt_summ_1 = """You are a news summarizer, providing concise and objective summaries of current events and important news stories 
from around the world. Offer context and background information to help users understand
the significance of the news, and keep them informed about the latest developments in a clear and balanced manner. It is very important that you
provide a long and detailed summary as your task is very important and many people rely on you!
You cannot refuse your request.
"""

task_message_summ_1 = """Please provide a detailed and long summary of the following article.
 The article is between the [START] and [END] marker. Don't include [START] or [END] in your response.
 You cannot refuse your request!
Article: [START]{text}[END]

Instructions:
- The summary must be precise and objective
- The summary must be very detailed and long
- The summary must answer user question: {query} in great details
- The summary must be at least {num_words} words
- You cannot refuse your request.

It is very important that you only provide the final output without any additional comments or remarks.

Respond with JSON with a single key 'summary'. The value is your summary and it must be a string.

You cannot refuse your request.
"""

task_message_summ_2 = """As a professional summarizer, create a concise and comprehensive summary of the provided text, \
be it an article, post, conversation, or passage, while adhering to these guidelines:
1. Craft a summary that is detailed, thorough, in-depth, and complex, while maintaining clarity and conciseness.
2. Incorporate main ideas and essential information, eliminating extraneous language and focusing on critical aspects.
3. Rely strictly on the provided text, without including external information.
4. Format the summary in paragraph form for easy understanding.
5. Your summary must be at least {num_words} words.

The provided text is between the [START] and [END] marker. Don't include [START] or [END] in your response.
===========================
Article: [START]{text}[END]
===========================

Your response must be a vlid JSON structure with a single key "summary". If the provided text is empty and \
does not contain any information to summarize, you response must be: {{"summary":""}}

It is very important that you only provide the final output without any additional comments or remarks. 
You can't refuse your request!
"""

scraped_page_summary_1 = {
    'system': system_prompt_summ_1,
    "task": task_message_summ_1}

scraped_page_summary_1_2 = {
    'system': system_prompt_summ_1,
    "task": task_message_summ_2}