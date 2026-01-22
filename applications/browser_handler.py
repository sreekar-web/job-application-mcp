"""
Browser automation handler for job applications.
Uses Playwright for reliable cross-platform form detection and autofill.
"""

import asyncio
import json
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime

try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext
except ImportError:
    raise ImportError("playwright not installed. Run: pip install playwright")


@dataclass
class FormField:
    """Detected form field with selectors and values."""
    name: str
    selector: str
    value: Optional[str] = None
    field_type: str = "text"  # text, email, phone, file, select, textarea
    detected: bool = False


@dataclass
class ApplicationResult:
    """Result of application submission attempt."""
    success: bool
    job_url: str
    status: str  # 'submitted', 'pending_user_input', 'error'
    filled_fields: Dict[str, str]
    ambiguous_fields: Dict[str, str]  # User-prompted fields
    error_message: Optional[str] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class BrowserHandler:
    """Manages browser automation for job applications."""
    
    def __init__(self, form_rules_path: Path = None):
        self.form_rules_path = form_rules_path or Path(__file__).parent.parent / "config" / "form_rules.json"
        self.form_rules = self._load_form_rules()
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        
    def _load_form_rules(self) -> Dict:
        """Load form rules for different ATS systems."""
        if not self.form_rules_path.exists():
            raise FileNotFoundError(f"Form rules not found: {self.form_rules_path}")
        return json.loads(self.form_rules_path.read_text())
    
    async def init(self):
        """Initialize Playwright browser."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context(
            viewport={"width": 1280, "height": 720}
        )
    
    async def close(self):
        """Close browser and cleanup."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
    
    async def open_job_link(self, job_url: str) -> Page:
        """Open job application link."""
        if not self.context:
            await self.init()
        page = await self.context.new_page()
        await page.goto(job_url, wait_until="domcontentloaded")
        await asyncio.sleep(2)  # Wait for JS to render
        return page
    
    def _detect_ats_system(self, page_content: str) -> str:
        """Detect which ATS system the job board uses."""
        if "greenhouse" in page_content.lower():
            return "greenhouse"
        elif "lever" in page_content.lower():
            return "lever"
        else:
            return "standard_html"
    
    async def detect_form_fields(self, page: Page) -> List[FormField]:
        """Detect all fillable form fields on the page."""
        page_content = await page.content()
        ats_system = self._detect_ats_system(page_content)
        rules = self.form_rules.get(ats_system, self.form_rules["standard_html"])
        
        detected_fields = []
        
        # Check for standard input fields
        for field_name, selectors in rules["selectors"].items():
            for selector in selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        field_type = await element.get_attribute("type") or "text"
                        detected_fields.append(FormField(
                            name=field_name,
                            selector=selector,
                            field_type=field_type,
                            detected=True
                        ))
                        break  # Found this field, move to next
                except Exception:
                    continue
        
        return detected_fields
    
    async def fill_form_field(self, page: Page, field: FormField, value: str) -> bool:
        """Fill a single form field with a value."""
        try:
            element = await page.query_selector(field.selector)
            if not element:
                return False
            
            # Handle different field types
            if field.field_type == "file":
                await element.set_input_files(value)
            elif field.field_type == "select":
                await page.select_option(field.selector, value)
            else:
                await element.click()
                await element.fill(value)
                await element.blur()
            
            return True
        except Exception as e:
            print(f"Error filling {field.name}: {e}")
            return False
    
    async def autofill_form(
        self,
        page: Page,
        user_data: Dict[str, str],
        detected_fields: List[FormField]
    ) -> Tuple[Dict[str, str], List[str]]:
        """
        Autofill detected form fields with user data.
        Returns (filled_fields, ambiguous_fields).
        """
        filled_fields = {}
        ambiguous_fields = []
        
        field_mapping = self.form_rules.get("field_mapping", {})
        
        for field in detected_fields:
            mapped_key = field_mapping.get(field.name, field.name)
            
            if mapped_key in user_data:
                value = user_data[mapped_key]
                success = await self.fill_form_field(page, field, value)
                if success:
                    filled_fields[field.name] = value
        
        return filled_fields, ambiguous_fields
    
    async def find_submit_button(self, page: Page) -> Optional[str]:
        """Find and return selector for submit button."""
        # Try standard selectors
        standard_selectors = [
            "button[type='submit']:not([disabled])",
            "button:has-text('Submit'):not([disabled])",
            "button:has-text('Apply'):not([disabled])",
            "input[type='submit']:not([disabled])"
        ]
        
        for selector in standard_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    return selector
            except Exception:
                continue
        
        return None
    
    async def submit_application(self, page: Page) -> bool:
        """Submit the application form."""
        submit_selector = await self.find_submit_button(page)
        if not submit_selector:
            print("Submit button not found")
            return False
        
        try:
            button = await page.query_selector(submit_selector)
            await button.click()
            await page.wait_for_load_state("networkidle")
            return True
        except Exception as e:
            print(f"Error submitting form: {e}")
            return False


async def test_browser_handler():
    """Test browser handler with sample job URL."""
    handler = BrowserHandler()
    try:
        await handler.init()
        
        # Example: Test with a real job board
        test_url = "https://boards.greenhouse.io/example/jobs"
        print(f"Opening {test_url}...")
        page = await handler.open_job_link(test_url)
        
        # Detect form fields
        fields = await handler.detect_form_fields(page)
        print(f"Detected {len(fields)} fields: {[f.name for f in fields]}")
        
        await page.close()
    finally:
        await handler.close()


if __name__ == "__main__":
    # Uncomment to test
    # asyncio.run(test_browser_handler())
    pass
