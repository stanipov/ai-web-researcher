from typing import Annotated, Dict, Union
from typing_extensions import TypedDict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage
from langchain_core.prompts import HumanMessagePromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers import JsonOutputParser


class BasicStrNode:
    """A simple node that runs a chain which returns a string and converts it in a JSON
    :param messages:   contains system prompt and template for the instructions/tasks.
                Example:
                messages = {
                    "system" : "You are talented physicist",
                    "task" : "Answer user question {q} about this text {text}. Write a simple and concise explanation."
                }
    :param llm:     LangChain Runnable LLM
    :param key:     JSON output key
    """

    def __init__(self,
                 messages: Dict[str, str],
                 llm,
                 key: str = 'result') -> None:
        """
        :param messages:   contains system prompt and template for the instructions/tasks.
                    Example:
                    messages = {
                        "system" : "You are talented physicist",
                        "task" : "Answer user question {q} about this text {text}. Write a simple and concise explanation."
                    }
        :param llm:     LangChain Runnable LLM
        :param key:     JSON output key
        """
        sys_prt = messages.get('system', "")
        task = messages.get('task', "")

        if key == '':
            raise ValueError(f'Key can\'t be empty string!')
        self.key = key

        if task == '':
            raise Exception(f'Task can\'t be empty string!')

        self.chat_prompt = ChatPromptTemplate.from_messages([SystemMessage(content=sys_prt),
                                                             HumanMessagePromptTemplate.from_template(task)])

        self.chain = self.chat_prompt | llm | StrOutputParser()

    def __call__(self, inputs: Dict[str, str]) -> Union[str, Dict[str, str]]:
        return {
            self.key: self.chain.invoke(inputs)
        }


class BasicJSONNode:
    """A simple node that runs a chain which returns a JSON
    :param messages:   contains system prompt and template for the instructions/tasks.
                    Example:
                    messages = {
                        "system" : "You are talented physicist",
                        "task" : "Answer user question {q} about this text {text}. Write a simple and concise explanation."
                    }
    :param llm:     LangChain Runnable LLM
    """

    def __init__(self,
                 messages: Dict[str, str],
                 llm) -> None:
        """A simple node that runs a chain which returns a JSON
        :param messages:   contains system prompt and template for the instructions/tasks.
                        Example:
                        messages = {
                            "system" : "You are talented physicist",
                            "task" : "Answer user question {q} about this text {text}. Write a simple and concise explanation."
                        }
        :param llm:     LangChain Runnable LLM
        """

        sys_prt = messages.get('system', "")
        task = messages.get('task', "")

        if task == '':
            raise Exception(f'Task can\'t be empty string!')

        self.chat_prompt = ChatPromptTemplate.from_messages([SystemMessage(content=sys_prt),
                                                             HumanMessagePromptTemplate.from_template(task)])

        self.chain = self.chat_prompt | llm | JsonOutputParser()

    def __call__(self, inputs: Dict[str, str]) -> Union[str, Dict[str, str]]:
        return self.chain.invoke(inputs)