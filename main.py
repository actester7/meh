"""
Discord Account Generator - NO CDP VERSION
Uses nodriver (undetectable) browser automation - NO Chrome DevTools Protocol
Python 3.14 Compatible - No aiohttp dependency

FIXES APPLIED:
1. KeyError: 'clicked' - Fixed with safe dictionary access
2. Premature form submission - Added 1.5s wait before submit
3. TOS checkbox verification before submitting
4. Fallback checkbox clicking method
5. Better error handling throughout
6. REPLACED zendriver with nodriver - NO CDP DETECTION
"""

import asyncio
from datetime import datetime
import hashlib
import os
import shutil
from pathlib import Path
import platform
import re
import sys
import threading
import time
import json
import random
import string
import signal
import tempfile
from typing import Optional, Dict
import requests
import httpx
import tls_client
from colorama import Fore, Style, init
from pystyle import Center
from rich.console import Console
import warnings
import nodriver as uc
import urllib3
import base64

# Try to import psutil for process management (optional)
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Initialize colorama
init(autoreset=True)

# domains func
def load_custom_domains(file_path="domains.txt"):
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r") as f:
        return [line.strip() for line in f if line.strip()]

# Disable SSL warnings and suppress nodriver connection errors
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore', category=ResourceWarning)
warnings.filterwarnings('ignore', message='.*connection.*refused.*')
warnings.filterwarnings('ignore', message='.*Task exception was never retrieved.*')

# Suppress asyncio errors in console
import logging
logging.getLogger('asyncio').setLevel(logging.CRITICAL)
logging.getLogger('websockets').setLevel(logging.CRITICAL)
logging.getLogger('nodriver').setLevel(logging.CRITICAL)

# ============================================================================
# DISCORD TOKEN FETCH FUNCTION
# ============================================================================

async def fetch_discord_token(email: str, password: str) -> str:
    url = "https://discord.com/api/v9/auth/login"
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "origin": "https://discord.com",
        "priority": "u=1, i",
        "referer": "https://discord.com/channels/@me",
        "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "x-discord-timezone": "Asia/Calcutta",
        "x-super-properties": "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiQ2hyb21lIiwiZGV2aWNlIjoiIiwic3lzdGVtX2xvY2FsZSI6ImVuLVVTIiwiaGFzX2NsaWVudF9tb2RzIjpmYWxzZSwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzEzNC4wLjAuMCBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiMTM0LjAuMC4wIiwib3NfdmVyc2lvbiI6IjEwIiwicmVmZXJyZXIiOiIiLCJyZWZlcnJpbmdfZG9tYWluIjoiIiwicmVmZXJyZXJfY3VycmVudCI6IiIsInJlZmVycmluZ19kb21haW5fY3VycmVudCI6IiIsInJlbGVhc2VfY2hhbm5lbCI6InN0YWJsZSIsImNsaWVudF9idWlsZF9udW1iZXIiOjM4NDg4NywiY2xpZW50X2V2ZW50X3NvdXJjZSI6bnVsbH0="
    }
    
    payload = {
        "gift_code_sku_id": None,
        "login": email,
        "login_source": None,
        "password": password,
        "undelete": False,
    }
    
    session = tls_client.Session(client_identifier="chrome_131", random_tls_extension_order=True)
    try:
        response = session.post(url, headers=headers, json=payload)
        print(f"Succesfully Fetched Token -> {email}")
        timestamp = datetime.now().strftime("%H:%M:%S")
        if response.status_code != 200:
            return ""
        response_data = response.json()
        token = response_data.get("token")
        if not token:
            return ""
        return token
    except:
        return ""

# ============================================================================
# JAVASCRIPT UTILITIES
# ============================================================================

JS_UTILS = '''
(() => {
    if (window.utils) return; // Already injected
    
    function setInput(selector, value) {
        const el = document.querySelector(selector);
        if (el) {
            el.value = value;
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
        }
    }
    
    function clickAllCheckboxes() {
        const checkboxes = document.querySelectorAll('input[type="checkbox"]');
        let clicked = 0;
        checkboxes.forEach(cb => {
            if (!cb.checked) {
                cb.click();
                cb.checked = true;
                cb.dispatchEvent(new Event('change', { bubbles: true }));
                clicked++;
            }
        });
        return { clicked: clicked, total: checkboxes.length };
    }
    
    function clickElement(selector) {
        const el = document.querySelector(selector);
        if (el) el.click();
    }
    
    function setDropdown(label, value) {
        const dropdown = document.querySelector(`div[role="button"][aria-label="${label}"]`);
        if (!dropdown) return;
        
        dropdown.click();
        
        setTimeout(() => {
            const options = document.querySelectorAll('div[role="option"]');
            const match = Array.from(options).find(opt => opt.textContent.trim() === value);
            if (match) match.click();
        }, 100);
    }
    
    function waitForDiscordToken(timeout = 5000) {
        return new Promise((resolve) => {
            const start = Date.now();
            const check = () => {
                const token = localStorage.getItem('token');
                if (token) {
                    resolve(token.replace(/^"|"$/g, ''));
                } else if (Date.now() - start < timeout) {
                    setTimeout(check, 200);
                } else {
                    resolve(null);
                }
            };
            check();
        });
    }
    
    function findCaptchaFrame() {
        const iframes = document.querySelectorAll('iframe');
        for (let iframe of iframes) {
            const src = iframe.src || '';
            if (src.includes('captcha') || src.includes('hcaptcha') || src.includes('recaptcha')) {
                return iframe;
            }
        }
        return null;
    }
    
    window.utils = {
        setInput,
        clickAllCheckboxes,
        clickElement,
        setDropdown,
        waitForDiscordToken,
        findCaptchaFrame
    };
})();
'''

# ============================================================================
# CONFIGURATION & GLOBALS
# ============================================================================

console = Console()
LOCK = threading.Lock()
SCRIPT_DIR = Path(__file__).parent
MS_CLIENT_ID = "d8fbe69d-15be-43fa-b204-5c5bc5a73ad7"  # Default Microsoft client ID

# Session counters (set at runtime by main)
SESSION_TARGET = 0          # 0 = infinite
SESSION_CREATED = 0         # accounts successfully created this session
SESSION_STOP = False        # signal workers to stop

# Load config
config_path = Path('input/config.json')

if config_path.exists():
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    # ── Patch missing keys from older config versions ──────────
    config.setdefault("email_api", {})
    config["email_api"].setdefault("hotmail007", {"client_key": "", "auto_buy": True})
    config["email_api"]["hotmail007"].setdefault("client_key", "")
    config["email_api"]["hotmail007"].setdefault("auto_buy", True)
    config["email_api"].setdefault("cybertemp", {"enabled": False, "api_key": ""})
    config["email_api"]["cybertemp"].setdefault("enabled", False)
    config["email_api"]["cybertemp"].setdefault("api_key", "")
    config.setdefault("proxy", {"enabled": False, "file": "input/proxies.txt"})
else:
    config = {
        "Threads": 1,
        "Humanize": False,
        "CustomizationSettings": {
            "Bio": False,
            "Avatar": False
        },
        "ai_api": {
            "groq": {
                "api_key": "",
                "model": "llama-3.3-70b-versatile"
            },
            "gemini": {
                "api_key": "",
                "model": "gemini-1.5-flash"
            }
        },
        "email_api": {
            "hotmail007": {
                "client_key": "8f91601f19da48fa8e1f4485280d27ee018119",
                "auto_buy": True
            },
            "cybertemp": {
                "enabled": True,
                "api_key": ""
            }
        },
        "proxy": {
            "enabled": False,
            "file": "input/proxies.txt"
        }
    }
    # Save default config
    config_path.parent.mkdir(exist_ok=True)
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)
    print(f"[DEBUG] Default config saved to {config_path}")


