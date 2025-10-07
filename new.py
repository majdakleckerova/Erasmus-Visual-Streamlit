import polars as pl
import logging as log
import os.path
from functions import unite_cols, rename_subs, get_url, get_coords, merge_universities

log.basicConfig(
    filename="data_loader_log.txt",
    encoding="utf-8",
    filemode="w",
    format="{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M",
    level=log.INFO
)

##############
### Nová funkce data_loader()
##############

def data_loader() -> pl.DataFrame:
    """
    Hlavní funkce pro načítání dat.
    """

    ### Načtení "Aplikace_IIA_zdroj_vzor.xlsx"
    source_file = "Aplikace_IIA_zdroj_vzor.xlsx"


    # Kontrola existence souboru
    if not os.path.exists(source_file):
        log.error(f"Soubor {source_file} nebyl nalezen.")
        raise FileNotFoundError(f"Soubor {source_file} neexistuje v aktuálním adresáři.")


    # Načtení dat
    df = pl.read_excel(source_file)
    log.info(f"Soubor {source_file} načten. Počet řádků: {len(df)}")


    # Kontrola existence sloupce 'nabizetVAplikaciIIA'
    if "nabizetVAplikaciIIA" not in df.columns:
        log.error("Sloupec 'nabizetVAplikaciIIA' nebyl nalezen v tabulce.")
        raise KeyError("Chybí sloupec 'nabizetVAplikaciIIA'.")


    # Filtrování řádků, kde je 'nabizetVAplikaciIIA' rovno "ANO"
    filtered_df = df.filter(pl.col("nabizetVAplikaciIIA") == "ANO")
    log.info(f"Počet vyfiltrovaných řádků: {len(filtered_df)}")
    df = filtered_df


    # Sjednocení sloupců
    df = unite_cols(df)
    log.info(f"Sloupce sjednoceny. Výsledné sloupce: {df.columns}")


    # Přejmenování oborů
    df = rename_subs(df)
    log.info(f"Sloupce přejmenovány. Náhled dat: {df.head()}")


    # Sloučení duplicitních univerzit
    df = merge_universities(df)
    log.info(f"Univerzity sloučeny. Počet řádků po merge: {len(df)}")
    log.info(f"Náhled dat po merge: {df.head()}")


    # Přidání chybějících URL adres a jejich úprava
    addresses = pl.read_excel("url_gen.xlsx").rename({"Erasms Code":"ERASMUS CODE"})
    df = get_url(df, addresses.select("ERASMUS CODE", "Website Url"))
    log.info(f"URL přidány. Náhled dat: {df.head()}")


    # Přidání geokoordinátů
    addresses = (
        pl.read_excel("url_gen.xlsx")
        .rename({"Erasms Code": "ERASMUS CODE"})
        .with_columns(
            pl.concat_list([pl.col("Street"), pl.col("City"), pl.col("Country Cd")]).alias("Address")))
    log.info(f"Adresa pro geokoordináty načtena. Náhled dat: {addresses.head()}")
    df = df.rename({"ERASMUS kód zahraniční školy": "ERASMUS CODE","Název zahraniční školy": "Univerzita"})
    log.info("Spouštím generování geokoordinátů...")
    df = get_coords(df, addresses.select("ERASMUS CODE", "Address"))
    df = df.rename({"ERASMUS CODE": "ERASMUS kód zahraniční školy","Univerzita": "Název zahraniční školy"})
    log.info(f"Geokoordináty přidány. Náhled dat: {df.head()}")


    # Zápis finální tabulky
    df.write_excel("new.xlsx")
    log.info("Výsledná tabulka byla úspěšně vytvořena jako new.xlsx")

    return df



if __name__ == "__main__":
    result = data_loader()
    print(result.head())
    log.info("Data loader finished successfully.")

