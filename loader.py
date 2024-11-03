import polars as pl
import easygui
import logging as log
from geopy.geocoders import Nominatim
from typing import Dict, List

log.basicConfig(
    filename="loader_log.txt",
    encoding="utf-8",
    filemode="w",
    format="{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M",
    level=log.INFO
)

def getColumnTrans() -> Dict[str, str]:
    return {
        "Univerzita":"ciziSkolaNazev",
        "ERASMUS CODE":"ciziSkolaZkratka",
        "Město":"ciziSkolaMesto",
        "Stát":"ciziSkolaStatNazev",
        "Obor":"kodyIscedUvedeneUDomacichPodmSml"
    }

def unite_cols(new_schools:pl.DataFrame) -> pl.DataFrame:
    column_translator:Dict[str, str] = getColumnTrans()
    shady_stuff:List[str] = list(column_translator.keys())
    return new_schools.rename({column_translator[cur_col]:cur_col for cur_col in shady_stuff}).select(shady_stuff)

def rename_subs(new_schools:pl.DataFrame) -> pl.DataFrame:
    code_trans = pl.read_excel("cz_isced_f_systematicka_cast.xlsx")
    new_schools = new_schools.with_columns(pl.col("Obor").str.split(", ").alias("Obor2")).drop("Obor").rename({"Obor2":"Obor"})
    new_schools_temp = new_schools.explode("Obor").join(code_trans, "Obor", how="left")

    obor_rename = new_schools_temp.lazy().group_by("Univerzita").agg(pl.col("Název")).collect().with_columns(pl.col("Název").list.join(", ").alias("Obory")).drop("Název")
    return new_schools.join(obor_rename, "Univerzita", "left").drop("Obor")

def get_url(new_schools:pl.DataFrame, url_source:pl.DataFrame) -> pl.DataFrame:
    return new_schools.join(url_source, "ERASMUS CODE", "left")

def get_coords(new_schools:pl.DataFrame, address_source:pl.DataFrame) -> pl.DataFrame:
    new_schools = new_schools.join(address_source, "ERASMUS CODE", "left")

    geolocator = Nominatim(user_agent="matej@sloupovi.info") # I hate everything

    log.info(new_schools.head())

    addressor = new_schools.to_series(new_schools.get_column_index("Address")).to_list()
    locations = [geolocator.geocode(address) for address in addressor]
    log.info(locations)
    new_schools = new_schools.with_columns(
        Latitude=pl.Series([loc.latitude for loc in locations]),
        Longtitude=pl.Series([loc.longtitude for loc in locations])
    )
    return new_schools
   

def main() -> None:
    # Načítání
    current_schools = pl.read_excel("schools.xlsx")
    new_schools = pl.read_excel(easygui.fileopenbox("Vyberte soubor s novými školami: ", "Hi", filetypes="*.xlsx"))
    addresses = pl.read_excel("url_gen.xlsx").rename({"Erasms Code":"ERASMUS CODE"}).with_columns(pl.concat_str(pl.col("Street"), pl.col("City"), pl.col("Country Cd"), separator=", ").alias("Address")).select("ERASMUS CODE", "Website Url", "Address")
    log.info("Tables read successfully.")

    # Sjednocení existujících sloupců
    new_schools = unite_cols(new_schools)
    log.info("Columns united.")

    # # Přejmenování oborů
    # new_schools = rename_subs(new_schools)
    # log.info("Renamed cols.")
    # log.info(new_schools.head())

    # # Získání url
    # new_schools = get_url(new_schools, addresses.select("ERASMUS CODE", "Website Url"))
    # log.info("Fetched url.")
    # log.info(new_schools.head()) 

    # Získání geokoordinací
    new_schools = get_coords(new_schools, addresses.select("ERASMUS CODE", "Address"))
    log.info("Fetched geocoords.")
    log.info(new_schools.head())

if __name__ == "__main__":
    main()