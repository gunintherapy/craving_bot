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

# -------- TOKEN --------
TOKEN = os.getenv("TOKEN")
PORT = int(os.getenv("PORT", 8000))

if not TOKEN:
    raise ValueError("❌ TOKEN не найден!")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# -------- НИЖНЕЕ МЕНЮ --------
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

# -------- START (ПРИНУДИТЕЛЬНОЕ ОБНОВЛЕНИЕ МЕНЮ) --------
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("🔄 Обновляю меню...")

    await message.answer(
        "Привет! 👋 Я — твой дневник тяги.\n\n"
        "Я помогу тебе отслеживать состояние и не срываться.\n\n"
        "Выбери действие ниже 👇",
        reply_markup=main_kb
    )

# -------- ДНЕВНИК --------
@dp.message(F.text == "📝 Дневник")
async def diary(message: types.Message, state: FSMContext):
    kb = InlineKeyboardBuilder()
    for txt in ["нет", "немного", "средне", "сильно"]:
        kb.button(text=txt, callback_data=f"c_{txt}")
    kb.adjust(1)

    await message.answer("Тебя сейчас тянет?", reply_markup=kb.as_markup())
    await state.set_state(Form.craving)

# -------- CRAVING --------
@dp.callback_query(F.data.startswith("c_"))
async def craving(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(craving=callback.data[2:])

    kb = InlineKeyboardBuilder()
    for i in range(11):
        kb.button(text=str(i), callback_data=f"l_{i}")
    kb.adjust(2)

    await callback.message.edit_text("Насколько сильно? (0–10)", reply_markup=kb.as_markup())
    await state.set_state(Form.level)

# -------- LEVEL --------
@dp.callback_query(F.data.startswith("l_"))
async def level(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(level=int(callback.data[2:]))

    kb = InlineKeyboardBuilder()
    for t in ["стресс", "скука", "одиночество", "усталость", "конфликт"]:
        kb.button(text=t, callback_data=f"t_{t}")
    kb.adjust(1)

    await callback.message.edit_text("Что это запустило?", reply_markup=kb.as_markup())
    await state.set_state(Form.trigger)

# -------- TRIGGER --------
@dp.callback_query(F.data.startswith("t_"))
async def trigger(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(trigger=callback.data[2:])

    kb = InlineKeyboardBuilder()
    for e in ["тревога", "злость", "грусть", "пустота", "стыд"]:
        kb.button(text=e, callback_data=f"e_{e}")
    kb.adjust(1)

    await callback.message.edit_text("Что ты сейчас чувствуешь?", reply_markup=kb.as_markup())
    await state.set_state(Form.emotion)

# -------- EMOTION --------
@dp.callback_query(F.data.startswith("e_"))
async def emotion(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(emotion=callback.data[2:])

    kb = InlineKeyboardBuilder()
    for th in ["нет", "мелькают", "крутятся постоянно"]:
        kb.button(text=th, callback_data=f"th_{th}")
    kb.adjust(1)

    await callback.message.edit_text("Есть мысли сорваться?", reply_markup=kb.as_markup())
    await state.set_state(Form.thoughts)

# -------- THOUGHTS --------
@dp.callback_query(F.data.startswith("th_"))
async def thoughts(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(thoughts=callback.data[3:])

    kb = InlineKeyboardBuilder()
    for c in ["да", "шатает", "почти нет"]:
        kb.button(text=c, callback_data=f"ctrl_{c}")
    kb.adjust(1)

    await callback.message.edit_text("Ты контролируешь ситуацию?", reply_markup=kb.as_markup())
    await state.set_state(Form.control)

# -------- CONTROL --------
@dp.callback_query(F.data.startswith("ctrl_"))
async def control(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(control=callback.data[5:])

    kb = InlineKeyboardBuilder()
    for a in ["позвоню", "выйду", "подышу", "отвлекусь", "ничего"]:
        kb.button(text=a, callback_data=f"a_{a}")
    kb.adjust(1)

    await callback.message.edit_text("Что сделаешь прямо сейчас?", reply_markup=kb.as_markup())
    await state.set_state(Form.action)

# -------- ACTION --------
@dp.callback_query(F.data.startswith("a_"))
async def action(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(action=callback.data[2:])

    data = await state.get_data()

    level = data.get("level", 0)
    thoughts = data.get("thoughts")
    control = data.get("control")
    trigger = data.get("trigger")

    if level >= 7 or thoughts == "крутятся постоянно" or control == "почти нет":
        text = (
            "🆘 СТОП! ОПАСНОСТЬ.\n\n"
            "Тебя сейчас несёт.\n\n"
            "Сделай прямо сейчас:\n"
            "— выйди\n"
            "— холодная вода\n"
            "— позвони кому-то"
        )
    elif level >= 4:
        text = (
            "⚠️ Внимание.\n\n"
            f"Триггер: {trigger}\n\n"
            "Сделай паузу:\n"
            "— смени место\n"
            "— выпей воды"
        )
    else:
        text = (
            "✅ Ты в контроле.\n\n"
            "Тяга есть, но она не управляет тобой.\n"
            "Продолжай."
        )

    if data.get("action") == "ничего":
        text += "\n\nЕсли ничего не делать — станет хуже."

    await callback.message.edit_text(text)
    await state.clear()

# -------- SOS --------
@dp.message(F.text == "🆘 SOS")
async def sos(message: types.Message):
    await message.answer(
        "🆘 СТОП!\n\n"
        "Сейчас важно не думать, а действовать:\n\n"
        "— выйди из места\n"
        "— холодная вода\n"
        "— позвони кому-то\n\n"
        "Ты не обязан срываться."
    )

# -------- ТЕХНИКИ --------
@dp.message(F.text == "🧘 Техники")
async def techniques(message: types.Message):
    await message.answer(
        "🧘 Техники:\n\n"
        "1. Дыхание 4-4-4\n"
        "2. Холодная вода\n"
        "3. Смена обстановки\n\n"
        "Сделай любую прямо сейчас."
    )

# -------- ПРОГРЕСС --------
@dp.message(F.text == "📊 Прогресс")
async def progress(message: types.Message):
    await message.answer(
        "📊 Прогресс скоро появится.\n\n"
        "Мы подключим аналитику."
    )

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
