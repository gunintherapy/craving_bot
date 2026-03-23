import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --------- TOKEN ---------
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("❌ TOKEN не найден! Добавь его в Render → Environment")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()


# --------- FSM ---------
class Form(StatesGroup):
    craving = State()
    craving_level = State()
    trigger = State()
    emotions = State()
    thoughts = State()
    control = State()
    action = State()


# --------- START ---------
@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.button(text="Начать чек", callback_data="start_check")

    await message.answer(
        "Это бот для отслеживания тяги.\n\n"
        "Займет 1–2 минуты.\n"
        "Поможет не сорваться.",
        reply_markup=kb.as_markup()
    )


# --------- START CHECK ---------
@dp.callback_query(F.data == "start_check")
async def start_check(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    kb = InlineKeyboardBuilder()
    for txt in ["нет", "немного", "нормально тянет", "очень сильно"]:
        kb.button(text=txt, callback_data=f"craving_{txt}")

    await callback.message.answer("Тебя сейчас тянет?", reply_markup=kb.as_markup())
    await state.set_state(Form.craving)


# --------- CRAVING ---------
@dp.callback_query(F.data.startswith("craving_"))
async def craving(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    value = callback.data.replace("craving_", "")
    await state.update_data(craving=value)

    kb = InlineKeyboardBuilder()
    for i in range(11):
        kb.button(text=str(i), callback_data=f"level_{i}")

    await callback.message.answer("Насколько сильно? (0–10)", reply_markup=kb.as_markup())
    await state.set_state(Form.craving_level)


# --------- LEVEL ---------
@dp.callback_query(F.data.startswith("level_"))
async def craving_level(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    value = int(callback.data.replace("level_", ""))
    await state.update_data(level=value)

    kb = InlineKeyboardBuilder()
    for o in ["стресс", "скука", "устал", "одиночество", "привычка", "не понимаю"]:
        kb.button(text=o, callback_data=f"trigger_{o}")

    await callback.message.answer("Что это запустило?", reply_markup=kb.as_markup())
    await state.set_state(Form.trigger)


# --------- TRIGGER ---------
@dp.callback_query(F.data.startswith("trigger_"))
async def trigger(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    value = callback.data.replace("trigger_", "")
    await state.update_data(trigger=value)

    kb = InlineKeyboardBuilder()
    for o in ["тревожно", "пусто", "злюсь", "грусть", "раздражение", "нормально"]:
        kb.button(text=o, callback_data=f"emotion_{o}")

    await callback.message.answer("Что внутри сейчас?", reply_markup=kb.as_markup())
    await state.set_state(Form.emotions)


# --------- EMOTIONS ---------
@dp.callback_query(F.data.startswith("emotion_"))
async def emotions(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    value = callback.data.replace("emotion_", "")
    await state.update_data(emotions=value)

    kb = InlineKeyboardBuilder()
    for o in ["нет", "иногда мелькают", "крутятся постоянно"]:
        kb.button(text=o, callback_data=f"thought_{o}")

    await callback.message.answer("Мысли сорваться есть?", reply_markup=kb.as_markup())
    await state.set_state(Form.thoughts)


# --------- THOUGHTS ---------
@dp.callback_query(F.data.startswith("thought_"))
async def thoughts(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    value = callback.data.replace("thought_", "")
    await state.update_data(thoughts=value)

    kb = InlineKeyboardBuilder()
    for o in ["контролирую", "шатает", "почти не контролирую"]:
        kb.button(text=o, callback_data=f"control_{o}")

    await callback.message.answer("Ты контролируешь ситуацию?", reply_markup=kb.as_markup())
    await state.set_state(Form.control)


# --------- CONTROL ---------
@dp.callback_query(F.data.startswith("control_"))
async def control(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    value = callback.data.replace("control_", "")
    await state.update_data(control=value)

    kb = InlineKeyboardBuilder()
    for o in ["выйду", "отвлекусь", "позвоню", "подышу", "ничего"]:
        kb.button(text=o, callback_data=f"action_{o}")

    await callback.message.answer("Что сделаешь сейчас?", reply_markup=kb.as_markup())
    await state.set_state(Form.action)


# --------- ACTION ---------
@dp.callback_query(F.data.startswith("action_"))
async def action(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    value = callback.data.replace("action_", "")
    await state.update_data(action=value)

    data = await state.get_data()

    level = data.get("level")
    thoughts = data.get("thoughts")
    control_val = data.get("control")
    trigger_val = data.get("trigger")

    if level >= 7 or thoughts == "крутятся постоянно" or control_val == "почти не контролирую":
        risk = "high"
    elif level >= 4:
        risk = "medium"
    else:
        risk = "low"

    trigger_text = ""
    if trigger_val == "стресс":
        trigger_text = "\nПохоже, тебя задел стресс."
    elif trigger_val == "одиночество":
        trigger_text = "\nСейчас тебе не хватает контакта."
    elif trigger_val == "скука":
        trigger_text = "\nЭто больше про пустоту."

    if risk == "low":
        text = "Ты сейчас в контроле. Продолжай."
    elif risk == "medium":
        text = "Важно остановиться. Смени место, отвлекись."
    else:
        text = "СТОП. Тебя несёт. Срочно выйди или позвони кому-то."

    if data.get("action") == "ничего":
        text += "\n\nЕсли ничего не делать — станет хуже."

    await callback.message.answer(text + trigger_text)
    await state.clear()


# --------- RUN ---------
async def main():
    print("🚀 Бот запущен")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
