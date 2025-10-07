import streamlit as st
import polars as pl
import folium as fo
from streamlit_folium import st_folium
import re
import pandas as pd
import base64
from st_aggrid import AgGrid, GridOptionsBuilder  

### Nastavení stránky
st.set_page_config(page_title="UJEP Erasmus+", page_icon="🌍", layout="wide")

def load_image_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

erasmus_logo = load_image_base64("erasmus_logo.png")
ujep_logo = load_image_base64("UJEP_Logo.svg.png")

### Vlastní CSS styly
st.markdown(f"""
<style>
.stApp {{
    background-color: #f8f9fb;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}}

.header-container {{
    background: linear-gradient(135deg, #d9ecff 0%, #9ec8f2 100%);
    color: #002b50;
    text-align: center;
    padding: 3rem 1rem 2.5rem 1rem;
    border-radius: 0 0 18px 18px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    margin-bottom: 1.5rem;
    position: relative;
}}

.main-title {{
    font-size: 2.8rem;
    font-weight: 700;
    color: #002b50;
    margin-bottom: 0.4rem;
}}

.subtitle {{
    font-size: 1.15rem;
    font-weight: 300;
    color: #1d4066;
    font-family: 'Inter', sans-serif;
    letter-spacing: 0.2px;
    margin-bottom: 0.8rem;
}}

.accent-line {{
    width: 80px;
    height: 3px;
    background: linear-gradient(90deg, #004a98, #00a0e3);
    border-radius: 3px;
    margin: 0 auto;
}}

.logos {{
    position: absolute;
    top: 15px;
    right: 25px;
    display: flex;
    align-items: center;
    gap: 18px;
}}
.logos img {{
    height: 48px;
    opacity: 0.95;
}}

.info-box {{
    background-color: #ffffff;
    border-left: 5px solid #0072ce;
    padding: 1.2rem 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    margin-bottom: 2rem;
}}
.info-box p {{
    margin: 0;
    font-size: 0.95rem;
    color: #333;
    line-height: 1.5;
}}
.info-box a {{
    color: #0072ce;
    text-decoration: none;
    font-weight: 500;
}}
.info-box a:hover {{
    text-decoration: underline;
}}

table.dataframe {{
    width: 100%;
    border-collapse: collapse;
    font-size: 15px;
}}
table.dataframe th, table.dataframe td {{
    border: 1px solid #ddd;
    padding: 8px;
    vertical-align: top;
    white-space: normal !important;
    word-wrap: break-word;
    max-width: 300px;
}}
table.dataframe th {{
    background-color: #efefef;
    font-weight: 600;
}}

iframe[title="st_folium"] {{
    height: 550px !important;
    margin-bottom: 0 !important;
}}
</style>
""", unsafe_allow_html=True)

### Hlavička
st.markdown(f"""
<div class="header-container">
    <div class="logos">
        <img src="data:image/png;base64,{erasmus_logo}" alt="Erasmus+">
        <img src="data:image/png;base64,{ujep_logo}" alt="UJEP">
    </div>
    <div class="main-title">UJEP Erasmus+</div>
    <div class="subtitle">Objev partnerské univerzity po celé Evropě – podle fakulty, oboru a země</div>
    <div class="accent-line"></div>
</div>
""", unsafe_allow_html=True)

### Informační box
st.markdown("""
<div class="info-box">
<p>
<b>Erasmus+</b> je vzdělávací program Evropské unie, který podporuje spolupráci a mobilitu ve všech sférách vzdělávání, 
v odborné přípravě a v oblasti sportu a mládeže. Je nástupcem Programu celoživotního učení, programu Mládež v akci a dalších. 
Program Erasmus vznikl v roce 1987, v České republice funguje od roku 1998. 
<b>Univerzita Jana Evangelisty Purkyně v Ústí nad Labem</b> je do programu zapojena od roku 1999.
</p>
<p style="margin-top:8px;">
🔗 <a href="https://www.ujep.cz/cs/zakladni-informace" target="_blank">Základní informace o programu Erasmus+ na webu UJEP</a>
</p>
</div>
""", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)


### Načtení dat
@st.cache_data
def load_data():
    df = pl.read_excel("new.xlsx")
    df = df.with_columns([
        pl.col("Latitude").cast(pl.Float64, strict=False),
        pl.col("Longtitude").cast(pl.Float64, strict=False)
    ])
    df = df.with_columns([
        pl.when((pl.col("Latitude") < 33) | (pl.col("Latitude") > 75) |
                (pl.col("Longtitude") < -31) | (pl.col("Longtitude") > 65))
          .then(None).otherwise(pl.col("Latitude")).alias("Latitude"),
        pl.when((pl.col("Latitude") < 33) | (pl.col("Latitude") > 75) |
                (pl.col("Longtitude") < -31) | (pl.col("Longtitude") > 65))
          .then(None).otherwise(pl.col("Longtitude")).alias("Longtitude")
    ])
    return df

df = load_data()

