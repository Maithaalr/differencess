import streamlit as st
import pandas as pd

st.set_page_config(page_title="تحليل النواقص", layout="wide")
st.title("تحليل النواقص في بيانات الموظفين")

st.markdown("### يرجى رفع ملفي البيانات للمقارنة:")

col1, col2 = st.columns(2)
with col1:
    old_file = st.file_uploader("ارفع ملف النظام القديم (ERP)", type=["xlsx"], key="old")
with col2:
    new_file = st.file_uploader("ارفع ملف النظام الجديد (Cloud)", type=["xlsx"], key="new")

if old_file and new_file:
    df_old = pd.read_excel(old_file, sheet_name=0)
    df_new = pd.read_excel(new_file, sheet_name=0)

    # تنظيف الأعمدة
    df_old.columns = df_old.columns.str.strip()
    df_new.columns = df_new.columns.str.strip()

    # إزالة التكرار
    df_old = df_old.loc[:, ~df_old.columns.duplicated()]
    df_new = df_new.loc[:, ~df_new.columns.duplicated()]

    # استثناء الدوائر المحددة
    excluded_departments = ['HC.نادي عجمان للفروسية', 'PD.الشرطة المحلية لإمارة عجمان', 'RC.الديوان الأميري']
    if 'الدائرة' in df_old.columns:
        df_old = df_old[~df_old['الدائرة'].isin(excluded_departments)]
    if 'الدائرة' in df_new.columns:
        df_new = df_new[~df_new['الدائرة'].isin(excluded_departments)]

    # دمج حسب الرقم الوظيفي
    merged = pd.merge(df_old, df_new, on="الرقم الوظيفي", how="inner", suffixes=('_old', '_new'))

    differences = []

    for _, row in merged.iterrows():
        emp_id = row["الرقم الوظيفي"]
        dept = row['الدائرة_old'] if 'الدائرة_old' in row else 'غير معروف'

        for col in df_old.columns:
            if col == "الرقم الوظيفي":
                continue
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

        # إنشاء تبويبات لكل عمود متغير
        changed_columns = diff_df['العمود'].unique().tolist()
        tabs = st.tabs(changed_columns)
        for i, col in enumerate(changed_columns):
            with tabs[i]:
                st.subheader(f"التغييرات في العمود: {col}")
                st.dataframe(diff_df[diff_df['العمود'] == col].reset_index(drop=True))
    else:
        st.info("لا توجد اختلافات بين النظامين.")
