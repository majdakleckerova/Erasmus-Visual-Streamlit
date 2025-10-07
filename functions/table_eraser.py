from loader import parseLines
import polars as pl
import logging as log
import os.path
from typing import Dict, List

### table_eraser(excel_file)
def table_eraser(excel_file) -> int:
    if not os.path.exists("schools.xlsx"):
        raise FileNotFoundError("First, make sure to have some schools.")
    log.info("Starting eraser.")
    lines:List[str] = parseLines(excel_file)
    current_schools = pl.read_excel("schools.xlsx")
    curLen = len(current_schools)
    current_schools = current_schools.filter(pl.col("ERASMUS CODE").is_in(lines).not_())
    current_schools.write_excel("schools.xlsx")
    log.info("Eraser finished correctly.")
    return curLen - len(current_schools)