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

    # --- načtení cache (pokud existuje)
    if os.path.exists("coords_cache.xlsx"):
        cache = pl.read_excel("coords_cache.xlsx")
        log.info(f"Načteno {len(cache)} uložených souřadnic z coords_cache.xlsx")
    else:
        cache = pl.DataFrame({"ERASMUS CODE": [], "Latitude": [], "Longtitude": []})


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

    # --- uložení nové cache (sloučení se starou)
    new_cache = pl.from_dict(df_maker)
    combined = cache.join(new_cache, on="ERASMUS CODE", how="outer_coalesce")
    combined.write_excel("coords_cache.xlsx")
    log.info(f"Cache aktualizována: {len(combined)} záznamů uloženo.")


    # Přidání koordinací do df
    df_maker = {"ERASMUS CODE":[], "Longtitude":[],"Latitude":[]}
    for loc in relocations.keys():
        df_maker["ERASMUS CODE"].append(loc)
        df_maker["Longtitude"].append(str(relocations[loc].longitude) if relocations[loc] != None else None)
        df_maker["Latitude"].append(str(relocations[loc].latitude) if relocations[loc] != None else None)
        reloc_info = f"{relocations[loc]} ({relocations[loc].latitude}, {relocations[loc].longitude})" if relocations[loc] != None else None
        log.info(f"{loc} - {reloc_info}")
    return new_schools.join(pl.from_dict(df_maker), "ERASMUS CODE", "left")