import logging
logger = logging.getLogger(__name__)

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import pandas as pd
import dask.dataframe as dd
import os
import pickle


class BaseWriterClass(ABC):
    @abstractmethod
    def __init__(self, *args, **kwargs):
        """
        Initiate with all necessary paths
        """
        pass

    @abstractmethod
    def write(self, *args, **kwargs):
        """
        Writes the object to the final designated location
        """
        pass

    @abstractmethod
    def read(self, *args, **kwargs):
        """
        Reads the data
        """
        pass


"""
"data": {
    # will save as parquet
    "save_dir": os.getenv('data_dump_dst'),
    "error_dump_dir": "/ext4/proj/2024/ai-web-researcher/experiments/dump"
}
"""
class DaskWriter(BaseWriterClass):
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the ParquetSaver with the output path.

        :param output_path: The directory or file path where the Parquet file will be saved.
        """
        self.save_dir = config.get("save_dir", os.getcwd())
        self.error_dump_dir = config.get('error_dump_dir', None)
        logger.info(f"Data will be saved in \"{self.save_dir}\"")
        if self.error_dump_dir is not None:
            if self.error_dump_dir == "":
                self.error_dump_dir = os.getcwd()
            self.err_dir = os.path.join(self.error_dump_dir, 'DaskWriter')

    def write(self, data: Dict[str, Any]|List):
        """
        Save a list of dictionaries to a Parquet file, optionally appending to an existing file.

        :param data: List of dictionaries to save.
        """
        #if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
        #    raise ValueError("Data must be a list of dictionaries.")

        new_df = pd.DataFrame(data).T
        if os.path.exists(self.save_dir):
            existing_df = dd.read_parquet(self.save_dir, engine="pyarrow")
            existing_df = existing_df.compute()
            combined_df = pd.concat([existing_df, new_df])
        else:
            combined_df = new_df

        dask_df = dd.from_pandas(combined_df, npartitions=1)
        dask_df.to_parquet(self.save_dir, engine="pyarrow")

    def read(self):
        return dd.read_parquet(self.save_dir, engine="pyarrow")