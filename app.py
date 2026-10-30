import sys
import gradio as gr
import matplotlib.pyplot as plt
import pandas as pd

# -------------------------------------------------------------------------
# 1. MOCK DATA REGISTRY (Simulating Glottolog Geo-Coordinate Extents)
# -------------------------------------------------------------------------
# Comprehensive spatial & chronological mapping database for Algic languages
GLOTTOLOG_GEO_DB = pd.DataFrame([
    # Proto-Algonquian Core (Estimated 1000 BC - 500 BC extents)
    {"code": "alg-pro", "name": "Proto-Algonquian (Core)", "lat": 46.0, "lon": -78.0, "time_layer": -1000, "branch": "Proto-Language"},
    
    # Plains Nodes (7000 BC to Modern Movements)
    {"code": "bla", "name": "Blackfoot (Siksika)", "lat": 51.0, "lon": -113.0, "time_layer": 1800, "branch": "Plains"},
    {"code": "chy", "name": "Cheyenne (Tsėhésenestse)", "lat": 45.5, "lon": -106.5, "time_layer": 1850, "branch": "Plains"},
    {"code": "arp", "name": "Arapaho", "lat": 40.0, "lon": -105.5, "time_layer": 1800, "branch": "Plains"},
    
    # Central Great Lakes / Great Lakes Algonquian Syllabics (GLAS) Domain
    {"code": "mia", "name": "Myaamia (Miami-Illinois)", "lat": 40.5, "lon": -86.0, "time_layer": 1650, "branch": "Central"},
    {"code": "pot", "name": "Potawatomi (Bodéwadmimwen)", "lat": 42.5, "lon": -86.5, "time_layer": 1700, "branch": "Central"},
    {"code": "sac", "name": "Meskwaki (Fox-Sac)", "lat": 42.0, "lon": -90.5, "time_layer": 1750, "branch": "Central"},
    {"code": "kic", "name": "Kickapoo", "lat": 39.5, "lon": -89.0, "time_layer": 1680, "branch": "Central"},
    {"code": "oji", "name": "Ojibwe (Anishinaabemowin)", "lat": 46.5, "lon": -89.5, "time_layer": 1800, "branch": "Central"},
    {"code": "sjw", "name": "Shawnee (Shall-Zwall)", "lat": 39.0, "lon": -83.0, "time_layer": 1750, "branch": "Central"},
    
    # Eastern Seaboard Clines
    {"code": "mic", "name": "Mi'kmaq", "lat": 46.0, "lon": -64.0, "time_layer": 1600, "branch": "Eastern"},
    {"code": "umu", "name": "Munsee Delaware", "lat": 41.0, "lon": -74.5, "time_layer": 1650, "branch": "Eastern"},
    
    # California Ritwan Isolates (Diverged deeply around 3000 BC - 5000 BC)
    {"code": "yur", "name": "Yurok", "lat": 41.2, "lon": -124.0, "time_layer": 1500, "branch": "Western (Ritwan)"},
    {"code": "wiy", "name": "Wiyot", "lat": 40.6, "lon": -124.2, "time_layer": 1500, "branch": "Western (Ritwan)"},
    
    # Remnant / Lost Macro-Groupings
    {"code": "pim", "name": "Powhatan (Virginia)", "lat": 37.5, "lon": -77.0, "time_layer": 1607, "branch": "Remnant / Uncertain"},
    {"code": "bue", "name": "Beothuk (Newfoundland)", "lat": 49.0, "lon": -56.0, "time_layer": 1500, "branch": "Remnant / Uncertain"}
])

