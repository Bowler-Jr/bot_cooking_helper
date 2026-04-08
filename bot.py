TOKEN = "8551136972:AAH-x-U7tNRc-t9lPs0x_Msk8w0twaOttPQ"
import json, re, asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
RECIPES = [{"id":1,"name":"Курица с рисом","servings":4,"time":"40 мин","ingredients":[{"name":"куриное филе","amount":500,"unit":"г"},{"name":"рис","amount":200,"unit":"г"},{"name":"лук","amount":1,"unit":"шт"},{"name":"морковь","amount":1,"unit":"шт"},{"name":"масло","amount":2,"unit":"ст.л"},{"name":"соль","amount":1,"unit":"ч.л"},{"name":"перец","amount":0.5,"unit":"ч.л"}],"instructions":"1. Нарежь курицу, лук, морковь.\n2. Обжарь курицу 5 мин, добавь лук и морковь, жарь ещё 5 мин.\n3. Добавь рис, залей 400 мл воды, соль, перец.\n4. Вари под крышкой 20 мин."},{"id":2,"name":"Омлет с помидорами","servings":2,"time":"15 мин","ingredients":[{"name":"яйца","amount":4,"unit":"шт"},{"name":"молоко","amount":100,"unit":"мл"},{"name":"помидоры","amount":2,"unit":"шт"},{"name":"сыр","amount":50,"unit":"г"},{"name":"соль","amount":0.5,"unit":"ч.л"},{"name":"масло слив.","amount":20,"unit":"г"}],"instructions":"1. Взбей яйца с молоком и солью.\n2. Нарежь помидоры, натри сыр.\n3. Вылей на сковороду, сверху помидоры и сыр.\n4. Готовь под крышкой 5-7 мин."},{"id":3,"name":"Греческий салат","servings":3,"time":"10 мин","ingredients":[{"name":"огурцы","amount":2,"unit":"шт"},{"name":"помидоры","amount":2,"unit":"шт"},{"name":"перец болг.","amount":1,"unit":"шт"},{"name":"фета","amount":150,"unit":"г"},{"name":"маслины","amount":50,"unit":"г"},{"name":"масло оливк.","amount":3,"unit":"ст.л"},{"name":"орегано","amount":0.5,"unit":"ч.л"}],"instructions":"1. Нарежь всё крупно.\n2. Добавь маслины и фету.\n3. Заправь маслом и орегано."},{"id":4,"name":"Паста Карбонара","servings":2,"time":"25 мин","ingredients":[{"name":"спагетти","amount":200,"unit":"г"},{"name":"бекон","amount":100,"unit":"г"},{"name":"желтки","amount":2,"unit":"шт"},{"name":"пармезан","amount":50,"unit":"г"},{"name":"сливки 20%","amount":50,"unit":"мл"},{"name":"чеснок","amount":1,"unit":"зуб"},{"name":"соль, перец","amount":0,"unit":"по вкусу"}],"instructions":"1. Свари спагетти.\n2. Обжарь бекон с чесноком.\n3. Смешай желтки, пармезан, сливки, соль, перец.\n4. Смешай с горячими спагетти и беконом."}]
MAIN_MENU = [["Поиск по названию", "Поиск по продуктам"], ["Показать все", "Конвертер порций"]]
WAIT_NAME, WAIT_ING, WAIT_CONV_NAME, WAIT_CONV_PORT, WAIT_SELECT = range(5)
async def start(upd, ctx):
    await upd.message.reply_text("Привет! Выбери действие:", reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True))
    return ConversationHandler.END
async def menu(upd, ctx):
    t = upd.message.text
    if t == "Поиск по названию":
        await upd.message.reply_text("Введи название блюда:")
        return WAIT_NAME
    if t == "Поиск по продуктам":
        await upd.message.reply_text("Введи продукты через запятую:")
        return WAIT_ING
    if t == "Показать все":
        ctx.user_data["search_results"] = RECIPES
        msg = "Все рецепты:\n" + "\n".join(f"{i+1}. {r['name']}" for i,r in enumerate(RECIPES))
        await upd.message.reply_text(msg + "\nВведи номер:")
        return WAIT_SELECT
    if t == "Конвертер порций":
        await upd.message.reply_text("Введи название рецепта:")
        return WAIT_CONV_NAME
    await upd.message.reply_text("Используй кнопки")
    return ConversationHandler.END
