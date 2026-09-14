import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes
)

from api.tse_client import TseClient
from services.option_scanner import OptionScanner

from strategies.bull_call_spread import BullCallSpread
from strategies.bear_call_spread import BearCallSpread
from strategies.covered_call import CoveredCall
from strategies.bear_put_spread import BearPutSpread
from strategies.short_strangle import ShortStrangle
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

MIN_ROI = 50

UNDERLYINGS = {
    "ahrm": "اهرم",
    "khodro": "خودرو",
    "khsa": "خساپا",
    "webmelat": "وبملت",
    "websader": "وبصادر",
    "vatejarat": "وتجارت",
    "shasta": "شستا"
}


tse = TseClient()
scanner = OptionScanner(tse)

bull_call = BullCallSpread()
bear_call = BearCallSpread()
covered_call = CoveredCall()
bear_put = BearPutSpread()
short_strangle = ShortStrangle()


def format_number(value):

    if value is None:
        return "-"

    if isinstance(value, float):

        if value.is_integer():
            return f"{int(value):,}"

        return f"{value:,.2f}"

    return f"{value:,}"


def strategy_keyboard():

    keyboard = [

        [
            InlineKeyboardButton(
                "🟢 کال اسپرد صعودی",
                callback_data="strategy_bull_call"
            )
        ],

        [
            InlineKeyboardButton(
                "🔴 کال اسپرد نزولی",
                callback_data="strategy_bear_call"
            )
        ],

        [
            InlineKeyboardButton(
                "🟡 کاورد کال",
                callback_data="strategy_covered_call"
            )
        ],

        [
            InlineKeyboardButton(
                "🔵 پوت اسپرد نزولی",
                callback_data="strategy_bear_put"
            )
        ],

        [
            InlineKeyboardButton(
                "⚡ شورت استرانگل",
                callback_data="strategy_short_strangle"
            )
        ]

    ]

    return InlineKeyboardMarkup(keyboard)


def symbol_keyboard(strategy):

    keyboard = [

        [
            InlineKeyboardButton(
                "🟣 اهرم",
                callback_data=f"symbol_{strategy}_ahrm"
            ),

            InlineKeyboardButton(
                "🚗 خودرو",
                callback_data=f"symbol_{strategy}_khodro"
            )
        ],

        [
            InlineKeyboardButton(
                "🟢 خساپا",
                callback_data=f"symbol_{strategy}_khsa"
            ),

            InlineKeyboardButton(
                "🏦 وبملت",
                callback_data=f"symbol_{strategy}_webmelat"
            )
        ],

        [
            InlineKeyboardButton(
                "🔵 وبصادر",
                callback_data=f"symbol_{strategy}_websader"
            ),

            InlineKeyboardButton(
                "🏦 وتجارت",
                callback_data=f"symbol_{strategy}_vatejarat"
            )
        ],

        [
            InlineKeyboardButton(
                "🟠 شستا",
                callback_data=f"symbol_{strategy}_shasta"
            )
        ],

        [
            InlineKeyboardButton(
                "⬅️ تغییر استراتژی",
                callback_data="back_to_strategy"
            )
        ]

    ]

    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = (
        "📊 <b>OptiBours</b>\n\n"
        "🎯 دستیار تحلیل استراتژی‌های آپشن\n\n"
        "لطفاً استراتژی موردنظر را انتخاب کنید:"
    )

    await update.message.reply_text(
        text,
        reply_markup=strategy_keyboard(),
        parse_mode="HTML"
    )


async def strategy_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    strategy = query.data.replace(
        "strategy_",
        ""
    )

    strategy_names = {

        "bull_call": "🟢 کال اسپرد صعودی",

        "bear_call": "🔴 کال اسپرد نزولی",

        "covered_call": "🟡 کاورد کال",

        "bear_put": "🔵 پوت اسپرد نزولی",

        "short_strangle": "⚡ شورت استرانگل"
    }

    strategy_name = strategy_names.get(
        strategy,
        "📊 استراتژی"
    )

    text = (
        f"📊 <b>{strategy_name}</b>\n\n"
        "📌 لطفاً نماد پایه را انتخاب کنید:"
    )

    await query.edit_message_text(
        text,
        reply_markup=symbol_keyboard(strategy),
        parse_mode="HTML"
    )


