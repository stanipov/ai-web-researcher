import logging
import datetime as dt
import sys

def set_logger():
    """ Sets up a stdout logger """
    today = dt.datetime.today()
    dt_str = f"{today.month:02d}-{today.day:02d}-{today.year}"

    logFormatter = logging.Formatter(
        #fmt="[%(asctime)s] [%(name)8s] [%(levelname)-8s] %(message)s"
        fmt="[%(asctime)s] [%(levelname)-8s] [%(module)s:%(lineno)s - %(funcName)20s()]  %(message)s"
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

def count_words(s, punkt = set(['*', ';'])):
    """A naive word counter"""
    words = [x for x in s.replace('\n', '').split(' ') if x != '' and x not in punkt]
    return len(words)