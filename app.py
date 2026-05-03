import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. การตั้งค่าหน้าจอ
st.set_page_config(page_title="Tree Compensation System V2", layout="wide", page_icon="🌳")

DATA_PATH = 'data.csv'

# 2. ฟังก์ชันโหลดข้อมูลพร้อมจัดการเรื่อง Comma และ Space
@st.cache_data
def load_data():
    if os.path.exists(DATA_PATH):
        # โหลดข้อมูล
        df = pd.read_csv(DATA_PATH)
        
        # --- ล้างข้อมูล (Data Cleaning) ---
        # ลบช่องว่างส่วนเกินในชื่อคอลัมน์ (เช่น '  year' -> 'year')
        df.columns = df.columns.str.strip()
        
        # จัดการคอลัมน์ราคา (ลบ Comma และแปลงเป็นตัวเลข)
        if 'compensation_price' in df.columns:
            # ลบเครื่องหมายคอมม่าออก
            df['compensation_price'] = df['compensation_price'].astype(str).str.replace(',', '', regex=False)
            # แปลงเป็นตัวเลข (ถ้าเป็นค่าว่างหรือแปลงไม่ได้จะกลายเป็น NaN)
            df['compensation_price'] = pd.to_numeric(df['compensation_price'], errors='coerce')
        
        # จัดการคอลัมน์ปี
        if 'year' in df.columns:
            df['year'] = pd.to_numeric(df['year'], errors='coerce')
        
        # ลบช่องว่างในข้อมูลที่เป็นตัวอักษร (เผื่อมีช่องว่างในชื่อพืช)
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).str.strip()
            
        return df
    return pd.DataFrame()

# โหลดข้อมูลเข้า Session State
if 'df' not in st.session_state:
    st.session_state.df = load_data()

# --- SIDEBAR MENU ---
st.sidebar.title("📋 เมนูหลัก")
menu = st.sidebar.radio("เลือกหน้า:", ["📊 Dashboard & ค้นหา", "➕ เพิ่มข้อมูลใหม่"])

# --- หน้าที่ 1: Dashboard & ค้นหา ---
if menu == "📊 Dashboard & ค้นหา":
    st.title("🌳 ระบบฐานข้อมูลและวิเคราะห์ราคาค่าทดแทน")
    
    # ตัวกรองใน Sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 ตัวกรองข้อมูล")
    search_q = st.sidebar.text_input("ค้นหาชื่อพืช/รหัสพืช", placeholder="เช่น ทุเรียน...")
    
    # ดึงรายชื่อปีที่มีในข้อมูล
    available_years = sorted(st.session_state.df['year'].dropna().unique().astype(int))
    selected_years = st.sidebar.multiselect("เลือกปี พ.ศ.", options=available_years, default=[max(available_years)] if available_years else [])
    
    acc_types = st.sidebar.multiselect("ประเภทบัญชี", options=['A', 'B'], default=['A', 'B'], 
                                      format_func=lambda x: "A: ไม้ยืนต้น" if x == 'A' else "B: พืชล้มลุก")

    # กรองข้อมูลตามเงื่อนไข
    df_f = st.session_state.df.copy()
    mask = df_f['year'].isin(selected_years) & df_f['account_type'].isin(acc_types)
    if search_q:
        mask &= (df_f['plant_name'].str.contains(search_q, na=False) | 
                 df_f['plant_id'].str.contains(search_q, na=False))
    
    final_df = df_f[mask]

    # --- ส่วนการแสดงผล KPI ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("รายการที่พบ", f"{len(final_df)} รายการ")
    
    # ป้องกัน error กรณีไม่มีข้อมูลหลังกรอง
    max_p = final_df['compensation_price'].max() if not final_df.empty else 0
    avg_p = final_df['compensation_price'].mean() if not final_df.empty else 0
    sum_p = final_df['compensation_price'].sum() if not final_df.empty else 0
    
    c2.metric("ราคาสูงสุด", f"{max_p:,.0f} ฿")
    c3.metric("ราคาเฉลี่ย", f"{avg_p:,.0f} ฿")
    c4.metric("รวมราคาค่าทดแทน", f"{sum_p:,.0f} ฿")

    st.markdown("---")

    # ส่วนของกราฟ
    g1, g2 = st.columns([6, 4])
    with g1:
        st.subheader("📈 แนวโน้มราคาเฉลี่ยตามปี")
        trend_data = df_f[df_f['account_type'].isin(acc_types)].groupby('year')['compensation_price'].mean().reset_index()
        fig_line = px.line(trend_data, x='year', y='compensation_price', markers=True, template="plotly_white")
        st.plotly_chart(fig_line, use_container_width=True)
        
    with g2:
        st.subheader("📊 สัดส่วนตามสภาพพืช")
        if not final_df.empty:
            pie_data = final_df['plant_condition'].value_counts().reset_index()
            fig_pie = px.pie(pie_data, values='count', names='plant_condition', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.write("ไม่มีข้อมูลสำหรับแสดงกราฟวงกลม")

    # ตารางข้อมูล
    st.subheader("📑 รายละเอียดข้อมูล (ตาราง)")
    st.dataframe(final_df, use_container_width=True, hide_index=True)

# --- หน้าที่ 2: เพิ่มข้อมูลใหม่ ---
elif menu == "➕ เพิ่มข้อมูลใหม่":
    st.title("➕ เพิ่มข้อมูลพืชผลใหม่")
    st.warning("⚠️ ข้อมูลจะถูกบันทึกลงไฟล์ data.csv ทันที")

    with st.form("entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            p_id = st.text_input("รหัสพืช (เช่น PLTA0001)")
            p_name = st.text_input("ชื่อพืช")
            p_acc = st.selectbox("ประเภทบัญชี", ["A", "B"])
            p_year = st.number_input("ปี พ.ศ.", value=2568)
        with col2:
            p_cat = st.text_input("หมวดหมู่ (ก-ฮ)")
            p_unit = st.text_input("หน่วย", value="ต้น")
            p_cond = st.selectbox("สภาพพืช", ["ไม่มีผล/ขนาดเล็ก", "มีผล/ขนาดใหญ่"])
            p_price = st.number_input("ราคาค่าทดแทน (บาท)", min_value=0.0)

        submitted = st.form_submit_button("💾 บันทึกข้อมูล")

        if submitted:
            if p_id and p_name:
                new_row = {
                    'id': len(st.session_state.df) + 1,
                    'plant_id': p_id,
                    'account_type': p_acc,
                    'category': p_cat,
                    'is_active': 1,
                    'plant_name': p_name,
                    'unit': p_unit,
                    'plant_condition': p_cond,
                    'year': p_year,
                    'compensation_price': p_price
                }
                # อัปเดต Data
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_row])], ignore_index=True)
                st.session_state.df.to_csv(DATA_PATH, index=False, encoding='utf-8-sig')
                st.success("บันทึกข้อมูลเรียบร้อย!")
                st.balloons()
            else:
                st.error("กรุณากรอกข้อมูลสำคัญ (ID และ ชื่อ) ให้ครบถ้วน")