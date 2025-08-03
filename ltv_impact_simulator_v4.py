#!/usr/bin/env python3
"""
[v4.0] 아키타입 유입에 따른 LTV 임팩트 시뮬레이터
목표: 사용자가 직접 아키타입별 신규 유입 셀러 수를 조절하며, 그 결정이 5년간의 누적 매출(LTV)에 미치는 영향을 실시간으로 시뮬레이션
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# 페이지 설정
st.set_page_config(
    page_title="LTV 임팩트 시뮬레이터",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 커스텀 CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
        color: #1f77b4;
    }
    .control-panel {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 15px;
        border: 2px solid #e9ecef;
        margin-bottom: 2rem;
    }
    .result-panel {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .archetype-input {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 5px solid;
    }
    .born-input { border-left-color: #2E86AB; }
    .grown-input { border-left-color: #A23B72; }
    .struggle-input { border-left-color: #F18F01; }
    .fail-input { border-left-color: #C73E1D; }
</style>
""", unsafe_allow_html=True)

# 아키타입별 파라미터 정의 (실제 데이터 기반)
ARCHETYPE_PARAMS = {
    'Born Successful': {
        'initial_monthly_revenue': 2029.95,  # 실제 평균 월 매출
        'monthly_growth_rate': 0.05,        # 실제 월 성장률
        'monthly_churn_rate': 0.0704,       # 실제 월 이탈률
        'subscription_fee': 52.28,          # 실제 평균 구독료
        'color': '#2E86AB',
        'description': '🏆 타고난 성공형'
    },
    'Grown Successful': {
        'initial_monthly_revenue': 257.42,   # 실제 평균 월 매출
        'monthly_growth_rate': 0.05,        # 실제 월 성장률
        'monthly_churn_rate': 0.15,         # 실제 월 이탈률
        'subscription_fee': 49.0,           # 실제 평균 구독료
        'color': '#A23B72',
        'description': '📈 성장한 성공형'
    },
    'Struggling': {
        'initial_monthly_revenue': 576.49,   # 실제 평균 월 매출
        'monthly_growth_rate': 0.05,        # 실제 월 성장률
        'monthly_churn_rate': 0.15,         # 실제 월 이탈률
        'subscription_fee': 49.23,          # 실제 평균 구독료
        'color': '#F18F01',
        'description': '⚠️ 고군분투형'
    },
    'Failed': {
        'initial_monthly_revenue': 405.39,   # 실제 평균 월 매출
        'monthly_growth_rate': 0.05,        # 실제 월 성장률
        'monthly_churn_rate': 0.15,         # 실제 월 이탈률
        'subscription_fee': 49.30,          # 실제 평균 구독료
        'color': '#C73E1D',
        'description': '❌ 실패형'
    }
}

