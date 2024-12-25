import logging
from typing import Dict, List, Tuple, Any

logger = logging.getLogger(__name__)

# Globals
MANDATORY_ATTRS = ['summarization_props', 'llm', "scrape", "search_engine", "data"]

def validate_global_config(cfg: Dict[str, str|Any]) -> bool:

    # contains mandatory fields
    logger.info(f"Validating global config: contains keys")
    for key in MANDATORY_ATTRS:
        if key not in cfg:
            logger.error(f"Mandatory key \"{key}\" not found!")
            return False

    # each entry is a dict type
    logger.info(f"Validating global config: valid dictionaries")
    for key in MANDATORY_ATTRS:
        if type(cfg['key']) != dict:
            logger.error(f"Entry for key \"{key}\" is not dict, got {type(cfg['key'])}")
            return False

    return True