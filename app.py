import streamlit as st
import mysql.connector
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
    ssl_ca=os.getenv("DB_SSL_CA")
)

st.write("Connected successfully!" if conn.is_connected() else "Connection failed.")


cursor = conn.cursor()
cursor.execute("SELECT * FROM ffhh")
rows = cursor.fetchall()
columns = [desc[0] for desc in cursor.description]

df = pd.DataFrame(rows, columns=columns)
st.dataframe(df)

cursor.close()