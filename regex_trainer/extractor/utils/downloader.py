from .settings import *
from urllib.parse import unquote
import codecs
import asyncio
import base64

import websockets
import asyncio
import pyppeteer
from concurrent.futures._base import TimeoutError


def render_from_pyppeteer(url, loop, retries=1, script=None, wait=0.3, scrolldown=False, sleep=0,
                          timeout=8.0, keep_page=False):
    """
    render page with pyppeteer
    :param url: page url
    :param retries: max retry times
    :param script: js script to evaluate
    :param wait: number of seconds to wait before loading the page, preventing timeouts
    :param scrolldown: how many times to page down
    :param sleep: how many long to sleep after initial render
    :param timeout: the longest wait time, otherwise raise timeout error
    :param keep_page: keep page not to be closed, browser object needed
    :param browser: pyppetter browser object
    :param with_result: return with js evaluation result
    :return: content, [result]
    """
    browser = loop.run_until_complete(pyppeteer.launch(headless=True,
                                                       handleSIGTERM=False,
                                                       handleSIGINT=False))

    # define async render
    async def async_render(url, loop, script, scrolldown, sleep, wait, timeout, keep_page):
        try:
                # basic render
            page = await browser.newPage()
            await asyncio.sleep(wait)
            response = await page.goto(url, options={'timeout': int(timeout * 1000)})
            if response.status != 200:
                return None, None, response.status
            result = None
            # evaluate with script
            if script:
                result = await page.evaluate(script)

            # scroll down for {scrolldown} times
            if scrolldown:
                for _ in range(scrolldown):
                    await page._keyboard.down('PageDown')
                    await asyncio.sleep(sleep)
            else:
                await asyncio.sleep(sleep)
            if scrolldown:
                await page._keyboard.up('PageDown')

            # get html of page
            content = await page.content()

            return content, result, response.status
        except TimeoutError:
            return None, None, 500
        finally:
            # if keep page, do not close it
            if not keep_page:
                await page.close()

    content, result, status = [None] * 3

    # retry for {retries} times
    for i in range(retries):
        if not content:
            content, result, status = loop.run_until_complete(
                async_render(url=url, loop=loop, script=script, sleep=sleep, wait=wait,
                             scrolldown=scrolldown, timeout=timeout, keep_page=keep_page))
        else:
            break
    loop.run_until_complete(browser.close())
    # if need to return js evaluation result
    return content, result, status


def download_rendered_url(spider, sample, script=None, keep_cache=True):
    """
    spider:spider name
    sample:a sample url after base64 encoded
    script: a script that needs to be injected
    """
    url = sample
    target_fileName = Path(caches_target_dir).joinpath(
        f"{spider}/{base64.b64encode(sample.encode()).decode()}.html")
    if target_fileName.exists() and keep_cache:
        content = codecs.open(str(target_fileName),
                              mode="r", encoding="utf-8").read()
        return {
            "content": content,
            "url": url
        }
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        content, result, status = render_from_pyppeteer(
            url=url, loop=loop, script=script)
        if keep_cache:
            if not target_fileName.parent.exists():
                os.makedirs(str(target_fileName.parent))
            codecs.open(str(target_fileName), mode="w",
                        encoding="utf-8").write(content)
        return {
            "content": content,
            "url": url
        }
    except Exception as e:
        return {"message": e.args}
    finally:
        loop.close()
