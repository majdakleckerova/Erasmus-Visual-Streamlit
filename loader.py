import polars as pl
import easygui
import logging as log
from geopy.geocoders import Nominatim
from typing import Dict, List

# Nastavení logování NOTE: Log se ukládá do loader_log.txt
log.basicConfig(
    filename="loader_log.txt",
    encoding="utf-8",
    filemode="w",
    format="{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M",
    level=log.INFO
)

# Funkce vracící slovník ve formátu {jméno v načítané tabulce:jméno v ukládané tabulce} 
def getColumnTrans() -> Dict[str, str]:
    return {
        "ciziSkolaNazev":"Univerzita",
        "ciziSkolaZkratka":"ERASMUS CODE",
        "ciziSkolaMesto":"Město",
        "ciziSkolaStatNazev":"Stát",
        "kodyIscedUvedeneUDomacichPodmSml":"Obor"
    }

# Funkce sjednoducíjící jména načítané a ukláadané tabulky
def unite_cols(new_schools:pl.DataFrame) -> pl.DataFrame:
    column_translator:Dict[str, str] = getColumnTrans()
    shady_stuff:List[str] = list(column_translator.values())
    return new_schools.rename(column_translator).select(shady_stuff)

# Funkce která předělává čísla oborů na jména
def rename_subs(new_schools:pl.DataFrame) -> pl.DataFrame:
    code_trans = pl.read_excel("cz_isced_f_systematicka_cast.xlsx") # Tabulka se jmény oborů

    # Rozepiš obory
    new_schools = new_schools.with_columns(pl.col("Obor").str.split(", ").alias("Obor2")).drop("Obor").rename({"Obor2":"Obor"})
    new_schools_temp = new_schools.explode("Obor").join(code_trans, "Obor", how="left")

    # Přejmenuj obory, slož je zpět podle škol
    obor_rename = new_schools_temp.lazy().group_by("Univerzita").agg(pl.col("Název")).collect().with_columns(pl.col("Název").list.join(", ").alias("Obory")).drop("Název")

    # Vrať zpět pracovní tabulku s názvy oborů
    return new_schools.join(obor_rename, "Univerzita", "left").drop("Obor") #Sloupec obor je zbytečný, jsou to jenom ty čísla

# Funkce která přidává url
def get_url(new_schools:pl.DataFrame, url_source:pl.DataFrame) -> pl.DataFrame:
    return new_schools.join(url_source, "ERASMUS CODE", "left").rename({"Website Url":"URL"})

# Funkce která přidává geografické koordinace (aka zdroj všeho zla)
def get_coords(new_schools:pl.DataFrame, address_source:pl.DataFrame) -> pl.DataFrame:
    # Mějme jen kódy škol a adresy
    address_source = address_source.join(new_schools.select("ERASMUS CODE"), "ERASMUS CODE", "inner")
    address_source.write_excel("addresses.xlsx")

    # Vytvoření clienta geolokátoru
    geolocator = Nominatim(user_agent="matej@sloupovi.info") # I hate everything

    # Získání koordinací
    locations = address_source.to_series(address_source.get_column_index("Address")).to_list()
    unis = address_source.to_series(address_source.get_column_index("ERASMUS CODE")).to_list()
    loc_dicts = {unis[index]:{"street":loc[0], "city":loc[1], "country":loc[2]} for index, loc in enumerate(locations)}
    relocations = [geolocator.geocode(loc_dicts[uni]) for uni in unis]
    #relocations = [loc_dicts[uni] for uni in unis if geolocator.geocode(loc_dicts[uni]) == None]

    # Přidání do tabulky
    lat = pl.Series("Latitude", [str(loc.latitude) if loc != None else None for loc in relocations], dtype=pl.String)
    long = pl.Series("Longtitude", [str(loc.longitude) if loc != None else None for loc in relocations], dtype=pl.String)
    log.info(relocations)
    #log.info(relocations.count(None))
    return new_schools.with_columns(lat, long)
   

def main() -> None:
    # Načítání
    current_schools = pl.read_excel("schools.xlsx")
    new_schools = pl.read_excel(easygui.fileopenbox("Vyberte soubor s novými školami: ", "Hi", filetypes="*.xlsx"))
    addresses = pl.read_excel("url_gen.xlsx").rename({"Erasms Code":"ERASMUS CODE"}).with_columns(pl.concat_list(pl.col("Street"), pl.col("City"), pl.col("Country Cd")).alias("Address")).select("ERASMUS CODE", "Website Url", "Address")
    log.info("Tables read successfully.")

    # Sjednocení existujících sloupců
    new_schools = unite_cols(new_schools)
    log.info("Columns united.")

    # Přejmenování oborů
    new_schools = rename_subs(new_schools)
    log.info("Renamed cols.")
    log.info(new_schools.head())

    # Získání url
    new_schools = get_url(new_schools, addresses.select("ERASMUS CODE", "Website Url"))
    log.info("Fetched url.")
    log.info(new_schools.head()) 

    # Získání geokoordinací
    new_schools = get_coords(new_schools, addresses.select("ERASMUS CODE", "Address"))
    log.info("Fetched geocoords.")
    log.info(new_schools.head())

    # Mergování a zápis
    new_schools = new_schools.select(current_schools.columns)
    current_schools.join(new_schools, "ERASMUS CODE", "anti").vstack(new_schools, in_place=True).write_excel("schools.xlsx")
    log.info("Done!")

    

if __name__ == "__main__":
    main()