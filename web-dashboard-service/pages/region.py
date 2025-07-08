import streamlit as st
import pandas as pd
import plotly.express as px
from db_utils import load_data, get_tech_stack_counts
from wordcloud import WordCloud
import matplotlib.pyplot as plt

st.set_page_config(page_title="지역별 채용 분석", page_icon="🗺️", layout="wide")

st.title("🗺️ 지역별 채용 분석")
st.markdown("주요 업무 지역별 채용 공고의 특징을 분석합니다.")

# --- 데이터 로딩 ---
@st.cache_data
def cached_load_data():
    return load_data()

df = cached_load_data()

if df.empty:
    st.error("데이터를 불러올 수 없습니다.")
    st.stop()

# --- 1. 지역 선택 ---
st.header("지역을 선택하여 분석 시작하기")
all_districts = df['location_district'].dropna().unique()
# 공고가 많은 순으로 정렬
sorted_districts = sorted(all_districts, key=lambda x: df[df['location_district'] == x].shape[0], reverse=True)

selected_district = st.selectbox(
    "분석할 지역(구)을 선택하세요.",
    options=sorted_districts
)

if selected_district:
    df_district = df[df['location_district'] == selected_district]
    
    st.header(f"📍 '{selected_district}' 분석 결과")
    
    # 기본 통계
    col1, col2, col3 = st.columns(3)
    col1.metric("총 공고 수", f"{len(df_district):,}개")
    col2.metric("고유 기업 수", f"{df_district['company_id'].nunique():,}개")
    col3.metric("데이터 직군 비율", f"{df_district['is_data_job'].mean():.1%}")
    
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # 기술스택 워드클라우드
        st.subheader("🛠️ 주요 기술스택")
        tech_counts = get_tech_stack_counts(df_district['tech_stack'])
        
        if tech_counts:
            try:
                wordcloud = WordCloud(
                    width=400, height=300, background_color='white',
                    colormap='viridis', max_words=30,
                    font_path='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'  # Docker 환경용 폰트
                ).generate_from_frequencies(tech_counts)
                
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.imshow(wordcloud, interpolation='bilinear')
                ax.axis('off')
                st.pyplot(fig, use_container_width=True)
                plt.close()
            except Exception as e:
                st.error(f"워드클라우드 생성 중 오류: {e}")
                st.info("폰트 파일을 찾을 수 없어 워드클라우드를 생성할 수 없습니다.")
        else:
            st.warning("기술스택 데이터가 없습니다.")

    with col2:
        # 주요 채용 포지션
        st.subheader("🚀 주요 채용 포지션 Top 10")
        top_positions = pd.DataFrame(df_district['position'].value_counts().nlargest(10))
        top_positions.columns = ['공고 수']
        st.dataframe(top_positions, use_container_width=True)
        
    st.markdown("---")
    
    # 해당 지역의 공고 리스트
    with st.expander(f"'{selected_district}' 전체 공고 보기 ({len(df_district)}개)"):
        st.dataframe(df_district[['position', 'company_id', 'tech_stack', 'experience_min_years', 'education']].reset_index(drop=True))

else:
    st.warning("분석할 지역을 선택해주세요.") 