from typing import Dict, Any

from src.scrapers.ddg import DDG_Scraper
from src.scrapers.loaders import ExtChromiumLoader

import logging
logger = logging.getLogger(__name__)


SUPPORTED_SEARCH_ENGINES = ['ddg']
SUPPORTED_LOADERS = ['chromium']
MANDATORY_FLDS_SCRAPE = ['loader']
MANDATORY_FLDS_SEARCH_ENGINE = ['name']
MANDATORY_ATTRS = {
    'scrape': MANDATORY_FLDS_SCRAPE,
    'search_engine': MANDATORY_FLDS_SEARCH_ENGINE
}


class ScraperInit:
    def __init__(self, *arg, **kwargs):
        """
        Nothing to add yet
        """
        return

    def set_scrapper(self, config: Dict[str, Any]):
        #
        logger.info(f"Verifying the config")
        # keys
        for fld in MANDATORY_ATTRS:
            if fld not in config:
                logger.error(f"Missing mandatory key: \"{fld}\"")
                raise KeyError(f"Missing mandatory key: \"{fld}\"")

        # mandatory keys for each sub-dict
        for key in MANDATORY_ATTRS:
            for fld in MANDATORY_ATTRS[key]:
                if fld not in config[key]:
                    msg = f"Missing mandatory key \"{fld}\" for \"{key}\""
                    logger.error(msg)
                    raise KeyError(msg)

        search_engine = config['search_engine']['name'].lower()
        if search_engine not in SUPPORTED_SEARCH_ENGINES:
            logger.error(f"Unsupported search engine, got {search_engine}, allowed: {', '.join(SUPPORTED_SEARCH_ENGINES)}")

        loader_name = config['scrape']['loader'].lower()
        if loader_name not in SUPPORTED_LOADERS:
            logger.error(f"Unsupported loader, got {loader_name}, allowed: {', '.join(SUPPORTED_LOADERS)}")

        # web search parameters
        max_results = config['search_engine']['max_results']
        srch_region = config['search_engine'].get('region', "wt-wt")
        srch_intvl = config['search_engine'].get('time', None)
        results_sep = config['search_engine'].get('resuts_sep', "<::SRC_SEP::>")
        srch_source = config['search_engine'].get('search_source', None)
        safe_srch = config['search_engine'].get('safe_search', "off")
        # scrape
        path_to_extension = config['scrape']['ext_path']
        coockie_btns = config['scrape']['cookie_btns']
        headless_scrape = config['scrape']['headless']

        scraper = None
        url_loader = None

        # URL loader
        if loader_name == 'chromium':
            url_loader = ExtChromiumLoader(ext_path=path_to_extension,
                                           headless=headless_scrape,
                                           cookie_btns_text=coockie_btns)

        # Search + scraper
        if search_engine == 'ddg' and url_loader is not None:
            scraper = DDG_Scraper(url_loader,
                                      max_results=max_results,
                                      src_region=srch_region,
                                      src_intvl=srch_intvl,
                                      resuts_sep=results_sep,
                                      src_source=srch_source,
                                      safe_src=safe_srch)


        return scraper

