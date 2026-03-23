import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ---------- TOKEN ----------
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("❌ TOKEN не найден! Добавь его в Render → Environment")

# ---------- LOGGING ----------
logging.basicConfig(level=logging.INFO)

# ---------- BOT ----------
bot = Bot(token=TOKEN)
dp = Dispatcher()


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
async def start(message: types.Message, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.button(text="Начать чек", callback_data="start")

    await message.answer(
        "Это бот для отслеживания тяги.\n\n"
        "Займет 1–2 минуты.\n"
        "Поможет не сорваться.",
        reply_markup=kb.as_markup()
    )


# ---------- START CHECK ----------
@dp.callback_query(F.data == "start")
async def start_check(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    kb = InlineKeyboardBuilder()
    for txt in ["нет", "немного", "средне", "сильно"]:
        kb.button(text=txt, callback_data=f"c_{txt}")

    await callback.message.answer("Тебя сейчас тянет?", reply_markup=kb.as_markup())
    await state.set_state(Form.craving)


# ---------- CRAVING ----------
@dp.callback_query(F.data.startswith("c_"))
async def craving(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    val = callback.data[2:]
    await state.update_data(craving=val)

    kb = InlineKeyboardBuilder()
    for i in range(11):
        kb.button(text=str(i), callback_data=f"l_{i}")

    await callback.message.answer("Оцени по шкале 0–10", reply_markup=kb.as_markup())
    await state.set_state(Form.level)


# ---------- LEVEL ----------
@dp.callback_query(F.data.startswith("l_"))
async def level(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    val = int(callback.data[2:])
    await state.update_data(level=val)

    kb = InlineKeyboardBuilder()
    for t in ["стресс", "скука", "одиночество", "устал"]:
        kb.button(text=t, callback_data=f"t_{t}")

    await callback.message.answer("Что это запустило?", reply_markup=kb.as_markup())
    await state.set_state(Form.trigger)


# ---------- TRIGGER ----------
@dp.callback_query(F.data.startswith("t_"))
async def trigger(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    val = callback.data[2:]
    await state.update_data(trigger=val)

    kb = InlineKeyboardBuilder()
    for e in ["тревога", "пусто", "злюсь", "грусть"]:
        kb.button(text=e, callback_data=f"e_{e}")

    await callback.message.answer("Что чувствуешь?", reply_markup=kb.as_markup())
    await state.set_state(Form.emotion)


# ---------- EMOTION ----------
@dp.callback_query(F.data.startswith("e_"))
async def emotion(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    val = callback.data[2:]
    await state.update_data(emotion=val)

    kb = InlineKeyboardBuilder()
    for th in ["нет", "есть немного", "сильные"]:
        kb.button(text=th, callback_data=f"th_{th}")

    await callback.message.answer("Мысли сорваться есть?", reply_markup=kb.as_markup())
    await state.set_state(Form.thoughts)


# ---------- THOUGHTS ----------
@dp.callback_query(F.data.startswith("th_"))
async def thoughts(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    val = callback.data[3:]
    await state.update_data(thoughts=val)

    kb = InlineKeyboardBuilder()
    for c in ["контроль есть", "шатает", "нет контроля"]:
        kb.button(text=c, callback_data=f"ctrl_{c}")

    await callback.message.answer("Контроль есть?", reply_markup=kb.as_markup())
    await state.set_state(Form.control)


# ---------- CONTROL ----------
@dp.callback_query(F.data.startswith("ctrl_"))
async def control(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    val = callback.data[5:]
    await state.update_data(control=val)

    kb = InlineKeyboardBuilder()
    for a in ["выйду", "отвлекусь", "позвоню", "ничего"]:
        kb.button(text=a, callback_data=f"a_{a}")

    await callback.message.answer("Что сделаешь?", reply_markup=kb.as_markup())
    await state.set_state(Form.action)


# ---------- ACTION ----------
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
        result = "⚠️ Высокий риск срыва.\nСрочно меняй обстановку."
    elif level >= 4:
        result = "⚠️ Средний риск.\nЛучше переключиться."
    else:
        result = "✅ Ты держишь ситуацию."

    if val == "ничего":
        result += "\n\nЕсли ничего не делать — станет хуже."

    await callback.message.answer(result)

    await state.clear()


# ---------- MAIN ----------
async def main():
    print("🚀 Бот запущен")

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        print("❌ Ошибка:", e)
    finally:
        await bot.session.close()


# ---------- RUN ----------
if __name__ == "__main__":
    asyncio.run(main())
