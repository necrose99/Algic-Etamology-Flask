# helpers/visualization.py
import os
import io
import sqlite3
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import matplotlib
matplotlib.use('Agg')  # Headless server-safe rendering pipeline
import matplotlib.pyplot as plt

DB_FILE = "myaamia-corpus.db"
CACHE_IMAGE_PATH = "static/cache_dashboard.png"

# WALS-aligned structural group mapping
GROUP_COLORS = {
    "Central": "#1abc9c",    # Teal (mia, kic, pot, sac, oji, cre)
    "Eastern": "#2980b9",    # Blue (mic, abe)
    "Plains":  "#e67e22",    # Orange (bft, arp, chy)
    "Western": "#e74c3c",    # Red (yur, wiy - CA outliers)
    "Remnant": "#7f8c8d",    # Gray (bue, pim, qyp)
    "Proto":   "#9b59b6"     # Purple (Ancestral root base)
}

# Baseline geographical centers for pre-contact coordinates
BASELINE_COORDS = {
    "mia": {"lon": -90.00, "lat": 40.00, "group": "Central"}, # Illinois / WALS ill
    "kic": {"lon": -88.50, "lat": 39.50, "group": "Central"}, 
    "cre": {"lon": -105.0, "lat": 55.00, "group": "Central"},
    "yur": {"lon": -124.0, "lat": 41.20, "group": "Western"}, # California Outlier
    "wiy": {"lon": -124.2, "lat": 40.60, "group": "Western"}  # California Outlier
}

def calculate_levenshtein_drift(word, root):
    """Normalized phonetic edit distance: 0.0 (identical) to 1.0 (max mutation)"""
    if not word or not root: return 1.0
    w1, w2 = word.lower().strip("*"), root.lower().strip("*")
    size_x, size_y = len(w1) + 1, len(w2) + 1
    matrix = np.zeros((size_x, size_y))
    for x in range(size_x): matrix[x, 0] = x
    for y in range(size_y): matrix[0, y] = y
    
    for x in range(1, size_x):
        for y in range(1, size_y):
            if w1[x-1] == w2[y-1]:
                matrix[x, y] = matrix[x-1, y-1]
            else:
                matrix[x, y] = min(matrix[x-1, y]+1, matrix[x, y-1]+1, matrix[x-1, y-1]+1)
    
    return round(matrix[size_x-1, size_y-1] / max(len(w1), len(w2)), 3)

def calculate_geo_drift_km(lon, lat, homeland_lon=-120.0, homeland_lat=46.0):
    """Approximates displacement from Proto-Algic Urheimat (Columbia Plateau)"""
    dx = (lon - homeland_lon) * 82.0 
    dy = (lat - homeland_lat) * 111.0
    return round(np.sqrt(dx**2 + dy**2), 1)

def update_and_render_cache():
    """Extracts SQLite logs, overlays GeoPandas surfaces, and writes PNG cache."""
    if not os.path.exists(DB_FILE):
        return
        
    with sqlite3.connect(DB_FILE) as conn:
        df = pd.read_sql_query("SELECT lang, form, proto_form, source_type FROM entries", conn)
        
    if df.empty:
        return

    # Map database languages to spatial baseline profiles
    processed = []
    for _, row in df.iterrows():
        lang = row['lang']
        if lang in BASELINE_COORDS:
            coords = BASELINE_COORDS[lang]
            etym_drift = calculate_levenshtein_drift(row['form'], row['proto_form'])
            geo_drift = calculate_geo_drift_km(coords['lon'], coords['lat'])
            processed.append({
                "lang": lang,
                "form": row['form'],
                "lon": coords['lon'],
                "lat": coords['lat'],
                "group": coords['group'],
                "etym_drift": etym_drift,
                "geo_drift_km": geo_drift
            })
            
    if not processed:
        return
        
    plot_df = pd.DataFrame(processed).drop_duplicates(subset=['lang', 'form'])
    geometry = [Point(xy) for xy in zip(plot_df['lon'], plot_df['lat'])]
    gdf = gpd.GeoDataFrame(plot_df, geometry=geometry, crs="EPSG:4326")

    # Generate side-by-side visualization maps
    fig, (ax_map, ax_drift) = plt.subplots(1, 2, figsize=(16, 7))
    
    for group_name, group_df in gdf.groupby('group'):
        color = GROUP_COLORS.get(group_name, "#333333")
        marker = 's' if group_name == 'Western' else 'o'
        
        # Panel 1: Canada / CONUS Geoplot projection
        group_df.plot(ax=ax_map, color=color, marker=marker, markersize=140, 
                      edgecolor='k', label=f"{group_name} Branch", zorder=3)
        
        # Panel 2: Etymological Change/Drift Grid
        ax_drift.scatter(group_df['etym_drift'], group_df['geo_drift_km'], 
                         color=color, marker=marker, s=140, edgecolors='k', zorder=3)

    # Label maps with codes
    for _, row in gdf.drop_duplicates(subset=['lang']).iterrows():
        ax_map.annotate(row['lang'].upper(), (row['geometry'].x, row['geometry'].y), 
                        textcoords="offset points", xytext=(0,12), ha='center', fontweight='bold', fontsize=10)
        
        ax_drift.annotate(row['lang'].upper(), (row['etym_drift'], row['geo_drift_km']), 
                          textcoords="offset points", xytext=(0,12), ha='center', fontsize=9)

    # Window frames perfectly matching Canada down to California boundaries
    ax_map.set_xlim(-130, -60)   
    ax_map.set_ylim(32, 60)      
    ax_map.set_title("Algic Geographic Coordinate Distribution", fontsize=12, fontweight='bold')
    ax_map.set_xlabel("Longitude")
    ax_map.set_ylabel("Latitude")
    ax_map.grid(True, linestyle=':', alpha=0.6)
    ax_map.legend(loc='lower left')

    ax_drift.set_title("Linguistic Evolution Map (Lexical mutation vs Distance)", fontsize=12, fontweight='bold')
    ax_drift.set_xlabel("Phonetic Drift Scale (Normalized Edit Distance)")
    ax_drift.set_ylabel("Calculated Displacement Vector from Homeland (km)")
    ax_drift.grid(True, linestyle=':', alpha=0.6)

    plt.tight_layout()
    os.makedirs(os.path.dirname(CACHE_IMAGE_PATH), exist_ok=True)
    plt.savefig(CACHE_IMAGE_PATH, format='png', dpi=140)
    plt.close(fig)
