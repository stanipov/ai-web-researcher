from abc import ABC, abstractmethod

class BaseSearchGvt:
    @abstractmethod
    def __init__(self, *args, **kwargs):
        pass

    @abstractmethod
    def save(self, *args, **kwargs):
        """
        Abstraction to save data
        """
        pass

    @abstractmethod
    def load(self, *args, **kwargs):
        """
        Abstraction to load data
        """
        pass

    @abstractmethod
    def retrieve(self, *args, **kwargs):
        """
        Abstraction to retrieve data (from web, docs, etc)
        """
        pass