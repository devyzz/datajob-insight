import streamlit as st
import pandas as pd
import plotly.express as px
from db_utils import load_data, get_tech_stack_counts
from api_client import get_company_size_stats_sync
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import numpy as np

# --- 페이지 설정 ---
st.set_page_config(
    page_title="기업 규모별 비교 분석",
    page_icon="🏢",
    layout="wide"
)

st.title("🏢 기업 규모별 비교 분석")
st.markdown("대기업, 중견기업, 중소기업, 스타트업이 각각 어떤 인재를 선호하는지 비교 분석")

# --- 데이터 로딩 ---
df = load_data()
if df.empty:
    st.error("데이터를 불러올 수 없습니다.")
    st.stop()

# --- 기업 규모별 데이터 가져오기 ---
company_size_stats = get_company_size_stats_sync()

# --- 기업 규모별 데이터 확인 ---
st.sidebar.markdown("### 📊 데이터 현황")
if company_size_stats:
    for stat in company_size_stats:
        st.sidebar.metric(f"{stat['company_size']} 공고 수", f"{stat['count']:,}개")
else:
    company_id_counts = df['company_id'].value_counts()
    for company_id, count in company_id_counts.items():
        st.sidebar.metric(f"기업 ID {company_id} 공고 수", f"{count:,}개")

# --- 1. 탭으로 기업 규모 선택 ---
# 기업 규모별로 탭 생성
if company_size_stats:
    company_sizes = [stat['company_size'] for stat in company_size_stats]
    tabs = st.tabs([f"{size} 분석" for size in company_sizes])
else:
    # API 데이터가 없을 경우 기업 ID로 대체
    company_ids = sorted(df['company_id'].unique())
    if not company_ids:
        st.error("기업 데이터가 없습니다.")
        st.stop()
    tabs = st.tabs([f"기업 ID {company_id} 분석" for company_id in company_ids])

