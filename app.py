import streamlit as st
import pandas as pd
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

# ---------------------------------------
# PAGE CONFIG
# ---------------------------------------

st.set_page_config(page_title="Engineering College Predictor", layout="wide")

# ---------------------------------------
# PATHS (GITHUB / STREAMLIT SAFE)
# ---------------------------------------

BASE_DIR = os.path.dirname(__file__)

CET_FOLDER = os.path.join(BASE_DIR, "Xlsx Files")
JEE_FILE = os.path.join(BASE_DIR, "Xlsx Files", "College_Cutoff_Cleaned.xlsx")

# ---------------------------------------
# DISTRICT → UNIVERSITY MAP
# ---------------------------------------

district_university = {
    "Chhatrapati Sambhajinagar":"Dr. Babasaheb Ambedkar Marathwada University",
    "Beed":"Dr. Babasaheb Ambedkar Marathwada University",
    "Jalna":"Dr. Babasaheb Ambedkar Marathwada University",
    "Dharashiv":"Dr. Babasaheb Ambedkar Marathwada University",
    "Hingoli":"Swami Ramanand Teerth Marathwada University",
    "Latur":"Swami Ramanand Teerth Marathwada University",
    "Nanded":"Swami Ramanand Teerth Marathwada University",
    "Parbhani":"Swami Ramanand Teerth Marathwada University",
    "Mumbai City":"Mumbai University",
    "Mumbai Suburban":"Mumbai University",
    "Ratnagiri":"Mumbai University",
    "Raigad":"Mumbai University",
    "Palghar":"Mumbai University",
    "Sindhudurg":"Mumbai University",
    "Thane":"Mumbai University",
    "Dhule":"KBC North Maharashtra University",
    "Jalgaon":"KBC North Maharashtra University",
    "Nandurbar":"KBC North Maharashtra University",
    "Ahmednagar":"Savitribai Phule Pune University",
    "Nashik":"Savitribai Phule Pune University",
    "Pune":"Savitribai Phule Pune University",
    "Kolhapur":"Shivaji University",
    "Sangli":"Shivaji University",
    "Satara":"Shivaji University",
    "Solapur":"Solapur University",
    "Akola":"Sant Gadge Baba Amravati University",
    "Amravati":"Sant Gadge Baba Amravati University",
    "Buldana":"Sant Gadge Baba Amravati University",
    "Washim":"Sant Gadge Baba Amravati University",
    "Yavatmal":"Sant Gadge Baba Amravati University",
    "Bhandara":"Nagpur University",
    "Gondia":"Nagpur University",
    "Nagpur":"Nagpur University",
    "Wardha":"Nagpur University",
    "Chandrapur":"Gondwana University",
    "Gadchiroli":"Gondwana University"
}

# ---------------------------------------
# LOAD CET DATA
# ---------------------------------------

@st.cache_data
def load_cet_data():

    all_data = []

    for root, dirs, files in os.walk(CET_FOLDER):

        for file in files:

            if file.endswith(".xlsx"):

                path = os.path.join(root, file)

                try:
                    df = pd.read_excel(path)
                    df.columns = df.columns.str.strip()

                    name = file.split("_")[0]

                    gender = name[0]
                    university = name[-1]
                    category = name[1:-1].upper()

                    df["Gender"] = gender
                    df["Category"] = category
                    df["University_Type"] = university

                    all_data.append(df)

                except:
                    pass

    if len(all_data) == 0:
        return pd.DataFrame()

    return pd.concat(all_data, ignore_index=True)

# ---------------------------------------
# LOAD JEE DATA
# ---------------------------------------

@st.cache_data
def load_jee_data():

    df = pd.read_excel(JEE_FILE)
    df.columns = df.columns.str.strip()

    return df

# ---------------------------------------
# DETECT BRANCH COLUMN
# ---------------------------------------

def detect_branch_column(df):

    possible = ["Branch","Course","Course Name","Branch Name","Program"]

    for col in possible:
        if col in df.columns:
            return col

    return None

