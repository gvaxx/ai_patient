
import streamlit as st
from pathlib import Path
import os
import random
from dotenv import load_dotenv

from src.domain.models import Session
from src.domain.services import TestService, EvaluationService
from src.data.case_loader import CaseLoader
from src.data.test_templates import TestTemplates
from src.ai.llm_provider import LLMClient

# Загрузка .env
load_dotenv()

# Настройка страницы
st.set_page_config(
    page_title="Виртуальный Пациент",
    page_icon="🏥",
    layout="wide"
)


@st.cache_resource
def init_services():
    """
    Инициализирует все сервисы один раз.
    
    Returns:
        dict с ключами:
        - "llm": LLMClient
        - "cases": Dict[str, ClinicalCase] 
        - "test_service": TestService
        - "evaluation_service": EvaluationService
    """
    # 1. Создать LLM клиент из .env
    llm = LLMClient.from_env()
    
    # 2. Загрузить все случаи
    case_loader = CaseLoader(cases_dir=Path("data/cases"))
    cases = case_loader.load_all()
    
    # 3. Создать сервисы
    test_service = TestService()
    evaluation_service = EvaluationService(llm_client=llm)
    
    return {
        "llm": llm,
        "cases": cases,
        "test_service": test_service,
        "evaluation_service": evaluation_service
    }


# Обработка ошибок инициализации
try:
    services = init_services()
except ValueError as e:
    st.error(f"❌ Ошибка конфигурации: {e}")
    st.info("💡 Проверьте файл .env и убедитесь что API ключ указан правильно")
    st.stop()
except Exception as e:
    st.error(f"❌ Ошибка загрузки: {e}")
    st.stop()


# Инициализация session state
if 'session' not in st.session_state:
    st.session_state.session = None  # Текущая сессия (Session объект)
    st.session_state.active_tab = "cases"  # cases, interview, tests, diagnosis


def start_new_session(case_id: str):
    """Начинает новую сессию с выбранным случаем"""
    case = services["cases"][case_id]
    st.session_state.session = Session(case=case)
    st.session_state.active_tab = "interview"


def start_random_session():
    """Начинает новую сессию со случайным случаем"""
    case_ids = list(services["cases"].keys())
    random_case_id = random.choice(case_ids)
    start_new_session(random_case_id)


def add_to_conversation(role: str, content: str):
    """Добавляет сообщение в историю"""
    st.session_state.session.conversation.append({
        "role": role,
        "content": content
    })


with st.sidebar:
    st.title("🏥 Виртуальный Пациент")
    
    if st.session_state.session is None:
        # Если сессии нет - показываем подсказку
        st.info("👈 Выберите клинический случай")
    
    else:
        # Если сессия активна - показываем информацию о пациенте
        case = st.session_state.session.case
        
        # Навигация по вкладкам
        st.subheader("Навигация")
        
        # Кнопка "Опрос"
        if st.button(
            "💬 Опрос пациента", 
            key="nav_interview",
            use_container_width=True,
            type="primary" if st.session_state.active_tab == "interview" else "secondary"
        ):
            st.session_state.active_tab = "interview"
            st.rerun()
        
        
        # Кнопка "Диагноз"
        if st.button(
            "📋 Диагноз и лечение", 
            key="nav_diagnosis",
            use_container_width=True,
            type="primary" if st.session_state.active_tab == "diagnosis" else "secondary"
        ):
            st.session_state.active_tab = "diagnosis"
            st.rerun()
        
        st.write("---")
        
        # Кнопка "Новый случай"
        if st.button("🔄 Начать новый случай", use_container_width=True):
            st.session_state.session = None
            st.session_state.active_tab = "cases"
            st.rerun()


# === ОСНОВНОЙ КОНТЕНТ ===