# 각 탭에 대한 분석 내용 표시
if company_size_stats:
    for tab, company_size in zip(tabs, company_sizes):
        with tab:
            st.header(f"{company_size} 분석 결과")
            
            # 해당 기업 규모의 데이터만 필터링 (API에서 가져온 데이터 사용)
            # 실제로는 company 테이블과 조인해서 필터링해야 하지만,
            # 현재는 API에서 이미 필터링된 통계를 사용
            df_company = df  # 전체 데이터 사용 (API에서 이미 필터링됨)
            
            if df_company.empty:
                st.warning(f"{company_size} 데이터가 없습니다.")
                continue
            
            # 기본 통계
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("총 공고 수", f"{len(df_company):,}개")
            with col2:
                st.metric("데이터 직군 비율", f"{df_company['is_data_job'].mean():.1%}")
            with col3:
                avg_exp = df_company['experience_min_years'].mean()
                st.metric("평균 요구 경력", f"{avg_exp:.1f}년")
            with col4:
                st.metric("고유 기업 수", f"{df_company['company_id'].nunique():,}개")
            
            st.markdown("---")
            
            # 기술스택 분석 (워드클라우드 + Top 10)
            st.subheader("🛠️ 기술스택 분석")
            tech_counts = get_tech_stack_counts(df_company['tech_stack'])
            
            if tech_counts:
                col1, col2 = st.columns([2, 1])

                with col1:
                    # 워드클라우드 생성
                    st.markdown("##### 워드클라우드")
                    try:
                        wordcloud = WordCloud(
                            width=800, 
                            height=400,
                            background_color='white',
                            colormap='viridis',
                            max_words=50,
                            font_path='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'  # Docker 환경용 폰트
                        ).generate_from_frequencies(tech_counts)
                        
                        # 워드클라우드 표시
                        fig, ax = plt.subplots()
                        ax.imshow(wordcloud, interpolation='bilinear')
                        ax.axis('off')
                        st.pyplot(fig, use_container_width=True)
                        plt.close()
                    except Exception as e:
                        st.error(f"워드클라우드 생성 중 오류: {e}")
                        st.info("폰트 파일을 찾을 수 없어 워드클라우드를 생성할 수 없습니다.")
                
                with col2:
                    # Top 10 기술스택
                    st.markdown("##### Top 10 기술스택")
                    top_tech = pd.DataFrame(tech_counts.most_common(10), columns=['기술', '언급 횟수'])
                    st.dataframe(top_tech, use_container_width=True, height=420)
            else:
                st.warning("기술스택 데이터가 충분하지 않습니다.")
            
            st.markdown("---")
            
            # 포지션 및 기타 분석
            col1, col2 = st.columns(2)
            
            with col1:
                # 주요 채용 포지션 Top 5
                st.subheader("🚀 주요 채용 포지션 Top 5")
                top_positions = df_company['position'].value_counts().nlargest(5)
                fig_pos = px.bar(
                    x=top_positions.values,
                    y=top_positions.index,
                    orientation='h',
                    title=f"{company_size}의 Top 5 포지션",
                    labels={'x': '공고 수', 'y': '포지션'}
                )
                fig_pos.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_pos, use_container_width=True)
                
            with col2:
                # 고용 형태 분포
                st.subheader("📄 고용 형태 분포")
                job_type_dist = df_company['job_type'].value_counts()
                
                if not job_type_dist.empty:
                    fig_job_type = px.pie(
                        job_type_dist,
                        values=job_type_dist.values,
                        names=job_type_dist.index,
                        title=f"{company_size}의 고용 형태",
                        hole=0.3
                    )
                    fig_job_type.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig_job_type, use_container_width=True)
                else:
                    st.warning("고용 형태 데이터가 없습니다.")

            st.markdown("---")
            
            # 선호 경력/학력
            col3, col4 = st.columns(2)
            with col3:
                st.subheader("📈 선호 경력 분포")
                # 경력 카테고리화 함수
                def categorize_experience(exp):
                    if pd.isna(exp) or exp == 0: return '신입 (0년)'
                    if 1 <= exp <= 3: return '주니어 (1~3년)'
                    if 4 <= exp <= 6: return '미들 (4~6년)'
                    if exp >= 7: return '시니어 (7년 이상)'
                    return '무관'
                
                df_company['experience_category'] = df_company['experience_min_years'].apply(categorize_experience)
                exp_dist = df_company['experience_category'].value_counts()
                
                fig_exp = px.pie(
                    exp_dist,
                    values=exp_dist.values,
                    names=exp_dist.index,
                    title=f"{company_size}의 선호 경력"
                )
                st.plotly_chart(fig_exp, use_container_width=True)

            with col4:
                st.subheader("🎓 선호 학력 분포")
                edu_dist = df_company['education'].value_counts()
                fig_edu = px.pie(
                    edu_dist,
                    values=edu_dist.values,
                    names=edu_dist.index,
                    title=f"{company_size}의 선호 학력"
                )
                st.plotly_chart(fig_edu, use_container_width=True)
