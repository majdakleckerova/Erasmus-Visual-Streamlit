from typing import List
import polars as pl
import logging as log
### parseLines()
# Umí číst buď Excel (.xlsx), nebo textový soubor (.txt)., Vrátí seznam „ERASMUS CODE“ hodnot.
# Používá se při mazání škol.
def parseLines(excel_file:any) -> List[str]:
    log.info("Starting file parsing by ascertaining file input type.")
    if type(excel_file) != str:
        try:
            excel_file = excel_file.name
        except:
            log.info("Type determination failed at input type determination. Throwing error.")
            raise ValueError("File has been inputted via an illegal method.")
        
    log.info(excel_file)
    
    match excel_file.split(".")[-1]:
        case "xlsx":
            log.info("File is an excel file.")
            buffer = pl.read_excel(excel_file)
            return buffer.to_series(buffer.get_column_index("ERASMUS CODE")).to_list()
        case "txt":
            log.info("File is a text file.")
            with open(excel_file, "r") as txtfile:
                return txtfile.read().split('\n')
        case _:
            log.info("Uh oh.")
            raise ValueError("File is of an unreadable format.")