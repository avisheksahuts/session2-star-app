
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.set_page_config(page_title="Stellar Data Explorer", layout="wide")

SUN_T = 5772.0
Z_SUN = 0.02

st.title("Stellar Data Explorer · Session 2 Part D")
st.write("Explore stellar evolution, metallicity, and the Hertzsprung–Russell diagram.")

# Metallicity: changing this slider reruns the Streamlit script
lz = st.slider("log10 metallicity", -4.0, -1.4, -1.7, step=0.05)
Z = 10 ** lz
zr = Z / Z_SUN

# Stellar parameters remain interactive
c1, c2 = st.columns(2)
with c1:
    mass = st.slider(
        "Stellar mass (solar masses)",
        0.1, 300.0, 1.0, step=0.1
    )
with c2:
    age = st.slider(
        "Stellar age (billion years)",
        0.0001, 1000.0, 5.0,
        step=0.1
    )

# Stellar evolution model
def stellar_times(m, zr):
    zt = zr ** 0.1
    t_pre = 0.03 * m ** -1.5 * zt
    t_ms = (
        10.0 * m ** -2.5 * zt
        * (1 + 2.5 * np.exp(-m / 0.12))
        + 0.0025
    )
    t_giant = 1.15 * t_ms
    return t_pre, t_ms, t_giant


def star_now(m, Z, age):
    zr = Z / Z_SUN
    t_pre, t_ms, t_giant = stellar_times(m, zr)

    L_ms = m ** 3.5 * zr ** -0.1
    T_ms = SUN_T * m ** 0.475 * zr ** -0.025

    if age < t_pre:
        phase = "Protostar"
        T = T_ms * 0.65
        L = L_ms * 0.2
    elif age < t_ms:
        phase = "Main sequence"
        T = T_ms
        L = L_ms
    elif age < t_giant:
        if m < 0.25:
            phase = "Main sequence"
            T = T_ms
            L = L_ms
        else:
            phase = "Giant"
            T = min(4800.0, T_ms * 0.65)
            L = L_ms * 100.0
    else:
        if m < 0.25 or m < 8:
            phase = "White dwarf"
            T = 12000.0
            L = max(1e-4, L_ms * 0.01)
        elif Z < 0.001 and 140 <= m <= 260:
            phase = "Pair-instability supernova"
            T = None
            L = None
        elif m < 25:
            phase = "Neutron star"
            T = None
            L = None
        else:
            phase = "Black hole"
            T = None
            L = None

    return {
        "mass": m,
        "age": age,
        "phase": phase,
        "temp_K": T,
        "lum": L,
    }


star = star_now(mass, Z, age)

st.write(
    f"Metallicity Z = {Z:.5f} | "
    f"Phase: {star['phase']}"
)

# Precompute the mass-age phase plane for the selected metallicity
masses = np.geomspace(0.1, 300, 180)
phase_rows = []

for m in masses:
    t_pre, t_ms, t_giant = stellar_times(m, zr)

    if m < 0.25:
        remnant = "White dwarf"
    elif Z < 0.001 and 140 <= m <= 260:
        remnant = "No remnant"
    elif m < 8:
        remnant = "White dwarf"
    elif m < 25:
        remnant = "Neutron star"
    else:
        remnant = "Black hole"

    phase_rows.extend([
        {"mass": m, "start": 1e-4, "end": max(t_pre, 1e-4),
         "phase": "Protostar"},
        {"mass": m, "start": max(t_pre, 1e-4),
         "end": max(t_ms, t_pre * 1.01), "phase": "Main sequence"},
        {"mass": m, "start": max(t_ms, 1e-4),
         "end": max(t_giant, t_ms * 1.01), "phase": "Giant"},
        {"mass": m, "start": max(t_giant, 1e-4),
         "end": 1000.0, "phase": remnant},
    ])

phase_df = pd.DataFrame(phase_rows)
phase_df = phase_df[
    (phase_df["end"] > phase_df["start"])
    & (phase_df["start"] <= 1000)
]

phase_colors = alt.Scale(
    domain=[
        "Protostar", "Main sequence", "Giant",
        "White dwarf", "Neutron star", "Black hole",
        "No remnant"
    ],
    range=[
        "#4a3118", "#6b8799", "#c73b25",
        "#b7aec4", "#7f7590", "#4a4256", "#141414"
    ]
)