async def search_name(upd, ctx):
    q = upd.message.text.lower()
    found = [r for r in RECIPES if q in r["name"].lower()]
    if not found:
        await upd.message.reply_text("Не найдено")
        return ConversationHandler.END
    ctx.user_data["search_results"] = found
    msg = "Найдено:\n" + "\n".join(f"{i+1}. {r['name']}" for i,r in enumerate(found))
    await upd.message.reply_text(msg + "\nВведи номер:")
    return WAIT_SELECT
async def search_ing(upd, ctx):
    req = [i.strip().lower() for i in re.split(r'[,，]', upd.message.text.lower()) if i.strip()]
    suitable = [r for r in RECIPES if all(ing["name"].lower() in [x["name"].lower() for x in r["ingredients"]] for ing in req)]
    if not suitable:
        await upd.message.reply_text("Нет рецептов с такими продуктами")
        return ConversationHandler.END
    ctx.user_data["search_results"] = suitable
    msg = "Найдено:\n" + "\n".join(f"{i+1}. {r['name']}" for i,r in enumerate(suitable))
    await upd.message.reply_text(msg + "\nВведи номер:")
    return WAIT_SELECT
async def select(upd, ctx):
    try:
        idx = int(upd.message.text) - 1
        recipe = ctx.user_data["search_results"][idx]
    except:
        await upd.message.reply_text("Введи номер правильно")
        return WAIT_SELECT
    ing = [f"{i['amount']} {i['unit']} {i['name']}" for i in recipe["ingredients"]]
    text = f"*{recipe['name']}* ({recipe['servings']} порц)\n*Время:* {recipe['time']}\n*Ингр:*\n" + "\n".join(f"• {x}" for x in ing) + f"\n*Пригот:*\n{recipe['instructions']}"
    await upd.message.reply_text(text, parse_mode="Markdown")
    await upd.message.reply_text("Меню:", reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True))
    ctx.user_data.pop("search_results", None)
    return ConversationHandler.END
async def conv_name(upd, ctx):
    q = upd.message.text.lower()
    found = [r for r in RECIPES if q in r["name"].lower()]
    if not found:
        await upd.message.reply_text("Не найдено")
        return ConversationHandler.END
    if len(found) > 1:
        ctx.user_data["convert_candidates"] = found
        msg = "Уточни:\n" + "\n".join(f"{i+1}. {r['name']}" for i,r in enumerate(found))
        await upd.message.reply_text(msg)
        return WAIT_CONV_NAME
    ctx.user_data["convert_recipe"] = found[0]
    await upd.message.reply_text(f"{found[0]['name']}, исходно {found[0]['servings']} порц. Введи новое число порций:")
    return WAIT_CONV_PORT
async def conv_port(upd, ctx):
    try:
        new = float(upd.message.text)
    except:
        await upd.message.reply_text("Введи число")
        return WAIT_CONV_PORT
    recipe = ctx.user_data["convert_recipe"]
    factor = new / recipe["servings"]
    new_ing = []
    for i in recipe["ingredients"]:
        amt = i["amount"] * factor
        amt = int(amt) if amt.is_integer() else round(amt,2)
        new_ing.append(f"{amt} {i['unit']} {i['name']}")
    text = f"*{recipe['name']}* (на {new} порц)\n*Время:* {recipe['time']}\n*Ингр:*\n" + "\n".join(f"• {x}" for x in new_ing) + f"\n*Пригот:*\n{recipe['instructions']}"
    await upd.message.reply_text(text, parse_mode="Markdown")
    await upd.message.reply_text("Меню:", reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True))
    return ConversationHandler.END
async def cancel(upd, ctx):
    await upd.message.reply_text("Отменено. /start")
    return ConversationHandler.END
def main():
    app = Application.builder().token(TOKEN).build()
    conv = ConversationHandler(entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, menu)], states={WAIT_NAME:[MessageHandler(filters.TEXT, search_name)], WAIT_ING:[MessageHandler(filters.TEXT, search_ing)], WAIT_SELECT:[MessageHandler(filters.TEXT, select)], WAIT_CONV_NAME:[MessageHandler(filters.TEXT, conv_name)], WAIT_CONV_PORT:[MessageHandler(filters.TEXT, conv_port)]}, fallbacks=[CommandHandler("cancel",cancel), CommandHandler("start",start)])
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    print("Бот запущен. Не забудь включить VPN!")
    app.run_polling()
if __name__ == "__main__": main()
