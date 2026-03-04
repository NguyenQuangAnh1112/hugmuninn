"""
test_browser_tools.py
---------------------
Test từng tool một để kiểm tra hoạt động đúng không.
Dùng trang https://quotes.toscrape.com — trang web public, miễn phí, không cần login.

Cách chạy:
    python test_browser_tools.py

Kết quả mỗi test:
    ✅ PASS — tool hoạt động tốt
    ❌ FAIL — tool có vấn đề, xem chi tiết lỗi bên dưới
"""

from dotenv import load_dotenv

load_dotenv()

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from src.tools.browser_tools import (
    BrowserManager,
    browser_click,
    browser_get_content,
    browser_get_current_url,
    browser_navigate,
    browser_press_key,
    browser_screenshot,
    browser_type,
    browser_wait_for_element,
)

# ══════════════════════════════════════════════════════════
# HELPER — In kết quả test cho dễ đọc
# ══════════════════════════════════════════════════════════


def print_result(test_name: str, result: str, expect_contains: str = None):
    """
    In kết quả của một test.
    - test_name: tên test
    - result: kết quả tool trả về
    - expect_contains: chuỗi cần có trong kết quả (nếu None thì chỉ cần không lỗi)
    """
    print(f"\n{'─' * 50}")
    print(f"🧪 Test: {test_name}")
    print(f"📤 Kết quả:\n{result}")

    if expect_contains:
        if expect_contains.lower() in result.lower():
            print(f"✅ PASS — tìm thấy '{expect_contains}' trong kết quả")
        else:
            print(f"❌ FAIL — KHÔNG tìm thấy '{expect_contains}' trong kết quả")
    else:
        if "❌" in result or "error" in result.lower():
            print(f"❌ FAIL — kết quả chứa lỗi")
        else:
            print(f"✅ PASS")


# ══════════════════════════════════════════════════════════
# CÁC TEST
# ══════════════════════════════════════════════════════════


def test_navigate():
    """Test mở trang web"""
    result = browser_navigate.invoke("https://quotes.toscrape.com")
    print_result(
        test_name="browser_navigate — mở trang web",
        result=result,
        expect_contains="Quotes",  # tiêu đề trang chứa "Quotes"
    )


def test_get_current_url():
    """Test lấy URL hiện tại — phải gọi sau test_navigate"""
    result = browser_get_current_url.invoke({})
    print_result(
        test_name="browser_get_current_url — lấy URL hiện tại",
        result=result,
        expect_contains="quotes.toscrape.com",
    )


def test_get_content_body():
    """Test đọc toàn bộ nội dung trang"""
    result = browser_get_content.invoke("body")
    print_result(
        test_name="browser_get_content — đọc toàn trang (body)",
        result=result,
        expect_contains="quote",  # trang này có nhiều quotes
    )


def test_get_content_specific():
    """Test đọc phần tử cụ thể — chỉ lấy quote đầu tiên"""
    result = browser_get_content.invoke(".quote:first-child")
    print_result(
        test_name="browser_get_content — đọc quote đầu tiên (.quote:first-child)",
        result=result,
        expect_contains="by",  # quote có dạng "..." by Author
    )


def test_wait_for_element():
    """Test chờ phần tử xuất hiện"""
    result = browser_wait_for_element.invoke(".quote")
    print_result(
        test_name="browser_wait_for_element — chờ .quote xuất hiện",
        result=result,
        expect_contains="xuất hiện",
    )


def test_click():
    """Test click link — click sang trang 2"""
    result = browser_click.invoke("li.next a")
    print_result(
        test_name="browser_click — click Next sang trang 2",
        result=result,
        expect_contains="click",
    )

    # Xác nhận đã sang trang 2
    url_result = browser_get_current_url.invoke({})
    print_result(
        test_name="  → Xác nhận URL sau khi click",
        result=url_result,
        expect_contains="page/2",
    )


def test_navigate_search_page():
    """Quay về trang chủ để test type"""
    browser_navigate.invoke("https://quotes.toscrape.com/search.aspx")


def test_type_and_press():
    """Test nhập text + nhấn Enter"""
    # Nhập từ khóa vào ô tìm kiếm
    result_type = browser_type.invoke({"selector": "#author", "text": "Einstein"})
    print_result(
        test_name="browser_type — nhập 'Einstein' vào ô tìm kiếm",
        result=result_type,
        expect_contains="Einstein",
    )

    # Click nút search
    result_click = browser_click.invoke("input[type=submit]")
    print_result(
        test_name="browser_press_key — click search",
        result=result_click,
        expect_contains="click",
    )


def test_screenshot():
    """Test chụp màn hình"""
    result = browser_screenshot.invoke({})
    print_result(
        test_name="browser_screenshot — chụp màn hình",
        result=result,
        expect_contains="Đã chụp",
    )
    print("   📁 Xem file: debug_screenshot.png")


# ══════════════════════════════════════════════════════════
# CHẠY TẤT CẢ TEST
# ══════════════════════════════════════════════════════════


def run_all_tests():
    print("=" * 50)
    print("🚀 BẮT ĐẦU CHẠY TEST BROWSER TOOLS")
    print("=" * 50)

    tests = [
        ("1. Navigate", test_navigate),
        ("2. Get Current URL", test_get_current_url),
        ("3. Get Content (body)", test_get_content_body),
        ("4. Get Content (cụ thể)", test_get_content_specific),
        ("5. Wait For Element", test_wait_for_element),
        ("6. Click", test_click),
        ("7. Type + Press Key", test_type_and_press),
        ("8. Screenshot", test_screenshot),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"\n{'─' * 50}")
            print(f"🧪 Test: {name}")
            print(f"❌ FAIL — Exception: {e}")
            failed += 1

    # Đóng browser sau khi test xong
    asyncio.run(BrowserManager.close())

    # Tổng kết
    print(f"\n{'=' * 50}")
    print(f"📊 KẾT QUẢ: {passed} PASS — {failed} FAIL")
    print(f"{'=' * 50}\n")


if __name__ == "__main__":
    run_all_tests()
