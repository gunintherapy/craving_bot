Вот мой новый полный код. Скажи мне что думаешь 
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

# -------- ГЛАВНОЕ МЕНЮ --------
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🆘 SOS"), KeyboardButton(text="📝 Дневник")],
        [KeyboardButton(text="🧘 Техники"), KeyboardButton(text="📊 Прогресс")]
    ],
    resize_keyboard=True
)

# -------- СОСТОЯНИЯ (FSM) --------
class Form(StatesGroup):
    craving = State()
    level = State()
    trigger = State()
    emotion = State()
    thoughts = State()
    control = State()
    action = State()

# -------- ОБРАБОТЧИКИ КОМАНД --------

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Привет! 👋 Я — твой дневник тяги.\n"
        "Выбери действие ниже 👇",
        reply_markup=main_kb
    )

@dp.message(F.text == "📝 Дневник")
async def diary(message: types.Message, state: FSMContext):
    kb = InlineKeyboardBuilder()
    for txt in ["нет", "немного", "средне", "сильно"]:
        kb.button(text=txt, callback_data=f"c_{txt}")
    kb.adjust(2)
    await message.answer("Тебя сейчас тянет?", reply_markup=kb.as_markup())
    await state.set_state(Form.craving)

@dp.callback_query(F.data.startswith("c_"))
async def craving_step(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(craving=callback.data[2:])
    kb = InlineKeyboardBuilder()
    for i in range(11):
        kb.button(text=str(i), callback_data=f"l_{i}")
    kb.adjust(5)
    await callback.message.answer("Насколько сильно? (0–10)", reply_markup=kb.as_markup())
    await state.set_state(Form.level)

@dp.callback_query(F.data.startswith("l_"))
async def level_step(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(level=int(callback.data[2:]))
    kb = InlineKeyboardBuilder()
    for t in ["стресс", "скука", "одиночество", "усталость", "конфликт"]:
        kb.button(text=t, callback_data=f"t_{t}")
    kb.adjust(2)
    await callback.message.answer("Что это запустило?", reply_markup=kb.as_markup())
    await state.set_state(Form.trigger)

@dp.callback_query(F.data.startswith("t_"))
async def trigger_step(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(trigger=callback.data[2:])
    kb = InlineKeyboardBuilder()
    for e in ["тревога", "злость", "грусть", "пустота", "стыд"]:
        kb.button(text=e, callback_data=f"e_{e}")
    kb.adjust(2)
    await callback.message.answer("Что ты сейчас чувствуешь?", reply_markup=kb.as_markup())
    await state.set_state(Form.emotion)

@dp.callback_query(F.data.startswith("e_"))
async def emotion_step(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(emotion=callback.data[2:])
    kb = InlineKeyboardBuilder()
    for th in ["нет", "мелькают", "постоянно"]:
        kb.button(text=th, callback_data=f"th_{th}")
    kb.adjust(3)
    await callback.message.answer("Есть мысли сорваться?", reply_markup=kb.as_markup())
    await state.set_state(Form.thoughts)

@dp.callback_query(F.data.startswith("th_"))
async def thoughts_step(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(thoughts=callback.data[3:])
    kb = InlineKeyboardBuilder()
    for c in ["да", "шатает", "почти нет"]:
        kb.button(text=c, callback_data=f"ctrl_{c}")
    kb.adjust(3)
    await callback.message.answer("Ты контролируешь ситуацию?", reply_markup=kb.as_markup())
    await state.set_state(Form.control)

@dp.callback_query(F.data.startswith("ctrl_"))
async def control_step(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(control=callback.data[5:])
    kb = InlineKeyboardBuilder()
    for a in ["позвоню", "выйду", "подышу", "отвлекусь", "ничего"]:
        kb.button(text=a, callback_data=f"a_{a}")
    kb.adjust(2)
    await callback.message.answer("Что сделаешь прямо сейчас?", reply_markup=kb.as_markup())
    await state.set_state(Form.action)

@dp.callback_query(F.data.startswith("a_"))
async def action_step(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(action=callback.data[2:])
    data = await state.get_data()
    
    level = data.get("level", 0)
    thoughts = data.get("thoughts")
    control = data.get("control")
    trigger = data.get("trigger")

    if level >= 7 or thoughts == "постоянно" or control == "почти нет":
        text = "🆘 СТОП! ОПАСНОСТЬ.\n\nТебя сейчас несёт. Сделай прямо сейчас:\n— выйди\n— холодная вода\n— позвони кому-то"
    elif level >= 4:
        text = f"⚠️ Внимание.\n\nТриггер: {trigger}\n\nСделай паузу:\n— смени место\n— выпей воды"
    else:
        text = "✅ Ты в контроле.\n\nТяга есть, но она не управляет тобой."

    await callback.message.answer(text)
    await state.clear()

@dp.message(F.text == "🆘 SOS")
async def sos_handler(message: types.Message):
    await message.answer("🆘 СТОП! Смени место, умойся водой или позвони близким прямо сейчас!")

@dp.message(F.text == "🧘 Техники")
async def tech_handler(message: types.Message):
    await message.answer("🧘 Техники:\n1. Дыхание 4-4-4\n2. Холодная вода\n3. Смена обстановки")

@dp.message(F.text == "📊 Прогресс")
async def progress_handler(message: types.Message):
    await message.answer("📊 Статистика в разработке.")

# -------- СЕРВЕРНАЯ ЧАСТЬ --------

async def handle(request):
    return web.Response(text="Bot is running", status=200)

async def start_webserver():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logging.info(f"✅ Web server started on port {PORT}")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    # Запускаем и сервер, и бота одновременно
    await asyncio.gather(
        start_webserver(),
        dp.start_polling(bot)
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен")

