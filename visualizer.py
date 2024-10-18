import streamlit as st
import polars as pl
import folium as fo
from streamlit_folium import st_folium
from typing import Dict, List

# Debug data
try:
    schools_source = pl.read_excel("schools.xlsx")
except:
    schools_source = pl.DataFrame({
        "name":["School 1", "School 2", "School 3", "School 4"],
        "country":["Spain", "Spain", "Czechia", "Mars"],
        "study":["Maths", "Chemistry", "Maths", "Biology"],
        "latitude":[50.5, 47.8, 67.1, 55.555],
        "longtitude":[14.25, 22.74, 37.8, 44.444]
        })

schools:pl.DataFrame = schools_source.select("name", "country", "study")
picks = schools.to_dict()
for column in picks.keys():
    picks[column] = ["---"]  + picks[column].unique(maintain_order=True).to_list()

def filter_schools(school_df:pl.DataFrame) -> pl.DataFrame:
    filtered = school_df
    filter_choice = []

    for column in filtered.columns:
        if column not in st.session_state:
            continue

        if len(st.session_state[column]) > 0:
            filter_choice.append(pl.col(column).is_in(st.session_state[column])) 
        
    if len(filter_choice) < 1:
        filter_choice = [True]
    print(filter_choice)

    return filtered.filter(filter_choice)

st.header("UJEP PRF Erasmus")
st.divider()

# --- TABULKA ---

filters = st.columns(len(schools.columns))
for index, column in enumerate(schools.columns):
    with filters[index]:
        #picks = schools_source.to_series(schools.get_column_index(column)).to_list()
        st.session_state[column] = st.multiselect(label=column, options=picks[column])

schools = filter_schools(schools_source)
schools_sub = schools.select("name", "country", "study")

st.table(schools_sub)

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

coords = zip(schools.to_series(schools.get_column_index("name")).to_list(),schools.to_series(schools.get_column_index("latitude")).to_list(),schools.to_series(schools.get_column_index("longtitude")).to_list())
for coord in coords:
    fo.Marker(
        location=[coord[1], coord[2]],
        popup=fo.Popup(coord[0])
    ).add_to(europe)

# Body ilustrující kam až lze tahat "kameru" (debug only)
fo.CircleMarker([max_lat, max_long]).add_to(europe)
fo.CircleMarker([max_lat, min_long]).add_to(europe)
fo.CircleMarker([min_lat, max_long]).add_to(europe)
fo.CircleMarker([min_lat, min_long]).add_to(europe)

# Spuštění (thank you based open-source contributors)
st_folium(europe, use_container_width=True)

st.session_state