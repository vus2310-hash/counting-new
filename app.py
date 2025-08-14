import streamlit as st
import pandas as pd
import numpy as np
import re
import glob

# ----- 최종 제외 목록 (직접 수정 가능) -----
EXCLUSION_LIST = [
    # 예: "9524 조인주 18",
]
# -----------------------------------------------------------

file_names = glob.glob("*.csv") + glob.glob("*.xlsx")

therapist_name = "편현준"
total_simplified_count = 0
categorized_items = {}

for file in file_names:
    try:
        df_list = []
        if file.endswith('.csv'):
            try:
                df_list.append(pd.read_csv(file, encoding='utf-8', header=None, low_memory=False))
            except UnicodeDecodeError:
                df_list.append(pd.read_csv(file, encoding='euc-kr', header=None, low_memory=False))
        else:
            xls = pd.ExcelFile(file)
            for sheet_name in xls.sheet_names:
                df_list.append(xls.parse(sheet_name, header=None))

        for df in df_list:
            therapist_col, therapist_row = None, None
            for r in range(min(5, df.shape[0])):
                for c in range(df.shape[1]):
                    if str(df.iloc[r, c]).strip() == therapist_name:
                        therapist_col, therapist_row = c, r
                        break
                if therapist_col is not None: break
            
            if therapist_col is not None:
                patient_cols = []
                data_start_row = therapist_row + 1
                header_row = therapist_row + 1

                format_found = False
                if header_row < df.shape[0]:
                    if therapist_col > 0 and '환자명' in str(df.iloc[header_row, therapist_col - 1]):
                        patient_cols.append(therapist_col - 1); format_found = True
                    elif therapist_col + 1 < df.shape[1] and '환자명' in str(df.iloc[header_row, therapist_col + 1]):
                        patient_cols.append(therapist_col + 1); format_found = True
                
                if not format_found:
                    if therapist_col > 0: patient_cols.append(therapist_col - 1)
                    if therapist_col + 1 < df.shape[1]: patient_cols.append(therapist_col + 1)
                
                all_treatments = pd.Series(dtype=object)
                for p_col in patient_cols:
                    if p_col < df.shape[1] and p_col >= 0:
                        col_data = df.iloc[data_start_row : data_start_row + 22, p_col].dropna()
                        all_treatments = pd.concat([all_treatments, col_data])

                if not all_treatments.empty:
                    treatments_to_count = []
                    previous_patient_id = None
                    for treatment in all_treatments:
                        treatment_str = str(treatment).strip()
                        
                        if not (re.match(r'^\d+', treatment_str) or treatment_str.startswith('(낮)')):
                            continue

                        current_patient_id = treatment_str.split()[0]
                        if not current_patient_id.startswith('(낮)'):
                           if current_patient_id != previous_patient_id:
                               treatments_to_count.append(treatment_str)
                           previous_patient_id = current_patient_id
                        else:
                           if treatment_str != previous_patient_id:
                               treatments_to_count.append(treatment_str)
                           previous_patient_id = treatment_str
                           
                    for treatment_str in treatments_to_count:
                        if treatment_str in EXCLUSION_LIST: continue
                        if "점심" in treatment_str: continue
                        if "FES" in treatment_str and not any(kw in treatment_str for kw in ["도수", "NDT", "평가", "pain", "신장", "충"]): continue
                        if "박한나" in treatment_str and "스쿼트" in treatment_str: continue
                        if "MAT" in treatment_str: continue
                        if "박종인" in treatment_str and len(re.sub(r'^\d+\s*', '', treatment_str).strip()) == 3: continue

                        final_category = None
                        
                        if "박형희" in treatment_str and "도수8" in treatment_str and "단순검사" in treatment_str: final_category = "도수9"
                        elif "윤지운" in treatment_str and "도수5" in treatment_str and "평가" in treatment_str: final_category = "도수9"
                        elif "변인혁" in treatment_str and "도수5" in treatment_str and "평가" in treatment_str: final_category = "도수8"
                        elif "박한나" in treatment_str and "도수5" in treatment_str and "평가" in treatment_str: final_category = "도수8"
                        elif "이성범" in treatment_str and "도수5" in treatment_str and "평가" in treatment_str: final_category = "도수9"
