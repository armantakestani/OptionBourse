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

UNDERLYINGS = [
    "اهرم",
    "سپا",
    "ملت"
]


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
                callback_data="bull_call"
            )
        ],

        [
            InlineKeyboardButton(
                "🔴 کال اسپرد نزولی",
                callback_data="bear_call"
            )
        ],

        [
            InlineKeyboardButton(
                "🟡 کاورد کال",
                callback_data="covered_call"
            )
        ],

        [
            InlineKeyboardButton(
                "🔵 پوت اسپرد نزولی",
                callback_data="bear_put"
            )
        ],

        [
            InlineKeyboardButton(
                "⚡ شورت استرانگل",
                callback_data="short_strangle"
            )
        ]

    ]

    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = (
        "📊 دستیار استراتژی آپشن\n\n"
        "لطفاً استراتژی موردنظر را انتخاب کنید:"
    )

    await update.message.reply_text(
        text,
        reply_markup=strategy_keyboard()
    )


async def strategy_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    strategy = query.data

    await query.edit_message_text(
        "⏳ در حال بررسی بازار...\n\n"
        "🔎 دریافت اطلاعات آپشن‌ها..."
    )

    try:

        all_results = []

        for underlying in UNDERLYINGS:

            groups = scanner.scan(underlying)

            if strategy == "bull_call":

                results = bull_call.find(groups)

            elif strategy == "bear_call":

                results = bear_call.find(groups)

            elif strategy == "bear_put":

                results = bear_put.find(groups)

            elif strategy == "short_strangle":

                results = short_strangle.find(groups)

            elif strategy == "covered_call":

                underlying_price = get_underlying_price(
                    underlying
                )

                results = covered_call.find(
                    groups,
                    underlying_price
                )

            else:

                results = []

            all_results.extend(results)

        if strategy != "short_strangle":

            all_results = [
                result
                for result in all_results
                if result["roi"] >= MIN_ROI
            ]

            all_results.sort(
                key=lambda x: x["roi"],
                reverse=True
            )

        else:

            all_results.sort(
                key=lambda x: x["premium"],
                reverse=True
            )

        all_results = all_results[:5]

        if not all_results:

            await query.edit_message_text(
                "❌ در حال حاضر فرصت مناسبی "
                "با شرایط تعیین‌شده پیدا نشد."
            )

            return

        text = build_result_message(
            strategy,
            all_results
        )

        await query.edit_message_text(text)

    except Exception as e:

        print("ERROR:", e)

        await query.edit_message_text(
            "❌ هنگام بررسی بازار خطایی رخ داد.\n\n"
            "لطفاً دوباره تلاش کنید."
        )


def get_underlying_price(symbol):

    options = scanner.search_options(symbol)

    if not options:
        return 0

    try:

        underlying_name = options[0]["underlying"]

        search_data = tse.get_instrument_search(
            underlying_name
        )

        items = search_data.get(
            "instrumentSearch",
            []
        )

        for item in items:

            if item.get("lVal18AFC") == underlying_name:

                ins_code = item.get("insCode")

                data = tse.get_closing_price_info(
                    ins_code
                )

                return float(
                    data.get("pClosing", 0)
                )

    except Exception:
        pass

    return 0


