from __future__ import annotations
import random
from typing import Dict, List, Any


class TestTemplates:
    """Шаблоны тестов и генерация нормальных результатов"""

    TEMPLATES: Dict[str, Dict[str, Any]] = {
        # Laboratory (numerical)
        "cbc": {
            "name": "Общий анализ крови",
            "category": "laboratory",
            "parameters": {
                "wbc": {
                    "name": "Лейкоциты",
                    "normal_range": [4.0, 9.0],
                    "unit": "×10⁹/л",
                    "ideal": 6.0,
                },
                "hgb": {
                    "name": "Гемоглобин",
                    "normal_range": [130, 160],
                    "unit": "г/л",
                    "ideal": 145,
                },
                "plt": {
                    "name": "Тромбоциты",
                    "normal_range": [150, 400],
                    "unit": "×10⁹/л",
                    "ideal": 250,
                },
                "neutrophils": {
                    "name": "Нейтрофилы",
                    "normal_range": [45, 70],
                    "unit": "%",
                    "ideal": 58,
                },
                "lymphocytes": {
                    "name": "Лимфоциты",
                    "normal_range": [20, 40],
                    "unit": "%",
                    "ideal": 30,
                },
            },
        },
        "biochemistry": {
            "name": "Биохимический анализ крови",
            "category": "laboratory",
            "parameters": {
                "glucose": {
                    "name": "Глюкоза",
                    "normal_range": [3.9, 6.1],
                    "unit": "ммоль/л",
                    "ideal": 5.0,
                },
                "creatinine": {
                    "name": "Креатинин",
                    "normal_range": [62, 106],
                    "unit": "мкмоль/л",
                    "ideal": 84,
                },
                "alt": {
                    "name": "АЛТ",
                    "normal_range": [0, 40],
                    "unit": "Ед/л",
                    "ideal": 22,
                },
                "ast": {
                    "name": "АСТ",
                    "normal_range": [0, 40],
                    "unit": "Ед/л",
                    "ideal": 22,
                },
                "crp": {
                    "name": "СРБ",
                    "normal_range": [0, 5],
                    "unit": "мг/л",
                    "ideal": 1,
                },
            },
        },
        "urinalysis": {
            "name": "Общий анализ мочи",
            "category": "laboratory",
            "parameters": {
                "protein": {
                    "name": "Белок",
                    "normal_range": [0.0, 0.033],
                    "unit": "г/л",
                    "ideal": 0.0,
                },
                "wbc": {
                    "name": "Лейкоциты",
                    "normal_range": [0, 5],
                    "unit": "клеток/п.зр.",
                    "ideal": 1,
                },
                "rbc": {
                    "name": "Эритроциты",
                    "normal_range": [0, 2],
                    "unit": "клеток/п.зр.",
                    "ideal": 0,
                },
            },
        },
        # Examination (descriptive or numerical style)
        "vital_signs": {
            "name": "Витальные показатели",
            "category": "examination",
            "parameters": {
                "bp_systolic": {
                    "name": "Систолическое АД",
                    "normal_range": [110, 130],
                    "unit": "мм рт. ст.",
                    "ideal": 120,
                },
                "hr": {
                    "name": "Частота пульса",
                    "normal_range": [60, 90],
                    "unit": "уд/мин",
                    "ideal": 75,
                },
                "temperature": {
                    "name": "Температура",
                    "normal_range": [36.3, 36.9],
                    "unit": "°C",
                    "ideal": 36.6,
                },
                "rr": {
                    "name": "ЧДД",
                    "normal_range": [12, 20],
                    "unit": "в/мин",
                    "ideal": 16,
                },
            },
        },
        "abdominal_exam": {
            "name": "Осмотр живота",
            "category": "examination",
            "description": (
                "Живот мягкий, безболезненный при пальпации во всех отделах. Симптомов раздражения брюшины нет."
            ),
        },
        "chest_exam": {
            "name": "Аускультация легких",
            "category": "examination",
            "description": (
                "Дыхание везикулярное, проводится во все отделы. Хрипов нет. Бронхиальное дыхание не выслушивается."
            ),
        },
        "heart_exam": {
            "name": "Аускультация сердца",
            "category": "examination",
            "description": (
                "Тоны сердца ясные, ритмичные. Шумов нет. Частота сердечных сокращений в пределах нормы."
            ),
        },
        # Imaging (descriptive)
        "ultrasound_abdomen": {
            "name": "УЗИ органов брюшной полости",
            "category": "imaging",
            "description": (
                "Печень: размеры не увеличены, эхогенность обычная. Желчный пузырь без конкрементов. Поджелудочная железа и селезенка без особенностей. Свободной жидкости нет."
            ),
        },
        "xray_chest": {
            "name": "Рентгенография органов грудной клетки",
            "category": "imaging",
            "description": (
                "Легочные поля без очаговых и инфильтративных изменений. Корни структурные. Сердце и средостение без особенностей."
            ),
        },
        "ct_abdomen": {
            "name": "КТ органов брюшной полости",
            "category": "imaging",
            "description": (
                "Печень, селезенка, поджелудочная железа: без патологических изменений. Почки обычной формы и размеров. Свободной жидкости нет."
            ),
        },
    }

    @classmethod
    def get_all_tests(cls) -> List[Dict]:
        return [
            {"test_id": test_id, "name": t.get("name"), "category": t.get("category")}
            for test_id, t in cls.TEMPLATES.items()
        ]

    @classmethod
    def _format_reference(cls, vmin: float, vmax: float) -> str:
        def fmt(v: float) -> str:
            # Show one decimal if range is not large; else integer
            if max(abs(vmin), abs(vmax)) > 50:
                return f"{round(v):.0f}"
            return f"{v:.1f}"
        return f"{fmt(vmin)}-{fmt(vmax)}"

    @classmethod
    def _generate_value_in_range(cls, vmin: float, vmax: float) -> float:
        center = (vmin + vmax) / 2.0
        width = (vmax - vmin)
        variation = 0.15 * width
        low = max(vmin, center - variation)
        high = min(vmax, center + variation)
        value = random.uniform(low, high)
        # Rounding rule
        if vmax > 50:
            return round(value)
        return round(value, 1)

    @classmethod
    def generate_normal_results(cls, test_id: str) -> Dict:
        if test_id not in cls.TEMPLATES:
            raise KeyError(f"Unknown test_id: {test_id}")
        t = cls.TEMPLATES[test_id]

        # Numerical style (has parameters)
        if "parameters" in t:
            results: Dict[str, Any] = {}
            # Special handling for CBC percentages to avoid neutrophils + lymphocytes > 100
            if test_id == "cbc":
                # First generate non-percentage params
                for pid, p in t["parameters"].items():
                    if pid in ("neutrophils", "lymphocytes"):
                        continue
                    vmin, vmax = p["normal_range"]
                    value = cls._generate_value_in_range(vmin, vmax)
                    results[pid] = {
                        "name": p["name"],
                        "value": value,
                        "unit": p.get("unit", ""),
                        "reference": cls._format_reference(vmin, vmax),
                        "status": "normal",
                    }

                # Generate percentages with constraint
                neutro_p = t["parameters"]["neutrophils"]
                lympho_p = t["parameters"]["lymphocytes"]
                n_vmin, n_vmax = neutro_p["normal_range"]
                l_vmin, l_vmax = lympho_p["normal_range"]
                neutro_val = cls._generate_value_in_range(n_vmin, n_vmax)
                # max lymphocytes so that sum <= 100
                lympho_max_allowed = min(l_vmax, max(0, 100 - neutro_val))
                # If allowed max is below min, clamp to min (will exceed 100 slightly, but keep within physiologic min)
                if lympho_max_allowed < l_vmin:
                    lympho_max_allowed = l_vmin
                lympho_val = cls._generate_value_in_range(l_vmin, lympho_max_allowed)

                results["neutrophils"] = {
                    "name": neutro_p["name"],
                    "value": neutro_val,
                    "unit": neutro_p.get("unit", ""),
                    "reference": cls._format_reference(n_vmin, n_vmax),
                    "status": "normal",
                }
                results["lymphocytes"] = {
                    "name": lympho_p["name"],
                    "value": lympho_val,
                    "unit": lympho_p.get("unit", ""),
                    "reference": cls._format_reference(l_vmin, l_vmax),
                    "status": "normal",
                }
            else:
                for pid, p in t["parameters"].items():
                    vmin, vmax = p["normal_range"]
                    value = cls._generate_value_in_range(vmin, vmax)
                    results[pid] = {
                        "name": p["name"],
                        "value": value,
                        "unit": p.get("unit", ""),
                        "reference": cls._format_reference(vmin, vmax),
                        "status": "normal",
                    }
            return {
                "test_id": test_id,
                "name": t["name"],
                "category": t["category"],
                "results": results,
            }

        # Descriptive
        return {
            "test_id": test_id,
            "name": t["name"],
            "category": t["category"],
            "description": t.get("description", ""),
        }

    @classmethod
    def merge_with_real_results(cls, test_id: str, real_results: Dict) -> Dict:
        normal = cls.generate_normal_results(test_id)

        # Descriptive test: override description when provided
        if "description" in normal:
            merged = dict(normal)
            desc = real_results.get("description") if isinstance(real_results, dict) else None
            if desc:
                merged["description"] = desc
            return merged

        # Numerical: deep-merge results
        merged = dict(normal)
        merged_results = dict(merged.get("results", {}))
        real_res_map = {}
        if isinstance(real_results, dict):
            real_res_map = real_results.get("results", {})
        for key, val in real_res_map.items():
            merged_results[key] = val
        merged["results"] = merged_results
        return merged
