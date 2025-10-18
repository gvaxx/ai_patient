from __future__ import annotations
import random
import json
from pathlib import Path
from typing import Dict, List, Any


class TestTemplates:
    """Шаблоны тестов и генерация нормальных результатов"""

    _templates: Dict[str, Dict[str, Any]] = None

    @classmethod
    def _load_templates(cls) -> Dict[str, Dict[str, Any]]:
        """Загружает шаблоны тестов из standarts.json"""
        if cls._templates is not None:
            return cls._templates
        
        # Путь к файлу standarts.json
        standarts_path = Path(__file__).parent.parent.parent / "data" / "tests" / "standarts.json"
        
        try:
            with open(standarts_path, "r", encoding="utf-8") as f:
                standarts_data = json.load(f)
                # Преобразуем данные из standarts.json в нужный формат
                cls._templates = cls._convert_standarts_to_templates(standarts_data)
        except FileNotFoundError:
            # Fallback к встроенным шаблонам
            cls._templates = cls._get_fallback_templates()
        
        return cls._templates

    @classmethod
    def _convert_standarts_to_templates(cls, standarts_data: Dict) -> Dict[str, Dict[str, Any]]:
        """Конвертирует данные из standarts.json в формат templates"""
        templates = {}
        
        for test_id, test_data in standarts_data.items():
            template = {
                "name": test_data.get("name", test_id),
                "category": test_data.get("category", "unknown")
            }
            
            # Если есть параметры - добавляем их
            if "parameters" in test_data:
                template["parameters"] = test_data["parameters"]
            
            # Если есть описание - добавляем его
            if "description" in test_data:
                template["description"] = test_data["description"]
            
            templates[test_id] = template
        
        return templates

    @classmethod
    def _get_fallback_templates(cls) -> Dict[str, Dict[str, Any]]:
        """Возвращает встроенные шаблоны как fallback"""
        return {
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
    def get_templates(cls) -> Dict[str, Dict[str, Any]]:
        """Возвращает загруженные шаблоны тестов"""
        return cls._load_templates()

    @classmethod
    def get_all_tests(cls) -> List[Dict]:
        templates = cls.get_templates()
        return [
            {"test_id": test_id, "name": t.get("name"), "category": t.get("category")}
            for test_id, t in templates.items()
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
        templates = cls.get_templates()
        if test_id not in templates:
            raise KeyError(f"Unknown test_id: {test_id}")
        t = templates[test_id]

        # Numerical style (has parameters)
        if "parameters" in t:
            results: Dict[str, Any] = {}
            # Special handling for CBC percentages to avoid neutrophils + lymphocytes > 100
            if test_id == "cbc":
                # First generate non-percentage params
                for pid, p in t["parameters"].items():
                    if pid in ("neutrophils", "lymphocytes"):
                        continue
                    normal_range = p["normal_range"]
                    if isinstance(normal_range, list) and len(normal_range) == 2 and all(isinstance(x, (int, float)) for x in normal_range):
                        vmin, vmax = normal_range
                        value = cls._generate_value_in_range(vmin, vmax)
                        results[pid] = {
                            "name": p["name"],
                            "value": value,
                            "unit": p.get("unit", ""),
                            "reference": cls._format_reference(vmin, vmax),
                            "status": "normal",
                        }
                    elif isinstance(normal_range, str):
                        # Для строковых значений (например, "отрицательно")
                        results[pid] = {
                            "name": p["name"],
                            "value": normal_range,
                            "unit": p.get("unit", ""),
                            "reference": normal_range,
                            "status": "normal",
                        }
                    elif isinstance(normal_range, list):
                        # Для списков строк (например, ["плотная", "оформленная"])
                        import random
                        value = random.choice(normal_range)
                        results[pid] = {
                            "name": p["name"],
                            "value": value,
                            "unit": p.get("unit", ""),
                            "reference": ", ".join(normal_range),
                            "status": "normal",
                        }
                    else:
                        # Fallback для других типов
                        continue

                # Generate percentages with constraint
                neutro_p = t["parameters"]["neutrophils"]
                lympho_p = t["parameters"]["lymphocytes"]
                n_normal_range = neutro_p["normal_range"]
                l_normal_range = lympho_p["normal_range"]
                
                if isinstance(n_normal_range, list) and len(n_normal_range) == 2:
                    n_vmin, n_vmax = n_normal_range
                else:
                    n_vmin, n_vmax = 45, 70  # fallback
                    
                if isinstance(l_normal_range, list) and len(l_normal_range) == 2:
                    l_vmin, l_vmax = l_normal_range
                else:
                    l_vmin, l_vmax = 20, 40  # fallback
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
                    normal_range = p["normal_range"]
                    if isinstance(normal_range, list) and len(normal_range) == 2 and all(isinstance(x, (int, float)) for x in normal_range):
                        vmin, vmax = normal_range
                        value = cls._generate_value_in_range(vmin, vmax)
                        results[pid] = {
                            "name": p["name"],
                            "value": value,
                            "unit": p.get("unit", ""),
                            "reference": cls._format_reference(vmin, vmax),
                            "status": "normal",
                        }
                    elif isinstance(normal_range, str):
                        # Для строковых значений (например, "отрицательно")
                        results[pid] = {
                            "name": p["name"],
                            "value": normal_range,
                            "unit": p.get("unit", ""),
                            "reference": normal_range,
                            "status": "normal",
                        }
                    elif isinstance(normal_range, list):
                        # Для списков строк (например, ["плотная", "оформленная"])
                        import random
                        value = random.choice(normal_range)
                        results[pid] = {
                            "name": p["name"],
                            "value": value,
                            "unit": p.get("unit", ""),
                            "reference": ", ".join(normal_range),
                            "status": "normal",
                        }
                    else:
                        # Fallback для других типов
                        continue
            return {
                "test_id": test_id,
                "name": t["name"],
                "category": t["category"],
                "results": results,
            }

        # Descriptive (только описание, без параметров)
        return {
            "test_id": test_id,
            "name": t["name"],
            "category": t["category"],
            "description": t.get("description", ""),
        }

    @classmethod
    def merge_with_real_results(cls, test_id: str, real_results: Dict) -> Dict:
        normal = cls.generate_normal_results(test_id)

        # Если real_results - строка, то это описательный тест
        if isinstance(real_results, str):
            merged = dict(normal)
            merged["description"] = real_results
            return merged

        # Если real_results - объект с results, то это числовой тест
        if isinstance(real_results, dict) and "results" in real_results:
            merged = dict(normal)
            merged_results = dict(merged.get("results", {}))
            real_res_map = real_results.get("results", {})
            for key, val in real_res_map.items():
                merged_results[key] = val
            merged["results"] = merged_results
            return merged

        # Если real_results - объект без results, но с параметрами (например, vital_signs)
        if isinstance(real_results, dict) and "results" not in real_results:
            # Проверяем, есть ли в normal тесте параметры
            if "parameters" in normal:
                merged = dict(normal)
                merged_results = dict(merged.get("results", {}))
                
                # Конвертируем real_results в формат results
                for key, val in real_results.items():
                    if key in merged_results:  # Только если параметр есть в шаблоне
                        if isinstance(val, str):
                            # Для строковых значений
                            merged_results[key] = {
                                "name": merged_results[key]["name"],
                                "value": val,
                                "unit": merged_results[key].get("unit", ""),
                                "reference": merged_results[key].get("reference", ""),
                                "status": "normal"
                            }
                        else:
                            # Для числовых значений
                            merged_results[key] = {
                                "name": merged_results[key]["name"],
                                "value": val,
                                "unit": merged_results[key].get("unit", ""),
                                "reference": merged_results[key].get("reference", ""),
                                "status": "normal"
                            }
                
                merged["results"] = merged_results
                return merged
            else:
                # Если нет параметров, то это описательный тест
                merged = dict(normal)
                merged["description"] = str(real_results)
                return merged

        # Fallback: если ничего не подошло
        merged = dict(normal)
        if isinstance(real_results, dict):
            merged["description"] = str(real_results)
        else:
            merged["description"] = str(real_results)
        return merged
