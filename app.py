import streamlit as st
import pandas as pd
import numpy as np
import re

# --------------------------------------------------------------------------
# 위에서 보여드린 '최종 계산 엔진 코드'가 여기에 그대로 들어갑니다.
# (이 코드는 숨겨져 있으며, app.py 파일 안에 함께 존재합니다)
def analyze_files(file_list, exclusion_list):
    therapist_name = "편현준"
    total_simplified_count = 0
    categorized_items = {}

    for file_obj in file_list:
        try:
            df_list = []
            if file_obj.name.endswith('.csv'):
                try:
                    df_list.append(pd.read_csv(file_obj, encoding='utf-8', header=None, low_memory=False))
                except UnicodeDecodeError:
                    df_list.append(pd.read_csv(file_obj, encoding='euc-kr', header=None, low_memory=False))
            else:
                xls = pd.ExcelFile(file_obj)
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
                            if not re.match(r'^\d+', treatment_str): continue
                            current_patient_id = treatment_str.split()[0]
                            if current_patient_id != previous_patient_id:
                                treatments_to_count.append(treatment_str)
                            previous_patient_id = current_patient_id

                        for treatment_str in treatments_to_count:
                            if treatment_str in exclusion_list: continue
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
                            elif "박종인" in treatment_str: final_category = "도수9"
                            elif "강대환" in treatment_str: final_category = "pain9"
                            elif "윤지운" in treatment_str and "도수8" in treatment_str and "단순검사" in treatment_str: final_category = "도수9"
                            elif "정성엽" in treatment_str and "도수8" in treatment_str and "단순검사" in treatment_str: final_category = "도수9"
                            elif "정성엽" in treatment_str and "도수7" in treatment_str and "평가" in treatment_str: final_category = "도수9"
                            elif "고아현" in treatment_str and "도수8" in treatment_str and "단순검사" in treatment_str: final_category = "도수9"
                            elif "변인혁" in treatment_str and "도수7" in treatment_str and "단순검사" in treatment_str: final_category = "도수8"
                            elif "주영민" in treatment_str and "평가" in treatment_str and "도수" not in treatment_str: final_category = "NDT"
                            elif "이준" in treatment_str and "평가" in treatment_str: final_category = "NDT"
                            elif "유세은" in treatment_str: final_category = "도수18"
                            elif "박한나" in treatment_str: final_category = "도수8"
                            elif "곽순욱" in treatment_str: final_category = "도수8"
                            elif "문장민" in treatment_str: final_category = "도수9"
                            elif "이덕헌" in treatment_str: final_category = "도수9"

                            if not final_category:
                                if "도수5" in treatment_str: final_category = "NDT"
                                else:
                                    patterns = {'도수': r'도수(\d+)', '신장': r'신장(\d+)', 'pain': r'pain(\d+)', '충격파': r'충(\d+)'}
                                    for base, pat in patterns.items():
                                        m = re.search(pat, treatment_str)
                                        if m: final_category = f"{base}{m.group(1)}"; break
                            
                            if not final_category:
                                if "NDT" in treatment_str: final_category = "NDT"

                            if final_category:
                                total_simplified_count += 1
                                categorized_items.setdefault(final_category, []).append(treatment_str)
        except Exception as e:
            st.error(f"{file_obj.name} 파일 처리 중 오류 발생: {e}")
            
    return total_simplified_count, categorized_items
# --------------------------------------------------------------------------


# --- 웹 앱 인터페이스 부분 ---

st.title(' 치료 건수 자동 계산 프로그램')

# 파일 업로드 (여러 파일 가능)
uploaded_files = st.file_uploader("분석할 스케줄 파일을 업로드하세요 (여러 개 선택 가능)",
                                  type=['csv', 'xlsx'], 
                                  accept_multiple_files=True)

# 제외 목록 (블랙리스트) 입력
st.header("제외 목록 (Blacklist)")
exclusion_text = st.text_area("여기에 실제로 시행하지 않은 치료 항목을 한 줄에 하나씩 정확하게 입력하세요.",
                              height=150,
                              placeholder="예시:\n1234 김철수 NDT\n5678 이영희 도수8")
exclusion_list = [line.strip() for line in exclusion_text.split('\n') if line.strip()]


# 분석 시작 버튼
if st.button('분석 시작'):
    if uploaded_files:
        with st.spinner('파일을 분석 중입니다...'):
            total_count, categorized_items = analyze_files(uploaded_files, exclusion_list)

            # --- 최종 결과 출력 형식 ---
            user_counts_format = {
                "도수5 (ndt)": [], "충격파8": [], "도수8": [], "도수9": [], 
                "pain9": [], "신장9": [], "신장14": [], "도수16": [], "도수18": []
            }

            if 'NDT' in categorized_items:
                user_counts_format["도수5 (ndt)"].extend(categorized_items.pop('NDT'))

            for category, items in categorized_items.items():
                user_counts_format.setdefault(category, []).extend(items)

            # --- 1단계: 요약 출력 ---
            st.header(f"총 치료 건수: {total_count}")
            st.subheader("--- 항목별 분류 (요약) ---")

            summary_data = []
            for category, items in user_counts_format.items():
                if items:
                    summary_data.append({'치료 항목': category, '건수': len(items)})
            
            if summary_data:
                summary_df = pd.DataFrame(summary_data).sort_values(by='건수', ascending=False).reset_index(drop=True)
                st.table(summary_df)

            # --- 2단계: 상세 내역 출력 ---
            st.subheader("--- 항목별 분류 (상세 내역) ---")
            
            sorted_summary = sorted(user_counts_format.items(), key=lambda item: len(item[1]), reverse=True)

            for category, items in sorted_summary:
                 if items:
                    with st.expander(f"▼ {category}: {len(items)} 건"):
                        # 상세 내역을 표 형태로 보여주기
                        detail_df = pd.DataFrame(items, columns=['치료 내용'])
                        st.table(detail_df)
    else:
        st.warning('분석할 파일을 먼저 업로드해주세요.')