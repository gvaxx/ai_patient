
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
        
        st.success(f"**Пациент:** {case.patient.name}")
        st.write(f"**Возраст:** {case.patient.age} лет")
        st.write(f"**Пол:** {'Мужской' if case.patient.gender == 'male' else 'Женский'}")
        
        st.write("---")
        
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
                with col2:
                    st.write(f"**Пол:** {'М' if case.patient.gender == 'male' else 'Ж'}")
                    if case.patient.occupation:
                        st.write(f"**Профессия:** {case.patient.occupation}")
                
                # Жалоба
                st.write(f"**Жалоба:** {case.chief_complaint}")
                
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
        st.markdown(f"**Жалоба:** _{case.chief_complaint}_")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Пациент", case.patient.name)
        with col2:
            st.metric("Возраст", f"{case.patient.age} лет")
        with col3:
            st.metric("Пол", "М" if case.patient.gender == "male" else "Ж")
    
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
        # Назначение анализов
        st.subheader("🧪 Назначение анализов")
        
        # Получаем список всех доступных тестов
        available_tests = TestTemplates.get_all_tests()
        
        # Группируем по категориям
        lab_tests = [t for t in available_tests if t["category"] == "laboratory"]
        exam_tests = [t for t in available_tests if t["category"] == "examination"]
        imaging_tests = [t for t in available_tests if t["category"] == "imaging"]
        
        # Лабораторные анализы
        with st.expander("🔬 Лабораторные анализы", expanded=True):
            lab_options = {t["name"]: t["test_id"] for t in lab_tests if t["test_id"] not in session.ordered_tests}
            selected_lab_name = st.selectbox(
                "Выберите анализ",
                options=["— не выбрано —"] + list(lab_options.keys()),
                key="select_lab_test",
            )
            if st.button("Провести анализ", key="run_lab_test", disabled=selected_lab_name == "— не выбрано —", use_container_width=True):
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
        
        # Клинические обследования
        with st.expander("🩺 Клинические обследования", expanded=True):
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
        
        # Инструментальные исследования
        with st.expander("📷 Инструментальные исследования", expanded=True):
            imaging_options = {t["name"]: t["test_id"] for t in imaging_tests if t["test_id"] not in session.ordered_tests}
            selected_img_name = st.selectbox(
                "Выберите исследование",
                options=["— не выбрано —"] + list(imaging_options.keys()),
                key="select_imaging_test",
            )
            if st.button("Провести исследование", key="run_imaging_test", disabled=selected_img_name == "— не выбрано —", use_container_width=True):
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
        if st.button("Далее: Диагноз →", use_container_width=True, type="primary"):
            st.session_state.active_tab = "diagnosis"
            st.rerun()

elif st.session_state.active_tab == "diagnosis":
    st.header("📋 Диагноз и план лечения")
    
    session = st.session_state.session
    case = session.case
    
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
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Диагноз",
                f"{session.evaluation['diagnosis']['score']}/100"
            )
        
        with col2:
            st.metric(
                "Лечение",
                f"{session.evaluation['treatment']['score']}/100"
            )
        
        with col3:
            # Определяем цвет по баллам
            if total_score >= 80:
                color_icon = "🟢"
            elif total_score >= 60:
                color_icon = "🟡"
            else:
                color_icon = "🔴"
            
            st.metric(
                "Итого",
                f"{color_icon} {total_score}/100"
            )
        
        st.write("---")
        
        # Детальная обратная связь в двух колонках
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔍 Обратная связь по диагнозу")
            
            # Иконка по статусу
            status_icons = {
                "correct": "✅",
                "partial": "⚠️",
                "incorrect": "❌"
            }
            status_icon = status_icons.get(
                session.evaluation['diagnosis']['status'], 
                "❓"
            )
            
            st.write(f"{status_icon} {session.evaluation['diagnosis']['feedback']}")
            
            # Показываем правильный ответ
            with st.expander("📚 Правильный диагноз"):
                st.write(f"**Диагноз:** {case.correct_diagnosis}")
                st.write(f"**МКБ-10:** {case.correct_icd10}")
        
        with col2:
            st.subheader("💊 Обратная связь по лечению")
            
            st.write(session.evaluation['treatment']['feedback'])
            
            # Показываем правильный ответ
            with st.expander("📚 Правильное лечение"):
                st.write("**Медикаменты:**")
                for med in case.correct_treatment.get("medications", []):
                    st.write(f"- {med['name']} {med['dose']} {med['route']} {med['frequency']}")
                
                st.write("\n**Процедуры:**")
                for proc in case.correct_treatment.get("procedures", []):
                    st.write(f"- {proc}")
        
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
        
        # Две колонки: диагноз слева, лечение справа
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔍 Диагноз")
            
            diagnosis_input = st.text_input(
                "Поставьте диагноз:",
                key="diagnosis_input",
                placeholder="Введите предполагаемый диагноз",
                help="Введите предполагаемый диагноз"
            )
            
            icd10_input = st.text_input(
                "Код МКБ-10 (опционально):",
                key="icd10_input",
                placeholder="Например: K35.8",
                help="Можно оставить пустым"
            )
        
        with col2:
            st.subheader("💊 План лечения")
            
            medications = st.text_area(
                "Медикаментозная терапия:",
                placeholder="Введите каждый препарат с новой строки.\nНапример:\nЦефтриаксон 1г в/в 2 раза в день\nМетронидазол 500мг в/в 3 раза в день",
                height=100,
                key="medications",
                help="По одному препарату на строку с дозировкой и режимом"
            )
            
            procedures = st.text_area(
                "Процедуры и операции:",
                placeholder="Введите каждую процедуру с новой строки.\nНапример:\nАппендэктомия\nИнфузионная терапия",
                height=100,
                key="procedures",
                help="По одной процедуре на строку"
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
                elif not medications and not procedures:
                    st.error("❌ Необходимо назначить хотя бы что-то из лечения!")
                else:
                    # Сохраняем ответы
                    session.submitted_diagnosis = diagnosis_input
                    session.submitted_treatment = {
                        "medications": [m.strip() for m in medications.split('\n') if m.strip()],
                        "procedures": [p.strip() for p in procedures.split('\n') if p.strip()]
                    }
                    
                    # Оцениваем
                    with st.spinner("⏳ Оценка ваших ответов..."):
                        # Оценка диагноза
                        diagnosis_eval = services["evaluation_service"].evaluate_diagnosis(
                            submitted=diagnosis_input,
                            correct=case.correct_diagnosis,
                            case=case
                        )
                        
                        # Оценка лечения
                        treatment_eval = services["evaluation_service"].evaluate_treatment(
                            submitted=session.submitted_treatment,
                            correct=case.correct_treatment,
                            case=case
                        )
                        
                        # Общая оценка (50% диагноз + 50% лечение)
                        total_score = (diagnosis_eval["score"] * 0.5) + (treatment_eval["score"] * 0.5)
                        
                        session.evaluation = {
                            "diagnosis": diagnosis_eval,
                            "treatment": treatment_eval,
                            "total_score": round(total_score, 1)
                        }
                    
                    st.rerun()
