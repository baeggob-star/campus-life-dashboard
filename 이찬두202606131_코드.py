import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from wordcloud import WordCloud
from kiwipiepy import Kiwi
from collections import Counter
import matplotlib.font_manager as fm
import re

# 1. Matplotlib 전역 한글 폰트 설정 (로컬 폰트 파일 우선 적용)
font_path = 'NanumGothic.ttf'
try:
    fm.fontManager.addfont(font_path)
    prop = fm.FontProperties(fname=font_path)
    plt.rc('font', family=prop.get_name())
except Exception:
    plt.rc('font', family='NanumGothic')
plt.rc('axes', unicode_minus=False)

# 대시보드 제목
st.title("📊 학생 생활 만족도 인터랙티브 대시보드")

# 파일 업로드 위젯
uploaded_file = st.file_uploader("CSV 파일을 업로드해주세요", type=['csv'])

if uploaded_file is not None:
    df_raw = pd.read_csv(uploaded_file)
    initial_count = len(df_raw)

    # 잘못된 데이터 정제
    numeric_cols = ['공부시간', '수면시간', '스마트폰', '만족도']

    for col in numeric_cols:
        if col in df_raw.columns:
            df_raw[col] = pd.to_numeric(df_raw[col], errors='coerce')

    df = df_raw.dropna(subset=numeric_cols + ['학과'])

    excluded_count = initial_count - len(df)
    if excluded_count > 0:
        st.error(f"※ 데이터 오류 또는 결측치로 인해 제외된 데이터: {excluded_count}건")

    # 데이터 미리보기
    st.subheader("데이터 미리보기 (Top 5)")
    st.dataframe(df.head())

    # 학과별 분석 대시보드 및 필터
    st.subheader("학과별 분석 대시보드")
    departments = ['전체'] + list(df['학과'].unique())
    selected_dept = st.selectbox("조회할 학과를 선택하세요:", departments)

    if selected_dept != '전체':
        filtered_df = df[df['학과'] == selected_dept]
    else:
        filtered_df = df

    if not filtered_df.empty:
        avg_satisfaction = filtered_df['만족도'].mean()
        st.success(f"**선택된 그룹 평균 학교생활 만족도:** {avg_satisfaction:.2f}점 (총 {len(filtered_df)}명)")

    # 상관관계 산점도
    st.write("### 요인별 만족도 상관관계 산점도")
    col1, col2, col3 = st.columns(3)

    with col1:
        fig1 = px.scatter(filtered_df, x='공부시간', y='만족도', title='공부시간 vs 만족도')
        fig1.update_layout(font=dict(family="NanumGothic"))
        fig1.update_xaxes(title_text='공부시간 (시간)')
        fig1.update_yaxes(title_text='만족도 (점수)')
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        fig2 = px.scatter(filtered_df, x='수면시간', y='만족도', title='수면시간 vs 만족도')
        fig2.update_layout(font=dict(family="NanumGothic"))
        fig2.update_xaxes(title_text='수면시간 (시간)')
        fig2.update_yaxes(title_text='만족도 (점수)')
        st.plotly_chart(fig2, use_container_width=True)

    with col3:
        fig3 = px.scatter(filtered_df, x='스마트폰', y='만족도', title='스마트폰 사용시간 vs 만족도')
        fig3.update_layout(font=dict(family="NanumGothic"))
        fig3.update_xaxes(title_text='스마트폰 사용시간 (시간)')
        fig3.update_yaxes(title_text='만족도 (점수)')
        st.plotly_chart(fig3, use_container_width=True)

    # 텍스트 분석
    st.write("### 📝 학생 한줄의견 텍스트 분석")

    if '한줄의견' in filtered_df.columns:
        kiwi = Kiwi()
        stop_words = set(['하다', '있다', '되다', '이다', '같다', '없다', '않다', '그렇다', '이', '그', '저', '수', '너무', '정말', '진짜'])
        pos_words = set(['좋다', '맛있다', '재미있다', '예쁘다', '도움', '최고', '편하다', '만족', '추천', '유익하다'])
        neg_words = set(['부족하다', '불편하다', '피곤하다', '힘들다', '나쁘다', '길다', '어렵다', '아쉽다', '짜증나다', '별로'])

        all_words = []

        for text in filtered_df['한줄의견'].dropna():
            tokens = kiwi.tokenize(str(text))
            for token in tokens:
                if token.tag.startswith('N') or token.tag in ['VV', 'VA']:
                    word = token.form
                    if token.tag in ['VV', 'VA']:
                        word += '다'
                    if word not in stop_words and len(word) > 1:
                        all_words.append(word)

        if all_words:
            word_counts = Counter(all_words)
            pos_count = sum(word_counts[w] for w in pos_words if w in word_counts)
            neg_count = sum(word_counts[w] for w in neg_words if w in word_counts)

            st.write("#### 📊 감성 단어 분석 결과")
            metric_col1, metric_col2 = st.columns(2)
            metric_col1.metric(label="😊 긍정 단어 등장 횟수", value=f"{pos_count}회")
            metric_col2.metric(label="😥 부정 단어 등장 횟수", value=f"{neg_count}회")

            st.write("---")

            st.write("#### 📈 자주 등장하는 단어 Top 10")
            top_10_words = word_counts.most_common(10)
            top10_df = pd.DataFrame(top_10_words, columns=['단어', '빈도수'])
            top10_df = top10_df.sort_values(by='빈도수', ascending=True)

            fig_bar = px.bar(top10_df, x='빈도수', y='단어', orientation='h', title='상위 10개 키워드')
            fig_bar.update_layout(font=dict(family="NanumGothic"))
            st.plotly_chart(fig_bar, use_container_width=True)

            st.write("---")

            st.write("#### ☁️ 텍스트 워드클라우드")
            word_string = " ".join(all_words)

            try:
                wc = WordCloud(
                    font_path='NanumGothic.ttf',
                    width=1000,
                    height=400,
                    background_color='white',
                    colormap='viridis'
                ).generate(word_string)

                fig_wc, ax = plt.subplots(figsize=(10, 4))
                ax.imshow(wc, interpolation='bilinear')
                ax.axis('off')
                st.pyplot(fig_wc)

            except AttributeError:
                import random
                from matplotlib.font_manager import FontProperties

                try:
                    custom_font = FontProperties(fname="NanumGothic.ttf")
                except Exception:
                    custom_font = FontProperties(family="NanumGothic")

                top_words_for_wc = word_counts.most_common(40)

                fig_wc, ax = plt.subplots(figsize=(10, 4))
                ax.set_facecolor('white')
                fig_wc.patch.set_facecolor('white')

                max_cnt = top_words_for_wc[0][1] if top_words_for_wc else 1
                colors = ['#440154', '#414487', '#2a788e', '#22a884', '#7ad151', '#fde725']

                random.seed(42)
                for word, cnt in top_words_for_wc:
                    size = max(12, int((cnt / max_cnt) * 50))
                    x = random.uniform(0.05, 0.85)
                    y = random.uniform(0.05, 0.85)
                    ax.text(x, y, word, fontsize=size, color=random.choice(colors),
                            ha='center', va='center', weight='bold', fontproperties=custom_font)

                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
                ax.axis('off')
                st.pyplot(fig_wc)

        else:
            st.info("조건에 맞는 유효한 한줄의견 데이터(표제어)가 없습니다.")