
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

## Деплой на Dokku

1. Создайте приложение на сервере Dokku:

```bash
ssh dokku@<your-dokku-host> apps:create ai-patient
```

2. Установите buildpack Python (обычно по умолчанию):

```bash
ssh dokku@<your-dokku-host> buildpacks:add ai-patient heroku/python
```

3. Задайте переменные окружения (обязательно `OPENROUTER_API_KEY`):

```bash
ssh dokku@<your-dokku-host> config:set ai-patient \
  OPENROUTER_API_KEY=your_key \
  LLM_PROVIDER=openrouter \
  LLM_MODEL=anthropic/claude-3.5-sonnet \
  STREAMLIT_SERVER_HEADLESS=true \
  STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
```

4. Добавьте remote и задеплойте:

```bash
git remote add dokku dokku@<your-dokku-host>:ai-patient
git push dokku main
```

5. Приложение запустится как веб-процесс (см. `Procfile`). Dokku автоматически пробросит `PORT`, а Streamlit будет слушать `0.0.0.0:$PORT`.

Пример локального файла окружения для справки: `env.example`.

### (Опционально) Персистентное хранилище для `data/cases`

Если вы хотите изменять или добавлять кейсы на сервере и сохранять их между деплоями:

```bash
ssh dokku@<your-dokku-host> storage:ensure-directory ai-patient
ssh dokku@<your-dokku-host> storage:mount ai-patient /var/lib/dokku/data/storage/ai-patient-cases:/app/data/cases
ssh dokku@<your-dokku-host> ps:rebuild ai-patient
```

## Структура проекта

- `src/domain/` - модели данных и бизнес-логика
- `src/data/` - работа с данными (загрузка случаев, шаблоны анализов)
- `src/ai/` - интеграция с LLM
- `src/ui/` - веб-интерфейс (Streamlit)
- `data/cases/` - клинические случаи в JSON формате
