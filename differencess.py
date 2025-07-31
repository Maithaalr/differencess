import streamlit as st
import pandas as pd

st.set_page_config(page_title="تحليل النواقص", layout="wide")
st.title("تحليل النواقص في بيانات الموظفين")

st.markdown("<div class='section-header'>يرجى تحميل ملف الموظفين (يحتوي على ورقتين: ERP و Cloud)</div>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("ارفع الملف (Excel)", type=["xlsx"])

if uploaded_file:
    # قراءة كل الشيتات
    all_sheets = pd.read_excel(uploaded_file, sheet_name=None)
    sheet_names = list(all_sheets.keys())

    col1, col2 = st.columns(2)
    with col1:
        old_sheet = st.selectbox("اختر ورقة النظام القديم (ERP)", sheet_names)
    with col2:
        new_sheet = st.selectbox("اختر ورقة النظام الجديد (Cloud)", sheet_names)

    df_old = all_sheets[old_sheet]
    df_new = all_sheets[new_sheet]

    # تنظيف الأعمدة
    df_old.columns = df_old.columns.str.strip()
    df_new.columns = df_new.columns.str.strip()

    # إزالة التكرار بالأعمدة
    df_old = df_old.loc[:, ~df_old.columns.duplicated()]
    df_new = df_new.loc[:, ~df_new.columns.duplicated()]

    # استثناء الدوائر
    excluded_departments = ['HC.نادي عجمان للفروسية', 'PD.الشرطة المحلية لإمارة عجمان', 'RC.الديوان الأميري']
    if 'الدائرة' in df_old.columns:
        df_old = df_old[~df_old['الدائرة'].isin(excluded_departments)]
    if 'الدائرة' in df_new.columns:
        df_new = df_new[~df_new['الدائرة'].isin(excluded_departments)]

    # الدمج حسب الرقم الوظيفي
    merged = pd.merge(df_old, df_new, on="الرقم الوظيفي", how="inner", suffixes=('_old', '_new'))

    differences = []

    for _, row in merged.iterrows():
        emp_id = row['الرقم الوظيفي']
        dept = row['الدائرة_old'] if 'الدائرة_old' in row else 'غير معروف'

        for col in df_old.columns:
            col_old = f"{col}_old"
            col_new = f"{col}_new"
            if col_old in merged.columns and col_new in merged.columns:
                val_old = row[col_old]
                val_new = row[col_new]
                if pd.isna(val_old) and pd.notna(val_new):
                    differences.append((emp_id, dept, col, 'NULL', val_new))
                elif pd.notna(val_old) and pd.isna(val_new):
                    differences.append((emp_id, dept, col, val_old, 'NULL'))
                elif val_old != val_new:
                    differences.append((emp_id, dept, col, val_old, val_new))

    if differences:
        diff_df = pd.DataFrame(differences, columns=["الرقم الوظيفي", "الدائرة", "العمود", "القيمة القديمة", "القيمة الجديدة"])
        st.success(f"تم العثور على {len(diff_df)} فرق.")
        st.dataframe(diff_df)
    else:
        st.info("لا توجد اختلافات بين النظامين.")

