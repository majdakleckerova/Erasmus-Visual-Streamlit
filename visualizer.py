import streamlit as st
import polars as pl

try:
    schools = pl.read_excel("schools.xlsx")
except:
    schools = pl.DataFrame({"name":["School 1", "School 2", "School 3"]})

st.header("UJEP PRF Erasmus")
st.divider()

st.map

