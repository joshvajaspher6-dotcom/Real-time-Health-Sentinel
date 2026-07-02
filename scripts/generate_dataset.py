"""
TestSentry Dataset Generator - Hybrid Edition
==============================================
Generates 3000 labeled pytest + pytest-playwright + pytest-selenium failure examples.
Run this overnight:  python scripts/generate_dataset.py

Output: data/training_dataset.json
"""

import os
import json
import time
import random
import traceback
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ── PYTEST + PLAYWRIGHT + SELENIUM ERROR TEMPLATES ──────────────────────
ERROR_TEMPLATES = {
    # ═══════════════════════════════════════════════════════════
    # PURE PYTEST FAILURES (Unit/Integration Tests)
    # ═══════════════════════════════════════════════════════════
    "PYTEST_ASSERTION": [
        "AssertionError: assert {actual} == {expected}",
        "AssertionError: assert result.status_code == 200, got {code}",
        "AssertionError: Expected {expected} but got {actual}",
        "AssertionError: {actual} is False - condition check failed",
        "AssertionError: List length {actual} != expected {expected}",
        "AssertionError: assert {obj}.{method}() raised {error}",
    ],
    "PYTEST_TYPE_ERROR": [
        "TypeError: unsupported operand type(s) for +: '{type1}' and '{type2}'",
        "TypeError: '{obj}.{method}()' takes {expected} positional argument but {actual} were given",
        "TypeError: {func}() argument must be {type1}, not {type2}",
        "TypeError: object of type '{type1}' is not iterable",
        "TypeError: {func}() missing {expected} required positional argument: '{arg}'",
    ],
    "PYTEST_ATTRIBUTE_ERROR": [
        "AttributeError: '{obj}' object has no attribute '{attr}'",
        "AttributeError: module '{module}' has no attribute '{attr}'",
        "AttributeError: 'NoneType' object has no attribute '{attr}'",
        "AttributeError: '{class}' object has no attribute '{method}'",
    ],
    "PYTEST_KEY_ERROR": [
        "KeyError: '{key}' not found in response dict",
        "KeyError: '{key}' - missing required field in {obj}",
        "KeyError: '{table}' table does not have column '{col}'",
    ],
    "PYTEST_INDEX_ERROR": [
        "IndexError: list index out of range at index {idx}",
        "IndexError: tuple index out of range accessing element {idx}",
        "IndexError: string index out of range",
    ],
    "PYTEST_VALUE_ERROR": [
        "ValueError: invalid literal for int() with base 10: '{val}'",
        "ValueError: {func}() argument out of range: {val}'",
        "ValueError: cannot unpack {actual} values (expected {expected})",
        "ValueError: {obj} is not a valid {enum_type}",
    ],
    "PYTEST_ZERO_DIVISION": [
        "ZeroDivisionError: division by zero in {func}",
        "ZeroDivisionError: integer division or modulo by zero",
    ],
    "PYTEST_RECURSION": [
        "RecursionError: maximum recursion depth exceeded in {func}",
        "RecursionError: infinite recursion detected in {func}",
    ],
    "PYTEST_IMPORT_ERROR": [
        "ImportError: cannot import name '{obj}' from '{module}'",
        "ModuleNotFoundError: No module named '{module}'",
        "ImportError: {module} requires {dependency}, but it's not installed",
    ],

    # ═══════════════════════════════════════════════════════════
    # PYTEST FLAKINESS (Intermittent Failures)
    # ═══════════════════════════════════════════════════════════
    "PYTEST_FLAKY_TIMEOUT": [
        "TimeoutError: test timed out after {seconds}s waiting for {resource}",
        "pytest.TimeoutError: timeout at {func}",
        "asyncio.TimeoutError: Task exceeded {seconds}s timeout",
        "concurrent.futures.TimeoutError: Future timed out after {seconds}s",
    ],
    "PYTEST_RACE_CONDITION": [
        "AssertionError: {expected} but got {actual} due to race condition",
        "AssertionError: Expected {expected} but got {actual} (intermittent)",
        "RuntimeError: Event loop is closed during async {operation}",
        "concurrent.futures._base.TimeoutError: race condition in {func}",
    ],

    # ═══════════════════════════════════════════════════════════
    # PLAYWRIGHT E2E FAILURES
    # ═══════════════════════════════════════════════════════════
    "PLAYWRIGHT_SELECTOR": [
        "PlaywrightError: locator('{selector}') did not resolve to any element",
        "TimeoutError: Timeout 30000ms exceeded waiting for locator('{selector}')",
        "Error: locator('{selector}') returned {count} elements, not 1",
        "PlaywrightError: No element matches selector '{selector}'",
    ],
    "PLAYWRIGHT_NAVIGATION": [
        "TimeoutError: page.goto: Timeout 30000ms waiting for {url}",
        "Error: net::ERR_FAILED {status_code} {method} {url}",
        "PlaywrightError: Navigation failed because the page was closed!",
        "TimeoutError: page.waitForLoadState('networkidle'): Timeout 30000ms",
        "Error: net::ERR_CONNECTION_REFUSED at {url}",
    ],
    "PLAYWRIGHT_VISIBILITY": [
        "PlaywrightError: locator.click: Element is not visible",
        "PlaywrightError: locator.fill: Element is outside of the viewport",
        "Error: {selector} element is covered by another element",
        "PlaywrightError: locator.check: Element is disabled",
    ],
    "PLAYWRIGHT_STALE": [
        "PlaywrightError: Target page, context or browser has been closed",
        "Error: Node is detached from document, can't click",
        "PlaywrightError: locator.click: Element has been detached from the DOM",
    ],
    "PLAYWRIGHT_INTERACTION": [
        "PlaywrightError: locator.select_option: No option with text='{option}' found",
        "Error: Cannot find option matching value='{value}' in dropdown",
        "PlaywrightError: locator.type: Keyboard input failed",
        "PlaywrightError: locator.check: Element is not a checkbox",
    ],
    "PLAYWRIGHT_BROWSER": [
        "PlaywrightError: Browser has been closed",
        "Error: WebSocket closed unexpectedly",
        "PlaywrightError: browser.newPage: Browser has been closed",
        "Error: ECONNREFUSED connection refused at localhost:{port}",
    ],

    # ═══════════════════════════════════════════════════════════
    # SELENIUM E2E FAILURES
    # ═══════════════════════════════════════════════════════════
    "SELENIUM_NO_SUCH_ELEMENT": [
        "NoSuchElementException: Message: no such element: Unable to locate element: {selector}",
        "NoSuchElementException: Unable to find element with xpath '{xpath}'",
        "selenium.common.exceptions.NoSuchElementException at {url}",
    ],
    "SELENIUM_STALE_ELEMENT": [
        "StaleElementReferenceException: stale element reference: element is no longer attached to the DOM",
        "StaleElementReferenceException: The element reference of {selector} is stale",
    ],
    "SELENIUM_TIMEOUT": [
        "TimeoutException: Message: timeout: Timed out receiving message from renderer: {url}",
        "selenium.common.exceptions.TimeoutException after {seconds}s",
        "TimeoutException: Timed out waiting for {condition} after {seconds}s",
    ],
    "SELENIUM_ELEMENT_NOT_VISIBLE": [
        "ElementNotVisibleException: Message: element not visible at {selector}",
        "ElementNotInteractableException: element not interactable at {selector}",
        "selenium.common.exceptions.ElementNotVisibleException",
    ],
    "SELENIUM_CLICK_ERROR": [
        "WebDriverException: Message: unknown error: Element is not clickable at point ({x}, {y})",
        "ElementClickInterceptedException: element click intercepted: Element is not clickable",
        "selenium.common.exceptions.WebDriverException: click failed at {selector}",
    ],
    "SELENIUM_NAVIGATION": [
        "WebDriverException: Message: chrome not reachable",
        "TimeoutException: Browser page load timeout at {url}",
        "WebDriverException: unknown error: net::{error_code} {message}",
    ],
    "SELENIUM_BROWSER_CRASH": [
        "WebDriverException: Message: unknown error: Chrome failed to start: crashed",
        "WebDriverException: unknown error: Session deleted because of page crash",
        "WebDriverException: disconnected: not connected to DevTools",
    ],

    # ═══════════════════════════════════════════════════════════
    # SHARED E2E ISSUES (Both Playwright & Selenium)
    # ═══════════════════════════════════════════════════════════
    "E2E_AUTHENTICATION": [
        "Error: 401 Unauthorized at {url}",
        "TimeoutError: waiting for login authentication at {url}",
        "Error: Invalid credentials provided to {auth_service}",
        "AssertionError: Login failed - expected dashboard, got login page",
    ],
    "E2E_ASSERTION": [
        "AssertionError: assert '{actual}' == '{expected}' on page content",
        "AssertionError: Element text '{actual}' != expected '{expected}'",
        "AssertionError: Page title '{actual}' != '{expected}'",
        "AssertionError: Element count {actual} != expected {expected}",
    ],
    "E2E_NETWORK": [
        "ConnectionError: connection reset by peer during {operation}",
        "TimeoutError: Network request timeout at {url}",
        "Error: Failed to fetch resource at {url} - {status_code}",
        "ConnectionRefusedError: [Errno 111] Connection refused to {host}:{port}",
    ],

    # ═══════════════════════════════════════════════════════════
    # DATABASE/EXTERNAL SERVICE ISSUES
    # ═══════════════════════════════════════════════════════════
    "DATABASE_ERROR": [
        "psycopg2.OperationalError: could not connect to server: Connection refused",
        "sqlite3.OperationalError: database is locked",
        "pymongo.errors.ServerSelectionTimeoutError: localhost:{port}: Connection refused",
        "sqlalchemy.exc.OperationalError: ({error_code}) {error_message}",
        "IntegrityError: duplicate key value violates unique constraint '{table}'",
    ],
    "SERVICE_UNAVAILABLE": [
        "redis.exceptions.ConnectionError: Error connecting to Redis on port {port}",
        "docker.errors.DockerException: Docker daemon not running",
        "elasticsearch.exceptions.ConnectionError: Connection refused to {host}:{port}",
        "kafka.errors.NoBrokersAvailable: NoBrokersAvailable on {host}:{port}",
    ],
}

