import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

# -------- TOKEN & PORT --------
TOKEN = os.getenv("TOKEN")
PORT = int(os.getenv("PORT", 8000))  # Render назначает порт через ENV

if not TOKEN:
    raise ValueError("❌ TOKEN не найден! Добавь его в Render → Environment")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# -------- FSM --------
class Form(StatesGroup):
    craving = State()
    craving_level = State()
    trigger = State()
    emotions = State()
    thoughts = State()
    control = State()
    action = State()

# -------- START --------
@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.button(text="Начать чек", callback_data="start_check")
    await message.answer(
        "Привет! 👋 Я — твой дневник тяги.\n"
        "Будем вместе отслеживать моменты, когда у тебя тяга.\n"
        "Следуй шаг за шагом — и ты не потеряешь контроле! 🔥",
        reply_markup=kb.as_markup()
    )

# -------- START CHECK --------
@dp.callback_query(F.data == "start_check")
async def start_check(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    kb = InlineKeyboardBuilder()
    for txt in ["нет", "немного", "нормально тянет", "очень сильно"]:
        kb.button(text=txt, callback_data=txt)
    await callback.message.answer("Тебя сейчас тянет?", reply_markup=kb.as_markup())
    await state.set_state(Form.craving)

# -------- CRAVING --------
@dp.callback_query(Form.craving)
async def craving(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(craving=callback.data)
    kb = InlineKeyboardBuilder()
    for i in range(11):
        kb.button(text=str(i), callback_data=str(i))
    await callback.message.answer("Насколько сильно? (0–10)", reply_markup=kb.as_markup())
    await state.set_state(Form.craving_level)

# -------- LEVEL --------
@dp.callback_query(Form.craving_level)
async def craving_level(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(level=int(callback.data))
    kb = InlineKeyboardBuilder()
    for o in ["стресс", "скука", "устал", "одиночество", "привычка", "не понимаю"]:
        kb.button(text=o, callback_data=o)
    await callback.message.answer("Что это запустило?", reply_markup=kb.as_markup())
    await state.set_state(Form.trigger)

# -------- TRIGGER --------
@dp.callback_query(Form.trigger)
async def trigger(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(trigger=callback.data)
    kb = InlineKeyboardBuilder()
    for o in ["тревожно", "пусто", "злюсь", "грусть", "раздражение", "нормально"]:
        kb.button(text=o, callback_data=o)
    await callback.message.answer("Что внутри сейчас?", reply_markup=kb.as_markup())
    await state.set_state(Form.emotions)

# -------- EMOTIONS --------
@dp.callback_query(Form.emotions)
async def emotions(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(emotions=callback.data)
    kb = InlineKeyboardBuilder()
    for o in ["нет", "иногда мелькают", "крутятся постоянно"]:
        kb.button(text=o, callback_data=o)
    await callback.message.answer("Мысли сорваться есть?", reply_markup=kb.as_markup())
    await state.set_state(Form.thoughts)

# -------- THOUGHTS --------
@dp.callback_query(Form.thoughts)
async def thoughts(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(thoughts=callback.data)
    kb = InlineKeyboardBuilder()
    for o in ["контролирую", "шатает", "почти не контролирую"]:
        kb.button(text=o, callback_data=o)
    await callback.message.answer("Ты контролируешь ситуацию?", reply_markup=kb.as_markup())
    await state.set_state(Form.control)

# -------- CONTROL --------
@dp.callback_query(Form.control)
async def control(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(control=callback.data)
    kb = InlineKeyboardBuilder()
    for o in ["выйду", "отвлекусь", "позвоню", "подышу", "ничего"]:
        kb.button(text=o, callback_data=o)
    await callback.message.answer("Что сделаешь сейчас?", reply_markup=kb.as_markup())
    await state.set_state(Form.action)

# -------- ACTION + ANALYSIS --------
@dp.callback_query(Form.action)
async def action(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(action=callback.data)
    data = await state.get_data()
    level = data.get("level")
    thoughts = data.get("thoughts")
    control_val = data.get("control")
    trigger_val = data.get("trigger")

    # ---- Логика риска ----
    if level >= 7 or thoughts == "крутятся постоянно" or control_val == "почти не контролирую":
        risk = "high"
    elif level >= 4:
        risk = "medium"
    else:
        risk = "low"

    trigger_text = ""
    if trigger_val == "стресс":
        trigger_text = "\nПохоже, тебя задел стресс."
    elif trigger_val == "одиночество":
        trigger_text = "\nСейчас тебе не хватает контакта."
    elif trigger_val == "скука":
        trigger_text = "\nЭто больше про пустоту."

    if risk == "low":
        text = "Ты сейчас в контроле. Продолжай."
    elif risk == "medium":
        text = "Важно остановиться. Смени место, отвлекись."
    else:
        text = "СТОП. Тебя несёт. Срочно выйди или позвони кому-то."

    if data.get("action") == "ничего":
        text += "\n\nЕсли ничего не делать — станет хуже."

    await callback.message.answer(text + trigger_text)
    await state.clear()

# -------- WEB SERVER --------
async def handle(request):
    return web.Response(text="Bot is running")

# -------- RUN --------
async def main():
    print("🚀 Бот запущен")
    await bot.delete_webhook(drop_pending_updates=True)

    # запуск polling в фоне
    asyncio.create_task(dp.start_polling(bot))

    # запуск web сервера (Render требует порт)
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    # держим процесс живым
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