if st.session_state.session is None:
    # Экран выбора случая
    st.header("Выберите клинический случай")
    
    # Кнопка случайного выбора сверху
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button(
            "🎲 Случайный случай", 
            use_container_width=True,
            type="primary",
            help="Начать работу со случайно выбранным случаем"
        ):
            start_random_session()
            st.rerun()
    
    st.write("---")
    st.write("Или выберите конкретный случай из списка ниже:")
    
    # Показываем все доступные случаи
    cases = services["cases"]
    
    # Располагаем в две колонки
    cols = st.columns(2)
    
    for idx, (case_id, case) in enumerate(cases.items()):
        with cols[idx % 2]:
            with st.container(border=True):
                st.subheader(case.title)
                
                # Информация о пациенте
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Пациент:** {case.patient.name}")
                    st.write(f"**Возраст:** {case.patient.age} лет")
                
                # Кнопка начать (выравнивание по двум колонкам)
                if st.button(
                    "▶️ Начать сессию", 
                    key=f"start_{case_id}",
                    use_container_width=True,
                    type="secondary"
                ):
                    start_new_session(case_id)
                    st.rerun()

elif st.session_state.active_tab == "interview":
    st.header("💬 Опрос пациента")
    
    session = st.session_state.session
    case = session.case
    
    # Верхняя панель с данными пациента и жалобой
    with st.container(border=True):
        # Жалоба крупно сверху
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Пациент", case.patient.name)
        with col2:
            st.metric("Возраст", f"{case.patient.age} лет")
    
    st.write("")
    
    # Основной контент в двух колонках
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("💬 Диалог с пациентом")
        
        # Контейнер для чата с фиксированной высотой
        chat_container = st.container(height=500)
        
        with chat_container:
            # Показываем всю историю разговора
            for msg in session.conversation:
                if msg['role'] == 'doctor':
                    st.chat_message("user", avatar="👨‍⚕️").write(msg['content'])
                elif msg['role'] == 'patient':
                    st.chat_message("assistant", avatar="🤒").write(msg['content'])
                elif msg['role'] == 'system':
                    st.chat_message("assistant", avatar="📊").write(msg['content'])
        
        # Поле ввода вопроса
        question = st.chat_input("Задайте вопрос пациенту...")
        
        if question:
            # Добавляем вопрос врача
            add_to_conversation("doctor", question)
            
            # Показываем спиннер пока генерируется ответ
            with st.spinner("Пациент думает..."):
                # Формируем контекст пациента
                patient_context = {
                    "name": case.patient.name,
                    "age": case.patient.age,
                    "gender": case.patient.gender,
                    "chief_complaint": case.chief_complaint,
                    "history": case.history,
                    "symptoms": case.symptoms
                }
                
                # Получаем ответ от LLM
                response = services["llm"].get_patient_response(
                    question=question,
                    patient_context=patient_context,
                    conversation_history=session.conversation
                )
            
            # Добавляем ответ пациента
            add_to_conversation("patient", response)
                

            # Перезагружаем страницу для отображения нового сообщения
            st.rerun()
    
    with col2:
        # Предварительный диагноз
        st.subheader("🔍 Предварительный диагноз")
        
        # Проверяем, есть ли уже предварительный диагноз
        if session.preliminary_diagnosis is None:
            # Форма для ввода предварительного диагноза
            with st.form("preliminary_diagnosis_form"):
                preliminary_diagnosis = st.text_area(
                    "Введите ваш предварительный диагноз:",
                    placeholder="Например: Острый аппендицит, Пневмония, Гастрит...",
                    height=80
                )
                
                submitted = st.form_submit_button("Оценить", type="primary")
                
                if submitted and preliminary_diagnosis.strip():
                    with st.spinner("Оцениваем..."):
                        # Оцениваем предварительный диагноз
                        evaluation = services["evaluation_service"].evaluate_preliminary_diagnosis(
                            submitted=preliminary_diagnosis.strip(),
                            correct=case.correct_preliminary_diagnosis,
                            case=case
                        )
                        
                        # Сохраняем результаты
                        session.preliminary_diagnosis = preliminary_diagnosis.strip()
                        session.preliminary_diagnosis_score = evaluation.get("score", 1)
                        session.preliminary_diagnosis_feedback = evaluation.get("feedback", "")
                        
                        st.rerun()
        
        else:
            # Показываем уже введенный диагноз и оценку
            st.info(session.preliminary_diagnosis)
            score = session.preliminary_diagnosis_score or 0
            if score > 6:
                st.success(f"✅ Оценка: {score}/10")
            else:
                st.error(f"❌ Оценка: {score}/10")
                # Кнопка для пересдачи предварительного диагноза
                if st.button("🔄 Пересдать предварительный диагноз", key="retake_preliminary", type="secondary"):
                    session.preliminary_diagnosis = None
                    session.preliminary_diagnosis_score = None
                    session.preliminary_diagnosis_feedback = None
                    st.rerun()
        
        st.write("---")
        
        # Назначение анализов
        st.subheader("🧪 Назначение анализов")
        
        # Проверяем, разблокированы ли анализы
        score = session.preliminary_diagnosis_score or 0
        tests_unlocked = score > 6
        
        if not tests_unlocked:
            st.warning("🔒 Лабораторные и инструментальные исследования заблокированы")
            st.info("💡 Для разблокировки получите оценку предварительного диагноза больше 6 баллов")
        else:
            st.success("🔓 Все анализы разблокированы!")
        
        # Получаем список всех доступных тестов
        available_tests = TestTemplates.get_all_tests()
        
        # Группируем по категориям
        lab_tests = [t for t in available_tests if t["category"] == "laboratory"]
        exam_tests = [t for t in available_tests if t["category"] == "examination"]
        imaging_tests = [t for t in available_tests if t["category"] == "imaging"]
        
        # Клинические обследования (всегда доступны)
        with st.expander("🩺 Клинические обследования", ):
            exam_options = {t["name"]: t["test_id"] for t in exam_tests if t["test_id"] not in session.ordered_tests}
            selected_exam_name = st.selectbox(
                "Выберите обследование",
                options=["— не выбрано —"] + list(exam_options.keys()),
                key="select_exam_test",
            )
            if st.button("Провести обследование", key="run_exam_test", disabled=selected_exam_name == "— не выбрано —", use_container_width=True):
                test_id = exam_options[selected_exam_name]
                with st.spinner("Получение результатов..."):
                    result = services["test_service"].get_test_results(test_id=test_id, case=case)
                    session.test_results[test_id] = result
                    if test_id not in session.ordered_tests:
                        session.ordered_tests.append(test_id)
                    
                    # Добавляем результат в чат
                    result_text = f"🩺 **Результат обследования: {result.name}**\n\n"
                    if "description" in result.results:
                        result_text += result.results["description"]
                    else:
                        # Создаем красивую таблицу
                        result_text += "| Показатель | Значение | Норма | Статус |\n"
                        result_text += "|------------|----------|-------|--------|\n"
                        for param_id, param_data in result.results.items():
                            status_icon = "✅ Норма" if param_data["status"] == "normal" else "⚠️ Отклонение"
                            normal_range = param_data.get("reference", "—")
                            result_text += f"| {param_data['name']} | {param_data['value']} {param_data['unit']} | {normal_range} | {status_icon} |\n"
                    
                    add_to_conversation("system", result_text)
                st.success(f"✅ Результаты добавлены: {result.name}")
                st.rerun()
        
        # Лабораторные анализы
        lab_title = "🔬 Лабораторные анализы" + (" 🔒" if not tests_unlocked else "")
        with st.expander(lab_title, ):
            lab_options = {t["name"]: t["test_id"] for t in lab_tests if t["test_id"] not in session.ordered_tests}
            selected_lab_name = st.selectbox(
                "Выберите анализ",
                options=["— не выбрано —"] + list(lab_options.keys()),
                key="select_lab_test",
                disabled=not tests_unlocked
            )
            if st.button("Провести анализ", key="run_lab_test", disabled=selected_lab_name == "— не выбрано —" or not tests_unlocked, use_container_width=True):
                test_id = lab_options[selected_lab_name]
                with st.spinner("Получение результатов..."):
                    result = services["test_service"].get_test_results(test_id=test_id, case=case)
                    session.test_results[test_id] = result
                    if test_id not in session.ordered_tests:
                        session.ordered_tests.append(test_id)
                    
                    # Добавляем результат в чат
                    result_text = f"📊 **Результат анализа: {result.name}**\n\n"
                    if "description" in result.results:
                        result_text += result.results["description"]
                    else:
                        # Создаем красивую таблицу
                        result_text += "| Показатель | Значение | Норма | Статус |\n"
                        result_text += "|------------|----------|-------|--------|\n"
                        for param_id, param_data in result.results.items():
                            status_icon = "✅ Норма" if param_data["status"] == "normal" else "⚠️ Отклонение"
                            normal_range = param_data.get("reference", "—")
                            result_text += f"| {param_data['name']} | {param_data['value']} {param_data['unit']} | {normal_range} | {status_icon} |\n"
                    
                    add_to_conversation("system", result_text)
                st.success(f"✅ Результаты добавлены: {result.name}")
                st.rerun()
        
        # Инструментальные исследования
        imaging_title = "📷 Инструментальные исследования" + (" 🔒" if not tests_unlocked else "")
        with st.expander(imaging_title, ):
            imaging_options = {t["name"]: t["test_id"] for t in imaging_tests if t["test_id"] not in session.ordered_tests}
            selected_img_name = st.selectbox(
                "Выберите исследование",
                options=["— не выбрано —"] + list(imaging_options.keys()),
                key="select_imaging_test",
                disabled=not tests_unlocked
            )
            if st.button("Провести исследование", key="run_imaging_test", disabled=selected_img_name == "— не выбрано —" or not tests_unlocked, use_container_width=True):
                test_id = imaging_options[selected_img_name]
                with st.spinner("Получение результатов..."):
                    result = services["test_service"].get_test_results(test_id=test_id, case=case)
                    session.test_results[test_id] = result
                    if test_id not in session.ordered_tests:
                        session.ordered_tests.append(test_id)
                    
                    # Добавляем результат в чат
                    result_text = f"📷 **Результат исследования: {result.name}**\n\n"
                    if "description" in result.results:
                        result_text += result.results["description"]
                    else:
                        # Создаем красивую таблицу
                        result_text += "| Показатель | Значение | Норма | Статус |\n"
                        result_text += "|------------|----------|-------|--------|\n"
                        for param_id, param_data in result.results.items():
                            status_icon = "✅ Норма" if param_data["status"] == "normal" else "⚠️ Отклонение"
                            normal_range = param_data.get("reference", "—")
                            result_text += f"| {param_data['name']} | {param_data['value']} {param_data['unit']} | {normal_range} | {status_icon} |\n"
                    
                    add_to_conversation("system", result_text)
                st.success(f"✅ Результаты добавлены: {result.name}")
                st.rerun()
        
        # Список проведенных тестов
        if session.test_results:
            st.write("---")
            st.write("**Проведенные тесты:**")
            for test_id, result in session.test_results.items():
                st.write(f"✓ {result.name}")
    
    st.write("---")
    
    # Кнопка перехода внизу
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Проверяем, прошел ли предварительный диагноз
        score = session.preliminary_diagnosis_score or 0
        if score > 6:
            if st.button("Далее: Диагноз →", use_container_width=True, type="primary"):
                st.session_state.active_tab = "diagnosis"
                st.rerun()
        else:
            if session.preliminary_diagnosis is None:
                st.warning("⚠️ Сначала поставьте предварительный диагноз")
            else:
                st.warning("⚠️ Для продолжения необходимо получить оценку предварительного диагноза больше 6 баллов")
            if st.button("Далее: Диагноз →", use_container_width=True, disabled=True):
                pass

