from typing import Dict, List
import polars as pl
import easygui
import logging as log
from geopy.geocoders import Nominatim
import os.path

log.basicConfig(
    filename="loader_log.txt",
    encoding="utf-8",
    filemode="w",
    format="{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M",
    level=log.INFO
)

### getColumnTrans() 
# Funkce vracící slovník ve formátu {jméno v načítané tabulce:jméno v ukládané tabulce} 
def getColumnTrans() -> Dict[str, str]:
    return {
        "ciziSkolaNazev":"Název zahraniční školy",
        "ciziSkolaZkratka":"ERASMUS kód zahraniční školy",
        "ciziSkolaMesto":"Město zahraniční školy",
        "ciziSkolaStatNazev":"Stát zahraniční školy",
        "ciziUrl":"Webová adresa zahraniční školy",
        "domaciPracoviste":"Domácí pracoviště (fakulta, katedra)",
        "KodyISCEDVEWPSpecifSmlouvy":"Obor",
    }




### unite_cols()
# Funkce sjednoducíjící jména načítané a ukláadané tabulky pomocí getColumnTrans(), vybere jen potřebné sloupce
def unite_cols(new_schools:pl.DataFrame) -> pl.DataFrame:
    column_translator:Dict[str, str] = getColumnTrans()
    shady_stuff:List[str] = list(column_translator.values())
    return new_schools.rename(column_translator).select(shady_stuff)



### rename_subs() 
# Funkce která předělává čísla oborů na jména
# načte tabulku s překladem, rozepíše obory podle čárek, přejmenuje je a složí zpět
def rename_subs(new_schools:pl.DataFrame) -> pl.DataFrame:
    code_trans = pl.read_excel("cz_isced_f_systematicka_cast.xlsx") # Tabulka se jmény oborů
    # Rozepiš obory
    new_schools = new_schools.with_columns(pl.col("Obor").str.split(", ").alias("Obor2")).drop("Obor").rename({"Obor2":"Obor"})
    new_schools_temp = new_schools.explode("Obor").join(code_trans, "Obor", how="left")
    # Přejmenuj obory, slož je zpět podle škol
    #obor_rename = new_schools_temp.lazy().group_by("Univerzita").agg(pl.col("Název")).collect().with_columns(pl.col("Název").list.join(", ").alias("Obory")).drop("Název")
    # Vrať zpět pracovní tabulku s názvy oborů
    log.info(new_schools_temp.columns)
    return new_schools_temp.drop("Obor").rename({"Název":"Obory"})#join(obor_rename, "Univerzita", "left").drop("Obor") #Sloupec obor je zbytečný, jsou to jenom ty čísla



### get_url()
# Funkce která přidává url
def get_url(new_schools: pl.DataFrame, url_source: pl.DataFrame) -> pl.DataFrame:
    # Spojení tabulek 
    merged = (
        new_schools.join(
            url_source.rename({"ERASMUS CODE": "ERASMUS kód zahraniční školy"}),
            on="ERASMUS kód zahraniční školy",
            how="left"
        )
        .rename({"Website Url": "URL_doplnena"})
    )
    # Doplnění chybějících URL
    if "Webová adresa zahraniční školy" in merged.columns:
        merged = merged.with_columns(
            pl.when(pl.col("Webová adresa zahraniční školy").is_null())
            .then(pl.col("URL_doplnena"))
            .otherwise(pl.col("Webová adresa zahraniční školy"))
            .alias("Webová adresa zahraniční školy")
        )
    else:
        merged = merged.rename({"URL_doplnena": "Webová adresa zahraniční školy"})
    # Přidání https:// pokud chybí
    merged = merged.with_columns(
        pl.when(
            (pl.col("Webová adresa zahraniční školy").is_not_null())
            & (~pl.col("Webová adresa zahraniční školy").str.starts_with("http"))
        )
        .then(pl.lit("https://") + pl.col("Webová adresa zahraniční školy"))
        .otherwise(pl.col("Webová adresa zahraniční školy"))
        .alias("Webová adresa zahraniční školy")
    )
    # Odstranění pomocného sloupce
    if "URL_doplnena" in merged.columns:
        merged = merged.drop("URL_doplnena")
    return merged

   

