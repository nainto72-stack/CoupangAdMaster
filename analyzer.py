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
        
        # 전문적인 용어로 진단
        leak_count = len(self.summary_df[(self.summary_df['l_imp'] == 0) & (self.summary_df['l_spend'] > 0)])
        no_conv_count = len(self.summary_df[(self.summary_df['orders'] == 0) & (self.summary_df['spend'] > 100)])
        
        briefing = f"현재 전체 ROAS는 {o['ROAS']:.1f}%로 [{status}] 상태입니다.\n"
        if leak_count > 0: 
            briefing += f"⚠️ 노출 없이 광고비만 지출되는 '노출 누수' 키워드가 {leak_count}개 발견되었습니다.\n"
        if no_conv_count > 0: 
            briefing += f"💸 클릭은 발생하나 주문이 없는 '전환 누수' 키워드가 {no_conv_count}개 있습니다.\n"
        
        advice = [
            {"subject": "📊 성과 진단 리포트", "meaning": f"광고비 {int(o['spend']):,}원 대비 {int(o['sales']):,}원의 매출을 기록 중입니다.", 
             "easy_story": "전반적인 광고 효율을 높이기 위해 저효율 키워드의 입찰가를 하향 조정하세요.", 
             "solution": ["ROAS 330% 미만 키워드 선별 관리", "노출/전환 누수 키워드 일시 중단 검토"]}
        ]
        return {'status': status, 'avg_metrics': o, 'advice': advice, 'briefing': briefing}