elif st.session_state.active_tab == "diagnosis":
    st.header("📋 Диагноз и план лечения")
    
    session = st.session_state.session
    case = session.case
    
    # Предварительный диагноз на самом верху
    if session.preliminary_diagnosis:
        score = session.preliminary_diagnosis_score or 0
        col1, col2 = st.columns([3, 1])
        with col1:
            if score > 6:
                st.success(f"🔍 **Предварительный диагноз:** {session.preliminary_diagnosis}")
            else:
                st.error(f"🔍 **Предварительный диагноз:** {session.preliminary_diagnosis}")
        with col2:
            if score <= 6:
                if st.button("🔄 Пересдать", key="retake_preliminary_diagnosis", type="secondary"):
                    session.preliminary_diagnosis = None
                    session.preliminary_diagnosis_score = None
                    session.preliminary_diagnosis_feedback = None
                    st.rerun()
        st.write("---")
    
    # Краткая сводка: опрос
    with st.expander("🧾 Сводка опроса", expanded=False):
        st.subheader("💬 Опрос (последние сообщения)")
        if session.conversation:
            for msg in session.conversation[-6:]:
                if msg.get('role') in ['doctor', 'patient']:
                    role_icon = "👨‍⚕️" if msg.get('role') == 'doctor' else "🤒"
                    st.write(f"{role_icon} {msg.get('content','')}")
        else:
            st.write("Нет данных опроса")
    
    # Проведенные анализы (отдельно от сводки)
    if session.test_results:
        st.subheader("🧪 Проведенные обследования")
        
        # Группируем анализы по категориям
        lab_results = []
        exam_results = []
        imaging_results = []
        
        for tid, res in session.test_results.items():
            # Определяем категорию по test_id или имени
            if any(keyword in res.name.lower() for keyword in ['анализ', 'кровь', 'моча', 'биохимия', 'общий']):
                lab_results.append(res)
            elif any(keyword in res.name.lower() for keyword in ['осмотр', 'пальпация', 'аускультация', 'перкуссия']):
                exam_results.append(res)
            else:
                imaging_results.append(res)
        
        if lab_results:
            st.write("**🔬 Лабораторные анализы:**")
            for res in lab_results:
                with st.expander(f"📄 {res.name}", expanded=False):
                    if "description" in res.results:
                        st.write(res.results["description"])
                    else:
                        # Формируем данные для таблицы
                        table_data = []
                        for param_id, param_data in res.results.items():
                            status_icon = "✅" if param_data["status"] == "normal" else "⚠️"
                            row = {
                                "Показатель": param_data["name"],
                                "Значение": f"{param_data['value']} {param_data['unit']}",
                                "Норма": param_data.get("reference", "—"),
                                "Статус": f"{status_icon} {'Норма' if param_data['status'] == 'normal' else 'Отклонение'}"
                            }
                            table_data.append(row)
                        
                        # Показываем компактную таблицу
                        if table_data:
                            st.dataframe(
                                table_data, 
                                use_container_width=True, 
                                hide_index=True,
                                column_config={
                                    "Показатель": st.column_config.TextColumn("Показатель", width="medium"),
                                    "Значение": st.column_config.TextColumn("Значение", width="small"),
                                    "Норма": st.column_config.TextColumn("Норма", width="small"),
                                    "Статус": st.column_config.TextColumn("Статус", width="small")
                                }
                            )
        
        if exam_results:
            st.write("**🩺 Клинические обследования:**")
            for res in exam_results:
                with st.expander(f"📄 {res.name}", expanded=False):
                    if "description" in res.results:
                        st.write(res.results["description"])
                    else:
                        # Формируем данные для таблицы
                        table_data = []
                        for param_id, param_data in res.results.items():
                            status_icon = "✅" if param_data["status"] == "normal" else "⚠️"
                            row = {
                                "Показатель": param_data["name"],
                                "Значение": f"{param_data['value']} {param_data['unit']}",
                                "Норма": param_data.get("reference", "—"),
                                "Статус": f"{status_icon} {'Норма' if param_data['status'] == 'normal' else 'Отклонение'}"
                            }
                            table_data.append(row)
                        
                        # Показываем компактную таблицу
                        if table_data:
                            st.dataframe(
                                table_data, 
                                use_container_width=True, 
                                hide_index=True,
                                column_config={
                                    "Показатель": st.column_config.TextColumn("Показатель", width="medium"),
                                    "Значение": st.column_config.TextColumn("Значение", width="small"),
                                    "Норма": st.column_config.TextColumn("Норма", width="small"),
                                    "Статус": st.column_config.TextColumn("Статус", width="small")
                                }
                            )
        
        if imaging_results:
            st.write("**📷 Инструментальные исследования:**")
            for res in imaging_results:
                with st.expander(f"📄 {res.name}", expanded=False):
                    if "description" in res.results:
                        st.write(res.results["description"])
                    else:
                        # Формируем данные для таблицы
                        table_data = []
                        for param_id, param_data in res.results.items():
                            status_icon = "✅" if param_data["status"] == "normal" else "⚠️"
                            row = {
                                "Показатель": param_data["name"],
                                "Значение": f"{param_data['value']} {param_data['unit']}",
                                "Норма": param_data.get("reference", "—"),
                                "Статус": f"{status_icon} {'Норма' if param_data['status'] == 'normal' else 'Отклонение'}"
                            }
                            table_data.append(row)
                        
                        # Показываем компактную таблицу
                        if table_data:
                            st.dataframe(
                                table_data, 
                                use_container_width=True, 
                                hide_index=True,
                                column_config={
                                    "Показатель": st.column_config.TextColumn("Показатель", width="medium"),
                                    "Значение": st.column_config.TextColumn("Значение", width="small"),
                                    "Норма": st.column_config.TextColumn("Норма", width="small"),
                                    "Статус": st.column_config.TextColumn("Статус", width="small")
                                }
                            )
    
    # Если оценка уже есть - показываем только результаты
    if session.evaluation is not None:
        # === ЭКРАН РЕЗУЛЬТАТОВ ===
        st.subheader("📈 Результаты оценки")
        
        # Общие баллы
        total_score = session.evaluation["total_score"]
        max_score = session.evaluation["max_score"]
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "Предв. диагноз",
                f"{session.evaluation['preliminary']['score']}/10"
            )
        
        with col2:
            st.metric(
                "Сопутств. забол.",
                f"{session.evaluation['comorbidities']['score']}/10"
            )
        
        with col3:
            st.metric(
                "Финальный диагноз",
                f"{session.evaluation['final_diagnosis']['score']}/20"
            )
        
        with col4:
            st.metric(
                "План лечения",
                f"{session.evaluation['final_treatment']['score']}/20"
            )
        
        with col5:
            # Определяем цвет по баллам
            percentage = (total_score / max_score) * 100
            if percentage >= 80:
                color_icon = "🟢"
            elif percentage >= 60:
                color_icon = "🟡"
            else:
                color_icon = "🔴"
            
            st.metric(
                "Итого",
                f"{color_icon} {total_score}/{max_score}"
            )
        
        st.write("---")
        
        # Детальная обратная связь в четырех колонках
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.subheader("🔍 Предв. диагноз")
            status_icons = {"correct": "✅", "partial": "⚠️", "incorrect": "❌"}
            status_icon = status_icons.get(session.evaluation['preliminary']['status'], "❓")
            st.write(f"{status_icon} {session.evaluation['preliminary']['feedback']}")
        
        with col2:
            st.subheader("🏥 Сопутств. забол.")
            status_icon = status_icons.get(session.evaluation['comorbidities']['status'], "❓")
            st.write(f"{status_icon} {session.evaluation['comorbidities']['feedback']}")
        
        with col3:
            st.subheader("🔍 Финальный диагноз")
            status_icon = status_icons.get(session.evaluation['final_diagnosis']['status'], "❓")
            st.write(f"{status_icon} {session.evaluation['final_diagnosis']['feedback']}")
        
        with col4:
            st.subheader("💊 План лечения")
            st.write(session.evaluation['final_treatment']['feedback'])
        
        st.write("---")
        
        # Правильные ответы
        with st.expander("📚 Правильные ответы", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Предварительный диагноз:**")
                st.write(case.correct_preliminary_diagnosis)
                st.write("**Сопутствующие заболевания:**")
                st.write(case.correct_comorbidities)
                st.write("**Финальный диагноз:**")
                st.write(case.correct_diagnosis)
            
            with col2:
                st.write("**План лечения:**")
                for med in case.correct_treatment.get("medications", []):
                    st.write(f"- {med['name']} {med['dose']} {med['route']} {med['frequency']}")
                for proc in case.correct_treatment.get("procedures", []):
                    st.write(f"- {proc}")
        
        st.write("---")
        
        # Расшифровка оценки
        with st.expander("📊 Расшифровка оценки", expanded=False):
            st.write("**Система оценки:**")
            st.write("- **Предварительный диагноз:** 1-10 баллов (оценка на основе клинической картины)")
            st.write("- **Сопутствующие заболевания:** 1-10 баллов (релевантность указанных заболеваний)")
            st.write("- **Финальный диагноз:** 1-20 баллов (точность окончательного диагноза)")
            st.write("- **План лечения:** 1-20 баллов (правильность медикаментов и процедур)")
            st.write("")
            st.write("**Общий балл:** максимум 60 баллов")
            st.write("- 🟢 80%+ (48+ баллов): Отлично")
            st.write("- 🟡 60-79% (36-47 баллов): Хорошо")
            st.write("- 🔴 <60% (<36 баллов): Требует улучшения")
        
        st.write("---")
        
        # Кнопки действий
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("🔄 Попробовать ещё раз", use_container_width=True):
                session.submitted_diagnosis = None
                session.submitted_treatment = None
                session.evaluation = None
                st.rerun()
        
        with col2:
            if st.button("🏠 Выбрать другой случай", use_container_width=True):
                st.session_state.session = None
                st.session_state.active_tab = "cases"
                st.rerun()
        
        with col3:
            if st.button("🎲 Случайный случай", use_container_width=True):
                start_random_session()
                st.rerun()
    
    else:
        # === ЭКРАН ВВОДА ДИАГНОЗА И ЛЕЧЕНИЯ ===
        
        # Две колонки: диагноз + сопутствующие, план лечения
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔍 Диагноз")
            
            diagnosis_input = st.text_input(
                "Поставьте диагноз:",
                key="diagnosis_input",
                placeholder="Введите предполагаемый диагноз",
                help="Введите предполагаемый диагноз"
            )
            
            comorbidities = st.text_area(
                "Сопутствующие заболевания:",
                placeholder="Например:\nАртериальная гипертензия\nСахарный диабет 2 типа",
                height=100,
                key="comorbidities",
                help="По одному заболеванию на строку"
            )
        
        with col2:
            st.subheader("💊 План лечения")
            
            treatment_plan = st.text_area(
                "План лечения:",
                placeholder="Введите медикаменты и процедуры\nНапример: Цефтриаксон 1г в/в 2 раза в день, Аппендэктомия, Инфузионная терапия",
                height=200,
                key="treatment_plan",
                help="Включает медикаменты, процедуры и операции"
            )
        
        st.write("---")
        
        # Кнопка отправки
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                "✅ Отправить на оценку", 
                type="primary", 
                use_container_width=True
            ):
                # Валидация
                if not diagnosis_input:
                    st.error("❌ Необходимо поставить диагноз!")
                elif not treatment_plan:
                    st.error("❌ Необходимо назначить план лечения!")
                else:
                    # Сохраняем ответы
                    session.submitted_diagnosis = diagnosis_input
                    session.submitted_treatment = {
                        "treatment_plan": [t.strip() for t in treatment_plan.split('\n') if t.strip()],
                        "comorbidities": [c.strip() for c in comorbidities.split('\n') if c.strip()]
                    }
                    
                    # Оцениваем
                    with st.spinner("⏳ Оценка ваших ответов..."):
                        # Асинхронная оценка всех компонентов
                        import asyncio
                        import concurrent.futures
                        
                        def run_evaluations():
                            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                                # Запускаем все оценки параллельно
                                futures = {
                                    'preliminary': executor.submit(
                                        services["evaluation_service"].evaluate_preliminary_diagnosis,
                                        session.preliminary_diagnosis or "",
                                        case.correct_preliminary_diagnosis,
                                        case
                                    ),
                                    'comorbidities': executor.submit(
                                        services["evaluation_service"].evaluate_comorbidities,
                                        '\n'.join(session.submitted_treatment.get("comorbidities", [])),
                                        case.correct_comorbidities,
                                        case
                                    ),
                                    'final_diagnosis': executor.submit(
                                        services["evaluation_service"].evaluate_final_diagnosis,
                                        diagnosis_input,
                                        case.correct_diagnosis,
                                        case
                                    ),
                                    'final_treatment': executor.submit(
                                        services["evaluation_service"].evaluate_final_treatment,
                                        '\n'.join(session.submitted_treatment.get("treatment_plan", [])),
                                        case.correct_treatment,
                                        case
                                    )
                                }
                                
                                # Получаем результаты
                                results = {}
                                for key, future in futures.items():
                                    try:
                                        results[key] = future.result(timeout=30)
                                    except Exception as e:
                                        results[key] = {"score": 1, "feedback": f"Ошибка оценки: {str(e)}"}
                                
                                return results
                        
                        # Запускаем оценки
                        evaluation_results = run_evaluations()
                        
                        # Вычисляем общий балл
                        total_score = (
                            evaluation_results['preliminary']['score'] +  # 1-10
                            evaluation_results['comorbidities']['score'] +  # 1-10
                            evaluation_results['final_diagnosis']['score'] +  # 1-20
                            evaluation_results['final_treatment']['score']  # 1-20
                        )  # Максимум 60 баллов
                        
                        session.evaluation = {
                            "preliminary": evaluation_results['preliminary'],
                            "comorbidities": evaluation_results['comorbidities'],
                            "final_diagnosis": evaluation_results['final_diagnosis'],
                            "final_treatment": evaluation_results['final_treatment'],
                            "total_score": total_score,
                            "max_score": 60
                        }
                    
                    st.rerun()
