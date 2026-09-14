class BearCallSpread:

    name = "کال اسپرد نزولی"

    def find(self, groups):

        results = []

        for group_key, options in groups.items():

            underlying, expiry = group_key

            calls = [
                option
                for option in options
                if option["type"] == "CALL"
                and option["bid"] > 0
                and option["ask"] > 0
            ]

            for short_call in calls:

                for long_call in calls:

                    if long_call["strike"] <= short_call["strike"]:
                        continue

                    net_credit = (
                        short_call["bid"]
                        - long_call["ask"]
                    )

                    if net_credit <= 0:
                        continue

                    strike_difference = (
                        long_call["strike"]
                        - short_call["strike"]
                    )

                    max_profit = net_credit

                    max_loss = (
                        strike_difference
                        - net_credit
                    )

                    if max_loss <= 0:
                        continue

                    break_even = (
                        short_call["strike"]
                        + net_credit
                    )

                    roi = (
                        max_profit
                        / max_loss
                    ) * 100

                    results.append({
                        "strategy": self.name,
                        "underlying": underlying,
                        "expiry": expiry,

                        "sell_symbol": short_call["symbol"],
                        "sell_strike": short_call["strike"],
                        "sell_price": short_call["bid"],

                        "buy_symbol": long_call["symbol"],
                        "buy_strike": long_call["strike"],
                        "buy_price": long_call["ask"],

                        "net_credit": net_credit,
                        "max_profit": max_profit,
                        "max_loss": max_loss,
                        "break_even": break_even,
                        "roi": roi
                    })

        return results