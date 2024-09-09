#pip install python-telegram-bot --upgrade
import threading as th
from telegram import (InlineKeyboardButton,
                      InlineKeyboardMarkup,
                      Update,
                      ReplyKeyboardMarkup, KeyboardButton)
from telegram.ext import (Application,
                          CallbackQueryHandler,
                          CommandHandler,
                          ContextTypes,
                          MessageHandler,
                          filters)
from datetime import datetime as dt

import config as c
import db
import image_generators as ig
import keyboards as kb

current_neural_network = None
current_point_map = 1


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


def build_routes_menu(buttons,
                      n_cols,
                      header_buttons=None,
                      footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, [header_buttons])
    if footer_buttons:
        menu.append([footer_buttons])
    return menu


async def start(update: Update,
                context: ContextTypes.DEFAULT_TYPE) -> None:
    reply_keyboard = [[KeyboardButton(text='stats')]]
    await update.message.reply_text('Бот запущен',
                                    reply_markup=ReplyKeyboardMarkup(reply_keyboard,
                                                                     one_time_keyboard=True))

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

    point_map = db.get_point_map(current_point_map)
    available_routes = db.get_available_routes(current_point_map)

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
            db.add_statistic_generated(current_neural_network.model_id.split('/')[-1].split('-')[0],
                                       time_generated=end - start)

            await context.bot.send_photo(chat_id=query.message.chat_id,
                                         photo=open(generate_image_path, 'rb'))
        except Exception as e:
            print(e)
            await context.bot.send_message(chat_id=query.message.chat.id,
                                           text="Изображение не было сгенерировано")
            return

    keyboard_buttons = []
    print(available_routes)
    for route in available_routes:
        keyboard_buttons.append(InlineKeyboardButton(route.name,
                                                     callback_data=route.id))

    if keyboard_buttons is None:
        await context.bot.send_message(chat_id=query.message.chat.id,
                                       text="Ты в тупике!")
    else:
        reply_markup = InlineKeyboardMarkup(build_routes_menu(keyboard_buttons,
                                                              1))

        await context.bot.send_message(chat_id=query.message.chat.id,
                                       text="Куда пойдёшь?",
                                       reply_markup=reply_markup)


async def button(update: Update,
                 context: ContextTypes.DEFAULT_TYPE) -> None:
    global current_neural_network
    global current_point_map
    print("Обработка нажатия")

    await context.bot.get_updates(timeout=1000)
    query = update.callback_query
    if query is not None:
        await query.answer()

        if query.data == 'stable_diffusion':
            await context.bot.send_message(chat_id=query.message.chat.id,
                                           text="Загрузка нейросети StableDiffusion")
            start_time = dt.now()
            thread = ThreadWithResult(target=ig.StableDiffusion,
                                      args=())
            thread.start()
            thread.join()
            current_neural_network = thread.result
            end_time = dt.now()

            await context.bot.send_message(chat_id=query.message.chat.id,
                                           text="Время инициализации нейросети StableDiffusion: "
                                                + str(end_time - start_time))
            neural_network_name = current_neural_network.model_id.split('/')[-1].split('-')[0]

            db.add_statistic_loaded(neural_network_name,
                                    end_time - start_time)

            await neural_network_loaded(update, context)
        elif query.data == 'kandinsky':
            await context.bot.send_message(chat_id=query.message.chat.id,
                                           text="Загрузка нейросети Kandinsky")
            start_time = dt.now()
            thread = ThreadWithResult(target=ig.Kandinsky,
                                      args=())
            thread.start()
            thread.join()
            current_neural_network = thread.result
            end_time = dt.now()

            await context.bot.send_message(chat_id=query.message.chat.id,
                                           text="Время инициализации нейросети Kandinsky: "
                                                + str(end_time - start_time))
            neural_network_name = current_neural_network.model_id.split('/')[-1].split('-')[0]

            db.add_statistic_loaded(neural_network_name,
                                    end_time - start_time)

            await neural_network_loaded(update, context)
        elif query.data == 'stable_cascade':
            await context.bot.send_message(chat_id=query.message.chat.id,
                                           text="Загрузка нейросети StableCascade")
            start_time = dt.now()
            thread = ThreadWithResult(target=ig.StableCascade,
                                      args=())
            thread.start()
            thread.join()
            current_neural_network = thread.result
            end_time = dt.now()
            await context.bot.send_message(chat_id=query.message.chat.id,
                                           text="Время инициализации нейросети StableCascade: "
                                                + str(end_time - start_time))
            neural_network_name = current_neural_network.model_id.split('/')[-1].split('-')[0]

            db.add_statistic_loaded(neural_network_name,
                                    end_time - start_time)

            await neural_network_loaded(update, context)
        else:
            current_point_map = query.data
            print("Номер следующего маршрута:",
                  current_point_map)
            await show_routes(update, context)
    else:
        text = context.bot.editMessageText(text="stats")

        if text == 'stats':
            await get_statistics(update, context)


async def get_statistics(update: Update,
                         context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    statistics_data = db.get_statistic()
    await context.bot.send_message(chat_id=query.message.chat.id,
                                   text="Статистика: "
                                        + statistics_data)


def main():
    application = Application.builder().token(c.TG_API_TOKEN).build()

    application.add_handler(CommandHandler(start.__name__,
                                           start))
    application.add_handler(CallbackQueryHandler(button))

    application.add_handler(CommandHandler("stats",
                                           get_statistics))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
