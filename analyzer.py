import pandas as pd
import numpy as np
import os
import re
from datetime import datetime

class CoupangAdAnalyzer:
    def __init__(self, file_path=None):
        self.file_path = file_path
        self.raw_df = None
        self.summary_df = None
        self.trend_df = None
        self.last_analysis_info = ""
        
    def load_data(self, file_path):
        self.file_path = file_path
        try:
            # 기본 로드
            df = pd.read_excel(file_path)
            # 헤더 위치 자동 탐색
            if any(k in " ".join([str(c) for c in df.columns]) for k in ['노출수', '클릭수', '광고비', '매출액']):
                self.raw_df = df
                return True
            
            for i in range(1, 15):
                temp_df = pd.read_excel(file_path, header=i)
                if any(k in " ".join([str(c) for c in temp_df.columns]) for k in ['노출수', '클릭수', '광고비', '매출액']):
                    self.raw_df = temp_df
                    return True
            
            self.raw_df = df
            return True
        except Exception as e:
            print(f"로드 오류: {e}")
            return False

    def _get_column_mapping(self, df):
        mapping = {
            'kw': None, 'imp': None, 'click': None, 'spend': None, 
            'sales': None, 'orders': None, 'rank': None, 'pname': None, 
            'date': None, 'region': None
        }
        sales_locked = False
        orders_locked = False
        for col in df.columns:
            c = str(col).replace(" ", "").replace("\n", "")
            # 키워드
            if ('키워드' in c or '검색어' in c) and '카테고리' not in c: 
                mapping['kw'] = col
            # 노출/클릭/광고비
            elif '노출수' in c: mapping['imp'] = col
            elif '클릭수' in c: mapping['click'] = col
            elif '광고비' in c or '지출' in c: mapping['spend'] = col
            # 매출액: '총 전환매출액(14일)'을 최우선, 상품명/옵션ID 제외
            elif ('전환매출' in c or '매출액' in c) and '상품명' not in c and 'ID' not in c and 'id' not in c and '옵션' not in c:
                if not sales_locked:
                    mapping['sales'] = col
                    if '총' in c and '14일' in c:
                        sales_locked = True  # 최우선 컬럼 확정
            # 주문수: '총 주문수(14일)'를 최우선
            elif '주문수' in c:
                if not orders_locked:
                    mapping['orders'] = col
                    if '총' in c and '14일' in c:
                        orders_locked = True
            # 상품명
            elif '상품명' in c and '매출' not in c and '전환' not in c: mapping['pname'] = col
            # 날짜
            elif ('날짜' in c or '일자' in c) and '캠페인' not in c: mapping['date'] = col
            # 노출영역
            elif '출력영역' in c or '노출지면' in c or '지면' in c: mapping['region'] = col
            # 순위
            elif '순위' in c: mapping['rank'] = col
            
        return mapping

    def parse_date_robust(self, val):
        if pd.isna(val): return None
        s = str(val).strip()
        if len(s) == 8 and s.isdigit():
            try: return datetime.strptime(s, '%Y%m%d')
            except: pass
        for fmt in ['%Y.%m.%d', '%Y-%m-%d', '%Y/%m/%d']:
            try: return datetime.strptime(s, fmt)
            except: pass
        try: return pd.to_datetime(val)
        except: return None

    def process(self):
        if self.raw_df is None: return None
        df = self.raw_df.copy()
        m = self._get_column_mapping(df)
        
        # 키워드가 '-' 이거나 비어있는 경우, 노출 영역(지면)명으로 대체하여 분리 집계되도록 함
        if m['kw'] and m['region']:
            df[m['kw']] = np.where(
                (df[m['kw']].astype(str).str.strip() == '-') | (df[m['kw']].isna()),
                df[m['region']],
                df[m['kw']]
            )

        num_cols = ['imp', 'click', 'spend', 'sales', 'orders']
        for k in num_cols:
            c = m[k]
            if c:
                df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', '').str.replace('₩', '').str.replace('원', ''), errors='coerce').fillna(0)
            else:
                df[f'tmp_{k}'] = 0
                m[k] = f'tmp_{k}'

        if m['rank']:
            df[m['rank']] = pd.to_numeric(df[m['rank']].astype(str).str.replace('위', ''), errors='coerce').fillna(0)

        if m['date']:
            df['p_date'] = df[m['date']].apply(self.parse_date_robust)
            df_c = df.dropna(subset=['p_date']).copy()
            active_dates = sorted(df_c[df_c[m['imp']] > 0]['p_date'].unique(), reverse=True)
            
            if active_dates:
                l_date = active_dates[0]
                l_df = df_c[df_c['p_date'] == l_date]
                
                agg_dict = {m['imp']: 'sum', m['click']: 'sum', m['spend']: 'sum', m['sales']: 'sum', m['orders']: 'sum'}
                if m['rank']: agg_dict[m['rank']] = 'mean'
                if m['pname']: agg_dict[m['pname']] = 'first'
                if m['region']: agg_dict[m['region']] = 'first'
                
                sum_df = df_c.groupby(m['kw']).agg(agg_dict).reset_index()
                rename_map = {m['kw']: 'kw', m['imp']: 'imp', m['click']: 'click', m['spend']: 'spend', m['sales']: 'sales', m['orders']: 'orders'}
                if m['rank']: rename_map[m['rank']] = 'rank'
                if m['pname']: rename_map[m['pname']] = 'pname'
                if m['region']: rename_map[m['region']] = 'region'
                sum_df.rename(columns=rename_map, inplace=True)
                
                l_sum = l_df.groupby(m['kw']).agg({m['imp']: 'sum', m['spend']: 'sum'}).reset_index()
                l_sum.columns = ['kw', 'l_imp', 'l_spend']
                sum_df = pd.merge(sum_df, l_sum, on='kw', how='left').fillna(0)
                
                if len(active_dates) > 1:
                    p_date = active_dates[1]
                    p_df = df_c[df_c['p_date'] == p_date]
                    p_sum = p_df.groupby(m['kw']).agg({m['imp']: 'sum', m['spend']: 'sum'}).reset_index()
                    p_sum.columns = ['kw', 'p_imp', 'p_spend']
                    sum_df = pd.merge(sum_df, p_sum, on='kw', how='left').fillna(0)
                    
                    def get_status_info(row):
                        if row['l_imp'] > 0 and row['p_imp'] == 0: return "신규"
                        if row['l_imp'] == 0 and row['p_imp'] > 0: return "중단"
                        return "유지"
                    
                    sum_df['status'] = sum_df.apply(get_status_info, axis=1)
                    sum_df['imp_diff'] = sum_df['l_imp'] - sum_df['p_imp']
                    sum_df['spend_diff'] = sum_df['l_spend'] - sum_df['p_spend']
                    self.last_analysis_info = f"{p_date.strftime('%m/%d')} ➔ {l_date.strftime('%m/%d')} 데이터 비교"
                else:
                    sum_df['status'], sum_df['imp_diff'], sum_df['spend_diff'] = "유지", 0, 0
                    sum_df['p_imp'], sum_df['p_spend'] = 0, 0
                    self.last_analysis_info = f"{l_date.strftime('%m/%d')} 기준 분석"
                
                sum_df['ROAS'] = np.where(sum_df['spend'] > 0, (sum_df['sales'] / sum_df['spend']) * 100, 0)
                sum_df['CTR'] = np.where(sum_df['imp'] > 0, (sum_df['click'] / sum_df['imp']) * 100, 0)
                sum_df['CPC'] = np.where(sum_df['click'] > 0, sum_df['spend'] / sum_df['click'], 0)
                sum_df['CVR'] = np.where(sum_df['click'] > 0, (sum_df['orders'] / sum_df['click']) * 100, 0)
                
                self.summary_df = sum_df
                
                tr = df_c.groupby('p_date').agg({m['imp']: 'sum', m['click']: 'sum', m['spend']: 'sum', m['sales']: 'sum', m['orders']: 'sum'}).reset_index()
                tr['date_s'] = tr['p_date'].dt.strftime('%m.%d')
                tr['ROAS'] = np.where(tr[m['spend']] > 0, (tr[m['sales']] / tr[m['spend']]) * 100, 0)
                tr['CTR'] = np.where(tr[m['imp']] > 0, (tr[m['click']] / tr[m['imp']]) * 100, 0)
                tr.rename(columns={m['imp']: 'imp', m['click']: 'click', m['spend']: 'spend', m['sales']: 'sales', m['orders']: 'orders'}, inplace=True)
                self.trend_df = tr.sort_values('p_date')
                
        return self.summary_df

    def get_overall_summary(self):
        if self.summary_df is None: return None
        s = self.summary_df
        t = {'spend': s['spend'].sum(), 'sales': s['sales'].sum(), 'orders': s['orders'].sum(), 'imp': s['imp'].sum(), 'click': s['click'].sum()}
        t['ROAS'] = (t['sales'] / t['spend'] * 100) if t['spend'] > 0 else 0
        t['CTR'] = (t['click'] / t['imp'] * 100) if t['imp'] > 0 else 0
        t['CVR'] = (t['orders'] / t['click'] * 100) if t['click'] > 0 else 0
        t['CPC'] = (t['spend'] / t['click']) if t['click'] > 0 else 0
        return t

    def get_daily_performance(self):
        if self.trend_df is None: return {'total': pd.DataFrame(), 'by_region': pd.DataFrame()}
        res = {'total': self.trend_df, 'by_region': pd.DataFrame()}
        if self.raw_df is not None:
            m = self._get_column_mapping(self.raw_df)
            if m['date'] and m['region']:
                df = self.raw_df.copy()
                df['date_s'] = df[m['date']].apply(self.parse_date_robust).dt.strftime('%m.%d')
                rt = df.groupby(['date_s', m['region']]).agg({m['spend']: 'sum', m['sales']: 'sum'}).reset_index()
                rt.columns = ['date_s', 'region', 'spend', 'sales']
                res['by_region'] = rt
        return res

    def get_region_summary(self):
        if self.raw_df is None: return pd.DataFrame()
        df = self.raw_df.copy()
        m = self._get_column_mapping(df)
        if not m['region']: return pd.DataFrame()
        for k in ['imp', 'click', 'spend', 'sales', 'orders']:
            if m[k]: df[m[k]] = pd.to_numeric(df[m[k]].astype(str).str.replace(',', '').str.replace('₩', '').str.replace('원', ''), errors='coerce').fillna(0)
        s = df.groupby(m['region']).agg({m['sales']: 'sum', m['spend']: 'sum', m['orders']: 'sum', m['click']: 'sum', m['imp']: 'sum'}).reset_index()
        s.columns = ['region', 'sales', 'spend', 'orders', 'click', 'imp']
        s['ROAS'] = np.where(s['spend'] > 0, (s['sales'] / s['spend']) * 100, 0)
        s['CTR'] = np.where(s['imp'] > 0, (s['click'] / s['imp']) * 100, 0)
        s['CVR'] = np.where(s['click'] > 0, (s['orders'] / s['click']) * 100, 0)
        s['CPC'] = np.where(s['click'] > 0, s['spend'] / s['click'], 0)
        return s

    def get_ai_diagnosis(self, memos=None):
        if self.summary_df is None: return None
        o = self.get_overall_summary()
        status = "안정"
        if o['ROAS'] < 330: status = "주의 (효율 저하)"
        elif o['ROAS'] > 500: status = "우수 (공격적 운용 권장)"
        
        leak_count = len(self.summary_df[(self.summary_df['l_imp'] == 0) & (self.summary_df['l_spend'] > 0)])
        no_conv_count = len(self.summary_df[(self.summary_df['orders'] == 0) & (self.summary_df['spend'] > 100)])
        
        profit = o['sales'] - o['spend']
        profit_text = f"통장에 돈이 척척 쌓이는 [+{int(profit):,}원] 흑자" if profit > 0 else f"쓴 광고비가 더 많아 [-{abs(int(profit)):,}원] 적자"
        
        briefing = (
            f"👑 [AI 최종 종합 판정 나침반]\n"
            f"쉽게 비유하자면, 현재 사장님의 광고는 "
            f"{'💪 [매우 튼튼하게 달리는 몸짱 체력왕]' if (o['ROAS'] >= 330 and profit > 0) else '🤒 [약간의 비타민 영양제와 처방이 필요한 감기 기운]' if profit > 0 else '🚨 [비상! 새는 구멍을 즉시 막아야 하는 긴급 환자]'} 상태입니다!\n"
            f"💰 현재 광고 지갑에서 용돈 {int(o['spend']):,}원을 꺼내 썼는데, 가게 매출로 {int(o['sales']):,}원을 벌어오며 "
            f"최종 결과는 {profit_text} 상태를 기록하고 있습니다. "
            f"평균 효율 점수(ROAS)는 업계 기준점(330%) 대비 {o['ROAS']:.1f}% 입니다."
        )
        if leak_count > 0 or no_conv_count > 0:
            briefing += "\n💡 [알림] "
            if leak_count > 0: briefing += f"안 보이고 돈만 나가는 구멍이 {leak_count}개 발견되었고, "
            if no_conv_count > 0: briefing += f"구경만 하고 아무도 안 산 구멍이 {no_conv_count}개 있어요. 아래 긴급 처방을 참고해 해결해 보세요!"

        advice = []
        
        # (1) 수익성 한눈에 보기
        p_meaning = f"총 광고비 {int(o['spend']):,}원 vs 총 매출 {int(o['sales']):,}원 → 순수익 {int(profit):,}원 기록 중."
        p_story = (
            "우와! 광고비 주머니보다 번 돈 주머니가 훨씬 커요! 쓴 돈보다 번 돈이 훨씬 많아서 통장에 돈이 척척 쌓이고 있어요! 최고예요!"
            if profit > 0 else
            "앗! 지금 쓴 돈 주머니가 벌어온 돈 주머니보다 무거워요. 번 돈보다 광고비로 새어나간 돈이 많아서 비상이에요! 밑 빠진 독에 물 붓기 상태가 되지 않게 얼른 점검해야 해요!"
        )
        advice.append({
            "subject": "💰 1. 수익성 한눈에 보기 (수익 주머니 비교)",
            "meaning": p_meaning,
            "easy_story": p_story,
            "solution": ["벌어들인 매출액 막대기가 광고비 막대기보다 무조건 우뚝 높게 서 있어야 성공하는 게임입니다!", 
                         f"현재 순수익 점수: {int(profit):,}원"]
        })
        
        # (2) TOP5 효자 키워드
        advice.append({
            "subject": "🏆 2. TOP5 효자 키워드 (우리 가게 일등공신)",
            "meaning": "매출을 가장 많이 견인하는 상위 키워드 분석 완료.",
            "easy_story": "이 키워드들은 사장님 가게의 '일등공신 우등생'들이에요! 반에서 공부 제일 잘하는 친구들처럼, 전체 매출의 대부분을 이 기특한 녀석들이 다 벌어다 주고 있어요!",
            "solution": ["일등공신 친구들에게 더 든든한 학비(광고비 예산)를 집중 지원해 주면 훨씬 더 큰돈을 효도하며 벌어올 거예요!",
                         "ROAS가 330%를 넘는 효자 키워드는 광고가 끊기지 않게 예산을 사수하세요."]
        })
        
        # (3) 핵심 KPI 건강도
        k_good_count = 0
        if o['ROAS'] >= 330: k_good_count += 1
        if o['CTR'] >= 0.5: k_good_count += 1
        if o['CVR'] >= 5.0: k_good_count += 1
        if o['CPC'] <= 600: k_good_count += 1
        
        k_story = (
            "완벽한 체력왕 상태! 4가지 건강검진 지표 중 대부분이 파란색(안전) 불빛을 반짝이고 있어요. 튼튼하게 달리는 중이니 걱정 없이 페달을 밟으셔도 됩니다!"
            if k_good_count >= 3 else
            "종합 비타민 처방 필요! 4가지 건강지표 중 일부에 빨간색 경고등이 켜졌어요. 유독 아픈 부위(비싼 클릭 단가나, 클릭해도 안 사는 이탈)를 콕 짚어 보충해 줘야 해요!"
        )
        advice.append({
            "subject": "⚡ 3. 광고 핵심 KPI 건강도 (광고 건강검진)",
            "meaning": f"4대 핵심 지표(ROAS/CTR/CVR/CPC) 중 양호 상태 지표 개수: {k_good_count}개/4개 중",
            "easy_story": k_story,
            "solution": [f"현재 지표: ROAS({o['ROAS']:.0f}%), CTR({o['CTR']:.2f}%), CVR({o['CVR']:.1f}%), CPC({int(o['CPC']):,}원)",
                         "초록색 게이지가 많을수록 건강한 체질이며, 노란색과 빨간색은 입찰가 조정이 급선무입니다."]
        })
        
        # (4) 영역별 광고 비중
        advice.append({
            "subject": "🍩 4. 노출 영역별 광고비 (전단지 돌리기 전략)",
            "meaning": "고객이 검색창에 쳐서 들어오는 검색 영역과 다른 외부 노출 영역의 비율 분석.",
            "easy_story": "징검다리 건너기 정공법! 고객들이 검색창에 직접 상품을 쳐서 들어오는 영리한 길목에 광고비를 가장 많이 쓰고 있어요. 헛걸음하는 고객이 적은 아주 안전하고 알짜배기 노출 전략이에요!",
            "solution": ["검색 영역의 광고비 비중을 안전하게 70% 이상 유지해 주는 것이 실속이 풍부합니다.",
                         "외부 오디언스 노출 비중이 너무 크다면 클릭당 가격(CPC)을 낮춰 방어막을 쳐야 합니다."]
        })
        
        # (5) 1. 매출 및 ROAS 추이
        r_story = (
            "와! 매출액(막대기)도 우뚝 높게 서 있고 동그라미 선(ROAS)도 하늘 위로 동시에 점프했어요! 효율과 덩치가 쌍둥이처럼 사이좋게 우상향하는 최고의 황금 비율 상태입니다!"
            if (o['ROAS'] >= 330) else
            "앗! 동그라미 선(ROAS)은 아래로 힘없이 떨어지는데 막대기(매출)만 억지로 높게 서 있어요. 이것은 내실 없이 광고비만 무리하게 부어 껍데기만 키우는 실속 없는 상태이니 주의하세요!"
        )
        advice.append({
            "subject": "📈 5. 매출 및 ROAS 추이 (매출액과 ROAS의 달리기 시합)",
            "meaning": f"현재 평균 ROAS {o['ROAS']:.1f}% 달성 중.",
            "easy_story": r_story,
            "solution": ["막대(매출)가 치솟을 때 선(ROAS)도 함께 위로 날아올라야 최고로 맛있고 실속 가득한 광고입니다.",
                         "ROAS 선이 꺾인다면 비효율 키워드가 섞여 있는지 키워드 탭에서 정렬하여 바로 잘라내세요."]
        })
        
        # (6) 2. 광고비 및 클릭 효율
        c_story = (
            "기적의 가성비 마술! 쓰는 광고비(막대기)는 점점 밑으로 낮아지는데, 구경하러 온 손님(클릭수 선)은 하늘 위로 높게 솟구쳤어요! 적은 용돈으로 최대 인기를 누리는 최고의 좋은 징조입니다!"
            if (o['CPC'] <= 450) else
            "앗! 광고비(막대기)는 우뚝 높게 서서 엄청난 돈이 나갔는데 상품을 구경하러 온 클릭 손님(선)은 바닥에 기어 다니고 있어요. 손님 유치 비용이 비싸다는 적신호이니 단가 조절이 급해요!"
        )
        advice.append({
            "subject": "📈 6. 광고비 및 클릭 효율 (돈 대비 손님 유치 가성비)",
            "meaning": f"평균 유입 단가(CPC)는 {int(o['CPC']):,}원 기록 중.",
            "easy_story": c_story,
            "solution": ["광고비(막대) 높이보다 클릭수(선)가 훨씬 더 높게 하늘을 찌르는 모습이 가성비 끝판왕의 자태입니다.",
                         "CPC(클릭단가)가 너무 치솟은 키워드는 입찰가를 낮춰서 막대기 높이를 깎아야 합니다."]
        })
        
        # (7) 3. CTR 및 CVR 분석
        ctr_cvr_story = "우리 상품이 얼마나 예쁜지 점수(첫인상 CTR 막대)와 얼마나 말을 잘하는지 점수(설득력 CVR 선)의 콜라보예요! 첫인상 막대기도 높고 말솜씨 선도 높이 솟아야 손님들이 신나서 카드를 긁게 됩니다!"
        advice.append({
            "subject": "📈 7. CTR 및 CVR 분석 (첫인상과 구매 말솜씨 점수)",
            "meaning": f"첫인상(CTR): {o['CTR']:.2f}% | 구매설득력(CVR): {o['CVR']:.1f}% 기록 중.",
            "easy_story": ctr_cvr_story,
            "solution": ["CTR 막대가 낮으면 대표 썸네일이나 가격을 더 예쁘게 성형해 줘야 하고,",
                         "CVR 선이 낮으면 상세페이지의 설명이나 고객 리뷰가 부족한 것이니 상품 설명을 보강해 줘야 합니다."]
        })
        
        # (8) 4. CPC 및 CPA
        cpc_cpa_story = "이 그래프는 막대기(유입 비용)와 선(결제 1건당 광고비)이 **최대한 바닥으로 낮게 납작하게 깔릴수록 무조건 이기는 게임**이에요! 막대기와 선이 위로 솟구치면 경쟁사 배만 불려주는 꼴이니 낮추세요!"
        advice.append({
            "subject": "📈 8. CPC 및 CPA (고객 1명 데려오고 물건 팔 때 드는 세금)",
            "meaning": f"1명 입장료(CPC): {int(o['CPC']):,}원 | 1건 판매비용(CPA): {int(np.where(o['orders']>0, o['spend']/o['orders'], 0)):,}원.",
            "easy_story": cpc_cpa_story,
            "solution": ["막대기(CPC)와 선(CPA)이 낮게 바닥을 기어 다닐 때가 헛돈 안 쓰고 순수익이 가장 꽉 찬 행복한 상태입니다.",
                         "CPA 선이 상품의 마진보다 높게 치솟았다면, 그 키워드는 파는 족족 적자이니 즉시 중단하십시오."]
        })
        
        # (9) 5. 클릭수 및 전환건수
        advice.append({
            "subject": "📈 9. 클릭수 및 전환건수 (구경꾼 대비 진짜 돈 낸 손님)",
            "meaning": f"구경꾼(클릭수): {int(o['click']):,}회 vs 진짜 결제한 손님(전환건수): {int(o['orders']):,}건.",
            "easy_story": "구경하러 온 손님 막대기(클릭) 대비 진짜 돈을 낸 주문 손님 선(전환건수)이 가파르게 하늘 높이 솟아야 해요! 구경꾼 막대기는 엄청 높은데 결제 선이 바닥에 있다면 상세페이지가 심심하다는 신호예요.",
            "solution": ["클릭수 막대기가 솟아오를 때, 전환건수 선도 춤추듯 가파르게 함께 우상향해야 최적의 광고 효율입니다.",
                         "클릭수만 많고 전환선이 정체된다면 낚시성 검색어 유입이 있는지 확인하고 걸러내세요."]
        })
        
        # (10) 6. 노출수 및 전환건수
        advice.append({
            "subject": "📈 10. 노출수 및 전환건수 (전단지 노출 대비 진짜 성적표)",
            "meaning": f"총 전단지 노출(노출수): {int(o['imp']):,}회 대비 최종 주문 전환: {int(o['orders']):,}건 달성.",
            "easy_story": "눈앞에 스쳐 지나간 광고 횟수 막대기(노출) 대비 진짜 결제한 손님 선(전환)이 꼿꼿한 고자세를 유지해야 최고예요! 노출 막대기는 산더미 같은데 구매 선이 0에 가깝다면 엉뚱한 동네에 전단지를 돌린 격이에요.",
            "solution": ["노출수(막대)의 압도적인 크기에 뒤처지지 않고 전환(선)이 동반 상승할 때 타겟팅이 아주 날카롭게 꽂힌 상태입니다.",
                         "노출만 잘 되고 전환이 안 나오면 상품 가격 매력도나 적합하지 않은 검색어 유입을 즉시 차단하세요."]
        })

        return {'status': status, 'avg_metrics': o, 'advice': advice, 'briefing': briefing}
