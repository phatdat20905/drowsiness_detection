# ============================================================
#  components/charts.py  –  Plotly chart helpers (dark theme)
# ============================================================

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Optional

# ── Plotly dark layout shared ─────────────────────────────────
_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(28,35,51,0.6)",
    font=dict(family="Inter", color="#8b949e", size=12),
    margin=dict(l=12, r=12, t=36, b=12),
    xaxis=dict(showgrid=True,  gridcolor="#30363d", linecolor="#30363d"),
    yaxis=dict(showgrid=True,  gridcolor="#30363d", linecolor="#30363d"),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#30363d",
                borderwidth=1, font=dict(size=11)),
    hoverlabel=dict(bgcolor="#1c2333", bordercolor="#30363d",
                    font_family="Inter"),
)

COLORS = {
    "accent":  "#2f81f7",
    "success": "#3fb950",
    "warning": "#d29922",
    "danger":  "#f85149",
    "purple":  "#bc8cff",
    "cyan":    "#39c5cf",
}


def alerts_timeseries(rows) -> go.Figure:
    """Biểu đồ cảnh báo theo ngày, phân loại TIRED / DROWSY."""
    if not rows:
        return _empty_chart("Chưa có dữ liệu")

    df = pd.DataFrame(rows, columns=["day", "status", "cnt"])
    fig = go.Figure()

    for status, color in [("TIRED", COLORS["warning"]), ("DROWSY", COLORS["danger"])]:
        sub = df[df.status == status]
        if not sub.empty:
            fig.add_trace(go.Bar(
                x=sub.day, y=sub.cnt, name=status,
                marker_color=color, opacity=0.85,
            ))

    fig.update_layout(
        **_BASE,
        title=dict(text="Cảnh báo theo ngày", font=dict(size=14, color="#e6edf3")),
        barmode="stack",
        height=280,
        xaxis_tickformat="%d/%m",
    )
    return fig


def status_donut(rows) -> go.Figure:
    """Donut: tỉ lệ NORMAL / TIRED / DROWSY."""
    if not rows:
        return _empty_chart("Chưa có dữ liệu")

    df = pd.DataFrame(rows, columns=["day", "status", "cnt"])
    grp = df.groupby("status")["cnt"].sum().reset_index()

    color_map = {
        "NORMAL": COLORS["success"],
        "TIRED":  COLORS["warning"],
        "DROWSY": COLORS["danger"],
    }
    colors = [color_map.get(s, "#8b949e") for s in grp.status]

    fig = go.Figure(go.Pie(
        labels=grp.status, values=grp.cnt,
        hole=0.62, marker=dict(colors=colors, line=dict(color="#0d1117", width=2)),
        textinfo="percent", hovertemplate="%{label}: %{value}<extra></extra>",
    ))
    fig.update_layout(
        **_BASE,
        title=dict(text="Phân loại cảnh báo", font=dict(size=14, color="#e6edf3")),
        height=280,
        showlegend=True,
    )
    return fig


def driver_bar(rows) -> go.Figure:
    """Horizontal bar: top tài xế có nhiều cảnh báo nhất."""
    if not rows:
        return _empty_chart("Chưa có dữ liệu")

    df = pd.DataFrame(rows, columns=["full_name", "username", "total",
                                      "drowsy", "tired", "min_score"])
    df = df.head(8).sort_values("total")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df.full_name, x=df.tired,
        name="TIRED", orientation="h",
        marker_color=COLORS["warning"], opacity=0.85,
    ))
    fig.add_trace(go.Bar(
        y=df.full_name, x=df.drowsy,
        name="DROWSY", orientation="h",
        marker_color=COLORS["danger"], opacity=0.85,
    ))
    fig.update_layout(
        **_BASE,
        title=dict(text="Cảnh báo theo tài xế", font=dict(size=14, color="#e6edf3")),
        barmode="stack",
        height=300,
        xaxis_title="Số cảnh báo",
    )
    return fig


