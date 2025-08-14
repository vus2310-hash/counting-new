import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="치료 데이터 분석기", layout="wide")
st.title("치료 데이터 분석기")

# ========== 사이드바 설정 ==========
with st.sidebar:
    st.markdown("### 설정")
    therapist_name = st.text_input("치료사 이름", value="편현준")
    st.caption("시트 상단 5행 내에서 정확히 일치하는 셀을 찾아 주변 열을 스캔합니다.")
    st.divider()
    st.markdown("**최종 제외 목록 (한 줄에 하나씩 입력)**")
    excl_text = st.text_area("", value="", height=120, placeholder="예) 9524 조인주 18")
    EXCLUSION_LIST = [line.strip() for line in excl_text.splitlines() if line.strip()]
    show_details = st.checkbox("상세 내역 표시", value=True)
    st.divider()
    st.markdown("**도움말**")
    st.markdown("- CSV/XLSX 업로드 시 자동 분석\n- 인코딩: UTF-8 → EUC-KR 순차 시도")

# ========== 파일 업로드 ==========
uploaded_files = st.file_uploader(
    "CSV 또는 XLSX 파일을 업로드하세요 (여러 개 가능).",
    type=["csv", "xlsx"],
    accept_multiple_files=True
)

# ========== 유틸 함수 ==========
def load_file(file):
    """업로드 파일을 DataFrame 리스트로 반환 (XLSX는 시트별로 분리)"""
    name = file.name.lower()
    if name.endswith(".csv"):
        try:
            df = pd.read_csv(file, encoding="utf-8", header=None, low_memory=False)
        except UnicodeDecodeError:
            file.seek(0)
            df = pd.read_csv(file, encoding="euc-kr", header=None, low_memory=False)
        return [df]
    else:
        xls = pd.ExcelFile(file)
        return [xls.parse(sheet_name, header=None) for sheet_name in xls.sheet_names]

def analyze_frames(df_list, therapist_name, exclusion):
    total_simplified_count = 0
    categorized_items = {}

    for df in df_list:
        try:
            therapist_col, therapist_row = None, None
            # 상단 5행에서 치료사 이름 탐색
            for r in range(min(5, df.shape[0])):
                for c in range(df.shape[1]):
                    if str(df.iloc[r, c]).strip() == therapist_name:
                        therapist_col, therapist_row = c, r
                        break
                if therapist_col is not None:
                    break

            if therapist_col is None:
                continue

            # 환자명/치료기록 열 후보
            patient_cols = []
            data_start_row = therapist_row + 1
            header_row = therapist_row + 1

            format_found = False
            if header_row < df.shape[0]:
                if therapist_col > 0 and "환자명" in str(df.iloc[header_row, therapist_col - 1]):
                    patient_cols.append(therapist_col - 1); format_found = True
                elif therapist_col + 1 < df.shape[1] and "환자명" in str(df.iloc[header_row, therapist_col + 1]):
                    patient_cols.append(therapist_col + 1); format_found = True

            if not format_found:
                if therapist_col > 0:
                    patient_cols.append(therapist_col - 1)
                if therapist_col + 1 < df.shape[1]:
                    patient_cols.append(therapist_col + 1)

            # 후보 열에서 22행 스캔
            all_treatments = pd.Series(dtype=object)
            for p_col in patient_cols:
                if 0 <= p_col < df.shape[1]:
                    col_data = df.iloc[data_start_row : data_start_row + 22, p_col].dropna()
                    all_treatments = pd.concat([all_treatments, col_data])

            if all_treatments.empty:
                continue

            treatments_to_count = []
            previous_patient_id = None
            for treatment in all_treatments:
                treatment_str = str(treatment).strip()

                # 숫자로 시작하거나 '(낮)'으로 시작하지 않으면 제외
                if not (re.match(r"^\d+", treatment_str) or treatment_str.startswith("(낮)")):
                    continue

                # 중복 제거: 첫 토큰(환자ID) 또는 '(낮)' 전체 문자열 기준
                current_patient_id = treatment_str.split()[0]
                if not current_patient_id.startswith("(낮)"):
                    if current_patient_id != previous_patient_id:
                        treatments_to_count.append(treatment_str)
                    previous_patient_id = current_patient_id
                else:
                    if treatment_str != previous_patient_id:
                        treatments_to_count.append(treatment_str)
                    previous_patient_id = treatment_str

            # 규칙 기반 카테고리 부여
            for treatment_str in treatments_to_count:
                if treatment_str in exclusion:
                    continue
                if "점심" in treatment_str:
                    continue
                if "FES" in treatment_str and not any(
                    kw in treatment_str for kw in ["도수", "NDT", "평가", "pain", "신장", "충"]
                ):
                    continue
                if "박한나" in treatment_str and "스쿼트" in treatment_str:
                    continue
                if "MAT" in treatment_str:
                    continue
                if "박종인" in treatment_str and len(re.sub(r"^\d+\s*", "", treatment_str).strip()) == 3:
                    continue

                final_category = None

                # 개별 매핑 규칙
                if "박형희" in treatment_str and "도수8" in treatment_str and "단순검사" in treatment_str:
                    final_category = "도수9"
                elif "윤지운" in treatment_str and "도수5" in treatment_str and "평가" in treatment_str:
                    final_category = "도수9"
                elif "변인혁" in treatment_str and "도수5" in treatment_str and "평가" in treatment_str:
                    final_category = "도수8"
                elif "박한나" in treatment_str and "도수5" in treatment_str and "평가" in treatment_str:
                    final_category = "도수8"
                elif "이성범" in treatment_str and "도수5" in treatment_str and "평가" in treatment_str:
                    final_category = "도수9"
                elif "박종인" in treatment_str:
                    final_category = "도수9"
                elif "강대환" in treatment_str:
                    final_category = "pain9"
                elif "윤지운" in treatment_str and "도수8" in treatment_str and "단순검사" in treatment_str:
                    final_category = "도수9"
                elif "정성엽" in treatment_str and "도수8" in treatment_str and "단순검사" in treatment_str:
                    final_category = "도수9"
                elif "정성엽" in treatment_str and "도수7" in treatment_str and "평가" in treatment_str:
                    final_category = "도수9"
                elif "고아현" in treatment_str and "도수8" in treatment_str and "단순검사" in treatment_str:
                    final_category = "도수9"
                elif "변인혁" in treatment_str and "도수7" in treatment_str and "단순검사" in treatment_str:
                    final_category = "도수8"
                elif "주영민" in treatment_str and "평가" in treatment_str and "도수" not in treatment_str:
                    final_category = "NDT"
                elif "이준" in treatment_str and "평가" in treatment_str:
                    final_category = "NDT"
                elif "박한나" in treatment_str:
                    final_category = "도수8"
                elif "곽순욱" in treatment_str:
                    final_category = "도수8"
                elif "문장민" in treatment_str:
                    final_category = "도수9"
                elif "이덕헌" in treatment_str:
                    final_category = "도수9"

                # 패턴/기본 규칙
                if not final_category:
                    if re.search(r"\s18$", treatment_str):
                        final_category = "도수18"
                    elif "도수5" in treatment_str:
                        final_category = "NDT"
                    else:
                        patterns = {
                            "도수": r"도수(\d+)",
                            "신장": r"신장(\d+)",
                            "pain": r"pain(\d+)",
                            "충격파": r"충(\d+)",
                        }
                        for base, pat in patterns.items():
                            m = re.search(pat, treatment_str)
                            if m:
                                final_category = f"{base}{m.group(1)}"
                                break

                if not final_category and "NDT" in treatment_str:
                    final_category = "NDT"

                if final_category:
                    total_simplified_count += 1
                    categorized_items.setdefault(final_category, []).append(treatment_str)

        except Exception as e:
            st.error(f"시트 처리 중 오류: {e}")

    return total_simplified_count, categorized_items

