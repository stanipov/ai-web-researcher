import sys

from loaders import logger

sys.path.append("./src")

from src.engines.loaders import ExtChromiumLoader
from src.utils.utils import set_logger
import asyncio



if __name__ == "__main__":
    path_to_extension = "/ext4/software/browser/bpwc"
    user_data_dir = "test/dump"

    logger = set_logger()

    ext_loader = ExtChromiumLoader(ext_path=path_to_extension, headless=True)
    no_ext_loader = ExtChromiumLoader()

    url1 = "https://www.bloomberg.com/news/articles/2024-08-17/digital-euro-has-germans-fretting-their-money-won-t-be-secure"
    url2 = "https://edition.cnn.com/2024/08/22/europe/pokrovsk-evacuations-eastern-ukraine-intl/"
    url3 = "https://arstechnica.com/"
    url4 = "https://www.washingtonpost.com/politics/2024/09/10/trump-harris-debate-gender/"
    urls = [url1, url2, url3, url4]

    logger.info(f"Testing loader with extensions in headless mode")
    pages_ext = asyncio.run(ext_loader.aload(urls))
    logger.info('Finished. Printing results in the console')

    for page in pages_ext:
        print(f"URL: {page}")
        print("Sample")
        print(f"{pages_ext[page][0:100]}")
        print("********************************************")
        print("********************************************")

    logger.info(f"Testing loader with NO extensions in headless mode")
    pages_no_ext = asyncio.run(no_ext_loader.aload(urls))
    logger.info('Finished. Printing results in the console')

    print("\n\n************** NO EXTENSION RESULTS **************\n\n")
    for page in pages_no_ext:
        print(f"URL: {page}")
        print("Sample")
        print(f"{pages_no_ext[page][0:100]}")
        print("********************************************")
        print("********************************************")

