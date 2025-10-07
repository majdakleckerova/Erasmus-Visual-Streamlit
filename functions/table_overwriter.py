import polars as pl
import easygui
import logging as log
from geopy.geocoders import Nominatim
import os.path
from typing import Dict, List
from loader import unite_cols, rename_subs, get_url, get_coords

def table_overwriter(excel_file) -> int: # Funkce zapíše všechno do souboru a následně vrátí počet řádků s nevalidními koordinacemi
    # Načítání
    current_schools = pl.DataFrame()
    if not os.path.exists("schools.xlsx"):
        current_schools = pl.from_dict({"ERASMUS CODE":[], "Univerzita":[], "Město":[], "Stát":[], "Longtitude":[], "Latitude":[], "URL":[], "Obory":[]})
    else:
        current_schools = pl.read_excel("schools.xlsx")
    new_schools = pl.read_excel(excel_file)
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
    #current_schools = current_schools.drop("Longtitude", "Latitude")
    new_schools = new_schools.select(current_schools.columns)
    current_schools.join(new_schools, "ERASMUS CODE", "anti").vstack(new_schools, in_place=True).write_excel("schools.xlsx")
    log.info("Done!")

    return len(new_schools.filter(pl.col("Longtitude").is_null() | pl.col("Latitude").is_null()))