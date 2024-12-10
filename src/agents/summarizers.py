from copyreg import pickle
from doctest import debug
from typing import Literal, Dict, Union
from src.utils.utils import make_data_dst

# For a Plain Summarizer
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage
from langchain_core.prompts import HumanMessagePromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import time, os, pickle
from hashlib import md5
from datetime import datetime

from utils.utils import count_words

# logging
import logging
logger = logging.getLogger(__name__)

class PlainSummarizer:
    """
    A simple summarizer which does not use LangGraph's graphs for better control
    and simplicity.

    summarize() method accepts a dictionary message to call the LC chain. The output
    is expected to be a JSON, and if parsing fails, it will make specified number of attempts
    delayed by specified  number of seconds
    """
    def __init__(self,
                sum_msgs: Dict[str, str],
                llm,
                debug_loc:str|None=None):

        sys_summ_prt = sum_msgs.get('system', "")
        task_summ_prt = sum_msgs.get('task', "")
        summ_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=sys_summ_prt),
            HumanMessagePromptTemplate.from_template(task_summ_prt)
        ])
        self.summ_chain = summ_prompt | llm
        self.json_parser = JsonOutputParser()

        try:
            self.model_name = llm.model_name
        except Exception as e:
            logger.warning(f"Could not find model name, use default! Error: {e}")
            self.model_name = "generic_llm"

        if debug_loc:
            if debug_loc == "":
                debug_loc = os.getcwd()
            debug_loc = os.path.join(debug_loc, 'PlainSummarizer')
            os.makedirs(debug_loc, exist_ok=True)
        self.debug_loc = debug_loc

    def summarize(self, sum_msg:Dict[str, str],
                  num_retries: int=0,
                  api_retry_time:int=0) -> Dict[str, str]:
        """
        Summarizes text provided into summ_msg. Contents of the sum_msg depends
        on what variables are expected in the summarization task template.

        For example:
            sum_msg = {
                "query": query text,
                "text": text to summarize,
                "num_words": maximal length summary
            }
        """
        t_start = time.time()
        raw_res = self.summ_chain.invoke(sum_msg)

        _sum = None

        try:
            _sum = self.json_parser.invoke(raw_res)
        except Exception as e:
            logger.error(f"Could not parse the output. Retrying one more time in {api_retry_time} seconds.")
            for i in range(num_retries):
                logger.info(f"Retry: {i+1}/{num_retries} in {api_retry_time} seconds.")
                time.sleep(api_retry_time)
                raw_res = self.summ_chain.invoke(sum_msg)
                try:
                    _sum = self.json_parser.invoke(raw_res)
                except Exception as e:
                    logger.error(f"Retry: {i+1}/{num_retries} failed.")

        if type(_sum) == dict:
            if 'summary' in _sum:
                _sum['summ_count'] = count_words(_sum['summary'])
                logger.info(f"Successfully summarized in {time.time() - t_start :.2f} sec.")
            else:
                logger.error(f"Could not find summary kw in the results: {_sum.keys()}")

                if self.debug_loc:
                    _hs = md5(str(sum_msg).encode('utf-8', 'gnore')).hexdigest()
                    _dt = datetime.utcnow().strftime("%Y-%m-%d")
                    fname = os.path.join(self.debug_loc, f"{_dt}-{_hs}.pkl")
                    logger.debug(f"Dumping results as is to {fname}")
                    dump_obj = {
                        'msg': sum_msg,
                        'raw_response': raw_res,
                        'converted': _sum
                    }
                    try:
                        with open(fname, 'wb') as f:
                            pickle.dump(dump_obj, f)
                        logger.debug("Dump succeed")
                    except Exception as e:
                        logger.error(f"While dumping for this error: {e}")

                _sum = None
        else:
            logger.warning(f"Failed to summarize. Output type: {type(_sum)}")
            _sum = None

        return _sum

########################################################################################################################
#
#                                               Old Stuff to Deprecate
#
########################################################################################################################
from langgraph.graph import StateGraph, START, END
from functools import partial

