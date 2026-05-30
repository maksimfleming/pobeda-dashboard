# -*- coding: utf-8 -*-
"""Страница «Дела» — детальный обзор задач по объекту."""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import date
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from sheets import get_dela_df

st.set_page_config(page_title="Дела · Победа", page_icon="✅", layout="wide")

st.markdown("""
<style>
    .stApp { background: #0c1424; }
    h1, h2, h3 { color: #f8fafc !important; }
    .metric-box {
        background: #1a2940; border: 1px solid #1e2d4a; border-radius: 12px;
        padding: 16px; text-align: center;
    }
    .metric-box-label { font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-box-value { font-size: 26px; font-weight: 700; color: #f8fafc; margin-top: 4px; }
    .stDataFrame { background: #1a2940; }
    [data-testid="stSidebar"] { background: #0a111e; border-right: 1px solid #1e2d4a; }
    .section-title {
        color: #f8fafc; font-size: 22px; font-weight: 700;
        margin: 18px 0 18px 0; padding-bottom: 10px;
        letter-spacing: 0.02em;
        border-bottom: 1px solid #1e2d4a;
    }
</style>
""", unsafe_allow_html=True)

st.title("Дела по объекту «Победа»")
st.caption("Все задачи · Фильтры по куратору, статусу, объекту, смете")

df = get_dela_df()
if df.empty:
    st.warning("Лист «Дела» пуст или ошибка загрузки.")
    st.stop()

# Удалить служебные колонки
df = df[[c for c in df.columns if not c.startswith("Column")]]
df = df[df["Задача"].str.strip() != ""] if "Задача" in df.columns else df

# ============ Фильтры в sidebar ============
st.sidebar.header("Фильтры")
filters = {}
for col in ["Объект", "Смета", "Раздел", "Статус Дела", "Куратор", "Ответственный"]:
    if col in df.columns:
        vals = sorted([v for v in df[col].unique() if v and v.strip()])
        if vals:
            sel = st.sidebar.multiselect(col, vals, default=[])
            if sel:
                filters[col] = sel

f = df.copy()
for col, vals in filters.items():
    f = f[f[col].isin(vals)]

# ============ KPI Дел ============
total = len(f)
done = (f["Статус Дела"] == "Сделано").sum() if "Статус Дела" in f.columns else 0
work = (f["Статус Дела"] == "В работе").sum() if "Статус Дела" in f.columns else 0
plan = (f["Статус Дела"] == "План").sum() if "Статус Дела" in f.columns else 0
late = (f["Статус Дела"] == "Просрочено").sum() if "Статус Дела" in f.columns else 0

# Доп: «горячие» — те у которых срок < 7 дней и статус не Сделано
hot = 0
if "Срок исполнения" in f.columns and "Статус Дела" in f.columns:
    today = date.today()
    for _, row in f.iterrows():
        if row["Статус Дела"] == "Сделано":
            continue
        try:
            d = pd.to_datetime(row["Срок исполнения"], errors="coerce", dayfirst=True)
            if pd.notna(d):
                days = (d.date() - today).days
                if 0 <= days <= 7:
                    hot += 1
        except Exception:
            pass

cols = st.columns(6)
metrics = [("Всего", total, "#4ade80"), ("План", plan, "#fbbf24"),
           ("В работе", work, "#a78bfa"), ("Сделано", done, "#10b981"),
           ("Просрочено", late, "#f87171"), ("Горит (<7 дн)", hot, "#fb923c")]
for c, (lab, val, color) in zip(cols, metrics):
    with c:
        st.markdown(f"""<div class="metric-box" style="border-top: 3px solid {color};">
            <div class="metric-box-label">{lab}</div>
            <div class="metric-box-value">{val}</div></div>""", unsafe_allow_html=True)

st.markdown("---")

# ============ Разбивки ============
g1, g2 = st.columns(2)
with g1:
    st.markdown('<div class="section-title">ПО СМЕТАМ</div>', unsafe_allow_html=True)
    if "Смета" in f.columns:
        by_smeta = f[f["Смета"] != ""]["Смета"].value_counts()
        if len(by_smeta):
            fig = go.Figure(go.Bar(
                x=by_smeta.values, y=by_smeta.index, orientation="h",
                marker=dict(color="#4ade80", line=dict(color="#243530", width=1)),
                text=by_smeta.values, textposition="outside"))
            fig.update_layout(height=300, margin=dict(t=10, b=10, l=10, r=40),
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              xaxis=dict(color="#9ca3af", gridcolor="#243530"),
                              yaxis=dict(color="#e5e7eb"), font=dict(color="#e5e7eb"))
            st.plotly_chart(fig, use_container_width=True,
                            config={"displayModeBar": False, "staticPlot": True})

with g2:
    st.markdown('<div class="section-title">ПО КУРАТОРАМ И СТАТУСАМ</div>', unsafe_allow_html=True)
    if "Куратор" in f.columns and "Статус Дела" in f.columns:
        ct = f[(f["Куратор"] != "") & (f["Статус Дела"] != "")].groupby(
            ["Куратор", "Статус Дела"]).size().reset_index(name="кол-во")
        if not ct.empty:
            colors = {"Сделано": "#4ade80", "В работе": "#a78bfa",
                      "План": "#fbbf24", "Просрочено": "#f87171"}
            fig = go.Figure()
            for stat in ["Сделано", "В работе", "План", "Просрочено"]:
                d = ct[ct["Статус Дела"] == stat]
                if not d.empty:
                    fig.add_trace(go.Bar(
                        x=d["кол-во"], y=d["Куратор"], orientation="h",
                        name=stat, marker_color=colors.get(stat, "#64748b")))
            fig.update_layout(barmode="stack", height=300,
                              margin=dict(t=30, b=10, l=10, r=10),
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              xaxis=dict(color="#9ca3af", gridcolor="#243530"),
                              yaxis=dict(color="#e5e7eb"), font=dict(color="#e5e7eb"),
                              legend=dict(orientation="h", y=-0.15))
            st.plotly_chart(fig, use_container_width=True,
                            config={"displayModeBar": False, "staticPlot": True})

st.markdown("---")

# ============ Просроченные / горящие — отдельным блоком ============
if "Срок исполнения" in f.columns and "Статус Дела" in f.columns:
    st.markdown('<div class="section-title">СРОЧНЫЕ И ПРОСРОЧЕННЫЕ</div>', unsafe_allow_html=True)
    rows = []
    today = date.today()
    for _, row in f.iterrows():
        if row["Статус Дела"] == "Сделано" or not row["Срок исполнения"]:
            continue
        try:
            d = pd.to_datetime(row["Срок исполнения"], errors="coerce", dayfirst=True)
            if pd.notna(d):
                days = (d.date() - today).days
                if days <= 7:
                    rows.append({
                        "Задача": row.get("Задача", ""),
                        "Куратор": row.get("Куратор", ""),
                        "Срок": d.strftime("%d.%m.%Y"),
                        "Осталось": f"{days} дн" if days >= 0 else f"⚠ {-days} дн назад",
                        "Статус": row.get("Статус Дела", ""),
                    })
        except Exception:
            pass
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Срочных и просроченных задач нет")

# ============ Полная таблица ============
st.markdown(f'<div class="section-title">ВСЕ ДЕЛА ({len(f)})</div>', unsafe_allow_html=True)
show_cols = ["№", "Объект", "Смета", "Раздел", "Задача", "Ответственный",
             "Срок исполнения", "Статус Дела", "Куратор"]
show_cols = [c for c in show_cols if c in f.columns]
st.dataframe(f[show_cols], use_container_width=True, hide_index=True, height=500)
