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

# ---------- НАСТРОЙКИ ----------
TOKEN = os.getenv("TOKEN")
PORT = int(os.getenv("PORT", 8000))

if not TOKEN:
    raise ValueError("❌ TOKEN не найден!")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ---------- МЕНЮ ----------
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🆘 SOS"), KeyboardButton(text="📝 Дневник")],
        [KeyboardButton(text="🧘 Техники"), KeyboardButton(text="📊 Прогресс")]
    ],
    resize_keyboard=True
)

# ---------- FSM ----------
class Form(StatesGroup):
    craving = State()
    level = State()
    trigger = State()
    emotion = State()
    thoughts = State()
    control = State()
    action = State()

# ---------- START ----------
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Привет 👋\n\n"
        "Я — твой дневник тяги.\n"
        "Помогаю не сорваться в моменте.\n\n"
        "Выбери действие 👇",
        reply_markup=main_kb
    )

# ---------- ЛОВИМ ВСЕ ТЕКСТЫ (ОЧЕНЬ ВАЖНО) ----------
@dp.message(F.text)
async def menu_handler(message: types.Message, state: FSMContext):
    text = message.text.strip()

    # --- ДНЕВНИК ---
    if text.startswith("📝"):
        kb = InlineKeyboardBuilder()
        kb.button(text="Нет", callback_data="c_0")
        kb.button(text="Лёгкая", callback_data="c_1")
        kb.button(text="Есть", callback_data="c_2")
        kb.button(text="Сильная", callback_data="c_3")
        kb.adjust(2)

        await message.answer("Ты сейчас испытываешь тягу?", reply_markup=kb.as_markup())
        await state.set_state(Form.craving)

    # --- SOS ---
    elif text.startswith("🆘"):
        await message.answer(
            "🆘 СТОП!\n\n"
            "Сделай прямо сейчас:\n"
            "— выйди\n"
            "— холодная вода\n"
            "— позвони кому-то"
        )

    # --- ТЕХНИКИ ---
    elif text.startswith("🧘"):
        await message.answer(
            "🧘 Техники:\n\n"
            "1. Дыхание 4-4-4\n"
            "2. Холодная вода\n"
            "3. Смена обстановки"
        )

    # --- ПРОГРЕСС ---
    elif text.startswith("📊"):
        await message.answer("📊 Прогресс скоро появится")

# ---------- CRAVING ----------
@dp.callback_query(F.data.startswith("c_"))
async def craving(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    val = int(callback.data[2:])
    await state.update_data(craving=val)

    # --- НЕТ ТЯГИ ---
    if val == 0:
        kb = InlineKeyboardBuilder()
        for r in ["спокойствие", "дело", "люди", "норм"]:
            kb.button(text=r, callback_data=f"res_{r}")
        kb.adjust(1)

        await callback.message.edit_text(
            "✅ Сейчас тяги нет.\n\n"
            "Зафиксируй состояние 👇",
            reply_markup=kb.as_markup()
        )
        return

    # --- ДАЛЬШЕ ---
    kb = InlineKeyboardBuilder()
    for i in range(11):
        kb.button(text=str(i), callback_data=f"l_{i}")
    kb.adjust(5)

    await callback.message.edit_text("Сила тяги (0–10)", reply_markup=kb.as_markup())
    await state.set_state(Form.level)

# ---------- RESOURCE ----------
@dp.callback_query(F.data.startswith("res_"))
async def res(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text("👍 Запомни это состояние")
    await state.clear()

# ---------- LEVEL ----------
@dp.callback_query(F.data.startswith("l_"))
async def level(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(level=int(callback.data[2:]))

    kb = InlineKeyboardBuilder()
    for t in ["стресс", "конфликт", "одиночество", "усталость", "скука"]:
        kb.button(text=t, callback_data=f"t_{t}")
    kb.adjust(2)

    await callback.message.edit_text("Причина?", reply_markup=kb.as_markup())
    await state.set_state(Form.trigger)

# ---------- TRIGGER ----------
@dp.callback_query(F.data.startswith("t_"))
async def trigger(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(trigger=callback.data[2:])

    kb = InlineKeyboardBuilder()
    for e in ["тревога", "злость", "грусть", "пустота", "стыд"]:
        kb.button(text=e, callback_data=f"e_{e}")
    kb.adjust(2)

    await callback.message.edit_text("Что чувствуешь?", reply_markup=kb.as_markup())
    await state.set_state(Form.emotion)

# ---------- EMOTION ----------
@dp.callback_query(F.data.startswith("e_"))
async def emotion(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(emotion=callback.data[2:])

    kb = InlineKeyboardBuilder()
    for th in ["нет", "иногда", "постоянно"]:
        kb.button(text=th, callback_data=f"th_{th}")
    kb.adjust(3)

    await callback.message.edit_text("Мысли сорваться?", reply_markup=kb.as_markup())
    await state.set_state(Form.thoughts)

# ---------- THOUGHTS ----------
@dp.callback_query(F.data.startswith("th_"))
async def thoughts(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(thoughts=callback.data[3:])

    kb = InlineKeyboardBuilder()
    for c in ["да", "шатает", "почти нет"]:
        kb.button(text=c, callback_data=f"ctrl_{c}")
    kb.adjust(3)

    await callback.message.edit_text("Контроль?", reply_markup=kb.as_markup())
    await state.set_state(Form.control)

# ---------- CONTROL ----------
@dp.callback_query(F.data.startswith("ctrl_"))
async def control(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(control=callback.data[5:])

    kb = InlineKeyboardBuilder()
    for a in ["позвоню", "выйду", "подышу", "ничего"]:
        kb.button(text=a, callback_data=f"a_{a}")
    kb.adjust(2)

    await callback.message.edit_text("Что сделаешь?", reply_markup=kb.as_markup())
    await state.set_state(Form.action)

# ---------- RESULT ----------
@dp.callback_query(F.data.startswith("a_"))
async def result(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(action=callback.data[2:])
    data = await state.get_data()

    level = data.get("level", 0)
    thoughts = data.get("thoughts")
    control = data.get("control")

    if level >= 7 or thoughts == "постоянно" or control == "почти нет":
        text = "🆘 СТОП! Тебя несёт. Срочно действуй!"
    elif level >= 4:
        text = "⚠️ Внимание. Смени обстановку."
    else:
        text = "✅ Ты в контроле."

    await callback.message.edit_text(text)
    await state.clear()

# ---------- WEB ----------
async def handle(request):
    return web.Response(text="OK")

async def main():
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