from agents.agent_states import SimpleSummarizerState, AdvancedSummarizerState
from agents.nodes import BasicJSONNode, BasicStrNode

def is_relevant_router(state: Union[SimpleSummarizerState, AdvancedSummarizerState]) -> Literal["proceed","__end__"]:
    """Conditional edge function"""
    if state['relevant']:
        logger.info("URL is relevant")
        return "proceed"
    else:
        logger.info("URL is NOT relevant")
        return "__end__"


def state_init(state: SimpleSummarizerState):
    return {"summary": "", "relevant": True}


def func_validator(state: Union[SimpleSummarizerState, AdvancedSummarizerState], val_node: BasicJSONNode):
    """Validates the input"""
    message = {
        'text': state['text'],
        'query': state['query']
    }
    return val_node(message)


def func_summarizer(state: Union[SimpleSummarizerState, AdvancedSummarizerState], sum_node: Union[BasicStrNode, BasicJSONNode]):
    """Summarizer function based on basic node"""
    if "new_prompt" in state:
        message = {
            'text': state['text'],
            'query': state['new_prompt'] if state['new_prompt'] != '' else state['query'],
            'num_words': state['num_words']
        }
    else:
        message = {
        'text': state['text'],
        'query': state['query'],
        'num_words': state['num_words']
        }
    return sum_node(message)


def func_rephraser(state: Union[SimpleSummarizerState, AdvancedSummarizerState], rephr_node: BasicJSONNode):
    message = {
        "query": state['query']
    }
    return rephr_node(message)


class D_PlainSummarizer:
    """
    A primitive summarizer graph with unconditional summarization.
    The summarizer will provide summary no longer than a predefined number of words
    (can be any integer or "any" for unrestricted length)
    """
    def __init__(self,
                sum_msgs: Dict[str, str],
                llm,
                num_words_summ_th:int = 300):
        NodeSummarizer = BasicJSONNode(sum_msgs, llm)
        summarizer = partial(func_summarizer, sum_node=NodeSummarizer)

        logger.info("Setting the graph")
        graph = StateGraph(SimpleSummarizerState)
        graph.add_node('init', state_init)
        graph.add_node('summarize', summarizer)
        graph.set_entry_point('init')
        graph.add_edge('init', 'summarize')
        graph.add_edge('summarize', END)
        logger.info("Compiling the graph")
        self.graph = graph.compile()
        self.num_words_summ_th = num_words_summ_th

    def rollback_result(self, query):
        """
        Rollback values when the summarization graph fails. This often happens because
        a model believes it has been asked something it was censored for
        :param query: user query
        :return: SimpleSummarizerState()
        """
        state = SimpleSummarizerState()
        state['text'] = query['text']
        state['query'] = query['query']
        state['num_words'] = query['num_words']
        state['summary'] = 'fail'
        state['relevant'] = True
        return state

    def invoke(self, query: Dict[str, Union[str, int, float]]) -> Dict[str, str]:
        if count_words(query['text']) <= self.num_words_summ_th:
            try:
                return self.graph.invoke(query)
            except Exception as e:
                logger.warning(f"Graph invocation failed with '{e}")
                logger.warning(f"Returning rollback values")
                return self.rollback_result(query)
        else:
            state = self.rollback_result(query)
            state['summary'] = ''
            return state


