
import streamlit as st
from pathlib import Path
import os
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
        
        # Кнопка "Анализы"
        if st.button(
            "🧪 Анализы", 
            key="nav_tests",
            use_container_width=True,
            type="primary" if st.session_state.active_tab == "tests" else "secondary"
        ):
            st.session_state.active_tab = "tests"
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
    st.write("Выберите один из доступных случаев для начала работы")
    
    st.write("---")
    
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
                btn_col1, btn_col2 = st.columns([1,1])
                with btn_col1:
                    if st.button(
                        "▶️ Начать сессию", 
                        key=f"start_{case_id}",
                        use_container_width=True,
                        type="primary"
                    ):
                        start_new_session(case_id)
                        st.rerun()

elif st.session_state.active_tab == "interview":
    st.header("💬 Опрос пациента")
    
    session = st.session_state.session
    case = session.case
    
    # Метрики сверху
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Пациент", case.patient.name)
    with col2:
        st.metric("Возраст", f"{case.patient.age} лет")
    with col3:
        st.metric("Пол", "М" if case.patient.gender == "male" else "Ж")
    with col4:
        st.metric("Жалоба", case.chief_complaint)
    
    st.write("---")
    
    # Контейнер для чата с фиксированной высотой
    chat_container = st.container(height=400)
    
    with chat_container:
        # Показываем всю историю разговора
        for msg in session.conversation:
            if msg['role'] == 'doctor':
                st.chat_message("user", avatar="👨‍⚕️").write(msg['content'])
            else:
                st.chat_message("assistant", avatar="🤒").write(msg['content'])
    
    # Поле ввода вопроса (внизу, вне контейнера)
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
    
    st.write("---")
    
    # Подсказка и кнопка перехода
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info("💡 Соберите анамнез, задайте важные вопросы о симптомах")
    with col2:
        if st.button("Далее: Анализы →", use_container_width=True, type="primary"):
            st.session_state.active_tab = "tests"
            st.rerun()

