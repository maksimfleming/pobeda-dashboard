# -*- coding: utf-8 -*-
"""Дашборд «Объект Победа» — главная (Обзор) в стиле тёмно-синих BI-дашбордов."""
import streamlit as st
import plotly.graph_objects as go
from datetime import date
from sheets import (
    get_smety_summary, get_totals, get_dela_df,
    get_recent_changes, days_to_deadline, DEADLINE,
)

st.set_page_config(
    page_title="Победа — Дашборд",
    page_icon="🏗️", layout="wide",
    initial_sidebar_state="expanded",
)

# ============ PWA метаданные (для установки на телефон) ============
st.markdown("""
<script>
(function() {
    const head = window.parent.document.head;
    const add = (tag, attrs) => {
        if ([...head.querySelectorAll(tag)].some(e => Object.entries(attrs)
            .every(([k,v]) => e.getAttribute(k) === v))) return;
        const el = document.createElement(tag);
        Object.entries(attrs).forEach(([k,v]) => el.setAttribute(k,v));
        head.appendChild(el);
    };
    // Web App Manifest
    add('link', {rel: 'manifest', href: '/app/static/manifest.json'});
    // Цвет адресной строки на Android Chrome
    add('meta', {name: 'theme-color', content: '#1e3a5f'});
    // iOS — Add to Home Screen
    add('meta', {name: 'apple-mobile-web-app-capable', content: 'yes'});
    add('meta', {name: 'apple-mobile-web-app-status-bar-style', content: 'black-translucent'});
    add('meta', {name: 'apple-mobile-web-app-title', content: 'Победа'});
    add('link', {rel: 'apple-touch-icon', sizes: '180x180', href: '/app/static/icon-180.png'});
    add('link', {rel: 'apple-touch-icon', sizes: '192x192', href: '/app/static/icon-192.png'});
    // Viewport — масштаб 1
    let vp = head.querySelector('meta[name="viewport"]');
    if (vp) vp.setAttribute('content', 'width=device-width,initial-scale=1,viewport-fit=cover');
})();
</script>
""", unsafe_allow_html=True)

