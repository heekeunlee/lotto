import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import matplotlib.font_manager as fm
import matplotlib as mpl
import random
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image, ImageDraw, ImageFont
import io

# 한글 폰트 설정 (한글 출력을 위함)
plt.rcParams['font.family'] = 'Malgun Gothic'  # 또는 시스템에 설치된 다른 한글 폰트
plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지

# 페이지 설정
st.set_page_config(
    page_title="로또 번호 통계 분석 및 투자 추천",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일 적용
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .sub-header {
        font-size: 1.5rem;
        color: #424242;
        margin-bottom: 1rem;
    }
    .lotto-ball {
        display: inline-block;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        text-align: center;
        line-height: 40px;
        font-weight: bold;
        margin: 5px;
        color: white;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
    }
    .info-box {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        border-left: 5px solid #1E88E5;
    }
    .stat-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-header'>로또 6/45 통계 분석 및 투자 전략 🍀</h1>", unsafe_allow_html=True)
st.markdown("<div class='info-box'>최근 로또 번호의 통계를 분석하고, 투자 전략을 제안합니다. 데이터 기반의 추천 번호로 5회 투자해보세요!</div>", unsafe_allow_html=True)

# 로또 번호 색상 정의 함수
def get_ball_color(number):
    if number <= 10:
        return "#FFCC00"  # 노란색
    elif number <= 20:
        return "#66B2FF"  # 파란색
    elif number <= 30:
        return "#FF6666"  # 빨간색
    elif number <= 40:
        return "#999999"  # 회색
    else:
        return "#66CC66"  # 녹색

# HTML로 로또 볼 렌더링
def render_lotto_balls(numbers):
    html = ""
    for num in numbers:
        color = get_ball_color(num)
        html += f"<span class='lotto-ball' style='background-color: {color};'>{num}</span>"
    return html

# 가상의 최근 5년 로또 데이터 생성 함수
def generate_lotto_data(num_weeks=260):  # 5년 = 약 260주
    results = []
    
    end_date = datetime.now()
    for i in range(num_weeks):
        # 날짜 계산 (가장 최근 주부터 역순으로)
        draw_date = end_date - timedelta(days=7*i)
        
        # 로또 번호 생성 (실제 분포와 비슷하게 약간의 편향성 추가)
        # 실제로는 모든 번호가 균등한 확률로 나와야 하지만, 시각화 목적으로 약간의 편향 추가
        weights = np.ones(45)
        weights[0:10] *= 1.1  # 1-10번 약간 더 자주 출현
        weights[40:45] *= 0.9  # 41-45번 약간 덜 출현
        weights = weights / weights.sum()  # 정규화
        
        # 6개 번호 추첨
        numbers = np.sort(np.random.choice(range(1, 46), 6, replace=False, p=weights))
        
        # 보너스 번호 추첨
        bonus = np.random.choice([n for n in range(1, 46) if n not in numbers])
        
        # 회차 번호 계산 (최근 회차를 1000번대로 가정)
        draw_round = 1000 + num_weeks - i
        
        results.append({
            'round': draw_round,
            'date': draw_date.strftime('%Y-%m-%d'),
            'numbers': numbers.tolist(),
            'bonus': bonus
        })
    
    return results

# 실제 로또 데이터를 가져오는 함수 (웹 스크래핑을 통해)
def get_real_lotto_data(start_round, end_round):
    results = []
    
    for round_num in range(start_round, end_round + 1):
        try:
            url = f"https://www.dhlottery.co.kr/gameResult.do?method=byWin&drwNo={round_num}"
            response = requests.get(url)
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 추첨일 추출
            date_text = soup.select_one(".win_result .desc").text.strip()
            draw_date = re.search(r'\((.+)\)', date_text).group(1)
            
            # 당첨번호 추출
            win_numbers = []
            for span in soup.select(".win_result .num.win p span"):
                win_numbers.append(int(span.text.strip()))
            
            # 보너스 번호 추출
            bonus_number = int(soup.select_one(".win_result .num.bonus p span").text.strip())
            
            results.append({
                "round": round_num,
                "date": draw_date,
                "numbers": win_numbers,
                "bonus": bonus_number
            })
            
            # 로그 메시지 (실제 앱에서는 주석 처리하거나 제거)
            # print(f"회차 {round_num} 데이터 수집 완료")
        except Exception as e:
            # 실패한 경우 빈 회차 처리
            # print(f"회차 {round_num} 데이터 수집 실패: {e}")
            pass
    
    return results

# 데이터 로딩 및 분석 함수
@st.cache_data
def load_and_analyze_data(num_rounds):
    # 여기에서 실제 데이터를 가져오거나 가상 데이터를 생성
    # 테스트를 위해 가상 데이터 사용
    lotto_data = generate_lotto_data(num_rounds)
    
    # 실제 데이터를 가져오려면 아래 코드 사용
    # current_round = 1170  # 예시 (실제 현재 회차로 대체 필요)
    # start_round = current_round - num_rounds + 1
    # lotto_data = get_real_lotto_data(start_round, current_round)
    
    # 번호별 출현 빈도 분석
    number_counts = np.zeros(45)
    bonus_counts = np.zeros(45)
    
    for draw in lotto_data:
        for num in draw['numbers']:
            number_counts[num-1] += 1
        bonus_counts[draw['bonus']-1] += 1
    
    # 데이터프레임으로 변환
    freq_df = pd.DataFrame({
        'number': range(1, 46),
        'frequency': number_counts,
        'bonus_frequency': bonus_counts,
        'total_frequency': number_counts + bonus_counts
    })
    
    # 구간별 분석
    ranges = {
        "1-10": (1, 10),
        "11-20": (11, 20),
        "21-30": (21, 30),
        "31-40": (31, 40),
        "41-45": (41, 45)
    }
    
    range_counts = {}
    for label, (start, end) in ranges.items():
        count = sum(number_counts[start-1:end])
        range_counts[label] = count
    
    # 홀짝 분석
    odd_numbers = [i for i in range(1, 46) if i % 2 == 1]
    even_numbers = [i for i in range(1, 46) if i % 2 == 0]
    
    odd_count = sum(number_counts[i-1] for i in odd_numbers)
    even_count = sum(number_counts[i-1] for i in even_numbers)
    
    # 시간에 따른 분석을 위한 데이터 변환
    data_for_trend = []
    for draw in lotto_data:
        draw_date = datetime.strptime(draw['date'], '%Y-%m-%d')
        year = draw_date.year
        month = draw_date.month
        
        # 각 번호의 출현 여부
        for num in range(1, 46):
            appeared = num in draw['numbers'] or num == draw['bonus']
            data_for_trend.append({
                'date': draw_date,
                'year': year,
                'month': month,
                'number': num,
                'appeared': 1 if appeared else 0
            })
    
    trend_df = pd.DataFrame(data_for_trend)
    
    # 결과 반환
    return {
        'lotto_data': lotto_data,
        'frequency': freq_df,
        'range_counts': range_counts,
        'odd_even': {'odd': odd_count, 'even': even_count},
        'trend_data': trend_df
    }

# 로또 번호 추천 함수 (통계 기반)
def recommend_lotto_numbers(data, strategy, num_sets=5):
    freq_df = data['frequency']
    recommended_sets = []
    
    for _ in range(num_sets):
        if strategy == "hot_numbers":
            # 고빈도 번호 중심 전략
            weights = freq_df['frequency'] ** 2  # 출현 빈도의 제곱으로 가중치 부여
        elif strategy == "balance":
            # 균형 전략 (약간의 빈도 가중치)
            weights = freq_df['frequency'] * 0.5 + 0.5  # 균등 확률 + 약간의 빈도 가중치
        elif strategy == "cold_numbers":
            # 저빈도 번호 중심 전략
            max_freq = freq_df['frequency'].max()
            weights = (max_freq - freq_df['frequency'] + 1) ** 2  # 저빈도 번호에 높은 가중치
        elif strategy == "mix_hot_cold":
            # 고빈도 + 저빈도 혼합 전략
            sorted_freq = freq_df.sort_values('frequency', ascending=False)
            hot_numbers = sorted_freq.head(15)['number'].values
            cold_numbers = sorted_freq.tail(15)['number'].values
            
            # 3개는 고빈도, 3개는 저빈도 선택
            hot_picks = np.random.choice(hot_numbers, 3, replace=False)
            cold_picks = np.random.choice(cold_numbers, 3, replace=False)
            recommended_sets.append(sorted(np.concatenate([hot_picks, cold_picks])))
            continue
        else:
            # 완전 랜덤 전략
            weights = np.ones(45)
        
        # 가중치 정규화
        weights = weights / weights.sum()
        
        # 번호 선택
        selected = np.random.choice(range(1, 46), 6, replace=False, p=weights)
        recommended_sets.append(sorted(selected))
    
    return recommended_sets

# 번호 세트 분석 함수
def analyze_number_set(numbers):
    # 홀짝 분석
    odd_count = len([n for n in numbers if n % 2 == 1])
    even_count = len([n for n in numbers if n % 2 == 0])
    
    # 번호 범위별 분포
    ranges = {
        "1-10": len([n for n in numbers if 1 <= n <= 10]),
        "11-20": len([n for n in numbers if 11 <= n <= 20]),
        "21-30": len([n for n in numbers if 21 <= n <= 30]),
        "31-40": len([n for n in numbers if 31 <= n <= 40]),
        "41-45": len([n for n in numbers if 41 <= n <= 45])
    }
    
    # 번호 합계 및 평균
    sum_numbers = sum(numbers)
    avg_numbers = sum_numbers / len(numbers)
    
    return {
        'odd_even': {'odd': odd_count, 'even': even_count},
        'ranges': ranges,
        'sum': sum_numbers,
        'avg': avg_numbers
    }

# 사이드바 설정
st.sidebar.markdown("## 분석 설정 ⚙️")
analysis_period = st.sidebar.slider("분석 기간 (최근 N회)", 50, 300, 200)

# 데이터 로딩
if 'data' not in st.session_state:
    st.session_state.data = load_and_analyze_data(analysis_period)
elif st.sidebar.button("데이터 새로고침"):
    st.session_state.data = load_and_analyze_data(analysis_period)

# 탭 설정
tab1, tab2, tab3 = st.tabs(["📊 번호 통계 분석", "📈 추세 분석", "💰 투자 추천"])

# 탭 1: 번호 통계 분석
with tab1:
    st.markdown("<h2 class='sub-header'>로또 번호 통계 분석</h2>", unsafe_allow_html=True)
    
    # 번호별 출현 빈도 차트
    freq_df = st.session_state.data['frequency']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='stat-card'>", unsafe_allow_html=True)
        st.subheader("번호별 출현 빈도")
        
        fig = px.bar(
            freq_df, 
            x='number', 
            y='frequency',
            color=[get_ball_color(num) for num in range(1, 46)],
            color_discrete_map="identity",
            labels={'number': '로또 번호', 'frequency': '출현 횟수'},
            title="번호별 출현 빈도 (일반 번호)"
        )
        fig.update_layout(xaxis=dict(tickmode='linear', dtick=5))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # 가장 많이/적게 출현한 번호
        st.markdown("<div class='stat-card'>", unsafe_allow_html=True)
        st.subheader("주목할 번호")
        
        hot_numbers = freq_df.nlargest(5, 'frequency')
        cold_numbers = freq_df.nsmallest(5, 'frequency')
        
        st.markdown("**가장 많이 출현한 번호 (Hot)**")
        hot_html = render_lotto_balls(hot_numbers['number'].tolist())
        st.markdown(hot_html, unsafe_allow_html=True)
        
        st.markdown("**가장 적게 출현한 번호 (Cold)**")
        cold_html = render_lotto_balls(cold_numbers['number'].tolist())
        st.markdown(cold_html, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col2:
        st.markdown("<div class='stat-card'>", unsafe_allow_html=True)
        st.subheader("구간별 출현 빈도")
        
        range_counts = st.session_state.data['range_counts']
        range_colors = ["#FFCC00", "#66B2FF", "#FF6666", "#999999", "#66CC66"]
        
        fig = px.bar(
            x=list(range_counts.keys()),
            y=list(range_counts.values()),
            color=list(range_counts.keys()),
            color_discrete_map={k: c for k, c in zip(range_counts.keys(), range_colors)},
            labels={'x': '번호 구간', 'y': '출현 횟수'},
            title="구간별 번호 출현 빈도"
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='stat-card'>", unsafe_allow_html=True)
        st.subheader("홀/짝 비율")
        
        odd_even = st.session_state.data['odd_even']
        fig = px.pie(
            values=[odd_even['odd'], odd_even['even']],
            names=['홀수', '짝수'],
            color=['홀수', '짝수'],
            color_discrete_map={'홀수': '#FF6666', '짝수': '#66B2FF'},
            hole=0.4,
            title="홀수 vs 짝수 출현 비율"
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# 탭 2: 추세 분석
with tab2:
    st.markdown("<h2 class='sub-header'>로또 번호 추세 분석</h2>", unsafe_allow_html=True)
    
    trend_data = st.session_state.data['trend_data']
    
    # 최근 10회차 당첨 번호 표시
    st.markdown("<div class='stat-card'>", unsafe_allow_html=True)
    st.subheader("최근 당첨 번호")
    
    recent_draws = st.session_state.data['lotto_data'][:10]
    for draw in recent_draws:
        st.markdown(f"**{draw['round']}회 ({draw['date']}):**")
        numbers_html = render_lotto_balls(draw['numbers'])
        bonus_html = f" + <span class='lotto-ball' style='background-color: {get_ball_color(draw['bonus'])};'>{draw['bonus']}</span>"
        st.markdown(numbers_html + bonus_html, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='stat-card'>", unsafe_allow_html=True)
        st.subheader("번호별 출현 패턴")
        
        # 출현 패턴 히트맵 (회차별)
        yearly_trend = trend_data[trend_data['appeared'] == 1].groupby(['year', 'number']).size().reset_index(name='count')
        pivot_yearly = yearly_trend.pivot(index='year', columns='number', values='count').fillna(0)
        
        fig = px.imshow(
            pivot_yearly,
            labels=dict(x="로또 번호", y="년도", color="출현 횟수"),
            x=[str(i) for i in range(1, 46)],
            y=pivot_yearly.index,
            color_continuous_scale="YlOrRd"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='stat-card'>", unsafe_allow_html=True)
        st.subheader("번호별 연속 미출현 기간")
        
        # 각 번호의 현재 연속 미출현 회차 계산
        latest_appearances = {}
        max_round = st.session_state.data['lotto_data'][0]['round']
        
        for draw in reversed(st.session_state.data['lotto_data']):
            round_num = draw['round']
            for num in range(1, 46):
                if num not in latest_appearances and (num in draw['numbers'] or num == draw['bonus']):
                    latest_appearances[num] = round_num
        
        # 미출현 회차 계산
        non_appearance = []
        for num in range(1, 46):
            last_round = latest_appearances.get(num, 0)
            if last_round == 0:
                streak = max_round  # 전체 기간 동안 한 번도 안 나온 경우
            else:
                streak = max_round - last_round
            non_appearance.append({'number': num, 'streak': streak})
        
        non_appearance_df = pd.DataFrame(non_appearance)
        non_appearance_df = non_appearance_df.sort_values('streak', ascending=False)
        
        # 상위 15개만 표시
        top_non_appearance = non_appearance_df.head(15)
        
        fig = px.bar(
            top_non_appearance,
            x='number',
            y='streak',
            color=[get_ball_color(num) for num in top_non_appearance['number']],
            color_discrete_map="identity",
            labels={'number': '로또 번호', 'streak': '연속 미출현 회차'},
            title="가장 오래 출현하지 않은 번호들"
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# 탭 3: 투자 추천
with tab3:
    st.markdown("<h2 class='sub-header'>최적 투자 전략 추천</h2>", unsafe_allow_html=True)
    
    st.markdown("<div class='info-box'>통계 데이터를 기반으로 5회 투자를 위한 번호 세트를 추천합니다. 각 전략에 따라 다른 번호 조합이 생성됩니다.</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.markdown("<div class='stat-card'>", unsafe_allow_html=True)
        st.subheader("투자 전략 선택")
        
        strategy = st.radio(
            "번호 선택 전략",
            options=[
                "hot_numbers", 
                "balance", 
                "cold_numbers", 
                "mix_hot_cold", 
                "random"
            ],
            format_func=lambda x: {
                "hot_numbers": "인기 번호 전략",
                "balance": "균형 전략",
                "cold_numbers": "저빈도 번호 전략",
                "mix_hot_cold": "인기+비인기 혼합",
                "random": "완전 랜덤"
            }[x]
        )
        
        if st.button("번호 생성하기", type="primary"):
            st.session_state.recommended_sets = recommend_lotto_numbers(
                st.session_state.data, 
                strategy,
                num_sets=5
            )
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='stat-card'>", unsafe_allow_html=True)
        st.subheader("전략 설명")
        
        strategy_descriptions = {
            "hot_numbers": "최근에 자주 출현한 인기 번호를 중심으로 선택합니다. 통계적으로 당첨 확률이 높다고 믿어지는 번호들을 선호합니다.",
            "balance": "전체적인 번호 빈도에 약간의 가중치를 두지만, 균형 잡힌 선택을 합니다. 안정적인 전략입니다.",
            "cold_numbers": "최근에 적게 출현한 번호를 중심으로 선택합니다. '반드시 나올 때가 되었다'는 믿음에 기반합니다.",
            "mix_hot_cold": "인기 번호 3개와 비인기 번호 3개를 혼합하여 균형을 맞춥니다. 인기/비인기 번호의 장점을 모두 활용합니다.",
            "random": "완전히 랜덤하게 번호를 선택합니다. 통계와 상관없는 순수 확률 기반 선택입니다."
        }
        
        st.info(strategy_descriptions[strategy])
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col1:
        st.markdown("<div class='stat-card'>", unsafe_allow_html=True)
        st.subheader("추천 번호 (5회 투자)")
        
        if 'recommended_sets' in st.session_state:
            for i, numbers in enumerate(st.session_state.recommended_sets):
                st.markdown(f"**투자 #{i+1}**")
                
                # 로또 볼 표시
                numbers_html = render_lotto_balls(numbers)
                st.markdown(numbers_html, unsafe_allow_html=True)
                
                # 번호 분석
                analysis = analyze_number_set(numbers)
                
                # 홀짝 비율
                odd_even_text = f"홀수: {analysis['odd_even']['odd']}개, 짝수: {analysis['odd_even']['even']}개"
                
                # 번호 범위 분포
                range_text = " | ".join([f"{k}: {v}개" for k, v in analysis['ranges'].items()])
                
                # 번호 합계 및 평균
                sum_avg_text = f"합계: {analysis['sum']} | 평균: {analysis['avg']:.1f}"
                
                st.markdown(f"{odd_even_text} | {sum_avg_text}")
                st.markdown(f"번호 분포: {range_text}")
                
                if i < len(st.session_state.recommended_sets) - 1:
                    st.markdown("---")
        else:
            st.info("오른쪽에서 투자 전략을 선택하고 '번호 생성하기' 버튼을 눌러주세요.")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # 당첨 확률 설명
    st.markdown("<div class='stat-card'>", unsafe_allow_html=True)
    st.subheader("로또 당첨 확률 안내")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**로또 6/45 당첨 확률:**")
        st.markdown("- 1등 (6개 번호 일치): 1/8,145,060")
        st.markdown("- 2등 (5개 번호 + 보너스): 1/1,357,510")
        st.markdown("- 3등 (5개 번호): 1/35,724")
        st.markdown("- 4등 (4개 번호): 1/733")
        st.markdown("- 5등 (3개 번호): 1/45")
    
    with col2:
        st.markdown("**참고 사항:**")
        st.markdown("- 로또는 랜덤한 게임이며, 과거 데이터로 미래를 정확히 예측할 수 없습니다.")
        st.markdown("- 제시된 추천 번호는 통계적 분석을 기반으로 하지만, 당첨을 보장하지 않습니다.")
        st.markdown("- 복권 구매는 즐거움을 위한 것이며, 책임감 있게 즐겨주세요.")
    
    st.markdown("</div>", unsafe_allow_html=True)

# 번호 선택 페이지 (직접 선택 기능)
if st.checkbox("나만의 번호 조합 분석하기"):
    st.markdown("<div class='stat-card'>", unsafe_allow_html=True)
    st.subheader("나만의 번호 조합")
    
    # 사용자 입력 받기
    user_numbers = []
    cols = st.columns(6)
    
    for i in range(6):
        user_numbers.append(cols[i].number_input(f"번호 {i+1}", min_value=1, max_value=45, step=1, value=i+1))
    
    if st.button("내 번호 분석하기"):
        # 중복 체크
        if len(set(user_numbers)) != 6:
            st.error("중복된 번호가 있습니다. 모든 번호는 서로 달라야 합니다.")
        else:
            # 번호 정렬
            user_numbers.sort()
            
            # 번호 표시
            numbers_html = render_lotto_balls(user_numbers)
            st.markdown(numbers_html, unsafe_allow_html=True)
            
            # 번호 분석
            analysis = analyze_number_set(user_numbers)
            
            # 통계 분석
            col1, col2 = st.columns(2)
            
            with col1:
                # 홀짝 비율
                fig = px.pie(
                    values=[analysis['odd_even']['odd'], analysis['odd_even']['even']],
                    names=['홀수', '짝수'],
                    color=['홀수', '짝수'],
                    color_discrete_map={'홀수': '#FF6666', '짝수': '#66B2FF'},
                    title="홀수 vs 짝수 비율"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # 번호 범위 분포
                fig = px.bar(
                    x=list(analysis['ranges'].keys()),
                    y=list(analysis['ranges'].values()),
                    color=list(analysis['ranges'].keys()),
                    color_discrete_map={k: c for k, c in zip(analysis['ranges'].keys(), ["#FFCC00", "#66B2FF", "#FF6666", "#999999", "#66CC66"])},
                    labels={'x': '번호 구간', 'y': '개수'},
                    title="번호 구간 분포"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # 선택한 번호의 출현 빈도 분석
            freq_df = st.session_state.data['frequency']
            selected_freq = freq_df[freq_df['number'].isin(user_numbers)]
            
            st.markdown("### 선택 번호의 최근 출현 빈도")
            
            fig = px.bar(
                selected_freq,
                x='number',
                y='frequency',
                color=[get_ball_color(num) for num in selected_freq['number']],
                color_discrete_map="identity",
                labels={'number': '로또 번호', 'frequency': '출현 횟수'},
                title="선택 번호의 출현 빈도"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 분석 요약
            avg_freq = selected_freq['frequency'].mean()
            all_avg_freq = freq_df['frequency'].mean()
            
            if avg_freq > all_avg_freq:
                st.success(f"선택하신 번호는 평균보다 {avg_freq/all_avg_freq:.1f}배 더 자주 출현했습니다.")
            else:
                st.warning(f"선택하신 번호는 평균보다 {all_avg_freq/avg_freq:.1f}배 덜 출현했습니다.")
    
    st.markdown("</div>", unsafe_allow_html=True)

# 푸터
st.markdown("---")
st.markdown("이 애플리케이션은 데이터 분석 및 시각화 연습을 위한 것으로, 실제 로또 당첨을 보장하지 않습니다.")
st.markdown("© 2025 로또 통계 분석 도구 | 개발자: Python & Streamlit 애호가")

# 로또 번호 생성 기능을 별도의 함수로 정의
def main():
    pass  # 이미 위에서 모든 기능이 구현되어 있음

if __name__ == "__main__":
    main()