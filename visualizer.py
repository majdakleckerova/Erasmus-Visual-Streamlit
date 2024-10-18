import streamlit as st
import polars as pl
import folium as fo
from streamlit_folium import st_folium

# Debug data
try:
    schools = pl.read_excel("schools.xlsx")
except:
    schools = pl.DataFrame({
        "name":["School 1", "School 2", "School 3", "School 4"],
        "country":["Spain", "Spain", "Czechia", "Mars"],
        "study":["Maths", "Chemistry", "Maths", "Biology"],
        "latitude":[50.5, 47.8, 67.1, 55.555],
        "longtitude":[14.25, 22.74, 37.8, 44.444]
        })

st.header("UJEP PRF Erasmus")
st.divider()

# --- MAPA ---
# Není tam možnost zobrazení informací o škole když se tam najede myší, takže jdeme dělat funky shit
#st.map(schools, latitude="latitude", longitude="longtitude")

# WE FOLIUM UP IN THIS HOE
# Hranice mapy
max_lat, min_lat = 75, 33
max_long, min_long = 65, -31

# Inicializace mapy
europe = fo.Map(
    [50.5, 14.25],
    zoom_start=4, # Počáteční krok přiblížení, čím menší tím oddálenější
    max_bounds=True, # Omezenení tahání vedle
    min_lat=min_lat,
    max_lat=max_lat,
    min_lon=min_long,
    max_lon=max_long
)

# Body ilustrující kam až lze tahat "kameru" (debug only)
fo.CircleMarker([max_lat, max_long]).add_to(europe)
fo.CircleMarker([max_lat, min_long]).add_to(europe)
fo.CircleMarker([min_lat, max_long]).add_to(europe)
fo.CircleMarker([min_lat, min_long]).add_to(europe)

# Spuštění (thank you based open-source contributors)
st_folium(europe, use_container_width=True)

# --- TABULKA ---
st.table(schools.select("name", "country", "study"))