### get_coords()
# volá online API Nominatim (OpenStreetMap) a získává GPS souřadnice
# Funkce která přidává geografické koordinace (aka zdroj všeho zla)
def get_coords(new_schools:pl.DataFrame, address_source:pl.DataFrame) -> pl.DataFrame:
    print("Získávám geokoordinace. Prosím, počkejte chvíli, tohle bude trvat.")
    # Mějme jen kódy škol a adresy
    address_source = address_source.join(new_schools.select("ERASMUS CODE", "Univerzita"), "ERASMUS CODE", "inner").unique("ERASMUS CODE")
    #address_source.write_excel("addresses.xlsx")
    # Vytvoření clienta geolokátoru
    geolocator = Nominatim(user_agent="matej@sloupovi.info") # NOTE: Tohle používá můj osobní účet. To není uplně ideální (jinak řečeno, this fuckin sucks).
    # Získání koordinací
    # Kolo 1
    names = address_source.to_series(address_source.get_column_index("Univerzita")).to_list()
    unis = address_source.to_series(address_source.get_column_index("ERASMUS CODE")).to_list()
    loc_dicts = {uni:name for uni,name in zip(unis, names)}
    relocations = {uni:geolocator.geocode(loc_dicts[uni], timeout=10) for uni in unis}
    # Kolo 2: Spravení (některých) None hodnot
    fixes = [uni for uni in unis if relocations[uni] == None]
    locations = {uni:loc for uni,loc in zip(unis, address_source.to_series(address_source.get_column_index("Address")).to_list())} #NOTE: This makes me cry
    loc_dicts = {uni:{"street":locations[uni][0], "city":locations[uni][1], "country":locations[uni][2]} for uni in fixes}
    for uni in fixes:
        relocations[uni] = geolocator.geocode(loc_dicts[uni], timeout=10)
    # Přidání koordinací do df
    df_maker = {"ERASMUS CODE":[], "Longtitude":[],"Latitude":[]}
    for loc in relocations.keys():
        df_maker["ERASMUS CODE"].append(loc)
        df_maker["Longtitude"].append(str(relocations[loc].longitude) if relocations[loc] != None else None)
        df_maker["Latitude"].append(str(relocations[loc].latitude) if relocations[loc] != None else None)
        reloc_info = f"{relocations[loc]} ({relocations[loc].latitude}, {relocations[loc].longitude})" if relocations[loc] != None else None
        log.info(f"{loc} - {reloc_info}")
    return new_schools.join(pl.from_dict(df_maker), "ERASMUS CODE", "left")

### merge_universities()
# Funkce která sloučí duplicitní univerzity do jednoho řádku
# Spojí hodnoty ve sloupcích 'Domácí pracoviště (fakulta, katedra)' a 'Obory' do jednoho řádku
import re
def merge_universities(df: pl.DataFrame) -> pl.DataFrame:
    """
    Sloučí duplicity univerzit podle identifikátorů a spojí hodnoty ze sloupců
    'Domácí pracoviště (fakulta, katedra)' a 'Obory' do jednoho řádku.
    Fakulty se spojují čárkami, obory středníky.
    """
    # Bezpečné rozdělení řetězce na seznam
    def safe_split(s: str, delimiter_pattern: str):
        if s is None:
            return []
        s = str(s).strip()
        if not s:
            return []
        return [x.strip() for x in re.split(delimiter_pattern, s) if x.strip()]
    # Definice klíčových sloupců a sloupců k merge
    merge_cols = ["Domácí pracoviště (fakulta, katedra)", "Obory"]
    key_cols = [
        "Název zahraniční školy",
        "ERASMUS kód zahraniční školy",
        "Město zahraniční školy",
        "Stát zahraniční školy",
        "Webová adresa zahraniční školy",
    ]
    # Příprava dat: rozdělení hodnot ve sloupcích na seznamy
    df = df.with_columns([
        pl.col("Domácí pracoviště (fakulta, katedra)")
        .map_elements(lambda x: safe_split(x, r"\s*,\s*"), return_dtype=pl.List(pl.Utf8))
        .alias("Domácí pracoviště (fakulta, katedra)"),
        pl.col("Obory")
        .map_elements(lambda x: safe_split(x, r"\s*;\s*"), return_dtype=pl.List(pl.Utf8))
        .alias("Obory"),
    ])
    # Sjednocení duplicitních univerzit
    df_merged = (
        df.group_by(key_cols)
        .agg([
            pl.col("Domácí pracoviště (fakulta, katedra)")
            .explode()
            .drop_nulls()
            .unique()
            .sort()
            .alias("Domácí pracoviště (fakulta, katedra)"),
            pl.col("Obory")
            .explode()
            .drop_nulls()
            .unique()
            .sort()
            .alias("Obory"),
        ])
        .with_columns([
            pl.col("Domácí pracoviště (fakulta, katedra)")
            .list.join(", ")
            .alias("Domácí pracoviště (fakulta, katedra)"),
            pl.col("Obory")
            .list.join("; ")
            .alias("Obory"),
        ])
    )
    return df_merged