async def symbol_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    data = query.data

    parts = data.split("_")

    strategy = "_".join(parts[1:-1])
    symbol_code = parts[-1]

    symbol = UNDERLYINGS.get(symbol_code)

    if not symbol:
        await query.edit_message_text(
            "❌ نماد انتخاب‌شده معتبر نیست."
        )
        return

    strategy_names = {

        "bull_call": "🟢 کال اسپرد صعودی",

        "bear_call": "🔴 کال اسپرد نزولی",

        "covered_call": "🟡 کاورد کال",

        "bear_put": "🔵 پوت اسپرد نزولی",

        "short_strangle": "⚡ شورت استرانگل"
    }

    strategy_name = strategy_names.get(
        strategy,
        "📊 استراتژی"
    )

    await query.edit_message_text(
        f"⏳ <b>در حال بررسی بازار...</b>\n\n"
        f"📊 استراتژی: {strategy_name}\n"
        f"📌 نماد: {symbol}\n\n"
        f"🔎 در حال دریافت اطلاعات آپشن‌ها...\n"
        f"📈 در حال محاسبه موقعیت‌های مناسب...",
        parse_mode="HTML"
    )

    try:

        groups = scanner.scan(symbol)

        if strategy == "bull_call":

            results = bull_call.find(groups)

        elif strategy == "bear_call":

            results = bear_call.find(groups)

        elif strategy == "bear_put":

            results = bear_put.find(groups)

        elif strategy == "short_strangle":

            results = short_strangle.find(groups)

        elif strategy == "covered_call":

            underlying_price = get_underlying_price(symbol)

            results = covered_call.find(
                groups,
                underlying_price
            )

        else:

            results = []

        if strategy != "short_strangle":

            results = [
                result
                for result in results
                if result.get("roi") is not None
                and result["roi"] >= MIN_ROI
            ]

            results.sort(
                key=lambda x: x["roi"],
                reverse=True
            )

        else:

            results.sort(
                key=lambda x: x["premium"],
                reverse=True
            )

        results = results[:5]

        if not results:

            keyboard = InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "🔄 بررسی مجدد",
                        callback_data=f"symbol_{strategy}_{symbol_code}"
                    )
                ],

                [
                    InlineKeyboardButton(
                        "📌 تغییر نماد",
                        callback_data=f"strategy_{strategy}"
                    )
                ],

                [
                    InlineKeyboardButton(
                        "📊 تغییر استراتژی",
                        callback_data="back_to_strategy"
                    )
                ]

            ])

            await query.edit_message_text(

                f"📊 <b>{strategy_name}</b>\n"
                f"📌 نماد: {symbol}\n\n"
                f"❌ در حال حاضر موقعیت مناسبی "
                f"با بازده حداقل {MIN_ROI}% پیدا نشد.",

                reply_markup=keyboard,
                parse_mode="HTML"
            )

            return

        text = build_result_message(
            strategy,
            symbol,
            results
        )

        keyboard = InlineKeyboardMarkup([

            [
                InlineKeyboardButton(
                    "🔄 بررسی مجدد",
                    callback_data=f"symbol_{strategy}_{symbol_code}"
                )
            ],

            [
                InlineKeyboardButton(
                    "📌 تغییر نماد",
                    callback_data=f"strategy_{strategy}"
                )
            ],

            [
                InlineKeyboardButton(
                    "📊 تغییر استراتژی",
                    callback_data="back_to_strategy"
                )
            ]

        ])

        await query.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    except Exception as e:

        print("ERROR:", e)

        await query.edit_message_text(

            "❌ <b>خطا در دریافت اطلاعات بازار</b>\n\n"
            "لطفاً چند لحظه بعد دوباره تلاش کنید.",

            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "🔄 تلاش مجدد",
                        callback_data=f"symbol_{strategy}_{symbol_code}"
                    )
                ],

                [
                    InlineKeyboardButton(
                        "📊 تغییر استراتژی",
                        callback_data="back_to_strategy"
                    )
                ]

            ]),

            parse_mode="HTML"
        )


