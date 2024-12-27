from typing import List, Union, Dict
from playwright.async_api import async_playwright, Playwright
import html2text
import logging
import os
import re

from sqlalchemy.dialects.mysql.mariadb import loader

logger = logging.getLogger(__name__)

class ExtChromiumLoader:
    def __init__(self,
                 ext_path:Union[str, None] = None,
                 user_agent:Union[str, None] = None,
                 headless:bool = True,
                 proxy: Dict[str, str] = None,
                 cookie_btns_text:List[str] = None):
        """
        Sets the loader

        :param ext_path - path to extensions if any
        :param user_agent - string, user agent
        :param proxy - Dict[str, str] - proxy parameters, read the docs https://playwright.dev/python/docs/network
        :param headless - bool  - run headless or not
        :param cookie_btns_text - List[str] or None, list of text to click cookie consent

        """
        self.__ext_path = ext_path
        self.__user_agent = user_agent
        self.__headless = headless
        self.__usr_data_path = os.path.join(os.getcwd(), '.tmp')
        self.__proxy = proxy

        logger.debug(f"Scraping headless: {self.__headless}")
        logger.debug(f"Extensions: {self.__ext_path}")
        logger.debug(f"User agent: {self.__user_agent}")

        self.__args = []
        if ext_path:
            self.__args = [
                f"--disable-extensions-except={self.__ext_path}",
                f"--load-extension={self.__ext_path}"
            ]

        # "--headless=new" is experimental for PlayWright
        # at the moment of writing this wrapper code.
        # If we want headless Chromium wth extensions
        # we add "--headless=new" in args and
        # set headless in the context as False.
        # Not doing so results in weird errors.
        if ext_path and headless==True:
            self.__headless = False
            self.__args.append("--headless=new")

        self.html2text = html2text.HTML2Text()
        self.html2text.ignore_links = True
        self.html2text.ignore_images = True
        self.html2text.ignore_mailto_links = True

        self.cookie_btns_text = cookie_btns_text


    async def __aload_urls(self, playwright: Playwright, urls: List[str]):
        """
        Async loading list of URLs. It allows to eliminate time on starting
        a new browser for each URL

        :param playwright -- Playwright context
        :param urls - list of URLs to scrape
        """
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir= self.__usr_data_path,
            user_agent=self.__user_agent,
            headless=self.__headless,
            args=self.__args,
            proxy=self.__proxy
        )

        contents = {}
        for idx, url in enumerate(urls):
            logger.info(f"{idx+1}/{len(urls)+1}: Loading {url}")
            page = await context.new_page()

            try:
                await page.goto(url, wait_until='domcontentloaded')
            except Exception as e:
                logger.warning(f"Could not load \"{url}\" with \"{e}\"!")
                continue

            # Accept cookies
            if self.cookie_btns_text is not None:
                logger.info(f"Accepting cookies if any")
                for btn in self.cookie_btns_text:
                    try:
                        await page.get_by_role('button', name=re.compile(f'{btn}', re.IGNORECASE)).click(timeout=1500)
                        logger.debug(f"\"{btn}\" was clicked")
                        break
                    except Exception as e:
                        pass

            try:
                logger.info(f'Converting to HTML')
                html_content = await page.content()
                content = self.html2text.handle(html_content)
                contents[url] = content
            except Exception as e:
                logger.warning(f"Could not convert to HTML")

            await page.context.pages[-1].close()
        await context.close()

        return contents


    async def aload(self, urls: List[str]):
        async with async_playwright() as pl:
            pages = await self.__aload_urls(pl, urls)
        return pages

    def is_headless(self):
        return self.__headless