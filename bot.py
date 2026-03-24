import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# --- НАСТРОЙКИ ---
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    logging.error("❌ TOKEN не найден!")
    exit(1)

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- МЕНЮ ---
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🆘 SOS"), KeyboardButton(text="📝 Дневник")],
        [KeyboardButton(text="🧘 Техники"), KeyboardButton(text="📊 Прогресс")]
    ],
    resize_keyboard=True
)

# --- FSM ---
class Form(StatesGroup):
    craving = State()
    level = State()
    trigger = State()
    emotion = State()
    thoughts = State()
    control = State()
    action = State()

# --- START ---
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Привет! 👋 Я твой дневник тяги.\n\n"
        "Я помогу тебе остановиться в момент импульса.\n\n"
        "Выбери действие 👇",
        reply_markup=main_kb
    )

# --- ДНЕВНИК ---
@dp.message(F.text == "📝 Дневник")
async def diary(message: types.Message, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.button(text="Нет", callback_data="c_0")
    kb.button(text="Лёгкая", callback_data="c_1")
    kb.button(text="Есть", callback_data="c_2")
    kb.button(text="Сильная", callback_data="c_3")
    kb.adjust(2)

    await message.answer("Ты сейчас испытываешь тягу?", reply_markup=kb.as_markup())
    await state.set_state(Form.craving)

# --- CRAVING ---
@dp.callback_query(F.data.startswith("c_"))
async def craving(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    val = int(callback.data[2:])
    await state.update_data(craving=val)

    # НЕТ ТЯГИ
    if val == 0:
        kb = InlineKeyboardBuilder()
        for r in ["Спокойствие", "Занят делом", "Люди рядом", "Всё норм"]:
            kb.button(text=r, callback_data=f"res_{r}")
        kb.adjust(2)

        await callback.message.edit_text(
            "✅ Тяги нет.\n\nЧто помогает тебе оставаться в этом состоянии?",
            reply_markup=kb.as_markup()
        )
        return

    # ЕСТЬ ТЯГА
    kb = InlineKeyboardBuilder()
    for i in range(11):
        kb.button(text=str(i), callback_data=f"l_{i}")
    kb.adjust(5)

    await callback.message.edit_text("Оцени силу тяги (0–10)", reply_markup=kb.as_markup())
    await state.set_state(Form.level)

# --- RESOURCE ---
@dp.callback_query(F.data.startswith("res_"))
async def resource(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text("👍 Отлично. Запомни это состояние.")
    await state.clear()

# --- LEVEL ---
@dp.callback_query(F.data.startswith("l_"))
async def level(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(level=int(callback.data[2:]))

    kb = InlineKeyboardBuilder()
    for t in ["стресс", "конфликт", "одиночество", "усталость", "скука"]:
        kb.button(text=t, callback_data=f"t_{t}")
    kb.adjust(2)

    await callback.message.edit_text("Что это запустило?", reply_markup=kb.as_markup())
    await state.set_state(Form.trigger)

# --- TRIGGER ---
@dp.callback_query(F.data.startswith("t_"))
async def trigger(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(trigger=callback.data[2:])

    kb = InlineKeyboardBuilder()
    for e in ["тревога", "злость", "грусть", "пустота", "стыд"]:
        kb.button(text=e, callback_data=f"e_{e}")
    kb.adjust(2)

    await callback.message.edit_text("Что ты чувствуешь?", reply_markup=kb.as_markup())
    await state.set_state(Form.emotion)

# --- EMOTION ---
@dp.callback_query(F.data.startswith("e_"))
async def emotion(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(emotion=callback.data[2:])

    kb = InlineKeyboardBuilder()
    for th in ["нет", "иногда", "постоянно"]:
        kb.button(text=th, callback_data=f"th_{th}")
    kb.adjust(3)

    await callback.message.edit_text("Есть мысли сорваться?", reply_markup=kb.as_markup())
    await state.set_state(Form.thoughts)

# --- THOUGHTS ---
@dp.callback_query(F.data.startswith("th_"))
async def thoughts(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(thoughts=callback.data[3:])

    kb = InlineKeyboardBuilder()
    for c in ["да", "шатает", "почти нет"]:
        kb.button(text=c, callback_data=f"ctrl_{c}")
    kb.adjust(3)

    await callback.message.edit_text("Контролируешь ситуацию?", reply_markup=kb.as_markup())
    await state.set_state(Form.control)

# --- CONTROL ---
@dp.callback_query(F.data.startswith("ctrl_"))
async def control(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(control=callback.data[5:])

    kb = InlineKeyboardBuilder()
    for a in ["позвоню", "выйду", "подышу", "отвлекусь", "ничего"]:
        kb.button(text=a, callback_data=f"a_{a}")
    kb.adjust(2)

    await callback.message.edit_text("Что сделаешь сейчас?", reply_markup=kb.as_markup())
    await state.set_state(Form.action)

# --- RESULT ---
@dp.callback_query(F.data.startswith("a_"))
async def action(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    data = await state.get_data()
    level = data.get("level", 0)

    if level >= 7 or data.get("thoughts") == "постоянно" or data.get("control") == "почти нет":
        text = "🆘 СТОП! Тебя сейчас несёт.\n\nСрочно:\n— выйди\n— холодная вода\n— позвони кому-то"
    elif level >= 4:
        text = "⚠️ Внимание.\n\nСделай паузу:\n— смени место\n— выпей воды"
    else:
        text = "✅ Ты в контроле.\n\nПродолжай."

    await callback.message.edit_text(text)
    await state.clear()

# --- КНОПКИ ---
@dp.message(F.text == "🆘 SOS")
async def sos(message: types.Message):
    await message.answer("🆘 СТОП!\n\n— выйди\n— вода\n— звонок")

@dp.message(F.text == "🧘 Техники")
async def tech(message: types.Message):
    await message.answer("🧘 Дыхание 4-4-4\nХолодная вода\nСмена обстановки")

@dp.message(F.text == "📊 Прогресс")
async def progress(message: types.Message):
    await message.answer("📊 Скоро будет статистика")

# --- ЗАПУСК ---
async def main():
    await bot.delete_webhook(drop_pending_updates=True)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
