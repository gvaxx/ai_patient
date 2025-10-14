import os
from dotenv import load_dotenv
from src.ai.llm_provider import LLMClient
from src.data.case_loader import CaseLoader
from src.domain.services import EvaluationService
from pathlib import Path

# Загрузить .env
load_dotenv()

# Создать клиент
client = LLMClient.from_env()

# Тест 1: Ответ пациента
print("=== ТЕСТ 1: Ответ пациента ===")
response = client.get_patient_response(
    question="Что вас беспокоит?",
    patient_context={
        "name": "Иван П.",
        "age": 34,
        "gender": "male",
        "chief_complaint": "Боль в животе",
        "history": "3 дня назад появилась боль",
        "symptoms": {"pain_location": "правая подвздошная область", "fever": 38.2}
    },
    conversation_history=[]
)
print(response)
print()

# Тест 2: Оценка диагноза
print("=== ТЕСТ 2: Оценка диагноза ===")

# Загрузить случай
loader = CaseLoader(Path("data/cases"))
cases = loader.load_all()
case = cases["appendicitis_001"]

# Создать evaluation service
eval_service = EvaluationService(client)

# Правильный диагноз
result = eval_service.evaluate_diagnosis(
    submitted="Острый аппендицит",
    correct=case.correct_diagnosis,
    case=case
)
print(f"Правильный диагноз: {result}")
print()

# Неправильный диагноз
result = eval_service.evaluate_diagnosis(
    submitted="Острый гастрит",
    correct=case.correct_diagnosis,
    case=case
)
print(f"Неправильный диагноз: {result}")
print()

# Тест 3: Оценка лечения
print("=== ТЕСТ 3: Оценка лечения ===")
result = eval_service.evaluate_treatment(
    submitted={
        "medications": ["Цефтриаксон 1г в/в", "Метронидазол"],
        "procedures": ["Аппендэктомия"]
    },
    correct=case.correct_treatment,
    case=case
)
print(result)
