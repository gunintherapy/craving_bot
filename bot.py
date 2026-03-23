import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

# -------- TOKEN --------
TOKEN = os.getenv("TOKEN")
PORT = int(os.getenv("PORT", 8000))

if not TOKEN:
    raise ValueError("TOKEN не найден!")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# -------- FSM --------
class Form(StatesGroup):
    craving = State()
    level = State()
    trigger = State()
    emotion = State()
    thoughts = State()
    control = State()
    action = State()

# -------- START --------
@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.button(text="📔 Начать дневник", callback_data="start_check")
    kb.button(text="🤝 Обратиться за помощью", url="https://t.me/voshodkrsk")
    kb.adjust(1)

    await message.answer(
        "Привет! 👋 Я — твой дневник тяги.\n\n"
        "Будем вместе отслеживать моменты, когда тянет.\n"
        "Это поможет тебе оставаться в контроле. 🔥\n\n"
        "📔 Начни дневник или обратись за поддержкой.",
        reply_markup=kb.as_markup()
    )

# -------- START CHECK --------
@dp.callback_query(F.data == "start_check")
async def start_check(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    kb = InlineKeyboardBuilder()
    for txt in ["нет", "немного", "средне", "сильно"]:
        kb.button(text=txt, callback_data=f"c_{txt}")
    kb.adjust(1)

    await callback.message.edit_text("Тебя сейчас тянет?", reply_markup=kb.as_markup())
    await state.set_state(Form.craving)

# -------- CRAVING --------
@dp.callback_query(F.data.startswith("c_"))
async def craving(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    val = callback.data[2:]
    await state.update_data(craving=val)

    kb = InlineKeyboardBuilder()
    for i in range(11):
        kb.button(text=str(i), callback_data=f"l_{i}")
    kb.adjust(2)  # по 2 кнопки в ряд (удобно)

    await callback.message.edit_text("Насколько сильно? (0–10)", reply_markup=kb.as_markup())
    await state.set_state(Form.level)

# -------- LEVEL --------
@dp.callback_query(F.data.startswith("l_"))
async def level(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    val = int(callback.data[2:])
    await state.update_data(level=val)

    kb = InlineKeyboardBuilder()
    for t in ["стресс", "скука", "одиночество", "устал"]:
        kb.button(text=t, callback_data=f"t_{t}")
    kb.adjust(1)

    await callback.message.edit_text("Что это запустило?", reply_markup=kb.as_markup())
    await state.set_state(Form.trigger)

# -------- TRIGGER --------
@dp.callback_query(F.data.startswith("t_"))
async def trigger(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    val = callback.data[2:]
    await state.update_data(trigger=val)

    kb = InlineKeyboardBuilder()
    for e in ["тревога", "пусто", "злюсь", "грусть"]:
        kb.button(text=e, callback_data=f"e_{e}")
    kb.adjust(1)

    await callback.message.edit_text("Что ты сейчас чувствуешь?", reply_markup=kb.as_markup())
    await state.set_state(Form.emotion)

# -------- EMOTION --------
@dp.callback_query(F.data.startswith("e_"))
async def emotion(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    val = callback.data[2:]
    await state.update_data(emotion=val)

    kb = InlineKeyboardBuilder()
    for th in ["нет", "есть немного", "сильные"]:
        kb.button(text=th, callback_data=f"th_{th}")
    kb.adjust(1)

    await callback.message.edit_text("Есть ли мысли сорваться?", reply_markup=kb.as_markup())
    await state.set_state(Form.thoughts)

# -------- THOUGHTS --------
@dp.callback_query(F.data.startswith("th_"))
async def thoughts(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    val = callback.data[3:]
    await state.update_data(thoughts=val)

    kb = InlineKeyboardBuilder()
    for c in ["контроль есть", "шатает", "нет контроля"]:
        kb.button(text=c, callback_data=f"ctrl_{c}")
    kb.adjust(1)

    await callback.message.edit_text("Ты контролируешь ситуацию?", reply_markup=kb.as_markup())
    await state.set_state(Form.control)

# -------- CONTROL --------
@dp.callback_query(F.data.startswith("ctrl_"))
async def control(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    val = callback.data[5:]
    await state.update_data(control=val)

    kb = InlineKeyboardBuilder()
    for a in ["выйду", "отвлекусь", "позвоню", "подышу", "ничего"]:
        kb.button(text=a, callback_data=f"a_{a}")
    kb.adjust(1)

    await callback.message.edit_text("Что сделаешь прямо сейчас?", reply_markup=kb.as_markup())
    await state.set_state(Form.action)

# -------- ACTION --------
@dp.callback_query(F.data.startswith("a_"))
async def action(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    val = callback.data[2:]
    await state.update_data(action=val)

    data = await state.get_data()

    level = data.get("level", 0)
    thoughts = data.get("thoughts")
    control = data.get("control")

    if level >= 7 or thoughts == "сильные" or control == "нет контроля":
        result = "⚠️ Сейчас высокий риск срыва.\n\nСрочно смени обстановку:\n— выйди\n— позвони\n— холодная вода"
    elif level >= 4:
        result = "⚠️ Риск растёт.\n\nСделай действие:\n— смени место\n— отвлекись"
    else:
        result = "✅ Ты сейчас в контроле.\nПродолжай так же."

    if val == "ничего":
        result += "\n\nЕсли ничего не делать — станет хуже."

    await callback.message.edit_text(result)

    await state.clear()

# -------- WEB SERVER --------
async def handle(request):
    return web.Response(text="Bot is running")

# -------- RUN --------
async def main():
    print("🚀 Бот запущен")

    await bot.delete_webhook(drop_pending_updates=True)

    asyncio.create_task(dp.start_polling(bot))

    app = web.Application()
    app.router.add_get("/", handle)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
