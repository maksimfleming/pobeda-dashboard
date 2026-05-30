# -*- coding: utf-8 -*-
"""Чтение данных из Google-таблицы «Объект Победа» через сервисный аккаунт."""
import os
from datetime import date
import gspread
from google.oauth2 import service_account
import streamlit as st

SID = "1J-aoVkq5m2VwiVVM0_Gs7ItaVi-8KY2M7M0KwRk7RiA"
KEY = os.path.join(os.path.dirname(__file__), "..", "secrets", "google_sa.json")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

DEADLINE = date(2026, 7, 17)


@st.cache_resource
def _client():
    # Streamlit Cloud: ключ в st.secrets["gcp_service_account"]
    if "gcp_service_account" in st.secrets:
        info = dict(st.secrets["gcp_service_account"])
        creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    else:
        # Локальная разработка: читаем из файла
        creds = service_account.Credentials.from_service_account_file(KEY, scopes=SCOPES)
    return gspread.authorize(creds).open_by_key(SID)


@st.cache_data(ttl=300)
def get_sheet(name: str):
    """Возвращает все строки листа как list[list[str]]."""
    ws = _client().worksheet(name)
    return ws.get_all_values()


def parse_money(s: str) -> float:
    if s is None:
        return 0.0
    s = str(s).strip()
    if not s:
        return 0.0
    s = s.replace("\xa0", "").replace(" ", "").replace("₽", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def parse_percent(s: str) -> float:
    if not s:
        return 0.0
    s = str(s).strip().replace(",", ".").replace("%", "").strip()
    try:
        v = float(s)
        return v if v > 1.5 else v * 100  # 0.72 -> 72, 72 -> 72
    except ValueError:
        return 0.0


# ---------- Сметы ----------
SMETY = [
    ("Смета_Проектные",    "Проектные работы"),
    ("Смета_Земляные",     "Земляные работы"),
    ("Смета_Строительные", "Строительные работы"),
    ("Смета_Ремонтные",    "Ремонтные работы"),
    ("Смета_Отделочные",   "Отделочные работы"),
    ("Смета_Коммуникации", "Коммуникации инженерные"),
]


@st.cache_data(ttl=300)
def get_smety_summary():
    """Тянет агрегат из листа «Данные_дашборд».
    Колонки: A=Смета, B=Стоимость, C=Выполнено, D=Выполнено_%,
             E=Оплачено, F=Остаток, G=Закуплено."""
    result = []
    try:
        rows = get_sheet("Данные_дашборд")
    except Exception:
        return result
    # Шапка — строка 1, данные с строки 2. Пропускаем «ИТОГО» (она = сумма)
    for r in rows[1:]:
        if len(r) < 2 or not r[0].strip():
            continue
        name = r[0].strip()
        if name.upper() in ("ИТОГО", "ВСЕГО", "TOTAL"):
            continue
        total = parse_money(r[1]) if len(r) > 1 else 0
        done = parse_money(r[2]) if len(r) > 2 else 0
        paid = parse_money(r[4]) if len(r) > 4 else 0
        remain = parse_money(r[5]) if len(r) > 5 else 0
        bought = parse_money(r[6]) if len(r) > 6 else 0
        pct = (done / total * 100) if total > 0 else 0
        # Подбираем sheet_name для перехода
        sheet_name = None
        for sn, disp in SMETY:
            if name.lower() in disp.lower() or disp.lower().startswith(name.lower()):
                sheet_name = sn; break
        result.append({
            "name": name, "sheet": sheet_name,
            "total": total, "done": done, "percent": pct,
            "paid": paid, "remain": remain, "bought": bought,
        })
    return result


@st.cache_data(ttl=300)
def get_totals():
    """Сумма по всем строкам Данные_дашборд: общая стоимость / выполнено / оплачено / закуплено."""
    smety = get_smety_summary()
    return {
        "total": sum(s["total"] for s in smety),
        "done":  sum(s["done"]  for s in smety),
        "paid":  sum(s["paid"]  for s in smety),
        "bought":sum(s["bought"] for s in smety),
        "remain":sum(s["remain"] for s in smety),
    }


# ---------- Дела ----------
@st.cache_data(ttl=300)
def get_dela_df():
    import pandas as pd
    rows = get_sheet("Дела")
    if len(rows) < 4:
        return pd.DataFrame()
    # Шапка строка 3 (idx 2)
    headers = rows[2]
    data = []
    for r in rows[3:]:
        if not any(r):
            continue
        row = list(r) + [""] * (len(headers) - len(r))
        data.append(row[:len(headers)])
    df = pd.DataFrame(data, columns=headers)
    return df


# ---------- Оплаты ----------
@st.cache_data(ttl=300)
def get_oplaty_df():
    import pandas as pd
    rows = get_sheet("Оплаты")
    if len(rows) < 4:
        return pd.DataFrame()
    headers = rows[2]
    data = [r + [""] * (len(headers) - len(r)) for r in rows[3:] if any(r)]
    df = pd.DataFrame([r[:len(headers)] for r in data], columns=headers)
    return df


# ---------- Закупка ----------
@st.cache_data(ttl=300)
def get_zakupka_df():
    import pandas as pd
    rows = get_sheet("Закупка_материалов")
    if len(rows) < 4:
        return pd.DataFrame()
    headers = rows[2]
    data = [r + [""] * (len(headers) - len(r)) for r in rows[3:] if any(r)]
    df = pd.DataFrame([r[:len(headers)] for r in data], columns=headers)
    return df


# ---------- Журнал последних изменений ----------
@st.cache_data(ttl=120)
def get_recent_changes(limit: int = 15):
    """Собирает последние записи из колонки «Журнал» на всех рабочих листах."""
    result = []
    sheets = ["Дела", "Закупка_материалов", "Оплаты"] + [s for s, _ in SMETY]
    for name in sheets:
        try:
            rows = get_sheet(name)
        except Exception:
            continue
        if len(rows) < 4:
            continue
        # Найти колонку «Журнал» в шапке
        headers = rows[2]
        j_idx = next((i for i, h in enumerate(headers) if h.strip() == "Журнал"), -1)
        if j_idx < 0:
            continue
        for r in rows[3:]:
            if len(r) <= j_idx:
                continue
            j = r[j_idx].strip()
            if not j:
                continue
            for line in j.split("\n"):
                line = line.strip()
                if not line:
                    continue
                result.append({"sheet": name, "entry": line})
                if len(result) >= limit * 3:
                    break
    return result[:limit]


# ---------- Дни до сдачи ----------
def days_to_deadline() -> int:
    return (DEADLINE - date.today()).days