class SimpleSummarizer:
    """
    A simple summarizer graph.
    The summarizer will provide summary no longer than a predefined number of words
    (can be any integer or "any" for unrestricted length)
    """
    def __init__(self,
                 val_msgs: Dict[str, str],
                 sum_msgs: Dict[str, str],
                 llm,
                 num_words_summ_th:int = 300):

        logger.info("Setting the nodes")
        NodeValidator = BasicJSONNode(val_msgs, llm)
        #NodeSummarizer = BasicStrNode(sum_msgs, llm, 'summary')
        NodeSummarizer = BasicJSONNode(sum_msgs, llm)

        validator = partial(func_validator, val_node=NodeValidator)
        summarizer = partial(func_summarizer, sum_node=NodeSummarizer)

        logger.info("Setting the graph")
        graph = StateGraph(SimpleSummarizerState)
        graph.add_node('init', state_init)
        graph.add_node('validate', validator)
        graph.add_node('summarize', summarizer)
        graph.set_entry_point('init')
        graph.add_edge('init', 'validate')
        graph.add_conditional_edges(
            'validate',
            is_relevant_router,
            {
                'proceed': 'summarize',
                '__end__': END
            }

        )

        logger.info("Compiling the graph")
        graph.add_edge('summarize', END)

        self.graph = graph.compile()
        self.num_words_summ_th = num_words_summ_th

    def rollback_result(self, query):
        """
        Rollback values when the summarization graph fails. This often happens because
        a model believes it has been asked something it was censored for
        :param query: user query
        :return: SimpleSummarizerState()
        """
        state = SimpleSummarizerState()
        state['text'] = query['text']
        state['query'] = query['query']
        state['num_words'] = query['num_words']
        state['summary'] = 'fail'
        state['relevant'] = True
        return state

    def invoke(self, query: Dict[str, Union[str, int, float]]) -> Dict[str, str]:
        if count_words(query['text']) <= self.num_words_summ_th:
            try:
                return self.graph.invoke(query)
            except Exception as e:
                logger.warning(f"Graph invocation failed with '{e}")
                logger.warning(f"Returning rollback values")
                return self.rollback_result(query)
        else:
            state = self.rollback_result(query)
            state['summary'] = ''
            return state


class AdvancedSummarizer:
    """
    More advanced summarizer with rewriting of user promt for better summarization.
    The summarizer will provide summary no longer than a predefined number of words
    (can be any interger or "any" for unrestricted lenght)
    """
    def __init__(self,
                 val_msgs: Dict[str, str],
                 sum_msgs: Dict[str, str],
                 rewrt_msgs: Dict[str, str],
                 llm,
                 num_words_summ_th:int = 300):

        logger = logging.getLogger('SimpleSummarizer')

        logger.info("Setting the nodes")
        NodeValidator = BasicJSONNode(val_msgs, llm)
        NodeSummarizer = BasicStrNode(sum_msgs, llm, 'summary')
        NodeRewriter = BasicJSONNode(rewrt_msgs, llm)
        self.num_words_summ_th = num_words_summ_th

        validator = partial(func_validator, val_node=NodeValidator)
        summarizer = partial(func_summarizer, sum_node=NodeSummarizer)
        rewriter = partial(func_rephraser, rephr_node=NodeRewriter)

        logger.info("Setting the graph")
        graph = StateGraph(AdvancedSummarizerState)
        graph.add_node('init', state_init)
        graph.add_node('validate', validator)
        graph.add_node('prompt_rewriter', rewriter)
        graph.add_node('summarize', summarizer)
        graph.set_entry_point('init')
        graph.add_edge('init', 'validate')
        graph.add_conditional_edges(
            'validate',
            is_relevant_router,
            {
                'proceed': 'prompt_rewriter',
                '__end__': END
            }

        )
        graph.add_edge('prompt_rewriter', 'summarize')
        logger.info("Compiling the graph")
        graph.add_edge('summarize', END)

        self.graph = graph.compile()

    def rollback_result(self, query):
        """
        Rollback values when the summarization graph fails. This often happens because
        a model believes it has been asked something it was censored for
        :param query: user query
        :return: AdvancedSummarizerState()
        """
        state = AdvancedSummarizerState()
        state['text'] = query['text']
        state['query'] = query['query']
        state['num_words'] = query['num_words']
        state['summary'] = 'fail'
        state['relevant'] = True
        state['new_prompt'] = ''
        return state

    def invoke(self, query: Dict[str, Union[str, int, float]]) -> Dict[str, str]:
        if count_words(query['text']) <= self.num_words_summ_th:
            try:
                return self.graph.invoke(query)
            except Exception as e:
                logger.warning(f"Graph invocation failed with '{e}")
                logger.warning(f"Returning rollback values")
                return self.rollback_result(query)
        else:
            state = self.rollback_result(query)
            state['summary'] = ''
            return state