# -------------------------------------------------------------------------
# 2. CHRONOLOGICAL SPATIAL RENDER ENGINE
# -------------------------------------------------------------------------
def render_glottolog_map(target_year: float, active_branch: str):
    """
    Filters Glottolog geo-vectors by historic epoch boundaries (-7000 to 2026) 
    and genetic branch classes to output an interactive geographic map.
    """
    # 1. Execute dynamic dataframe filtering operations
    filtered_df = GLOTTOLOG_GEO_DB[GLOTTOLOG_GEO_DB["branch"] == active_branch]
    
    # Filter points existing at or prior to selected temporal matrix horizon
    # For deep pre-contact structures, we match points active relative to chronological thresholds
    epoch_filtered = filtered_df[filtered_df["time_layer"] <= target_year]
    
    # 2. Build high-contrast geo-projection map layout
    fig, ax = plt.subplots(figsize=(9, 5), facecolor='#0f172a')
    ax.set_facecolor('#0f172a')
    
    # Rough structural baseline boundary grid for North American landmass tracking
    ax.axhline(y=40, color='#334155', linestyle=':', linewidth=0.8)
    ax.axhline(y=45, color='#334155', linestyle=':', linewidth=0.8)
    ax.axhline(y=50, color='#334155', linestyle=':', linewidth=0.8)
    ax.axvline(x=-120, color='#334155', linestyle=':', linewidth=0.8)
    ax.axvline(x=-90, color='#334155', linestyle=':', linewidth=0.8)
    ax.axvline(x=-75, color='#334155', linestyle=':', linewidth=0.8)

    # Plot historical trajectory points
    if not epoch_filtered.empty:
        # Scatter geo coordinate points
        ax.scatter(epoch_filtered["lon"], epoch_filtered["lat"], 
                   color='#14b8a6', s=120, edgecolors='#f8fafc', linewidths=1.5, zorder=3, label="Dialect Node")
        
        # Overlay textual labels for coordinate metrics
        for _, row in epoch_filtered.iterrows():
            ax.text(row["lon"] + 0.8, row["lat"] + 0.3, f"{row['name']} [{row['code'].upper()}]", 
                    color='#f1f5f9', fontsize=9, weight='semibold', zorder=4,
                    bbox=dict(boxstyle='square,pad=0.2', fc='#1e293b', ec='#475569', alpha=0.8))
    else:
        ax.text(0.5, 0.5, "No attested language groups in this specific branch\nprior to selected chronological epoch layer.", 
                color='#94a3b8', fontsize=11, ha='center', va='center', transform=ax.transAxes)

    # Label styling configurations
    title_suffix = f"{abs(int(target_year))} BC" if target_year < 0 else f"{int(target_year)} AD"
    ax.set_title(f"Algic Geo-Linguistic Range Mapping Configuration ({title_suffix})", color='#38bdf8', fontsize=12, pad=12)
    ax.set_xlabel("Longitude Extent (Glottolog Vector)", color='#64748b')
    ax.set_ylabel("Latitude Extent (Glottolog Vector)", color='#64748b')
    
    # Set explicit plot frame scale limits for continental tracking
    ax.set_xlim(-130, -50)
    ax.set_ylim(32, 58)
    
    ax.tick_params(colors='#64748b', labelsize=8)
    ax.grid(True, color='#1e293b', linestyle='-', linewidth=0.5)
    plt.tight_layout()
    
    # Format the accompanying dataset matrix for structural UI viewing
    view_table = epoch_filtered[["code", "name", "time_layer", "lat", "lon"]].copy()
    view_table.columns = ["ISO Key", "Dialect Metric", "Attested Horizon Epoch", "Latitude", "Longitude"]
    
    return fig, view_table