# ── Fill templates with random values ───────────────────────
def fill_template(template: str) -> str:
    replacements = {
        # Generic
        "{actual}": random.choice(["None", "False", "0", "[]", "{}", "''", "-1", "404"]),
        "{expected}": random.choice(["True", "200", "1", "[1,2,3]", "'active'", "Dashboard"]),
        "{code}": random.choice(["404", "500", "403", "422", "503"]),
        "{type1}": random.choice(["int", "str", "NoneType", "list", "dict"]),
        "{type2}": random.choice(["str", "int", "dict", "NoneType", "float"]),
        "{obj}": random.choice(["User", "Order", "Payment", "Session", "Cart", "Product"]),
        "{attr}": random.choice(["id", "email", "status", "created_at", "total", "name"]),
        "{method}": random.choice(["save", "delete", "validate", "process", "execute"]),
        "{key}": random.choice(["user_id", "token", "status", "data", "result", "email"]),
        "{idx}": str(random.randint(0, 10)),
        "{val}": random.choice(["None", "abc", "", "N/A", "null", "undefined"]),
        "{func}": random.choice(["calculate_tax", "process_payment", "validate_user", "fetch_data"]),
        "{seconds}": str(random.choice([5, 10, 30, 60])),
        "{resource}": random.choice(["database", "redis", "API", "file", "lock"]),
        "{operation}": random.choice(["read", "write", "connect", "authenticate", "upload"]),
        "{count}": str(random.randint(1, 10)),
        "{actual_count}": str(random.randint(0, 5)),
        "{expected_count}": str(random.randint(1, 10)),
        
        # Playwright specific
        "{selector}": random.choice([
            "[data-testid='login-button']",
            ".header-nav",
            "#main-content",
            "input[name='email']",
            "button:has-text('Submit')",
            "xpath=//button[@id='submit']",
        ]),
        "{xpath}": random.choice([
            "//button[@id='submit']",
            "//div[@class='form-input']",
            "//span[contains(text(), 'Login')]",
            "//input[@type='email']",
        ]),
        "{option}": random.choice(["admin", "user", "guest", "verified", "moderator"]),
        "{value}": random.choice(["admin_role", "user_id_123", "guest_access", "active"]),
        
        # Selenium specific
        "{x}": str(random.randint(100, 1000)),
        "{y}": str(random.randint(100, 800)),
        "{condition}": random.choice(["element visible", "page loaded", "ajax complete"]),
        
        # URL/Network
        "{url}": random.choice([
            "https://app.example.com/login",
            "https://api.example.com/data",
            "https://dashboard.example.com",
            "https://auth.example.com/callback",
        ]),
        "{error_code}": random.choice(["ERR_FAILED", "ERR_ABORTED", "ERR_TIMED_OUT", "ERR_CONNECTION_REFUSED"]),
        "{error_message}": random.choice(["Connection refused", "Timeout", "Network error", "Service unavailable"]),
        "{status_code}": random.choice(["401", "403", "404", "500", "503"]),
        "{port}": str(random.choice([5432, 6379, 27017, 9200, 8080, 3000])),
        "{host}": random.choice(["localhost", "127.0.0.1", "db.internal", "redis-server"]),
        "{message}": random.choice(["timeout", "connection refused", "invalid response", "bad gateway"]),
        
        # Database/Auth
        "{table}": random.choice(["users", "orders", "payments", "sessions", "products", "logs"]),
        "{col}": random.choice(["id", "email", "status", "created_at", "user_id"]),
        "{auth_service}": random.choice(["OAuth", "SAML", "JWT", "Session", "2FA"]),
        "{module}": random.choice(["auth", "database", "api", "utils", "models"]),
        "{dependency}": random.choice(["requests", "sqlalchemy", "redis", "playwright"]),
        "{arg}": random.choice(["token", "user_id", "config", "database"]),
        "{class}": random.choice(["User", "Database", "ApiClient", "Validator"]),
        "{enum_type}": random.choice(["Status", "Role", "Permission", "State"]),
        "{error_type}": random.choice(["NETWORK_ERROR", "TIMEOUT", "REFUSED", "INTERNAL_ERROR"]),
    }
    for placeholder, value in replacements.items():
        template = template.replace(placeholder, value)
    return template


