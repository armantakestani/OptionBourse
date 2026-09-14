class CoveredCall:

    name = "کاورد کال"

    def find(self, groups, underlying_price):

        results = []

        for group_key, options in groups.items():

            underlying, expiry = group_key

            calls = [
                option
                for option in options
                if option["type"] == "CALL"
                and option["bid"] > 0
            ]

            for call in calls:

                premium = call["bid"]

                break_even = (
                    underlying_price
                    - premium
                )

                max_profit = (
                    call["strike"]
                    - underlying_price
                    + premium
                )

                if max_profit <= 0:
                    continue

                max_loss = (
                    underlying_price
                    - premium
                )

                if max_loss <= 0:
                    continue

                roi = (
                    max_profit
                    / max_loss
                ) * 100

                results.append({
                    "strategy": self.name,
                    "underlying": underlying,
                    "expiry": expiry,

                    "stock_price": underlying_price,

                    "sell_symbol": call["symbol"],
                    "sell_strike": call["strike"],
                    "sell_price": call["bid"],

                    "premium": premium,

                    "max_profit": max_profit,
                    "max_loss": max_loss,
                    "break_even": break_even,
                    "roi": roi
                })

        return results