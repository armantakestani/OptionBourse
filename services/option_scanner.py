import re
from itertools import combinations


class OptionScanner:

    def __init__(self, tse_client):
        self.tse = tse_client

    def search_options(self, symbol):

        data = self.tse.get_instrument_search(symbol)

        if isinstance(data, dict):
            items = data.get("instrumentSearch", [])

            if not items:
                items = data.get("instrument", [])

            if not items:
                items = data.get("items", [])

        elif isinstance(data, list):
            items = data

        else:
            items = []

        options = []

        for item in items:

            name = item.get("lVal30") or ""
            option_symbol = item.get("lVal18AFC") or ""
            ins_code = item.get("insCode")

            if not ins_code:
                continue

            match = re.search(
                r"اختيار([خف])\s+(.+?)-(\d+)-(\d{4}/\d{2}/\d{2})",
                name
            )

            if not match:
                continue

            option_type_code = match.group(1)
            underlying = match.group(2).strip()
            strike = float(match.group(3))
            expiry = match.group(4)

            if option_type_code == "خ":
                option_type = "CALL"
            else:
                option_type = "PUT"

            options.append({
                "symbol": option_symbol,
                "ins_code": str(ins_code),
                "name": name,
                "underlying": underlying,
                "type": option_type,
                "strike": strike,
                "expiry": expiry
            })

        return options

    def get_market_price(self, option):

        try:
            data = self.tse.get_best_limits(option["ins_code"])

            if isinstance(data, dict):
                limits = data.get("bestLimits", [])

                if not limits:
                    limits = data.get("bestLimitsData", [])

            elif isinstance(data, list):
                limits = data

            else:
                limits = []

            if not limits:
                return None

            level_one = limits[0]

            bid = level_one.get("pMeDem", 0)
            ask = level_one.get("pMeOf", 0)

            try:
                bid = float(bid or 0)
            except:
                bid = 0

            try:
                ask = float(ask or 0)
            except:
                ask = 0

            option["bid"] = bid
            option["ask"] = ask

            return option

        except Exception:
            return None

    def enrich_options(self, options):

        result = []

        for option in options:

            market_option = self.get_market_price(option)

            if market_option is None:
                continue

            if market_option["bid"] <= 0 and market_option["ask"] <= 0:
                continue

            result.append(market_option)

        return result

    def group_options(self, options):

        groups = {}

        for option in options:

            key = (
                option["underlying"],
                option["expiry"]
            )

            if key not in groups:
                groups[key] = []

            groups[key].append(option)

        return groups

    def scan(self, symbol):

        options = self.search_options(symbol)

        options = self.enrich_options(options)

        return self.group_options(options)