import streamlit as st
import pandas as pd
import plotly.express as px
from db_utils import load_data, get_tech_stack_counts

# --- 페이지 설정 ---
st.set_page_config(
    page_title="포지션 및 직군 분석",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 포지션 및 직군 분석")
st.markdown("관심 있는 직무의 상세 스펙을 확인하거나, 데이터 직군과 비 데이터 직군의 특징을 비교 분석합니다.")

# --- 데이터 로딩 ---
@st.cache_data
def cached_load_data():
    return load_data()

df = cached_load_data()

if df.empty:
    st.error("데이터를 불러올 수 없습니다.")
    st.stop()

# --- 분석 선택 탭 ---
tab1, tab2 = st.tabs(["직군 전체 비교 분석", "포지션별 상세 분석"])

# =========================
# 1. 직군 전체 비교 분석 탭
# =========================
with tab1:
    st.header("📊 데이터 직군 vs 비 데이터 직군 비교")
    
    # 데이터 분리
    df_data_job = df[df['is_data_job'] == True]
    df_non_data_job = df[df['is_data_job'] == False]

    # 기본 통계 비교
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("데이터 직군 (Data Jobs)")
        if not df_data_job.empty:
            c1, c2 = st.columns(2)
            c1.metric("총 공고 수", f"{len(df_data_job):,}개")
            c2.metric("평균 요구 경력", f"{df_data_job['experience_min_years'].mean():.1f}년")
        else:
            st.warning("데이터 직군 공고가 없습니다.")
            
    with col2:
        st.subheader("비 데이터 직군 (Non-Data Jobs)")
        if not df_non_data_job.empty:
            c1, c2 = st.columns(2)
            c1.metric("총 공고 수", f"{len(df_non_data_job):,}개")
            c2.metric("평균 요구 경력", f"{df_non_data_job['experience_min_years'].mean():.1f}년")
        else:
            st.warning("비 데이터 직군 공고가 없습니다.")
            
    st.markdown("---")

    # 기술 스택 비교
    st.subheader("🛠️ 기술 스택 비교 Top 15")
    col1, col2 = st.columns(2)
    with col1:
        tech_counts_data = get_tech_stack_counts(df_data_job['tech_stack'])
        if tech_counts_data:
            top_tech = pd.DataFrame(tech_counts_data.most_common(15), columns=['Tech', 'Count'])
            fig = px.bar(top_tech.sort_values('Count'), x='Count', y='Tech', title="데이터 직군 요구 기술", orientation='h')
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        tech_counts_non_data = get_tech_stack_counts(df_non_data_job['tech_stack'])
        if tech_counts_non_data:
            top_tech = pd.DataFrame(tech_counts_non_data.most_common(15), columns=['Tech', 'Count'])
            fig = px.bar(top_tech.sort_values('Count'), x='Count', y='Tech', title="비 데이터 직군 요구 기술", orientation='h')
            st.plotly_chart(fig, use_container_width=True)

# =========================
# 2. 포지션별 상세 분석 탭
# =========================
with tab2:
    st.header("🧑‍💻 포지션별 상세 분석")
    # --- 포지션 선택 ---
    all_positions = sorted(df['position'].dropna().unique())
    selected_position = st.selectbox(
        '분석할 포지션을 선택하세요:',
        all_positions,
        index=all_positions.index('데이터 엔지니어') if '데이터 엔지니어' in all_positions else 0
    )

    # 선택된 포지션에 해당하는 데이터만 필터링
    df_selected = df[df['position'] == selected_position].copy()
    st.subheader(f"'{selected_position}' 직무 분석 결과")
    
    # --- 분석 결과 시각화 ---
    col1, col2 = st.columns([1, 1])

    with col1:
        # 요구 기술 스택 Top 15
        st.markdown("##### 🛠️ 요구 기술 스택")
        tech_counts = get_tech_stack_counts(df_selected['tech_stack'])
        if not tech_counts:
            st.warning("해당 포지션의 기술스택 데이터가 충분하지 않습니다.")
        else:
            top_tech = pd.DataFrame(tech_counts.most_common(15), columns=['Tech', 'Count'])
            fig_tech = px.bar(
                top_tech.sort_values('Count'),
                x='Count', y='Tech',
                orientation='h',
                title=f"'{selected_position}' 요구 기술 Top 15"
            )
            st.plotly_chart(fig_tech, use_container_width=True)

    with col2:
        # 요구 경력 분포
        st.markdown("##### 📈 요구 경력 분포")
        def categorize_experience(exp):
            if pd.isna(exp) or exp == 0: return '신입 (0년)'
            if 1 <= exp <= 3: return '주니어 (1~3년)'
            if 4 <= exp <= 6: return '미들 (4~6년)'
            if exp >= 7: return '시니어 (7년 이상)'
            return '무관'

        df_selected['experience_category'] = df_selected['experience_min_years'].apply(categorize_experience)
        exp_dist = df_selected['experience_category'].value_counts()
        
        fig_exp = px.pie(
            exp_dist, values=exp_dist.values, names=exp_dist.index,
            title=f"'{selected_position}' 요구 경력 분포", hole=0.3
        )
        st.plotly_chart(fig_exp, use_container_width=True)

    st.markdown("---")
    
    # 관련 공고 목록
    with st.expander(f"'{selected_position}' 관련 최신 공고 보기 ({len(df_selected)}개)"):
        st.dataframe(
            df_selected[['company_id', 'position', 'experience_min', 'tech_stack', 'url']].head(20)
        ) 