async def back_to_strategy(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    await query.edit_message_text(
        "📊 <b>انتخاب استراتژی</b>\n\n"
        "استراتژی موردنظر را انتخاب کنید:",
        reply_markup=strategy_keyboard(),
        parse_mode="HTML"
    )


def get_underlying_price(symbol):

    try:

        search_data = tse.get_instrument_search(
            symbol
        )

        if isinstance(search_data, dict):

            items = search_data.get(
                "instrumentSearch",
                []
            )

        else:

            items = []

        for item in items:

            option_name = item.get(
                "lVal30",
                ""
            )

            instrument_symbol = item.get(
                "lVal18AFC",
                ""
            )

            if (
                instrument_symbol == symbol
                or option_name == symbol
            ):

                ins_code = item.get(
                    "insCode"
                )

                if not ins_code:
                    continue

                data = tse.get_closing_price_info(
                    ins_code
                )

                return float(
                    data.get(
                        "pClosing",
                        0
                    )
                )

    except Exception as e:

        print(
            "Underlying price error:",
            e
        )

    return 0


def build_result_message(
    strategy,
    symbol,
    results
):

    strategy_names = {

        "bull_call": "🟢 کال اسپرد صعودی",

        "bear_call": "🔴 کال اسپرد نزولی",

        "covered_call": "🟡 کاورد کال",

        "bear_put": "🔵 پوت اسپرد نزولی",

        "short_strangle": "⚡ شورت استرانگل"
    }

    title = strategy_names.get(
        strategy,
        "📊 استراتژی"
    )

    text = (
        f"📊 <b>{title}</b>\n"
        f"📌 نماد پایه: <b>{symbol}</b>\n\n"
    )

    for index, result in enumerate(
        results,
        start=1
    ):

        text += (
            f"━━━━━━━━━━━━━━\n"
            f"🏆 <b>فرصت شماره {index}</b>\n\n"
        )

        text += (
            f"📅 تاریخ سررسید: "
            f"<b>{result['expiry']}</b>\n\n"
        )

        if strategy == "bull_call":

            text += (
                f"🟢 خرید: "
                f"<b>{result['buy_symbol']}</b>\n"
                f"🎯 قیمت اعمال: "
                f"{format_number(result['buy_strike'])}\n"
                f"💰 قیمت خرید: "
                f"{format_number(result['buy_price'])}\n\n"

                f"🔴 فروش: "
                f"<b>{result['sell_symbol']}</b>\n"
                f"🎯 قیمت اعمال: "
                f"{format_number(result['sell_strike'])}\n"
                f"💰 قیمت فروش: "
                f"{format_number(result['sell_price'])}\n\n"

                f"💵 خالص پرداختی: "
                f"<b>{format_number(result['net_debit'])}</b>\n"
                f"📈 حداکثر سود: "
                f"<b>{format_number(result['max_profit'])}</b>\n"
                f"📉 حداکثر ضرر: "
                f"<b>{format_number(result['max_loss'])}</b>\n"
                f"⚖️ نقطه سر به سری: "
                f"<b>{format_number(result['break_even'])}</b>\n"
                f"📊 بازده: "
                f"<b>{result['roi']:.2f}%</b>\n"
            )

        elif strategy == "bear_call":

            text += (
                f"🔴 فروش: "
                f"<b>{result['sell_symbol']}</b>\n"
                f"🎯 قیمت اعمال: "
                f"{format_number(result['sell_strike'])}\n"
                f"💰 قیمت فروش: "
                f"{format_number(result['sell_price'])}\n\n"

                f"🟢 خرید: "
                f"<b>{result['buy_symbol']}</b>\n"
                f"🎯 قیمت اعمال: "
                f"{format_number(result['buy_strike'])}\n"
                f"💰 قیمت خرید: "
                f"{format_number(result['buy_price'])}\n\n"

                f"💰 خالص دریافتی: "
                f"<b>{format_number(result['net_credit'])}</b>\n"
                f"📈 حداکثر سود: "
                f"<b>{format_number(result['max_profit'])}</b>\n"
                f"📉 حداکثر ضرر: "
                f"<b>{format_number(result['max_loss'])}</b>\n"
                f"⚖️ نقطه سر به سری: "
                f"<b>{format_number(result['break_even'])}</b>\n"
                f"📊 بازده: "
                f"<b>{result['roi']:.2f}%</b>\n"
            )

        elif strategy == "bear_put":

            text += (
                f"🟢 خرید: "
                f"<b>{result['buy_symbol']}</b>\n"
                f"🎯 قیمت اعمال: "
                f"{format_number(result['buy_strike'])}\n"
                f"💰 قیمت خرید: "
                f"{format_number(result['buy_price'])}\n\n"

                f"🔴 فروش: "
                f"<b>{result['sell_symbol']}</b>\n"
                f"🎯 قیمت اعمال: "
                f"{format_number(result['sell_strike'])}\n"
                f"💰 قیمت فروش: "
                f"{format_number(result['sell_price'])}\n\n"

                f"💵 خالص پرداختی: "
                f"<b>{format_number(result['net_debit'])}</b>\n"
                f"📈 حداکثر سود: "
                f"<b>{format_number(result['max_profit'])}</b>\n"
                f"📉 حداکثر ضرر: "
                f"<b>{format_number(result['max_loss'])}</b>\n"
                f"⚖️ نقطه سر به سری: "
                f"<b>{format_number(result['break_even'])}</b>\n"
                f"📊 بازده: "
                f"<b>{result['roi']:.2f}%</b>\n"
            )

        elif strategy == "covered_call":

            text += (
                f"🟢 قیمت سهم: "
                f"<b>{format_number(result['stock_price'])}</b>\n\n"

                f"🔴 فروش Call: "
                f"<b>{result['sell_symbol']}</b>\n"
                f"🎯 قیمت اعمال: "
                f"{format_number(result['sell_strike'])}\n"
                f"💰 قیمت فروش: "
                f"{format_number(result['sell_price'])}\n\n"

                f"💵 درآمد فروش Call: "
                f"<b>{format_number(result['premium'])}</b>\n"
                f"📈 حداکثر سود: "
                f"<b>{format_number(result['max_profit'])}</b>\n"
                f"📉 حداکثر ضرر: "
                f"<b>{format_number(result['max_loss'])}</b>\n"
                f"⚖️ نقطه سر به سری: "
                f"<b>{format_number(result['break_even'])}</b>\n"
                f"📊 بازده: "
                f"<b>{result['roi']:.2f}%</b>\n"
            )

        elif strategy == "short_strangle":

            text += (
                f"🔴 فروش Call: "
                f"<b>{result['call_symbol']}</b>\n"
                f"🎯 قیمت اعمال: "
                f"{format_number(result['call_strike'])}\n"
                f"💰 قیمت فروش: "
                f"{format_number(result['call_price'])}\n\n"

                f"🔴 فروش Put: "
                f"<b>{result['put_symbol']}</b>\n"
                f"🎯 قیمت اعمال: "
                f"{format_number(result['put_strike'])}\n"
                f"💰 قیمت فروش: "
                f"{format_number(result['put_price'])}\n\n"

                f"💰 خالص دریافتی: "
                f"<b>{format_number(result['premium'])}</b>\n"
                f"📈 حداکثر سود: "
                f"<b>{format_number(result['max_profit'])}</b>\n"
                f"📉 حداکثر ضرر: <b>نامحدود</b>\n"
                f"⚖️ سر به سری پایین: "
                f"<b>{format_number(result['lower_break_even'])}</b>\n"
                f"⚖️ سر به سری بالا: "
                f"<b>{format_number(result['upper_break_even'])}</b>\n"
            )

        text += "\n"

    text += (
        "━━━━━━━━━━━━━━\n"
        f"🔎 حداقل بازده موردنظر: {MIN_ROI}%\n"
        f"🎯 تعداد فرصت‌های پیدا شده: {len(results)}"
    )

    return text


def main():

    if not BOT_TOKEN:

        raise RuntimeError(
            "BOT_TOKEN environment variable is not set."
        )

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            strategy_handler,
            pattern=r"^strategy_"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            symbol_handler,
            pattern=r"^symbol_"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            back_to_strategy,
            pattern=r"^back_to_strategy$"
        )
    )

    print("OptiEdge bot started...")

    application.run_polling()


if __name__ == "__main__":
    main()