# ============ Глобальный CSS ============
CSS = """
<style>
    .stApp { background: #0c1424; }
    .main > div { padding-top: 0.8rem; }
    h1, h2, h3, h4 { color: #f8fafc !important; }
    [data-testid="stSidebar"] { background: #0a111e; border-right: 1px solid #1e2d4a; }

    /* === Шапка === */
    .top-bar {
        display: flex; align-items: center; justify-content: space-between;
        background: linear-gradient(135deg, #1e3a5f 0%, #2d4f7f 100%);
        border: 1px solid #2d4f7f; border-radius: 16px;
        padding: 20px 30px; margin-bottom: 24px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.3);
    }
    .top-bar-left h1 { color: #f8fafc; margin: 0; font-size: 28px; font-weight: 700; }
    .top-bar-left p  { color: rgba(248,250,252,.7); margin: 8px 0 0 0; font-size: 15px; }
    .top-bar-right { text-align: right; }
    .top-bar-right .date { color: rgba(248,250,252,.85); font-size: 18px; font-weight: 500; line-height: 1.4; }
    .top-bar-right .deadline {
        color: #fbbf24; font-size: 44px; font-weight: 800;
        line-height: 1.1; margin: 6px 0; letter-spacing: -0.02em;
    }
    .top-bar-right .deadline-sub {
        color: rgba(251,191,36,.85); font-size: 16px; font-weight: 600;
        letter-spacing: 0.04em; text-transform: uppercase;
    }

    /* === Цветные KPI плитки === */
    .kpi-card {
        background: linear-gradient(135deg, var(--c1), var(--c2));
        border-radius: 16px; padding: 22px 24px; height: 100%;
        position: relative; overflow: hidden; min-height: 140px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }
    .kpi-card-label {
        font-size: 13px; color: rgba(255,255,255,0.85); font-weight: 600;
        text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 8px;
        max-width: 70%; line-height: 1.3;
    }
    .kpi-card-value {
        font-size: 30px; color: white; font-weight: 700; line-height: 1.1;
        margin-bottom: 4px;
    }
    .kpi-card-sub { font-size: 13px; color: rgba(255,255,255,0.75); }
    .kpi-card-donut {
        position: absolute; top: 16px; right: 16px;
        width: 70px; height: 70px;
    }

    /* === Карточки сметы (Spireflow-стиль) === */
    .smeta-row {
        display: flex; align-items: center; gap: 16px;
        background: #1a2940; border: 1px solid #1e2d4a; border-radius: 12px;
        padding: 14px 18px; margin-bottom: 10px;
    }
    .smeta-row-name { flex: 1.2; color: #f8fafc; font-weight: 600; font-size: 14px; }
    .smeta-row-sum  { flex: 1; color: #cbd5e1; font-size: 13px; }
    .smeta-row-bar  {
        flex: 2; height: 10px; background: #0c1424; border-radius: 6px;
        overflow: hidden; position: relative;
    }
    .smeta-row-bar-fill { height: 100%; border-radius: 6px;
        background: linear-gradient(90deg, var(--c1), var(--c2)); }
    .smeta-row-pct {
        flex: 0 0 50px; text-align: right;
        font-weight: 700; font-size: 14px; color: var(--c1);
    }

    /* === Журнал === */
    .journal-row {
        background: #1a2940; border: 1px solid #1e2d4a; border-radius: 10px;
        padding: 10px 14px; margin-bottom: 6px; font-size: 13px; color: #cbd5e1;
        border-left: 3px solid #3b82f6;
    }
    .journal-row .tag {
        display: inline-block; background: #3b82f6; color: white;
        font-size: 10px; font-weight: 700; padding: 2px 8px;
        border-radius: 4px; margin-right: 8px; text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* === Хедер секции === */
    .section-title {
        color: #f8fafc; font-size: 22px; font-weight: 700;
        margin: 18px 0 18px 0; padding-bottom: 10px;
        letter-spacing: 0.02em;
        border-bottom: 1px solid #1e2d4a;
    }
    .section-title-sub {
        color: #94a3b8; font-size: 13px; font-weight: 400;
        margin-top: 2px; letter-spacing: 0;
    }

    /* === Контейнер графика === */
    .chart-box {
        background: #1a2940; border: 1px solid #1e2d4a; border-radius: 14px;
        padding: 16px; margin-bottom: 14px;
    }

    /* ============ МОБИЛЬНАЯ ВЕРСИЯ (≤768px) ============ */
    @media (max-width: 768px) {
        .main > div { padding-top: 0.4rem; padding-left: 0.5rem; padding-right: 0.5rem; }
        /* Шапка — стек вертикально */
        .top-bar {
            flex-direction: column; padding: 14px 16px;
            text-align: center; gap: 8px;
        }
        .top-bar-left h1 { font-size: 18px; }
        .top-bar-left p  { font-size: 12px; }
        .top-bar-right { text-align: center; }
        .top-bar-right .deadline { font-size: 36px; }
        .top-bar-right .deadline-sub { font-size: 13px; }
        .top-bar-right .date { font-size: 14px; }

        /* KPI плитки — компактнее */
        .kpi-card { padding: 14px 16px; min-height: 100px; }
        .kpi-card-label { font-size: 10px; max-width: 100%; }
        .kpi-card-value { font-size: 22px; }
        .kpi-card-sub { display: none; }       /* убираем дублирующие цифры */
        .kpi-card-donut { width: 48px; height: 48px; top: 10px; right: 10px; }

        /* Прогресс по сметам — стек */
        .smeta-row {
            flex-wrap: wrap; gap: 6px; padding: 10px 12px;
        }
        .smeta-row-name { flex: 1 1 100%; font-size: 13px; }
        .smeta-row-sum  { flex: 1 1 60%; font-size: 11px; }
        .smeta-row-pct  { flex: 0 0 auto; font-size: 13px; }
        .smeta-row-bar  { flex: 1 1 100%; height: 8px; }

        /* Заголовки секций — компактнее */
        .section-title { font-size: 16px; margin: 12px 0 10px 0; }

        /* Журнал */
        .journal-row { font-size: 12px; padding: 8px 10px; }

        /* Sidebar по умолчанию свёрнут на мобиле */
        [data-testid="stSidebar"] {
            position: absolute !important;
            transform: translateX(-100%);
            transition: transform 0.3s;
        }
    }

    /* Очень узкие (≤480px, например iPhone SE) */
    @media (max-width: 480px) {
        .kpi-card-value { font-size: 18px; }
        .top-bar-right .deadline { font-size: 30px; }
    }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ============ Утилиты ============
def fmt_rub(x):
    if x >= 1_000_000:
        return f"{x/1_000_000:.2f} млн ₽"
    if x >= 1_000:
        return f"{x/1_000:.0f} тыс ₽"
    return f"{x:,.0f} ₽".replace(",", " ")


def donut_svg(pct: float, size: int = 70, stroke: int = 8) -> str:
    """Маленький круговой donut для KPI-карточки."""
    pct = max(0, min(100, pct))
    r = (size - stroke) / 2
    c = 2 * 3.14159 * r
    dash = c * pct / 100
    return f"""
    <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
        <circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none"
                stroke="rgba(255,255,255,0.18)" stroke-width="{stroke}"/>
        <circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none"
                stroke="white" stroke-width="{stroke}"
                stroke-dasharray="{dash:.1f} {c:.1f}" stroke-linecap="round"
                transform="rotate(-90 {size/2} {size/2})"/>
        <text x="{size/2}" y="{size/2 + 5}" text-anchor="middle"
              fill="white" font-size="14" font-weight="700">{pct:.0f}%</text>
    </svg>
    """


def kpi_card(label: str, value: str, sub: str, color1: str, color2: str,
             pct: float = None) -> str:
    donut = f'<div class="kpi-card-donut">{donut_svg(pct)}</div>' if pct is not None else ''
    return (
        f'<div class="kpi-card" style="--c1:{color1}; --c2:{color2};">'
        f'{donut}'
        f'<div class="kpi-card-label">{label}</div>'
        f'<div class="kpi-card-value">{value}</div>'
        f'<div class="kpi-card-sub">{sub}</div>'
        f'</div>'
    )


# ============ Шапка ============
days = days_to_deadline()
today_str = date.today().strftime("%d.%m.%Y")

st.markdown(f"""
<div class="top-bar">
    <div class="top-bar-left">
        <h1>Объект «Победа» — Усадьба в Победе</h1>
        <p>Генподряд 78 · Заказчик Равиль М.Д. · Сегодня {today_str}</p>
    </div>
    <div class="top-bar-right">
        <div class="deadline">{abs(days)} дн</div>
        <div class="deadline-sub">до сдачи объекта</div>
        <div class="date">Срок: {DEADLINE.strftime('%d.%m.%Y')}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ============ KPI ============