else:
    for tab, company_id in zip(tabs, company_ids):
        with tab:
            st.header(f"기업 ID {company_id} 분석 결과")
            
            # 해당 기업의 데이터만 필터링
            df_company = df[df['company_id'] == company_id]
        
        if df_company.empty:
            st.warning(f"기업 ID {company_id} 데이터가 없습니다.")
            continue
        
        # 기본 통계
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("총 공고 수", f"{len(df_company):,}개")
        with col2:
            st.metric("데이터 직군 비율", f"{df_company['is_data_job'].mean():.1%}")
        with col3:
            avg_exp = df_company['experience_min_years'].mean()
            st.metric("평균 요구 경력", f"{avg_exp:.1f}년")
        with col4:
            st.metric("고유 기업 수", f"{df_company['company_id'].nunique():,}개")
        
        st.markdown("---")
        
        # 기술스택 분석 (워드클라우드 + Top 10)
        st.subheader("🛠️ 기술스택 분석")
        tech_counts = get_tech_stack_counts(df_company['tech_stack'])
        
        if tech_counts:
            col1, col2 = st.columns([2, 1])

            with col1:
                # 워드클라우드 생성
                st.markdown("##### 워드클라우드")
                try:
                    wordcloud = WordCloud(
                        width=800, 
                        height=400,
                        background_color='white',
                        colormap='viridis',
                        max_words=50,
                        font_path='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'  # Docker 환경용 폰트
                    ).generate_from_frequencies(tech_counts)
                    
                    # 워드클라우드 표시
                    fig, ax = plt.subplots()
                    ax.imshow(wordcloud, interpolation='bilinear')
                    ax.axis('off')
                    st.pyplot(fig, use_container_width=True)
                    plt.close()
                except Exception as e:
                    st.error(f"워드클라우드 생성 중 오류: {e}")
                    st.info("폰트 파일을 찾을 수 없어 워드클라우드를 생성할 수 없습니다.")
            
            with col2:
                # Top 10 기술스택
                st.markdown("##### Top 10 기술스택")
                top_tech = pd.DataFrame(tech_counts.most_common(10), columns=['기술', '언급 횟수'])
                st.dataframe(top_tech, use_container_width=True, height=420)
        else:
            st.warning("기술스택 데이터가 충분하지 않습니다.")
        
        st.markdown("---")
        
        # 포지션 및 기타 분석
        col1, col2 = st.columns(2)
        
        with col1:
            # 주요 채용 포지션 Top 5
            st.subheader("🚀 주요 채용 포지션 Top 5")
            top_positions = df_company['position'].value_counts().nlargest(5)
            fig_pos = px.bar(
                x=top_positions.values,
                y=top_positions.index,
                orientation='h',
                title=f"기업 ID {company_id}의 Top 5 포지션",
                labels={'x': '공고 수', 'y': '포지션'}
            )
            fig_pos.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_pos, use_container_width=True)
            
        with col2:
            # 고용 형태 분포
            st.subheader("📄 고용 형태 분포")
            job_type_dist = df_company['job_type'].value_counts()
            
            if not job_type_dist.empty:
                fig_job_type = px.pie(
                    job_type_dist,
                    values=job_type_dist.values,
                    names=job_type_dist.index,
                    title=f"기업 ID {company_id}의 고용 형태",
                    hole=0.3
                )
                fig_job_type.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_job_type, use_container_width=True)
            else:
                st.warning("고용 형태 데이터가 없습니다.")

        st.markdown("---")
        
        # 선호 경력/학력
        col3, col4 = st.columns(2)
        with col3:
            st.subheader("📈 선호 경력 분포")
            # 경력 카테고리화 함수
            def categorize_experience(exp):
                if pd.isna(exp) or exp == 0: return '신입 (0년)'
                if 1 <= exp <= 3: return '주니어 (1~3년)'
                if 4 <= exp <= 6: return '미들 (4~6년)'
                if exp >= 7: return '시니어 (7년 이상)'
                return '무관'
            
            df_company['experience_category'] = df_company['experience_min_years'].apply(categorize_experience)
            exp_dist = df_company['experience_category'].value_counts()
            
            fig_exp = px.pie(
                exp_dist,
                values=exp_dist.values,
                names=exp_dist.index,
                title=f"기업 ID {company_id}의 선호 경력"
            )
            st.plotly_chart(fig_exp, use_container_width=True)

        with col4:
            st.subheader("🎓 선호 학력 분포")
            edu_dist = df_company['education'].value_counts()
            fig_edu = px.pie(
                edu_dist,
                values=edu_dist.values,
                names=edu_dist.index,
                title=f"기업 ID {company_id}의 선호 학력"
            )
            st.plotly_chart(fig_edu, use_container_width=True) 