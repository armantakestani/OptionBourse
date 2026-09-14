class BearPutSpread:

    name = "پوت اسپرد نزولی"

    def find(self, groups):

        results = []

        for group_key, options in groups.items():

            underlying, expiry = group_key

            puts = [
                option
                for option in options
                if option["type"] == "PUT"
                and option["ask"] > 0
                and option["bid"] > 0
            ]

            for long_put in puts:

                for short_put in puts:

                    if long_put["strike"] <= short_put["strike"]:
                        continue

                    net_debit = (
                        long_put["ask"]
                        - short_put["bid"]
                    )

                    if net_debit <= 0:
                        continue

                    strike_difference = (
                        long_put["strike"]
                        - short_put["strike"]
                    )

                    max_profit = (
                        strike_difference
                        - net_debit
                    )

                    max_loss = net_debit

                    if max_profit <= 0:
                        continue

                    break_even = (
                        long_put["strike"]
                        - net_debit
                    )

                    roi = (
                        max_profit
                        / max_loss
                    ) * 100

                    results.append({
                        "strategy": self.name,
                        "underlying": underlying,
                        "expiry": expiry,

                        "buy_symbol": long_put["symbol"],
                        "buy_strike": long_put["strike"],
                        "buy_price": long_put["ask"],

                        "sell_symbol": short_put["symbol"],
                        "sell_strike": short_put["strike"],
                        "sell_price": short_put["bid"],

                        "net_debit": net_debit,
                        "max_profit": max_profit,
                        "max_loss": max_loss,
                        "break_even": break_even,
                        "roi": roi
                    })

        return results