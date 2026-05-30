# -*- coding: utf-8 -*-
"""Страница «Закупки материалов» — детальный обзор с разбивкой по сметам и разделам."""
import streamlit as st
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from sheets import get_zakupka_df, get_smety_summary, parse_money

st.set_page_config(page_title="Закупки · Победа", page_icon="🛒", layout="wide")

# === CSS ===
st.markdown("""
<style>
    .stApp { background: #0c1424; }
    h1, h2, h3 { color: #f8fafc !important; }
    [data-testid="stSidebar"] { background: #0a111e; border-right: 1px solid #1e2d4a; }

    .metric-box {
        background: #1a2940; border: 1px solid #1e2d4a; border-radius: 12px;
        padding: 16px; text-align: center;
    }
    .metric-box-label { font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-box-value { font-size: 26px; font-weight: 700; color: #f8fafc; margin-top: 4px; }
    .metric-box-sub { font-size: 12px; color: #94a3b8; margin-top: 4px; }

    .section-title {
        color: #f8fafc; font-size: 22px; font-weight: 700;
        margin: 18px 0 18px 0; padding-bottom: 10px;
        letter-spacing: 0.02em;
        border-bottom: 1px solid #1e2d4a;
    }

    /* Карточка сметы */
    .smeta-card-big {
        display: flex; align-items: center; gap: 16px;
        background: #1a2940; border: 1px solid #1e2d4a; border-radius: 12px;
        padding: 14px 18px; margin-bottom: 4px;
    }
    .smeta-card-name {
        flex: 1.5; color: #f8fafc; font-weight: 600; font-size: 15px;
        display: flex; align-items: center; gap: 10px;
    }
    .smeta-card-dot {
        width: 12px; height: 12px; border-radius: 50%;
        background: var(--c1); flex-shrink: 0;
    }
    .smeta-card-info { flex: 1.2; color: #cbd5e1; font-size: 13px; }
    .smeta-card-bar  {
        flex: 2.5; height: 12px; background: #0c1424; border-radius: 6px;
        overflow: hidden;
    }
    .smeta-card-fill {
        height: 100%; border-radius: 6px;
        background: linear-gradient(90deg, var(--c1), var(--c2));
    }
    .smeta-card-pct {
        flex: 0 0 60px; text-align: right;
        font-weight: 700; font-size: 15px; color: var(--c1);
    }

    /* Подкарточка раздела */
    .razdel-row {
        display: flex; align-items: center; gap: 12px;
        background: #0f1c30; border-left: 3px solid var(--c1);
        padding: 8px 14px; margin: 4px 0 4px 32px;
        border-radius: 6px; font-size: 13px;
    }
    .razdel-row-name { flex: 2; color: #e5e7eb; }
    .razdel-row-cnt  { flex: 0 0 100px; color: #94a3b8; text-align: right; }
    .razdel-row-sum  { flex: 0 0 130px; color: #f8fafc; font-weight: 600; text-align: right; }
</style>
""", unsafe_allow_html=True)


def fmt_rub(x):
    if x >= 1_000_000:
        return f"{x/1_000_000:.2f} млн ₽"
    if x >= 1_000:
        return f"{x/1_000:.0f} тыс ₽"
    return f"{x:,.0f} ₽".replace(",", " ")


SMETA_COLORS = [
    ("#3b82f6", "#1d4ed8"),   # Проектные — синий
    ("#f97316", "#c2410c"),   # Земляные — оранжевый
    ("#a855f7", "#6b21a8"),   # Строительные — фиолетовый
    ("#14b8a6", "#0f766e"),   # Ремонтные — бирюзовый
    ("#ec4899", "#9d174d"),   # Отделочные — розовый
    ("#fbbf24", "#b45309"),   # Коммуникации — янтарный
    ("#94a3b8", "#475569"),   # Материалы — серый
]
SMETA_ORDER = ["Проектные", "Земляные", "Строительные",
               "Ремонтные", "Отделочные", "Коммуникации", "Материалы"]


