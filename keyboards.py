from telegram import InlineKeyboardButton, KeyboardButton
from enum import Enum

keyboard_neural_network = [
    [
        InlineKeyboardButton("Stable Diffusion",
                             callback_data="stable_diffusion"),
        InlineKeyboardButton("Kandinsky",
                             callback_data="kandinsky"),
        InlineKeyboardButton("Stable Cascade",
                             callback_data="stable_cascade"),
    ]
]