# pip install aiogram
import threading as th
import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

import config as c
import db
import image_generators as ig
import keyboards as kb
import texts as tx
import statistic as st

current_neural_network = None
current_point_map = 1

bot = Bot(token=c.TG_API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


class ThreadWithResult(th.Thread):
    """
    Класс для создания потоков, возвращающих результат выполнения функции
    """
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
                      count_columns,
                      header_buttons=None,
                      footer_buttons=None):
    """
    Функция создания меню, выравнивающая кнопки в зависимости от указанного количества столбцов
    :param buttons: Массив кнопок
    :param count_columns: Количество столбцов
    :param header_buttons: Кнопки заголовка
    :param footer_buttons: Кнопки под заголовком
    :return: Выравненные кнопки
    """
    menu = [buttons[i:i + count_columns] for i in range(0,
                                                        len(buttons),
                                                        count_columns)]
    if header_buttons:
        menu.insert(0,
                    [header_buttons])
    if footer_buttons:
        menu.append([footer_buttons])
    return menu


async def get_neural_network_name(neural_network):
    """
    Функция возвращает имя нейронной сети из базы данных
    :param neural_network: Нейронная сеть
    :return: Имя нейронной сети
    """
    _slash = '/'
    _minus = '-'
    _underscore = '_'
    _kandinsky = 'kandinsky'

    if neural_network is None:
        return None
    else:
        if neural_network.model_id.find(_kandinsky) >= 0:
            return neural_network.model_id.split(_slash)[-1].split(_minus)[0]
        else:
            parts_name = neural_network.model_id.split(_slash)[-1].split(_minus)
            return parts_name[0] + _underscore + parts_name[1]


async def load_neural_network(neural_network_name: str,
                              call: CallbackQuery):
    """
    Функция загрузки нейронной сети в память компьютера
    :param neural_network_name: Название нейронной сети
    :param call: Запрос
    :return: Ошибка при загрузке
    """
    global current_neural_network
    global current_point_map

    await call.answer(text=tx.NEURO_LOADING.format(neural_network_name))

    start_time = db.dt.datetime.now()
    if neural_network_name == kb.BUTTON_STABLE_DIFFUSION_CALL:
        thread = ThreadWithResult(target=ig.StableDiffusion,
                                  args=())
    elif neural_network_name == kb.BUTTON_KANDINSKY_CALL:
        thread = ThreadWithResult(target=ig.Kandinsky,
                                  args=())
    elif neural_network_name == kb.BUTTON_STABLE_CASCADE_CALL:
        thread = ThreadWithResult(target=ig.StableCascade,
                                  args=())
    else:
        return await call.answer(tx.NEURO_NOT_FOUND)

    thread.start()

    i = 0
    text = (tx.NEURO_IN_PROCESS + f"{i}" + tx.TIME_UNITS)
    load_message = await bot.send_message(chat_id=call.message.chat.id,
                                          text=text)
    while thread.is_alive():
        i += 1
        await asyncio.sleep(1)
        text = (tx.NEURO_LOADING_TIME + f"{i}" + tx.TIME_UNITS)
        await load_message.edit_text(text=text)

    await load_message.delete()
    current_neural_network = thread.result
    end_time = db.dt.datetime.now()
    time_load_in_seconds = (end_time - start_time).total_seconds()

    if st.SHOW_STATISTICS:
        await bot.send_message(chat_id=call.message.chat.id,
                               text=tx.NEURO_INIT_TIME
                               + str(time_load_in_seconds))
    if st.COLLECT_STATISTIC:
        db.add_statistic_loaded(neural_network_name,
                                time_load_in_seconds)


async def call_to_message(call: CallbackQuery,
                          text: str):
    """
    Функция преобразования сообщения из запроса
    :param call: Запрос
    :param text: Текст сообщения
    :return: Сообщение
    """
    message = Message(
        message_id=call.message.message_id,
        from_user=call.from_user,
        chat=call.message.chat,
        date=call.message.date,
        text=text
    )
    return message


@dp.message(Command(tx.COMMAND_START))
async def start(call: CallbackQuery):
    """"
    Функция запуска бота, предоставляет выбор нейронной сети и добавляет кнопку статистики
    """
    await call.answer(tx.BOT_START,
                      reply_markup=kb.stats_kb)

    await call.answer(text=tx.NEURO_SELECT,
                      reply_markup=kb.neural_network_kb)



