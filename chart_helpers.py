import plotly.graph_objects as go

# Color constants for traces
C1 = "#3B82F6"  # primary blue
C2 = "#F97316"  # comparison orange

def chart_layout(xtitle, ytitle):
    """
    Generate a standardized Plotly layout dictionary for all charts.

    Parameters
    ----------
    xtitle : str
        The title for the X-axis.
    ytitle : str
        The title for the Y-axis.

    Returns
    -------
    dict
        A dictionary containing Plotly layout configuration parameters.
    """
    return dict(
        xaxis_title=xtitle, 
        yaxis_title=ytitle,
        template="plotly_dark",
        plot_bgcolor='rgba(0,0,0,0)', 
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=10, t=30, b=20),
        hovermode=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        font=dict(family="Inter, sans-serif", size=12),
    )

def add_grid(fig):
    """
    Add a subtle grid to the X and Y axes of a Plotly figure.

    Parameters
    ----------
    fig : plotly.graph_objects.Figure
        The figure to apply the grid to.

    Returns
    -------
    plotly.graph_objects.Figure
        The updated figure with grid lines added.
    """
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.05)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.05)')
    return fig