def simulate_archetype_ltv(archetype, seller_count, months=60):
    """특정 아키타입의 셀러들에 대한 LTV를 시뮬레이션합니다."""
    if seller_count == 0:
        return [0] * (months // 12)
    
    params = ARCHETYPE_PARAMS[archetype]
    
    # 단일 셀러의 월별 LTV 계산
    single_seller_ltv = []
    survival_probability = 1.0
    cumulative_ltv = 0.0
    
    for month in range(1, months + 1):
        # 생존 확률 업데이트
        survival_probability *= (1 - params['monthly_churn_rate'])
        
        # 해당 월의 예상 구독료 수익
        monthly_subscription = params['subscription_fee'] * survival_probability
        cumulative_ltv += monthly_subscription
        
        # 연도별 데이터 저장
        if month % 12 == 0:
            single_seller_ltv.append(cumulative_ltv)
    
    # 셀러 수만큼 곱하기
    return [ltv * seller_count for ltv in single_seller_ltv]

def calculate_total_ltv(seller_counts):
    """모든 아키타입의 총 LTV를 계산합니다."""
    total_ltv_by_year = [0] * 5
    archetype_contributions = {}
    
    for archetype, count in seller_counts.items():
        archetype_ltv = simulate_archetype_ltv(archetype, count)
        archetype_contributions[archetype] = archetype_ltv[-1]  # 5년차 총 LTV
        
        for i in range(5):
            total_ltv_by_year[i] += archetype_ltv[i]
    
    return total_ltv_by_year, archetype_contributions

# 대시보드 제목
st.markdown('<h1 class="main-header">🎯 LTV 임팩트 시뮬레이터</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">아키타입별 셀러 유입 수를 조절하여 5년간의 매출 임팩트를 실시간으로 시뮬레이션하세요</p>', unsafe_allow_html=True)

# 레이아웃: 좌측 컨트롤 패널, 우측 결과 패널
col_left, col_right = st.columns([1, 2])

with col_left:
    st.markdown('<div class="control-panel">', unsafe_allow_html=True)
    st.markdown("### 🎛️ 시뮬레이션 컨트롤 패널")
    st.markdown("각 아키타입별로 유입시킬 셀러 수를 입력하세요:")
    
    # 아키타입별 입력 필드
    seller_counts = {}
    
    # Born Successful
    st.markdown('<div class="archetype-input born-input">', unsafe_allow_html=True)
    st.markdown("**🏆 Born Successful 셀러**")
    st.markdown("*높은 초기 매출, 낮은 이탈률, 안정적 성장*")
    seller_counts['Born Successful'] = st.number_input(
        "Born 셀러 수",
        min_value=0,
        max_value=5000,
        value=226,
        step=1,
        key="born_count"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Grown Successful
    st.markdown('<div class="archetype-input grown-input">', unsafe_allow_html=True)
    st.markdown("**📈 Grown Successful 셀러**")
    st.markdown("*낮은 초기 매출, 높은 성장률, 잠재력 높음*")
    seller_counts['Grown Successful'] = st.number_input(
        "Grown 셀러 수",
        min_value=0,
        max_value=5000,
        value=142,
        step=1,
        key="grown_count"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Struggling
    st.markdown('<div class="archetype-input struggle-input">', unsafe_allow_html=True)
    st.markdown("**⚠️ Struggling 셀러**")
    st.markdown("*중간 수준 매출, 불안정한 성장*")
    seller_counts['Struggling'] = st.number_input(
        "Struggling 셀러 수",
        min_value=0,
        max_value=5000,
        value=708,
        step=1,
        key="struggle_count"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Failed
    st.markdown('<div class="archetype-input fail-input">', unsafe_allow_html=True)
    st.markdown("**❌ Failed 셀러**")
    st.markdown("*낮은 매출, 높은 이탈률*")
    seller_counts['Failed'] = st.number_input(
        "Failed 셀러 수",
        min_value=0,
        max_value=5000,
        value=1901,
        step=1,
        key="fail_count"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 시뮬레이션 실행 (자동으로 실행됨)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 입력 요약
    total_sellers = sum(seller_counts.values())
    st.info(f"**총 입력 셀러 수: {total_sellers:,}명**")

with col_right:
    # 시뮬레이션 실행
    total_ltv_by_year, archetype_contributions = calculate_total_ltv(seller_counts)
    final_ltv = total_ltv_by_year[-1]
    
    # 핵심 결과 KPI
    st.markdown(f"""
    <div class="result-panel">
        <h2 style="margin: 0; color: white;">💰 5년 후 총 누적 매출</h2>
        <h1 style="margin: 0.5rem 0; font-size: 4rem; color: white;">R${final_ltv:,.0f}</h1>
        <p style="margin: 0; font-size: 1.2rem; opacity: 0.9;">입력된 셀러 조합의 예상 총 LTV</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 메인 차트: 누적 매출 성장 곡선
    st.subheader("📊 누적 매출 성장 곡선")
    
    # 차트 데이터 준비
    years = [1, 2, 3, 4, 5]
    year_labels = ['1Y', '2Y', '3Y', '4Y', '5Y']
    
    fig_main = go.Figure()
    
    # 총합 라인 추가
    fig_main.add_trace(go.Scatter(
        x=years,
        y=total_ltv_by_year,
        mode='lines+markers',
        name='총 누적 매출',
        line=dict(color='#1f77b4', width=6),
        marker=dict(size=12, color='#1f77b4'),
        hovertemplate='<b>총 누적 매출</b><br>' +
                     'Year: %{x}Y<br>' +
                     'LTV: R$%{y:,.0f}<br>' +
                     '<extra></extra>'
    ))
    
    # 차트 레이아웃
    fig_main.update_layout(
        title={
            'text': f'총 {total_sellers:,}명 셀러의 5년간 누적 매출 성장',
            'x': 0.5,
            'font': {'size': 18}
        },
        xaxis_title='연도',
        yaxis_title='누적 매출 (R$)',
        height=400,
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(
            tickmode='array',
            tickvals=years,
            ticktext=year_labels,
            showgrid=False,
            tickfont=dict(color='black', size=12)
        ),
        yaxis=dict(
            showgrid=False,
            tickformat=',.0f',
            tickfont=dict(color='black', size=12)
        )
    )
    
    st.plotly_chart(fig_main, use_container_width=True)
    
    # 서브 차트: LTV 기여도 비중 (도넛 차트)
    st.subheader("🍩 아키타입별 LTV 기여도 비중")
    
    # 기여도 데이터 준비 (0이 아닌 것만)
    contribution_data = []
    for archetype, contribution in archetype_contributions.items():
        if contribution > 0:
            contribution_data.append({
                'Archetype': ARCHETYPE_PARAMS[archetype]['description'],
                'Contribution': contribution,
                'Count': seller_counts[archetype]
            })
    
    if contribution_data:
        contribution_df = pd.DataFrame(contribution_data)
        
        fig_donut = px.pie(
            contribution_df,
            values='Contribution',
            names='Archetype',
            title="5년차 아키타입별 LTV 기여도",
            color='Archetype',
            color_discrete_map={
                '🏆 타고난 성공형': '#2E86AB',
                '📈 성장한 성공형': '#A23B72',
                '⚠️ 고군분투형': '#F18F01',
                '❌ 실패형': '#C73E1D'
            },
            hole=0.4
        )
        
        fig_donut.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>' +
                         'LTV: R$%{value:,.0f}<br>' +
                         '비중: %{percent}<br>' +
                         '<extra></extra>'
        )
        
        fig_donut.update_layout(
            height=400,
            showlegend=False,
            annotations=[dict(
                text=f'총 LTV<br>R${final_ltv:,.0f}',
                x=0.5, y=0.5,
                font_size=14,
                showarrow=False
            )]
        )
        
        st.plotly_chart(fig_donut, use_container_width=True)
    else:
        st.info("셀러를 입력하면 기여도 차트가 표시됩니다.")

# 하단: 상세 분석
st.header("📈 상세 분석")

col1, col2 = st.columns(2)

with col1:
    st.subheader("💡 시뮬레이션 인사이트")
    
    if total_sellers > 0:
        # 셀러당 평균 LTV
        avg_ltv_per_seller = final_ltv / total_sellers
        
        # 가장 효율적인 아키타입
        efficiency_data = []
        for archetype, contribution in archetype_contributions.items():
            count = seller_counts[archetype]
            if count > 0:
                efficiency = contribution / count
                efficiency_data.append((archetype, efficiency))
        
        if efficiency_data:
            efficiency_data.sort(key=lambda x: x[1], reverse=True)
            best_archetype = efficiency_data[0][0]
            best_efficiency = efficiency_data[0][1]
            
            st.success(f"""
            **핵심 인사이트:**
            - 셀러 1명당 평균 LTV: R${avg_ltv_per_seller:,.0f}
            - 가장 효율적인 아키타입: {ARCHETYPE_PARAMS[best_archetype]['description']}
            - 최고 효율 LTV: R${best_efficiency:,.0f}/명
            """)
            
            # 효율성 순위
            st.write("**아키타입별 효율성 순위:**")
            for i, (archetype, efficiency) in enumerate(efficiency_data, 1):
                count = seller_counts[archetype]
                st.write(f"{i}. {ARCHETYPE_PARAMS[archetype]['description']}: R${efficiency:,.0f}/명 ({count}명)")
    else:
        st.info("셀러를 입력하면 인사이트가 표시됩니다.")

with col2:
    st.subheader("🎯 최적화 제안")
    
    if total_sellers > 0:
        # 예산 효율성 분석
        st.write("**예산 효율성 분석:**")
        
        # Born vs Others 비교
        born_count = seller_counts['Born Successful']
        born_contribution = archetype_contributions['Born Successful']
        
        others_count = total_sellers - born_count
        others_contribution = final_ltv - born_contribution
        
        if born_count > 0 and others_count > 0:
            born_efficiency = born_contribution / born_count
            others_efficiency = others_contribution / others_count
            
            st.write(f"- Born 셀러 효율성: R${born_efficiency:,.0f}/명")
            st.write(f"- 기타 셀러 효율성: R${others_efficiency:,.0f}/명")
            
            if born_efficiency > others_efficiency:
                ratio = born_efficiency / others_efficiency
                st.warning(f"💡 Born 셀러가 {ratio:.1f}배 더 효율적입니다!")
        
        # 개선 제안
        st.write("**개선 제안:**")
        if seller_counts['Failed'] > 0:
            st.write("- Failed 셀러를 Born/Grown으로 전환 고려")
        if seller_counts['Struggling'] > seller_counts['Grown Successful']:
            st.write("- Struggling 셀러 일부를 Grown으로 육성")
        if seller_counts['Born Successful'] < 5:
            st.write("- Born 셀러 유치에 더 집중 필요")
    else:
        st.info("셀러를 입력하면 최적화 제안이 표시됩니다.")

with st.expander("📋 상세 시뮬레이션 데이터"):
    if total_sellers > 0:
        # 연도별 상세 데이터
        detail_data = []
        for i, year in enumerate([1, 2, 3, 4, 5]):
            detail_data.append({
                'Year': f'{year}Y',
                'Cumulative_LTV': f"R${total_ltv_by_year[i]:,.0f}",
                'Born_Contribution': f"R${simulate_archetype_ltv('Born Successful', seller_counts['Born Successful'])[i]:,.0f}",
                'Grown_Contribution': f"R${simulate_archetype_ltv('Grown Successful', seller_counts['Grown Successful'])[i]:,.0f}",
                'Struggling_Contribution': f"R${simulate_archetype_ltv('Struggling', seller_counts['Struggling'])[i]:,.0f}",
                'Failed_Contribution': f"R${simulate_archetype_ltv('Failed', seller_counts['Failed'])[i]:,.0f}"
            })
        
        detail_df = pd.DataFrame(detail_data)
        st.dataframe(detail_df, use_container_width=True)
    else:
        st.info("셀러를 입력하면 상세 데이터가 표시됩니다.")

# 푸터
st.markdown(
    """
    <div style='text-align: center; color: #666666;'>
        <p>LTV 임팩트 시뮬레이터 v4.0 | 
        실시간 시뮬레이션 | 
        <a href='https://github.com/your-repo' target='_blank'>GitHub</a></p>
    </div>
    """, 
    unsafe_allow_html=True
)