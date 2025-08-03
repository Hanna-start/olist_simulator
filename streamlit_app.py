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
        border: 1px solid #dee2e6;
    }
    .metric-card {
        background: rgba(255, 255, 255, 0.1);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem;
        backdrop-filter: blur(10px);
    }
    .stSlider > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)

# 아키타입별 LTV 데이터 (실제 분석 결과 기반)
ARCHETYPE_DATA = {
    'Rising_Star': {
        'name': '🌟 Rising Star',
        'description': '빠른 성장과 높은 수익성을 보이는 셀러',
        'avg_ltv': 15420.50,
        'growth_rate': 0.25,
        'retention_rate': 0.85,
        'color': '#FF6B6B'
    },
    'Steady_Performer': {
        'name': '📈 Steady Performer', 
        'description': '안정적이고 지속적인 성과를 내는 셀러',
        'avg_ltv': 8750.30,
        'growth_rate': 0.15,
        'retention_rate': 0.78,
        'color': '#4ECDC4'
    },
    'Struggling_Seller': {
        'name': '⚠️ Struggling Seller',
        'description': '어려움을 겪고 있지만 잠재력이 있는 셀러',
        'avg_ltv': 3250.80,
        'growth_rate': 0.08,
        'retention_rate': 0.45,
        'color': '#FFE66D'
    },
    'Underperformer': {
        'name': '📉 Underperformer',
        'description': '성과가 저조하고 개선이 필요한 셀러',
        'avg_ltv': 1180.20,
        'growth_rate': 0.02,
        'retention_rate': 0.25,
        'color': '#FF8E53'
    }
}

def calculate_ltv_impact(seller_counts):
    """아키타입별 셀러 수에 따른 5년 LTV 임팩트 계산"""
    total_impact = 0
    yearly_projections = []
    archetype_contributions = {}
    
    for archetype, count in seller_counts.items():
        if count > 0:
            data = ARCHETYPE_DATA[archetype]
            base_ltv = data['avg_ltv']
            growth_rate = data['growth_rate']
            retention_rate = data['retention_rate']
            
            # 5년간 누적 LTV 계산 (복리 성장 + 이탈률 고려)
            yearly_ltv = []
            remaining_sellers = count
            
            for year in range(1, 6):
                # 해당 연도 LTV = 기본 LTV * (1 + 성장률)^연도 * 잔존 셀러 수
                year_ltv = base_ltv * (1 + growth_rate) ** year * remaining_sellers
                yearly_ltv.append(year_ltv)
                
                # 다음 연도를 위한 잔존 셀러 수 계산
                remaining_sellers *= retention_rate
            
            archetype_contributions[archetype] = {
                'total': sum(yearly_ltv),
                'yearly': yearly_ltv,
                'name': data['name'],
                'color': data['color']
            }
            
            total_impact += sum(yearly_ltv)
    
    # 연도별 총합 계산
    for year in range(5):
        year_total = sum([contrib['yearly'][year] for contrib in archetype_contributions.values()])
        yearly_projections.append(year_total)
    
    return total_impact, yearly_projections, archetype_contributions

def create_ltv_projection_chart(yearly_projections, archetype_contributions):
    """5년 LTV 프로젝션 차트 생성"""
    fig = go.Figure()
    
    years = list(range(2025, 2030))
    
    # 아키타입별 스택 차트
    for archetype, contrib in archetype_contributions.items():
        fig.add_trace(go.Scatter(
            x=years,
            y=contrib['yearly'],
            mode='lines+markers',
            name=contrib['name'],
            line=dict(color=contrib['color'], width=3),
            marker=dict(size=8),
            hovertemplate=f"<b>{contrib['name']}</b><br>" +
                         "연도: %{x}<br>" +
                         "LTV: ₩%{y:,.0f}<br>" +
                         "<extra></extra>"
        ))
    
    # 총합 라인 추가
    fig.add_trace(go.Scatter(
        x=years,
        y=yearly_projections,
        mode='lines+markers',
        name='📊 총 LTV',
        line=dict(color='#2E86AB', width=4, dash='dash'),
        marker=dict(size=10, symbol='diamond'),
        hovertemplate="<b>총 LTV</b><br>" +
                     "연도: %{x}<br>" +
                     "총 LTV: ₩%{y:,.0f}<br>" +
                     "<extra></extra>"
    ))
    
    fig.update_layout(
        title={
            'text': '📈 5년간 LTV 프로젝션',
            'x': 0.5,
            'font': {'size': 24, 'color': '#2E86AB'}
        },
        xaxis_title='연도',
        yaxis_title='LTV (원)',
        hovermode='x unified',
        template='plotly_white',
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def create_archetype_contribution_chart(archetype_contributions):
    """아키타입별 기여도 파이 차트"""
    if not archetype_contributions:
        return None
        
    labels = [contrib['name'] for contrib in archetype_contributions.values()]
    values = [contrib['total'] for contrib in archetype_contributions.values()]
    colors = [contrib['color'] for contrib in archetype_contributions.values()]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker_colors=colors,
        textinfo='label+percent',
        textfont_size=12,
        hovertemplate="<b>%{label}</b><br>" +
                     "LTV: ₩%{value:,.0f}<br>" +
                     "비율: %{percent}<br>" +
                     "<extra></extra>"
    )])
    
    fig.update_layout(
        title={
            'text': '🎯 아키타입별 LTV 기여도',
            'x': 0.5,
            'font': {'size': 20, 'color': '#2E86AB'}
        },
        height=400,
        template='plotly_white'
    )
    
    return fig

