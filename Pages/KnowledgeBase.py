#Referenced knowledge base for all the datasets, presets, and other relevant information.
import streamlit as st
#Used SI for proper language and proper scientific representation of the data, also used for proper formatting of the data.

def render():
    st.markdown("### Metric Guide & Evaluation Index")
    st.write(
        "Orb.Ignite computes physical combustion metrics based on documented NASA flight test "
        "and ground experiments (FLEX, Saffire, SoFIE, ACME, BASS, SAME, SOFBALL, FLARE, DAFT, and PSI-62). "
        "Below is how to interpret each parameter and output:"
    )

    st.markdown("#### Primary Environment Inputs")
    st.markdown(
        r"- **Gravity Level ($g$):** Ambient acceleration relative to standard Earth gravity ($1.0g$). Microgravity ($0.0g$) removes buoyancy, creating spherical flames. Lunar ($0.16g$) and Martian ($0.38g$) introduce partial natural convection where limiting oxygen concentrations are lowest." "\n"
        r"- **Oxygen Concentration ($\%\ \text{O}_2$):** Normal ambient is $21\%$. Spacecraft exploration habitats (e.g., Artemis Gateway) test elevated oxygen ($26\%\text{--}34\%\ \text{O}_2$), which accelerates flame spread and ignition." "\n"
        r"- **Cabin Airflow / Ventilation ($u_\infty$, cm/s):** Forced air velocity from ECLSS fans. Critical for microgravity flames; without airflow, combustion products ($\text{CO}_2, \text{H}_2\text{O}$) accumulate and induce radiative quenching ($<5\text{ cm/s}$)." "\n"
        r"- **Cabin Pressure ($P$, atm):** Ambient atmospheric pressure. Reduced pressures ($0.56\text{--}0.70\text{ atm}$) alter chemical time scales and flammability envelopes."
    )

    st.markdown("#### Core Governing Physics & Metrics")
    st.markdown(
        r"- **Category Surety ($\%$):** Confidence percentage indicating how closely the chosen fuel and environmental state align with validated NASA experimental envelopes." "\n"
        r"- **Spalding Transfer Number ($B_T$):** Thermodynamic driving force for droplet gasification and mass transfer in liquid fuel combustion (FLEX)." "\n"
        r"- **Burning Rate Constant ($K$, $\text{mm}^2/\text{s}$):** Regression slope of the classical $d^2$ law: $d(t)^2 = d_0^2 - K t$." "\n"
        r"- **Damköhler Number ($Da$):** Ratio of convective residence time to chemical kinetic reaction time ($\tau_{\text{flow}} / \tau_{\text{chem}}$). Values below $1.0$ indicate high blow-off risk." "\n"
        r"- **Ignition Delay ($t_{\text{ig}}$, s):** Time required for solid polymers to ignite under surface radiative heat flux, inversely proportional to the material's thermal inertia ($k_s \rho_s c_s$)." "\n"
        r"- **Surface Conduction ($q_{\text{cond}}''$) & Radiative Loss ($q_{\text{rad}}''$):** Heat transferred through the solid matrix versus Stefan-Boltzmann radiation emitted from the hot surface ($\sigma (T_s^4 - T_\infty^4)$)." "\n"
        r"- **Flame Spread Velocity ($V_f$, mm/s):** Rate at which the flame front propagates over thin or thick solids (de Ris formulation)." "\n"
        r"- **Grashof ($Gr$) & Rayleigh ($Ra$) Numbers:** Dimensionless ratios characterizing the strength of buoyant natural convection relative to viscous and thermal diffusion in partial gravity." "\n"
        r"- **Lewis ($Le$) & Peclet ($Pe$) Numbers:** Evaluates preferential mass diffusion of light fuels (e.g., $\text{H}_2$) forming stationary spherical flame balls without convective motion (SOFBALL)." "\n"
        r"- **Agglomerated Smoke Diameter ($d_p$, $\mu\text{m}$):** Particulate growth via Brownian coagulation under non-convective smouldering (SAME). In microgravity, soot chains grow larger ($>1.0\text{--}2.0\ \mu\text{m}$), cutting traditional ionization sensor sensitivity." "\n"
        r"- **Threat Score ($0\text{--}100$) & Probabilistic Hazard Rate ($h(t)$):** Composite fire hazard score integrating combustion rates, oxygen enrichment, cool-flame persistence, and spatial scaling alongside instantaneous failure rate $h(t) = f(t) / (1 - F(t))$." "\n"
        r"- **Exposure Factor ($EF$) & Loss Expectancy ($ALE$):** Fraction of enclosed assets exposed ($EF \in [0, 1]$) and scaled risk expectancy index via $SLE = AV \times EF$ and $ALE = SLE \times ARO$." "\n"
        r"- **Spatial Area Scaling ($A$, $\text{m}^2$):** Decreasing area ($A < 0.6\ \text{m}^2$) confines thermal energy, elevates radiative wall feedback and $\text{HCl}/\text{HF}$ sensor adsorption lag, and promotes cool-flame regime shifts; increasing area ($A > 1.8\ \text{m}^2$) accelerates exposed surface pyrolysis and causes non-buoyant $0g$ smoke dispersion across large cabin volumes."
    )
