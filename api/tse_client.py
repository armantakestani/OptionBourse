import requests
import os
import urllib3

# جلوگیری از نمایش هشدارهای امنیتی (چون داریم SSL رو غیرفعال می‌کنیم)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class TseClient:
    BASE_URL = "https://cdn.tsetmc.com/api/"

    def __init__(self):
        self.session = requests.Session()
        
        # غیرفعال کردن بررسی SSL برای تمام درخواست‌های این سشن
        self.session.verify = False
        
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        
        proxy_url = os.getenv("IRAN_PROXY") 
        if proxy_url:
            # فرمت ساکس5 باید به این صورت باشد: socks5://ip:port
            self.session.proxies = {
                "http": proxy_url,
                "https": proxy_url,
            }

    def get_instrument_search(self, symbol):
        url = f"{self.BASE_URL}Instrument/GetInstrumentSearch/{symbol}"
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        return response.json()

    def get_closing_price_info(self, ins_code):
        url = f"{self.BASE_URL}ClosingPrice/GetClosingPriceInfo/{ins_code}"
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        return response.json()

    def get_best_limits(self, ins_code):
        url = f"{self.BASE_URL}BestLimits/{ins_code}"
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        return response.json()

    def get_instrument_info(self, ins_code):
        url = f"{self.BASE_URL}Instrument/GetInstrumentInfo/{ins_code}"
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
