class BullCallSpread:

    name = "کال اسپرد صعودی"

    def find(self, groups):

        results = []

        for group_key, options in groups.items():

            underlying, expiry = group_key

            calls = [
                option
                for option in options
                if option["type"] == "CALL"
                and option["ask"] > 0
                and option["bid"] >= 0
            ]

            for long_call in calls:

                for short_call in calls:

                    if short_call["strike"] <= long_call["strike"]:
                        continue

                    if short_call["bid"] <= 0:
                        continue

                    net_debit = (
                        long_call["ask"]
                        - short_call["bid"]
                    )

                    if net_debit <= 0:
                        continue

                    strike_difference = (
                        short_call["strike"]
                        - long_call["strike"]
                    )

                    max_profit = (
                        strike_difference
                        - net_debit
                    )

                    max_loss = net_debit

                    if max_profit <= 0:
                        continue

                    break_even = (
                        long_call["strike"]
                        + net_debit
                    )

                    roi = (
                        max_profit
                        / max_loss
                    ) * 100

                    results.append({
                        "strategy": self.name,
                        "underlying": underlying,
                        "expiry": expiry,

                        "buy_symbol": long_call["symbol"],
                        "buy_strike": long_call["strike"],
                        "buy_price": long_call["ask"],

                        "sell_symbol": short_call["symbol"],
                        "sell_strike": short_call["strike"],
                        "sell_price": short_call["bid"],

                        "net_debit": net_debit,
                        "max_profit": max_profit,
                        "max_loss": max_loss,
                        "break_even": break_even,
                        "roi": roi
                    })

        return results