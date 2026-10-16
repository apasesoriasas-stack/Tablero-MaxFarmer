"""Tablero de planificación de importaciones avícolas - Max Farmer S.A.S.

16 SKU Clase A · Pronóstico a 3 meses (lead time 90-120 días) · Modelo vigente: SES.
Ejecutar con:  streamlit run app.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------- parámetros
LT = 3            # horizonte = lead time en meses
Z = 1.65          # nivel de servicio 95 %
TASA = 0.11       # costo financiero anual
FUT = ["2026-01", "2026-02", "2026-03"]
MES_DECISION = "enero 2026"

AZUL, NARANJA, ROJO, AMBAR, VERDE = "#2a78d6", "#eb6834", "#c63434", "#b27800", "#0c8a0c"
ESTADO = {"crit": "■ Quiebre inminente", "warn": "▲ Pedir ahora", "good": "● Cubierto"}
COLOR_ESTADO = {"crit": ROJO, "warn": AMBAR, "good": VERDE}

st.set_page_config(page_title="Planificación de Importaciones Avícolas", page_icon="📦", layout="wide")
st.markdown(
    """<style>
    .block-container{padding-top:1.6rem}
    div[data-testid="stMetric"]{background:#fff;border:1px solid #dde2dc;border-radius:8px;padding:10px 14px}
    .eyebrow{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:#1f6f4a;font-weight:600}
    .meta{font-size:13px;color:#4f5a54;text-align:right;padding-top:28px}
    </style>""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------- utilidades
def fmt(v: float, d: int = 0) -> str:
    """Formato numérico Ecuador: 1.234,56"""
    s = f"{v:,.{d}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def mlabel(m: str) -> str:
    y, mm = m.split("-")
    return ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"][int(mm) - 1] + "-" + y[2:]


@st.cache_data
def cargar() -> dict:
    base = Path(__file__).parent
    ruta = base / "data" / "resultados.json"
    if not ruta.exists():          # también funciona si el JSON está junto a app.py
        ruta = base / "resultados.json"
    D = json.loads(ruta.read_text(encoding="utf-8"))
    for s in D["skus"]:
        s["f3"] = sum(s["f"])
        s["fm"] = s["f3"] / 3
        s["ss"] = Z * s["sd"]
        s["cob"] = s["stock"] / s["fm"] if s["fm"] > 0 else math.inf
        s["ped"] = max(0, math.ceil(s["f3"] + s["ss"] - s["stock"]))
        s["pedUsd"] = s["ped"] * s["cost"]
        s["invUsd"] = s["stock"] * s["cost"]
        s["state"] = "crit" if s["cob"] < 1 else ("warn" if s["cob"] < LT else "good")
        s["nq"] = sum(s["quiebre"])
    return D


def grafico_linea(hist, f, sd, quiebre=None, titulo=""):
    """Venta real, pronóstico y rango de error (90 %)."""
    meses = D["months"] + FUT
    x_hist = [mlabel(m) for m in D["months"]]
    x_fut = [mlabel(m) for m in meses[len(hist) - 1:]]
    banda = sd / math.sqrt(3) * Z
    hi = [hist[-1]] + [v + banda for v in f]
    lo = [hist[-1]] + [max(0, v - banda) for v in f]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_fut + x_fut[::-1], y=hi + lo[::-1], fill="toself",
                             fillcolor="rgba(235,104,52,.16)", line=dict(width=0), mode="lines",
                             name="Rango de error", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=x_hist, y=hist, mode="lines+markers", name="Venta real",
                             line=dict(color=AZUL, width=2), marker=dict(size=4)))
    fig.add_trace(go.Scatter(x=x_fut, y=[hist[-1]] + list(f), mode="lines+markers", name="Pronóstico",
                             line=dict(color=NARANJA, width=2, dash="dash"), marker=dict(size=6)))
    if quiebre:
        qx = [x_hist[i] for i, q in enumerate(quiebre) if q]
        qy = [hist[i] for i, q in enumerate(quiebre) if q]
        if qx:
            fig.add_trace(go.Scatter(x=qx, y=qy, mode="markers", name="Quiebre probable",
                                     marker=dict(color=ROJO, size=10)))
    fig.update_layout(title=titulo, height=380, margin=dict(l=10, r=10, t=40, b=80),
                      legend=dict(orientation="h", y=-0.32), plot_bgcolor="white",
                      yaxis=dict(gridcolor="#e5e8e3", title="Unidades"),
                      xaxis=dict(categoryorder="array", categoryarray=[mlabel(m) for m in meses], tickangle=-45,
                                 tickmode="array", tickvals=[mlabel(m) for m in meses[::3]]))
    return fig


D = cargar()

# ---------------------------------------------------------------- encabezado
c1, c2 = st.columns([3, 2])
c1.markdown('<div class="eyebrow">Línea avícola · 16 SKU Clase A</div>', unsafe_allow_html=True)
c1.markdown("## Planificación de Importaciones Avícolas")
c2.markdown(f'<div class="meta">Mes de decisión: <b>{MES_DECISION}</b> · Horizonte: 3 meses '
            f'(lead time 90–120 días) · Modelo vigente: <b>SES</b></div>', unsafe_allow_html=True)
st.divider()

# ---------------------------------------------------------------- filtros globales
f1, f2, _ = st.columns([1, 2, 2])
familias = ["Todas"] + sorted({s["fam"] for s in D["skus"]})
fam = f1.selectbox("Familia", familias)
lista = [s for s in D["skus"] if fam == "Todas" or s["fam"] == fam]
opciones = ["Todos"] + [f'{s["sku"]} · {s["prod"][:40]}' for s in lista]
sel_sku = f2.selectbox("SKU", opciones)
S = lista if sel_sku == "Todos" else [s for s in lista if s["sku"] == sel_sku.split(" · ")[0]]

tab1, tab2, tab3, tab4 = st.tabs(["1. Resumen", "2. Pronóstico y reposición",
                                  "3. Precisión del modelo", "4. Calidad de datos y quiebres"])

# ---------------------------------------------------------------- vista 1: resumen
with tab1:
    f3 = sum(s["f3"] for s in S)
    inv = sum(s["invUsd"] for s in S)
    ped = sum(s["pedUsd"] for s in S)
    riesgo = [s for s in S if s["state"] != "good"]
    ses = next(g for g in D["glob"] if g["m"] == "SES")
    naive = next(g for g in D["glob"] if g["m"] == "Naive")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Demanda próximos 3 meses", f"{fmt(f3)} u.", help="Enero–marzo 2026, modelo SES")
    k1.caption("ene–mar 2026, modelo SES")
    k2.metric("Inventario a costo", f"${fmt(inv, 2)}")
    k2.caption(f"cierre 2025 · costo financiero ≈ ${fmt(inv * TASA, 2)}/año (11 %)")
    k3.metric("SKU que requieren pedido", f"{len(riesgo)} de {len(S)}")
    k3.caption(f'{sum(s["state"] == "crit" for s in S)} con quiebre inminente')
    k4.metric("Pedido sugerido a costo", f"${fmt(ped, 2)}")
    k4.caption(f'WAPE del modelo vigente: {fmt(ses["wape"], 1)} % (Naive: {fmt(naive["wape"], 1)} %)')

    g1, g2 = st.columns([1.25, 1])
    hist = [sum(s["hist"][i] for s in S) for i in range(len(D["months"]))]
    fc = [sum(s["f"][k] for s in S) for k in range(3)]
    sd = math.sqrt(sum(s["sd"] ** 2 for s in S))
    titulo = f'{S[0]["sku"]} · {S[0]["prod"]}' if len(S) == 1 else \
        f'Ventas mensuales y pronóstico · {"16 SKU" if fam == "Todas" else fam}'
    g1.plotly_chart(grafico_linea(hist, fc, sd, S[0]["quiebre"] if len(S) == 1 else None, titulo),
                    use_container_width=True, key="el1")
    with g2:
        st.markdown("**SKU que requieren pedido**")
        st.caption("Ordenados por cobertura, de menor a mayor.")
        if riesgo:
            st.dataframe(pd.DataFrame([{
                "SKU": s["sku"], "Producto": s["prod"][:28], "Cobertura (meses)": round(s["cob"], 1),
                "Pedido (u.)": s["ped"], "Estado": ESTADO[s["state"]]}
                for s in sorted(riesgo, key=lambda s: s["cob"])]),
                hide_index=True, use_container_width=True, key="el2")
        else:
            st.success("Todos los SKU de esta selección cubren el lead time de 3 meses.")

# ---------------------------------------------------------------- vista 2: reposición
with tab2:
    st.markdown("**Tabla de reposición por SKU**")
    st.caption("Pedido sugerido = pronóstico 3 meses + stock de seguridad − stock al cierre de 2025. "
               "Stock de seguridad = 1,65 × desviación del error acumulado de 3 meses del modelo SES "
               "(nivel de servicio 95 %). Cobertura = stock ÷ pronóstico mensual.")
    orden = sorted(S, key=lambda s: s["cob"])
    tabla = pd.DataFrame([{
        "SKU": s["sku"], "Producto": s["prod"][:34], "Familia": s["fam"],
        "Pronóst. 3 m": round(s["f3"]), "Stock": int(s["stock"]),
        "Cobertura (meses)": round(s["cob"], 1) if s["cob"] < 99 else 99.0,
        "Stock seguridad": round(s["ss"]), "Pedido sugerido": s["ped"],
        "Pedido USD": round(s["pedUsd"], 2), "Estado": ESTADO[s["state"]]} for s in orden])

    def color_estado(v):
        for k, lab in ESTADO.items():
            if v == lab:
                return f"color:{COLOR_ESTADO[k]};font-weight:600"
        return ""

    evento = st.dataframe(
        tabla.style.map(color_estado, subset=["Estado"]).format(
            {"Pedido USD": lambda v: f"${fmt(v, 2)}", "Cobertura (meses)": lambda v: fmt(v, 1),
             "Pronóst. 3 m": fmt, "Stock": fmt, "Stock seguridad": fmt, "Pedido sugerido": fmt}),
        hide_index=True, use_container_width=True, on_select="rerun", selection_mode="single-row", key="repo_tabla")
    st.markdown(f'**Total:** {fmt(tabla["Pedido sugerido"].sum())} u. · '
                f'${fmt(tabla["Pedido USD"].sum(), 2)} a costo')
    st.caption("■ Quiebre inminente: cobertura menor a 1 mes · ▲ Pedir ahora: menor al lead time (3 meses) "
               "· ● Cubierto: 3 meses o más. Seleccione una fila para ver el detalle del SKU.")

    filas = evento.selection.rows if evento and evento.selection else []
    s = orden[filas[0]] if filas else (orden[0] if orden else None)
    if s:
        st.plotly_chart(grafico_linea(s["hist"], s["f"], s["sd"], s["quiebre"], f'{s["sku"]} · {s["prod"]}'),
                        use_container_width=True, key="el3")
        st.caption(f'Mejor modelo en validación: **{s["best"]}** (WAPE {fmt(s["bestW"], 1)} %, '
                   f'Bias {"+" if s["bestB"] > 0 else ""}{fmt(s["bestB"], 1)} %). '
                   f'WAPE con SES: {fmt(s["wape"]["SES"], 1)} %. Meses con quiebre probable: {s["nq"]}.')
    st.info("Los pedidos en tránsito no se registran en Sheyla ni en el inventario. Si hay una importación "
            "en camino, Comercio Exterior debe restarla del pedido sugerido. Stock y costo: Inventario Final 2025.")

# ---------------------------------------------------------------- vista 3: precisión
with tab3:
    G = D["glob"]
    p1, p2 = st.columns([1.2, 1])
    with p1:
        st.markdown("**WAPE global por modelo**")
        st.caption("Validación con origen móvil: 10 orígenes, horizonte de 3 meses, todo 2025. Menor es mejor. "
                   "La línea punteada es el modelo Naive.")
        fig = go.Figure(go.Bar(x=[g["wape"] for g in G], y=[g["m"] for g in G], orientation="h",
                               marker_color=[AZUL if i == 0 else "rgba(42,120,214,.45)" for i in range(len(G))],
                               text=[f'{fmt(g["wape"], 1)} %' for g in G], textposition="outside"))
        fig.add_vline(x=naive["wape"], line_dash="dash", line_color="#4f5a54")
        fig.update_layout(height=320, margin=dict(l=10, r=40, t=10, b=10), plot_bgcolor="white",
                          yaxis=dict(autorange="reversed"), xaxis=dict(range=[0, 145], gridcolor="#e5e8e3"))
        st.plotly_chart(fig, use_container_width=True, key="el4")
    with p2:
        st.markdown("**Detalle por modelo**")
        st.caption("Bias positivo: el modelo pide de más. Negativo: pide de menos. MASE < 1: supera al Naive.")
        st.dataframe(pd.DataFrame([{"Modelo": g["m"], "WAPE %": g["wape"], "Bias %": g["bias"],
                                    "MASE": g["mase"], "WAPE USD %": g["wusd"], "WAPE 3 m acum. %": g["acum"]}
                                   for g in G]), hide_index=True, use_container_width=True, key="el5")

    st.markdown("**WAPE (%) por SKU y modelo**")
    st.caption("En negrita, el mejor modelo de cada SKU. El color indica el nivel de error.")
    modelos = [g["m"] for g in G]
    z = [[s["wape"][m] for m in modelos] for s in S]
    txt = [[(f'<b>{fmt(s["wape"][m], 1)}</b>' if m == s["best"] else fmt(s["wape"][m], 1)) for m in modelos] for s in S]
    hm = go.Figure(go.Heatmap(z=z, x=modelos, y=[f'{s["sku"]} {s["prod"][:28]}' for s in S], text=txt,
                              texttemplate="%{text}", colorscale=[[0, "#e3f3e3"], [1, "#e08a8a"]],
                              zmin=40, zmax=160, showscale=False))
    hm.update_layout(height=max(220, 34 * len(S) + 60), margin=dict(l=10, r=10, t=10, b=10),
                     yaxis=dict(autorange="reversed"))
    st.plotly_chart(hm, use_container_width=True, key="el6")

    st.markdown("**Nivel familia: pronóstico directo vs. suma por SKU**")
    st.caption("Sumar los pronósticos de cada SKU con SES da el menor error agregado (68,8 %).")
    st.dataframe(pd.DataFrame([{"Modelo": f["m"], "Directo por familia %": f["d"], "Suma por SKU %": f["b"]}
                               for f in D["fam"]]), hide_index=True, key="fam_tabla")

# ---------------------------------------------------------------- vista 4: calidad y quiebres
with tab4:
    ceros = [(s, i) for s in S for i, v in enumerate(s["hist"]) if v == 0]
    nq = sum(s["quiebre"][i] for s, i in ceros)
    neg = [s["sku"] for s in S if any(v is not None and v < 0 for v in s["stockIni"])]
    q1, q2, q3, q4 = st.columns(4)
    q1.metric("Meses con venta cero", fmt(len(ceros)))
    q1.caption(f"de {len(S) * 36} SKU-mes")
    q2.metric("Quiebres probables", fmt(nq))
    q2.caption(f'{sum(s["quiebre"][i] for s, i in ceros if D["months"][i].startswith("2025"))} en 2025')
    q3.metric("Ceros sin demanda", fmt(len(ceros) - nq))
    q3.caption("había stock y no se vendió")
    q4.metric("SKU con stock negativo", fmt(len(neg)))
    q4.caption(", ".join(neg) or "ninguno")

    st.markdown("**Mapa de meses por SKU**")
    st.caption("Cada celda es un mes (enero 2023 a diciembre 2025). Un mes sin venta se marca como quiebre "
               "probable si al inicio del mes había 2 unidades o menos en el stock reconstruido.")
    zc = [[0 if v > 0 else (2 if s["quiebre"][i] else 1) for i, v in enumerate(s["hist"])] for s in S]
    tip = [[f'{s["sku"]} · {mlabel(D["months"][i])}: {fmt(v)} u. · stock inicial {fmt(s["stockIni"][i])}'
            for i, v in enumerate(s["hist"])] for s in S]
    mp = go.Figure(go.Heatmap(z=zc, x=[mlabel(m) for m in D["months"]], y=[s["sku"] for s in S],
                              text=tip, hoverinfo="text", zmin=0, zmax=2, showscale=False, xgap=2, ygap=2,
                              colorscale=[[0, "#dde2dc"], [0.33, "#dde2dc"], [0.34, AMBAR], [0.66, AMBAR],
                                          [0.67, ROJO], [1, ROJO]]))
    mp.update_layout(height=max(200, 26 * len(S) + 60), margin=dict(l=10, r=10, t=10, b=10),
                     yaxis=dict(autorange="reversed"), plot_bgcolor="white")
    st.plotly_chart(mp, use_container_width=True, key="el7")
    st.caption("Gris: con venta · Ámbar: cero sin demanda (había stock) · Rojo: quiebre probable")

    st.markdown("**Meses con venta cero**")
    st.dataframe(pd.DataFrame([{"SKU": s["sku"], "Producto": s["prod"], "Mes": mlabel(D["months"][i]),
                                "Stock inicial": s["stockIni"][i],
                                "Clasificación": "■ Quiebre probable" if s["quiebre"][i] else "▲ Sin demanda"}
                               for s, i in ceros]), hide_index=True, use_container_width=True, key="el8")
    st.caption("Stock reconstruido hacia atrás desde el inventario de cierre 2025: stock inicial = stock final "
               "− compras + ventas. Los valores negativos indican diferencias entre fuentes.")
