# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from api_client import (
    load_data_from_api, 
    get_stats_overview_sync,
    get_tech_stack_stats_sync,
    get_position_stats_sync,
    get_company_size_stats_sync,
    get_data_job_stats_sync,
    get_experience_stats_sync,
    get_location_stats_sync,
    get_jobs_sync
)
from _common.schema.job_grid import JobGridResponse, CompanyResponse
from collections import Counter

# 페이지 설정
st.set_page_config(
    page_title="데이터 직무 채용 현황 대시보드",
    page_icon="📊",
    layout="wide"
)

# 제목
st.title("📊 데이터 직무 채용 현황 대시보드")
st.markdown("데이터 관련 직무의 채용 현황을 종합적으로 분석합니다.")

st.markdown("---")

# 데이터 로딩 (API에서 가져오기)
df = load_data_from_api()

if df.empty:
    st.error("API에서 데이터를 불러올 수 없습니다.")
    st.stop()

# API에서 통계 데이터 가져오기
stats_overview = get_stats_overview_sync()
tech_stack_stats = get_tech_stack_stats_sync()
position_stats = get_position_stats_sync()
company_size_stats = get_company_size_stats_sync()
data_job_stats = get_data_job_stats_sync()
experience_stats = get_experience_stats_sync()
location_stats = get_location_stats_sync()

# 기본 통계
st.header("📈 기본 통계")
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_jobs = stats_overview.get('total_jobs', len(df))
    st.metric("총 채용공고 수", f"{total_jobs:,}개")
with col2:
    data_job_ratio = stats_overview.get('data_job_ratio', df['is_data_job'].mean() * 100)
    st.metric("데이터 직군 비율", f"{data_job_ratio:.1f}%")
with col3:
    avg_exp = df['experience_min_years'].mean()
    st.metric("평균 요구 경력", f"{avg_exp:.1f}년")
with col4:
    st.metric("고유 기업 수", f"{df['company_id'].nunique():,}개")

st.markdown("---")

# 1. 포지션별 분석
st.subheader("🎯 포지션별 채용 현황")
if position_stats:
    position_df = pd.DataFrame(position_stats)
    fig_pos = px.bar(
        position_df.head(10),
        x='count',
        y='position',
        orientation='h',
        title="포지션별 채용공고 수",
        labels={'count': '공고 수', 'position': '포지션'}
    )
    fig_pos.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_pos, use_container_width=True)
else:
    # API 데이터가 없을 경우 DataFrame에서 계산
    top_positions = df['position'].value_counts().nlargest(10)
    fig_pos = px.bar(
        top_positions,
        x=top_positions.values,
        y=top_positions.index,
        orientation='h',
        title="포지션별 채용공고 수",
        labels={'공고 수': '공고 수', '포지션': '포지션'}
    )
    fig_pos.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_pos, use_container_width=True)

st.markdown("---")

# 2. 추가 분석 (경력, 학력, 지역)
st.subheader("📊 경력, 학력, 지역별 채용 현황")
col1, col2, col3 = st.columns(3)

with col1:
    # 경력 요구사항 분포
    st.markdown("##### 📈 요구 경력 분포")
    if experience_stats:
        exp_df = pd.DataFrame(experience_stats)
        fig_exp = px.pie(
            exp_df,
            values='count',
            names='experience_level',
            title="전체 경력 요구사항"
        )
        fig_exp.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_exp, use_container_width=True)
    else:
        # API 데이터가 없을 경우 DataFrame에서 계산
        def categorize_experience(exp):
            if pd.isna(exp) or exp == 0: return '신입 (0년)'
            if 1 <= exp <= 3: return '주니어 (1~3년)'
            if 4 <= exp <= 6: return '미들 (4~6년)'
            if exp >= 7: return '시니어 (7년 이상)'
            return '무관'
                
        df['experience_category'] = df['experience_min_years'].apply(categorize_experience)
        exp_dist = df['experience_category'].value_counts()
        
        fig_exp = px.pie(
            exp_dist,
            values=exp_dist.values,
            names=exp_dist.index,
            title="전체 경력 요구사항"
        )
        fig_exp.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_exp, use_container_width=True)

with col2:
    # 학력 요구사항 분포
    st.markdown("##### 🎓 요구 학력 분포")
    edu_dist = df['education'].value_counts()
    fig_edu = px.pie(
        edu_dist,
        values=edu_dist.values,
        names=edu_dist.index,
        title="전체 학력 요구사항"
    )
    fig_edu.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_edu, use_container_width=True)

with col3:
    # 지역별 공고 분포 (Top 10)
    st.markdown("##### 🗺️ 채용 활발 지역 Top 10")
    if location_stats:
        location_df = pd.DataFrame(location_stats)
        fig_loc = px.bar(
            location_df.head(10),
            x='count',
            y='district',
            orientation='h',
            title="채용공고 수 기준",
            labels={'count': '공고 수', 'district': '지역'}
        )
        fig_loc.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_loc, use_container_width=True)
    else:
        # API 데이터가 없을 경우 DataFrame에서 계산
        top_locations = df['location_district'].value_counts().nlargest(10)
        top_locations_df = top_locations.reset_index()
        top_locations_df.columns = ['지역', '공고 수']
        fig_loc = px.bar(
            top_locations_df,
            x='공고 수',
            y='지역',
            orientation='h',
            title="채용공고 수 기준",
            labels={'공고 수': '공고 수', '지역': '지역'}
        )
        fig_loc.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_loc, use_container_width=True)

