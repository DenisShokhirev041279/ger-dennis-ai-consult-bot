from aiogram.fsm.state import State, StatesGroup

class UserStates(StatesGroup):
    LANGUAGE_SELECT = State()
    MAIN_MENU = State()
    BOOKING_PACKAGE = State()
    BOOKING_PAYMENT = State()
    WAIT_FOR_PAYMENT = State()
    CONSULT_MODE = State()
    REF_PHOTO_COLLECT = State()

    # CV Tools States
    CV_BRAND_AUDIT = State()
    CV_PRODUCT_PHOTO = State()
    CV_SOCIAL_KIT = State()
    CV_AI_VIDEO = State()
