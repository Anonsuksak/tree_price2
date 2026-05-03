import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Tree Price Analytics Pro", layout="wide", page_icon="🌳")

DATA_PATH = 'data.csv'

@st.cache_data
def load_data():
    if os.path.exists(DATA_PATH):
        df = pd.read_csv(DATA_PATH)
        df.columns = df.columns.str.strip()
        
        # คลีนข้อมูลราคาและปี
        if 'compensation_price' in df.columns:
            df['compensation_price'] = df['compensation_price'].astype(str).str.replace(',', '', regex=False)
            df['compensation_price'] = pd.to_numeric(df['compensation_price'], errors='coerce')
        
        if 'year' in df.columns:
            df['year'] = pd.to_numeric(df['year'], errors='coerce')

        # คลีนช่องว่างในข้อมูล Text
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).str.strip()
            
        return df
    return pd.DataFrame()

if 'df' not in st.session_state:
    st.session_state.df = load_data()

# --- SIDEBAR ---
st.sidebar.header("🔍 ปรับแต่งการดูข้อมูล")

# ค้นหา
search_q = st.sidebar.text_input("ค้นหาชื่อพืช", placeholder="พิมพ์ชื่อพืช...")

# กรองปี
all_years = sorted(st.session_state.df['year'].dropna().unique().astype(int))
selected_years = st.sidebar.multiselect("เลือกปี พ.ศ.", options=all_years, default=all_years[-3:] if len(all_years) > 3 else all_years)

# กรองประเภทบัญชี
acc_types = st.sidebar.multiselect("ประเภทบัญชี", options=['A', 'B'], default=['A', 'B'], 
                                  format_func=lambda x: "A: ไม้ยืนต้น" if x == 'A' else "B: พืชล้มลุก")

# ✅ เพิ่ม Filter สภาพพืช (ตามที่คุณต้องการ)
all_conditions = st.session_state.df['plant_condition'].unique().tolist()
selected_conditions = st.sidebar.multiselect("สภาพพืช", options=all_conditions, default=all_conditions)

# --- กรองข้อมูลหลัก ---
mask = (st.session_state.df['year'].isin(selected_years)) & \
       (st.session_state.df['account_type'].isin(acc_types)) & \
       (st.session_state.df['plant_condition'].isin(selected_conditions))

if search_q:
    mask &= (st.session_state.df['plant_name'].str.contains(search_q, na=False))

df_filtered = st.session_state.df[mask]

# --- MAIN PAGE ---
st.title("🌳 วิเคราะห์ฐานข้อมูลราคาค่าทดแทนพืชผล")

# KPI Metrics
m1, m2, m3, m4 = st.columns(4)
m1.metric("รายการที่แสดง", f"{len(df_filtered):,}")
m2.metric("ราคาสูงสุด", f"{df_filtered['compensation_price'].max():,.0f} ฿")
m3.metric("ราคาเฉลี่ย", f"{df_filtered['compensation_price'].mean():,.0f} ฿")
m4.metric("ส่วนต่างราคาเฉลี่ย", f"{(df_filtered['compensation_price'].max() - df_filtered['compensation_price'].min()):,.0f} ฿")

st.markdown("---")

# --- วิเคราะห์เชิงลึก (Charts) ---
row1_col1, row1_col2 = st.columns([6, 4])

with row1_col1:
    # 📈 กราฟเปรียบเทียบ "มีผล vs ไม่มีผล" ในแต่ละปี
    st.subheader("📊 เปรียบเทียบราคาเฉลี่ย: มีผล vs ไม่มีผล (ตามปี)")
    if not df_filtered.empty:
        compare_data = df_filtered.groupby(['year', 'plant_condition'])['compensation_price'].mean().reset_index()
        fig_compare = px.bar(compare_data, x='year', y='compensation_price', 
                             color='plant_condition', barmode='group',
                             text_auto='.0f', labels={'compensation_price': 'ราคาเฉลี่ย (฿)'},
                             color_discrete_map={'มีผล/ขนาดใหญ่': '#2E7D32', 'ไม่มีผล/ขนาดเล็ก': '#81C784'})
        st.plotly_chart(fig_compare, use_container_width=True)

with row1_col2:
    # 🎯 กราฟสัดส่วนหมวดหมู่ที่ราคาสูงสุด
    st.subheader("📌 หมวดหมู่ที่มีมูลค่ารวมสูงสุด")
    cat_data = df_filtered.groupby('category')['compensation_price'].sum().sort_values(ascending=False).head(5).reset_index()
    fig_cat = px.pie(cat_data, values='compensation_price', names='category', hole=0.5,
                     color_discrete_sequence=px.colors.sequential.Greens_r)
    st.plotly_chart(fig_cat, use_container_width=True)

# 🌊 กราฟใหม่: วิเคราะห์การกระจายตัวของราคา (Box Plot / Scatter)
st.subheader("🔍 วิเคราะห์การกระจายตัวของราคาตามหมวดหมู่ (Price Distribution)")
fig_scatter = px.box(df_filtered, x='category', y='compensation_price', 
                     color='plant_condition', points="all",
                     hover_data=['plant_name'],
                     labels={'compensation_price': 'ราคา (฿)', 'category': 'หมวดหมู่ (ก-ฮ)'},
                     color_discrete_map={'มีผล/ขนาดใหญ่': '#2E7D32', 'ไม่มีผล/ขนาดเล็ก': '#81C784'})
st.plotly_chart(fig_scatter, use_container_width=True)

# ตารางข้อมูล
with st.expander("ดูตารางข้อมูลทั้งหมด"):
    st.dataframe(df_filtered.sort_values(by='compensation_price', ascending=False), use_container_width=True)