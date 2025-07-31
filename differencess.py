import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="تحليل النواقص", layout="wide")
st.title("تحليل النواقص في بيانات الموظفين")
st.markdown("### 📁 يرجى رفع ملفي البيانات للمقارنة:")

# رفع الملفين
col1, col2 = st.columns(2)
with col1:
    old_file = st.file_uploader("📂 ملف النظام القديم (ERP)", type=["xlsx"], key="old")
with col2:
    new_file = st.file_uploader("📂 ملف النظام الجديد (Cloud)", type=["xlsx"], key="new")

if old_file and new_file:
    # اختيار الشيت والصفوف
    old_sheets = pd.ExcelFile(old_file).sheet_names
    new_sheets = pd.ExcelFile(new_file).sheet_names

    col1, col2 = st.columns(2)
    with col1:
        old_sheet = st.selectbox("📄 اختر ورقة ERP", old_sheets, key="erp_sheet")
        old_skiprows = st.number_input("تخطي صفوف (ERP)", min_value=0, max_value=20, value=0)
    with col2:
        new_sheet = st.selectbox("📄 اختر ورقة Cloud", new_sheets, key="cloud_sheet")
        new_skiprows = st.number_input("تخطي صفوف (Cloud)", min_value=0, max_value=20, value=0)

    # قراءة البيانات
    df_old = pd.read_excel(old_file, sheet_name=old_sheet, skiprows=old_skiprows)
    df_new = pd.read_excel(new_file, sheet_name=new_sheet, skiprows=new_skiprows)

    df_old.columns = df_old.columns.str.strip()
    df_new.columns = df_new.columns.str.strip()

    # البحث عن عمود الرقم الوظيفي
    id_column_old = [col for col in df_old.columns if "الرقم" in col and "الوظيفي" in col]
    id_column_new = [col for col in df_new.columns if "الرقم" in col and "الوظيفي" in col]

    if not id_column_old or not id_column_new:
        st.error("⚠️ لم يتم العثور على عمود 'الرقم الوظيفي'.")
        st.write("أعمدة ERP:", df_old.columns.tolist())
        st.write("أعمدة Cloud:", df_new.columns.tolist())
    else:
        id_col_old = id_column_old[0]
        id_col_new = id_column_new[0]

        df_old = df_old.dropna(subset=[id_col_old])
        df_new = df_new.dropna(subset=[id_col_new])

        # استثناء الدوائر
        excluded_departments = ['HC.نادي عجمان للفروسية', 'PD.الشرطة المحلية لإمارة عجمان', 'RC.الديوان الأميري']
        if 'الدائرة' in df_old.columns:
            df_old = df_old[~df_old['الدائرة'].isin(excluded_departments)]
        if 'الدائرة' in df_new.columns:
            df_new = df_new[~df_new['الدائرة'].isin(excluded_departments)]

        # الدمج
        merged = pd.merge(df_old, df_new, left_on=id_col_old, right_on=id_col_new,
                          how="inner", suffixes=('_old', '_new'))

        # استخراج الفروقات
        differences = []
        for _, row in merged.iterrows():
            emp_id = row[id_col_old]
            dept = row['الدائرة_old'] if 'الدائرة_old' in row else 'غير معروف'
            for col in df_old.columns:
                if col == id_col_old:
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
                    elif pd.isna(val_old) and pd.isna(val_new):
                        continue
                    elif val_old != val_new:
                        differences.append((emp_id, dept, col, val_old, val_new))

        if differences:
            diff_df = pd.DataFrame(differences, columns=["الرقم الوظيفي", "الدائرة", "العمود", "القيمة القديمة", "القيمة الجديدة"])
            st.success(f"✅ تم العثور على {len(diff_df)} فرق في البيانات.")

            # 🔍 فلتر بحث
            emp_filter = st.text_input("🔍 ابحث برقم وظيفي أو جزء من الرقم")
            if emp_filter:
                diff_df = diff_df[diff_df["الرقم الوظيفي"].astype(str).str.contains(emp_filter.strip())]

            # 📊 رسم بياني لعدد التغييرات
            fig = px.bar(diff_df['العمود'].value_counts().reset_index(),
                         x='index', y='العمود',
                         labels={'index': 'العمود', 'العمود': 'عدد التغييرات'},
                         title="📊 عدد التغييرات لكل عمود")
            st.plotly_chart(fig, use_container_width=True)

            # 📑 تبويبات حسب الأعمدة المتغيرة
            changed_columns = diff_df['العمود'].unique().tolist()
            tabs = st.tabs(changed_columns)
            for i, col in enumerate(changed_columns):
                with tabs[i]:
                    st.subheader(f"🔸 التغييرات في العمود: {col}")
                    st.dataframe(diff_df[diff_df['العمود'] == col].reset_index(drop=True))

            # 🔽 تحميل النتائج
            csv = diff_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 تحميل التغييرات بصيغة Excel", data=csv, file_name="الفروقات.csv", mime='text/csv')
        else:
            st.info("✅ لا توجد اختلافات بين النظامين.")
