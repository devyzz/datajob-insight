# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from db_utils import load_data, get_tech_stack_counts, get_company_size_specs, get_data_job_analysis, get_skill_analysis, get_position_analysis

# 페이지 설정
st.set_page_config(
    page_title="데이터 직무 채용 현황 대시보드",
    page_icon="📊",
    layout="wide"
)

# 제목
st.title("📊 데이터 직무 채용 현황 대시보드")
st.markdown("데이터 관련 직무의 채용 현황을 종합적으로 분석합니다.")

# 데이터 로딩
@st.cache_data
def cached_load_data():
    return load_data()

df = cached_load_data()

if df.empty:
    st.error("데이터를 불러올 수 없습니다.")
    st.stop()

# 기본 통계
st.header("📈 기본 통계")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("총 채용공고 수", f"{len(df):,}개")
with col2:
    st.metric("데이터 직군 비율", f"{df['is_data_job'].mean():.1%}")
with col3:
    avg_exp = df['experience_min_years'].mean()
    st.metric("평균 요구 경력", f"{avg_exp:.1f}년")
with col4:
    st.metric("고유 기업 수", f"{df['company_id'].nunique():,}개")

st.markdown("---")

# 1. 포지션별 분석
st.subheader("🎯 포지션별 채용 현황")
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
    # 2. 기업 규모별 공고 분포
    st.subheader("🏢 기업 규모별 공고 분포")
    company_size_dist = df['company_id'].value_counts()
    fig_size = px.pie(
        company_size_dist, 
        values=company_size_dist.values, 
        names=company_size_dist.index,
        title="기업 ID별 채용공고 비율"
    )
    st.plotly_chart(fig_size, use_container_width=True)

with col2:
    # 3. 가장 많이 요구되는 기술스택 Top 20
    st.subheader("🛠️ 가장 많이 요구되는 기술스택 Top 20")
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

# 4. 새로운 분석 섹션 추가
st.subheader("🔍 상세 분석")

# 기술 스택 분석
skill_df = get_skill_analysis()
if not skill_df.empty:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 💻 기술 스택별 사용 빈도 (Top 15)")
        top_skills = skill_df.head(15)
        fig_skills = px.bar(
            top_skills,
            x='usage_count',
            y='skill_name',
            orientation='h',
            color='skill_type',
            title="기술 스택 사용 빈도",
            labels={'usage_count': '사용 횟수', 'skill_name': '기술명'}
        )
        fig_skills.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_skills, use_container_width=True)
    
    with col2:
        st.markdown("##### 📊 기술 스택 타입별 분포")
        skill_type_dist = skill_df['skill_type'].value_counts()
        fig_skill_type = px.pie(
            skill_type_dist,
            values=skill_type_dist.values,
            names=skill_type_dist.index,
            title="기술 스택 타입별 분포"
        )
        fig_skill_type.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_skill_type, use_container_width=True)

# 포지션 분석
position_df = get_position_analysis()
if not position_df.empty:
    st.markdown("##### 🎯 포지션 카테고리별 분석")
    col1, col2 = st.columns(2)
    
    with col1:
        # 데이터 직군 vs 일반 직군
        data_role_dist = position_df['is_data_job'].value_counts()
        fig_data_role = px.pie(
            data_role_dist,
            values=data_role_dist.values,
            names=['일반 직군', '데이터 직군'],
            title="데이터 직군 vs 일반 직군 비율"
        )
        fig_data_role.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_data_role, use_container_width=True)
    
    with col2:
        # 주요 카테고리별 분포
        primary_cat_dist = position_df['primary_category'].value_counts().head(10)
        primary_cat_df = primary_cat_dist.reset_index()
        primary_cat_df.columns = ['카테고리', '공고 수']
        fig_primary_cat = px.bar(
            primary_cat_df,
            x='공고 수',
            y='카테고리',
            orientation='h',
            title="주요 카테고리별 채용공고 수 (Top 10)"
        )
        fig_primary_cat.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_primary_cat, use_container_width=True)

# 5. 플랫폼별 분석
st.markdown("---")
st.subheader("🌐 플랫폼별 채용 현황")

platform_stats = df.groupby('platform_id').agg({
    'posting_id': 'count',
    'is_data_job': 'mean',
    'company_id': 'nunique'
}).reset_index()
platform_stats.columns = ['Platform_ID', 'Job_Count', 'Data_Job_Ratio', 'Company_Count']

col1, col2 = st.columns(2)

with col1:
    fig_platform_jobs = px.bar(
        platform_stats,
        x='Platform_ID',
        y='Job_Count',
        title="플랫폼별 채용공고 수",
        labels={'Job_Count': '공고 수', 'Platform_ID': '플랫폼 ID'}
    )
    st.plotly_chart(fig_platform_jobs, use_container_width=True)

with col2:
    fig_platform_data = px.bar(
        platform_stats,
        x='Platform_ID',
        y='Data_Job_Ratio',
        title="플랫폼별 데이터 직군 비율",
        labels={'Data_Job_Ratio': '데이터 직군 비율', 'Platform_ID': '플랫폼 ID'}
    )
    st.plotly_chart(fig_platform_data, use_container_width=True)