elif st.session_state.active_tab == "tests":
    st.header("🧪 Назначение обследований")
    
    session = st.session_state.session
    case = session.case
    
    # Получаем список всех доступных тестов
    available_tests = TestTemplates.get_all_tests()
    
    # Группируем по категориям
    lab_tests = [t for t in available_tests if t["category"] == "laboratory"]
    exam_tests = [t for t in available_tests if t["category"] == "examination"]
    imaging_tests = [t for t in available_tests if t["category"] == "imaging"]
    
    # Разделяем на две колонки
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Проведение обследований по одному")
        
        # Лабораторные анализы
        with st.expander("🔬 Лабораторные анализы", expanded=True):
            lab_options = {t["name"]: t["test_id"] for t in lab_tests if t["test_id"] not in session.ordered_tests}
            selected_lab_name = st.selectbox(
                "Выберите анализ",
                options=["— не выбрано —"] + list(lab_options.keys()),
                key="select_lab_test",
            )
            if st.button("Провести лабораторный анализ", key="run_lab_test", disabled=selected_lab_name == "— не выбрано —"):
                test_id = lab_options[selected_lab_name]
                with st.spinner("Получение результатов..."):
                    result = services["test_service"].get_test_results(test_id=test_id, case=case)
                    session.test_results[test_id] = result
                    if test_id not in session.ordered_tests:
                        session.ordered_tests.append(test_id)
                st.success(f"✅ Результаты добавлены: {result.name}")
                st.rerun()
        
        # Осмотр и пальпация
        with st.expander("🩺 Осмотр и пальпация", expanded=True):
            exam_options = {t["name"]: t["test_id"] for t in exam_tests if t["test_id"] not in session.ordered_tests}
            selected_exam_name = st.selectbox(
                "Выберите осмотр",
                options=["— не выбрано —"] + list(exam_options.keys()),
                key="select_exam_test",
            )
            if st.button("Провести осмотр", key="run_exam_test", disabled=selected_exam_name == "— не выбрано —"):
                test_id = exam_options[selected_exam_name]
                with st.spinner("Получение результатов..."):
                    result = services["test_service"].get_test_results(test_id=test_id, case=case)
                    session.test_results[test_id] = result
                    if test_id not in session.ordered_tests:
                        session.ordered_tests.append(test_id)
                st.success(f"✅ Результаты добавлены: {result.name}")
                st.rerun()
        
        # Визуализация
        with st.expander("📷 Визуализация", expanded=True):
            imaging_options = {t["name"]: t["test_id"] for t in imaging_tests if t["test_id"] not in session.ordered_tests}
            selected_img_name = st.selectbox(
                "Выберите исследование",
                options=["— не выбрано —"] + list(imaging_options.keys()),
                key="select_imaging_test",
            )
            if st.button("Провести визуализацию", key="run_imaging_test", disabled=selected_img_name == "— не выбрано —"):
                test_id = imaging_options[selected_img_name]
                with st.spinner("Получение результатов..."):
                    result = services["test_service"].get_test_results(test_id=test_id, case=case)
                    session.test_results[test_id] = result
                    if test_id not in session.ordered_tests:
                        session.ordered_tests.append(test_id)
                st.success(f"✅ Результаты добавлены: {result.name}")
                st.rerun()
    
    with col2:
        # Панель статистики
        st.subheader("Статус")
        st.metric("Проведено тестов", len(session.ordered_tests))
        st.metric("Получено результатов", len(session.test_results))
        
        if session.test_results:
            st.write("---")
            st.write("**Полученные результаты:**")
            for test_id, result in session.test_results.items():
                st.write(f"✓ {result.name}")
    
    # Показываем результаты
    if session.test_results:
        st.write("---")
        st.subheader("📊 Результаты обследований")
        
        for test_id, result in session.test_results.items():
            with st.expander(f"📄 {result.name}", expanded=False):
                # Проверяем тип результата
                if "description" in result.results:
                    # Описательный результат (осмотр, визуализация)
                    st.write(result.results["description"])
                else:
                    # Численный результат (лабораторные)
                    # Формируем данные для таблицы
                    table_data = []
                    for param_id, param_data in result.results.items():
                        row = {
                            "Показатель": param_data["name"],
                            "Значение": f"{param_data['value']} {param_data['unit']}",
                        }
                        if "reference" in param_data:
                            row["Норма"] = param_data["reference"]
                            row["Статус"] = "✅ Норма" if param_data["status"] == "normal" else "⚠️ Отклонение"
                        table_data.append(row)
                    
                    # Показываем таблицу
                    st.dataframe(
                        table_data, 
                        use_container_width=True, 
                        hide_index=True
                    )
    
    st.write("---")
    
    # Подсказка и кнопка перехода
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info("💡 Проводите обследования по одному и анализируйте результаты")
    with col2:
        if st.button("Далее: Диагноз →", use_container_width=True, type="primary"):
            st.session_state.active_tab = "diagnosis"
            st.rerun()

elif st.session_state.active_tab == "diagnosis":
    st.header("📋 Диагноз и план лечения")
    
    session = st.session_state.session
    case = session.case
    
    # Краткая сводка: опрос и проведенные анализы
    with st.expander("🧾 Сводка опроса и обследований", expanded=False):
        st.subheader("Опрос (последние сообщения)")
        if session.conversation:
            for msg in session.conversation[-6:]:
                role_icon = "👨‍⚕️" if msg.get('role') == 'doctor' else "🤒"
                st.write(f"{role_icon} {msg.get('content','')}")
        else:
            st.write("Нет данных опроса")
        
        st.subheader("Проведенные обследования")
        if session.test_results:
            for tid, res in session.test_results.items():
                st.write(f"• {res.name}")
        else:
            st.write("Пока обследований не проводилось")
    
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
        col1, col2 = st.columns(2)
        
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
