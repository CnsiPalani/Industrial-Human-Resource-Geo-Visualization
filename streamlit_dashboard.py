import streamlit as st
import pandas as pd
import plotly.express as px
import re
import os
import pandas.errors
import streamlit.components.v1 as components
from modules import utils

# Column name constants
COL_STATE_CODE = 'State Code'
COL_NIC_NAME = 'NIC Name'
COL_BUSINESS_CATEGORY = 'Business Category'
COL_DISTRICT_CODE = 'District Code'
COL_STATE_NAME = 'India/States'
COL_MAIN_WORKERS = 'Main Workers - Total -  Persons'
# --- Added constants for repeated worker columns ---
COL_MAIN_WORKERS_TOTAL_MALES = 'Main Workers - Total - Males'
COL_MAIN_WORKERS_TOTAL_FEMALES = 'Main Workers - Total - Females'
COL_MARGINAL_WORKERS_TOTAL_PERSONS = 'Marginal Workers - Total -  Persons'
COL_MARGINAL_WORKERS_TOTAL_MALES = 'Marginal Workers - Total - Males'
COL_MARGINAL_WORKERS_TOTAL_FEMALES = 'Marginal Workers - Total - Females'

def merge_csvs_from_dir(data_dir):
	"""
	Reads and merges all CSVs in a directory, normalizes columns.
	Returns merged DataFrame with canonical columns.
	"""
	
	csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
	df_list = []
	for file in csv_files:
		file_path = os.path.join(data_dir, file)
		try:
			df = try_read_csv(file_path)
			if df is None:
				warn_streamlit(f"Skipped file due to encoding issues: {file}")
				continue
		except pandas.errors.EmptyDataError:
			warn_streamlit(f"Skipped empty file: {file}")
			continue
		except Exception as e:
			warn_streamlit(f"Skipped file due to error: {file} ({e})")
			continue
		if df.empty or df.shape[1] == 0:
			warn_streamlit(f"Skipped file with no columns: {file}")
			continue
		df_list.append(df)
	if df_list:
		merged_df = pd.concat(df_list, ignore_index=True)
		return merged_df
	
def try_read_csv(file_path):
	"""Try reading a CSV file with multiple encodings."""
	encodings = ['utf-8', 'cp1252', 'latin1']
	for enc in encodings:
		try:
			return pd.read_csv(file_path, encoding=enc)
		except UnicodeDecodeError:
			continue
	return None

def warn_streamlit(message):
	"""Show a warning in Streamlit if available."""
	try:
		import streamlit as st
		st.warning(message)
	except ImportError:
		pass

# Load the data
file_path = 'C:\\WA\\POC\\Python\\IHRGV\\data\\DDW_B18_1200_NIC_FINAL_STATE_ARUNACHAL_PRADESH-2011.csv'
data_dir = "C:\\WA\\POC\\Python\\IHRGV\\data" 
data = merge_csvs_from_dir(data_dir)


# Clean the data
cleaned_data = data.dropna(how='all')
cleaned_data.columns = [col.strip() for col in cleaned_data.columns]

# Remove special characters and trim spaces from key columns
for col in ['State Code', 'District Code', 'India/States', 'Division', 'Group', 'Class']:
    if col in cleaned_data.columns:
        cleaned_data[col] = cleaned_data[col].astype(str).str.replace(r'[^\w\s-]', '', regex=True).str.strip()




# Clean the columns by removing backticks, trimming spaces, and zero-padding
for col, width in zip(['Division', 'Group', 'Class'], [2, 3, 4]):
    cleaned_data[col] = cleaned_data[col].astype(str).str.replace('`', '').str.strip().str.zfill(width)

cleaned_data[COL_NIC_NAME] = cleaned_data[COL_NIC_NAME].astype(str).str.strip()




# Categorize business activities using NLP keywords

categories = {
    'Retail': ['stalls', 'markets', 'via', 'or', 'food', 'beverages', 'tobacco', 'motor', 'non-specialized', 'household'],
    'Poultry': ['raising', 'poultry'],
    'Agriculture': ['growing', 'crops', 'fruits', 'crop', 'forestry', 'support', 'rice', 'non-perennial', 'perennial', 'post-harvest'],
    'Manufacturing': ['machinery', 'vehicles', 'metal', 'apparel', 'basic', 'motor', 'chemical', 'paper', 'rubber', 'animal'],
    'Education': ['education', 'secondary', 'cultural', 'educational', 'support', 'general', 'higher', 'primary', 'regulation', 'providing'],
    'Healthcare': ['health', 'mental', 'transportation', 'human', 'residential', 'care', 'retardation', 'hospital', 'medical', 'dental']
}



