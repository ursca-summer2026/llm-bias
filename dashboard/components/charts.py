"""
Reusable chart components using Plotly and Altair.

Provides consistent, colorblind-safe visualizations across the dashboard.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Colorblind-safe color schemes
PRONOUN_COLORS = {
    "he/him": "#2a78d6",    # Blue
    "she/her": "#1baf7a",   # Green
    "they/them": "#eda100", # Yellow/Orange
    "none": "#898781",      # Gray
}

CATEGORICAL_COLORS = [
    "#2a78d6", "#1baf7a", "#eda100", "#008300",
    "#4a3aa7", "#e34948", "#e87ba4", "#eb6834"
]


def create_stacked_bar(
    data: pd.DataFrame,
    x_col: str,
    color_col: str = "pronoun_group",
    title: str = "",
    x_title: str = "",
    y_title: str = "Percentage",
    as_percentage: bool = True,
) -> go.Figure:
    """Create a stacked bar chart for pronoun distribution.

    Args:
        data: DataFrame with data to plot.
        x_col: Column for x-axis grouping.
        color_col: Column for color grouping (default: pronoun_group).
        title: Chart title.
        x_title: X-axis label.
        y_title: Y-axis label.
        as_percentage: Show as percentages vs counts.

    Returns:
        Plotly Figure object.
    """
    # Group and count
    grouped = data.groupby([x_col, color_col]).size().unstack(fill_value=0)

    if as_percentage:
        grouped = grouped.div(grouped.sum(axis=1), axis=0) * 100

    fig = go.Figure()

    for pronoun in ["he/him", "she/her", "they/them", "none"]:
        if pronoun in grouped.columns:
            fig.add_trace(
                go.Bar(
                    name=pronoun,
                    x=grouped.index,
                    y=grouped[pronoun],
                    marker_color=PRONOUN_COLORS.get(pronoun, "#cccccc"),
                    hovertemplate=f"<b>{pronoun}</b><br>" + "%{y:.1f}%<extra></extra>",
                )
            )

    fig.update_layout(
        barmode="stack",
        title=title,
        xaxis_title=x_title,
        yaxis_title=y_title,
        height=400,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        hovermode="x unified",
    )

    return fig


def create_heatmap(
    data: pd.DataFrame,
    row_col: str,
    col_col: str = "pronoun_group",
    title: str = "",
    row_title: str = "",
    col_title: str = "Pronoun Group",
    annotate: bool = True,
) -> go.Figure:
    """Create a heatmap for pronoun distribution.

    Args:
        data: DataFrame with data to plot.
        row_col: Column for rows.
        col_col: Column for columns (default: pronoun_group).
        title: Chart title.
        row_title: Y-axis label.
        col_title: X-axis label.
        annotate: Whether to show values in cells.

    Returns:
        Plotly Figure object.
    """
    # Create contingency table
    contingency = pd.crosstab(data[row_col], data[col_col])

    # Reorder columns to standard order
    col_order = [c for c in ["he/him", "she/her", "they/them", "none"] if c in contingency.columns]
    contingency = contingency[col_order]

    # Create heatmap
    fig = go.Figure(
        data=go.Heatmap(
            z=contingency.values,
            x=contingency.columns,
            y=contingency.index,
            colorscale="Blues",
            text=contingency.values if annotate else None,
            texttemplate="%{text}" if annotate else None,
            textfont={"size": 12},
            hovertemplate="<b>%{y}</b><br>%{x}: %{z}<extra></extra>",
        )
    )

    fig.update_layout(
        title=title,
        xaxis_title=col_title,
        yaxis_title=row_title,
        height=max(400, len(contingency.index) * 40),
    )

    return fig


def create_grouped_bar(
    data: pd.DataFrame,
    x_col: str,
    group_col: str,
    y_col: str,
    title: str = "",
    x_title: str = "",
    y_title: str = "",
) -> go.Figure:
    """Create a grouped bar chart.

    Args:
        data: DataFrame with data to plot.
        x_col: Column for x-axis.
        group_col: Column for grouping bars.
        y_col: Column for y values.
        title: Chart title.
        x_title: X-axis label.
        y_title: Y-axis label.

    Returns:
        Plotly Figure object.
    """
    fig = px.bar(
        data,
        x=x_col,
        y=y_col,
        color=group_col,
        barmode="group",
        title=title,
        labels={x_col: x_title, y_col: y_title},
        color_discrete_sequence=CATEGORICAL_COLORS,
    )

    fig.update_layout(
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return fig


def create_scatter_matrix(
    similarity_matrix: pd.DataFrame,
    title: str = "Model Similarity Matrix",
) -> go.Figure:
    """Create a similarity matrix heatmap.

    Args:
        similarity_matrix: Square DataFrame with similarity scores.
        title: Chart title.

    Returns:
        Plotly Figure object.
    """
    fig = go.Figure(
        data=go.Heatmap(
            z=similarity_matrix.values,
            x=similarity_matrix.columns,
            y=similarity_matrix.index,
            colorscale="RdYlGn",
            zmin=0,
            zmax=1,
            text=np.round(similarity_matrix.values, 3),
            texttemplate="%{text}",
            textfont={"size": 10},
            hovertemplate="<b>%{y}</b> vs <b>%{x}</b><br>Similarity: %{z:.3f}<extra></extra>",
        )
    )

    fig.update_layout(
        title=title,
        xaxis_title="Model",
        yaxis_title="Model",
        height=500,
    )

    return fig


def create_pie_chart(
    data: pd.DataFrame,
    values_col: str,
    names_col: str,
    title: str = "",
) -> go.Figure:
    """Create a pie chart for pronoun distribution.

    Args:
        data: DataFrame with data to plot.
        values_col: Column for pie slice sizes.
        names_col: Column for slice labels.
        title: Chart title.

    Returns:
        Plotly Figure object.
    """
    fig = px.pie(
        data,
        values=values_col,
        names=names_col,
        title=title,
        color=names_col,
        color_discrete_map=PRONOUN_COLORS,
    )

    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>%{value} responses<br>%{percent}<extra></extra>",
    )

    fig.update_layout(height=400)

    return fig


def create_line_chart(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: str = None,
    title: str = "",
    x_title: str = "",
    y_title: str = "",
) -> go.Figure:
    """Create a line chart for time series analysis.

    Args:
        data: DataFrame with data to plot.
        x_col: Column for x-axis (e.g., time, version).
        y_col: Column for y values.
        color_col: Optional column for multiple lines.
        title: Chart title.
        x_title: X-axis label.
        y_title: Y-axis label.

    Returns:
        Plotly Figure object.
    """
    if color_col:
        fig = px.line(
            data,
            x=x_col,
            y=y_col,
            color=color_col,
            title=title,
            labels={x_col: x_title, y_col: y_title},
            color_discrete_map=PRONOUN_COLORS,
            markers=True,
        )
    else:
        fig = px.line(
            data,
            x=x_col,
            y=y_col,
            title=title,
            labels={x_col: x_title, y_col: y_title},
            markers=True,
        )

    fig.update_layout(
        height=400,
        hovermode="x unified",
    )

    return fig
