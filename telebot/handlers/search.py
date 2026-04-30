from aiogram import Router, types, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.api_client import ApiClient
from keyboards.main_menu import get_main_menu

router = Router()


class SearchState(StatesGroup):
    main_menu = State()
    waiting_for_keyword = State()
    waiting_for_area = State()
    waiting_for_area_skills = State()
    waiting_for_skills = State()


@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    first_name = message.from_user.first_name or "пользователь"

    text = f"Привет, {first_name}!\n\nЯ помогу тебе проанализировать требования к вакансиям с HH.ru."

    await message.answer(
        text=text,
        reply_markup=get_main_menu()
    )

    await state.set_state(SearchState.main_menu)

@router.message(StateFilter(SearchState.main_menu))
async def main_menu_handler(message: types.Message, state: FSMContext):
    text = message.text.strip()

    if text == "🔍 Новый поиск":
        await message.answer("Введите регион для поиска вакансий:")
        await state.set_state(SearchState.waiting_for_area)

    elif text == "🔎 Поиск по навыкам":
        await message.answer("Введите регион для поиска по навыкам:")
        await state.set_state(SearchState.waiting_for_area_skills)

    elif text == "ℹ️ О боте":
        await message.answer("Это бот для анализа вакансий с HH.ru.\n\nОн извлекает ключевые навыки и показывает статистику.")
        await state.set_state(SearchState.main_menu)

    else:
        await message.answer("Пожалуйста, используйте кнопки меню 👇", reply_markup=get_main_menu())

@router.message(StateFilter(SearchState.waiting_for_area))
async def process_area(message: types.Message, state: FSMContext):
    area_name = message.text.strip()
    
    if area_name in ["ℹ️ О боте", "🔍 Новый поиск", "🔎 Поиск по навыкам"]:
        await message.answer("Произошла ошибка при обработке запроса. Выберите команду в меню ещё раз.")
        await state.set_state(SearchState.main_menu)
        return


    if not area_name:
        await message.answer("Название региона не может быть пустым. Введите заново:")
        return

    api_client = ApiClient()

    area_id = await api_client.check_area(area_name=area_name)

    if area_id is None:
        await message.answer(
            f"Регион «{area_name}» не найден.\n\n"
            "Попробуйте ввести другое название (например: Москва, Санкт-Петербург, Россия, Красноярск):"
        )
        return

    await state.update_data(area_name=area_name, area_id=area_id)

    await message.answer(
        f"✅ Регион «{area_name}» найден (ID: {area_id})\n\n"
        "Теперь введите ключевое слово или фразу для поиска:"
    )

    await state.set_state(SearchState.waiting_for_keyword)

@router.message(StateFilter(SearchState.waiting_for_keyword))
async def process_keyword(message: types.Message, state: FSMContext):
    keyword = message.text.strip()

    if not keyword:
        await message.answer("Ключевое слово не может быть пустым.")
        await state.set_state(SearchState.main_menu)
        return
    
    if keyword in ["ℹ️ О боте", "🔍 Новый поиск", "🔎 Поиск по навыкам"]:
        await message.answer("Произошла ошибка при обработке запроса. Выберите команду в меню ещё раз.")
        await state.set_state(SearchState.main_menu)
        return

    tg_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    api_client = ApiClient()
    await message.answer("⏳ Ищу и анализирую вакансии...")

    state_data = await state.get_data()
    area_name = state_data.get("area_name")
    area_id = state_data.get("area_id")
    
    data = await api_client.get_data(
        keyword=keyword,
        tg_id=tg_id,
        username=username,
        first_name=first_name,
        area_id=area_id
    )


    if data and isinstance(data, dict):
        top_skills = data.get("top_skills", [])
        request_count = data.get("request_count", 0)
        avg_salary = data.get("average_salary")

        if top_skills:
            reply_text = f"🔍 Топ навыков по запросу «{keyword}» в регионе {area_name}:\n\n"
            
            for i, skill in enumerate(top_skills, 1):
                skill_name = skill.get("skill_name", "—")
                count = skill.get("count", 0)
                reply_text += f"{i}. {skill_name} — {count} раз\n"

            if isinstance(request_count, int) and request_count > 1:
                reply_text += f"\n👥 Этот запрос уже делали {request_count} раз" 

            vacancies = data.get("vacancies_parsed", 0)
            extracted = data.get("skills_extracted", 0)
            unique_skills = data.get("unique_skills_count", 0)

            if avg_salary is not None:
                reply_text += f"\n💰 Средняя зарплата: {avg_salary} ₽"

            reply_text += f"\n\n📊 Обработано вакансий: {vacancies} | Извлечено навыков: {extracted} | Уникальных навыков: {unique_skills}"
        else:
            reply_text = f"По запросу «{keyword}» не удалось найти релевантных навыков."
    else:
        reply_text = "❌ Не удалось получить данные от сервера. Попробуйте позже."

    await message.answer(
        reply_text,
        reply_markup=get_main_menu()
    )

    await state.set_state(SearchState.main_menu)

