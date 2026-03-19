import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px
import pycountry

country_list = [country.name for country in pycountry.countries]


def show_histogram(df_raw, column_name):
    st.header(f"Showing histogram for column: {column_name}")

    country = st.selectbox(
        "Select a country",
        options=country_list,
        index=country_list.index("Brazil"),
    )
    st.markdown(f"Showing data for: **{country}**")

    try:
        country_df = df_raw[df_raw["entity"] == country].dropna(subset=[column_name, "year"])

        if country_df.empty:
            st.warning(f"No data found for '{country}'.")
            return

        fig, ax = plt.subplots(figsize=(12, 5))
        colors = ["#d32f2f" if v < 0 else "#2e7d32" for v in country_df[column_name]]
        ax.bar(country_df["year"], country_df[column_name], color=colors, edgecolor="white", linewidth=0.5)
        ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
        ax.set_title(
            f"{column_name.replace('-', ' ').title()} — {country}",
            fontsize=16,
            fontweight="bold",
        )
        ax.set_xlabel("Year", fontsize=13)
        ax.set_ylabel("Value", fontsize=13)
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    except (KeyError, ValueError) as e:
        st.error(f"Error: {e}")


def show_histogram_red_list_index(processor, column_name="red-list-index"):
    st.header("Red List Index — Country Comparison")

    countries = st.multiselect(
        "Select countries",
        options=country_list,
        default=["Chile", "Georgia", "Italy", "Serbia"],
        key="histogram_rli_countries",
    )

    if not countries:
        st.warning("Please select at least one country.")
        return

    try:
        df_plot = processor.get_red_list_index(countries)

        # Get the most recent value per country
        latest = (
            df_plot.dropna(subset=[column_name])
            .sort_values("year")
            .groupby("entity")
            .last()
            .reset_index()
        )

        if latest.empty:
            st.warning("No data found for selected countries.")
            return

        latest = latest.sort_values(column_name, ascending=True)
        colors = ["#d32f2f" if v < 0.9 else "#2e7d32" for v in latest[column_name]]

        fig, ax = plt.subplots(figsize=(10, max(4, len(countries) * 0.6)))
        bars = ax.barh(latest["entity"], latest[column_name], color=colors, edgecolor="white", linewidth=0.5)

        for bar, val in zip(bars, latest[column_name]):
            ax.text(
                bar.get_width() + 0.005,
                bar.get_y() + bar.get_height() / 2,
                f"{val:.3f}",
                va="center",
                fontsize=10,
            )

        ax.axvline(1.0, color="black", linewidth=0.8, linestyle="--", label="Max (1.0 = Not Threatened)")
        ax.set_xlim(0, 1.08)
        ax.set_xlabel("Red List Index", fontsize=13)
        ax.set_title("Red List Index — Latest Available Value per Country", fontsize=14, fontweight="bold")
        ax.grid(axis="x", linestyle="--", alpha=0.4)
        ax.legend(fontsize=10)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    except Exception as e:
        st.error(f"Error: {e}")


def _interpolate_plasma(stops, pos):
    """Return the hex color at `pos` by linearly interpolating between plasma stops."""
    pos = max(0.0, min(1.0, pos))
    for i in range(len(stops) - 1):
        p0, c0 = stops[i]
        p1, c1 = stops[i + 1]
        if p0 <= pos <= p1:
            t = (pos - p0) / (p1 - p0) if p1 != p0 else 0
            r = int(int(c0[1:3], 16) + t * (int(c1[1:3], 16) - int(c0[1:3], 16)))
            g = int(int(c0[3:5], 16) + t * (int(c1[3:5], 16) - int(c0[3:5], 16)))
            b = int(int(c0[5:7], 16) + t * (int(c1[5:7], 16) - int(c0[5:7], 16)))
            return f"#{r:02x}{g:02x}{b:02x}"
    return stops[-1][1]


_PLASMA_STOPS = [
    (0.000, "#0d0887"), (0.042, "#1b0990"), (0.083, "#280b98"),
    (0.125, "#3607a0"), (0.167, "#4302a7"), (0.208, "#5002ac"),
    (0.250, "#5c01a6"), (0.292, "#6a00a8"), (0.333, "#7201a8"),
    (0.375, "#8405a7"), (0.417, "#9512a1"), (0.458, "#a52c60"),
    (0.500, "#b5367a"), (0.542, "#c33d80"), (0.583, "#d1426a"),
    (0.625, "#de5046"), (0.667, "#ed7953"), (0.708, "#f48849"),
    (0.750, "#fb9f3a"), (0.792, "#fbb130"), (0.833, "#fac228"),
    (0.875, "#f7d324"), (0.917, "#f4e322"), (0.958, "#f2f022"),
    (1.000, "#f0f921"),
]


def draw_chloropleth_map(df, column_name):
    filtered_df = df[df[column_name].notnull()].copy()

    real_min = filtered_df[column_name].min()
    real_max = filtered_df[column_name].max()

    EPSILON   = 1e-6
    zero_pos  = (0 - real_min) / (real_max - real_min)

    custom_colorscale = []

    for pos, color in _PLASMA_STOPS:
        if pos < zero_pos - EPSILON:
            custom_colorscale.append([pos, color])

    custom_colorscale += [
        [max(0.0, zero_pos - EPSILON), _interpolate_plasma(_PLASMA_STOPS, zero_pos - EPSILON)],
        [zero_pos,                      "#aaaaaa"],
        [min(1.0, zero_pos + EPSILON),  _interpolate_plasma(_PLASMA_STOPS, zero_pos + EPSILON)],
    ]

    for pos, color in _PLASMA_STOPS:
        if pos > zero_pos + EPSILON:
            custom_colorscale.append([pos, color])

    custom_colorscale = sorted(custom_colorscale, key=lambda x: x[0])

    fig = px.choropleth(
        filtered_df,
        locations="ISO_A3",
        locationmode="ISO-3",
        color=column_name,
        color_continuous_scale=custom_colorscale,
        range_color=[real_min, real_max],
        projection="natural earth",
        hover_name="NAME",
        hover_data={"year": True, column_name: True, "ISO_A3": False},
    )

    tick_vals = [real_min + i * (real_max - real_min) / 4 for i in range(5)]
    fig.update_coloraxes(
        colorbar=dict(
            tickvals=tick_vals,
            ticktext=[f"{v:.1f}" for v in tick_vals],
            title=column_name,
        )
    )
    fig.update_geos(fitbounds="locations", visible=False, center={"lat": 20, "lon": 0})
    fig.update_layout(height=450, margin={"r": 0, "t": 0, "l": 0, "b": 0})

    st.write(
        f"This map shows the most recent available data for **{column_name}**. "
        "Darker colors indicate higher values. "
        "Countries with a value of **0** are shown in **grey**. "
        "Countries with no data are shown in the default map background."
    )
    st.plotly_chart(fig, width="stretch", key=f"map_{column_name}")