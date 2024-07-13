from typing_extensions import TypedDict
from typing import Annotated, Dict, Union

class SimpleSummarizerState(TypedDict):
    text: str
    query: str
    summary: str
    relevant: bool