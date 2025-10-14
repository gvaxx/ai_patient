import json
from pathlib import Path
from typing import Dict
from ..domain.models import ClinicalCase, Patient


class CaseLoader:
    """Загрузчик клинических случаев из JSON файлов"""

    def __init__(self, cases_dir: Path):
        """
        Args:
            cases_dir: Путь к директории с JSON файлами случаев
        """
        self.cases_dir = cases_dir

    def load_all(self) -> Dict[str, ClinicalCase]:
        """
        Загружает все случаи из директории.

        Возвращает словарь: {case_id: ClinicalCase}
        """
        cases: Dict[str, ClinicalCase] = {}
        if not self.cases_dir.exists():
            return cases

        for file_path in sorted(self.cases_dir.glob("*.json")):
            case = self.load_from_file(file_path)
            cases[case.case_id] = case
        return cases

    def load_from_file(self, file_path: Path) -> ClinicalCase:
        """
        Загружает один случай из JSON файла.

        Парсит JSON и возвращает объект ClinicalCase
        """
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return self._parse_case(data)

    def _parse_case(self, data: Dict) -> ClinicalCase:
        """
        Конвертирует словарь из JSON в объект ClinicalCase.

        Должен правильно создать:
        - Patient объект из data["patient"]
        - Извлечь все поля из data["presentation"]
        - Извлечь correct_answers
        - Извлечь real_test_results (если есть)
        """
        # Создаем Patient
        patient = Patient(
            name=data["patient"]["name"],
            age=data["patient"]["age"],
            gender=data["patient"]["gender"],
            occupation=data["patient"].get("occupation"),
        )

        presentation = data.get("presentation", {})
        correct = data.get("correct_answers", {})
        diagnosis = correct.get("diagnosis", {})
        treatment = correct.get("treatment", {})

        # Создаем и возвращаем ClinicalCase
        return ClinicalCase(
            case_id=data["case_id"],
            title=data["title"],
            patient=patient,
            chief_complaint=presentation.get("chief_complaint", ""),
            history=presentation.get("history", ""),
            symptoms=presentation.get("symptoms", {}),
            correct_diagnosis=diagnosis.get("primary", ""),
            correct_icd10=diagnosis.get("icd10", ""),
            correct_treatment=treatment,
            real_test_results=data.get("real_test_results", {}),
        )