def categorize_activity(nic_name):
    nic_name_lower = str(nic_name).lower()
    for category, keywords in categories.items():
        if any(re.search(keyword, nic_name_lower) for keyword in keywords):
            return category
    return 'Other'

# Assign business category before filtering out 'Total' row
cleaned_data[COL_BUSINESS_CATEGORY] = cleaned_data[COL_NIC_NAME].apply(categorize_activity)

# Remove the 'Total' row from the cleaned data for all downstream analysis
base_data = cleaned_data[~(
    (cleaned_data['Division'] == '00') &
    (cleaned_data['Group'] == '000') &
    (cleaned_data['Class'] == '0000') &
    (cleaned_data[COL_NIC_NAME].str.lower() == 'total')
)]





# --- Streamlit UI Enhancements ---
st.set_page_config(
    page_title="Industrial Human Resource Geo-Visualization",
    page_icon="🧑‍🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Compute states, districts, categories_list for sidebar metrics and filters
state_mask = base_data[COL_STATE_NAME].str.upper().str.startswith('STATE')
states = base_data.loc[state_mask, COL_STATE_NAME].unique()
districts = base_data[COL_STATE_NAME].dropna().astype(str).str.strip()
districts = districts[(districts != '') & (~districts.str.upper().str.startswith('STATE'))]
districts = districts.unique()
categories_list = base_data[COL_BUSINESS_CATEGORY].unique() if COL_BUSINESS_CATEGORY in base_data.columns else []


st.markdown("""
<style>
.main > div {
    background: #f8fafc;
    border-radius: 10px;
    padding: 1.5rem 2rem 1rem 2rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.stTabs [data-baseweb="tab-list"] button {
    font-size: 1.1rem;
    font-weight: 600;
}
.stPlotlyChart {background: #fff; border-radius: 8px;}
.stDataFrame {background: #fff; border-radius: 8px;}

/* Sidebar background and text color */
section[data-testid="stSidebar"] {
    background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
    color: #222;
}
section[data-testid="stSidebar"] .stMultiSelect, section[data-testid="stSidebar"] .stSelectbox {
    background: #f1f5fa !important;
    border-radius: 8px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    font-weight: 600;
    font-size: 1.08em;
    margin-bottom: 1em;
}
section[data-testid="stSidebar"] label {
    color: #3b3b6d !important;
    font-weight: 700;
}
section[data-testid="stSidebar"] .stMultiSelect [data-baseweb="select"] {
    background: #e0e7ff !important;
    border-radius: 8px !important;
    font-size: 1.08em;
    font-weight: 600;
}
section[data-testid="stSidebar"] .stMultiSelect [data-baseweb="select"] div {
    color: #222 !important;
}
</style>
""", unsafe_allow_html=True)


# --- Welcome Banner ---
st.markdown("""
<div style='background: linear-gradient(90deg, #e0e7ff 0%, #f8fafc 100%); border-radius: 12px; padding: 1.2em 2em; margin-bottom: 1.5em; display: flex; align-items: center;'>
	<span style='font-size:2.2em; margin-right: 0.5em;'>🧑‍🏭</span>
	<span style='font-size:1.5em; font-weight:600;'>Industrial Human Resource Geo-Visualization</span>
</div>
<div style='font-size:1.1em; color:#444; margin-bottom:1.5em;'>
	<b>Welcome!</b> Explore India's industrial workforce by state, district, and business category. Use the sidebar to filter and the tabs below for advanced analytics.
</div>
""", unsafe_allow_html=True)


selected_states = st.sidebar.multiselect('🗂️ Select State(s):', states, default=states)

# Based selected  state  to filter the district 
dfs = base_data[base_data[COL_STATE_NAME].isin(selected_states)]
selected_states_code=dfs[COL_STATE_CODE].unique()
base_data = base_data[base_data[COL_STATE_CODE].isin(selected_states_code)]

# Use only values from India/States column that start with 'District' for the district dropdown
districts = base_data[COL_STATE_NAME].dropna().astype(str).str.strip()
districts = districts[(districts != '') & (~districts.str.upper().str.startswith('STATE'))]
districts = districts.unique()
selected_districts = st.sidebar.multiselect('🏙️ Select District(s):', districts, default=districts)


df2 = base_data[base_data[COL_STATE_NAME].isin(selected_districts)]
categories_list = df2[COL_BUSINESS_CATEGORY].unique()
selected_categories = st.sidebar.multiselect('🏭 Select Business Category:', categories_list, default=categories_list)

# Filter data for district chart: only rows where India/States starts with 'District' and matches selected districts
district_mask = base_data[COL_STATE_NAME].astype(str).str.upper().str.startswith('DISTRICT')
filtered_district_data = base_data[district_mask & base_data[COL_STATE_NAME].isin(selected_districts) & base_data[COL_BUSINESS_CATEGORY].isin(selected_categories)]

# Filter data for state chart: only rows where India/States starts with 'STATE' and matches selected states
state_mask = base_data[COL_STATE_NAME].astype(str).str.upper().str.startswith('STATE')
filtered_state_data = base_data[state_mask & base_data[COL_STATE_NAME].isin(selected_states) & base_data[COL_BUSINESS_CATEGORY].isin(selected_categories)]

# Filtered data for table: union of both
filtered_data = pd.concat([filtered_district_data, filtered_state_data])


# Debug: Show if any 'Total' rows remain

# Summarize data
category_summary = filtered_data.groupby(COL_BUSINESS_CATEGORY)[COL_MAIN_WORKERS].sum().reset_index()
district_summary = filtered_district_data.groupby(COL_STATE_NAME)[COL_MAIN_WORKERS].sum().reset_index()
state_summary = filtered_state_data.groupby(COL_STATE_NAME)[COL_MAIN_WORKERS].sum().reset_index()

# --- Quick Stats in Main Header ---
worker_columns = [
        'Main Workers - Total -  Persons', COL_MAIN_WORKERS_TOTAL_MALES, COL_MAIN_WORKERS_TOTAL_FEMALES,
        'Main Workers - Rural -  Persons', 'Main Workers - Rural -  Males', 'Main Workers - Rural -  Females',
        'Main Workers - Urban -  Persons', 'Main Workers - Urban -  Males', 'Main Workers - Urban -  Females',
        COL_MARGINAL_WORKERS_TOTAL_PERSONS, COL_MARGINAL_WORKERS_TOTAL_MALES, COL_MARGINAL_WORKERS_TOTAL_FEMALES,
        'Marginal Workers - Rural -  Persons', 'Marginal Workers - Rural -  Males', 'Marginal Workers - Rural -  Females',
        'Marginal Workers - Urban -  Persons', 'Marginal Workers - Urban -  Males', 'Marginal Workers - Urban -  Females'
]

def safe_sum(col):
	if col in filtered_data.columns:
		intval = int(pd.to_numeric(filtered_data[col], errors='coerce').fillna(0).sum())
		return intval
	return 0

main_total = safe_sum('Main Workers - Total -  Persons')
main_males = safe_sum(COL_MAIN_WORKERS_TOTAL_MALES)
main_females = safe_sum(COL_MAIN_WORKERS_TOTAL_FEMALES)
main_rural = safe_sum('Main Workers - Rural -  Persons')
main_urban = safe_sum('Main Workers - Urban -  Persons')
marginal_total = safe_sum(COL_MARGINAL_WORKERS_TOTAL_PERSONS)
marginal_males = safe_sum(COL_MARGINAL_WORKERS_TOTAL_MALES)
marginal_females = safe_sum(COL_MARGINAL_WORKERS_TOTAL_FEMALES)
marginal_rural = safe_sum('Marginal Workers - Rural -  Persons')
marginal_urban = safe_sum('Marginal Workers - Urban -  Persons')

st.markdown(f"""
<div style='display: flex; flex-wrap: wrap; gap: 2em; align-items: flex-start; margin-bottom: 1.5em;'>
	<div style='background: #f1f5fa; border-radius: 10px; padding: 1em 2em; box-shadow: 0 2px 8px rgba(0,0,0,0.04); min-width:220px;'>
		<b>📊 Total States:</b> {len(states)}<br>
		<b>🏙️ Total Districts:</b> {len(districts)}<br>
		<b>🏭 Business Categories:</b> {len(categories_list)}
	</div>
	<div style='background: #f1f5fa; border-radius: 10px; padding: 1em 2em; box-shadow: 0 2px 8px rgba(0,0,0,0.04); min-width:260px;'>
		<b>👷 Main Workers</b><br>
		Total: <b>{main_total:,}</b><br>
		Males: <b>{main_males:,}</b> &nbsp; Females: <b>{main_females:,}</b><br>
		Rural: <b>{main_rural:,}</b> &nbsp; Urban: <b>{main_urban:,}</b>
	</div>
	<div style='background: #f1f5fa; border-radius: 10px; padding: 1em 2em; box-shadow: 0 2px 8px rgba(0,0,0,0.04); min-width:260px;'>
		<b>🧑‍🌾 Marginal Workers</b><br>
		Total: <b>{marginal_total:,}</b><br>
		Males: <b>{marginal_males:,}</b> &nbsp; Females: <b>{marginal_females:,}</b><br>
		Rural: <b>{marginal_rural:,}</b> &nbsp; Urban: <b>{marginal_urban:,}</b>
	</div>
</div>
""", unsafe_allow_html=True)

# --- Wizard/Tab UI ---
wizard_tab = st.tabs(["1️⃣ Data Overview", "2️⃣ Visualizations", "3️⃣ Machine Learning"])

# --- Tab 1: Data Overview ---
with wizard_tab[0]:
	st.markdown('Use the filters in the sidebar to customize the data below. You can sort and search the table interactively.')
	st.dataframe(filtered_data, use_container_width=True)
	with st.expander("See sample of filtered data", expanded=False):
		st.dataframe(filtered_data.head(10), use_container_width=True)




# --- Tab 2: Visualizations ---

with wizard_tab[1]:
    viz_options = [
        "👷 Main Workers",
        "🧑‍🌾 Marginal Workers",
        "📊 Combined Main vs Marginal",
        "🏞️ Main: Rural/Urban",
        "👫 Main: Male vs Female",
        "🏞️ Marginal: Rural/Urban",
        "👫 Marginal: Male vs Female"
    ]
    viz_view = st.selectbox(
        "<span style='font-size:1.1em; font-weight:600;'>Select Visualization View:</span>",
        viz_options,
        key="viz_view_select",
        format_func=lambda x: x,
        help="Choose a visualization type to explore different aspects of the workforce."
    )
    st.markdown("""
    <style>
    .stSelectbox > div[data-baseweb="select"] {
        background: #f8fafc;
        border-radius: 8px;
        padding: 0.5em 1em;
        font-size: 1.1em;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        margin-bottom: 1.2em;
    }
    </style>
    """, unsafe_allow_html=True)

    def group_sum(df, group_col, sum_col):
        return df.groupby(group_col)[sum_col].sum().reset_index()

    def group_sum_multi(df, group_col, sum_cols):
        return df.groupby(group_col)[sum_cols].sum().reset_index()

    if viz_view == "👷 Main Workers":
        st.markdown("#### <span style='font-size:1.2em'>🏞️ Main Workers by State</span>", unsafe_allow_html=True)
        main_state = group_sum(filtered_state_data, COL_STATE_NAME, COL_MAIN_WORKERS)
        fig = px.bar(main_state, x=COL_STATE_NAME, y=COL_MAIN_WORKERS, color=COL_STATE_NAME)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### <span style='font-size:1.2em'>🏙️ Main Workers by District</span>", unsafe_allow_html=True)
        main_district = group_sum(filtered_district_data, COL_STATE_NAME, COL_MAIN_WORKERS)
        fig = px.bar(main_district, x=COL_STATE_NAME, y=COL_MAIN_WORKERS, color=COL_STATE_NAME)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### <span style='font-size:1.2em'>📊 Main Workers by Business Category</span>", unsafe_allow_html=True)
        main_cat = group_sum(filtered_data, COL_BUSINESS_CATEGORY, COL_MAIN_WORKERS)
        fig = px.bar(main_cat, x=COL_BUSINESS_CATEGORY, y=COL_MAIN_WORKERS, color=COL_BUSINESS_CATEGORY)
        st.plotly_chart(fig, use_container_width=True)

    elif viz_view == "🧑‍🌾 Marginal Workers":
        st.markdown("#### <span style='font-size:1.2em'>🏞️ Marginal Workers by State</span>", unsafe_allow_html=True)
        marg_state = group_sum(filtered_state_data, COL_STATE_NAME, COL_MARGINAL_WORKERS_TOTAL_PERSONS)
        fig = px.bar(marg_state, x=COL_STATE_NAME, y=COL_MARGINAL_WORKERS_TOTAL_PERSONS, color=COL_STATE_NAME)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### <span style='font-size:1.2em'>🏙️ Marginal Workers by District</span>", unsafe_allow_html=True)
        marg_district = group_sum(filtered_district_data, COL_STATE_NAME, COL_MARGINAL_WORKERS_TOTAL_PERSONS)
        fig = px.bar(marg_district, x=COL_STATE_NAME, y=COL_MARGINAL_WORKERS_TOTAL_PERSONS, color=COL_STATE_NAME)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### <span style='font-size:1.2em'>📊 Marginal Workers by Business Category</span>", unsafe_allow_html=True)
        marg_cat = group_sum(filtered_data, COL_BUSINESS_CATEGORY, COL_MARGINAL_WORKERS_TOTAL_PERSONS)
        fig = px.bar(marg_cat, x=COL_BUSINESS_CATEGORY, y=COL_MARGINAL_WORKERS_TOTAL_PERSONS, color=COL_BUSINESS_CATEGORY)
        st.plotly_chart(fig, use_container_width=True)

    elif viz_view == "📊 Combined Main vs Marginal":
        st.markdown("#### <span style='font-size:1.2em'>🏞️ Main vs Marginal by State</span>", unsafe_allow_html=True)
        combined_state = group_sum_multi(filtered_state_data, COL_STATE_NAME, [COL_MAIN_WORKERS, COL_MARGINAL_WORKERS_TOTAL_PERSONS])
        fig = px.bar(combined_state, x=COL_STATE_NAME, y=[COL_MAIN_WORKERS, COL_MARGINAL_WORKERS_TOTAL_PERSONS], barmode='group',
                     labels={COL_MAIN_WORKERS:'Main', COL_MARGINAL_WORKERS_TOTAL_PERSONS:'Marginal'})
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### <span style='font-size:1.2em'>🏙️ Main vs Marginal by District</span>", unsafe_allow_html=True)
        combined_district = group_sum_multi(filtered_district_data, COL_STATE_NAME, [COL_MAIN_WORKERS, COL_MARGINAL_WORKERS_TOTAL_PERSONS])
        fig = px.bar(combined_district, x=COL_STATE_NAME, y=[COL_MAIN_WORKERS, COL_MARGINAL_WORKERS_TOTAL_PERSONS], barmode='group',
                     labels={COL_MAIN_WORKERS:'Main', COL_MARGINAL_WORKERS_TOTAL_PERSONS:'Marginal'})
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### <span style='font-size:1.2em'>📊 Main vs Marginal by Business Category</span>", unsafe_allow_html=True)
        combined_cat = group_sum_multi(filtered_data, COL_BUSINESS_CATEGORY, [COL_MAIN_WORKERS, COL_MARGINAL_WORKERS_TOTAL_PERSONS])
        fig = px.bar(combined_cat, x=COL_BUSINESS_CATEGORY, y=[COL_MAIN_WORKERS, COL_MARGINAL_WORKERS_TOTAL_PERSONS], barmode='group',
                     labels={COL_MAIN_WORKERS:'Main', COL_MARGINAL_WORKERS_TOTAL_PERSONS:'Marginal'})
        st.plotly_chart(fig, use_container_width=True)

    elif viz_view == "🏞️ Main: Rural/Urban":
        st.markdown("#### <span style='font-size:1.2em'>🏞️ Main Workers Rural vs Urban by State</span>", unsafe_allow_html=True)
        rural_col = 'Main Workers - Rural -  Persons'
        urban_col = 'Main Workers - Urban -  Persons'
        main_rural_urban = group_sum_multi(filtered_state_data, COL_STATE_NAME, [rural_col, urban_col])
        fig = px.bar(main_rural_urban, x=COL_STATE_NAME, y=[rural_col, urban_col], barmode='group',
                     labels={rural_col:'Rural', urban_col:'Urban'})
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### <span style='font-size:1.2em'>🏙️ Main Workers Rural vs Urban by District</span>", unsafe_allow_html=True)
        main_rural_urban_dist = group_sum_multi(filtered_district_data, COL_STATE_NAME, [rural_col, urban_col])
        fig = px.bar(main_rural_urban_dist, x=COL_STATE_NAME, y=[rural_col, urban_col], barmode='group',
                     labels={rural_col:'Rural', urban_col:'Urban'})
        st.plotly_chart(fig, use_container_width=True)

    elif viz_view == "👫 Main: Male vs Female":
        st.markdown("#### <span style='font-size:1.2em'>🏞️ Main Workers Male vs Female by State</span>", unsafe_allow_html=True)
        male_col = COL_MAIN_WORKERS_TOTAL_MALES
        female_col = COL_MAIN_WORKERS_TOTAL_FEMALES
        main_mf = group_sum_multi(filtered_state_data, COL_STATE_NAME, [male_col, female_col])
        fig = px.bar(main_mf, x=COL_STATE_NAME, y=[male_col, female_col], barmode='group',
                     labels={male_col:'Male', female_col:'Female'})
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### <span style='font-size:1.2em'>🏙️ Main Workers Male vs Female by District</span>", unsafe_allow_html=True)
        main_mf_dist = group_sum_multi(filtered_district_data, COL_STATE_NAME, [male_col, female_col])
        fig = px.bar(main_mf_dist, x=COL_STATE_NAME, y=[male_col, female_col], barmode='group',
                     labels={male_col:'Male', female_col:'Female'})
        st.plotly_chart(fig, use_container_width=True)

    elif viz_view == "🏞️ Marginal: Rural/Urban":
        st.markdown("#### <span style='font-size:1.2em'>🏞️ Marginal Workers Rural vs Urban by State</span>", unsafe_allow_html=True)
        marg_rural_col = 'Marginal Workers - Rural -  Persons'
        marg_urban_col = 'Marginal Workers - Urban -  Persons'
        marg_rural_urban = group_sum_multi(filtered_state_data, COL_STATE_NAME, [marg_rural_col, marg_urban_col])
        fig = px.bar(marg_rural_urban, x=COL_STATE_NAME, y=[marg_rural_col, marg_urban_col], barmode='group',
                     labels={marg_rural_col:'Rural', marg_urban_col:'Urban'})
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### <span style='font-size:1.2em'>🏙️ Marginal Workers Rural vs Urban by District</span>", unsafe_allow_html=True)
        marg_rural_urban_dist = group_sum_multi(filtered_district_data, COL_STATE_NAME, [marg_rural_col, marg_urban_col])
        fig = px.bar(marg_rural_urban_dist, x=COL_STATE_NAME, y=[marg_rural_col, marg_urban_col], barmode='group',
                     labels={marg_rural_col:'Rural', marg_urban_col:'Urban'})
        st.plotly_chart(fig, use_container_width=True)

    elif viz_view == "👫 Marginal: Male vs Female":
        st.markdown("#### <span style='font-size:1.2em'>🏞️ Marginal Workers Male vs Female by State</span>", unsafe_allow_html=True)
        marg_male_col = COL_MARGINAL_WORKERS_TOTAL_MALES
        marg_female_col = COL_MARGINAL_WORKERS_TOTAL_FEMALES
        marg_mf = group_sum_multi(filtered_state_data, COL_STATE_NAME, [marg_male_col, marg_female_col])
        fig = px.bar(marg_mf, x=COL_STATE_NAME, y=[marg_male_col, marg_female_col], barmode='group',
                     labels={marg_male_col:'Male', marg_female_col:'Female'})
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### <span style='font-size:1.2em'>🏙️ Marginal Workers Male vs Female by District</span>", unsafe_allow_html=True)
        marg_mf_dist = group_sum_multi(filtered_district_data, COL_STATE_NAME, [marg_male_col, marg_female_col])
        fig = px.bar(marg_mf_dist, x=COL_STATE_NAME, y=[marg_male_col, marg_female_col], barmode='group',
                     labels={marg_male_col:'Male', marg_female_col:'Female'})
        st.plotly_chart(fig, use_container_width=True)

# --- Tab 3: Machine Learning ---
with wizard_tab[2]:
	st.markdown("Use the tabs below to explore clustering and classification models. Hover over chart elements for details.")
	from sklearn.cluster import KMeans
	from sklearn.ensemble import RandomForestClassifier
	from sklearn.model_selection import train_test_split
	from sklearn.metrics import classification_report, accuracy_score
	import numpy as np
	ml_tab = st.tabs(["🔗 Clustering (KMeans)", "🧮 Classification (Random Forest)"])
	with ml_tab[0]:
		st.subheader("🔗 KMeans Clustering: Districts by Worker Composition")
		cluster_df = filtered_data.copy()
		cluster_features = [
            'Main Workers - Total -  Persons',
            COL_MARGINAL_WORKERS_TOTAL_PERSONS,
            COL_MAIN_WORKERS_TOTAL_MALES,
            COL_MAIN_WORKERS_TOTAL_FEMALES,
            COL_MARGINAL_WORKERS_TOTAL_MALES,
            COL_MARGINAL_WORKERS_TOTAL_FEMALES
        ]
		available_features = [col for col in cluster_features if col in cluster_df.columns]
		if len(available_features) >= 2:
			if 'India/States' in cluster_df.columns:
				group_df = cluster_df.groupby('India/States')[available_features].sum().dropna()
				n_clusters = st.slider("Number of clusters", 2, 8, 3)
				kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
				clusters = kmeans.fit_predict(group_df)
				group_df['Cluster'] = clusters
				st.write("Clustered Districts/States:")
				st.dataframe(group_df.reset_index())
				fig = px.scatter_matrix(
					group_df.reset_index(),
					dimensions=available_features,
					color='Cluster',
					title="Clusters by Worker Composition"
				)
				st.plotly_chart(fig, use_container_width=True)
			else:
				st.warning("'India/States' column not found for grouping.")
		else:
			st.warning("Not enough features available for clustering.")
	with ml_tab[1]:
		st.subheader("🧮 Random Forest Classification: Predict Business Category")
		class_df = filtered_data.copy()
		class_features = [
            'Main Workers - Total -  Persons',
            COL_MARGINAL_WORKERS_TOTAL_PERSONS,
            COL_MAIN_WORKERS_TOTAL_MALES,
            COL_MAIN_WORKERS_TOTAL_FEMALES,
            COL_MARGINAL_WORKERS_TOTAL_MALES,
            COL_MARGINAL_WORKERS_TOTAL_FEMALES
        ]
		available_class_features = [col for col in class_features if col in class_df.columns]
		if COL_BUSINESS_CATEGORY in class_df.columns and len(available_class_features) >= 2:
			class_df = class_df.dropna(subset=[COL_BUSINESS_CATEGORY])
			
			X = class_df[available_class_features].fillna(0)
			y = class_df[COL_BUSINESS_CATEGORY]
			if y.nunique() > 1:
				X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
				clf = RandomForestClassifier( 					
						n_estimators=600,
						max_depth=None,
						min_samples_leaf=2,
						max_features='sqrt',
						n_jobs=-1,
						random_state=42,
						class_weight='balanced'  # helpful for imbalance
				)
				clf.fit(X_train, y_train)
				y_pred = clf.predict(X_test)
				acc = accuracy_score(y_test, y_pred)
				st.write(f"**Test Accuracy:** {acc:.2f}")
				st.text("Classification Report:")
				st.text(classification_report(y_test, y_pred))
				importances = clf.feature_importances_
				feat_imp_df = pd.DataFrame({'Feature': available_class_features, 'Importance': importances})
				fig_imp = px.bar(feat_imp_df.sort_values('Importance', ascending=False), x='Importance', y='Feature', orientation='h', title="Feature Importances")
				st.plotly_chart(fig_imp, use_container_width=True)
			else:
				st.warning("Not enough classes in Business Category for classification.")
		else:
			st.warning("Not enough features or target for classification.")

# --- Footer ---
st.markdown("""
<hr style='margin-top:2em; margin-bottom:0.5em;'>
<div style='text-align:center; color:#888; font-size:1em;'>
  Made with ❤️ using Streamlit & Plotly | 2026
</div>
""", unsafe_allow_html=True)


