from typing import Literal, Dict
from langgraph.graph import StateGraph, START, END
from functools import partial

from agents.agent_states import SimpleSummarizerState
from agents.nodes import BasicJSONNode, BasicStrNode

import logging

def is_relevant_router(state: SimpleSummarizerState) -> Literal["proceed","__end__"]:
    if state['relevant']:
        return "proceed"
    else:
        return "__end__"


def state_init(state: SimpleSummarizerState):
    return {"summary": ""}


def func_validator(state: SimpleSummarizerState, val_node: BasicJSONNode):
    message = {
        'text': state['text'],
        'query': state['query']
    }
    return val_node(message)


def func_summarizeer(state: SimpleSummarizerState, sum_node: BasicStrNode):
    message = {
        'text': state['text'],
        'query': state['query']
    }
    return sum_node(message)


class SimpleSummarizer:
    def __init__(self,
                 val_msgs: Dict[str, str],
                 sum_msgs: Dict[str, str],
                 llm):

        self.logger = logging.getLogger('SimpleSummarizer')

        self.logger.info("Setting the nodes")
        NodeValidator = BasicJSONNode(val_msgs, llm)
        NodeSummarizer = BasicStrNode(sum_msgs, llm, 'summary')

        validator = partial(func_validator, val_node=NodeValidator)
        summarizer = partial(func_summarizeer, sum_node=NodeSummarizer)

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

    def invoke(self, query: Dict[str, str]) -> Dict[str, str]:
        return self.graph.invoke(query)