def monthly_trend(rows) -> go.Figure:
    """Line: xu hướng cảnh báo theo tháng."""
    if not rows:
        return _empty_chart("Chưa có dữ liệu")

    df = pd.DataFrame(rows, columns=["month", "total_alerts", "drowsy_count"])

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.month, y=df.total_alerts,
        mode="lines+markers", name="Tổng cảnh báo",
        line=dict(color=COLORS["accent"], width=2),
        marker=dict(size=6),
        fill="tozeroy", fillcolor="rgba(47,129,247,0.08)",
    ))
    fig.add_trace(go.Scatter(
        x=df.month, y=df.drowsy_count,
        mode="lines+markers", name="DROWSY",
        line=dict(color=COLORS["danger"], width=2, dash="dot"),
        marker=dict(size=6),
    ))
    fig.update_layout(
        **_BASE,
        title=dict(text="Xu hướng theo tháng", font=dict(size=14, color="#e6edf3")),
        height=260,
    )
    return fig


def score_gauge(score: float) -> go.Figure:
    if score >= 70:
        color = COLORS["success"]
    elif score >= 40:
        color = COLORS["warning"]
    else:
        color = COLORS["danger"]

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={"x": [0, 1], "y": [0, 1]},
        number={"font": {"color": color, "size": 42, "family": "Inter"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#8b949e",
                     "tickfont": {"color": "#8b949e", "size": 10}},
            "bar":  {"color": color, "thickness": 0.22},
            "bgcolor": "#1c2333",
            "borderwidth": 0,
            "steps": [
                {"range": [0,  40], "color": "#3a1a1a"},
                {"range": [40, 70], "color": "#3a2e1a"},
                {"range": [70,100], "color": "#1e3a2a"},
            ],
            "threshold": {
                "line": {"color": color, "width": 3},
                "thickness": 0.85,
                "value": score,
            },
        },
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#8b949e"),
        margin=dict(l=20, r=20, t=20, b=20),
        height=200,
    )
    return fig


def ear_mar_scatter(rows) -> go.Figure:
    """Scatter EAR vs MAR, màu theo status."""
    if not rows:
        return _empty_chart("Chưa có dữ liệu")

    cols = ["id", "user_id", "session_id", "timestamp", "status",
            "score", "ear", "mar", "blink_rate", "head_pose",
            "cnn_prob_eye", "cnn_prob_mouth", "fused_eye", "fused_mouth",
            "full_name", "username"]
    df = pd.DataFrame(rows, columns=cols)

    color_map = {"TIRED": COLORS["warning"], "DROWSY": COLORS["danger"]}
    fig = go.Figure()
    for status, color in color_map.items():
        sub = df[df.status == status]
        if not sub.empty:
            fig.add_trace(go.Scatter(
                x=sub.ear, y=sub.mar, mode="markers",
                name=status,
                marker=dict(color=color, size=6, opacity=0.75),
                hovertemplate=(
                    "<b>%{customdata}</b><br>"
                    "EAR: %{x:.3f}<br>MAR: %{y:.3f}<extra></extra>"
                ),
                customdata=sub.full_name,
            ))
    fig.add_vline(x=0.21, line_dash="dot", line_color="#484f58",
                  annotation_text="EAR threshold", annotation_font_color="#484f58")
    fig.add_hline(y=0.60, line_dash="dot", line_color="#484f58",
                  annotation_text="MAR threshold", annotation_font_color="#484f58")
    fig.update_layout(
        **_BASE,
        title=dict(text="Phân tán EAR vs MAR", font=dict(size=14, color="#e6edf3")),
        xaxis_title="EAR (Eye Aspect Ratio)",
        yaxis_title="MAR (Mouth Aspect Ratio)",
        height=300,
    )
    return fig


def _empty_chart(msg: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=msg, xref="paper", yref="paper",
                       x=0.5, y=0.5, showarrow=False,
                       font=dict(color="#484f58", size=14))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(28,35,51,0.6)",
        height=260,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig
