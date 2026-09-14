class ShortStrangle:

    name = "شورت استرانگل"

    def find(self, groups):

        results = []

        for group_key, options in groups.items():

            underlying, expiry = group_key

            calls = [
                option
                for option in options
                if option["type"] == "CALL"
                and option["bid"] > 0
            ]

            puts = [
                option
                for option in options
                if option["type"] == "PUT"
                and option["bid"] > 0
            ]

            for call in calls:

                for put in puts:

                    if call["strike"] <= put["strike"]:
                        continue

                    premium = (
                        call["bid"]
                        + put["bid"]
                    )

                    if premium <= 0:
                        continue

                    lower_break_even = (
                        put["strike"]
                        - premium
                    )

                    upper_break_even = (
                        call["strike"]
                        + premium
                    )

                    results.append({
                        "strategy": self.name,
                        "underlying": underlying,
                        "expiry": expiry,

                        "call_symbol": call["symbol"],
                        "call_strike": call["strike"],
                        "call_price": call["bid"],

                        "put_symbol": put["symbol"],
                        "put_strike": put["strike"],
                        "put_price": put["bid"],

                        "premium": premium,

                        "lower_break_even": lower_break_even,
                        "upper_break_even": upper_break_even,

                        "max_profit": premium,

                        "max_loss": None,

                        "roi": None
                    })

        return results