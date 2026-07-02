import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from app.reports.models import ReportChart

ROUTE_COLOR = "#2F3EE0"
LIVE_COLOR = "#1B8C6F"
ATTN_COLOR = "#C4432B"
INK_COLOR = "#14181A"
LINE_COLOR = "#DCE0DA"
PALETTE = [ROUTE_COLOR, LIVE_COLOR, ATTN_COLOR, "#8A9390", "#5B6461"]


def render_chart_png(chart: ReportChart, width_px: int = 900, height_px: int = 480, dpi: int = 150) -> bytes:
    fig, ax = plt.subplots(figsize=(width_px / dpi, height_px / dpi), dpi=dpi)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")

    if chart.chart_type == "pie":
        first_series = next(iter(chart.series.values()), [])
        ax.pie(first_series, labels=chart.labels, colors=PALETTE, autopct="%1.0f%%", textprops={"color": INK_COLOR, "fontsize": 9})
    else:
        positions = list(range(len(chart.labels)))
        if chart.chart_type == "line":
            for i, (name, values) in enumerate(chart.series.items()):
                ax.plot(positions, values, marker="o", color=PALETTE[i % len(PALETTE)], label=name, linewidth=2)
        else:
            series_count = max(len(chart.series), 1)
            bar_width = 0.8 / series_count
            for i, (name, values) in enumerate(chart.series.items()):
                offsets = [p + i * bar_width - 0.4 + bar_width / 2 for p in positions]
                ax.bar(offsets, values, width=bar_width, color=PALETTE[i % len(PALETTE)], label=name)
        ax.set_xticks(positions)
        rotate = len(chart.labels) > 6
        ax.set_xticklabels(chart.labels, rotation=30 if rotate else 0, ha="right" if rotate else "center", fontsize=9, color=INK_COLOR)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(LINE_COLOR)
        ax.spines["bottom"].set_color(LINE_COLOR)
        ax.tick_params(colors=INK_COLOR)
        ax.grid(axis="y", color=LINE_COLOR, linewidth=0.6)
        ax.set_axisbelow(True)
        if len(chart.series) > 1:
            ax.legend(frameon=False, fontsize=8, labelcolor=INK_COLOR)

    ax.set_title(chart.title, fontsize=11, color=INK_COLOR, loc="left")
    fig.tight_layout()

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", facecolor=fig.get_facecolor())
    plt.close(fig)
    return buffer.getvalue()
