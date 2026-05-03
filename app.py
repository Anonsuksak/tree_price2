import streamlit as st
import pandas as pd
import plotly.express as px
import os

# การตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Tree Compensation System", layout="wide", page_icon="🌳")

# ฟังก์ชันจัดการข้อมูล
DATA_PATH = 'data.csv'

def load_data():
    if os.path.exists(DATA_PATH):
        df = pd.read_csv(DATA_PATH)
        # ตรวจสอบและทำความสะอาดข้อมูลเบื้องต้น
        df['compensation_price'] = pd.to_numeric(df['compensation_price'], errors='coerce')
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
        return df
    return pd.DataFrame()

# โหลดข้อมูลเข้า Session State เพื่อให้ App ทำงานแบบ Dynamic
if 'df' not in st.session_state:
    st.session_state.df = load_data()

# --- SIDEBAR MENU ---
st.sidebar.title("📋 เมนูระบบ")
menu = st.sidebar.radio("เลือกการทำงาน:", ["📊 Dashboard & Search", "➕ เพิ่มข้อมูลใหม่"])

# --- หน้าที่ 1: ค้นหาและ DASHBOARD ---
if menu == "📊 Dashboard & Search":
    st.title("🌳 ระบบวิเคราะห์ราคาค่าทดแทนพืชผล (2559-2568)")
    
    # ตัวกรองใน Sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 ตัวกรองข้อมูล")
    
    search_q = st.sidebar.text_input("ค้นหาชื่อพืช/รหัสพืช", placeholder="เช่น ทุเรียน, PLTA...")
    
    # กรองตามปี
    all_years = sorted(st.session_state.df['year'].dropna().unique().astype(int))
    selected_years = st.sidebar.multiselect("เลือกปี พ.ศ.", options=all_years, default=[2568])
    
    # กรองตามประเภทบัญชี
    acc_types = st.sidebar.multiselect("ประเภทบัญชี", options=['A', 'B'], default=['A', 'B'], 
                                      format_func=lambda x: "A: ไม้ยืนต้น" if x == 'A' else "B: พืชล้มลุก")

    # ประมวลผลการกรอง
    df_filter = st.session_state.df.copy()
    mask = df_filter['year'].isin(selected_years) & df_filter['account_type'].isin(acc_types)
    
    if search_q:
        mask &= (df_filter['plant_name'].str.contains(search_q, na=False) | 
                 df_filter['plant_id'].str.contains(search_q, na=False))
    
    final_df = df_filter[mask]

    # --- ส่วนการแสดงผล Dashboard ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("จำนวนรายการ", f"{len(final_df)} รายการ")
    col2.metric("ราคาสูงสุด", f"{final_df['compensation_price'].max():,.0f} ฿")
    col3.metric("ราคาเฉลี่ย", f"{final_df['compensation_price'].mean():,.0f} ฿")
    col4.metric("งบประมาณรวม", f"{final_df['compensation_price'].sum():,.0f} ฿")

    st.markdown("---")
    
    # กราฟ
    g1, g2 = st.columns([6, 4])
    with g1:
        st.subheader("📈 แนวโน้มราคาค่าทดแทนเฉลี่ยรายปี")
        line_data = df_filter[df_filter['account_type'].isin(acc_types)].groupby('year')['compensation_price'].mean().reset_index()
        fig_line = px.line(line_data, x='year', y='compensation_price', markers=True, template="plotly_white")
        st.plotly_chart(fig_line, use_container_width=True)
        
    with g2:
        st.subheader("📊 สัดส่วนตามสภาพพืช")
        pie_data = final_df['plant_condition'].value_counts().reset_index()
        fig_pie = px.pie(pie_data, values='count', names='plant_condition', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

    # ตารางข้อมูลหลัก
    st.subheader("📑 ตารางรายละเอียดข้อมูล")
    st.dataframe(final_df[['plant_id', 'plant_name', 'plant_condition', 'unit', 'year', 'compensation_price']], 
                 use_container_width=True, hide_index=True)
    
    # ปุ่มดาวน์โหลด
    csv_data = final_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 Download Filtered Data (CSV)", data=csv_data, file_name='compensation_export.csv')

# --- หน้าที่ 2: เพิ่มข้อมูลใหม่ (ADD DATA) ---
elif menu == "➕ เพิ่มข้อมูลใหม่":
    st.title("➕ เพิ่มข้อมูลพืชผลและราคาใหม่")
    st.warning("⚠️ ข้อมูลที่เพิ่มจะถูกบันทึกลงในฐานข้อมูลหลัก (data.csv) ทันที")

    with st.form("entry_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            new_id = st.text_input("รหัสพืช (Plant ID)*", placeholder="เช่น PLTA1234")
            new_name = st.text_input("ชื่อรายการพืช*")
            new_acc = st.selectbox("ประเภทบัญชี", ["A", "B"])
            new_year = st.number_input("ปี พ.ศ.", value=2569)
        
        with c2:
            new_cat = st.text_input("หมวดหมู่ (ก-ฮ)")
            new_unit = st.text_input("หน่วย", value="ต้น")
            new_cond = st.selectbox("สภาพพืช", ["ไม่มีผล/ขนาดเล็ก", "มีผล/ขนาดใหญ่"])
            new_price = st.number_input("ราคาค่าทดแทน (บาท)", min_value=0.0, step=10.0)
            
        submitted = st.form_submit_button("💾 บันทึกข้อมูลลงฐานข้อมูล")

        if submitted:
            if new_id and new_name:
                # สร้างข้อมูลแถวใหม่
                new_row = {
                    'id': len(st.session_state.df) + 1,
                    'plant_id': new_id,
                    'account_type': new_acc,
                    'category': new_cat,
                    'is_active': 1,
                    'plant_name': new_name,
                    'unit': new_unit,
                    'plant_condition': new_cond,
                    'year': new_year,
                    'compensation_price': new_price
                }
                
                # อัปเดต Data
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_row])], ignore_index=True)
                # บันทึกลงไฟล์จริง
                st.session_state.df.to_csv(DATA_PATH, index=False, encoding='utf-8-sig')
                
                st.success(f"บันทึกข้อมูล '{new_name}' (ปี {new_year}) สำเร็จแล้ว!")
                st.balloons()
            else:
                st.error("กรุณากรอกรหัสพืชและชื่อพืชให้ครบถ้วน")