phase_chart = alt.Chart(phase_df).mark_area(
    opacity=0.9
).encode(
    x=alt.X(
        "mass:Q",
        title="Mass (solar masses)",
        scale=alt.Scale(type="log", domain=[0.1, 300])
    ),
    y=alt.Y(
        "start:Q",
        title="Age (billion years)",
        scale=alt.Scale(type="log", domain=[1e-4, 1000])
    ),
    y2="end:Q",
    color=alt.Color("phase:N", scale=phase_colors, title="Phase"),
    detail="mass:Q"
)

selected_star = pd.DataFrame([{
    "mass": mass,
    "age": max(age, 1e-4),
    "phase": star["phase"]
}])

selected_point = alt.Chart(selected_star).mark_point(
    size=150, filled=True, color="#ffff00",
    stroke="white", strokeWidth=1.5
).encode(
    x="mass:Q",
    y="age:Q",
    tooltip=["mass:Q", "age:Q", "phase:N"]
)

phase_chart = (phase_chart + selected_point).properties(
    title="Stellar mass-age phase plane",
    height=450
)

# HR diagram: main-sequence band
ms_masses = np.geomspace(0.1, 100, 400)

ms_df = pd.DataFrame({
    "temp_K": SUN_T * ms_masses ** 0.475 * zr ** -0.025,
    "lum": ms_masses ** 3.5 * zr ** -0.1,
})

hr_line = alt.Chart(ms_df).mark_line(
    color="#718b9b", strokeWidth=4
).encode(
    x=alt.X(
        "temp_K:Q",
        title="Surface temperature (K)",
        scale=alt.Scale(
            type="log", domain=[40000, 1500], reverse=True
        ),
        axis=alt.Axis(values=[2000, 3000, 5000, 10000, 20000, 40000])
    ),
    y=alt.Y(
        "lum:Q",
        title="Luminosity (solar luminosities)",
        scale=alt.Scale(type="log", domain=[1e-4, 1e6])
    )
)

# Current star: phase-adjusted temperature and luminosity
if star["temp_K"] is not None and star["lum"] is not None:
    if star["temp_K"] > 0 and star["lum"] > 0:
        star_df = pd.DataFrame([star])

        hr_point = alt.Chart(star_df).mark_point(
            size=180,
            filled=True,
            color="#ff4b4b",
            stroke="white",
            strokeWidth=1.5
        ).encode(
            x=alt.X(
                "temp_K:Q",
                title="Surface temperature (K)",
                scale=alt.Scale(
                    type="log", domain=[40000, 1500], reverse=True
                ),
                axis=alt.Axis(
                    values=[2000, 3000, 5000, 10000, 20000, 40000]
                )
            ),
            y=alt.Y(
                "lum:Q",
                title="Luminosity (solar luminosities)",
                scale=alt.Scale(type="log", domain=[1e-4, 1e6])
            ),
            tooltip=["mass:Q", "age:Q", "phase:N", "temp_K:Q", "lum:Q"]
        )

        hr_chart = (hr_line + hr_point).properties(
            title="Hertzsprung–Russell (HR) Diagram",
            height=450
        )
    else:
        hr_chart = hr_line.properties(
            title="Hertzsprung–Russell (HR) Diagram",
            height=450
        )
else:
    hr_chart = hr_line.properties(
        title="Hertzsprung–Russell (HR) Diagram",
        height=450
    )

# Display both panels
left, right = st.columns(2)

with left:
    st.altair_chart(phase_chart, use_container_width=True)

with right:
    st.altair_chart(hr_chart, use_container_width=True)

st.subheader("Selected star")
st.write(f"**Evolutionary phase:** {star['phase']}")
st.write(f"**Mass:** {mass:.2f} solar masses")
st.write(f"**Age:** {age:.2f} billion years")

if star["temp_K"] is not None:
    st.write(f"**Surface temperature:** {star['temp_K']:,.0f} K")
else:
    st.write("**Surface temperature:** Not plotted for this remnant/event")

if star["lum"] is not None:
    st.write(f"**Luminosity:** {star['lum']:.4g} solar luminosities")
else:
    st.write("**Luminosity:** Not plotted")
