from typing_extensions import TypedDict
from typing import Annotated, Dict, Union

class SimpleSummarizerState(TypedDict):
    """State for a simple agent"""
    text: str
    query: str
    num_words: Union[int, str]
    summary: str
    relevant: bool

class AdvancedSummarizerState(TypedDict):
    """State for agent which rewrites user prompt for better relevance and summarization"""
    text: str
    query: str
    new_prompt: str
    num_words: Union[int, str]
    summary: str
    relevant: bool