st.title("Закупка материалов")
st.caption("Объект «Победа» · Поставщики, разбивка по сметам и разделам")

df = get_zakupka_df()
if df.empty:
    st.warning("Лист «Закупка_материалов» пуст или ошибка загрузки.")
    st.stop()

df = df[[c for c in df.columns if not c.startswith("Column")]]
if "Наименование" in df.columns:
    df = df[df["Наименование"].str.strip() != ""]

if "Сумма, ₽" in df.columns:
    df["_сумма"] = df["Сумма, ₽"].apply(parse_money)
else:
    df["_сумма"] = 0

# === Фильтры ===
st.sidebar.header("Фильтры")
filters = {}
for col in ["Поставщик", "Смета", "Раздел", "Ответственный"]:
    if col in df.columns:
        vals = sorted([v for v in df[col].unique() if v and v.strip()])
        if vals:
            sel = st.sidebar.multiselect(col, vals, default=[])
            if sel:
                filters[col] = sel

f = df.copy()
for col, vals in filters.items():
    f = f[f[col].isin(vals)]

# === KPI ===
total_sum = f["_сумма"].sum()
n_items = len(f)
n_postavshikov = len(set([v for v in f.get("Поставщик", []) if v and v.strip()])) if "Поставщик" in f.columns else 0
n_smet = len(set([v for v in f.get("Смета", []) if v and v.strip()])) if "Смета" in f.columns else 0
avg = total_sum / n_items if n_items else 0

cols = st.columns(5)
metrics = [
    ("Общая сумма", fmt_rub(total_sum), f"{total_sum:,.0f} ₽".replace(",", " "), "#4ade80"),
    ("Позиций", str(n_items), "наименований", "#60a5fa"),
    ("Поставщиков", str(n_postavshikov), "разных", "#a78bfa"),
    ("Смет затронуто", str(n_smet), "из 7", "#fbbf24"),
    ("Средний чек", fmt_rub(avg), "на позицию", "#fb923c"),
]
for c, (lab, val, sub, color) in zip(cols, metrics):
    with c:
        st.markdown(f"""<div class="metric-box" style="border-top: 3px solid {color};">
            <div class="metric-box-label">{lab}</div>
            <div class="metric-box-value">{val}</div>
            <div class="metric-box-sub">{sub}</div></div>""", unsafe_allow_html=True)

st.markdown("---")

