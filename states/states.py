from aiogram.dispatcher.filters.state import StatesGroup, State

class AllStates(StatesGroup):
    waiting_for_email = State()
    waiting_for_password = State()
    waiting_for_period = State()
    waiting_for_subject = State()
    waiting_for_student = State()