# ---------------------------------------
# PDF GENERATOR
# ---------------------------------------

def generate_pdf(data):

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)

    y = 750
    pdf.drawString(200,800,"College Prediction Result")

    for _, row in data.iterrows():

        text = f"{row['College Code']} | {row['College Name']} | {row['Branch']} | {row['Percentile']}"

        pdf.drawString(40,y,text)

        y -= 20

        if y < 50:
            pdf.showPage()
            y = 750

    pdf.save()

    buffer.seek(0)

    return buffer

# ---------------------------------------
# UI
# ---------------------------------------

st.title("🎓 Engineering College Predictor")

tab1, tab2 = st.tabs(["MH-CET Predictor","JEE Main Predictor"])

# =====================================================
# MH CET TAB
# =====================================================

with tab1:

    st.header("MH-CET College Predictor")

    df = load_cet_data()

    percentile = st.number_input("Enter CET Percentile",0.0,100.0,key="cet_percentile")

    gender = st.selectbox("Select Gender",["G","L"],key="cet_gender")

    categories = ["OPEN","SC","ST","VJ","NT1","NT2","NT3","SEBC","EWS","ORPHAN","TFWS"]
    category = st.selectbox("Select Category",categories,key="cet_category")

    university_type = st.selectbox(
        "University Type",
        ["Home University","Other University","State Level"],
        key="cet_uni"
    )

    district = st.selectbox(
        "Select District",
        sorted(district_university.keys()),
        key="cet_district"
    )

    st.info(f"Home University : {district_university[district]}")

    branch_column = detect_branch_column(df)

    if branch_column:

        branch = st.multiselect(
            "Select Branch",
            sorted(df[branch_column].dropna().unique()),
            key="cet_branch"
        )

    else:
        st.warning("Branch column not found")
        branch = []

    variation = st.slider(
        "Score Variation",
        0.0,10.0,2.0,
        key="cet_variation"
    )

    if st.button("Predict CET Colleges",key="cet_button"):

        result = df.copy()

        result = result[result["Gender"] == gender]
        result = result[result["Category"].str.upper() == category]

        if university_type == "Home University":
            result = result[result["University_Type"] == "H"]

        elif university_type == "Other University":
            result = result[result["University_Type"] == "O"]

        if branch and branch_column:
            result = result[result[branch_column].isin(branch)]

        if "Percentile" in result.columns:

            result = result[
                (result["Percentile"] >= percentile-variation) &
                (result["Percentile"] <= percentile+variation)
            ]

        if branch_column != "Branch":
            result.rename(columns={branch_column:"Branch"}, inplace=True)

        st.dataframe(result,use_container_width=True,hide_index=True)

        if len(result) > 0:

            pdf = generate_pdf(result)

            st.download_button(
                "Download PDF",
                pdf,
                "cet_prediction.pdf",
                "application/pdf"
            )

# =====================================================
# JEE TAB
# =====================================================

with tab2:

    st.header("JEE Main College Predictor")

    df = load_jee_data()

    percentile = st.number_input(
        "Enter JEE Percentile",
        0.0,100.0,
        key="jee_percentile"
    )

    branch_column = detect_branch_column(df)

    if branch_column:

        branch = st.multiselect(
            "Select Branch",
            sorted(df[branch_column].dropna().unique()),
            key="jee_branch"
        )

    else:
        st.warning("Branch column not found")
        branch = []

    variation = st.slider(
        "Score Variation",
        0.0,10.0,2.0,
        key="jee_variation"
    )

    if st.button("Predict JEE Colleges",key="jee_button"):

        result = df.copy()

        if branch and branch_column:
            result = result[result[branch_column].isin(branch)]

        if "Percentile" in result.columns:

            result = result[
                (result["Percentile"] >= percentile-variation) &
                (result["Percentile"] <= percentile+variation)
            ]

        st.dataframe(result,use_container_width=True,hide_index=True)
