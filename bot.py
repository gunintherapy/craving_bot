# bot.py
import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from flask import Flask
import threading

# --------- Настройки ---------
TOKEN = os.getenv("TOKEN")  # берем токен из Render
PORT = int(os.getenv("PORT", 8000))

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --------- FSM (состояния бота) ---------
class Form(StatesGroup):
    craving = State()
    craving_level = State()
    trigger = State()
    emotions = State()
    thoughts = State()
    control = State()
    action = State()

# --------- Команда /start ---------
@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.button(text="Начать чек", callback_data="start_check")
    await message.answer(
        "Привет! Это бот для отслеживания тяги.\nЗаймет 1–2 минуты.\nПоможет не сорваться.",
        reply_markup=kb.as_markup()
    )

# --------- Обработка кнопки "Начать чек" ---------
@dp.callback_query(lambda c: c.data == "start_check")
async def start_check(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()  # убираем "часики" на кнопке
    kb = InlineKeyboardBuilder()
    for option in ["нет", "немного", "нормально тянет", "очень сильно"]:
        kb.button(text=option, callback_data=f"craving_{option}")
    await callback.message.answer("Тебя сейчас тянет?", reply_markup=kb.as_markup())
    await state.set_state(Form.craving)

# --------- Обработка выбора тяги ---------
@dp.callback_query(lambda c: c.data.startswith("craving_"))
async def handle_craving(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    selected = callback.data.split("_")[1]
    await callback.message.answer(f"Ты выбрал: {selected}\nСпасибо! Чек завершен.")
    await state.clear()  # очищаем состояние после чека

# --------- Запуск бота ---------
async def main():
    await dp.start_polling(bot)

# --------- Flask для Render Web Service ---------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

if __name__ == "__main__":
    threading.Thread(target=lambda: asyncio.run(main())).start()
    app.run(host="0.0.0.0", port=PORT)
