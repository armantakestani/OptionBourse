import requests


class TseClient:

    BASE_URL = "https://cdn.tsetmc.com/api/"

    def __init__(self):
        self.session = requests.Session()
        # مقدار را از ENV می‌خوانیم، اگر نبود پروکسی نمی‌زنیم
        proxy_url = os.getenv("IRAN_PROXY") 
        if proxy_url:
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
        url = (
            f"{self.BASE_URL}"
            f"ClosingPrice/GetClosingPriceInfo/{ins_code}"
        )

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