st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    # 2. 경력별 공고 분포
    st.subheader("💼 경력별 공고 분포")
    if experience_stats:
        experience_df = pd.DataFrame(experience_stats)
        fig_exp = px.pie(
            experience_df,
            values='count',
            names='experience_level',
            title="경력별 채용공고 비율"
        )
        st.plotly_chart(fig_exp, use_container_width=True)
    else:
        # API 데이터가 없을 경우 DataFrame에서 계산
        experience_dist = df['experience_min'].value_counts()
        fig_exp = px.pie(
            experience_dist, 
            values=experience_dist.values, 
            names=experience_dist.index,
            title="경력별 채용공고 비율"
        )
        st.plotly_chart(fig_exp, use_container_width=True)

with col2:
    # 3. 가장 많이 요구되는 기술스택 Top 20
    st.subheader("🛠️ 가장 많이 요구되는 기술스택 Top 20")
    if tech_stack_stats:
        tech_df = pd.DataFrame(tech_stack_stats)
        fig_tech = px.bar(
            tech_df.head(20),
            x='count',
            y='tech_name',
            orientation='h',
            title="Top 20 요구 기술스택",
            labels={'count': '언급 횟수', 'tech_name': '기술스택'}
        )
        fig_tech.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_tech, use_container_width=True)
    else:
        # API 데이터가 없을 경우 DataFrame에서 계산
        def get_tech_stack_counts(series):
            tech_list = []
            for item in series.dropna():
                techs = [tech.strip() for tech in item.replace('/', ',').replace(' ', ',').split(',') if tech.strip()]
                tech_list.extend(techs)
            return Counter(tech_list)
        
        tech_counts = get_tech_stack_counts(df['tech_stack'])
        top_tech = pd.DataFrame(tech_counts.most_common(20), columns=['Tech', 'Count'])
        
        fig_tech = px.bar(
            top_tech,
            x='Count',
            y='Tech',
            orientation='h',
            title="Top 20 요구 기술스택",
            labels={'Count': '언급 횟수', 'Tech': '기술스택'}
        )
        fig_tech.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_tech, use_container_width=True)

st.markdown("---")

# 4. 데이터 직군 vs 일반 직군 분석
st.subheader("🔍 데이터 직군 vs 일반 직군 분석")
if data_job_stats:
    data_job_df = pd.DataFrame(data_job_stats)
    col1, col2 = st.columns(2)
    
    with col1:
        # 데이터 직군 vs 일반 직군 비율
        fig_data_role = px.pie(
            data_job_df,
            values='count',
            names=['일반 직군', '데이터 직군'],
            title="데이터 직군 vs 일반 직군 비율"
        )
        fig_data_role.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_data_role, use_container_width=True)
    
    with col2:
        # 데이터 직군별 평균 경력
        fig_avg_exp = px.bar(
            data_job_df,
            x='is_data_job',
            y='avg_experience',
            title="데이터 직군별 평균 요구 경력",
            labels={'is_data_job': '데이터 직군 여부', 'avg_experience': '평균 경력 (년)'}
        )
        st.plotly_chart(fig_avg_exp, use_container_width=True)
else:
    # API 데이터가 없을 경우 DataFrame에서 계산
    col1, col2 = st.columns(2)
    
    with col1:
        data_role_dist = df['is_data_job'].value_counts()
        fig_data_role = px.pie(
            data_role_dist,
            values=data_role_dist.values,
            names=['일반 직군', '데이터 직군'],
            title="데이터 직군 vs 일반 직군 비율"
        )
        fig_data_role.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_data_role, use_container_width=True)
    
    with col2:
        # 데이터 직군별 평균 경력
        avg_exp_by_type = df.groupby('is_data_job')['experience_min_years'].mean()
        fig_avg_exp = px.bar(
            x=['일반 직군', '데이터 직군'],
            y=avg_exp_by_type.values,
            title="데이터 직군별 평균 요구 경력",
            labels={'x': '데이터 직군 여부', 'y': '평균 경력 (년)'}
        )
        st.plotly_chart(fig_avg_exp, use_container_width=True)

st.markdown("---")

# 5. 상세 데이터 테이블
st.subheader("📋 상세 채용 정보")
if not df.empty:
    # 필터링 옵션
    col1, col2, col3 = st.columns(3)
    
    with col1:
        data_job_filter = st.selectbox(
            "데이터 직군 필터",
            ["전체", "데이터 직군만", "일반 직군만"]
        )
    
    with col2:
        experience_filter = st.selectbox(
            "경력 필터",
            ["전체", "신입", "경력"]
        )
    
    with col3:
        position_filter = st.selectbox(
            "포지션 필터",
            ["전체"] + df['position'].unique().tolist()
        )
    
    # 필터링 적용
    filtered_df = df.copy()
    
    if data_job_filter == "데이터 직군만":
        filtered_df = filtered_df[filtered_df['is_data_job'] == True]
    elif data_job_filter == "일반 직군만":
        filtered_df = filtered_df[filtered_df['is_data_job'] == False]
    
    if experience_filter == "신입":
        filtered_df = filtered_df[filtered_df['experience_min'] == '신입']
    elif experience_filter == "경력":
        filtered_df = filtered_df[filtered_df['experience_min'] != '신입']
    
    if position_filter != "전체":
        filtered_df = filtered_df[filtered_df['position'] == position_filter]
    
    # 표시할 컬럼 선택
    display_columns = ['title', 'company_id', 'position', 'experience_min', 'location', 'tech_stack', 'is_data_job']
    
    st.dataframe(
        filtered_df[display_columns].head(50),
        use_container_width=True,
        column_config={
            "title": "채용 제목",
            "company_id": "기업 ID",
            "position": "포지션",
            "experience_min": "최소 경력",
            "location": "지역",
            "tech_stack": "기술스택",
            "is_data_job": "데이터 직군"
        }
    )