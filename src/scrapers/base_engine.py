from abc import ABC
import asyncio

async def engine_ainvoke(engine, query, config = None, **kwargs):
    res = await engine.ainvoke(query, config, **kwargs)
    return res

class BaseEngine(ABC):
    def __init__(self, *args, **kwargs):
        raise NotImplementedError("Not implemented")

    def invoke(self, query):
        raise NotImplementedError("Not implemented")