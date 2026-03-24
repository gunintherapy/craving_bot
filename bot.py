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

# --- КОНФИГУРАЦИЯ ---
TOKEN = os.getenv("TOKEN")
PORT = int(os.getenv("PORT", 8000))

if not TOKEN:
    logging.error("❌ ОШИБКА: Переменная TOKEN не установлена!")
    exit(1)

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- КНОПКИ ГЛАВНОГО МЕНЮ ---
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🆘 SOS"), KeyboardButton(text="📝 Дневник")],
        [KeyboardButton(text="🧘 Техники"), KeyboardButton(text="📊 Прогресс")]
    ],
    resize_keyboard=True
)

# --- СОСТОЯНИЯ (FSM) ---
class Form(StatesGroup):
    craving = State()
    level = State()
    trigger = State()
    emotion = State()
    thoughts = State()
    control = State()
    action = State()

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! 👋 Я твой инструмент поддержки в трезвости.\n"
        "Используй меню ниже, когда почувствуешь импульс или для ежедневной проверки.",
        reply_markup=main_kb
    )

# --- ЛОГИКА ДНЕВНИКА ---

@dp.message(F.text == "📝 Дневник")
async def diary_start(message: types.Message, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.button(text="Нет", callback_data="c_0")
    kb.button(text="Лёгкая", callback_data="c_1")
    kb.button(text="Есть", callback_data="c_2")
    kb.button(text="Сильная", callback_data="c_3")
    kb.adjust(2)
    await message.answer("Ты сейчас испытываешь тягу?", reply_markup=kb.as_markup())
    await state.set_state(Form.craving)

@dp.callback_query(F.data.startswith("c_"))
async def craving_branch(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    val = int(callback.data[2:])
    await state.update_data(craving=val)

    if val == 0:
        kb = InlineKeyboardBuilder()
        for r in ["Спокойствие", "Занят делом", "Люди рядом", "Всё норм"]:
            kb.button(text=r, callback_data=f"res_{r}")
        kb.adjust(2)
        await callback.message.edit_text(
            "✅ Это отличные новости! Тяги нет.\n"
            "Что помогает тебе оставаться в этом состоянии?", 
            reply_markup=kb.as_markup()
        )
        return

    kb = InlineKeyboardBuilder()
    for i in range(11):
        kb.button(text=str(i), callback_data=f"l_{i}")
    kb.adjust(5)
    await callback.message.edit_text("Оцени силу тяги от 0 до 10:", reply_markup=kb.as_markup())
    await state.set_state(Form.level)

@dp.callback_query(F.data.startswith("res_"))
async def resource_finish(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text("💪 Зафиксировано. Трезвость — это твой выбор. Продолжай в том же духе!")
    await state.clear()

@dp.callback_query(F.data.startswith("l_"))
async def level_step(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(level=int(callback.data[2:]))
    kb = InlineKeyboardBuilder()
    for t in ["стресс", "конфликт", "одиночество", "усталость", "скука"]:
        kb.button(text=t, callback_data=f"t_{t}")
    kb.adjust(2)
    await callback.message.edit_text("Что спровоцировало тягу (триггер)?", reply_markup=kb.as_markup())
    await state.set_state(Form.trigger)

@dp.callback_query(F.data.startswith("t_"))
async def trigger_step(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(trigger=callback.data[2:])
    kb = InlineKeyboardBuilder()
    for e in ["тревога", "злость", "грусть", "пустота", "стыд"]:
        kb.button(text=e, callback_data=f"e_{e}")
    kb.adjust(2)
    await callback.message.edit_text("Какую эмоцию ты проживаешь?", reply_markup=kb.as_markup())
    await state.set_state(Form.emotion)

@dp.callback_query(F.data.startswith("e_"))
async def emotion_step(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(emotion=callback.data[2:])
    kb = InlineKeyboardBuilder()
    for th in ["нет", "иногда", "постоянно"]:
        kb.button(text=th, callback_data=f"th_{th}")
    kb.adjust(3)
    await callback.message.edit_text("Как часто возникают мысли о срыве?", reply_markup=kb.as_markup())
    await state.set_state(Form.thoughts)

@dp.callback_query(F.data.startswith("th_"))
async def thoughts_step(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(thoughts=callback.data[3:])
    kb = InlineKeyboardBuilder()
    for c in ["да", "шатает", "почти нет"]:
        kb.button(text=c, callback_data=f"ctrl_{c}")
    kb.adjust(3)
    await callback.message.edit_text("Ты чувствуешь контроль над ситуацией?", reply_markup=kb.as_markup())
    await state.set_state(Form.control)

@dp.callback_query(F.data.startswith("ctrl_"))
async def control_step(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(control=callback.data[5:])
    kb = InlineKeyboardBuilder()
    for a in ["позвоню", "выйду", "подышу", "отвлекусь", "ничего"]:
        kb.button(text=a, callback_data=f"a_{a}")
    kb.adjust(2)
    await callback.message.edit_text("Твоё действие прямо сейчас?", reply_markup=kb.as_markup())
    await state.set_state(Form.action)

@dp.callback_query(F.data.startswith("a_"))
async def final_analysis(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    level = data.get("level", 0)
    
    if level >= 7 or data.get("thoughts") == "постоянно" or data.get("control") == "почти нет":
        text = "🆘 **КРИТИЧЕСКАЯ ТЯГА!**\n\nНемедленно примени план спасения:\n1. Умойся ледяной водой.\n2. Выйди из текущей обстановки.\n3. Позвони наставнику или доверенному лицу прямо сейчас!"
    elif level >= 4:
        text = "⚠️ **ВНИМАНИЕ: ЖЕЛТАЯ ЗОНА.**\n\nТяга растет. Сделай паузу 15 минут. Выпей воды, подыши. Помни: это состояние пройдет."
    else:
        text = "✅ **БЕЗОПАСНЫЙ УРОВЕНЬ.**\n\nТяга есть, но она не управляет тобой. Ты справляешься. Можешь вернуться к своим делам."

    await callback.message.edit_text(text, parse_mode="Markdown")
    await state.clear()

# --- КНОПКИ БЫСТРОГО ДОСТУПА ---

@dp.message(F.text == "🆘 SOS")
async def sos_action(message: types.Message):
    await message.answer("🆘 **ПЛАН ЭКСТРЕННОЙ ПОМОЩИ:**\n- Остановись (HALT: ты не голоден, не зол, не одинок, не устал?)\n- Умойся холодной водой.\n- Сделай 10 глубоких вдохов.\n- Позвони человеку из группы поддержки.")

@dp.message(F.text == "🧘 Техники")
async def tech_action(message: types.Message):
    await message.answer("🧘 **ТЕХНИКИ ДЛЯ ТЕБЯ:**\n1. **Дыхание 4-4-4-4**: вдох, задержка, выдох, задержка.\n2. **Заземление**: найди глазами 5 красных предметов.\n3. **Серфинг тяги**: представь тягу как волну, которая неизбежно спадет.")

@dp.message(F.text == "📊 Прогресс")
async def prog_action(message: types.Message):
    await message.answer("📊 Статистика будет доступна после подключения базы данных. Ты на верном пути!")

# --- СЕРВЕР ДЛЯ RAILWAY/HEALTH CHECK ---

async def handle_ping(request):
    return web.Response(text="Bot is alive", status=200)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запускаем веб-сервер и бота параллельно
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    
    await site.start()
    logging.info(f"🚀 Сервер на порту {PORT}")
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Остановка бота")