# ── Generate one example using Groq ─────────────────────────
def generate_example(category: str, error_msg: str) -> dict | None:
    try:
        framework = "Playwright" if "PLAYWRIGHT" in category else \
                   "Selenium" if "SELENIUM" in category else \
                   "pytest" if "PYTEST" in category or "E2E" not in category else "E2E"
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a senior QA engineer specializing in {framework} testing.
                    Create ONLY valid JSON responses. No markdown. No extra text."""
                },
                {
                    "role": "user",
                    "content": f"""Create a {framework} failure training example.

Category: {category}
Error: {error_msg}

Return ONLY this JSON structure (no markdown, no backticks, no extra text):
{{
    "test_name": "tests/test_module.py::test_function_name",
    "error_msg": "{error_msg}",
    "category": "{category}",
    "framework": "{framework}",
    "confidence_pct": 87,
    "why_it_failed": "Why this error occurred in 1-2 sentences",
    "suggested_fix": "Specific actionable fix in 1-2 sentences",
    "affected_module": "module.py",
    "is_flaky": false
}}"""
                }
            ],
            temperature=0.7,
            max_tokens=400
        )

        content = response.choices[0].message.content.strip()

        # Strip markdown if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        example = json.loads(content)

        # Validate required fields
        required = ["test_name", "error_msg", "category", "why_it_failed", "suggested_fix"]
        if all(k in example for k in required):
            return example
        else:
            print(f"❌ Missing required fields in response: {example.keys()}")
            return None

    except json.JSONDecodeError as e:
        print(f"❌ JSON Parse Error: {e}")
        print(f"   Response was: {content[:100]}")
        return None
    except Exception as e:
        print(f"❌ API Error: {e}")
        traceback.print_exc()
        return None


# ── Main generation loop ──────────────────────────────────────
def main():
    TARGET = 3000
    NUM_CATEGORIES = len(ERROR_TEMPLATES)
    PER_CATEGORY = TARGET // NUM_CATEGORIES
    OUTPUT_FILE = "data/training_dataset.json"

    os.makedirs("data", exist_ok=True)

    # Load existing progress if interrupted
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE) as f:
            dataset = json.load(f)
        print(f"✅ Resuming from {len(dataset)} existing examples\n")
    else:
        dataset = []

    categories = list(ERROR_TEMPLATES.keys())
    category_counts = {c: sum(1 for d in dataset if d.get("category") == c)
                       for c in categories}

    print(f"\n🔬 TestSentry Hybrid Dataset Generator")
    print(f"   Frameworks: pytest + Playwright + Selenium")
    print(f"   Target: {TARGET} examples ({PER_CATEGORY} per category)")
    print(f"   Categories: {NUM_CATEGORIES}")
    print(f"   Current breakdown:")
    for cat, count in sorted(category_counts.items()):
        print(f"      {cat}: {count}/{PER_CATEGORY}")
    print(f"\nStarting generation... (Ctrl+C to pause and resume later)\n")

    generated = 0
    errors = 0
    api_errors = 0

    try:
        while len(dataset) < TARGET:
            # Pick category with fewest examples
            category = min(category_counts,
                          key=lambda c: category_counts[c])

            if category_counts[category] >= PER_CATEGORY:
                break

            # Pick random template for this category
            template = random.choice(ERROR_TEMPLATES[category])
            error_msg = fill_template(template)

            # Generate example
            example = generate_example(category, error_msg)

            if example:
                dataset.append(example)
                category_counts[category] += 1
                generated += 1

                # Save every 50 examples
                if generated % 50 == 0:
                    with open(OUTPUT_FILE, "w") as f:
                        json.dump(dataset, f, indent=2)
                    progress = {c: category_counts[c] for c in categories}
                    print(f"✅ {len(dataset)}/{TARGET} generated")
                    print(f"   {progress}\n")

            else:
                errors += 1
                api_errors += 1
                if api_errors > 5:
                    print(f"\n⚠️  Multiple API errors detected!")
                    print(f"   Generated: {generated}")
                    print(f"   Failed: {errors}")
                    print(f"   Check your Groq API key and rate limits")
                    print(f"   Exiting to prevent further issues...\n")
                    break

            # Rate limiting — Groq free tier: 30 req/min (1 req per 2 seconds)
            time.sleep(2.1)

    except KeyboardInterrupt:
        print("\n⏸️  Paused — progress saved. Run again to resume.")

    # Final save
    with open(OUTPUT_FILE, "w") as f:
        json.dump(dataset, f, indent=2)

    print(f"\n✅ Generation Status:")
    print(f"   Total examples: {len(dataset)}/{TARGET}")
    print(f"   Successfully generated: {generated}")
    print(f"   Errors/Failed: {errors}")
    print(f"   Saved to: {OUTPUT_FILE}")
    print(f"\n📊 Final breakdown:")
    for cat in sorted(category_counts.keys()):
        print(f"   {cat}: {category_counts[cat]}/{PER_CATEGORY}")


if __name__ == "__main__":
    main()