def main():
    # 메인 헤더
    st.markdown('<div class="main-header">🎯 LTV 임팩트 시뮬레이터 v4.0</div>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666; margin-bottom: 2rem;">아키타입별 셀러 유입이 5년간 매출에 미치는 영향을 실시간으로 시뮬레이션하세요</p>', unsafe_allow_html=True)
    
    # 레이아웃 설정
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown('<div class="control-panel">', unsafe_allow_html=True)
        st.markdown("### 🎛️ 셀러 유입 시뮬레이션")
        st.markdown("각 아키타입별로 신규 유입될 셀러 수를 설정하세요:")
        
        seller_counts = {}
        
        for archetype, data in ARCHETYPE_DATA.items():
            st.markdown(f'<div class="archetype-input">', unsafe_allow_html=True)
            st.markdown(f"**{data['name']}**")
            st.markdown(f"<small>{data['description']}</small>", unsafe_allow_html=True)
            st.markdown(f"<small>평균 LTV: ₩{data['avg_ltv']:,.0f}</small>", unsafe_allow_html=True)
            
            seller_counts[archetype] = st.slider(
                f"셀러 수",
                min_value=0,
                max_value=1000,
                value=0,
                step=10,
                key=f"slider_{archetype}",
                help=f"이 아키타입의 신규 셀러 유입 수를 설정하세요"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 총 셀러 수 표시
        total_sellers = sum(seller_counts.values())
        st.info(f"📊 **총 신규 셀러 수**: {total_sellers:,}명")
    
    with col2:
        if total_sellers > 0:
            # LTV 임팩트 계산
            total_impact, yearly_projections, archetype_contributions = calculate_ltv_impact(seller_counts)
            
            # 결과 패널
            st.markdown('<div class="result-panel">', unsafe_allow_html=True)
            st.markdown("### 💰 5년 누적 LTV 임팩트")
            st.markdown(f'<h1 style="font-size: 3rem; margin: 1rem 0;">₩{total_impact:,.0f}</h1>', unsafe_allow_html=True)
            
            # 메트릭 카드들
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.markdown("**연평균 매출**")
                st.markdown(f"₩{total_impact/5:,.0f}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col_b:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.markdown("**셀러당 평균 LTV**")
                st.markdown(f"₩{total_impact/total_sellers:,.0f}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col_c:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.markdown("**최고 수익 연도**")
                max_year_idx = yearly_projections.index(max(yearly_projections))
                st.markdown(f"{2025 + max_year_idx}년")
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 차트들
            st.plotly_chart(create_ltv_projection_chart(yearly_projections, archetype_contributions), use_container_width=True)
            
            # 아키타입별 기여도 차트
            contribution_chart = create_archetype_contribution_chart(archetype_contributions)
            if contribution_chart:
                st.plotly_chart(contribution_chart, use_container_width=True)
            
            # 상세 분석 테이블
            st.markdown("### 📋 상세 분석")
            
            analysis_data = []
            for archetype, count in seller_counts.items():
                if count > 0:
                    data = ARCHETYPE_DATA[archetype]
                    contrib = archetype_contributions[archetype]
                    analysis_data.append({
                        '아키타입': data['name'],
                        '셀러 수': f"{count:,}명",
                        '5년 총 LTV': f"₩{contrib['total']:,.0f}",
                        '셀러당 평균 LTV': f"₩{contrib['total']/count:,.0f}",
                        '전체 기여도': f"{contrib['total']/total_impact*100:.1f}%"
                    })
            
            if analysis_data:
                df_analysis = pd.DataFrame(analysis_data)
                st.dataframe(df_analysis, use_container_width=True, hide_index=True)
        
        else:
            st.markdown('<div class="result-panel">', unsafe_allow_html=True)
            st.markdown("### 🎯 시뮬레이션 시작")
            st.markdown("좌측 패널에서 아키타입별 셀러 수를 설정하면")
            st.markdown("실시간으로 LTV 임팩트가 계산됩니다!")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 아키타입 설명 카드
            st.markdown("### 📚 아키타입 가이드")
            for archetype, data in ARCHETYPE_DATA.items():
                with st.expander(f"{data['name']} - 평균 LTV: ₩{data['avg_ltv']:,.0f}"):
                    st.write(f"**설명**: {data['description']}")
                    st.write(f"**연간 성장률**: {data['growth_rate']*100:.0f}%")
                    st.write(f"**유지율**: {data['retention_rate']*100:.0f}%")
    
    # 푸터
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p>💡 <strong>사용 팁</strong>: 다양한 조합을 시도해보며 최적의 셀러 포트폴리오를 찾아보세요!</p>
        <p><small>데이터 기반: Olist 브라질 이커머스 플랫폼 실제 분석 결과</small></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()