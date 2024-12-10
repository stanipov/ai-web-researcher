import logging
import datetime as dt
import sys
from datetime import datetime, timezone
import os

def set_logger(fmt:str="[%(asctime)s] [%(name)8s] [%(levelname)-8s] %(message)s"):
    """ Sets up a stdout logger """
    # this is what I used before
    # fmt="[%(asctime)s] [%(levelname)-8s] [%(module)s:%(lineno)s - %(funcName)20s()] %(message)s"
    today = dt.datetime.today()
    dt_str = f"{today.month:02d}-{today.day:02d}-{today.year}"

    logFormatter = logging.Formatter(
        fmt=fmt
    )
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(logFormatter)
    ch.setLevel(logging.INFO)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(ch)
    logger = logging.getLogger(__name__)
    return logger


def config_reader(cfg_file):
    """
    Parses the config file for the whole app

    :param cfg_file:
    :return:
    """
    return

def count_words(s: str, punkt = set(['*', ';'])):
    """A naive word counter"""
    if type(s) != str:
        s = str(s)
    words = [x for x in s.replace('\n', '').split(' ') if x != '' and x not in punkt]
    return len(words)


def make_data_dst(cwd):
    save_dst = os.path.join(cwd, datetime.utcnow().strftime("%Y-%m-%d"))
    os.makedirs(save_dst, exist_ok=True)
    return save_dst