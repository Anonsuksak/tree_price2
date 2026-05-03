import streamlit as st
import pandas as pd
import plotly.express as px
import os

# การตั้งค่าหน้าจอ
st.set_page_config(page_title="Tree Compensation Dashboard", layout="wide")

# ฟังก์ชันจัดการข้อมูล
DATA_PATH = 'data.csv'

@st.cache_data
def load_data():
    if os.path.exists(DATA_PATH):
        df = pd.read_csv(DATA_PATH)
        return df
    return pd.DataFrame()

# โหลดข้อมูลเข้า Session State
if 'df' not in st.session_state:
    st.session_state.df = load_data()

# --- SIDEBAR MENU ---
st.sidebar.title("🌳 ระบบจัดการค่าทดแทน")
menu = st.sidebar.radio("เมนูหลัก", ["🔍 ค้นหาและ Dashboard", "➕ เพิ่มข้อมูลใหม่"])

# --- หน้าที่ 1: ค้นหาและ DASHBOARD ---
if menu == "🔍 ค้นหาและ Dashboard":
    st.title("📊 Dashboard และระบบค้นหาค่าทดแทนพืชผล")
    
    # ตัวกรองข้อมูล
    st.sidebar.markdown("---")
    search_query = st.sidebar.text_input("ค้นหาชื่อพืช/รหัสพืช", placeholder="เช่น ทุเรียน...")
    selected_year = st.sidebar.multiselect("เลือกปี พ.ศ.", 
                                          options=sorted(st.session_state.df['year'].unique()),
                                          default=[2568])
    acc_type = st.sidebar.multiselect("ประเภทบัญชี", 
                                     options=st.session_state.df['account_type'].unique(),
                                     default=['A', 'B'])

    # กรองข้อมูล
    df_filtered = st.session_state.df.copy()
    mask = df_filtered['year'].isin(selected_year) & df_filtered['account_type'].isin(acc_type)
    if search_query:
        mask &= (df_filtered['plant_name'].str.contains(search_query, na=False) | 
                 df_filtered['plant_id'].str.contains(search_query, na=False))
    
    df_display = df_filtered[mask]

    # ส่วนแสดง KPI
    c1, c2, c3 = st.columns(3)
    c1.metric("รายการที่พบ", f"{len(df_display)} รายการ")
    c2.metric("ราคาสูงสุด", f"{df_display['compensation_price'].max():,.0f} บาท")
    c3.metric("ราคาเฉลี่ย", f"{df_display['compensation_price'].mean():,.0f} บาท")

    # กราฟวิเคราะห์
    st.markdown("---")
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("📈 แนวโน้มราคาค่าทดแทนเฉลี่ยตามปี")
        trend_data = df_display.groupby('year')['compensation_price'].mean().reset_index()
        fig_line = px.line(trend_data, x='year', y='compensation_price', markers=True)
        st.plotly_chart(fig_line, use_container_width=True)
    
    with g2:
        st.subheader("📊 สัดส่วนราคาตามประเภทพืช (Top 10)")
        top_10 = df_display.nlargest(10, 'compensation_price')
        fig_bar = px.bar(top_10, x='compensation_price', y='plant_name', orientation='h', color='compensation_price')
        st.plotly_chart(fig_bar, use_container_width=True)

    # ตารางข้อมูล
    st.subheader("📑 รายละเอียดข้อมูล")
    st.dataframe(df_display, use_container_width=True, hide_index=True)

# --- หน้าที่ 2: เพิ่มข้อมูลใหม่ ---
elif menu == "➕ เพิ่มข้อมูลใหม่":
    st.title("➕ เพิ่มข้อมูลพืชผลและราคาใหม่")
    st.info("คุณสามารถเพิ่มรายการใหม่ลงในฐานข้อมูลได้โดยตรง ข้อมูลจะถูกบันทึกลงไฟล์ CSV")

    with st.form("add_form", clear_on_submit=True):
        f1, f2 = st.columns(2)
        with f1:
            p_id = st.text_input("รหัสพืช (Plant ID)", placeholder="เช่น PLTA9999")
            p_name = st.text_input("ชื่อรายการต้นไม้/พืชผล")
            p_type = st.selectbox("ประเภทบัญชี", ["A", "B"])
            p_year = st.number_input("ปี พ.ศ.", value=2568)
        with f2:
            p_cat = st.text_input("หมวดหมู่ (ก-ฮ)")
            p_unit = st.text_input("หน่วย", value="ต้น")
            p_cond = st.selectbox("สภาพพืช", ["มีผล/ขนาดใหญ่", "ไม่มีผล/ขนาดเล็ก"])
            p_price = st.number_input("ราคาค่าทดแทน (บาท)", min_value=0.0)

        submit = st.form_submit_button("💾 บันทึกข้อมูล")

        if submit:
            if p_id and p_name:
                new_data = {
                    'id': len(st.session_state.df) + 1,
                    'plant_id': p_id,
                    'account_type': p_type,
                    'category': p_cat,
                    'is_active': 1,
                    'plant_name': p_name,
                    'unit': p_unit,
                    'plant_condition': p_cond,
                    'year': p_year,
                    'compensation_price': p_price
                }
                # อัปเดต Data
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_data])], ignore_index=True)
                st.session_state.df.to_csv(DATA_PATH, index=False, encoding='utf-8-sig')
                st.success(f"เพิ่มข้อมูล '{p_name}' เรียบร้อยแล้ว! สามารถไปเช็กได้ที่หน้า Dashboard")
            else:
                st.error("กรุณากรอกข้อมูล รหัสพืช และ ชื่อพืช")