def unique_values(series: pl.Series, delimiter: str):
    vals = set()
    for cell in series.drop_nulls():
        for item in re.split(fr"\s*{re.escape(delimiter)}\s*", str(cell)):
            item = item.strip()
            if item:
                vals.add(item)
    return sorted(vals)






### Filtry
fakulty = unique_values(df["Domácí pracoviště (fakulta, katedra)"], ",")
obory = unique_values(df["Obory"], ";")
zeme = unique_values(df["Stát zahraniční školy"], ",")

st.markdown("### <span style='color:#004A98;'>Filtrování</span>", unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)
with col1:
    vybrane_fakulty = st.multiselect("Domácí pracoviště (fakulta, katedra)", fakulty)
with col2:
    vybrane_obory = st.multiselect("Obory", obory)
with col3:
    vybrane_zeme = st.multiselect("Stát zahraniční školy", zeme)

### Filtrování dat
df_filtered = df
if vybrane_fakulty:
    df_filtered = df_filtered.filter(
        pl.col("Domácí pracoviště (fakulta, katedra)").map_elements(
            lambda x: any(f.lower().strip() in [p.lower().strip() for p in re.split(r",\s*", str(x))] for f in vybrane_fakulty)
        )
    )
if vybrane_obory:
    df_filtered = df_filtered.filter(
        pl.col("Obory").map_elements(
            lambda x: any(o.lower().strip() in [p.lower().strip() for p in re.split(r";\s*", str(x))] for o in vybrane_obory)
        )
    )
if vybrane_zeme:
    df_filtered = df_filtered.filter(pl.col("Stát zahraniční školy").is_in(vybrane_zeme))

st.markdown("</div>", unsafe_allow_html=True)







### Mapa
st.markdown("### <span style='color:#004A98;'>Mapa partnerských univerzit</span>", unsafe_allow_html=True)

europe = fo.Map(location=[50.5, 14.25], zoom_start=4, max_bounds=True)

df_with_coords = df_filtered.filter(
    (pl.col("Latitude").is_not_null()) & (pl.col("Longtitude").is_not_null())
)

for row in df_with_coords.iter_rows(named=True):
    name = row["Název zahraniční školy"]
    city = row["Město zahraniční školy"]
    country = row["Stát zahraniční školy"]
    url = row.get("Webová adresa zahraniční školy", "")
    lat, lon = row["Latitude"], row["Longtitude"]

    popup_html = f"""
    <div style='font-family: Inter, sans-serif; width: 220px;'>
        <strong style='font-size:16px;'>{name}</strong><br>
        <span style='color:#666;'>{city}, {country}</span><br><br>
        <a href='{url}' target='_blank' style='color:#0072ce; text-decoration:none;'>🌐 Otevřít web</a>
    </div>
    """
    fo.Marker(
        location=[lat, lon],
        popup=fo.Popup(popup_html, max_width=250),
        icon=fo.Icon(color="cadetblue", icon="university", prefix="fa")
    ).add_to(europe)

st_folium(europe, use_container_width=True, height=550)

st.caption(

    "ℹ*Některé partnerské univerzity se nemusí zobrazit na mapě z důvodu chybějících souřadnic. "
    "V tabulce níže jsou však uvedeny všechny dostupné instituce.*"
)




### Tabulka

st.markdown("### <span style='color:#004A98;'>Seznam univerzit</span>", unsafe_allow_html=True)
cols_to_show = [c for c in df_filtered.columns if c not in ("Latitude", "Longtitude")]
st.write(f"Zobrazeno univerzit: **{len(df_filtered)}** (z {len(df)} celkem)")
df_pd = df_filtered.select(cols_to_show).to_pandas()
search_text = st.text_input("Vyhledat univerzitu nebo stát:", placeholder="Začni psát název nebo zemi...")


st.markdown("""
<style>
input[type="text"] {
    border-radius: 8px;
    border: 1px solid #cbd5e1 !important;
    padding: 8px 10px !important;
    background-color: #f8fafc !important;
    font-size: 15px !important;
}
</style>
""", unsafe_allow_html=True)


if search_text:
    df_pd = df_pd[df_pd.apply(lambda row: row.astype(str).str.lower().str.contains(search_text).any(), axis=1)]

gb = GridOptionsBuilder.from_dataframe(df_pd)
gb.configure_default_column(
    wrapText=True,
    autoHeight=True,
    resizable=True,
    sortable=True,   
    filter=False     
)
gb.configure_grid_options(domLayout='normal')
grid_options = gb.build()

AgGrid(
    df_pd,
    gridOptions=grid_options,
    theme="balham",
    height=500,
    allow_unsafe_jscode=True
)

st.markdown("""
<hr>
<p style='text-align:center; color:#888; font-size:14px;'>
© 2025 Univerzita J. E. Purkyně – Erasmus+ | Vyvinuto v rámci interního projektu Katedry informatiky UJEP
</p>
""", unsafe_allow_html=True)
