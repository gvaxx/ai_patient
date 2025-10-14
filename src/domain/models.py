
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

@dataclass
class Patient:
    """Модель пациента"""
    name: str
    age: int
    gender: str  # "male" или "female"
    occupation: Optional[str] = None

    def to_dict(self) -> Dict:
        """Конвертирует в словарь"""
        return {
            "name": self.name,
            "age": self.age,
            "gender": self.gender,
            "occupation": self.occupation
        }

@dataclass
class ClinicalCase:
    """Клинический случай"""
    case_id: str
    title: str
    patient: 'Patient'

    # Презентация
    chief_complaint: str          # Главная жалоба
    history: str                  # История заболевания
    symptoms: Dict[str, Any]      # Симптомы

    # Правильные ответы
    correct_diagnosis: str        # Правильный диагноз
    correct_icd10: str            # Код МКБ-10
    correct_treatment: Dict[str, Any]  # Лечение

    # Реальные результаты анализов (опционально)
    real_test_results: Dict[str, Dict] = field(default_factory=dict)

    def has_real_results(self, test_id: str) -> bool:
        """Проверяет наличие реальных результатов теста"""
        return test_id in self.real_test_results

    def get_real_results(self, test_id: str) -> Optional[Dict]:
        """Возвращает реальные результаты если есть"""
        return self.real_test_results.get(test_id)

@dataclass
class TestResult:
    """Результат теста/анализа"""
    test_id: str
    name: str
    category: str  # "laboratory", "examination", "imaging"
    results: Dict[str, Any]
    interpretation: Optional[str] = None

@dataclass
class Session:
    """Сессия работы с пациентом"""
    case: ClinicalCase
    conversation: List[Dict] = field(default_factory=list)
    ordered_tests: List[str] = field(default_factory=list)
    test_results: Dict[str, TestResult] = field(default_factory=dict)
    submitted_diagnosis: Optional[str] = None
    submitted_treatment: Optional[Dict] = None
    evaluation: Optional[Dict] = None
