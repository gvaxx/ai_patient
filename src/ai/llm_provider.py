from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, List
import os
import json
import requests


class LLMProvider(ABC):
    """Абстрактный базовый класс для LLM провайдеров"""
    
    @abstractmethod
    def generate(self, messages: List[Dict], max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """
        Генерирует ответ от LLM.
        
        Args:
            messages: Список сообщений в формате [{"role": "user/system", "content": "text"}]
            max_tokens: Максимальное количество токенов
            temperature: Температура генерации (0-1)
            
        Returns:
            Текст ответа от модели
        """
        raise NotImplementedError


class OpenRouterProvider(LLMProvider):
    """
    Провайдер для OpenRouter API.
    Поддерживает любые модели через единый API.
    """
    
    def __init__(
        self, 
        api_key: str,
        model: str = "anthropic/claude-3.5-sonnet",
        base_url: str = "https://openrouter.ai/api/v1"
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
    
    def generate(self, messages: List[Dict], max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """
        Отправляет запрос к OpenRouter API.
        """
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            # Optional headers to be nice
            "HTTP-Referer": "https://github.com/yourusername/virtual-patient",
            "X-Title": "Virtual Patient MVP",
        }
        body = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        resp = requests.post(url, headers=headers, data=json.dumps(body), timeout=60)
        if resp.status_code != 200:
            raise Exception(f"OpenRouter error {resp.status_code}: {resp.text}")
        data = resp.json()
        try:
            return data["choices"][0]["message"]["content"]
        except Exception:
            raise Exception(f"Unexpected OpenRouter response: {data}")


class LLMClient:
    """
    Unified LLM Client - работает с любым провайдером.
    Предоставляет высокоуровневые методы для работы с пациентом и оценкой.
    """
    
    def __init__(self, provider: LLMProvider):
        self.provider = provider
    
    @classmethod
    def from_env(cls) -> "LLMClient":
        """
        Создает клиент из переменных окружения.
        """
        provider_type = os.getenv("LLM_PROVIDER", "openrouter").lower()
        
        if provider_type == "openrouter":
            api_key = os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPENROUTER_API_KEY not found in environment. "
                    "Please set it in .env file or environment variables."
                )
            model = os.getenv("LLM_MODEL", "anthropic/claude-3.5-sonnet")
            provider = OpenRouterProvider(api_key=api_key, model=model)
        else:
            raise ValueError(f"Unknown provider: {provider_type}")
        
        return cls(provider)
    
    def get_patient_response(
        self,
        question: str,
        patient_context: Dict,
        conversation_history: List[Dict]
    ) -> str:
        """
        Генерирует ответ пациента на вопрос врача.
        """
        from .prompts import PATIENT_ROLE_PROMPT

        # take last 10 messages as context
        history_items = conversation_history[-10:]
        history_lines = []
        for msg in history_items:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            history_lines.append(f"{role}: {content}")
        history_str = "\n".join(history_lines) if history_lines else "(пока нет)"

        prompt = PATIENT_ROLE_PROMPT.format(
            patient_name=patient_context.get("name", "Пациент"),
            patient_age=patient_context.get("age", "-"),
            patient_gender=patient_context.get("gender", "-"),
            chief_complaint=patient_context.get("chief_complaint", "-"),
            history=patient_context.get("history", "-"),
            symptoms=json.dumps(patient_context.get("symptoms", {}), ensure_ascii=False, indent=2),
            conversation_history=history_str,
            doctor_question=question,
        )
        messages = [{"role": "user", "content": prompt}]
        return self.provider.generate(messages, temperature=0.8)
    
    def evaluate_diagnosis(
        self,
        submitted: str,
        correct: str,
        case_context: Dict
    ) -> Dict:
        from .prompts import DIAGNOSIS_EVALUATION_PROMPT

        prompt = DIAGNOSIS_EVALUATION_PROMPT.format(
            submitted_diagnosis=submitted,
            correct_diagnosis=correct,
            chief_complaint=case_context.get("chief_complaint", ""),
            symptoms=json.dumps(case_context.get("symptoms", {}), ensure_ascii=False),
        )
        messages = [{"role": "user", "content": prompt}]
        raw = self.provider.generate(messages, temperature=0.3)

        # sanitize code fences if any
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip('`')
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        cleaned = cleaned.strip()
        try:
            return json.loads(cleaned)
        except Exception:
            return {"score": 0, "status": "incorrect", "feedback": "Не удалось распарсить ответ модели."}

    def evaluate_treatment(
        self,
        submitted: Dict,
        correct: Dict,
        patient: Dict
    ) -> Dict:
        from .prompts import TREATMENT_EVALUATION_PROMPT

        prompt = TREATMENT_EVALUATION_PROMPT.format(
            submitted_treatment=json.dumps(submitted, ensure_ascii=False),
            correct_treatment=json.dumps(correct, ensure_ascii=False),
            patient_age=patient.get("age", "-"),
            patient_gender=patient.get("gender", "-"),
        )
        messages = [{"role": "user", "content": prompt}]
        raw = self.provider.generate(messages, temperature=0.3)

        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip('`')
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        cleaned = cleaned.strip()
        try:
            return json.loads(cleaned)
        except Exception:
            return {"score": 0, "feedback": "Не удалось распарсить ответ модели."}

    def evaluate_preliminary_diagnosis(
        self,
        submitted: str,
        correct: str,
        case_context: Dict
    ) -> Dict:
        from .prompts import PRELIMINARY_DIAGNOSIS_EVALUATION_PROMPT

        prompt = PRELIMINARY_DIAGNOSIS_EVALUATION_PROMPT.format(
            submitted_diagnosis=submitted,
            correct_diagnosis=correct,
            chief_complaint=case_context.get("chief_complaint", ""),
            symptoms=json.dumps(case_context.get("symptoms", {}), ensure_ascii=False),
        )
        messages = [{"role": "user", "content": prompt}]
        raw = self.provider.generate(messages, temperature=0.3)

        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip('`')
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        cleaned = cleaned.strip()
        try:
            return json.loads(cleaned)
        except Exception:
            return {"score": 1, "status": "incorrect", "feedback": "Не удалось распарсить ответ модели."}

    def evaluate_comorbidities(
        self,
        submitted: str,
        correct: str,
        case_context: Dict
    ) -> Dict:
        from .prompts import COMORBIDITIES_EVALUATION_PROMPT

        prompt = COMORBIDITIES_EVALUATION_PROMPT.format(
            submitted_comorbidities=submitted,
            correct_comorbidities=correct,
            chief_complaint=case_context.get("chief_complaint", ""),
            symptoms=json.dumps(case_context.get("symptoms", {}), ensure_ascii=False),
        )
        messages = [{"role": "user", "content": prompt}]
        raw = self.provider.generate(messages, temperature=0.3)

        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip('`')
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        cleaned = cleaned.strip()
        try:
            return json.loads(cleaned)
        except Exception:
            return {"score": 1, "status": "incorrect", "feedback": "Не удалось распарсить ответ модели."}

    def evaluate_final_diagnosis(
        self,
        submitted: str,
        correct: str,
        case_context: Dict
    ) -> Dict:
        from .prompts import FINAL_DIAGNOSIS_EVALUATION_PROMPT

        prompt = FINAL_DIAGNOSIS_EVALUATION_PROMPT.format(
            submitted_diagnosis=submitted,
            correct_diagnosis=correct,
            chief_complaint=case_context.get("chief_complaint", ""),
            symptoms=json.dumps(case_context.get("symptoms", {}), ensure_ascii=False),
        )
        messages = [{"role": "user", "content": prompt}]
        raw = self.provider.generate(messages, temperature=0.3)

        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip('`')
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        cleaned = cleaned.strip()
        try:
            return json.loads(cleaned)
        except Exception:
            return {"score": 1, "status": "incorrect", "feedback": "Не удалось распарсить ответ модели."}

    def evaluate_final_treatment(
        self,
        submitted: str,
        correct: Dict,
        patient: Dict
    ) -> Dict:
        from .prompts import FINAL_TREATMENT_EVALUATION_PROMPT

        prompt = FINAL_TREATMENT_EVALUATION_PROMPT.format(
            submitted_treatment=submitted,
            correct_treatment=json.dumps(correct, ensure_ascii=False),
            patient_age=patient.get("age", "-"),
            patient_gender=patient.get("gender", "-"),
        )
        messages = [{"role": "user", "content": prompt}]
        raw = self.provider.generate(messages, temperature=0.3)

        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip('`')
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        cleaned = cleaned.strip()
        try:
            return json.loads(cleaned)
        except Exception:
            return {"score": 1, "feedback": "Не удалось распарсить ответ модели."}


