from typing import Literal, Dict, Union
from langgraph.graph import StateGraph, START, END
from functools import partial

from agents.agent_states import SimpleSummarizerState, AdvancedSummarizerState
from agents.nodes import BasicJSONNode, BasicStrNode

import logging

def is_relevant_router(state: Union[SimpleSummarizerState, AdvancedSummarizerState]) -> Literal["proceed","__end__"]:
    """Conditional edge function"""
    if state['relevant']:
        return "proceed"
    else:
        return "__end__"


def state_init(state: SimpleSummarizerState):
    return {"summary": ""}


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


class SimpleSummarizer:
    """
    A simple summarizer graph.
    The summarizer will provide summary no longer than a predefined number of words
    (can be any integer or "any" for unrestricted length)
    """
    def __init__(self,
                 val_msgs: Dict[str, str],
                 sum_msgs: Dict[str, str],
                 llm):

        self.logger = logging.getLogger('SimpleSummarizer')

        self.logger.info("Setting the nodes")
        NodeValidator = BasicJSONNode(val_msgs, llm)
        NodeSummarizer = BasicStrNode(sum_msgs, llm, 'summary')

        validator = partial(func_validator, val_node=NodeValidator)
        summarizer = partial(func_summarizer, sum_node=NodeSummarizer)

        self.logger.info("Setting the graph")
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

        self.logger.info("Compiling the graph")
        graph.add_edge('summarize', END)

        self.graph = graph.compile()

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
        try:
            return self.graph.invoke(query)
        except Exception as e:
            self.logger.warning(f"Graph invocation failed with '{e}")
            self.logger.warning(f"Returning rollback values")
            return self.rollback_result(query)



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
                 llm):

        self.logger = logging.getLogger('SimpleSummarizer')

        self.logger.info("Setting the nodes")
        NodeValidator = BasicJSONNode(val_msgs, llm)
        NodeSummarizer = BasicStrNode(sum_msgs, llm, 'summary')
        NodeRewriter = BasicJSONNode(rewrt_msgs, llm)

        validator = partial(func_validator, val_node=NodeValidator)
        summarizer = partial(func_summarizer, sum_node=NodeSummarizer)
        rewriter = partial(func_rephraser, rephr_node=NodeRewriter)

        self.logger.info("Setting the graph")
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
        self.logger.info("Compiling the graph")
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
        try:
            return self.graph.invoke(query)
        except Exception as e:
            self.logger.warning(f"Graph invocation failed with '{e}")
            self.logger.warning(f"Returning rollback values")
            return self.rollback_result(query)