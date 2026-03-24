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
    raise ValueError("❌ TOKEN не найден!")

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
    message_id = State()  # для редактирования сообщения теста

# -------- START --------
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Привет! 👋 Я — твой дневник тяги.\n\n"
        "Я помогу тебе не сорваться в момент импульса.\n\n"
        "Выбери действие 👇",
        reply_markup=main_kb
    )

# -------- ДНЕВНИК --------
@dp.message(F.text == "📝 Дневник")
async def diary(message: types.Message, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.button(text="Нет", callback_data="c_0")
    kb.button(text="Лёгкая", callback_data="c_1")
    kb.button(text="Есть", callback_data="c_2")
    kb.button(text="Сильная", callback_data="c_3")
    kb.adjust(2)
    msg = await message.answer("Ты сейчас испытываешь тягу? (шаг 1/7)", reply_markup=kb.as_markup())
    await state.set_state(Form.craving)
    await state.update_data(message_id=msg.message_id)

# -------- HELPER: редактируем сообщение --------
async def edit_test_message(callback: types.CallbackQuery, text: str, kb: InlineKeyboardBuilder, state: FSMContext):
    data = await state.get_data()
    msg_id = data.get("message_id")
    if msg_id:
        await bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=msg_id,
            text=text,
            reply_markup=kb.as_markup()
        )

# -------- CRAVING --------
@dp.callback_query(F.data.startswith("c_"))
async def craving_step(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    craving_val = int(callback.data[2:])
    await state.update_data(craving=craving_val)

    if craving_val == 0:  # если тяги нет
        kb = InlineKeyboardBuilder()
        kb.button(text="Спокойствие", callback_data="res_спокойствие")
        kb.button(text="Занят делом", callback_data="res_дело")
        kb.button(text="Рядом люди", callback_data="res_люди")
        kb.button(text="Просто норм", callback_data="res_норм")
        kb.adjust(1)
        await edit_test_message(callback, "✅ Сейчас тяги нет.\nВыбери, что помогает тебе оставаться в спокойствии:", kb, state)
        return

    kb = InlineKeyboardBuilder()
    for i in range(11):
        kb.button(text=str(i), callback_data=f"l_{i}")
    kb.adjust(5)
    await edit_test_message(callback, "Насколько сильная тяга? (0–10, шаг 2/7)", kb, state)
    await state.set_state(Form.level)

# -------- РЕСУРС --------
@dp.callback_query(F.data.startswith("res_"))
async def resource_step(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text("👍 Отлично! Запомни это состояние — оно тебе поможет в сложный момент.")
    await state.clear()

# -------- LEVEL --------
@dp.callback_query(F.data.startswith("l_"))
async def level_step(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    level = int(callback.data[2:])
    await state.update_data(level=level)

    kb = InlineKeyboardBuilder()
    for t in ["стресс", "конфликт", "одиночество", "усталость", "скука"]:
        kb.button(text=t, callback_data=f"t_{t}")
    kb.adjust(2)
    await edit_test_message(callback, "Что запустило это состояние? (шаг 3/7)", kb, state)
    await state.set_state(Form.trigger)

# -------- TRIGGER --------
@dp.callback_query(F.data.startswith("t_"))
async def trigger_step(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(trigger=callback.data[2:])

    kb = InlineKeyboardBuilder()
    for e in ["тревога", "злость", "грусть", "пустота", "стыд"]:
        kb.button(text=e, callback_data=f"e_{e}")
    kb.adjust(2)
    await edit_test_message(callback, "Что ты сейчас чувствуешь? (шаг 4/7)", kb, state)
    await state.set_state(Form.emotion)

# -------- EMOTION --------
@dp.callback_query(F.data.startswith("e_"))
async def emotion_step(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(emotion=callback.data[2:])

    kb = InlineKeyboardBuilder()
    for th in ["нет", "иногда", "постоянно"]:
        kb.button(text=th, callback_data=f"th_{th}")
    kb.adjust(3)
    await edit_test_message(callback, "Есть мысли сорваться? (шаг 5/7)", kb, state)
    await state.set_state(Form.thoughts)

# -------- THOUGHTS --------
@dp.callback_query(F.data.startswith("th_"))
async def thoughts_step(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(thoughts=callback.data[3:])

    kb = InlineKeyboardBuilder()
    for c in ["да", "шатает", "почти нет"]:
        kb.button(text=c, callback_data=f"ctrl_{c}")
    kb.adjust(3)
    await edit_test_message(callback, "Ты контролируешь ситуацию? (шаг 6/7)", kb, state)
    await state.set_state(Form.control)

# -------- CONTROL --------
@dp.callback_query(F.data.startswith("ctrl_"))
async def control_step(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(control=callback.data[5:])

    kb = InlineKeyboardBuilder()
    for a in ["позвоню", "выйду", "подышу", "отвлекусь", "ничего"]:
        kb.button(text=a, callback_data=f"a_{a}")
    kb.adjust(2)
    await edit_test_message(callback, "Что сделаешь прямо сейчас? (шаг 7/7)", kb, state)
    await state.set_state(Form.action)

# -------- ACTION --------
@dp.callback_query(F.data.startswith("a_"))
async def action_step(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(action=callback.data[2:])
    data = await state.get_data()

    level = data.get("level", 0)
    thoughts = data.get("thoughts")
    control = data.get("control")
    action = data.get("action")

    # ---- логика риска ----
    if level >= 7 or thoughts == "постоянно" or control == "почти нет":
        text = "🆘 СТОП! ОПАСНОСТЬ.\n\nТебя сейчас несёт.\n— выйди\n— холодная вода\n— позвони кому-то"
    elif level >= 4:
        text = "⚠️ Внимание.\n\nСостояние нестабильное.\n— смени место\n— выпей воды"
    else:
        text = "✅ Ты в контроле.\nТяга есть, но она не управляет тобой."

    if action == "ничего":
        text += "\n\nЕсли ничего не делать — станет хуже."

    await callback.message.edit_text(text)
    await state.clear()

# -------- SOS --------
@dp.message(F.text == "🆘 SOS")
async def sos_handler(message: types.Message):
    await message.answer(
        "🆘 СТОП!\n\nСейчас важно действовать:\n— выйди из места\n— холодная вода\n— позвони кому-то"
    )

# -------- ТЕХНИКИ --------
@dp.message(F.text == "🧘 Техники")
async def tech_handler(message: types.Message):
    await message.answer("🧘 Техники:\n1. Дыхание 4-4-4\n2. Холодная вода\n3. Смена обстановки")

# -------- ПРОГРЕСС --------
@dp.message(F.text == "📊 Прогресс")
async def progress_handler(message: types.Message):
    await message.answer("📊 Прогресс скоро появится.")

# -------- WEB --------
async def handle(request):
    return web.Response(text="Bot is running")

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