def build_result_message(strategy, results):

    titles = {
        "bull_call": "🟢 کال اسپرد صعودی",
        "bear_call": "🔴 کال اسپرد نزولی",
        "covered_call": "🟡 کاورد کال",
        "bear_put": "🔵 پوت اسپرد نزولی",
        "short_strangle": "⚡ شورت استرانگل"
    }

    title = titles.get(
        strategy,
        "📊 استراتژی"
    )

    text = f"📊 {title}\n\n"

    for index, result in enumerate(results, start=1):

        text += f"━━━━━━━━━━━━━━\n"
        text += f"🎯 فرصت شماره {index}\n\n"

        text += (
            f"📌 نماد پایه: "
            f"{result['underlying']}\n"
        )

        text += (
            f"📅 تاریخ سررسید: "
            f"{result['expiry']}\n\n"
        )

        if strategy == "bull_call":

            text += (
                f"🟢 خرید: {result['buy_symbol']}\n"
                f"🎯 قیمت اعمال: "
                f"{format_number(result['buy_strike'])}\n"
                f"💰 قیمت خرید: "
                f"{format_number(result['buy_price'])}\n\n"
            )

            text += (
                f"🔴 فروش: {result['sell_symbol']}\n"
                f"🎯 قیمت اعمال: "
                f"{format_number(result['sell_strike'])}\n"
                f"💰 قیمت فروش: "
                f"{format_number(result['sell_price'])}\n\n"
            )

            text += (
                f"💵 خالص پرداختی: "
                f"{format_number(result['net_debit'])}\n"
                f"📈 حداکثر سود: "
                f"{format_number(result['max_profit'])}\n"
                f"📉 حداکثر ضرر: "
                f"{format_number(result['max_loss'])}\n"
                f"⚖️ نقطه سر به سری: "
                f"{format_number(result['break_even'])}\n"
                f"📊 بازده: "
                f"{result['roi']:.2f}%\n\n"
            )

        elif strategy == "bear_call":

            text += (
                f"🔴 فروش: {result['sell_symbol']}\n"
                f"🎯 قیمت اعمال: "
                f"{format_number(result['sell_strike'])}\n"
                f"💰 قیمت فروش: "
                f"{format_number(result['sell_price'])}\n\n"
            )

            text += (
                f"🟢 خرید: {result['buy_symbol']}\n"
                f"🎯 قیمت اعمال: "
                f"{format_number(result['buy_strike'])}\n"
                f"💰 قیمت خرید: "
                f"{format_number(result['buy_price'])}\n\n"
            )

            text += (
                f"💰 خالص دریافتی: "
                f"{format_number(result['net_credit'])}\n"
                f"📈 حداکثر سود: "
                f"{format_number(result['max_profit'])}\n"
                f"📉 حداکثر ضرر: "
                f"{format_number(result['max_loss'])}\n"
                f"⚖️ نقطه سر به سری: "
                f"{format_number(result['break_even'])}\n"
                f"📊 بازده: "
                f"{result['roi']:.2f}%\n\n"
            )

        elif strategy == "bear_put":

            text += (
                f"🟢 خرید: {result['buy_symbol']}\n"
                f"🎯 قیمت اعمال: "
                f"{format_number(result['buy_strike'])}\n"
                f"💰 قیمت خرید: "
                f"{format_number(result['buy_price'])}\n\n"
            )

            text += (
                f"🔴 فروش: {result['sell_symbol']}\n"
                f"🎯 قیمت اعمال: "
                f"{format_number(result['sell_strike'])}\n"
                f"💰 قیمت فروش: "
                f"{format_number(result['sell_price'])}\n\n"
            )

            text += (
                f"💵 خالص پرداختی: "
                f"{format_number(result['net_debit'])}\n"
                f"📈 حداکثر سود: "
                f"{format_number(result['max_profit'])}\n"
                f"📉 حداکثر ضرر: "
                f"{format_number(result['max_loss'])}\n"
                f"⚖️ نقطه سر به سری: "
                f"{format_number(result['break_even'])}\n"
                f"📊 بازده: "
                f"{result['roi']:.2f}%\n\n"
            )

        elif strategy == "short_strangle":

            text += (
                f"🔴 فروش Call: "
                f"{result['call_symbol']}\n"
                f"🎯 قیمت اعمال: "
                f"{format_number(result['call_strike'])}\n"
                f"💰 قیمت فروش: "
                f"{format_number(result['call_price'])}\n\n"
            )

            text += (
                f"🔴 فروش Put: "
                f"{result['put_symbol']}\n"
                f"🎯 قیمت اعمال: "
                f"{format_number(result['put_strike'])}\n"
                f"💰 قیمت فروش: "
                f"{format_number(result['put_price'])}\n\n"
            )

            text += (
                f"💰 خالص دریافتی: "
                f"{format_number(result['premium'])}\n"
                f"📈 حداکثر سود: "
                f"{format_number(result['max_profit'])}\n"
                f"📉 حداکثر ضرر: نامحدود\n"
                f"⚖️ سر به سری پایین: "
                f"{format_number(result['lower_break_even'])}\n"
                f"⚖️ سر به سری بالا: "
                f"{format_number(result['upper_break_even'])}\n\n"
            )

        elif strategy == "covered_call":

            text += (
                f"🟢 سهم پایه: "
                f"{format_number(result['stock_price'])}\n\n"
                f"🔴 فروش Call: "
                f"{result['sell_symbol']}\n"
                f"🎯 قیمت اعمال: "
                f"{format_number(result['sell_strike'])}\n"
                f"💰 قیمت فروش: "
                f"{format_number(result['sell_price'])}\n\n"
            )

            text += (
                f"💰 درآمد حاصل از فروش Call: "
                f"{format_number(result['premium'])}\n"
                f"📈 حداکثر سود: "
                f"{format_number(result['max_profit'])}\n"
                f"📉 حداکثر ضرر: "
                f"{format_number(result['max_loss'])}\n"
                f"⚖️ نقطه سر به سری: "
                f"{format_number(result['break_even'])}\n"
                f"📊 بازده: "
                f"{result['roi']:.2f}%\n\n"
            )

        text += "━━━━━━━━━━━━━━\n\n"

    text += (
        f"🔎 حداقل بازده: {MIN_ROI}%\n"
        f"📊 تعداد فرصت‌ها: {len(results)}"
    )

    return text


def main():

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CallbackQueryHandler(
            strategy_handler
        )
    )

    print("Bot started...")

    application.run_polling()


if __name__ == "__main__":
    main()