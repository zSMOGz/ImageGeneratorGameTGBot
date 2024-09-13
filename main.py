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

current_neural_network = None
current_point_map = 1

bot = Bot(token=c.TG_API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


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


def get_datetime(date,
                 time):
    return db.dt.datetime.strptime("{} {}".format(date, time),
                                   "%Y-%m-%d %H:%M:%S")


def build_routes_menu(buttons,
                      n_cols,
                      header_buttons=None,
                      footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0,
                                                 len(buttons),
                                                 n_cols)]
    if header_buttons:
        menu.insert(0,
                    [header_buttons])
    if footer_buttons:
        menu.append([footer_buttons])
    return menu


async def get_neural_network_name(neural_network):
    if neural_network is None:
        return None
    else:
        return neural_network.model_id.split('/')[-1].split('-')[0]


async def load_neural_network(neural_network_name: str,
                              call: CallbackQuery):
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
    td = end_time - start_time

    await bot.send_message(chat_id=call.message.chat.id,
                           text=tx.NEURO_INIT_TIME
                           + str(td))
    db.add_statistic_loaded(neural_network_name,
                            get_datetime(db.dt.date.today(),
                                         str(td).split(".")[0]))


async def call_to_message(call: CallbackQuery,
                          text: str):
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
    await call.answer(tx.BOT_START,
                      reply_markup=kb.start_kb)

    await call.answer(text=tx.NEURO_SELECT,
                      reply_markup=kb.neural_network_kb)


async def show_routes_handler(message_or_call):
    point_map = db.get_point_map(current_point_map)
    available_routes = db.get_available_routes(current_point_map)

    if point_map is None:
        await message_or_call.answer(tx.ROUTES_UNAVAILABLE)
        return

    if isinstance(message_or_call, Message):
        await bot.send_message(chat_id=message_or_call.chat.id,
                               text=point_map.name)
        await bot.send_message(chat_id=message_or_call.chat.id,
                               text=point_map.description)
    else:
        print("Не сообещение")
        await message_or_call.answer(point_map.name)
        await message_or_call.answer(point_map.description)

    if point_map.ai_description is None:
        if isinstance(message_or_call, Message):
            await bot.send_message(chat_id=message_or_call.chat.id,
                                   text=tx.ROUTES_WITHOUT_DESCRIPTION)
        else:
            await bot.send_message(chat_id=message_or_call.message.chat.id,
                                   text=tx.ROUTES_WITHOUT_DESCRIPTION)
        # await message_or_call.answer(tx.ROUTES_WITHOUT_DESCRIPTION)
    else:
        try:
            start_time = db.dt.datetime.now()
            thread = ThreadWithResult(target=current_neural_network.generate_image,
                                      args=(point_map.ai_description,))
            thread.start()

            i = 0
            text = (tx.GENERATION_IN_PROCESS + f"{i}" + tx.TIME_UNITS)
            if isinstance(message_or_call, Message):
                load_message = await bot.send_message(chat_id=message_or_call.chat.id,
                                                      text=text)
            else:
                load_message = await bot.send_message(chat_id=message_or_call.message.chat.id,
                                                      text=text)
            while thread.is_alive():
                i += 1
                await asyncio.sleep(1)
                text = (tx.GENERATION_IN_PROCESS + f"{i}" + tx.TIME_UNITS)
                await load_message.edit_text(text=text)

            await load_message.delete()
            generate_image_path = thread.result

            end_time = db.dt.datetime.now()

            td = end_time - start_time
            text = (tx.GENERATION_TIME + str(td) + tx.TIME_UNITS)
            if isinstance(message_or_call, Message):
                await bot.send_message(chat_id=message_or_call.chat.id,
                                       text=text)
            else:
                await message_or_call.answer(text)

            name = await get_neural_network_name(current_neural_network)
            db.add_statistic_generated(name,
                                       get_datetime(db.dt.date.today(),
                                                    str(td).split(".")[0]))

            if isinstance(message_or_call, Message):
                await bot.send_photo(chat_id=message_or_call.chat.id,
                                     photo=FSInputFile(generate_image_path))
            else:
                await message_or_call.answer_photo(photo=FSInputFile(generate_image_path))
        except Exception as e:
            print(e)
            if isinstance(message_or_call, Message):
                await bot.send_message(chat_id=message_or_call.chat.id,
                                       text=tx.GENERATION_ERROR)
            else:
                await message_or_call.answer(tx.GENERATION_ERROR)
            return

    keyboard_buttons = []

    for route in available_routes:
        keyboard_buttons.append(InlineKeyboardButton(text=route.name,
                                                     callback_data=str(route.id)))

    if keyboard_buttons is None:
        if isinstance(message_or_call, Message):
            await bot.send_message(chat_id=message_or_call.chat.id,
                                   text=tx.ROUTES_UNAVAILABLE)
        else:
            await message_or_call.answer(tx.ROUTES_UNAVAILABLE)
    else:
        keyboard_markup = InlineKeyboardMarkup(inline_keyboard=build_routes_menu(keyboard_buttons,
                                                                                 1))
        if isinstance(message_or_call, Message):
            await bot.send_message(chat_id=message_or_call.chat.id,
                                   text=tx.ROUTES_ANSWER,
                                   reply_markup=keyboard_markup)
        else:
            await message_or_call.answer(text=tx.ROUTES_ANSWER,
                                         reply_markup=keyboard_markup)


@dp.message(Command(tx.COMMAND_SHOW_ROUTES))
async def show_routes(message: Message):
    await show_routes_handler(message)


@dp.callback_query(F.data == kb.BUTTON_SHOW_ROUTES_CALL)
async def show_routes(call: CallbackQuery):
    await show_routes_handler(call)


@dp.callback_query(F.data == kb.BUTTON_STABLE_DIFFUSION_CALL)
async def stable_diffusion(call: CallbackQuery):
    await load_neural_network(kb.BUTTON_STABLE_DIFFUSION_CALL,
                              call)

    message = await call_to_message(call,
                                    tx.COMMAND_SHOW_ROUTES)
    await show_routes(message)


@dp.callback_query(F.data == kb.BUTTON_KANDINSKY_CALL)
async def kandinsky(call: CallbackQuery):
    await load_neural_network(kb.BUTTON_KANDINSKY_CALL,
                              call)

    message = await call_to_message(call,
                                    tx.COMMAND_SHOW_ROUTES)
    await show_routes(message)


@dp.callback_query(F.data == kb.BUTTON_STABLE_CASCADE_CALL)
async def stable_cascade(call: CallbackQuery):
    await load_neural_network(kb.BUTTON_STABLE_CASCADE_CALL,
                              call)
    message = await call_to_message(call,
                                    tx.COMMAND_SHOW_ROUTES)
    await show_routes(message)


@dp.callback_query()
async def next_route(call: CallbackQuery):
    global current_point_map
    current_point_map = call.data
    print(current_point_map)
    message = await call_to_message(call,
                                    tx.COMMAND_SHOW_ROUTES)

    await show_routes_handler(message)


@dp.callback_query(F.data == tx.COMMAND_STATISTICS)
async def get_statistics(message: Message):
    statistics_data = db.get_statistic()
    await message.answer(tx.COMMAND_STATISTICS_TEXT
                         + statistics_data)


async def main():
    await bot.get_updates(timeout=100)
    await dp.start_polling(bot,
                           skip_updates=True)


if __name__ == tx.MAIN_MODULE_NAME:
    asyncio.run(main())
