# -*- coding: utf-8 -*-
from typing import Dict, List
from .models import ClinicalCase, TestResult
from ..data.test_templates import TestTemplates


class TestService:
    """Сервис работы с анализами"""
    
    @staticmethod
    def get_test_results(test_id: str, case: ClinicalCase) -> TestResult:
        """
        Возвращает результаты теста для данного случая.
        """

        if case.has_real_results(test_id):
            merged = TestTemplates.merge_with_real_results(test_id, case.get_real_results(test_id))
        else:
            merged = TestTemplates.generate_normal_results(test_id)
        if "results" in merged:
            return TestResult(
                test_id=test_id,
                name=merged.get("name", test_id),
                category=merged.get("category", ""),
                results=merged["results"],
                interpretation=None,
            )
        else:
            # descriptive: wrap description under results for uniform access
            return TestResult(
                test_id=test_id,
                name=merged.get("name", test_id),
                category=merged.get("category", ""),
                results={"description": merged.get("description", "")},
                interpretation=None,
            )

    @staticmethod
    def get_available_tests() -> List[Dict]:
        """
        Возвращает список всех доступных тестов.
        Просто вызывает TestTemplates.get_all_tests()
        """
        return TestTemplates.get_all_tests()


class EvaluationService:
    """Сервис оценки действий врача"""
    
    def __init__(self, llm_client):
        """
        Args:
            llm_client: Экземпляр LLMClient из src.ai.llm_provider
        """
        self.llm = llm_client
    
    def evaluate_diagnosis(
        self, 
        submitted: str, 
        correct: str,
        case: ClinicalCase
    ) -> Dict:
        """
        Оценивает поставленный диагноз.
        """
        s = (submitted or "").strip().lower()
        c = (correct or "").strip().lower()
        if s and c and s == c:
            return {"score": 100, "status": "correct", "feedback": "✅ Диагноз поставлен абсолютно верно!"}

        case_context = {
            "chief_complaint": case.chief_complaint,
            "symptoms": case.symptoms,
        }
        return self.llm.evaluate_diagnosis(submitted=submitted, correct=correct, case_context=case_context)

    def evaluate_treatment(
        self, 
        submitted: Dict, 
        correct: Dict,
        case: ClinicalCase
    ) -> Dict:
        """
        Оценивает план лечения.
        """
        patient_ctx = {
            "age": case.patient.age,
            "gender": case.patient.gender,
        }
        return self.llm.evaluate_treatment(submitted=submitted, correct=correct, patient=patient_ctx)

    def evaluate_preliminary_diagnosis(
        self, 
        submitted: str, 
        correct: str,
        case: ClinicalCase
    ) -> Dict:
        """
        Оценивает предварительный диагноз.
        """
        case_context = {
            "chief_complaint": case.chief_complaint,
            "symptoms": case.symptoms,
        }
        return self.llm.evaluate_preliminary_diagnosis(submitted=submitted, correct=correct, case_context=case_context)

    def evaluate_comorbidities(
        self, 
        submitted: str, 
        correct: str,
        case: ClinicalCase
    ) -> Dict:
        """
        Оценивает сопутствующие заболевания.
        """
        case_context = {
            "chief_complaint": case.chief_complaint,
            "symptoms": case.symptoms,
        }
        return self.llm.evaluate_comorbidities(submitted=submitted, correct=correct, case_context=case_context)

    def evaluate_final_diagnosis(
        self, 
        submitted: str, 
        correct: str,
        case: ClinicalCase
    ) -> Dict:
        """
        Оценивает финальный диагноз.
        """
        case_context = {
            "chief_complaint": case.chief_complaint,
            "symptoms": case.symptoms,
        }
        return self.llm.evaluate_final_diagnosis(submitted=submitted, correct=correct, case_context=case_context)

    def evaluate_final_treatment(
        self, 
        submitted: str, 
        correct: Dict,
        case: ClinicalCase
    ) -> Dict:
        """
        Оценивает финальный план лечения.
        """
        patient_ctx = {
            "age": case.patient.age,
            "gender": case.patient.gender,
        }
        return self.llm.evaluate_final_treatment(submitted=submitted, correct=correct, patient=patient_ctx)

    def evaluate_combined(
        self,
        submitted_diagnosis: str,
        submitted_treatment: str,
        correct_diagnosis: str,
        correct_treatment: Dict,
        case: ClinicalCase
    ) -> Dict:
        """
        Оценивает диагноз и лечение в одном запросе.
        """
        case_context = {
            "chief_complaint": case.chief_complaint,
            "symptoms": case.symptoms,
            "patient_age": case.patient.age,
            "patient_gender": case.patient.gender,
        }
        return self.llm.evaluate_combined(
            submitted_diagnosis=submitted_diagnosis,
            submitted_treatment=submitted_treatment,
            correct_diagnosis=correct_diagnosis,
            correct_treatment=correct_treatment,
            case_context=case_context
        )

