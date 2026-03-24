import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiohttp import web

# -------- НАСТРОЙКИ --------
TOKEN = os.getenv("TOKEN")
PORT = int(os.getenv("PORT", 8000))

if not TOKEN:
    logging.error("❌ TOKEN не найден!")
    exit(1)

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# -------- МЕНЮ --------
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🆘 SOS"), KeyboardButton(text="📝 Дневник")],
        [KeyboardButton(text="🧘 Техники"), KeyboardButton(text="📊 Прогресс")]
    ],
    resize_keyboard=True
)

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
async def start(message: types.Message):
    await message.answer(
        "Привет! 👋 Я — твой дневник тяги.\nВыбери действие ниже 👇",
        reply_markup=main_kb
    )

# -------- ДНЕВНИК --------
@dp.message(F.text == "📝 Дневник")
async def diary(message: types.Message, state: FSMContext):
    kb = InlineKeyboardBuilder()
    for txt in ["нет", "немного", "средне", "сильно"]:
        kb.button(text=txt, callback_data=f"c_{txt}")
    kb.adjust(2)

    await message.answer(
        "Шаг 1 из 7\n\nТебя сейчас тянет?",
        reply_markup=kb.as_markup()
    )
    await state.set_state(Form.craving)

# -------- ШАГ 1 --------
@dp.callback_query(F.data.startswith("c_"))
async def craving(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(craving=callback.data[2:])

    kb = InlineKeyboardBuilder()
    for i in range(11):
        kb.button(text=str(i), callback_data=f"l_{i}")
    kb.adjust(5)

    await callback.message.edit_text(
        "Шаг 2 из 7\n\nНасколько сильно? (0–10)",
        reply_markup=kb.as_markup()
    )
    await state.set_state(Form.level)

# -------- ШАГ 2 --------
@dp.callback_query(F.data.startswith("l_"))
async def level(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(level=int(callback.data[2:]))

    kb = InlineKeyboardBuilder()
    for t in ["стресс", "скука", "одиночество", "усталость", "конфликт"]:
        kb.button(text=t, callback_data=f"t_{t}")
    kb.adjust(2)

    await callback.message.edit_text(
        "Шаг 3 из 7\n\nЧто это запустило?",
        reply_markup=kb.as_markup()
    )
    await state.set_state(Form.trigger)

# -------- ШАГ 3 --------
@dp.callback_query(F.data.startswith("t_"))
async def trigger(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(trigger=callback.data[2:])

    kb = InlineKeyboardBuilder()
    for e in ["тревога", "злость", "грусть", "пустота", "стыд"]:
        kb.button(text=e, callback_data=f"e_{e}")
    kb.adjust(2)

    await callback.message.edit_text(
        "Шаг 4 из 7\n\nЧто ты сейчас чувствуешь?",
        reply_markup=kb.as_markup()
    )
    await state.set_state(Form.emotion)

# -------- ШАГ 4 --------
@dp.callback_query(F.data.startswith("e_"))
async def emotion(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(emotion=callback.data[2:])

    kb = InlineKeyboardBuilder()
    for th in ["нет", "мелькают", "постоянно"]:
        kb.button(text=th, callback_data=f"th_{th}")
    kb.adjust(3)

    await callback.message.edit_text(
        "Шаг 5 из 7\n\nЕсть мысли сорваться?",
        reply_markup=kb.as_markup()
    )
    await state.set_state(Form.thoughts)

# -------- ШАГ 5 --------
@dp.callback_query(F.data.startswith("th_"))
async def thoughts(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(thoughts=callback.data[3:])

    kb = InlineKeyboardBuilder()
    for c in ["да", "шатает", "почти нет"]:
        kb.button(text=c, callback_data=f"ctrl_{c}")
    kb.adjust(3)

    await callback.message.edit_text(
        "Шаг 6 из 7\n\nТы контролируешь ситуацию?",
        reply_markup=kb.as_markup()
    )
    await state.set_state(Form.control)

# -------- ШАГ 6 --------
@dp.callback_query(F.data.startswith("ctrl_"))
async def control(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(control=callback.data[5:])

    kb = InlineKeyboardBuilder()
    for a in ["позвоню", "выйду", "подышу", "отвлекусь", "ничего"]:
        kb.button(text=a, callback_data=f"a_{a}")
    kb.adjust(2)

    await callback.message.edit_text(
        "Шаг 7 из 7\n\nЧто сделаешь прямо сейчас?",
        reply_markup=kb.as_markup()
    )
    await state.set_state(Form.action)

# -------- ФИНАЛ --------
@dp.callback_query(F.data.startswith("a_"))
async def action(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(action=callback.data[2:])

    data = await state.get_data()
    level = data.get("level", 0)
    thoughts = data.get("thoughts")
    control = data.get("control")
    trigger = data.get("trigger")

    if level >= 7 or thoughts == "постоянно" or control == "почти нет":
        text = "🆘 СТОП! ОПАСНОСТЬ.\n\nСделай сейчас:\n— выйди\n— холодная вода\n— позвони"
    elif level >= 4:
        text = f"⚠️ Внимание\nТриггер: {trigger}\n\nСмени обстановку"
    else:
        text = "✅ Ты в контроле"

    await callback.message.edit_text(text)
    await state.clear()

# -------- ПРОЧЕЕ --------
@dp.message(F.text == "🆘 SOS")
async def sos(message: types.Message):
    await message.answer("🆘 Срочно смени обстановку или позвони кому-то.")

@dp.message(F.text == "🧘 Техники")
async def tech(message: types.Message):
    await message.answer("🧘 Дыхание 4-4-4\nХолодная вода\nСмена места")

@dp.message(F.text == "📊 Прогресс")
async def progress(message: types.Message):
    await message.answer("📊 В разработке")

# -------- WEB --------
async def handle(request):
    return web.Response(text="Bot is running")

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