smety = get_smety_summary()
t = get_totals()
total_cost = t["total"]
total_done = t["done"]
paid_sum = t["paid"]
buy_sum = t["bought"]
total_pct = (total_done / total_cost * 100) if total_cost > 0 else 0
paid_pct = (paid_sum / total_cost * 100) if total_cost else 0

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.markdown(kpi_card("Стоимость объекта", fmt_rub(total_cost),
                         f"{total_cost:,.0f} ₽".replace(",", " "),
                         "#3b82f6", "#2563eb"), unsafe_allow_html=True)
with k2:
    st.markdown(kpi_card("Выполнено работ", fmt_rub(total_done),
                         f"{total_done:,.0f} ₽".replace(",", " "),
                         "#f97316", "#ea580c", pct=total_pct), unsafe_allow_html=True)
with k3:
    st.markdown(kpi_card("Оплачено", fmt_rub(paid_sum),
                         f"{paid_sum:,.0f} ₽".replace(",", " "),
                         "#a855f7", "#7e22ce", pct=paid_pct), unsafe_allow_html=True)
with k4:
    st.markdown(kpi_card("Закуплено материалов", fmt_rub(buy_sum),
                         f"{buy_sum:,.0f} ₽".replace(",", " "),
                         "#14b8a6", "#0d9488"), unsafe_allow_html=True)
with k5:
    remain = total_cost - total_done
    remain_pct = (remain / total_cost * 100) if total_cost else 0
    st.markdown(kpi_card("Осталось работ", fmt_rub(remain),
                         f"{remain:,.0f} ₽".replace(",", " "),
                         "#ec4899", "#be185d", pct=remain_pct), unsafe_allow_html=True)