# -------------------------------------------------------------------------
# 3. GRADIO CONSOLE ASSEMBLY WITH GEOPANDAS HELPER SUBPAGE
# -------------------------------------------------------------------------
def build_interface():
    with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue", neutral_hue="slate")) as demo:
        gr.Markdown("# 🗺️ Algic Chrono-Spatial Workbench")
        gr.Markdown("Interactive visualization companion mapping Glottolog geo-coordinates from **7000 BC** to **Modern Times**.")
        
        with gr.Tabs():
            # Tab 1: Geographic Distribution Applet
            with gr.TabItem("Glottolog Spatial Projection Engine"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 🎛️ Spatio-Temporal Calibration")
                        
                        # Slider managing your requested -7000 BC to current year timeframe
                        timeline_slider = gr.Slider(
                            minimum=-7000, 
                            maximum=2026, 
                            value=1800, 
                            step=50, 
                            label="Target Chronological Layer Horizon (Negative = BC, Positive = AD)"
                        )
                        
                        branch_dropdown = gr.Dropdown(
                            choices=["Proto-Language", "Plains", "Central", "Eastern", "Western (Ritwan)", "Remnant / Uncertain"],
                            value="Central",
                            label="Genetic Language Family Taxonomy Filter"
                        )
                        
                        render_btn = gr.Button("Recompute Geographic Projections", variant="primary")
                        
                    with gr.Column(scale=2):
                        gr.Markdown("### 🗺️ Intercept Spatial Distribution Map Canvas")
                        geo_plot = gr.Plot(label="Algic Map Space Canvas")
                
                with gr.Row():
                    gr.Markdown("### 📊 Active Coordinate Extraction Vector Matrix")
                    extract_matrix = gr.Dataframe(
                        headers=["ISO Key", "Dialect Metric", "Attested Horizon Epoch", "Latitude", "Longitude"],
                        datatype=["str", "str", "int", "float", "float"],
                        interactive=False
                    )
                
                render_btn.click(
                    fn=render_glottolog_map,
                    inputs=[timeline_slider, branch_dropdown],
                    outputs=[geo_plot, extract_matrix]
                )
                
            # Tab 2: Contextual Ingest Documentation
            with gr.TabItem("Automated Peer Ingress Log"):
                gr.Markdown("""
                ### 📡 Automated Translation-Memory Reciprocity Engine
                When peer nodes connect to your Hugging Face space running `--mcp-only`, they exchange high-value data. 
                This map interface queries your local graph via **SPARQL** to match incoming coordinates automatically.
                
                *   **7000 BC - 3000 BC:** Deep split windows tracking ancestral Wiyot/Yurok Ritwan shifts away from Proto-Algonquian clusters.
                *   **1600 AD - 1850 AD:** Mass geographic movements, tracking migrations from Great Lakes core areas down into Oklahoma and westward across the Plains.
                """)
                
    return demo

if __name__ == "__main__":
    ui = build_interface()
    ui.launch(server_name="0.0.0.0", server_port=8181)
# Continental Boundary Boxes for mapping canvas constraints
CONUS_CA_BOUNDS = {
    "min_lon": -130.0,  # Pacific Edge (Yurok/Wiyot)
    "max_lon": -52.0,   # Atlantic Edge (Mi'kmaq/Beothuk)
    "min_lat": 32.0,    # Southern Extent (Kickapoo/Powhatan)
    "max_lat": 60.0     # Northern Boreal Extent (Cree/Atikamekw)
}

def render_conus_ca_canvas(target_year, active_branch):
    fig, ax = plt.subplots(figsize=(10, 5.5), facecolor='#0f172a')
    ax.set_facecolor('#0f172a')
    
    # 1. Overlay coarse geographic guide markers for CONUS/CA zones
    # Pacific Littoral Zone
    ax.axvspan(-125, -121, color='#1e293b', alpha=0.3, label="Pacific Coast Isolation Zone")
    # Great Lakes / Woodlands Core System
    ax.axvspan(-92, -76, color='#0f2027', alpha=0.4, label="Algonquian Woodlands Core")
    
    # 2. Filter your Glottolog dataset and scatter nodes
    # (The layout uses the CONUS_CA_BOUNDS constraints to frame the map perfectly)
    ax.set_xlim(CONUS_CA_BOUNDS["min_lon"], CONUS_CA_BOUNDS["max_lon"])
    ax.set_ylim(CONUS_CA_BOUNDS["min_lat"], CONUS_CA_BOUNDS["max_lat"])
    
    ax.set_title("CONUS / CA Macro-Family Divergence Mapping Core", color='#38bdf8')
    return fig
# Extended Continental Boundary Map Constraints including Northern Mexico
AMERICA_MACRO_BOUNDS = {
    "min_lon": -130.0,  # Pacific Rim (Yurok / Wiyot)
    "max_lon": -52.0,   # Atlantic Coast (Mi'kmaq / Beothuk)
    "min_lat": 24.0,    # Southern Shift Constraint -> Captures Coahuila, MX Kickapoo outlier
    "max_lat": 60.0     # Northern Canadian Boreal Extent (Cree variants)
}

# Update your Glottolog mock registry entry to anchor the Mexico node accurately
KICKAPOO_MEXICO_NODE = {
    "code": "kic-mx", 
    "name": "Kickapoo (El Nacimiento, MX)", 
    "lat": 26.85,       # Deep southern outlier coordinates
    "lon": -102.72, 
    "time_layer": 1852, # Mid-19th century Mexican settlement horizon
    "branch": "Central"
}
