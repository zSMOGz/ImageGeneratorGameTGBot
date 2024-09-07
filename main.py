#pip install python-telegram-bot --upgrade
import threading as th
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (Application,
                          CallbackQueryHandler,
                          CommandHandler,
                          ContextTypes,
                          )
from datetime import datetime as dt

import config as c
import db
import image_generators as ig
import keyboards as kb

current_neural_network = None


class ThreadWithResult(th.Thread):
    def __init__(self,
                 group=None,
                 target=None,
                 name=None,
                 args=(),
                 kwargs={},
                 *,
                 daemon=None):
        def function():
            self.result = target(*args,
                                 **kwargs)
        super().__init__(group=group,
                         target=function,
                         name=name,
                         daemon=daemon)


async def start(update: Update,
                context: ContextTypes.DEFAULT_TYPE) -> None:
    reply_markup = InlineKeyboardMarkup(kb.keyboard_neural_network)

    await update.message.reply_text(text="Выберете нейросеть для генерации изображений:",
                                    reply_markup=reply_markup)


async def neural_network_loaded(update: Update,
                                context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    await show_routes(update, context)


async def show_routes(update: Update,
                      context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    point_map = db.get_point_map(1)
    available_routes = db.get_available_routes(1)

    if point_map is None:
        await context.bot.send_message(chat_id=query.message.chat.id,
                                       text="Движение недоступно")
        return

    await context.bot.send_message(chat_id=query.message.chat.id,
                                   text=point_map.name)
    await context.bot.send_message(chat_id=query.message.chat.id,
                                   text=point_map.description)

    if point_map.ai_description is None:
        await context.bot.send_message(chat_id=query.message.chat.id,
                                       text="Отсутствует текстовое описание изображения")
    else:
        try:
            start = dt.now()
            generate_image_path = current_neural_network.generate_image(point_map.ai_description)
            end = dt.now()
            await context.bot.send_message(chat_id=query.message.chat.id,
                                           text="Время генерации изображения: "
                                                + str(end - start))

            await context.bot.send_photo(chat_id=query.message.chat_id,
                                         photo=open(generate_image_path, 'rb'))
        except Exception as e:
            print(e)
            await context.bot.send_message(chat_id=query.message.chat.id,
                                           text="Изображение не было сгенерировано")
            return

    keyboard_buttons = []

    for route in available_routes:
        print(route)
        keyboard_buttons.append(InlineKeyboardButton(route.name,
                                                     callback_data=route.id))

    if keyboard_buttons is None:
        await context.bot.send_message(chat_id=query.message.chat.id,
                                       text="Ты в тупике!")
    else:
        keyboard = [
            keyboard_buttons
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(chat_id=query.message.chat.id,
                                       text="Куда пойдёшь?",
                                       reply_markup=reply_markup)


async def button(update: Update,
                 context: ContextTypes.DEFAULT_TYPE) -> None:
    global current_neural_network

    await context.bot.get_updates(timeout=1000)
    query = update.callback_query
    await query.answer()

    if query.data == 'stable_diffusion':
        start = dt.now()
        thread = ThreadWithResult(target=ig.StableDiffusion,
                                  args=())
        thread.start()
        thread.join()
        current_neural_network = thread.result
        end = dt.now()

        await context.bot.send_message(chat_id=query.message.chat.id,
                                       text="Время инициализации нейросети StableDiffusion: "
                                            + str(end - start))

        await neural_network_loaded(update, context)
    elif query.data == 'kandinsky':
        start = dt.now()
        thread = ThreadWithResult(target=ig.Kandinsky,
                                  args=())
        thread.start()
        thread.join()
        current_neural_network = thread.result
        end = dt.now()

        await context.bot.send_message(chat_id=query.message.chat.id,
                                       text="Время инициализации нейросети Kandinsky: "
                                            + str(end - start))

        await neural_network_loaded(update, context)
    elif query.data == 'stable_cascade':
        start = dt.now()
        thread = ThreadWithResult(target=ig.StableCascade,
                                  args=())
        thread.start()
        thread.join()
        current_neural_network = thread.result
        end = dt.now()
        await context.bot.send_message(chat_id=query.message.chat.id,
                                       text="Время инициализации нейросети StableCascade: "
                                            + str(end - start))

        await neural_network_loaded(update, context)
    elif query.data == show_routes.__name__:
        await show_routes(update, context)


def main():
    application = Application.builder().token(c.TG_API_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
