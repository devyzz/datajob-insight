import streamlit as st
import pandas as pd
import plotly.express as px
from db_utils import load_data, get_tech_stack_counts
from collections import Counter
from itertools import combinations
from wordcloud import WordCloud
import matplotlib.pyplot as plt

st.set_page_config(page_title="기술 스택 심층 분석", page_icon="🛠️", layout="wide")

st.title("🛠️ 기술 스택 심층 분석")
st.markdown("직군(포지션)별로 많이 요구되는 기술스택과, 자주 함께 등장하는 기술 조합을 자동으로 분석합니다.")

# --- 데이터 로딩 ---
@st.cache_data
def cached_load_data():
    return load_data()

df = cached_load_data()

if df.empty:
    st.error("데이터를 불러올 수 없습니다.")
    st.stop()

# --- 1. 직군(포지션) 선택 ---
all_positions = sorted(df['position'].dropna().unique())
def_pos = '데이터 엔지니어' if '데이터 엔지니어' in all_positions else all_positions[0]
selected_position = st.selectbox(
    '분석할 직군(포지션)을 선택하세요:',
    all_positions,
    index=all_positions.index(def_pos)
)

# --- 2. 해당 직군 데이터 필터링 ---
df_pos = df[df['position'] == selected_position]

if df_pos.empty:
    st.warning(f"'{selected_position}' 직군의 데이터가 없습니다.")
    st.stop()

# --- 3. Top 10 기술스택 (워드클라우드 & 바차트) ---
st.header(f"'{selected_position}' 직군의 Top 10 기술스택")
tech_counts = get_tech_stack_counts(df_pos['tech_stack'])

col1, col2 = st.columns([2, 1])
with col1:
    if tech_counts:
        try:
            wordcloud = WordCloud(
                width=600, height=300, background_color='white',
                colormap='viridis', max_words=30,
                font_path='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'  # Docker 환경용 폰트
            ).generate_from_frequencies(tech_counts)
            fig, ax = plt.subplots(figsize=(8, 4))
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
    if tech_counts:
        top_tech = pd.DataFrame(tech_counts.most_common(10), columns=['기술', '언급 횟수'])
        st.dataframe(top_tech, use_container_width=True)
    else:
        st.info("기술스택 데이터가 없습니다.")

st.markdown("---")

# --- 4. 자주 함께 요구되는 기술 조합 Top 10 ---
st.header(f"'{selected_position}' 직군에서 자주 함께 요구되는 기술 조합 Top 10")
tech_lists = df_pos['tech_stack'].dropna().apply(lambda x: [tech.strip() for tech in x.replace('/', ',').split(',') if tech.strip()])
co_occurrence = Counter()
for tech_list in tech_lists:
    if len(tech_list) >= 2:
        for p in combinations(sorted(list(set(tech_list))), 2):
            co_occurrence[p] += 1

if not co_occurrence:
    st.info("2개 이상 기술이 함께 언급된 공고가 충분하지 않습니다.")
else:
    top_pairs = co_occurrence.most_common(10)
    df_pairs = pd.DataFrame(top_pairs, columns=['기술 조합', '언급 횟수'])
    df_pairs['기술 조합'] = df_pairs['기술 조합'].apply(lambda x: f"{x[0]} & {x[1]}")
    fig = px.bar(
        df_pairs.sort_values('언급 횟수'),
        x='언급 횟수',
        y='기술 조합',
        orientation='h',
        title=f"'{selected_position}' 직군에서 자주 함께 요구되는 기술 조합 Top 10"
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df_pairs, use_container_width=True)

st.markdown("---")