# Output directory
OUTPUT_DIR = Path('output')
OUTPUT_DIR.mkdir(exist_ok=True)

# ============================================================================
# LOGGER
# ============================================================================

class Logger:
    def __init__(self):
        pass
        
    def get_time(self):
        return datetime.now().strftime('%H:%M:%S')
    
    def info(self, message: str):
        print(f"{Fore.CYAN}[INFO]{Fore.RESET} {message}")
    
    def success(self, message: str):
        print(f"{Fore.GREEN}[SUCCESS]{Fore.RESET} {message}")
    
    def warning(self, message: str):
        print(f"{Fore.YELLOW}[WARNING]{Fore.RESET} {message}")
    
    def error(self, message: str):
        print(f"{Fore.RED}[ERROR]{Fore.RESET} {message}")
    
    def debug(self, message: str):
        print(f"{Fore.BLUE}[DEBUG]{Fore.RESET} {message}")

log = Logger()

# ============================================================================
# PROXY HANDLER
# ============================================================================

def load_proxies(config: dict) -> list:
    """Load proxies from file"""
    proxy_enabled = config.get("proxy", {}).get("enabled", False)
    if not proxy_enabled:
        return []
    
    proxy_file = config.get("proxy", {}).get("file", "input/proxies.txt")
    proxy_path = Path(proxy_file)
    
    if not proxy_path.exists():
        log.warning(f"Proxy file not found: {proxy_file}")
        log.info(f"Create file at: {proxy_path.absolute()}")
        return []
    
    try:
        with open(proxy_path, 'r', encoding='utf-8') as f:
            proxies = [line.strip() for line in f if line.strip()]
        
        if proxies:
            log.success(f"Loaded {len(proxies)} proxies from {proxy_file}")
            for i, p in enumerate(proxies, 1):
                log.info(f"  Proxy {i}: {p}")
            return proxies
        else:
            log.warning("Proxy file is empty")
            return []
    except Exception as e:
        log.error(f"Error loading proxies: {e}")
        return []


def get_random_proxy(proxies: list) -> str:
    """Get a random proxy from the list"""
    if not proxies:
        return None
    return random.choice(proxies)

# ============================================================================
# JAVASCRIPT HELPER CLASS
# ============================================================================

class JsHelper:
    _injected = set()
    
    @staticmethod
    def setup(page):
        """Inject JS utilities into page"""
        page_id = id(page)
        if page_id in JsHelper._injected:
            return
        try:
            page.evaluate(JS_UTILS)
            JsHelper._injected.add(page_id)
        except Exception as e:
            log.warning(f"JS inject error: {e}")
    
    @staticmethod
    def set_input(page, selector: str, value: str):
        """Set input value using JS"""
        value_escaped = value.replace('\\', '\\\\').replace('"', '\\"')
        selector_escaped = selector.replace('\\', '\\\\').replace('"', '\\"')
        page.evaluate(f'window.utils.setInput("{selector_escaped}", "{value_escaped}")')
    
    @staticmethod
    def click_all_checkboxes(page):
        """Click all checkboxes using JS"""
        return page.evaluate('window.utils.clickAllCheckboxes()')
    
    @staticmethod
    def click_element(page, selector: str):
        """Click element using JS"""
        selector_escaped = selector.replace('\\', '\\\\').replace('"', '\\"')
        page.evaluate(f'window.utils.clickElement("{selector_escaped}")')
    
    @staticmethod
    def find_captcha_frame(page):
        """Find captcha iframe using JS"""
        return page.evaluate('window.utils.findCaptchaFrame()')
    
    @staticmethod
    def wait_for_token(page, timeout: int = 5000):
        """Wait for Discord token in localStorage"""
        try:
            return page.evaluate(f'window.utils.waitForDiscordToken({timeout})')
        except:
            return None

# ============================================================================
# HOTMAIL007 EMAIL API
# ============================================================================

