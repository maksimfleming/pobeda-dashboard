# Дашборд «Победа»

Веб-дашборд для объекта **Усадьба в Победе** — генподряд 78.

Источник данных: Google-таблица `Объект_Победа_для_Google_v2`.
Стек: Streamlit + Plotly + gspread.

## Запуск локально

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

Ключ сервисного аккаунта Google положить в `../secrets/google_sa.json`.

## Деплой на Streamlit Cloud

1. Подключить этот репо в [share.streamlit.io](https://share.streamlit.io)
2. В Settings → Secrets вставить содержимое `google_sa.json` под ключом `gcp_service_account`:

```toml
[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
# и далее все поля из json
```

## Страницы

- **Главная** — KPI, прогресс по сметам, статусы дел, журнал
- **Дела** — фильтры, аналитика, срочные и просроченные
- **Закупки** — поставщики, разбивка по сметам и разделам
