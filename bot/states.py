from aiogram.fsm.state import State, StatesGroup

class UserStates(StatesGroup):
    LANGUAGE_SELECT = State()
    MAIN_MENU = State()
    BOOKING_PACKAGE = State()
    BOOKING_PAYMENT = State()
    WAIT_FOR_PAYMENT = State()
    CONSULT_MODE = State()
