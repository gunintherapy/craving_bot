# bot.py
import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from flask import Flask
import threading

# --------- Токен ---------
TOKEN = os.getenv("TOKEN")  # будет браться из переменной окружения Render

# --------- Настройки ---------
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

# --------- START ---------
@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.button(text="Начать чек", callback_data="start_check")
    await message.answer(
        "Привет! Это бот для отслеживания тяги.\nЗаймет 1–2 минуты.\nПоможет не сорваться.",
        reply_markup=kb.as_markup()
    )

@dp.callback_query(F.data == "start_check")
async def start_check(callback: types.CallbackQuery, state: FSMContext):
    kb = InlineKeyboardBuilder()
    for txt in ["нет", "немного", "нормально тянет", "очень сильно"]:
        kb.button(text=txt, callback_data=txt)
    await callback.message.answer("Тебя сейчас тянет?", reply_markup=kb.as_markup())
    await state.set_state(Form.craving)

# --------- Далее добавляем остальные состояния FSM (craving_level, trigger, emotions, thoughts, control, action)
# Можно скопировать из полного примера, который я присылал ранее

async def main():
    await dp.start_polling(bot)

# --------- Flask для Render Web Service ---------
app = Flask(__name__)
PORT = int(os.environ.get("PORT", 8000))

@app.route("/")
def home():
    return "Bot is running"

if __name__ == "__main__":
    # Запускаем бота в отдельном потоке
    threading.Thread(target=lambda: asyncio.run(main())).start()
    # Запускаем Flask
    app.run(host="0.0.0.0", port=PORT)
