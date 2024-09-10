"""
Testing Playwright with BypassPaywallsClean addon for Chromium.
See: https://github.com/bpc-clone/bpc_updates/releases/tag/latest for getting the addon
"""

import asyncio
from playwright.async_api import async_playwright, Playwright

from langchain_community.document_transformers import Html2TextTransformer

path_to_extension = "/ext4/software/browser/bpwc"
user_data_dir = "test/dump"

async def run(playwright: Playwright, url: str):
    context = await playwright.chromium.launch_persistent_context(
        user_data_dir,
        headless=False,
        args=[
            f"--disable-extensions-except={path_to_extension}",
            f"--load-extension={path_to_extension}",
        ],
    )

    html2text = Html2TextTransformer()

    if len(context.background_pages) == 0:
        background_page = await context.wait_for_event('backgroundpage')
    else:
        background_page = context.background_pages[0]

    # Test the background page as you would any other page.

    # Open a new page
    page = await context.new_page()

    # Go to the target website
    await page.goto(url)

    # Scrape the desired data
    content = await page.content()
    print(page)
    print(await page.evaluate('document.body.innerHTML'))
    return content #html2text.transform_documents(content)
    await context.close()

async def main(url):
    async with async_playwright() as playwright:
        await run(playwright, url)


if __name__ == "__main__":
    url = "https://www.bloomberg.com/news/articles/2024-08-17/digital-euro-has-germans-fretting-their-money-won-t-be-secure?srnd=homepage-europe"

    print(f"Trying\n{url}\npage")

    page = asyncio.run(main(url))

    print(page)
