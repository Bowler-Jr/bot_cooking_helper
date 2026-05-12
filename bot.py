"""
Telegram-бот "Кулинарный помощник"
Разработчик: Молоствов Дмитрий, 10 класс
"""

TOKEN = "8551136972:AAH-x-U7tNRc-t9lPs0x_Msk8w0twaOttPQ"

# ========== ИМПОРТЫ ==========
import json
import re
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes
)


# ========== ЗАГРУЗКА РЕЦЕПТОВ ИЗ JSON ==========
def load_recipes():
    with open("recipes.json", "r", encoding="utf-8") as file:
        return json.load(file)


RECIPES = load_recipes()


# ========== КЛАВИАТУРА МЕНЮ ==========
MAIN_MENU = [
    ["Поиск по названию", "Поиск по продуктам"],
    ["Показать все", "Конвертер порций"]
]


# ========== СОСТОЯНИЯ ДЛЯ CONVERSATION HANDLER ==========
WAIT_NAME, WAIT_ING, WAIT_CONV_NAME, WAIT_CONV_PORT, WAIT_SELECT = range(5)


# ========== ОБРАБОТЧИК КОМАНДЫ /start ==========
async def start(upd: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await upd.message.reply_text(
        "Привет! Я кулинарный помощник. Выбери действие:",
        reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    )
    return ConversationHandler.END


# ========== ОБРАБОТЧИК ГЛАВНОГО МЕНЮ ==========
async def menu(upd: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = upd.message.text

    if text == "Поиск по названию":
        await upd.message.reply_text("Введи название блюда:")
        return WAIT_NAME

    if text == "Поиск по продуктам":
        await upd.message.reply_text("Введи продукты через запятую:")
        return WAIT_ING

    if text == "Показать все":
        ctx.user_data["search_results"] = RECIPES
        msg = "Все рецепты:\n" + "\n".join(
            f"{i+1}. {r['name']}" for i, r in enumerate(RECIPES)
        )
        await upd.message.reply_text(msg + "\nВведи номер:")
        return WAIT_SELECT

    if text == "Конвертер порций":
        await upd.message.reply_text("Введи название рецепта:")
        return WAIT_CONV_NAME

    await upd.message.reply_text("Используй кнопки меню")
    return ConversationHandler.END


# ========== ПОИСК ПО НАЗВАНИЮ ==========
async def search_name(upd: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = upd.message.text.lower()
    found = [r for r in RECIPES if query in r["name"].lower()]

    if not found:
        await upd.message.reply_text("Рецепт не найден")
        return ConversationHandler.END

    ctx.user_data["search_results"] = found
    msg = "Найдено:\n" + "\n".join(f"{i+1}. {r['name']}" for i, r in enumerate(found))
    await upd.message.reply_text(msg + "\nВведи номер рецепта:")
    return WAIT_SELECT


# ========== ПОИСК ПО ПРОДУКТАМ ==========
async def search_ing(upd: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ingredients_req = [
        i.strip().lower()
        for i in re.split(r'[,，]', upd.message.text.lower())
        if i.strip()
    ]

    suitable = []
    for recipe in RECIPES:
        recipe_ing = [ing["name"].lower() for ing in recipe["ingredients"]]
        if all(req_ing in recipe_ing for req_ing in ingredients_req):
            suitable.append(recipe)

    if not suitable:
        await upd.message.reply_text("Нет рецептов с такими продуктами")
        return ConversationHandler.END

    ctx.user_data["search_results"] = suitable
    msg = "Найдено:\n" + "\n".join(f"{i+1}. {r['name']}" for i, r in enumerate(suitable))
    await upd.message.reply_text(msg + "\nВведи номер рецепта:")
    return WAIT_SELECT


# ========== ВЫВОД ВЫБРАННОГО РЕЦЕПТА ==========
async def select(upd: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        idx = int(upd.message.text) - 1
        recipe = ctx.user_data["search_results"][idx]
    except (IndexError, ValueError):
        await upd.message.reply_text("Введи корректный номер")
        return WAIT_SELECT

    ingredients_text = [
        f"{ing['amount']} {ing['unit']} {ing['name']}"
        for ing in recipe["ingredients"]
    ]

    response = (
        f"*{recipe['name']}* ({recipe['servings']} порц)\n"
        f"*Время:* {recipe['time']}\n"
        f"*Ингредиенты:*\n" + "\n".join(f"• {x}" for x in ingredients_text) +
        f"\n*Приготовление:*\n{recipe['instructions']}"
    )

    await upd.message.reply_text(response, parse_mode="Markdown")
    await upd.message.reply_text(
        "Меню:",
        reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    )
    ctx.user_data.pop("search_results", None)
    return ConversationHandler.END


# ========== КОНВЕРТЕР: ВВОД НАЗВАНИЯ ==========
async def conv_name(upd: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = upd.message.text.lower()
    found = [r for r in RECIPES if query in r["name"].lower()]

    if not found:
        await upd.message.reply_text("Рецепт не найден")
        return ConversationHandler.END

    if len(found) > 1:
        ctx.user_data["convert_candidates"] = found
        msg = "Уточни:\n" + "\n".join(f"{i+1}. {r['name']}" for i, r in enumerate(found))
        await upd.message.reply_text(msg)
        return WAIT_CONV_NAME

    ctx.user_data["convert_recipe"] = found[0]
    await upd.message.reply_text(
        f"{found[0]['name']}, исходно {found[0]['servings']} порц. "
        f"Введи новое количество порций:"
    )
    return WAIT_CONV_PORT


# ========== КОНВЕРТЕР: ВВОД ПОРЦИЙ ==========
async def conv_port(upd: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        new_servings = float(upd.message.text)
    except ValueError:
        await upd.message.reply_text("Введи число")
        return WAIT_CONV_PORT

    recipe = ctx.user_data["convert_recipe"]
    factor = new_servings / recipe["servings"]

    new_ingredients = []
    for ing in recipe["ingredients"]:
        amount = ing["amount"] * factor
        amount = int(amount) if amount.is_integer() else round(amount, 2)
        new_ingredients.append(f"{amount} {ing['unit']} {ing['name']}")

    response = (
        f"*{recipe['name']}* (на {new_servings} порц)\n"
        f"*Время:* {recipe['time']}\n"
        f"*Ингредиенты:*\n" + "\n".join(f"• {x}" for x in new_ingredients) +
        f"\n*Приготовление:*\n{recipe['instructions']}"
    )

    await upd.message.reply_text(response, parse_mode="Markdown")
    await upd.message.reply_text(
        "Меню:",
        reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    )
    return ConversationHandler.END


# ========== ОТМЕНА ==========
async def cancel(upd: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await upd.message.reply_text("Отменено. Напиши /start для начала работы")
    return ConversationHandler.END


# ========== ЗАПУСК БОТА ==========
def main():
    app = Application.builder().token(TOKEN).build()

    conversation_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, menu)],
        states={
            WAIT_NAME: [MessageHandler(filters.TEXT, search_name)],
            WAIT_ING: [MessageHandler(filters.TEXT, search_ing)],
            WAIT_SELECT: [MessageHandler(filters.TEXT, select)],
            WAIT_CONV_NAME: [MessageHandler(filters.TEXT, conv_name)],
            WAIT_CONV_PORT: [MessageHandler(filters.TEXT, conv_port)],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conversation_handler)

    print("Бот запущен!")
    app.run_polling()


if __name__ == "__main__":
    main()