@router.message(StateFilter(SearchState.waiting_for_area_skills))
async def process_area_for_skills(message: types.Message, state: FSMContext):
    area_name = message.text.strip()
    
    if area_name in ["ℹ️ О боте", "🔍 Новый поиск", "🔎 Поиск по навыкам"]:
        await message.answer("Произошла ошибка при обработке запроса. Выберите команду в меню ещё раз.")
        await state.set_state(SearchState.main_menu)
        return

    if not area_name:
        await message.answer("Название региона не может быть пустым.")
        return

    api_client = ApiClient()
    area_id = await api_client.check_area(area_name)

    if area_id is None:
        await message.answer(
            f"❌ Регион «{area_name}» не найден.\n\n"
            "Попробуйте ввести другое название (Москва, Санкт-Петербург, Красноярск и т.д.):"
        )
        return

    await state.update_data(area_id=area_id, area_name=area_name)

    await message.answer(
        f"✅ Регион «{area_name}» найден (ID: {area_id})\n\n"
        "Теперь введите навыки через запятую:\n"
        "Пример: `Python, Django, PostgreSQL, Docker, Git`"
    )
    await state.set_state(SearchState.waiting_for_skills)

@router.message(StateFilter(SearchState.waiting_for_skills))
async def process_skills_search(message: types.Message, state: FSMContext):
    skills_text = message.text.strip()
    
    if skills_text in ["ℹ️ О боте", "🔍 Новый поиск", "🔎 Поиск по навыкам"]:
        await message.answer("Произошла ошибка при обработке запроса. Выберите команду в меню ещё раз.")
        await state.set_state(SearchState.main_menu)
        return

    if not skills_text:
        await message.answer("Введите хотя бы один навык.")
        return

    skills_list = [s.strip() for s in skills_text.split(",") if s.strip()]

    data = await state.get_data()
    area_id = data.get("area_id")
    area_name = data.get("area_name")

    api_client = ApiClient()
    await message.answer("⏳ Ищу вакансии с этими навыками...")

    result = await api_client.search_by_skills(skills=skills_list, area_id=area_id)

    if not result or not result.get("success"):
        await message.answer("❌ Не удалось выполнить поиск. Попробуйте позже.")
        await state.clear()
        return

    vacancies = result.get("vacancies", [])
    total_found = result.get("total_found", 0)
    avg_salary = result.get("average_salary")

    if total_found == 0:
        await message.answer(f"В регионе «{area_name}» не найдено вакансий, где есть **все** указанные навыки.")
    else:
        text = f"🔍 Найдено **{total_found}** вакансий в регионе «{area_name}»\n\n"

        if avg_salary:
            text += f"💰 Средняя зарплата: **{avg_salary} ₽**\n\n"

        text += "**🏆 Топ-10 по зарплате:**\n\n"

        for i, vac in enumerate(vacancies[:10], 1):
            salary = f"{vac.get('salary')} ₽" if vac.get('salary') else "З/п не указана"
            text += f"{i}. [{vac['name']}]({vac['url']}) — {salary}\n"

        await message.answer(
            text, 
            parse_mode="Markdown", 
            disable_web_page_preview=True
        )

    await state.set_state(SearchState.main_menu)