# === Топ поставщиков ===
st.markdown('<div class="section-title">ТОП ПОСТАВЩИКОВ ПО СУММАМ</div>', unsafe_allow_html=True)
if "Поставщик" in f.columns:
    by_post = f[f["Поставщик"] != ""].groupby("Поставщик")["_сумма"].sum().sort_values(ascending=True)
    if len(by_post):
        fig = go.Figure(go.Bar(
            x=by_post.values, y=by_post.index, orientation="h",
            marker=dict(color="#a78bfa", line=dict(color="#1e2d4a", width=1)),
            text=[fmt_rub(v) for v in by_post.values], textposition="outside",
            textfont=dict(color="#f8fafc")))
        fig.update_layout(height=max(280, len(by_post) * 40),
                          margin=dict(t=10, b=10, l=10, r=100),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          xaxis=dict(color="#94a3b8", gridcolor="#1e2d4a"),
                          yaxis=dict(color="#e5e7eb"), font=dict(color="#e5e7eb"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Нет данных по поставщикам — заполни колонку Поставщик в Закупке")

st.markdown("---")

# === Разбивка по сметам с разделами ===
st.markdown('<div class="section-title">РАЗБИВКА ПО СМЕТАМ И РАЗДЕЛАМ</div>', unsafe_allow_html=True)

# Получаем total по каждой смете для процентов прогресса
smety_totals = {s["name"].lower(): s for s in get_smety_summary()}


def find_total_for(name: str):
    """Найти стоимость сметы из Данные_дашборд по подстроке."""
    name_l = name.lower()
    for k, v in smety_totals.items():
        if name_l in k or k in name_l:
            return v["total"]
    return 0


# Группируем по смете
if "Смета" in f.columns:
    sm_groups = f[f["Смета"] != ""].groupby("Смета")
    seen = set()
    order = []
    for canonical in SMETA_ORDER:
        for sm in sm_groups.groups.keys():
            if canonical.lower() in sm.lower() and sm not in seen:
                order.append(sm)
                seen.add(sm)
    # Добавим оставшиеся (если не в SMETA_ORDER)
    for sm in sm_groups.groups.keys():
        if sm not in seen:
            order.append(sm)

    if not order:
        st.info("В закупках нет ни одной строки со сметой. Заполни колонку 'Смета' на листе Закупка_материалов.")

    for idx, sm in enumerate(order):
        group = sm_groups.get_group(sm)
        sm_sum = group["_сумма"].sum()
        sm_total = find_total_for(sm)
        pct = (sm_sum / sm_total * 100) if sm_total > 0 else 0
        c1, c2 = SMETA_COLORS[idx % len(SMETA_COLORS)]

        # Карточка сметы
        st.markdown(f"""
        <div class="smeta-card-big" style="--c1:{c1}; --c2:{c2};">
            <div class="smeta-card-name">
                <div class="smeta-card-dot"></div>{sm}
            </div>
            <div class="smeta-card-info">
                {fmt_rub(sm_sum)} закуплено · {len(group)} поз. · стоимость сметы {fmt_rub(sm_total)}
            </div>
            <div class="smeta-card-bar">
                <div class="smeta-card-fill" style="width: {min(pct, 100)}%;"></div>
            </div>
            <div class="smeta-card-pct">{pct:.0f}%</div>
        </div>
        """, unsafe_allow_html=True)

        # Подкарточки разделов
        if "Раздел" in group.columns:
            by_razd = group.groupby(group["Раздел"].fillna(""))["_сумма"].agg(["sum", "count"]).reset_index()
            by_razd.columns = ["razdel", "summ", "cnt"]
            by_razd = by_razd.sort_values("summ", ascending=False)
            for _, row in by_razd.iterrows():
                rname = row["razdel"].strip() if row["razdel"] else "— Без раздела —"
                st.markdown(f"""
                <div class="razdel-row" style="--c1:{c1};">
                    <div class="razdel-row-name">{rname}</div>
                    <div class="razdel-row-cnt">{int(row['cnt'])} поз.</div>
                    <div class="razdel-row-sum">{fmt_rub(row['summ'])}</div>
                </div>
                """, unsafe_allow_html=True)

            # Развёрнутая таблица позиций
            with st.expander(f"Показать все {len(group)} позиций этой сметы"):
                show_cols = ["№", "Наименование", "Сумма, ₽", "Поставщик", "Раздел",
                             "Ответственный", "Телефон"]
                show_cols = [c for c in show_cols if c in group.columns]
                st.dataframe(group[show_cols], use_container_width=True, hide_index=True)
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

# === Позиции без сметы ===
no_smeta = f[f["Смета"].fillna("").str.strip() == ""]
if not no_smeta.empty:
    st.markdown(f'<div class="section-title">БЕЗ СМЕТЫ ({len(no_smeta)})</div>', unsafe_allow_html=True)
    st.caption("Эти позиции не привязаны к смете — добавь смету в колонке Смета на листе Закупка_материалов")
    show_cols = ["№", "Наименование", "Сумма, ₽", "Поставщик", "Ответственный"]
    show_cols = [c for c in show_cols if c in no_smeta.columns]
    st.dataframe(no_smeta[show_cols], use_container_width=True, hide_index=True)

st.markdown("---")

# === Полная таблица (можно скрыть в expander) ===
with st.expander(f"Полная таблица всех закупок ({len(f)})"):
    show_cols = ["№", "Наименование", "Сумма, ₽", "Поставщик", "Смета",
                 "Раздел", "Ответственный", "Телефон", "Почта"]
    show_cols = [c for c in show_cols if c in f.columns]
    st.dataframe(f[show_cols], use_container_width=True, hide_index=True, height=500)
