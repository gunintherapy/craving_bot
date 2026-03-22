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

# --------- Настройки ---------
TOKEN = os.getenv("TOKEN")
PORT = int(os.getenv("PORT", 8000))

if not TOKEN:
    raise ValueError("❌ Переменная окружения TOKEN не установлена! Render не подставил токен!")

# Выводим первые символы токена для проверки
print("✅ TOKEN проверка:", TOKEN[:10], "...")

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
        "Это бот для отслеживания тяги.\n\n"
        "Займет 1–2 минуты.\n"
        "Поможет не сорваться.",
        reply_markup=kb.as_markup()
    )

# --------- START CHECK ---------
@dp.callback_query(F.data == "start_check")
async def start_check(callback: types.CallbackQuery, state: FSMContext):
    kb = InlineKeyboardBuilder()
    for txt in ["нет", "немного", "нормально тянет", "очень сильно"]:
        kb.button(text=txt, callback_data=txt)

    await callback.message.answer("Тебя сейчас тянет?", reply_markup=kb.as_markup())
    await state.set_state(Form.craving)

# --------- CRAVING ---------
@dp.callback_query(Form.craving)
async def craving(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(craving=callback.data)

    kb = InlineKeyboardBuilder()
    for i in range(0, 11):
        kb.button(text=str(i), callback_data=str(i))

    await callback.message.answer("Насколько сильно? (0–10)", reply_markup=kb.as_markup())
    await state.set_state(Form.craving_level)

# --------- LEVEL ---------
@dp.callback_query(Form.craving_level)
async def craving_level(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(level=int(callback.data))

    kb = InlineKeyboardBuilder()
    options = ["стресс", "скука", "устал", "одиночество", "привычка", "не понимаю"]
    for o in options:
        kb.button(text=o, callback_data=o)

    await callback.message.answer("Что это запустило?", reply_markup=kb.as_markup())
    await state.set_state(Form.trigger)

# --------- TRIGGER ---------
@dp.callback_query(Form.trigger)
async def trigger(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(trigger=callback.data)

    kb = InlineKeyboardBuilder()
    options = ["тревожно", "пусто", "злюсь", "грусть", "раздражение", "нормально"]
    for o in options:
        kb.button(text=o, callback_data=o)

    await callback.message.answer("Что внутри сейчас?", reply_markup=kb.as_markup())
    await state.set_state(Form.emotions)

# --------- EMOTIONS ---------
@dp.callback_query(Form.emotions)
async def emotions(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(emotions=callback.data)

    kb = InlineKeyboardBuilder()
    options = ["нет", "иногда мелькают", "крутятся постоянно"]
    for o in options:
        kb.button(text=o, callback_data=o)

    await callback.message.answer("Мысли сорваться есть?", reply_markup=kb.as_markup())
    await state.set_state(Form.thoughts)

# --------- THOUGHTS ---------
@dp.callback_query(Form.thoughts)
async def thoughts(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(thoughts=callback.data)

    kb = InlineKeyboardBuilder()
    options = ["контролирую", "шатает", "почти не контролирую"]
    for o in options:
        kb.button(text=o, callback_data=o)

    await callback.message.answer("Ты контролируешь ситуацию?", reply_markup=kb.as_markup())
    await state.set_state(Form.control)

# --------- CONTROL ---------
@dp.callback_query(Form.control)
async def control(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(control=callback.data)

    kb = InlineKeyboardBuilder()
    options = ["выйду", "отвлекусь", "позвоню", "подышу", "ничего"]
    for o in options:
        kb.button(text=o, callback_data=o)

    await callback.message.answer("Что сделаешь сейчас?", reply_markup=kb.as_markup())
    await state.set_state(Form.action)

# --------- ACTION + ANALYSIS ---------
@dp.callback_query(Form.action)
async def action(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(action=callback.data)
    data = await state.get_data()

    level = data.get("level")
    thoughts = data.get("thoughts")
    control_val = data.get("control")
    trigger_val = data.get("trigger")

    # Определение состояния
    if level >= 7 or thoughts == "крутятся постоянно" or control_val == "почти не контролирую":
        risk = "high"
    elif level >= 4:
        risk = "medium"
    else:
        risk = "low"

    # Персонализация
    trigger_text = ""
    if trigger_val == "стресс":
        trigger_text = "\nПохоже, тебя задел стресс."
    elif trigger_val == "одиночество":
        trigger_text = "\nСейчас тебе не хватает контакта."
    elif trigger_val == "скука":
        trigger_text = "\nЭто больше про пустоту, чем про желание."

    # Ответ
    if risk == "low":
        text = (
            "Ты сейчас в контроле.\n\n"
            "Тяга есть, но ты её держишь.\n"
            "Продолжай в том же духе."
        )
    elif risk == "medium":
        text = (
            "Сейчас тот момент, где всё может раскрутиться.\n"
            "Важно остановиться.\n\n"
            "Сделай простое действие:\n"
            "— смени место\n— выйди\n— отвлекись"
        )
    else:
        text = (
            "Стоп.\nТебя сейчас несёт.\n\n"
            "Если ничего не сделать — будет срыв.\n\n"
            "Сделай прямо сейчас:\n"
            "— выйди\n— позвони\n— холодная вода"
        )

    if data.get("action") == "ничего":
        text += "\n\nЕсли ничего не делать — станет хуже. Ты сейчас на развилке."

    await callback.message.answer(text + trigger_text)
    await state.clear()

# --------- RUN ---------
async def main():
    await dp.start_polling(bot)

# Flask для Render
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running ✅"

if __name__ == "__main__":
    threading.Thread(target=lambda: asyncio.run(main())).start()
    app.run(host="0.0.0.0", port=PORT)