# Кнопка обновления — компактная справа
col_btn_l, col_btn_r = st.columns([6, 1])
with col_btn_r:
    if st.button("Обновить", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# ============ Прогресс по сметам + Donut статусов ============
col_smety, col_stats = st.columns([5, 4])

with col_smety:
    st.markdown('<div class="section-title">ПРОГРЕСС ПО СМЕТАМ</div>', unsafe_allow_html=True)
    color_pairs = [
        ("#3b82f6", "#1d4ed8"),   # blue
        ("#f97316", "#c2410c"),   # orange
        ("#a855f7", "#6b21a8"),   # purple
        ("#14b8a6", "#0f766e"),   # teal
        ("#ec4899", "#9d174d"),   # pink
        ("#fbbf24", "#b45309"),   # amber
    ]
    for i, s in enumerate(smety):
        c1, c2 = color_pairs[i % len(color_pairs)]
        pct = min(s["percent"], 100)
        st.markdown(f"""
        <div class="smeta-row" style="--c1:{c1}; --c2:{c2};">
            <div class="smeta-row-name">{s['name']}</div>
            <div class="smeta-row-sum">{fmt_rub(s['done'])} / {fmt_rub(s['total'])}</div>
            <div class="smeta-row-bar"><div class="smeta-row-bar-fill"
                style="width: {pct}%; --c1:{c1}; --c2:{c2};"></div></div>
            <div class="smeta-row-pct">{s['percent']:.0f}%</div>
        </div>
        """, unsafe_allow_html=True)

with col_stats:
    st.markdown('<div class="section-title">СТАТУСЫ ДЕЛ</div>', unsafe_allow_html=True)
    dela_df = get_dela_df()
    if not dela_df.empty and "Статус Дела" in dela_df.columns:
        stat_counts = dela_df["Статус Дела"].value_counts()
        stat_counts = stat_counts[stat_counts.index != ""]
        if len(stat_counts):
            colors = {"Сделано": "#10b981", "В работе": "#a855f7",
                      "План": "#fbbf24", "Просрочено": "#ef4444"}
            total_dels = int(stat_counts.sum())
            fig = go.Figure(go.Pie(
                labels=stat_counts.index, values=stat_counts.values, hole=0.65,
                marker=dict(colors=[colors.get(s, "#64748b") for s in stat_counts.index],
                            line=dict(color="#0c1424", width=3)),
                textinfo="label+percent", textposition="outside",
                textfont=dict(color="#e5e7eb", size=12),
                hovertemplate="<b>%{label}</b><br>%{value} дел<extra></extra>",
            ))
            fig.add_annotation(
                text=f"<b style='font-size:32px'>{total_dels}</b><br>"
                     f"<span style='color:#94a3b8; font-size:11px'>ВСЕГО ДЕЛ</span>",
                showarrow=False, font=dict(color="#f8fafc"), x=0.5, y=0.5)
            fig.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10),
                              height=320, paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-title">КУРАТОРЫ</div>', unsafe_allow_html=True)
    if not dela_df.empty and "Куратор" in dela_df.columns:
        kur = dela_df["Куратор"].value_counts()
        kur = kur[kur.index != ""].head(6)
        if len(kur):
            fig = go.Figure(go.Bar(
                x=kur.values, y=kur.index, orientation="h",
                marker=dict(color="#3b82f6", line=dict(color="#1d4ed8", width=1)),
                text=kur.values, textposition="outside",
                textfont=dict(color="#f8fafc")))
            fig.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=30),
                              height=240, paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)",
                              xaxis=dict(color="#94a3b8", gridcolor="#1e2d4a", showgrid=False),
                              yaxis=dict(color="#e5e7eb"), font=dict(color="#e5e7eb"))
            st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ============ Последние изменения ============
st.markdown('<div class="section-title">ПОСЛЕДНИЕ ИЗМЕНЕНИЯ</div>', unsafe_allow_html=True)
changes = get_recent_changes(limit=12)
if changes:
    cols_j = st.columns(2)
    for i, c in enumerate(changes):
        with cols_j[i % 2]:
            st.markdown(f"""
            <div class="journal-row">
                <span class="tag">{c['sheet'][:14]}</span>{c['entry']}
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("Журнал пока пуст — изменения появятся когда команда начнёт работу.")

st.markdown("---")
st.caption("🤖 MaxJarvis · Дашборд «Победа» · v0.3 · Меню разделов слева ↑")
