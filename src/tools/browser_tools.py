import asyncio
import base64
from concurrent import futures
from socket import timeout
from typing import Optional

from langchain_core.tools import tool
from langchain_tavily import TavilySearch
from playwright.async_api import Browser, Page, async_playwright

from src.utils.exception import he


class BrowserManager:
    _browser: Optional[Browser] = None
    _page: Optional[Page] = None
    _playwright = None

    @classmethod
    async def get_page(cls) -> Page:
        if cls._page is None or cls._page.is_closed():
            cls._playwright = await async_playwright().start()

            cls._browser = await cls._playwright.chromium.launch(headless=True)

            cls._page = await cls._browser.new_page()
        return cls._page

    @classmethod
    async def close(cls):
        if cls._browser:
            await cls._browser.close()
        if cls._playwright:
            await cls._playwright.stop()

        cls._playwright = None
        cls._page = None
        cls._browser = None


def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


tavily_search = TavilySearch(
    max_result=5,
    description=(
        "Tìm kiếm thông tin trên internet. "
        "Dùng khi cần tìm thông tin công khai, tin tức, hoặc nghiên cứu nhanh. "
        "KHÔNG dùng khi cần đăng nhập hoặc tương tác với web app. "
        "Input: câu hỏi hoặc từ khóa tìm kiếm bằng tiếng Anh hoặc tiếng Việt."
    ),
)


@tool
@he
def browser_navigate(url: str) -> str:
    """
    Mở một trang web trong trình duyệt.
    Dùng khi cần truy cập một URL cụ thể.
    Luôn gọi tool này TRƯỚC khi dùng các browser tool khác.
    Input: URL đầy đủ, ví dụ https://google.com
    """

    async def _run():
        page = await BrowserManager.get_page()

        # wait_until="domcontentloaded" -> chờ HTML load xong (nhanh)
        # wait_until="networkidle" -> chờ mọi request xong (chậm hơn nhưng chắc)
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)

        title = await page.title()

        return f"Opened: {url} | Title: {title}"

    return run_async(_run())


@tool
@he
def browser_get_content(selector: str = "body") -> str:
    """
    Đọc nội dung văn bản từ trang hiện tại.
    Dùng sau khi đã mở trang bằng browser_navigate.
    Input: CSS selector của phần tử cần đọc.
    Ví dụ: 'body' (toàn trang), 'h1', '#content', '.article-body'
    """

    async def _run() -> str:
        page = await BrowserManager.get_page()

        await page.wait_for_selector(selector, timeout=10000)

        text = await page.locator(selector).first.inner_text()

        if len(text) > 4000:
            text = text[:4000] + "\n ...(nội dung đã được cắt bớt)"

        return text

    return run_async(_run())


@tool
@he
def browser_click(selector: str) -> str:
    """
    Click vào một phần tử trên trang web.
    Dùng để click nút, link, checkbox, radio button...
    Input: CSS selector của phần tử cần click.
    Ví dụ: 'button[type=submit]', '#login-btn', 'a.nav-link'
    """

    async def _run():
        page = await BrowserManager.get_page()

        await page.wait_for_selector(selector, timeout=10000)
        await page.locator(selector).first.click()

        await page.wait_for_load_state("domcontentloaded")

        return f"Đã click vào {selector}"

    return run_async(_run())


@tool
@he
def browser_type(selector: str, text: str) -> str:
    """
    Nhập văn bản vào một ô input hoặc textarea.
    Dùng để điền form, ô tìm kiếm, username, password...
    Input:
      - selector: CSS selector của ô input
      - text: nội dung cần nhập
    Ví dụ selector: 'input[name=username]', '#search-box', 'textarea'
    """

    async def _run():
        page = await BrowserManager.get_page()

        await page.wait_for_selector(selector, timeout=10000)
        locator = page.locator(selector).first

        await locator.clear()
        await locator.fill(text)

        return f"Dẫ nhập '{text}' vào {selector}"

    return run_async(_run())


@tool
@he
def browser_press_key(key: str) -> str:
    """
    Nhấn một phím bàn phím trên trang hiện tại.
    Dùng sau browser_type khi cần nhấn Enter để submit form.
    Input: tên phím, ví dụ 'Enter', 'Tab', 'Escape', 'ArrowDown'
    """

    async def _run():
        page = await BrowserManager.get_page()

        await page.keyboard.press(key)
        await page.wait_for_load_state("domcontentloaded")

        return f"Đã nhấn phím: {key}"

    return run_async(_run())


@tool
@he
def browser_get_current_url() -> str:
    """
    Lấy URL của trang đang mở trong trình duyệt.
    Dùng để kiểm tra agent đang ở trang nào,
    hoặc xác nhận đã điều hướng đúng trang.
    Không cần input.
    """

    async def _run():
        page = await BrowserManager.get_page()
        return f"URL hiện tại: {page.url}"

    return run_async(_run())


@tool
@he
def browser_wait_for_element(selector: str) -> str:
    """
    Chờ một phần tử xuất hiện trên trang.
    Dùng khi trang load chậm hoặc nội dung xuất hiện sau vài giây.
    Nên dùng tool này TRƯỚC khi đọc nội dung động (AJAX, lazy load...).
    Input: CSS selector của phần tử cần chờ.
    """

    async def _run():
        page = await BrowserManager.get_page()

        await page.wait_for_selector(selector, timeout=15000)

        return f"Phần tử '{selector}' đã xuất hiện, có thể tương tác"

    return run_async(_run())


@tool
@he
def browser_screenshot() -> str:
    """
    Chụp ảnh màn hình trang hiện tại.
    Dùng để debug khi không chắc trang đang hiển thị gì,
    hoặc để xác nhận trạng thái trang trước khi thực hiện tác vụ.
    Không cần input.
    """

    async def _run():
        page = await BrowserManager.get_page()

        path = "debug_screenshot.png"

        await page.screenshot(path=path, full_page=False)

        screenshot_byte = await page.screenshot(full_page=False)
        b64 = base64.b64encode(screenshot_byte).decode()

        return (
            f"Đã chụp screenshot trang: {page.url}\n"
            f"Đã lưu file: {path}\n"
            f"Base64 (100 ký tự đầu): {b64[:100]}..."
        )

    return run_async(_run())


browser_tools = [
    tavily_search,
    browser_navigate,
    browser_get_content,
    browser_click,
    browser_type,
    browser_press_key,
    browser_get_current_url,
    browser_wait_for_element,
    browser_screenshot,
]
