import asyncio
import logging
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# -----------------------
# ТОКЕН
# -----------------------
TOKEN = os.getenv("TOKEN")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# -----------------------
# ВЕБ-СЕРВЕР (для Render)
# -----------------------
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot is running')

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()

threading.Thread(target=run_server).start()

# -----------------------
# Состояния
# -----------------------
class QuizStates(StatesGroup):
    question_idx = State()
    yes_count = State()

# -----------------------
# Вопросы
# -----------------------
QUESTIONS = [
    "Он/она не может остановиться, если начал(а) употреблять?",
    "Были обещания 'завязать', но всё повторялось?",
    "После употребления говорит: 'это последний раз'?",
    "Есть проблемы с работой или учёбой из-за этого?",
    "Были долги или финансовые проблемы?",
    "Деньги уходят на употребление, а не на жизнь?",
    "Становится агрессивным(ой) или резко меняется настроение?",
    "В трезвом состоянии один человек, в употреблении — другой?",
    "Отрицает проблему или говорит 'всё под контролем'?",
    "В семье конфликты из-за этого?",
    "Ты пытался(ась) контролировать, но не получается?",
    "Ты живёшь в постоянной тревоге?",
    "Праздники невозможны без алкоголя/употребления?",
    "Круг общения связан с употреблением?",
    "Ситуация со временем ухудшается?",
    "Ты боишься, что дальше будет хуже?",
    "Ты думал(а), что нужна помощь извне?",
    "Ты чувствуешь, что сам(а) не справляешься?"
]

# -----------------------
# Кнопки Да / Нет
# -----------------------
def get_yes_no_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Да", callback_data="yes")
    kb.button(text="❌ Нет", callback_data="no")
    kb.adjust(2)
    return kb.as_markup()

# -----------------------
# /start
# -----------------------
@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await state.clear()

    kb = InlineKeyboardBuilder()
    kb.button(text="📊 Пройти тест", callback_data="start_quiz")
    kb.button(text="💬 Написать специалисту", url="https://t.me/voshodkrsk")
    kb.adjust(1)

    await message.answer(
        "Ты пытаешься помочь близкому.\n\n"
        "Уговариваешь, контролируешь, веришь, что он справится сам…\n\n"
        "Но внутри уже есть тревога:\n\n"
        "👉 А вдруг всё зашло слишком далеко?\n"
        "👉 А если уже нужна реабилитация?\n\n"
        "Пройди тест и посмотри честно, что происходит.",
        reply_markup=kb.as_markup()
    )

# -----------------------
# Старт теста
# -----------------------
@dp.callback_query(F.data == "start_quiz")
async def start_quiz(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(QuizStates.question_idx)
    await state.update_data(question_idx=0, yes_count=0)

    await callback.message.answer(
        "Я задам тебе 18 вопросов.\n\n"
        "Отвечай честно:\n"
        "👉 Да или Нет\n\n"
        "Это не диагноз, но покажет реальную картину.\n\nПоехали."
    )

    await callback.message.answer(
        f"Вопрос 1:\n\n{QUESTIONS[0]}",
        reply_markup=get_yes_no_keyboard()
    )

    await callback.answer()

# -----------------------
# Ответы
# -----------------------
@dp.callback_query(F.data.in_(["yes", "no"]))
async def process_answer(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    q_idx = data.get("question_idx", 0)
    yes_count = data.get("yes_count", 0)

    if callback.data == "yes":
        yes_count += 1

    next_q_idx = q_idx + 1

    if next_q_idx < len(QUESTIONS):
        await state.update_data(question_idx=next_q_idx, yes_count=yes_count)

        await callback.message.edit_text(
            f"Вопрос {next_q_idx + 1}:\n\n{QUESTIONS[next_q_idx]}",
            reply_markup=get_yes_no_keyboard()
        )
    else:
        result_text = get_result_text(yes_count)

        kb = InlineKeyboardBuilder()
        kb.button(text="💬 Разобрать ситуацию", url="https://t.me/voshodkrsk")
        kb.button(text="📊 Пройти тест снова", callback_data="start_quiz")
        kb.adjust(1)

        await callback.message.edit_text(
            f"Тест завершен.\n\n"
            f"Количество ответов 'Да': {yes_count}\n\n"
            f"{result_text}\n\n"
            f"👉 Это не просто тест.\n"
            f"Это реальная картина.\n\n"
            f"Напиши мне:\n👉 Нужна помощь\n\n"
            f"Я скажу честно, нужна ли реабилитация.",
            reply_markup=kb.as_markup()
        )

        await state.clear()

    await callback.answer()

# -----------------------
# Результат
# -----------------------
def get_result_text(yes_count):
    if yes_count <= 4:
        return (
            "🟢 Пока ситуация не критическая.\n\n"
            "Но уже есть тревожные сигналы.\n"
            "Важно не игнорировать их."
        )
    elif yes_count <= 9:
        return (
            "🟡 Это уже формирующаяся зависимость.\n\n"
            "Само это не проходит.\n"
            "Дальше будет сложнее."
        )
    else:
        return (
            "🔴 Это уже зависимость.\n\n"
            "Сам человек не может остановиться.\n"
            "И здесь нужна реабилитация."
        )

# -----------------------
# Запуск
# -----------------------
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
