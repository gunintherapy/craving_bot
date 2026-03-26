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
# -------- SOS СЦЕНАРИЙ --------

@dp.message(F.text == "🆘 SOS")
async def sos_start(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Сделал. Что дальше?", callback_data="sos_1")
    kb.adjust(1)

    await message.answer(
        "СТОП! ЗАМРИ. ✋\n\n"
        "Прямо сейчас твой мозг пытается тебя обмануть.\n"
        "Это не ты — это импульс. Он пройдет.\n\n"
        "ТВОЕ ЗАДАНИЕ:\n"
        "— уйди в другое место\n"
        "— умойся холодной водой 3 раза\n\n"
        "Сделай это прямо сейчас.",
        reply_markup=kb.as_markup()
    )


# --- ШАГ 2 ---
@dp.callback_query(F.data == "sos_1")
async def sos_step_2(callback: types.CallbackQuery):
    await callback.answer()

    kb = InlineKeyboardBuilder()
    kb.button(text="✅ В реальности. Давай дышать.", callback_data="sos_2")
    kb.adjust(1)

    await callback.message.edit_text(
        "Хорошо. Возвращаем тебя в реальность.\n\n"
        "Техника 5-4-3-2-1:\n\n"
        "👀 Назови 5 предметов\n"
        "👂 4 звука\n"
        "🤝 3 ощущения\n"
        "👃 2 запаха\n"
        "👅 1 вкус\n\n"
        "Делай это прямо сейчас.",
        reply_markup=kb.as_markup()
    )


# --- ШАГ 3 ---
@dp.callback_query(F.data == "sos_2")
async def sos_step_3(callback: types.CallbackQuery):
    await callback.answer()

    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Дыхание в норме. Финал.", callback_data="sos_3")
    kb.adjust(1)

    await callback.message.edit_text(
        "Теперь дыхание.\n\n"
        "Делаем квадрат:\n\n"
        "1️⃣ Вдох — 4 сек\n"
        "2️⃣ Задержка — 4 сек\n"
        "3️⃣ Выдох — 4 сек\n"
        "4️⃣ Задержка — 4 сек\n\n"
        "Повтори 4 раза.",
        reply_markup=kb.as_markup()
    )


# --- ШАГ 4 ---
@dp.callback_query(F.data == "sos_3")
async def sos_step_4(callback: types.CallbackQuery):
    await callback.answer()

    kb = InlineKeyboardBuilder()
    kb.button(text="🏠 В меню", callback_data="sos_end")
    kb.adjust(1)

    await callback.message.edit_text(
        "Ты выстоял пик. Серьезно.\n\n"
        "Сейчас важно закрепить:\n\n"
        "— позвони кому-то\n"
        "— напиши кому-то\n"
        "— выпей чай или съешь что-то сладкое\n\n"
        "Не оставайся один.",
        reply_markup=kb.as_markup()
    )


# --- ВОЗВРАТ В МЕНЮ ---
@dp.callback_query(F.data == "sos_end")
async def sos_end(callback: types.CallbackQuery):
    await callback.answer()

    await callback.message.edit_text(
        "Ты справился. 💪\n\n"
        "Если понадобится — я рядом."
    )
# --- ТЕХНИКИ (ИНТЕРАКТИВНОЕ МЕНЮ) ---

@dp.message(F.text == "🧘 Техники")
async def tech_menu(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="🫁 Дыхание", callback_data="tech_breath")
    kb.button(text="🧊 Холод", callback_data="tech_cold")
    kb.button(text="🌍 Заземление", callback_data="tech_ground")
    kb.button(text="🧠 Переключение", callback_data="tech_switch")
    kb.adjust(1)

    await message.answer(
        "Выбери технику 👇",
        reply_markup=kb.as_markup()
    )


# --- ДЫХАНИЕ ---
@dp.callback_query(F.data == "tech_breath")
async def tech_breath(callback: types.CallbackQuery):
    await callback.answer()

    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Назад", callback_data="tech_back")

    await callback.message.edit_text(
        "🫁 ДЫХАНИЕ\n\n"
        "Сделай 4 цикла:\n"
        "— вдох 4 сек\n"
        "— пауза 4 сек\n"
        "— выдох 4 сек\n"
        "— пауза 4 сек\n\n"
        "Сделай это прямо сейчас.",
        reply_markup=kb.as_markup()
    )


# --- ХОЛОД ---
@dp.callback_query(F.data == "tech_cold")
async def tech_cold(callback: types.CallbackQuery):
    await callback.answer()

    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Назад", callback_data="tech_back")

    await callback.message.edit_text(
        "🧊 ХОЛОД\n\n"
        "Сделай прямо сейчас:\n"
        "— умойся холодной водой\n"
        "или\n"
        "— подержи руки под холодной водой\n\n"
        "Это быстро снижает тягу.",
        reply_markup=kb.as_markup()
    )


# --- ЗАЗЕМЛЕНИЕ ---
@dp.callback_query(F.data == "tech_ground")
async def tech_ground(callback: types.CallbackQuery):
    await callback.answer()

    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Назад", callback_data="tech_back")

    await callback.message.edit_text(
        "🌍 ЗАЗЕМЛЕНИЕ\n\n"
        "Назови вслух:\n"
        "5 — что видишь\n"
        "4 — что слышишь\n"
        "3 — что чувствуешь\n"
        "2 — запаха\n"
        "1 — вкус\n\n"
        "Это вернет тебя в реальность.",
        reply_markup=kb.as_markup()
    )


# --- ПЕРЕКЛЮЧЕНИЕ ---
@dp.callback_query(F.data == "tech_switch")
async def tech_switch(callback: types.CallbackQuery):
    await callback.answer()

    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Назад", callback_data="tech_back")

    await callback.message.edit_text(
        "🧠 ПЕРЕКЛЮЧЕНИЕ\n\n"
        "Сделай прямо сейчас:\n"
        "— выйди из помещения\n"
        "— начни движение\n"
        "— заговори с кем-то\n\n"
        "Тяга усиливается в бездействии.",
        reply_markup=kb.as_markup()
    )


# --- НАЗАД В МЕНЮ ТЕХНИК ---
@dp.callback_query(F.data == "tech_back")
async def tech_back(callback: types.CallbackQuery):
    await callback.answer()

    kb = InlineKeyboardBuilder()
    kb.button(text="🫁 Дыхание", callback_data="tech_breath")
    kb.button(text="🧊 Холод", callback_data="tech_cold")
    kb.button(text="🌍 Заземление", callback_data="tech_ground")
    kb.button(text="🧠 Переключение", callback_data="tech_switch")
    kb.adjust(1)

    await callback.message.edit_text(
        "Выбери технику 👇",
        reply_markup=kb.as_markup()
    )

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
