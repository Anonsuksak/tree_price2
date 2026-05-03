import streamlit as st
import pandas as pd
import plotly.express as px
import os

# การตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Tree Compensation Explorer", layout="wide", page_icon="🌳")

# ฟังก์ชันจัดการไฟล์
DATA_PATH = 'data.csv'

def load_data():
    if os.path.exists(DATA_PATH):
        df = pd.read_csv(DATA_PATH)
        df['compensation_price'] = pd.to_numeric(df['compensation_price'], errors='coerce')
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
        return df
    return pd.DataFrame()

# เก็บข้อมูลไว้ใน Session เพื่อให้ระบบลื่นไหล
if 'df' not in st.session_state:
    st.session_state.df = load_data()

# --- SIDEBAR ---
st.sidebar.title("🌳 เมนูระบบฐานข้อมูล")
page = st.sidebar.radio("เลือกหน้า:", ["🔍 ระบบค้นหา & Dashboard", "➕ เพิ่มข้อมูลใหม่"])

# --- หน้า 1: ระบบค้นหา & Dashboard ---
if page == "🔍 ระบบค้นหา & Dashboard":
    st.title("📊 ระบบวิเคราะห์ราคาค่าทดแทนพืชผล")
    st.markdown("ข้อมูลย้อนหลังปี 2559 - 2568")

    # ตัวกรอง
    st.sidebar.markdown("---")
    search_q = st.sidebar.text_input("ค้นหาชื่อพืช/รหัสพืช", placeholder="เช่น ทุเรียน, สับปะรด...")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        years = sorted(st.session_state.df['year'].dropna().unique().astype(int))
        selected_years = st.multiselect("เลือกปี พ.ศ.", options=years, default=[2568])
    with col_f2:
        acc_types = st.multiselect("ประเภทบัญชี", options=['A', 'B'], default=['A', 'B'], 
                                  format_func=lambda x: "บัญชี A (ยืนต้น)" if x == 'A' else "บัญชี B (ล้มลุก)")

    # การกรองข้อมูล
    mask = st.session_state.df['year'].isin(selected_years) & st.session_state.df['account_type'].isin(acc_types)
    if search_q:
        mask &= (st.session_state.df['plant_name'].str.contains(search_q, na=False) | 
                 st.session_state.df['plant_id'].str.contains(search_q, na=False))
    
    df_filtered = st.session_state.df[mask]

    # สรุปตัวเลข (KPI)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("รายการที่พบ", len(df_filtered))
    m2.metric("ราคาสูงสุด", f"{df_filtered['compensation_price'].max():,.0f} ฿")
    m3.metric("ราคาเฉลี่ย", f"{df_filtered['compensation_price'].mean():,.0f} ฿")
    m4.metric("ราคามัธยฐาน", f"{df_filtered['compensation_price'].median():,.0f} ฿")

    st.markdown("---")

    # กราฟ
    g1, g2 = st.columns([6, 4])
    with g1:
        st.subheader("📈 แนวโน้มราคาค่าทดแทนเฉลี่ยรายปี")
        trend_df = st.session_state.df[st.session_state.df['account_type'].isin(acc_types)].groupby('year')['compensation_price'].mean().reset_index()
        fig_line = px.line(trend_df, x='year', y='compensation_price', markers=True, template="plotly_white")
        st.plotly_chart(fig_line, use_container_width=True)
    
    with g2:
        st.subheader("📊 การกระจายตัวของราคา (Box Plot)")
        fig_box = px.box(df_filtered, x='account_type', y='compensation_price', color='account_type')
        st.plotly_chart(fig_box, use_container_width=True)

    # ตาราง
    st.subheader("📑 รายละเอียดข้อมูล")
    st.dataframe(df_filtered, use_container_width=True, hide_index=True)

    # ปุ่มดาวน์โหลด
    csv = df_filtered.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 ดาวน์โหลดข้อมูลนี้เป็น CSV", data=csv, file_name='export_data.csv')

# --- หน้า 2: เพิ่มข้อมูลใหม่ ---
elif page == "➕ เพิ่มข้อมูลใหม่":
    st.title("➕ เพิ่มข้อมูลพืชและราคากลางใหม่")
    st.info("กรุณากรอกข้อมูลให้ครบถ้วนเพื่อบันทึกลงฐานข้อมูลหลัก")

    with st.form("add_data_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            p_id = st.text_input("รหัสพืช (เช่น PLTA0001)")
            p_name = st.text_input("ชื่อพืชผล")
            p_type = st.selectbox("ประเภทบัญชี", ["A", "B"])
            p_year = st.number_input("ปี พ.ศ.", value=2569)
        with c2:
            p_unit = st.text_input("หน่วย (เช่น ต้น, ไร่)")
            p_cond = st.selectbox("สภาพพืช", ["ไม่มีผล/ขนาดเล็ก", "มีผล/ขนาดใหญ่"])
            p_cat = st.text_input("หมวดหมู่ (ก-ฮ)")
            p_price = st.number_input("ราคาค่าทดแทน (บาท)", min_value=0.0)

        submitted = st.form_submit_button("💾 บันทึกข้อมูล")

        if submitted:
            if p_id and p_name:
                new_row = {
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
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_row])], ignore_index=True)
                st.session_state.df.to_csv(DATA_PATH, index=False, encoding='utf-8-sig')
                st.success("บันทึกข้อมูลสำเร็จ!")
                st.balloons()
            else:
                st.error("กรุณากรอกข้อมูลที่สำคัญให้ครบ")