@dp.message(Command(tx.COMMAND_SHOW_ROUTES))
async def show_routes(message: Message):
    """
    Функция отображения маршрутов
    :param message: Сообщение
    """
    point_map = db.get_point_map(current_point_map)
    available_routes = db.get_available_routes(current_point_map)

    if point_map is None:
        await message.answer(tx.ROUTES_UNAVAILABLE)
        return

    await bot.send_message(chat_id=message.chat.id,
                           text=point_map.name)
    await bot.send_message(chat_id=message.chat.id,
                           text=point_map.description)

    if point_map.ai_description is None:
        await bot.send_message(chat_id=message.chat.id,
                               text=tx.ROUTES_WITHOUT_DESCRIPTION)
    else:
        try:
            start_time = db.dt.datetime.now()
            thread = ThreadWithResult(target=current_neural_network.generate_image,
                                      args=(point_map.ai_description,))
            thread.start()

            i = 0
            text = (tx.GENERATION_IN_PROCESS + f"{i}" + tx.TIME_UNITS)

            load_message = await bot.send_message(chat_id=message.chat.id,
                                                  text=text)
            while thread.is_alive():
                i += 1
                await asyncio.sleep(1)
                text = (tx.GENERATION_IN_PROCESS + f"{i}" + tx.TIME_UNITS)
                await load_message.edit_text(text=text)

            await load_message.delete()
            generate_image_path = thread.result

            end_time = db.dt.datetime.now()

            time_generate_in_seconds = (end_time - start_time).total_seconds()

            text = (tx.GENERATION_TIME + str(time_generate_in_seconds) + tx.TIME_UNITS)
            if st.SHOW_STATISTICS:
                await bot.send_message(chat_id=message.chat.id,
                                       text=text)

            if st.COLLECT_STATISTIC:
                name = await get_neural_network_name(current_neural_network)

                db.add_statistic_generated(name,
                                           time_generate_in_seconds)

            await bot.send_photo(chat_id=message.chat.id,
                                 photo=FSInputFile(generate_image_path))
        except Exception as e:
            print(e)
            await bot.send_message(chat_id=message.chat.id,
                                   text=tx.GENERATION_ERROR)
            return

    keyboard_buttons = []

    for route in available_routes:
        keyboard_buttons.append(InlineKeyboardButton(text=route.name,
                                                     callback_data=str(route.id)))

    if keyboard_buttons is None:
        await bot.send_message(chat_id=message.chat.id,
                               text=tx.ROUTES_UNAVAILABLE)
    else:
        keyboard_markup = InlineKeyboardMarkup(inline_keyboard=build_routes_menu(keyboard_buttons,
                                                                                 1))
        await bot.send_message(chat_id=message.chat.id,
                               text=tx.ROUTES_ANSWER,
                               reply_markup=keyboard_markup)


@dp.callback_query(F.data == kb.BUTTON_STABLE_DIFFUSION_CALL)
async def stable_diffusion(call: CallbackQuery):
    """
    Функция загрузки нейронной сети Stable Diffusion
    :param call: Запрос
    """
    await load_neural_network(kb.BUTTON_STABLE_DIFFUSION_CALL,
                              call)

    message = await call_to_message(call,
                                    tx.COMMAND_SHOW_ROUTES)
    await show_routes(message)


@dp.callback_query(F.data == kb.BUTTON_KANDINSKY_CALL)
async def kandinsky(call: CallbackQuery):
    """
    Функция загрузки нейронной сети Kandinsky
    :param call: Запрос
    """
    await load_neural_network(kb.BUTTON_KANDINSKY_CALL,
                              call)

    message = await call_to_message(call,
                                    tx.COMMAND_SHOW_ROUTES)
    await show_routes(message)


@dp.callback_query(F.data == kb.BUTTON_STABLE_CASCADE_CALL)
async def stable_cascade(call: CallbackQuery):
    """
    Функция загрузки нейронной сети Stable Cascade
    :param call: Запрос
    """
    await load_neural_network(kb.BUTTON_STABLE_CASCADE_CALL,
                              call)
    message = await call_to_message(call,
                                    tx.COMMAND_SHOW_ROUTES)
    await show_routes(message)


@dp.callback_query()
async def next_route(call: CallbackQuery):
    """
    Функция перехода к следующему маршруту
    :param call: Запрос
    """
    global current_point_map
    current_point_map = call.data

    message = await call_to_message(call,
                                    tx.COMMAND_SHOW_ROUTES)

    await show_routes(message)


@dp.message(lambda message: message.text == kb.BUTTON_STATS)
async def get_statistics(message: Message):
    """
    Статистика загрузки нейронных сетей, и времени создания изображений
    :param message: Сообщение
    """
    statistics_data = db.get_statistic()
    text = ""

    await message.answer(tx.COMMAND_STATISTICS_TEXT)
    for stat in statistics_data:
        text = stat.neural_network_name + ": \n"
        if stat.time_generated is not None:
            text += st.AVG_TIME_GENERATED_NAME + str(stat.time_generated)
            text += "\n"
        if stat.time_loaded is not None:
            text += st.AVG_TIME_LOADED_NAME + str(stat.time_loaded)
            text += "\n"
        text += "\n"
        await message.answer(text)
        text = ""
    # Разделение статистики по нейронным сетям
    statistics_detailed_data = db.get_statistic_detailed()

    lists_by_neural_networks = await st.get_lists_by_neural_networks(statistics_detailed_data)

    (lists_time_generated,
     lists_time_generated_indexes,
     lists_time_loaded,
     lists_time_loaded_indexes) = await st.get_time_generated_list_and_indexes(lists_by_neural_networks)

    index = 0
    for list in lists_by_neural_networks:
        list_time_generated = lists_time_generated[index]
        list_time_generated_indexes = lists_time_generated_indexes[index]
        list_time_loaded = lists_time_loaded[index]
        list_time_loaded_indexes = lists_time_loaded_indexes[index]

        (neural_network_name,
         time_loaded,
         time_generated) = list[index]

        graph_file_path = await st.create_graph(list_time_generated_indexes,
                                                list_time_generated,
                                                st.TIME_GENERATED_NAME + " " + neural_network_name,
                                                st.INDEX_NAME,
                                                st.TIME_GENERATED_NAME,
                                                list_time_generated_indexes,
                                                list_time_generated)
        await bot.send_photo(chat_id=message.chat.id,
                             photo=FSInputFile(graph_file_path))

        graph_file_path = await st.create_graph(list_time_loaded_indexes,
                                                list_time_loaded,
                                                st.TIME_LOADED_NAME + " " + neural_network_name,
                                                st.INDEX_NAME,
                                                st.TIME_LOADED_NAME,
                                                list_time_loaded_indexes,
                                                list_time_loaded)

        await bot.send_photo(chat_id=message.chat.id,
                             photo=FSInputFile(graph_file_path))

        index += 1


async def main():
    """
    Запуск бота
    """
    await bot.get_updates(timeout=100)
    await dp.start_polling(bot,
                           skip_updates=True)


if __name__ == tx.MAIN_MODULE_NAME:
    asyncio.run(main())
