from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import KeyboardButton

BUTTON_STATS = "Статистка"
BUTTON_STATS_CALL = "stats"
BUTTON_SHOW_ROUTES_CALL = "show_routes"

BUTTON_STABLE_DIFFUSION = "Stable Diffusion"
BUTTON_STABLE_DIFFUSION_CALL = "stable_diffusion"
BUTTON_KANDINSKY = "Kandinsky"
BUTTON_KANDINSKY_CALL = "kandinsky"
BUTTON_STABLE_CASCADE = "Stable Cascade"
BUTTON_STABLE_CASCADE_CALL = "stable_cascade"

neural_network_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=BUTTON_STABLE_DIFFUSION,
                              callback_data=BUTTON_STABLE_DIFFUSION_CALL)],
        [InlineKeyboardButton(text=BUTTON_KANDINSKY,
                              callback_data=BUTTON_KANDINSKY_CALL)],
        [InlineKeyboardButton(text=BUTTON_STABLE_CASCADE,
                              callback_data=BUTTON_STABLE_CASCADE_CALL)],
    ], resize_keyboard=True
)

stats_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=BUTTON_STATS)
        ]
    ], resize_keyboard=True
)
