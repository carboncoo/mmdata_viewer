import streamlit as st
import json
import pandas as pd
import os
from PIL import Image

import streamlit as st
st.set_page_config(page_title="Data Viewer", layout="wide")
st.title("Data Viewer")

# Paths for storing multiple config profiles
def get_profiles_path():
    return os.path.join(os.getcwd(), 'config_profiles.json')

# Load or create default profiles
def load_profiles():
    path = get_profiles_path()
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    # Default single profile
    default = {
        "HRScene": {
            "json_path": "example_data/hrscene/annotations.json",
            "pred_dir": "",
            "image_root": "example_data/hrscene/images"
        },
        "MME-Realworld": {
            "json_path": "example_data/mme_realworld/MME_realworld.json",
            "pred_dir": "example_data/mme_realworld/mme_realwolrd_test_results",
            "image_root": "example_data/mme_realworld/mme_images"
        }
    }
    save_profiles(default)
    return default

# Save profiles dict to file
def save_profiles(profiles):
    path = get_profiles_path()
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(profiles, f, indent=2)

# Streamlit UI: select or create profile
st.sidebar.header('Configuration Profiles')
profiles = load_profiles()
profiles_keys = list(profiles.keys())
selected_profile = st.sidebar.selectbox('Select Profile', profiles_keys)

# New profile creation
with st.sidebar.expander('Create New Profile'):
    new_name = st.text_input('New profile name')
    if st.button('Create Profile'):
        if new_name and new_name not in profiles:
            profiles[new_name] = profiles[selected_profile].copy()
            save_profiles(profiles)
            st.success(f'Profile "{new_name}" created. Please select it.')
        else:
            st.error('Invalid or duplicate profile name')

# Edit selected profile
with st.sidebar.expander(f'Edit Profile: {selected_profile}', expanded=False):
    cfg = profiles[selected_profile]
    json_path_input = st.text_input('JSON Path:', value=cfg['json_path'], key='cfg_json')
    pred_dir_input = st.text_input('Predictions Dir:', value=cfg['pred_dir'], key='cfg_pred')
    image_root_input = st.text_input('Image Root Dir:', value=cfg['image_root'], key='cfg_img')
    if st.button('Save Profile'):
        profiles[selected_profile]['json_path'] = json_path_input
        profiles[selected_profile]['pred_dir'] = pred_dir_input
        profiles[selected_profile]['image_root'] = image_root_input
        save_profiles(profiles)
        st.success(f'Profile "{selected_profile}" updated')

# Use selected profile
cfg = profiles[selected_profile]

# Expand modals for tables
st.markdown(
    """
    <style>
    div[role=\"dialog\"] > div {
        width: 90vw !important;
        max-width: 90vw !important;
    }
    </style>
    """, unsafe_allow_html=True
)
# Display options
st.sidebar.header("Display Options")
max_rows = st.sidebar.number_input(
    "Max rows to display:", min_value=10, max_value=1000, value=100, step=10, key="max_rows"
)

@st.cache_data
def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

@st.dialog("Original Image")
def original_image(full_path, current_qid):
    img = Image.open(full_path)
    width, _ = img.size
    st.image(img, caption=f"Original - {current_qid}", width=width)

@st.dialog("Model Comparison")
def comparison_dialog(acc_df):
    st.dataframe(
        acc_df.style.format("{:.2%}").highlight_max(axis=1),
        use_container_width=True
    )

# Load main JSON
raw = []
if os.path.exists(cfg['json_path']):
    try:
        raw = load_json(cfg['json_path'])
    except Exception:
        st.error('Failed to load JSON from config path')
else:
    st.error('JSON path from config not found')

# Build DataFrame
df = pd.json_normalize(raw)
if df.empty:
    st.info("No data loaded. Check profile config or upload JSON.")
    st.stop()

if 'Task' not in df.columns:
    df['Task'] = ''
    
if 'Subtask' not in df.columns:
    df['Subtask'] = ''

if 'Category' not in df.columns:
    df['Category'] = ''

# Composite category
df['FullCategory'] = (
    df['Task'].fillna('') + '/' + df['Subtask'].fillna('') + '/' + df['Category'].fillna('')
)