# ========== 실행 ==========
if not uploaded_files:
    st.info("왼쪽(또는 위)의 업로드 영역에 CSV/XLSX 파일을 추가하세요.")
else:
    total_simplified_count = 0
    categorized_items_all = {}

    for uf in uploaded_files:
        try:
            df_list = load_file(uf)
        except Exception as e:
            st.error(f"{uf.name} 로딩 오류: {e}")
            continue

        t_count, cat_items = analyze_frames(df_list, therapist_name, EXCLUSION_LIST)
        total_simplified_count += t_count
        for k, v in cat_items.items():
            categorized_items_all.setdefault(k, []).extend(v)

    # 결과 포맷팅
    user_counts_format = {
        "도수5 (ndt)": [],
        "충격파8": [],
        "도수8": [],
        "도수9": [],
        "pain9": [],
        "신장9": [],
        "신장14": [],
        "도수16": [],
        "도수18": [],
    }

    if "NDT" in categorized_items_all:
        user_counts_format["도수5 (ndt)"].extend(categorized_items_all.pop("NDT"))

    for category, items in categorized_items_all.items():
        if category in user_counts_format:
            user_counts_format[category].extend(items)
        else:
            user_counts_format.setdefault(category, []).extend(items)

    display_order = ["도수5 (ndt)", "충격파8", "도수8", "도수9", "pain9", "신장9", "신장14", "도수16", "도수18"]
    sorted_summary = []
    remaining_summary = user_counts_format.copy()
    for category in display_order:
        if category in remaining_summary:
            sorted_summary.append((category, remaining_summary.pop(category)))
    sorted_summary.extend(sorted(remaining_summary.items()))

    # 요약 표
    summary_rows = [{"카테고리": cat, "건수": len(items) if items else 0} for cat, items in sorted_summary]
    summary_df = pd.DataFrame(summary_rows)

    st.success(f"총 치료 건수: **{total_simplified_count}** 건")
    st.markdown("### 항목별 분류 (요약)")
    st.dataframe(summary_df, use_container_width=True)

    # 다운로드: 요약 CSV
    csv_summary = summary_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("요약 CSV 다운로드", data=csv_summary, file_name="summary_counts.csv", mime="text/csv")

    if show_details:
        st.markdown("### 항목별 분류 (상세 내역)")
        detail_records = []
        for category, items in sorted_summary:
            if items:
                st.markdown(f"**{category}: {len(items)} 건**")
                st.text("\n".join(sorted(items)))
                for item in items:
                    detail_records.append({"카테고리": category, "항목": item})

        if detail_records:
            st.markdown("#### 상세 내역 표")
            detail_df = pd.DataFrame(detail_records)
            st.dataframe(detail_df, use_container_width=True)
            csv_details = detail_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("상세 내역 CSV 다운로드", data=csv_details, file_name="details_items.csv", mime="text/csv")

st.markdown("---")
st.caption("ⓘ 출력이 비어 있으면 치료사 이름이 정확히 일치하는지, 업로드한 시트 상단(첫 5행)에 존재하는지 확인하세요.")