class Hotmail007API:
    """Hotmail007 API - CORRECT ENDPOINT STRUCTURE"""
    
    def __init__(self, client_key: str):
        self.session = requests.Session()
        self.session.verify = False  # Disable SSL verification
        self.client_key = client_key
        self.base_url = "https://api.hotmail007.com"
        self.mail_types = ["outlook", "hotmail"]
    
    def _fetch_email(self, mail_type: str) -> dict:
        """Internal method to fetch email of specific type"""
        url = f"{self.base_url}/api/mail/getMail"
        params = {
            "clientKey": self.client_key,
            "mailType": mail_type,
            "quantity": 1
        }
        try:
            resp = self.session.get(url, params=params, verify=False)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success") and data.get("code") == 0 and "data" in data:
                    accounts = data["data"]
                    if accounts:
                        parts = accounts[0].split(":")
                        if len(parts) >= 4:
                            return {
                                "success": True,
                                "email": parts[0],
                                "password": parts[1],
                                "token": parts[2],
                                "uuid": parts[3] if parts[3] else ""
                            }
        except Exception as e:
            pass
        return {"success": False}
    
    def buy_email(self, max_retries: int = 10) -> dict:
        """
        Purchase email with auto-retry (tries outlook and hotmail)
        Retries for up to 20 seconds
        Returns: {"success": True, "email": "xxx@outlook.com", "password": "xxx"}
        """
        if not self.client_key:
            log.error("Missing hotmail007 client_key in config")
            return {"success": False, "error": "Missing client_key"}
        
        log.info("Purchasing email from Hotmail007...")
        start_time = time.time()
        timeout = 20  # 20 seconds total timeout
        attempt = 0
        
        while (time.time() - start_time) < timeout:
            attempt += 1
            for mail_type in self.mail_types:
                log.info(f"Attempt {attempt}: Trying {mail_type}...")
                account = self._fetch_email(mail_type)
                if account.get("success"):
                    email = account.get("email")
                    password = account.get("password")
                    log.success(f"✓ Got {mail_type}: {email}")
                    return {
                        "success": True,
                        "email": email,
                        "password": password,
                        "token": account.get("token", ""),
                        "uuid": account.get("uuid", "")
                    }
            time.sleep(1)
        
        log.error("Failed to purchase email after 20s")
        return {"success": False, "error": "Timeout after 20s"}
    
    def check_inbox(self, email: str) -> dict:
        """Check inbox for verification emails"""
        try:
            response = self.session.get(
                f"{self.base_url}/inbox",
                params={
                    "clientKey": self.client_key,
                    "email": email
                },
                verify=False,
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                return {"success": True, "messages": data.get("messages", [])}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


# ============================================================================
# CYBERTEMP EMAIL API
# ============================================================================

class CybertempAPI:
    """CyberTemp API for temporary Discord-compatible email addresses"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.base_url = "https://api.cybertemp.xyz"
        self.session = requests.Session()
        self.session.verify = False
        if api_key:
            self.session.headers.update({"X-API-KEY": api_key})
    
    def get_discord_domains(self) -> list:
        """Fetch all discord-type domains from CyberTemp"""
        try:
            resp = self.session.get(
                f"{self.base_url}/getDomains",
                params={"type": "discord", "limit": 100},
                timeout=30
            )
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and data:
                    return data
                else:
                    log.error(f"CyberTemp getDomains unexpected response: {data}")
            else:
                log.error(f"CyberTemp getDomains HTTP {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            log.error(f"CyberTemp getDomains error: {e}")
        return []
    
    def create_email(self) -> dict:
        """
        Generate a random email address using a CyberTemp discord domain.
        Returns: {"success": True, "email": "user@domain.com", "password": "xxx"}
        """
        domains = self.get_discord_domains()
        if not domains:
            log.error("No CyberTemp discord domains available")
            return {"success": False, "error": "No discord domains available"}
    
        custom_domains = load_custom_domains()
        domain = random.choice(custom_domains) if custom_domains else "tempmail.com"
           

        local_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
        email = f"{local_part}@{domain}"
        password = ''.join(random.choices(string.ascii_letters + string.digits + "!@#$%", k=16))

        return {
            "success": True,
            "email": email,
            "password": password,
            "domain": domain
        }
    
    def check_inbox(self, email: str) -> dict:
        """Check inbox for messages sent to a CyberTemp address"""
        try:
            resp = self.session.get(
                f"{self.base_url}/getMail",
                params={"email": email},
                timeout=30
            )
            if resp.status_code == 200:
                data = resp.json()
                messages = data if isinstance(data, list) else data.get("messages", [])
                return {"success": True, "messages": messages}
            else:
                return {"success": False, "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


def get_hotmail007_email(config: dict) -> tuple:
    """
    Get email from Hotmail007 API with AUTO-RETRY
    Returns: (email, password, token, uuid) or (None, None, None, None) if failed
    """
    client_key = config.get("email_api", {}).get("hotmail007", {}).get("client_key", "").strip()
    auto_buy = config.get("email_api", {}).get("hotmail007", {}).get("auto_buy", True)
    
    if not client_key:
        log.warning("No Hotmail007 client_key configured")
        return None, None, None, None
    
    if not auto_buy:
        log.info("Auto-buy disabled in config")
        return None, None, None, None
    
    # Initialize API
    api = Hotmail007API(client_key)
    
    # Buy email with auto-retry (tries outlook and hotmail types)
    result = api.buy_email(max_retries=10)
    
    if result.get("success"):
        return (
            result.get("email"),
            result.get("password"),
            result.get("token", ""),
            result.get("uuid", "")
        )
    else:
        log.error("Failed to purchase email after all retries")
        return None, None, None, None


def get_cybertemp_email(config: dict) -> tuple:
    """
    Get a temporary email from CyberTemp API (always uses discord domains)
    Returns: (email, password, token, uuid) or (None, None, None, None) if failed
    """
    cybertemp_config = config.get("email_api", {}).get("cybertemp", {})
    enabled = cybertemp_config.get("enabled", False)
    api_key = cybertemp_config.get("api_key", "").strip()
    
    if not enabled:
        return None, None, None, None
    
    # Initialize API (api_key is optional - free tier works without subscription)
    api = CybertempAPI(api_key if api_key else None)
    
    result = api.create_email()
    
    if result.get("success"):
        return (
            result.get("email"),
            result.get("password"),
            "",  # No OAuth token for CyberTemp
            ""   # No uuid for CyberTemp
        )
    else:
        log.error("Failed to generate CyberTemp email")
        return None, None, None, None


def get_email_from_provider(config: dict) -> tuple:
    """
    Get email from configured provider (Hotmail007 or CyberTemp)
    Returns: (email, password, token, uuid, provider) or (None, None, None, None, None) if failed
    """
    cybertemp_enabled = config.get("email_api", {}).get("cybertemp", {}).get("enabled", False)
    hotmail_enabled = config.get("email_api", {}).get("hotmail007", {}).get("auto_buy", True)
    
    # Try CyberTemp first if enabled
    if cybertemp_enabled:
        log.info("Using CyberTemp email provider (discord domain)")
        email, password, token, uuid = get_cybertemp_email(config)
        if email:
            return email, password, token, uuid, "cybertemp"
    
    # Try Hotmail007 if enabled
    if hotmail_enabled:
        log.info("Using Hotmail007 email provider")
        email, password, token, uuid = get_hotmail007_email(config)
        if email:
            return email, password, token, uuid, "hotmail007"
    
    log.error("No email provider available or all failed")
    return None, None, None, None, None


# ============================================================================
# MS GRAPH EMAIL VERIFICATION
# ============================================================================

def get_access_token(refresh_token: str, client_id: str = None) -> Optional[str]:
    """Get MS Graph access token from refresh token"""
    try:
        cid = client_id or MS_CLIENT_ID
        if refresh_token.endswith("$"):
            refresh_token = refresh_token[:-1]
        
        response = requests.post(
            "https://login.microsoftonline.com/common/oauth2/v2.0/token",
            data={
                "client_id": cid,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
                "scope": "https://graph.microsoft.com/.default"
            },
            timeout=30,
            verify=False
        )
        result = response.json()
        return result.get("access_token")
    except Exception as e:
        log.error(f"Token refresh error: {e}")
        return None


def fetch_verification_url(email_data: Dict, timeout: int = 120) -> Optional[str]:
    """Fetch Discord verification URL from email using MS Graph API"""
    log.info("Fetching verification email from inbox...")
    
    refresh_token = email_data.get("token", "")
    client_id = email_data.get("uuid", "") or MS_CLIENT_ID
    
    access_token = get_access_token(refresh_token, client_id)
    if not access_token:
        log.error("Failed to get Graph access token")
        return None
    
    start_time = time.time()
    attempt = 0
    
    while (time.time() - start_time) < timeout:
        attempt += 1
        try:
            response = requests.get(
                "https://graph.microsoft.com/v1.0/me/messages",
                headers={"Authorization": f"Bearer {access_token}"},
                params={
                    "$top": 5,
                    "$orderby": "receivedDateTime desc",
                    "$select": "subject,body,from,bodyPreview,receivedDateTime"
                },
                timeout=15,
                verify=False
            )
            emails = response.json().get("value", [])
            
            if attempt % 5 == 0:
                elapsed = int(time.time() - start_time)
                log.info(f"Checking inbox... ({elapsed}s elapsed)")
            
            for email in emails:
                subject = email.get("subject", "").lower()
                from_addr = email.get("from", {}).get("emailAddress", {}).get("address", "").lower()
                
                # Must be a Discord email verification
                is_verify_email = (
                    ("verify" in subject or "confirm" in subject or "email" in subject) and
                    ("discord" in from_addr or "noreply@discord.com" in from_addr)
                )
                
                if not is_verify_email:
                    continue
                
                body_html = email.get("body", {}).get("content", "")
                
                # First priority: Direct discord.com/verify link
                verify_pattern = r'https://discord\.com/verify\?token=[^"\'\>\s]+'
                direct_match = re.search(verify_pattern, body_html)
                if direct_match:
                    log.success("Found verify link in email!")
                    return direct_match.group(0)
                
                # Second priority: Click tracking links
                click_patterns = [
                    r'https://click\.discord\.com/ls/click\?[^"\'\>\s]+',
                    r'https://links\.discord\.com[^"\'\>\s]+'
                ]
                
                for pat in click_patterns:
                    for m in re.finditer(pat, body_html):
                        url = m.group(0)
                        try:
                            resp = requests.get(url, allow_redirects=True, verify=False)
                            final_url = resp.url
                            
                            if "discord.com/verify" in final_url:
                                log.success("Found verify link via redirect!")
                                return final_url
                            
                            verify_in_body = re.search(r'https://discord\.com/verify\?token=[^"\'\>\s]+', resp.text)
                            if verify_in_body:
                                log.success("Found verify link in response body!")
                                return verify_in_body.group(0)
                        except:
                            pass
                
                log.warning("Discord email found but no valid verify link")
                    
        except Exception as e:
            log.warning(f"Graph API error: {e}")
        
        time.sleep(3)
    
    log.warning("Verification email not found after timeout")
    return None

# ============================================================================
# CYBERTEMP EMAIL VERIFICATION
# ============================================================================

def fetch_verification_url_cybertemp(email: str, api_key: str = None, timeout: int = 120) -> Optional[str]:
    """
    Poll CyberTemp /getMail until a Discord verification email arrives,
    then extract and return the verify URL.
    """
    log.info(f"Polling CyberTemp inbox for verification email: {email}")
    
    headers = {}
    if api_key:
        headers["X-API-KEY"] = api_key
    
    base_url = "https://api.cybertemp.xyz/getMail"
    start_time = time.time()
    attempt = 0
    seen_ids = set()
    
    while (time.time() - start_time) < timeout:
        attempt += 1
        try:
            resp = requests.get(
                base_url,
                params={"email": email, "limit": 25},
                headers=headers,
                timeout=20,
                verify=False
            )
            
            if resp.status_code != 200:
                log.debug(f"CyberTemp getMail HTTP {resp.status_code}")
                time.sleep(3)
                continue
            
            messages = resp.json()
            if not isinstance(messages, list):
                time.sleep(3)
                continue
            
            if attempt % 5 == 0:
                elapsed = int(time.time() - start_time)
                log.info(f"Checking CyberTemp inbox... ({elapsed}s elapsed, {len(messages)} emails found)")
            
            for msg in messages:
                msg_id = msg.get("id", "")
                if msg_id in seen_ids:
                    continue
                seen_ids.add(msg_id)
                
                subject   = (msg.get("subject") or "").lower()
                from_addr = (msg.get("from")    or "").lower()
                body_html = msg.get("html")  or msg.get("text") or ""
                
                # Must be from Discord and look like a verify email
                is_discord = "discord" in from_addr or "noreply@discord.com" in from_addr
                is_verify  = any(k in subject for k in ("verify", "confirm", "email"))
                
                if not (is_discord and is_verify):
                    continue
                
                
                # Direct verify link
                direct = re.search(r'https://discord\.com/verify\?token=[^"\'\>\s&]+(?:&[^"\'\>\s]+)*', body_html)
                if direct:
                    log.success("Extracted direct verify link!")
                    return direct.group(0)
                
                # Click-tracking / redirect links
                for pat in [
                    r'https://click\.discord\.com/ls/click\?[^"\'\>\s]+',
                    r'https://links\.discord\.com[^"\'\>\s]+'
                ]:
                    for m in re.finditer(pat, body_html):
                        url = m.group(0)
                        try:
                            r2 = requests.get(url, allow_redirects=True, verify=False)
                            if "discord.com/verify" in r2.url:
                                log.success("Extracted verify link via redirect!")
                                return r2.url
                            found = re.search(r'https://discord\.com/verify\?token=[^"\'\>\s]+', r2.text)
                            if found:
                                log.success("Extracted verify link from redirect body!")
                                return found.group(0)
                        except:
                            pass
                
                log.warning("Discord email found but could not extract verify link")
        
        except Exception as e:
            log.debug(f"CyberTemp poll error: {e}")
        
        time.sleep(3)
    
    log.warning("Verification email not found in CyberTemp inbox after timeout")
    return None


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_random_string(length: int) -> str:
    """Generate random alphanumeric string"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def generate_username() -> str:
    """Generate random username"""
    adjectives = ['Cool', 'Epic', 'Super', 'Mega', 'Ultra', 'Pro', 'Elite', 'Master']
    nouns = ['Gamer', 'Player', 'User', 'Hero', 'Legend', 'Champion', 'Warrior']
    return f"{random.choice(adjectives)}{random.choice(nouns)}{random.randint(100, 9999)}"


def generate_password(length: int = 16) -> str:
    """Generate secure random password"""
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(random.choices(chars, k=length))
    # Ensure it has at least one of each type
    if not any(c.isupper() for c in password):
        password = password[:1].upper() + password[1:]
    if not any(c.isdigit() for c in password):
        password = password[:-1] + str(random.randint(0, 9))
    return password


def check_token(token: str) -> str:
    """
    Check if Discord token is valid, locked, or invalid
    Returns: 'VALID', 'LOCKED', 'INVALID', or 'ERROR'
    """
    try:
        session = tls_client.Session(client_identifier="chrome_138", random_tls_extension_order=True)
        headers = {
            'Authorization': token,
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
        }
        
        # Use library endpoint like the working checker
        response = session.get(
            'https://discordapp.com/api/v9/users/@me/library',
            headers=headers
        )
        
        if response.status_code == 200:
            return 'VALID'
        elif response.status_code == 403:
            # Account locked/disabled
            return 'LOCKED'
        elif response.status_code == 401:
            return 'INVALID'
        elif response.status_code == 429:
            # Rate limited - treat as error to retry later
            return 'ERROR'
        else:
            return 'INVALID'
    except Exception as e:
        log.debug(f"Token check error: {e}")
        return 'ERROR'


def save_account_to_file(email: str, password: str, token: str, status: str):
    """
    Save account to appropriate file based on token status
    - valid.txt: Working accounts
    - locked.txt: Locked/disabled accounts
    - invalid.txt: Invalid tokens
    """
    try:
        # Determine output file based on status
        if status == 'VALID':
            output_file = OUTPUT_DIR / "valid.txt"
        elif status == 'LOCKED':
            output_file = OUTPUT_DIR / "locked.txt"
        else:  # INVALID or ERROR
            output_file = OUTPUT_DIR / "invalid.txt"
        
        # Save account
        with LOCK:
            with open(output_file, 'a', encoding='utf-8') as f:
                f.write(f"{email}:{password}:{token}\n")
        
        log.success(f"✓ Saved to {output_file.name}")
        return True
    except Exception as e:
        log.error(f"Failed to save account: {e}")
        return False


def check_email_verified_api(token: str):
    """Check if email is verified via API"""
    try:
        session = tls_client.Session(client_identifier="chrome_138", random_tls_extension_order=True)
        headers = {
            'Authorization': token,
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = session.get(
            'https://discord.com/api/v9/users/@me',
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            verified = data.get('verified', False)
            email = data.get('email', 'N/A')
            return verified, email
        
        return None, None
    except:
        return None, None


# ============================================================================
# REGISTRATION FORM FILLING - FIXED VERSION
# ============================================================================

async def fill_registration_form(page, email: str, display_name: str, username: str, password: str) -> bool:
    """
    Fill Discord registration form with proper element waiting
    """
    try:
        log.info("Filling form...")
        
        # Email - wait for it to exist
        try:
            email_element = await page.wait_for('input[name="email"]', timeout=10000)
            await email_element.send_keys(email)
            await asyncio.sleep(0.1)
        except Exception as e:
            log.error(f"Email input failed: {e}")
            return False
        
        # Display Name
        try:
            display_element = await page.wait_for('input[name="global_name"]', timeout=5000)
            await display_element.send_keys(display_name)
            await asyncio.sleep(0.1)
        except Exception as e:
            log.error(f"Display name input failed: {e}")
            return False
        
        # Username
        try:
            username_element = await page.wait_for('input[name="username"]', timeout=5000)
            await username_element.send_keys(username)
            await asyncio.sleep(0.1)
        except Exception as e:
            log.error(f"Username input failed: {e}")
            return False
        
        # Password
        try:
            password_element = await page.wait_for('input[aria-label="Password"]', timeout=5000)
            await password_element.send_keys(password)
            await asyncio.sleep(0.1)
        except Exception as e:
            log.error(f"Password input failed: {e}")
            return False
        
        # Date of birth
        await asyncio.sleep(0.2)
        await fill_date_of_birth(page)
        await asyncio.sleep(0.1)
        
        # Inject JS and click checkboxes
        try:
            await page.evaluate(JS_UTILS)
            await asyncio.sleep(0.1)
            result = await page.evaluate('window.utils.clickAllCheckboxes()')
            if result and result.get('clicked', 0) > 0:
                log.success(f"✓ Clicked {result.get('clicked')} checkbox(es)")
            await asyncio.sleep(0.1)
        except Exception as e:
            log.debug(f"Checkbox error: {e}")
        
        # Find and click submit button
        clicked = False
        
        # Wait a bit for submit button to be enabled
        await asyncio.sleep(0.3)
        
        # Try finding submit button
        try:
            buttons = await page.query_selector_all('button')
            for button in buttons:
                try:
                    text = await button.text_content()
                    if text and any(keyword in text for keyword in ['Continue', 'Create', 'Submit', 'Register']):
                        await button.click()
                        clicked = True
                        break
                except:
                    continue
        except:
            pass
        
        # Fallback: submit by type
        if not clicked:
            try:
                submit = await page.query_selector('[type="submit"]')
                if submit:
                    await submit.click()
                    clicked = True
            except:
                pass
        
        if not clicked:
            log.error("Could not find submit button")
            return False
        
        # Try method 3: Last resort - evaluate and click
        if not clicked:
            try:
                log.info("Trying submit via evaluate...")
                clicked_eval = await page.evaluate('''() => {
                    const buttons = document.querySelectorAll('button');
                    for (const btn of buttons) {
                        const text = btn.textContent || '';
                        if (text.includes('Continue') || text.includes('Create') || text.includes('Submit')) {
                            btn.click();
                            return true;
                        }
                    }
                    return false;
                }''')
                
                if clicked_eval:
                    clicked = True
                    log.success("Clicked submit button via evaluate")
            except Exception as e:
                log.warning(f"Evaluate submit failed: {e}")
        
        if not clicked:
            log.error("✗ Failed to click submit button!")
            return False
        
        log.success("✓ Form submitted!")
        return True
        
    except Exception as e:
        log.error(f"Form fill error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def fill_date_of_birth(page):
    """Fill date of birth dropdowns - INSTANT"""
    
    # Generate random DOB
    months = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]
    day = str(random.randint(1, 28))
    month = random.choice(months)
    year = str(random.randint(1990, 2004))
    
    try:
        # INSTANT date fill - no delays
        result = await page.evaluate(f'''
        (async () => {{
            if (!window.discordUtils) {{
                class DOMHelper {{
                    static query(selector, all = false) {{
                        return all ? [...document.querySelectorAll(selector)] : document.querySelector(selector);
                    }}
                    static waitForCondition(fn, interval = 20, timeout = 3000) {{
                        return new Promise((resolve, reject) => {{
                            const start = Date.now();
                            const check = () => {{
                                const result = fn();
                                if (result) {{
                                    resolve(result);
                                }} else if (Date.now() - start > timeout) {{
                                    reject(new Error('Timeout'));
                                }} else {{
                                    setTimeout(check, interval);
                                }}
                            }};
                            check();
                        }});
                    }}
                }}

                async function setDropdown(label, value) {{
                    try {{
                        const dropdown = DOMHelper.query(`div[role="button"][aria-label="${{label}}"]`);
                        if (!dropdown) return {{ success: false }};
                        dropdown.click();
                        await new Promise(r => setTimeout(r, 50)); // MINIMAL delay
                        
                        const options = await DOMHelper.waitForCondition(() => {{
                            const opts = DOMHelper.query('div[role="option"]', true);
                            return opts.length > 0 ? opts : null;
                        }}, 20, 2000);
                        
                        const match = options.find(opt => opt.textContent.trim() === value);
                        if (match) {{
                            match.click();
                            return {{ success: true }};
                        }}
                        return {{ success: false }};
                    }} catch (err) {{
                        return {{ success: false }};
                    }}
                }}

                window.discordUtils = {{ setDropdown }};
            }}
            
            try {{
                const monthResult = await window.discordUtils.setDropdown("Month", "{month}");
                if (!monthResult.success) return monthResult;
                
                await new Promise(r => setTimeout(r, 50)); // MINIMAL delay
                
                const dayResult = await window.discordUtils.setDropdown("Day", "{day}");
                if (!dayResult.success) return dayResult;
                
                await new Promise(r => setTimeout(r, 50)); // MINIMAL delay
                
                const yearResult = await window.discordUtils.setDropdown("Year", "{year}");
                return yearResult;
            }} catch (err) {{
                return {{ success: false, error: err.message }};
            }}
        }})()
        ''')
        
        if result and isinstance(result, dict) and result.get('success'):
            log.success(f"✓ DOB: {month} {day}, {year}")
        
    except Exception as e:
        log.debug(f"DOB error: {e}")


# ============================================================================
# WAIT FOR ACCOUNT CREATION
# ============================================================================

async def wait_for_account_creation(page, timeout: int = 300) -> bool:
    """Wait for account to be created by detecting URL change to channels/@me"""
    start_time = time.time()
    i = 0
    last_url = ""
    
    while (time.time() - start_time) < timeout:
        await asyncio.sleep(0.1)  # Very fast polling - check every 100ms
        i += 1
        
        try:
            # Get URL using multiple methods for reliability
            current_url = ""
            
            # Method 1: Use page.url property
            try:
                current_url = str(page.url) if page.url else ""
            except:
                pass
            
            # Method 2: Fallback to JavaScript evaluation
            if not current_url:
                try:
                    url_result = await page.evaluate('window.location.href')
                    if hasattr(url_result, 'value'):
                        current_url = url_result.value
                    elif isinstance(url_result, dict) and 'value' in url_result:
                        current_url = url_result['value']
                    else:
                        current_url = str(url_result) if url_result else ''
                except:
                    pass
            
            # Log URL changes
            if current_url and current_url != last_url:
                last_url = current_url
            
            # Check for successful account creation
            if current_url and ('discord.com/channels/@me' in current_url or 'channels/%40me' in current_url):
                return True
            
            # Alternative success patterns
            if current_url and 'discord.com/channels/' in current_url and '/channels/@me' not in current_url:
                # Might have joined a server directly
                return True
            
            # Progress updates every 30 seconds
            if i % 300 == 0:  # 300 * 0.1s = 30s
                elapsed = int(time.time() - start_time)
                log.info(f"{elapsed}s elapsed, still waiting...")
        
        except Exception as e:
            log.debug(f"Error checking URL: {e}")
    
    log.error("Timeout waiting for account creation")
    return False


# ============================================================================
# TOKEN EXTRACTION
# ============================================================================

async def wait_for_discord_token(page, timeout: int = 30, email: str = None, password: str = None):
    """Extract Discord authentication token using API call"""
    log.info("Fetching Discord token via API...")
    
    if not email or not password:
        log.error("Email and password required for token fetch")
        return None
    
    # Wait a bit for account to be ready
    await asyncio.sleep(3)
    
    attempts = 0
    max_attempts = 5
    
    while attempts < max_attempts:
        attempts += 1
        
        try:
            # Use API to fetch token
            token = await fetch_discord_token(email, password)
            
            if token:
                log.success(f"✓ Token fetched via API! (attempt {attempts})")
                return token
            else:
                log.warning(f"API returned empty token (attempt {attempts})")
        
        except Exception as e:
            log.debug(f"Error fetching token via API (attempt {attempts}): {e}")
        
        # Wait before retry
        await asyncio.sleep(3)
    
    log.error(f"Could not fetch token after {attempts} attempts")
    return None


# ============================================================================
# SAFE BROWSER NAVIGATION HELPER
# ============================================================================

async def safe_browser_get(browser, url: str, max_retries: int = 3):
    """
    Safely navigate browser to URL with retry logic for StopIteration errors
    """
    for attempt in range(max_retries):
        try:
            page = await browser.get(url)
            return page
        except (StopIteration, RuntimeError) as e:
            if attempt < max_retries - 1:
                log.warning(f"Browser navigation failed (attempt {attempt + 1}/{max_retries}), retrying...")
                await asyncio.sleep(2)
            else:
                log.error(f"Failed to navigate to {url} after {max_retries} attempts")
                raise
    return None


# ============================================================================
# MAIN WORKER FUNCTION
# ============================================================================

async def worker():
    """Main worker function to create Discord account"""
    global SESSION_CREATED, SESSION_STOP
    browser = None
    profile_dir = None
    
    # Check if session target already reached
    if SESSION_STOP:
        return
    
    try:
        # Get proxy from session config (set in terminal)
        proxy = config.get("proxy_session")
        
        if proxy:
            log.info(f"Using proxy: {proxy}")
        else:
            log.info("No proxy configured - using direct connection")
        
        # Generate account details
        username = generate_username()
        display_name = random.choice([
            # Arabic/Middle Eastern Names
            'Afham', 'Arhan', 'Ahmed', 'Ali', 'Hassan', 'Ibrahim', 'Karim', 'Malik', 'Nasser', 'Omar',
            'Rashid', 'Samir', 'Tariq', 'Walid', 'Youssef', 'Zahra', 'Amina', 'Fatima', 'Layla', 'Mariam',
            'Noor', 'Rania', 'Samira', 'Yasmin', 'Nadia', 'Hana', 'Iman', 'Leila', 'Maha', 'Salma',
            # Western Names
            'Alex', 'Jordan', 'Taylor', 'Morgan', 'Casey', 'Riley', 'Sam', 'Blake', 'Drew', 'Avery',
            'Jamie', 'Parker', 'Quinn', 'Rowan', 'Sage', 'Scout', 'Skyler', 'Tatum', 'Vale', 'Xander',
            # European Names
            'Henrik', 'Johan', 'Magnus', 'Nils', 'Soren', 'Stellan', 'Anders', 'Lars', 'Mikael', 'Olaf',
            'Pierre', 'Jean', 'Claude', 'Antoine', 'Benoit', 'Cedric', 'Dominique', 'Fabrice', 'Gerard', 'Henri',
            'Klaus', 'Gunther', 'Friedrich', 'Wolfgang', 'Jasper', 'Matthias', 'Sebastian', 'Christoph', 'Stefan', 'Andreas',
            # Asian Names
            'Akira', 'Hideo', 'Kenji', 'Koji', 'Masaru', 'Noboru', 'Satoshi', 'Takeshi', 'Toshiro', 'Yuki',
            'Wei', 'Lei', 'Ming', 'Jun', 'Feng', 'Hua', 'Jie', 'Liang', 'Peng', 'Xia',
            'Arjun', 'Ankit', 'Aditya', 'Devesh', 'Harish', 'Raj', 'Vikram', 'Rohan', 'Sanjay', 'Nikhil',
            # Fashion/Sport Names
            'Ashton', 'Bradley', 'Calvin', 'Derek', 'Ethan', 'Fiona', 'Graham', 'Harper', 'Isabella', 'Jackson',
            'Kai', 'Logan', 'Mason', 'Nathan', 'Owen', 'Patrick', 'Quinn', 'Ryan', 'Sean', 'Tyler'
        ])
        
        # Try to get email from configured provider
        email_from_api, email_password, email_token, email_uuid, email_provider = get_email_from_provider(config)
        
        if email_from_api:
            email = email_from_api
            # Use email password as Discord password
            password = email_password
        else:
            # Fallback to temporary email
            custom_domains = load_custom_domains()
            fallback_domain = random.choice(custom_domains) if custom_domains else "tempmail.com"
            email = f"{generate_random_string(12)}@{fallback_domain}"

            email_password = "N/A"
            password = generate_password()
            log.info(f"Using temporary email: {email}")
        
        # Create temp profile directory
        import tempfile
        profile_dir = tempfile.mkdtemp(prefix='discord_profile_')
        
        # Browser arguments
        browser_args = [
            f'--user-data-dir={profile_dir}',
            '--no-first-run',
            '--disable-default-apps',
            '--disable-extensions',
            '--disable-plugins',
            '--disable-web-security',
            '--disable-features=TranslateUI',
            '--disable-ipc-flooding-protection'
        ]
        
        # Add proxy if available
        if proxy:
            # Make sure proxy has http:// prefix
            if not proxy.startswith('http://') and not proxy.startswith('https://') and not proxy.startswith('socks5://'):
                proxy = f'http://{proxy}'
            browser_args.append(f'--proxy-server={proxy}')
            log.info(f"Proxy argument added: --proxy-server={proxy}")
        
        # Start Brave browser
        log.info("Starting Brave browser...")
        
        # Auto-detect Brave path based on OS
        import platform
        system = platform.system()
        brave_path = None
        
        if system == "Windows":
            brave_paths = [
                r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
                r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
                os.path.expanduser(r"~\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe")
            ]
        elif system == "Darwin":  # macOS
            brave_paths = [
                "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
            ]
        else:  # Linux
            brave_paths = [
                "/usr/bin/brave-browser",
                "/usr/bin/brave",
                "/snap/bin/brave"
            ]
        
        # Find Brave
        for path in brave_paths:
            if os.path.exists(path):
                brave_path = path
                log.info(f"Found Brave at: {path}")
                break
        
        if not brave_path:
            log.warning("Brave not found, using default browser")
        
        browser = await uc.start(
            headless=False,
            browser_executable_path=brave_path,
            browser_args=browser_args + [
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process'
            ]
        )
        
        # Wait a moment for browser to initialize
        await asyncio.sleep(2)
        
        # Use safe navigation helper
        log.info("Loading Discord registration page...")
        page = await safe_browser_get(browser, "https://discord.com/register")
        
        # Wait for page to fully load - check for email input to be present
        log.info("Waiting for page to load...")
        page_loaded = False
        for attempt in range(20):  # 20 attempts × 0.5s = 10 seconds max
            try:
                email_check = await page.query_selector('input[name="email"]')
                if email_check:
                    page_loaded = True
                    log.success("✓ Page loaded")
                    break
            except:
                pass
            await asyncio.sleep(0.5)
        
        if not page_loaded:
            log.warning("Page load timeout - continuing anyway")
        
        # Additional 500ms for all JavaScript to initialize
        await asyncio.sleep(0.5)
        
        # Fill form
        success = await fill_registration_form(page, email, display_name, username, password)
        if not success:
            log.error("Form fill failed")
            return
        
        # Random clicks to appear more human
        try:
            for _ in range(5):
                # Get random coordinates
                x = random.randint(100, 800)
                y = random.randint(100, 600)
                await page.mouse_click(x, y)
                await asyncio.sleep(random.uniform(0.05, 0.15))  # Very fast clicks
        except:
            pass  # Don't fail if clicks don't work
        
        # Wait for manual captcha solving
        log.info("Waiting for captcha to be solved...")
        
        created = await wait_for_account_creation(page)
        if not created:
            log.error("Account creation failed - no redirect detected")
            log.error("Please check if you solved the captcha correctly")
            return
        
        # Account is created - immediately extract token
        
        log.info("Extracting token...")
        token = await wait_for_discord_token(page, email=email, password=password)
        
        if token:
            # Clean token
            if token.startswith('"') and token.endswith('"'):
                token = token[1:-1]
            
            # Validate token format
            token_match = re.search(r'([a-zA-Z0-9_-]{20,})\.([a-zA-Z0-9_-]{6})\.([a-zA-Z0-9_-]{27,})', token)
            if token_match:
                token = f"{token_match.group(1)}.{token_match.group(2)}.{token_match.group(3)}"
            
            # Only show token
            log.success(f"Token: {token[:30]}...")
            
            # STEP 1: Verify email first
            log.info("Checking email verification status...")
            verified, user_email = check_email_verified_api(token)
            
            if verified is not None:
                if verified:
                    log.success("✓ Email already verified!")
                else:
                    log.info("Email not verified. Attempting to verify...")
                    
                    # Auto-verify email if not verified and we have email data
                    if email_provider == "hotmail007" and email_token:
                        email_data = {
                            "email": email,
                            "password": email_password,
                            "token": email_token,
                            "uuid": email_uuid
                        }
                        
                        verify_url = fetch_verification_url(email_data)
                        if verify_url:
                            log.success(f"Got verification URL!")
                            # Navigate to verify URL
                            try:
                                verify_page = await safe_browser_get(browser, verify_url)
                                await asyncio.sleep(3)
                                
                                log.info("╔════════════════════════════════════════════════════════════╗")
                                log.info("║  EMAIL VERIFICATION CAPTCHA DETECTED                        ║")
                                log.info("║  Please solve the captcha manually in the browser           ║")
                                log.info("║  The script will wait for you to complete it...             ║")
                                log.info("╚════════════════════════════════════════════════════════════╝")
                                
                                # Wait for user to solve verification captcha - check every 5 seconds
                                log.info("Waiting for verification captcha to be solved...")
                                max_wait = 120  # Wait up to 2 minutes
                                elapsed = 0
                                verified = False
                                
                                while elapsed < max_wait:
                                    await asyncio.sleep(5)
                                    elapsed += 5
                                    
                                    # Check if verified
                                    verified, _ = check_email_verified_api(token)
                                    if verified:
                                        log.success("✓ Email verified!")
                                        log.success("✓ Verification confirmed via API")
                                        break
                                    
                                    if elapsed % 15 == 0:
                                        log.info(f"Still waiting for captcha solve... ({elapsed}s elapsed)")
                                
                                if not verified:
                                    log.warning("Verification timeout - captcha may not have been solved")
                                    
                            except Exception as e:
                                log.error(f"Error navigating to verify URL: {e}")
                        else:
                            log.warning("Could not fetch verification URL")
                    
                    elif email_provider == "cybertemp":
                        ct_api_key = config.get("email_api", {}).get("cybertemp", {}).get("api_key", "").strip() or None
                        
                        verify_url = fetch_verification_url_cybertemp(email, api_key=ct_api_key)
                        if verify_url:
                            log.success(f"Got verification URL!")
                            try:
                                verify_page = await safe_browser_get(browser, verify_url)
                                await asyncio.sleep(5)
                                
                                # Poll until Discord API confirms verified (no captcha needed for verify link)
                                log.info("Waiting for verification to confirm...")
                                max_wait = 60
                                elapsed = 0
                                verified = False
                                
                                while elapsed < max_wait:
                                    await asyncio.sleep(5)
                                    elapsed += 5
                                    verified, _ = check_email_verified_api(token)
                                    if verified:
                                        log.success("✓ Email verified successfully!")
                                        break
                                    if elapsed % 15 == 0:
                                        log.info(f"Confirming verification... ({elapsed}s elapsed)")
                                
                                if not verified:
                                    log.warning("Verification not confirmed — may still be processing")
                            except Exception as e:
                                log.error(f"Error navigating to verify URL: {e}")
                        else:
                            log.warning("Could not find verification email in CyberTemp inbox")
            
            # STEP 2: Now check token status
            log.info("Checking token status...")
            result = check_token(token)
            log.info(f"Token Status: {result}")
            
            # Save to appropriate file based on status
            save_account_to_file(email, password, token, result)
            
            # Update session counter
            with LOCK:
                SESSION_CREATED += 1
                created_now = SESSION_CREATED
            
            # Simple account count display
            log.success(f"Account #{created_now} created")
            
            # ═══════════════════════════════════════════════════════════
            # IMMEDIATE COMPLETE BROWSER CLEANUP AFTER SAVE
            # ═══════════════════════════════════════════════════════════
            log.info("🧹 Starting complete browser cleanup...")
            
            # Step 1: Clear all browser data via JavaScript
            try:
                clear_js = """
                    (async () => {
                        try {
                            // Clear localStorage & sessionStorage
                            localStorage.clear();
                            sessionStorage.clear();
                        } catch(e) { console.log('Storage clear error:', e); }

                        try {
                            // Clear all IndexedDB databases
                            if (window.indexedDB && indexedDB.databases) {
                                const dbs = await indexedDB.databases();
                                for (const db of dbs) {
                                    indexedDB.deleteDatabase(db.name);
                                }
                            }
                        } catch(e) { console.log('IndexedDB clear error:', e); }

                        try {
                            // Unregister all service workers
                            if (navigator.serviceWorker) {
                                const regs = await navigator.serviceWorker.getRegistrations();
                                for (const reg of regs) { 
                                    await reg.unregister(); 
                                }
                            }
                        } catch(e) { console.log('Service worker clear error:', e); }

                        try {
                            // Clear all caches
                            if (window.caches) {
                                const keys = await caches.keys();
                                for (const key of keys) { 
                                    await caches.delete(key); 
                                }
                            }
                        } catch(e) { console.log('Cache clear error:', e); }

                        return 'cleared';
                    })();
                """
                
                try:
                    await page.evaluate(clear_js)
                    log.success("✓ JavaScript storage cleared")
                except:
                    log.debug("Could not clear JS storage (page may be closed)")
            except:
                pass
            
            # Step 2: Close all pages/tabs (without CDP)
            try:
                # Simply close the browser - this will close all tabs
                log.success("✓ Preparing to close browser and all tabs")
            except:
                pass
            
            # Step 3: Stop the browser completely
            try:
                await browser.stop()
                log.success("✓ Browser stopped")
            except:
                log.debug("Browser already stopped")
            
            # Step 4: Force kill any remaining browser processes
            if PSUTIL_AVAILABLE:
                try:
                    # Kill Brave/Chrome processes
                    for proc in psutil.process_iter(['pid', 'name']):
                        try:
                            proc_name = proc.info['name'].lower()
                            if any(x in proc_name for x in ['brave', 'chrome', 'chromium']) and proc.info['pid'] != os.getpid():
                                # Check if it's our profile
                                try:
                                    cmdline = ' '.join(proc.cmdline())
                                    if profile_dir and profile_dir in cmdline:
                                        os.kill(proc.info['pid'], signal.SIGTERM)
                                        log.success(f"✓ Killed browser process {proc.info['pid']}")
                                except:
                                    pass
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                except Exception as e:
                    log.debug(f"Process kill error: {e}")
            else:
                log.debug("psutil not available, skipping process kill (install with: pip install psutil)")
            
            await asyncio.sleep(0.5)  # Give processes time to terminate
            
            # Step 5: Completely wipe the profile directory
            if profile_dir and os.path.exists(profile_dir):
                try:
                    # Wait a moment for processes to fully close
                    await asyncio.sleep(1)
                    
                    # Force remove with retries
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            shutil.rmtree(profile_dir, ignore_errors=True)
                            
                            # Verify deletion
                            if not os.path.exists(profile_dir):
                                log.success(f"✓ Profile directory wiped: {profile_dir}")
                                break
                        except Exception as e:
                            if attempt < max_retries - 1:
                                await asyncio.sleep(1)
                            else:
                                log.warning(f"Could not fully remove profile: {e}")
                except Exception as e:
                    log.debug(f"Profile wipe error: {e}")
            
            # Step 6: Clear any temp files
            try:
                temp_dir = tempfile.gettempdir()
                for item in os.listdir(temp_dir):
                    if item.startswith('discord_profile_'):
                        item_path = os.path.join(temp_dir, item)
                        try:
                            if os.path.isdir(item_path):
                                shutil.rmtree(item_path, ignore_errors=True)
                        except:
                            pass
                log.success("✓ Temp files cleaned")
            except:
                pass
            
            log.success("🧹 Complete cleanup finished - no traces left!")
            
            # Set browser to None to prevent further cleanup in finally block
            browser = None
            profile_dir = None
            
            # Check if session target reached (using renamed variable to avoid conflict)
            session_target = SESSION_TARGET
            if session_target > 0 and created_now >= session_target:
                with LOCK:
                    SESSION_STOP = True
                log.success(f"🎯 Target reached! {created_now}/{session_target} accounts created. Stopping...")
                return
        else:
            log.warning("Could not extract token, but account may be created")
        
        # Keep browser open for 120 seconds cooldown with real-time countdown
        log.info("Cooldown: Waiting 120 seconds before next account...")
        for remaining in range(120, 0, -1):
            mins, secs = divmod(remaining, 60)
            timer = f"{mins:02d}:{secs:02d}"
            print(f"\r{Fore.YELLOW}[COOLDOWN]{Fore.RESET} Time remaining: {Fore.CYAN}{timer}{Fore.RESET} ", end='', flush=True)
            await asyncio.sleep(1)
        print()  # New line after countdown
        log.success("Cooldown complete! Starting next account...")
    
    except StopIteration as e:
        log.error(f"Browser tab error: No page available. This usually means the browser closed unexpectedly.")
        log.error("Try restarting the script or check if another browser instance is interfering.")
    except RuntimeError as e:
        log.error(f"Runtime error: {e}")
        if "StopIteration" in str(e):
            log.error("Browser tab error detected. Try closing all browser windows and restart the script.")
    except Exception as e:
        log.error(f"Worker error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Emergency cleanup - only runs if something failed before normal cleanup
        if browser is not None:
            log.info("Emergency cleanup: Closing browser...")
            try:
                await browser.stop()
            except:
                pass
        
        # Emergency profile wipe
        if profile_dir and os.path.exists(profile_dir):
            try:
                shutil.rmtree(profile_dir, ignore_errors=True)
            except:
                pass


# ============================================================================
# MAIN FUNCTION
# ============================================================================

async def main():
    """Main function"""
    global SESSION_TARGET, SESSION_CREATED, SESSION_STOP

    # Print ASCII art banner
    banner = f"""
{Fore.CYAN}
    

{'██████╗  █████╗ ███╗   ██╗ ██████╗ █████╗ ██╗  ██╗███████╗'.center(90)}
{'██╔══██╗██╔══██╗████╗  ██║██╔════╝██╔══██╗██║ ██╔╝██╔════╝'.center(90)}
{'██████╔╝███████║██╔██╗ ██║██║     ███████║█████╔╝ █████╗  '.center(90)}
{'██╔═══╝ ██╔══██║██║╚██╗██║██║     ██╔══██║██╔═██╗ ██╔══╝  '.center(90)}
{'██║     ██║  ██║██║ ╚████║╚██████╗██║  ██║██║  ██╗███████╗'.center(90)}
{'╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝'.center(90)}

                 Discord Account Generator v3.3                
              CyberTemp / Hotmail007 │ Manual Captcha           
      ══════════════════════════════════════════════════════════
{Fore.RESET}
    """
    print(banner)

    divider = f"{Fore.CYAN}{'━'*60}{Fore.RESET}"

    # ── Step 1: Email provider ──────────────────────────────────
    print(divider)
    print(f"{Fore.CYAN}  [1/4]  Email Provider{Fore.RESET}")
    print(divider)
    print(f"  {Fore.WHITE}1{Fore.RESET} → CyberTemp  {Fore.CYAN}(temp discord-domain emails){Fore.RESET}")
    print(f"  {Fore.WHITE}2{Fore.RESET} → Hotmail007 {Fore.CYAN}(purchased outlook/hotmail accounts){Fore.RESET}")
    while True:
        choice = input(f"\n{Fore.GREEN}Select provider [1/2]: {Fore.RESET}").strip()
        if choice in ("1", "2"):
            break
        log.warning("Please enter 1 or 2")

    provider_name = "cybertemp" if choice == "1" else "hotmail007"

    # ── Step 2: API key ─────────────────────────────────────────
    print(f"\n{divider}")
    print(f"{Fore.CYAN}  [2/4]  API Key{Fore.RESET}")
    print(divider)

    if provider_name == "cybertemp":
        print(f"  {Fore.YELLOW}CyberTemp:{Fore.RESET} Free tier works without a key (standard speed).")
        print(f"  Add a subscription key for instant / priority access.")
        api_key_input = input(f"\n{Fore.GREEN}Enter CyberTemp API key (or press Enter to skip): {Fore.RESET}").strip()
        # Apply to config
        config["email_api"]["cybertemp"]["enabled"] = True
        config["email_api"]["cybertemp"]["api_key"] = api_key_input
        config["email_api"]["hotmail007"]["auto_buy"] = False  # disable other provider
        if api_key_input:
            log.success(f"CyberTemp key set → Priority mode active")
        else:
            log.info("No key entered → CyberTemp Free Tier (standard speed)")

    else:  # hotmail007
        print(f"  {Fore.YELLOW}Hotmail007:{Fore.RESET} Client key required to purchase emails.")
        while True:
            api_key_input = input(f"\n{Fore.GREEN}Enter Hotmail007 client key: {Fore.RESET}").strip()
            if api_key_input:
                break
            log.warning("Client key cannot be empty for Hotmail007")
        config["email_api"]["hotmail007"]["client_key"] = api_key_input
        config["email_api"]["hotmail007"]["auto_buy"] = True
        config["email_api"]["cybertemp"]["enabled"] = False  # disable other provider
        log.success(f"Hotmail007 key set")

    # ── Step 3: Proxy ───────────────────────────────────────────
    print(f"\n{divider}")
    print(f"{Fore.CYAN}  [3/4]  Proxy{Fore.RESET}")
    print(divider)
    proxy_input = input(
        f"{Fore.GREEN}Enter proxy (user:pass@ip:port) or press Enter to skip: {Fore.RESET}"
    ).strip()

    if proxy_input:
        if not proxy_input.startswith(('http://', 'https://', 'socks5://')):
            proxy_input = f'http://{proxy_input}'
        config["proxy_session"] = proxy_input
        log.success(f"Proxy enabled: {proxy_input}")
    else:
        config["proxy_session"] = None
        log.info("No proxy - using direct connection")

    # ── Step 4: Account count ───────────────────────────────────
    print(f"\n{divider}")
    print(f"{Fore.CYAN}  [4/4]  How Many Accounts?{Fore.RESET}")
    print(divider)
    print(f"  Enter a number  → create that many accounts then stop")
    print(f"  Enter {Fore.WHITE}0{Fore.RESET}          → run {Fore.CYAN}infinitely{Fore.RESET} until you press Ctrl+C")
    while True:
        count_input = input(f"\n{Fore.GREEN}Number of accounts to create [0 = infinite]: {Fore.RESET}").strip()
        if count_input.isdigit():
            SESSION_TARGET = int(count_input)
            break
        log.warning("Please enter a valid number (0 for infinite)")

    SESSION_CREATED = 0
    SESSION_STOP = False

    if SESSION_TARGET == 0:
        log.info("Mode: INFINITE  — press Ctrl+C to stop")
    else:
        log.info(f"Mode: FIXED     — will create {SESSION_TARGET} account(s) then stop")

    print(f"\n{divider}\n")

    # ── Start workers ────────────────────────────────────────────
    thread_count = int(config.get('Threads', 1))
    log.info(f"Starting {thread_count} worker thread(s)\n")

    while True:
        if SESSION_STOP:
            break
        tasks = [asyncio.create_task(worker()) for _ in range(thread_count)]
        await asyncio.gather(*tasks)
        if SESSION_STOP:
            break

    print(f"\n{Fore.GREEN}{'━'*60}{Fore.RESET}")
    print(f"{Fore.GREEN}  Session complete — {SESSION_CREATED} account(s) saved to output/discord_accounts.txt{Fore.RESET}")
    print(f"{Fore.GREEN}{'━'*60}{Fore.RESET}\n")


if __name__ == "__main__":
    warnings.filterwarnings('ignore', category=ResourceWarning)
    
    try:
        uc.loop().run_until_complete(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[WARNING]{Fore.RESET} Stopped by user")
    except Exception as e:
        print(f"\n{Fore.RED}[ERROR]{Fore.RESET} {e}")