# Load and merge predictions
pred_tables = []
if os.path.isdir(cfg['pred_dir']):
    for fname in os.listdir(cfg['pred_dir']):
        if fname.endswith('.json'):
            model = os.path.splitext(fname)[0]
            try:
                data = load_json(os.path.join(cfg['pred_dir'], fname))
                dfp = pd.json_normalize(data)[['Question_id', 'response', 'correct']]
                dfp = dfp.groupby('Question_id', as_index=False).first()
                dfp = dfp.set_index('Question_id').rename(
                    columns={'response': f'{model}_response', 'correct': f'{model}_correct'}
                )
                pred_tables.append(dfp)
            except:
                st.warning(f"Prediction load failed: {fname}")
    if pred_tables:
        merged = pd.concat(pred_tables, axis=1)
        df = df.set_index('Question_id').join(merged).reset_index()
        st.sidebar.header("Model Accuracy")
        for col in df.columns:
            if col.endswith('_correct'):
                st.sidebar.write(f"**{col[:-8]}:** {df[col].mean():.2%}")
else:
    st.sidebar.warning('Predictions directory not found')

# Filters
# Task Filter
st.sidebar.header("Task Filter")
tasks = ['All'] + sorted(df['Task'].dropna().unique())
selected_task = st.sidebar.selectbox('Task:', tasks)
if selected_task != 'All':
    df = df[df['Task'] == selected_task]

# Subtask Filter
st.sidebar.header("Subtask Filter")
subtasks = ['All'] + sorted(df['Subtask'].dropna().unique())
selected_subtask = st.sidebar.selectbox('Subtask:', subtasks)
if selected_subtask != 'All':
    df = df[df['Subtask'] == selected_subtask]

# Category Filter
st.sidebar.header("Category Filter")
cats = ['All'] + sorted(df['FullCategory'].unique())
sel_cat = st.sidebar.selectbox('Category:', cats)
if sel_cat != 'All': df = df[df['FullCategory']==sel_cat]

qid = st.sidebar.text_input('Filter Question ID contains:')
if qid: df = df[df['Question_id'].str.contains(qid, na=False, case=False)]

# Prediction correctness filter
if pred_tables:
    st.sidebar.header('Prediction Filter')
    models = sorted({c[:-8] for c in df.columns if c.endswith('_correct')})
    sel_models = st.sidebar.multiselect('Models:', models)
    mod_status = {}
    for m in sel_models:
        mod_status[m] = st.sidebar.selectbox(f'{m} status:', ['All','Correct','Incorrect'], key=f'st_{m}')
    for m,s in mod_status.items():
        col = f'{m}_correct'
        if s=='Correct': df = df[df[col]==True]
        if s=='Incorrect': df = df[df[col]==False]

    # Compare models button
    if sel_models and st.sidebar.button('Compare Models by Task'):
        accs = {m: df.groupby('FullCategory')[f'{m}_correct'].mean().fillna(0) for m in sel_models}
        acc_df = pd.DataFrame(accs); acc_df.index.name='FullCategory'
        comparison_dialog(acc_df)

# Summary and table
st.subheader(f'Total rows: {len(df)}')
cols = ['Question_id','Question Type','Text','Ground truth'] + [c for c in df.columns if c.endswith('_response')]
st.dataframe(df.head(max_rows)[cols], use_container_width=True)

# Navigation
def clamp(i): return max(0, min(i, len(df)-1))
if 'idx' not in st.session_state: st.session_state.idx=0
p,n = st.sidebar.columns(2)
if p.button('Previous'): st.session_state.idx = clamp(st.session_state.idx-1)
if n.button('Next'): st.session_state.idx = clamp(st.session_state.idx+1)
row = df.iloc[st.session_state.idx]
st.markdown(f'### Details for {row.Question_id}')
c1,c2 = st.columns([1,2])
with c1:
    path = os.path.join(cfg['image_root'], row.Image)
    try: st.image(path, use_container_width=True)
    except: st.write('Image missing')
    if st.button('View Original', key='orig2'): original_image(path, row.Question_id)
with c2:
    st.write('**Question:**', row.Text)
    for ch in row['Answer choices']:
        st.write('-', ch)
    st.write('**Ground Truth:**', row['Ground truth'])
