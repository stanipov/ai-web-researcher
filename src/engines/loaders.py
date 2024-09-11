from typing import List, Union
from playwright.async_api import async_playwright, Playwright
import html2text
import logging
import os


logger = logging.getLogger(__name__)

class ExtChromiumLoader:
    def __init__(self,
                 ext_path:Union[str, None] = None,
                 user_agent:Union[str, None] = None,
                 headless:bool = True):
        self.__ext_path = ext_path
        self.__user_agent = user_agent
        self.__headless = headless
        self.__usr_data_path = os.path.join(os.getcwd(), '.tmp')

        self.__args = []
        if ext_path:
            self.__args = [
                f"--disable-extensions-except={self.__ext_path}",
                f"--load-extension={self.__ext_path}"
            ]

        # "--headless=new" is experimental for PlayWright
        # at the moment of writing this wrapper code
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

        self.cookie_btns_text = ['Accept']


    async def __aload_urls(self, playwright: Playwright, urls: List[str]):
        """
        Async loading list of URLs. It allows to eliminate time on starting
        a new browser for each URL

        """
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir= self.__usr_data_path,
            user_agent=self.__user_agent,
            headless=self.__headless,
            args=self.__args
        )

        contents = {}
        for url in urls:
            logger.info(f"Loading {url}")
            page = await context.new_page()

            try:
                await page.goto(url, wait_until='domcontentloaded')
            except Exception as e:
                logger.warning(f"Could not load \"{url}\" with \"{e}\"!")

            # Accept cookies
            for btn in self.cookie_btns_text:
                logger.info(f"Accepting cookies if any; looking for \"{btn}\" button.")
                try:
                    await page.locator(f'button:has-text("{btn}")').click(timeout=1000)
                except Exception as e:
                    logger.info(f'While trying to accept cookies, got "{e}"')

            try:
                logger.info(f'Converting "{url}" to HTML')
                html_content = await page.content()
                content = self.html2text.handle(html_content)
                contents[url] = content
            except Exception as e:
                logger.warning(f"Could not convert to HTML page \"{url}\"")
            await page.context.pages[-1].close()
        await context.close()

        return contents


    async def aload(self, urls: List[str]):
        async with async_playwright() as pl:
            pages = await self.__aload_urls(pl, urls)
        return pages