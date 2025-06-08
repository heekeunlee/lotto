import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta

# 기본 설정
st.set_page_config(page_title="로또 번호 통계 분석", layout="wide")

# 스타일
st.markdown("""
<style>
    .lotto-ball {
        display: inline-block;
        width: 40px; height: 40px;
        border-radius: 50%;
        background-color: gray;
        color: white;
        text-align: center;
        line-height: 40px;
        font-weight: bold;
        margin: 2px;
    }
</style>
""", unsafe_allow_html=True)

def get_ball_color(n):
    if n <= 10:
        return "#FFD700"
    elif n <= 20:
        return "#1E90FF"
    elif n <= 30:
        return "#FF4500"
    elif n <= 40:
        return "#808080"
    else:
        return "#32CD32"

def render_lotto_balls(numbers):
    return " ".join([f"<span class='lotto-ball' style='background-color:{get_ball_color(n)}'>{n}</span>" for n in numbers])

@st.cache_data
def generate_lotto_data(n=100):
    results = []
    for i in range(n):
        date = datetime.now() - timedelta(weeks=i)
        nums = sorted(np.random.choice(range(1, 46), 6, replace=False))
        bonus = np.random.choice([x for x in range(1, 46) if x not in nums])
        results.append({
            "round": 1000 - i,
            "date": date.strftime("%Y-%m-%d"),
            "numbers": nums,
            "bonus": bonus
        })
    return results

# UI
st.title("🎯 로또 번호 통계 분석 및 추천")
rounds = st.sidebar.slider("최근 회차 수", 50, 300, 100)
data = generate_lotto_data(rounds)

# 번호별 통계
all_numbers = []
for draw in data:
    all_numbers += draw['numbers']
counts = pd.Series(all_numbers).value_counts().sort_index()
df = pd.DataFrame({'number': counts.index, 'count': counts.values})

fig = px.bar(df, x='number', y='count', labels={'count': '출현 수', 'number': '번호'})
st.plotly_chart(fig, use_container_width=True)

# 추천 번호
st.subheader("🎲 추천 번호")
weights = df['count'] + 1
weights = weights / weights.sum()
for i in range(5):
    rec = sorted(np.random.choice(df['number'], 6, replace=False, p=weights))
    st.markdown(render_lotto_balls(rec), unsafe_allow_html=True)
