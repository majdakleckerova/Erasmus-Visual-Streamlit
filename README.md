# POUŽITÍ
- Skript přijímá tabulku ve formátu `.xlsx` generovanou stagem. 
- ! Tabulka musí obsahovat sloupce pojmenované `nabizetVAplikaciIIA` s možnostmi ["ANO","NE"],
`ciziSkolaNazev`,`ciziSkolaZkratka` ,`ciziSkolaMesto`,`ciziSkolaStatNazev`, `ciziUrl`, `domaciPracoviste`, `KodyISCEDVEWPSpecifSmlouvy`

1. Vložte soubor do stejného adresáře jako loader.py a visualizer.py a přejmenujte ho na `.....` .
2. Spusťe skript `loader.py` a vyčkejte (generování souřadnic chvíli trvá).
3. Po úspěšném dokončení zadejte do terminálu příkaz `streamlit run visualizer.py`
4. Hotovo.



--- 






# Erasmus-visualization: Streamlit varianta
Vizualizace možných zájezdů na Erasmus skrze streamlit. Pretty self-explanatory.
Akutální web verze (NEREFLEKTUJE AKTUALIZACE): erasmus-proto.streamlit.app

# Builděte to přes Docker: "docker-compose up --build"
## Pak ctrl + click na Local URL pro otevření stránky 

## Co je třeba udělat:
- Excel tabulku
    - Předělat katedry na obory                             [DONE]
    - Dodělat zbytek škol z poslaného souboru od Škvora     [SOMEWHAT DONE]
    - Spravit generaci koordinací
        * Některé školy nevracejí koordinace
        * Prakticky žádná škola nevrací validní koordinace
- Skript na přidání škol                                    [SOMEWHAT DONE]
- Přístup k dalším souborům and whatnot
- Sepsat sem všechno ostatní co spravit/přidat

## Experimentální funkce: Admin tools
### Jak se k nim dostat
1) Přejděte na AdminAccessContingency větev v gitu
```
git checkout AdminAccessContingency #Pro návrat do main větve nahradit AdminAccess... za main
```
2) Spustit visualizer ve streamlitu a přejít na localhost:5000/admin
3) Následovat pokyny na stránce

Admin tools jsou zavřený za dvěma vrstvama bezpečnosti:
- Na hlavní stránce o tom není zmínka (malá výjimka: pokud soubor schools.xlsx neexistuje, uživateli se zobrazí redirect na admin tools)
- STAG login spojenej s whitelistem
    - Whitelist není trackován gitem, inicializován při prvním loginu do admin tools (tento uživatel je přidán, zbytek se musí přidat nebo odebrat)
    - Whitelist je txt soubor, silně neideální
    - Bypass: Jít na localhost:500/admin&stagUserName={validní uživatelský jméno zašifrováno do base64}



### FINÁLNÍ ÚKOLY PRO ODEVZDÁNÍ
- **Vstupní data**: `Aplikace_IIA_zdroj_vzor.xlsx` ... tabulka vygenerovaná stagem 2x ročně; přidán sloupec *Nabízet v aplikaci k IIA* – `nabizetVAplikaciIIA` s možnostmi ["ANO","NE"] (momentálně default `ANO`)
- **Sloupce na frontendu**: 
    - Název zahraniční školy – `ciziSkolaNazev`
    - Erasmus kód zahraniční školy  – `ciziSkolaZkratka` 
    - město zahraniční školy – `ciziSkolaMesto`
    - země zahraniční školy – `ciziSkolaStatNazev`
    - webová adresa zahraniční školy – `ciziUrl`
    - domácí pracoviště (fakulta, katedra) – `domaciPracoviste`
    - kódy oborů - resp. názvy – `KodyISCEDVEWPSpecifSmlouvy`

- **PROBLÉMY**
    - **JEDNA UNIVERZITA JE V NĚKOLIKA ŘÁDCÍCH, V NĚKTERÝCH URL ATD. JE, JINDE NE, NĚKDE JEDEN KÓD OBORU, JINDE VÍCE ODDĚLENÝCH ČÁRKOU, NĚKDE DOMÁCÍ PRACOVIŠTĚ VE FORMÁTU XX/XXX, NĚKDE XX, NĚKDE JEDNO NĚKDE VÍCE STRAŠNÉ NA ZPRACOVÁNÍ**




