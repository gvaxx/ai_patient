
# Виртуальный Пациент MVP

Система для обучения врачей с использованием AI.

## Установка

```bash
pip install -r requirements.txt
cp .env.example .env
# Отредактируйте .env и добавьте свой API ключ
```

## Запуск

```bash
streamlit run src/ui/app.py
```

## Структура проекта

- `src/domain/` - модели данных и бизнес-логика
- `src/data/` - работа с данными (загрузка случаев, шаблоны анализов)
- `src/ai/` - интеграция с LLM
- `src/ui/` - веб-интерфейс (Streamlit)
- `data/cases/` - клинические случаи в JSON формате
