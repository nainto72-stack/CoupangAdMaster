import customtkinter as ctk
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import threading
from datetime import datetime
import os
import json
from tkinter import filedialog, messagebox, ttk
import tkinter as tk
from analyzer import CoupangAdAnalyzer
import re
import traceback
import matplotlib.patheffects as path_effects

class AdOptimizerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        print(">>> 프로그램 초기화 시작...")
        self.title("쿠팡 광고 최적화 마스터 v2.0")
        self.geometry("1600x950")
        
        self.analyzer = CoupangAdAnalyzer()
        self.current_data = None
        self.memos = self._load_memos()
        self.keyword_classes = self._load_keyword_classes()
        
        self._init_context_menu()
        self._setup_ui()
        print(">>> UI 설정 완료.")
        
    def _setup_ui(self):
        ctk.set_appearance_mode("dark")
        self.configure(fg_color="#0B0B1A")
        
        self.header_frame = ctk.CTkFrame(self, height=100, corner_radius=0, fg_color="#1A1A2E")
        self.header_frame.pack(fill="x")
        
        self.title_label = ctk.CTkLabel(self.header_frame, text="🚀 쿠팡 광고 최적화 마스터", 
                                        font=ctk.CTkFont(family="Malgun Gothic", size=32, weight="bold"))
        self.title_label.pack(side="left", padx=40, pady=25)
        
        self.btn_group = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.btn_group.pack(side="right", padx=30, pady=20)
        
        self.file_btn = ctk.CTkButton(self.btn_group, text="📂 엑셀 파일 불러오기", command=self._choose_file, 
                                       fg_color="#2563EB", hover_color="#1D4ED8", width=180, height=45, font=("Malgun Gothic", 14, "bold"))
        self.file_btn.pack(side="right", padx=10)
        
        self.exec_btn = ctk.CTkButton(self.btn_group, text="▶ 분석 실행", command=self._execute_analysis, 
                                       fg_color="#059669", hover_color="#047857", width=140, height=45, font=("Malgun Gothic", 14, "bold"))
        self.exec_btn.pack(side="right", padx=10)
        
        self.filename_label = ctk.CTkLabel(self.btn_group, text="파일이 선택되지 않았습니다", font=("Malgun Gothic", 12), text_color="#AAAAAA")
        self.filename_label.pack(side="right", padx=20)

        self.status_panel = ctk.CTkFrame(self, corner_radius=0, fg_color="#1A1A2E")
        self.status_panel.pack(fill="x", pady=(5, 0))
        
        self.status_btn_container = ctk.CTkFrame(self.status_panel, fg_color="transparent")
        self.status_btn_container.pack(fill="x", padx=20, pady=(5, 5))
        
        self.btn_status_0 = ctk.CTkButton(self.status_btn_container, text="● 전환매출 0", fg_color="#F97316", corner_radius=8, height=55, font=("Malgun Gothic", 18, "bold"), command=lambda: self._filter_by_status("rev0"))
        self.btn_status_0.pack(side="left", expand=True, fill="x", padx=5)
        
        self.btn_status_low = ctk.CTkButton(self.status_btn_container, text="● ROAS 330% 미만", fg_color="#22C55E", corner_radius=8, height=55, font=("Malgun Gothic", 18, "bold"), command=lambda: self._filter_by_status("low_roas"))
        self.btn_status_low.pack(side="left", expand=True, fill="x", padx=5)
        
        self.btn_status_plus = ctk.CTkButton(self.status_btn_container, text="● 전환매출 0 초과", fg_color="#3B82F6", corner_radius=8, height=55, font=("Malgun Gothic", 18, "bold"), command=lambda: self._filter_by_status("rev_plus"))
        self.btn_status_plus.pack(side="left", expand=True, fill="x", padx=5)

        self.tabview = ctk.CTkTabview(self, corner_radius=0, fg_color="transparent")
        self.tabview._segmented_button.configure(font=("Malgun Gothic", 15, "bold"), selected_color="#2563EB", unselected_color="#1A1A2E", height=50)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=5)
        
        self.tab_dashboard = self.tabview.add("📊 광고요약 대시보드")
        self.tab_keywords = self.tabview.add("🔍 키워드 분석")
        self.tab_target = self.tabview.add("🎯 타겟 키워드 관리")
        self.tab_manual = self.tabview.add("⚙️ 수동 입찰가 관리")
        self.tab_exclude = self.tabview.add("🚫 제외 키워드 관리")
        self.tab_metrics = self.tabview.add("📈 성과 추이 (그래프)")
        self.tab_product_metrics = self.tabview.add("📦 상품별 성과 (그래프)")
        self.tab_memos = self.tabview.add("📝 일별 기록 / 메모")
        self.tab_diagnosis = self.tabview.add("🛡️ AI 전략 나침반")
        
        self._setup_dashboard_tab()
        self._setup_keyword_tab()
        self._setup_management_tab(self.tab_target, "타겟")
        self._setup_management_tab(self.tab_manual, "수동")
        self._setup_management_tab(self.tab_exclude, "제외")
        self._setup_metrics_tab()
        self._setup_product_metrics_tab()
        self._setup_memos_tab()
        self._setup_diagnosis_tab()
        
        self._refresh_management_tabs()
        
        self.status_label = ctk.CTkLabel(self, text="준비됨", anchor="w", padx=20, height=35, fg_color="#1A1A2E", font=("Malgun Gothic", 11))
        self.status_label.pack(fill="x", side="bottom")

    def _setup_dashboard_tab(self):
        self.dashboard_scroll = ctk.CTkScrollableFrame(self.tab_dashboard, fg_color="#0B0B1A")
        self.dashboard_scroll.pack(fill="both", expand=True)
        
        # 1. 성과 카드
        self._setup_performance_cards()
        
        # 2. 4분할 그래프 레이아웃 (2x2)
        self.chart_grid = ctk.CTkFrame(self.dashboard_scroll, fg_color="transparent")
        self.chart_grid.pack(fill="both", expand=True, padx=15, pady=10)
        self.chart_grid.grid_columnconfigure((0, 1), weight=1)
        self.chart_grid.grid_rowconfigure((0, 1), weight=1)
        
        self.chart_frame_tl = ctk.CTkFrame(self.chart_grid, height=450, fg_color="#0B0B1A", corner_radius=12, border_width=1, border_color="#1A3A4A")
        self.chart_frame_tl.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")
        self.chart_frame_tr = ctk.CTkFrame(self.chart_grid, height=450, fg_color="#0B0B1A", corner_radius=12, border_width=1, border_color="#3A1A1A")
        self.chart_frame_tr.grid(row=0, column=1, padx=8, pady=8, sticky="nsew")
        self.chart_frame_bl = ctk.CTkFrame(self.chart_grid, height=400, fg_color="#0B0B1A", corner_radius=12, border_width=1, border_color="#1A2A1A")
        self.chart_frame_bl.grid(row=1, column=0, padx=8, pady=8, sticky="nsew")
        self.chart_frame_br = ctk.CTkFrame(self.chart_grid, height=400, fg_color="#0B0B1A", corner_radius=12, border_width=1, border_color="#1A1A3A")
        self.chart_frame_br.grid(row=1, column=1, padx=8, pady=8, sticky="nsew")

        # 3. 하단 상세 요약 표
        self.summary_container = ctk.CTkFrame(self.dashboard_scroll, fg_color="#1A1A2E", corner_radius=15)
        self.summary_container.pack(fill="x", padx=15, pady=30)
        
        self.summary_label = ctk.CTkLabel(self.summary_container, text="📋 영역별 광고 성과 요약 (Summary)", font=("Malgun Gothic", 18, "bold"), text_color="#60A5FA")
        self.summary_label.pack(pady=(20, 10), padx=25, anchor="w")
        
        self.summary_frame = ctk.CTkFrame(self.summary_container, fg_color="transparent")
        self.summary_frame.pack(fill="x", padx=15, pady=15)
        
        self.s_cols = ("노출영역", "매출액", "광고비", "광고효율(ROAS)%", "주문건수", "클릭수", "노출수", "CTR%", "전환율%", "CPC")
        self.summary_tree = ttk.Treeview(self.summary_frame, columns=self.s_cols, show="headings", height=5)
        for col in self.s_cols:
            self.summary_tree.heading(col, text=col)
            self.summary_tree.column(col, anchor="center", width=130)
        self.summary_tree.pack(fill="x", expand=True)

    def _setup_performance_cards(self):
        self.perf_card_frame = ctk.CTkFrame(self.dashboard_scroll, fg_color="transparent")
        self.perf_card_frame.pack(fill="x", padx=15, pady=5)
        
        metrics = [
            ("전체 광고비", "spend", "원"), ("집행 광고비", "spend", "원"),
            ("전환 매출", "sales", "원"), ("전체 매출", "sales", "원"),
            ("전체 판매수", "orders", "회"), ("노출수", "imp", "회"),
            ("클릭수", "click", "회"), ("클릭률", "CTR", "%"),
            ("전환 판매수", "orders", "회"), ("전환 주문수", "orders", "회"),
            ("수익률(ROAS)", "ROAS", "%"), ("전환율(CVR)", "CVR", "%")
        ]
        
        self.perf_labels = {}
        for i, (t, k, u) in enumerate(metrics):
            r, c = divmod(i, 6)
            card = ctk.CTkFrame(self.perf_card_frame, fg_color="white", corner_radius=4)
            card.grid(row=r, column=c, padx=4, pady=4, sticky="nsew")
            self.perf_card_frame.grid_columnconfigure(c, weight=1)
            
            ctk.CTkLabel(card, text=t, font=("Malgun Gothic", 12), text_color="#4B5563").pack(pady=(10, 0))
            v_lbl = ctk.CTkLabel(card, text="-", font=("Consolas", 20, "bold"), text_color="#111827")
            v_lbl.pack(pady=(5, 10))
            self.perf_labels[i] = {"label": v_lbl, "unit": u, "key": k}

    def _setup_keyword_tab(self):
        self.action_frame = ctk.CTkFrame(self.tab_keywords, fg_color="transparent")
        self.action_frame.pack(fill="x", padx=20, pady=15)
        
        # 좌측: 필터 상태 라벨
        self.filter_label = ctk.CTkLabel(self.action_frame, text="", font=("Malgun Gothic", 15, "bold"), text_color="#60A5FA")
        self.filter_label.pack(side="left", padx=10)
        
        # 우측: 필터 해제 버튼
        self.btn_reset_filter = ctk.CTkButton(self.action_frame, text="🔄 필터 해제", command=self._reset_keyword_filter, 
                                              fg_color="#4B5563", width=120, height=35)
        self.btn_reset_filter.pack(side="right", padx=5)
        
        # 검색 프레임
        search_frame = ctk.CTkFrame(self.tab_keywords, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=(0, 8))
        
        ctk.CTkLabel(search_frame, text="🔍 키워드 검색:", font=("Malgun Gothic", 13, "bold"), 
                    text_color="#94A3B8").pack(side="left", padx=(0, 8))
        
        self.kw_search_var = tk.StringVar()
        self.kw_search_entry = ctk.CTkEntry(search_frame, textvariable=self.kw_search_var, 
                                            width=280, height=35, font=("Malgun Gothic", 13),
                                            placeholder_text="키워드를 입력하세요 (예: 두릅, 엄나무순)")
        self.kw_search_entry.pack(side="left", padx=(0, 8))
        self.kw_search_entry.bind("<Return>", lambda e: self._search_keywords())
        
        ctk.CTkButton(search_frame, text="검색", command=self._search_keywords,
                     fg_color="#3B82F6", hover_color="#2563EB", width=80, height=35,
                     font=("Malgun Gothic", 13, "bold")).pack(side="left", padx=(0, 5))
        
        ctk.CTkButton(search_frame, text="초기화", command=self._clear_keyword_search,
                     fg_color="#6B7280", hover_color="#4B5563", width=80, height=35,
                     font=("Malgun Gothic", 13)).pack(side="left", padx=(0, 5))
        
        # 검색 결과 라벨
        self.search_result_label = ctk.CTkLabel(search_frame, text="", font=("Malgun Gothic", 12), text_color="#F59E0B")
        self.search_result_label.pack(side="left", padx=15)
        
        self.kw_frame = ctk.CTkFrame(self.tab_keywords)
        self.kw_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.k_cols = ("구분", "키워드", "최신노출", "전일대비", "누적노출", "클릭수", "CTR%", "전환율%", "주문건수", 
                       "최신광고비", "지출변동", "누적광고비", "전환매출", "CPC", "ROAS", "광고순위", "상품명")
        
        # 트리뷰 + 스크롤바 프레임
        tree_container = ctk.CTkFrame(self.kw_frame, fg_color="transparent")
        tree_container.pack(fill="both", expand=True)
        
        self.kw_tree = ttk.Treeview(tree_container, columns=self.k_cols, show="headings", selectmode="extended")
        
        # 수직 스크롤바
        vsb = ttk.Scrollbar(tree_container, orient="vertical", command=self.kw_tree.yview)
        # 수평 스크롤바
        hsb = ttk.Scrollbar(tree_container, orient="horizontal", command=self.kw_tree.xview)
        self.kw_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.kw_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)
        
        # 컬럼 너비 설정 (모든 컬럼이 보이도록)
        col_widths = {
            "구분": 80, "키워드": 160, "최신노출": 85, "전일대비": 130, "누적노출": 85,
            "클릭수": 65, "CTR%": 65, "전환율%": 65, "주문건수": 65,
            "최신광고비": 90, "지출변동": 100, "누적광고비": 90, "전환매출": 90,
            "CPC": 70, "ROAS": 80, "광고순위": 70, "상품명": 350
        }
        for col in self.k_cols:
            self.kw_tree.heading(col, text=col, command=lambda _col=col: self._sort_by_column(_col, False))
            w = col_widths.get(col, 80)
            self.kw_tree.column(col, anchor="center", width=w, minwidth=50)
            
        self.kw_tree.bind("<Double-1>", self._on_kw_double_click)
        self.kw_tree.bind("<Button-3>", self._on_kw_right_click)
        
        self.kw_tree.tag_configure("tag_rev0", background="#F97316", foreground="white")
        self.kw_tree.tag_configure("tag_low_roas", background="#22C55E", foreground="white")
        self.kw_tree.tag_configure("tag_rev_plus", background="#3B82F6", foreground="white")

    def _setup_management_tab(self, tab, name):
        frame = ctk.CTkFrame(tab, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        lbl = ctk.CTkLabel(frame, text=f"📋 {name} 키워드 관리 리스트", font=("Malgun Gothic", 18, "bold"), text_color="#60A5FA")
        lbl.pack(anchor="w", pady=(0, 10))
        
        cols = ("키워드", "최초 등록일", "메모")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=15, selectmode="extended")
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, anchor="center", width=200 if c=="키워드" else 400 if c=="메모" else 150)
        tree.pack(fill="both", expand=True)
        tree.bind("<Button-3>", lambda e: self._on_management_right_click(e, tree, name))
        
        if not hasattr(self, 'mgmt_trees'): self.mgmt_trees = {}
        self.mgmt_trees[name] = tree

    def _setup_metrics_tab(self):
        self.metrics_scroll = ctk.CTkScrollableFrame(self.tab_metrics, fg_color="#0B0B1A")
        self.metrics_scroll.pack(fill="both", expand=True)

    def _setup_product_metrics_tab(self):
        # 상단 상품명 선택 바
        self.prod_filter_frame = ctk.CTkFrame(self.tab_product_metrics, height=75, fg_color="#1A1A2E", corner_radius=12)
        self.prod_filter_frame.pack(fill="x", padx=15, pady=(10, 5))
        
        ctk.CTkLabel(self.prod_filter_frame, text="📦 상품명 선택 (클릭하여 선택) :", 
                     font=("Malgun Gothic", 16, "bold"), text_color="#60A5FA").pack(side="left", padx=(25, 10), pady=18)
        
        # 상품 드롭다운 박스 (클릭하여 선택 가능)
        self.product_combobox = ctk.CTkComboBox(self.prod_filter_frame, width=550, height=38, 
                                                 font=("Malgun Gothic", 13), dropdown_font=("Malgun Gothic", 13), 
                                                 state="readonly", command=self._on_product_select)
        self.product_combobox.pack(side="left", padx=10, pady=18)
        self.product_combobox.set("데이터 분석을 먼저 진행해주세요.")
        
        # 차트 조회 버튼 (선택 사항 - 클릭으로 자동 로드되나 예비용)
        self.prod_search_btn = ctk.CTkButton(self.prod_filter_frame, text="📊 차트 조회", command=self._draw_product_charts, 
                                             fg_color="#2563EB", hover_color="#1D4ED8", width=120, height=38, font=("Malgun Gothic", 13, "bold"))
        self.prod_search_btn.pack(side="left", padx=15, pady=18)
        
        # 하단 스크롤 가능한 차트 뷰포트
        self.prod_metrics_scroll = ctk.CTkScrollableFrame(self.tab_product_metrics, fg_color="#0B0B1A")
        self.prod_metrics_scroll.pack(fill="both", expand=True, padx=15, pady=(5, 15))

    def _on_product_select(self, value):
        """드롭다운에서 상품명을 클릭하여 선택 시 자동으로 차트를 로딩"""
        self._draw_product_charts()

    def _update_product_combobox(self):
        """분석 완료 시점에 데이터에서 상품 리스트를 정렬 추출하여 콤보박스에 등록"""
        if self.analyzer.raw_df is None:
            self.product_combobox.configure(values=[])
            self.product_combobox.set("데이터 분석을 먼저 진행해주세요.")
            return
            
        m = self.analyzer._get_column_mapping(self.analyzer.raw_df)
        pname_col = m.get('pname')
        
        if pname_col and pname_col in self.analyzer.raw_df.columns:
            products = self.analyzer.raw_df[pname_col].dropna().unique().tolist()
            products = [str(p).strip() for p in products if str(p).strip() and str(p).strip() != '-']
            products = sorted(products)
            
            if products:
                self.product_combobox.configure(values=products)
                self.product_combobox.set(products[0])  # 기본값 첫 번째 상품 선택
                self._draw_product_charts()  # 즉각 첫 렌더링
            else:
                self.product_combobox.configure(values=[])
                self.product_combobox.set("엑셀에 추출된 상품명이 없습니다.")
        else:
            self.product_combobox.configure(values=[])
            self.product_combobox.set("상품명 컬럼을 찾을 수 없습니다.")

    def _draw_product_charts(self):
        """선택한 상품의 데이터로 기존 10대 차트를 필터링 렌더링"""
        for w in self.prod_metrics_scroll.winfo_children():
            w.destroy()
            
        if self.analyzer.raw_df is None:
            ctk.CTkLabel(self.prod_metrics_scroll, text="⚠️ 분석을 실행한 뒤 상품을 선택해주세요.", text_color="#EF4444", font=("Malgun Gothic", 14, "bold")).pack(pady=40)
            return
            
        selected = self.product_combobox.get()
        if not selected or selected in ["데이터 분석을 먼저 진행해주세요.", "엑셀에 추출된 상품명이 없습니다.", "상품명 컬럼을 찾을 수 없습니다."]:
            ctk.CTkLabel(self.prod_metrics_scroll, text="⚠️ 유효한 상품을 선택해주세요.", text_color="#EF4444", font=("Malgun Gothic", 14, "bold")).pack(pady=40)
            return
            
        m = self.analyzer._get_column_mapping(self.analyzer.raw_df)
        pname_col = m.get('pname')
        if not pname_col:
            ctk.CTkLabel(self.prod_metrics_scroll, text="⚠️ 상품명 매핑 정보를 찾을 수 없습니다.", text_color="#EF4444", font=("Malgun Gothic", 14, "bold")).pack(pady=40)
            return
            
        # 해당 상품에 해당하는 행 필터링
        raw_filtered = self.analyzer.raw_df[self.analyzer.raw_df[pname_col] == selected].copy()
        if raw_filtered.empty:
            ctk.CTkLabel(self.prod_metrics_scroll, text="⚠️ 해당 상품에 대한 데이터가 없습니다.", text_color="#EF4444", font=("Malgun Gothic", 14, "bold")).pack(pady=40)
            return
            
        try:
            # 서브 분석기 구동으로 데이터 구조화
            sub_analyzer = CoupangAdAnalyzer()
            sub_analyzer.raw_df = raw_filtered
            sub_analyzer.process()
            
            if sub_analyzer.trend_df is not None and not sub_analyzer.trend_df.empty:
                df = sub_analyzer.trend_df
                kw_data = sub_analyzer.summary_df
                
                # 공용 10대 차트 렌더러 호출
                self._render_large_trend_chart(df, kw_data, self.prod_metrics_scroll)
            else:
                ctk.CTkLabel(self.prod_metrics_scroll, text="⚠️ 해당 상품의 일별 추이 데이터를 추출할 수 없습니다.", text_color="#EF4444", font=("Malgun Gothic", 14, "bold")).pack(pady=40)
        except Exception as e:
            import traceback; traceback.print_exc()
            ctk.CTkLabel(self.prod_metrics_scroll, text=f"⚠️ 상품 차트 렌더링 오류: {e}", text_color="#EF4444", font=("Malgun Gothic", 12)).pack(pady=20)

    def _setup_memos_tab(self):
        self.memo_frame = ctk.CTkFrame(self.tab_memos, fg_color="transparent")
        self.memo_frame.pack(fill="both", expand=True, padx=30, pady=20)
        
        # 좌측: 메모 입력/수정 영역
        left = ctk.CTkFrame(self.memo_frame, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # 날짜 선택 행
        date_row = ctk.CTkFrame(left, fg_color="transparent")
        date_row.pack(fill="x", pady=(0, 5))
        
        ctk.CTkLabel(date_row, text="날짜:", font=("Malgun Gothic", 16, "bold"), 
                     text_color="#60A5FA").pack(side="left", padx=(0, 8))
        
        self.memo_date_var = ctk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.memo_date_entry = ctk.CTkEntry(date_row, textvariable=self.memo_date_var,
                                             width=160, height=36, font=("Malgun Gothic", 14),
                                             fg_color="#1A1A2E", text_color="white", border_color="#3B82F6")
        self.memo_date_entry.pack(side="left", padx=(0, 10))
        
        self.memo_edit_label = ctk.CTkLabel(date_row, text="[새 메모]", 
                                             font=("Malgun Gothic", 13), text_color="#10B981")
        self.memo_edit_label.pack(side="left")
        
        ctk.CTkLabel(left, text="광고 운영 기록을 남겨두세요. (입찰가 변경, 키워드 추가/삭제 등)", 
                     font=("Malgun Gothic", 13), text_color="#94A3B8").pack(anchor="w", pady=(5, 5))
        
        self.memo_input = ctk.CTkTextbox(left, height=300, font=("Malgun Gothic", 15), 
                                          fg_color="#1A1A2E", text_color="white", corner_radius=10)
        self.memo_input.pack(fill="both", expand=True, pady=5)
        
        # 오늘 메모 불러오기
        today_str = datetime.now().strftime("%Y-%m-%d")
        if today_str in self.memos:
            self.memo_input.insert("0.0", self.memos[today_str])
        
        btn_row = ctk.CTkFrame(left, fg_color="transparent")
        btn_row.pack(fill="x", pady=5)
        
        ctk.CTkButton(btn_row, text="저장", command=self._save_memo_by_date, 
                      fg_color="#059669", hover_color="#047857", height=45, width=200,
                      font=("Malgun Gothic", 15, "bold")).pack(side="left", padx=(0, 5))
        
        ctk.CTkButton(btn_row, text="새 메모", command=self._new_memo, 
                      fg_color="#2563EB", hover_color="#1D4ED8", height=45, width=120,
                      font=("Malgun Gothic", 14, "bold")).pack(side="left", padx=5)
        
        # 우측: 날짜별 기록 목록 (세로 정렬)
        right = ctk.CTkFrame(self.memo_frame, fg_color="#1A1A2E", corner_radius=15, width=400)
        right.pack(side="right", fill="both", padx=(10, 0))
        right.pack_propagate(False)
        
        ctk.CTkLabel(right, text="날짜별 기록 목록", font=("Malgun Gothic", 18, "bold"), 
                     text_color="#60A5FA").pack(pady=(20, 10), padx=15, anchor="w")
        
        self.memo_list_frame = ctk.CTkScrollableFrame(right, fg_color="transparent")
        self.memo_list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self._refresh_memo_list()

    def _refresh_memo_list(self):
        for w in self.memo_list_frame.winfo_children(): w.destroy()
        
        sorted_dates = sorted(self.memos.keys(), reverse=True)
        if not sorted_dates:
            ctk.CTkLabel(self.memo_list_frame, text="저장된 기록이 없습니다.", 
                         font=("Malgun Gothic", 13), text_color="#6B7280").pack(pady=20)
            return
        
        for date_str in sorted_dates:
            memo_text = self.memos[date_str]
            preview = memo_text[:35] + "..." if len(memo_text) > 35 else memo_text
            
            row = ctk.CTkFrame(self.memo_list_frame, fg_color="#0B0B1A", corner_radius=8)
            row.pack(fill="x", pady=4)
            
            # 날짜 + 미리보기
            ctk.CTkLabel(row, text=f"{date_str}", font=("Malgun Gothic", 14, "bold"), 
                         text_color="#F59E0B").pack(anchor="w", padx=12, pady=(8, 2))
            ctk.CTkLabel(row, text=preview, font=("Malgun Gothic", 11), 
                         text_color="#94A3B8", wraplength=340, justify="left").pack(anchor="w", padx=12, pady=(0, 4))
            
            # 버튼행
            btn_frame = ctk.CTkFrame(row, fg_color="transparent")
            btn_frame.pack(anchor="e", padx=10, pady=(0, 8))
            
            d = date_str
            ctk.CTkButton(btn_frame, text="수정", width=60, height=26, fg_color="#2563EB", 
                          font=("Malgun Gothic", 11), 
                          command=lambda d=d: self._edit_memo(d)).pack(side="left", padx=3)
            ctk.CTkButton(btn_frame, text="삭제", width=60, height=26, fg_color="#DC2626",
                          font=("Malgun Gothic", 11),
                          command=lambda d=d: self._delete_memo(d)).pack(side="left", padx=3)

    def _edit_memo(self, date_str):
        """기존 메모를 좌측 편집 영역에 불러오기 (수정 모드)"""
        if date_str in self.memos:
            self.memo_date_var.set(date_str)
            self.memo_input.delete("0.0", "end")
            self.memo_input.insert("0.0", self.memos[date_str])
            self.memo_edit_label.configure(text=f"[{date_str} 수정 중]", text_color="#F59E0B")

    def _load_memo(self, date_str):
        self._edit_memo(date_str)

    def _new_memo(self):
        """새 메모 작성 모드로 전환"""
        self.memo_date_var.set(datetime.now().strftime("%Y-%m-%d"))
        self.memo_input.delete("0.0", "end")
        self.memo_edit_label.configure(text="[새 메모]", text_color="#10B981")

    def _save_memo_by_date(self):
        """날짜 입력 기반 메모 저장"""
        memo = self.memo_input.get("0.0", "end").strip()
        date_str = self.memo_date_var.get().strip()
        if not date_str:
            messagebox.showwarning("알림", "날짜를 입력해주세요.")
            return
        if not memo:
            messagebox.showwarning("알림", "메모 내용을 입력해주세요.")
            return
        self.memos[date_str] = memo
        with open("ad_memos.json", "w", encoding="utf-8") as f:
            json.dump(self.memos, f, ensure_ascii=False, indent=4)
        self._refresh_memo_list()
        self.memo_edit_label.configure(text=f"[{date_str} 저장 완료]", text_color="#10B981")
        messagebox.showinfo("알림", f"{date_str} 기록이 저장되었습니다.")

    def _delete_memo(self, date_str):
        if date_str in self.memos:
            if messagebox.askyesno("확인", f"{date_str} 기록을 삭제하시겠습니까?"):
                del self.memos[date_str]
                with open("ad_memos.json", "w", encoding="utf-8") as f:
                    json.dump(self.memos, f, ensure_ascii=False, indent=4)
                self._refresh_memo_list()

    def _setup_diagnosis_tab(self):
        self.diag_scroll = ctk.CTkScrollableFrame(self.tab_diagnosis, fg_color="#0B0B1A")
        self.diag_scroll.pack(fill="both", expand=True)
        
        self.diag_title = ctk.CTkLabel(self.diag_scroll, text="🛡️ AI 전략 나침반", font=("Malgun Gothic", 28, "bold"), text_color="#60A5FA")
        self.diag_title.pack(pady=30)
        
        self.advice_container = ctk.CTkFrame(self.diag_scroll, fg_color="transparent")
        self.advice_container.pack(fill="both", expand=True, padx=50)

    def _execute_analysis(self):
        if not self.analyzer.file_path:
            messagebox.showwarning("경고", "엑셀 파일을 먼저 선택해주세요.")
            return
            
        self.exec_btn.configure(state="disabled", text="⏳ 분석 중...")
        self.status_label.configure(text="⏳ AI가 데이터를 정밀 분석하고 있습니다...")
        
        def run():
            try:
                if self.analyzer.load_data(self.analyzer.file_path):
                    data = self.analyzer.process()
                    self.after(0, lambda: self._refresh_ui(data))
                else:
                    self.after(0, lambda: messagebox.showerror("오류", "파일 형식이 올바르지 않습니다."))
            except Exception:
                err = traceback.format_exc()
                self.after(0, lambda: messagebox.showerror("분석 오류", f"데이터 분석 중 오류가 발생했습니다.\n\n{err}"))
            finally:
                self.after(0, lambda: self.exec_btn.configure(state="normal", text="▶ 분석 실행"))
                
        threading.Thread(target=run, daemon=True).start()

    def _refresh_ui(self, data):
        self.current_data = data
        self._populate_kw_tree(data)
        self._populate_summary_table()
        self._update_performance_cards()
        self._draw_all_charts()
        self._update_diagnosis()
        self._update_product_combobox()
        self.status_label.configure(text=f"✅ 분석 완료! ({self.analyzer.last_analysis_info})")

    def _populate_kw_tree(self, data):
        for item in self.kw_tree.get_children(): self.kw_tree.delete(item)
        if data is None: return
        
        for _, r in data.iterrows():
            tag = "tag_rev0" if r['sales'] == 0 else ("tag_low_roas" if r['ROAS'] < 330 else "tag_rev_plus")
            
            st = r.get('status', '유지')
            diff_v = int(r.get('imp_diff', 0))
            if st == "신규": diff_text = f"✨[신규] ▲{diff_v:,}"
            elif st == "중단": diff_text = f"🛑[중단] (전일:{int(r.get('p_imp',0)):,})"
            else:
                p_imp = int(r.get('p_imp', 0))
                pct = (diff_v / p_imp * 100) if p_imp > 0 else 0
                diff_text = f"▲{diff_v:,} (+{pct:.1f}%)" if diff_v > 0 else (f"▼{abs(diff_v):,} ({pct:.1f}%)" if diff_v < 0 else "-")
            
            sp_diff = int(r.get('spend_diff', 0))
            sp_diff_text = f"▲{sp_diff:,}" if sp_diff > 0 else (f"▼{abs(sp_diff):,}" if sp_diff < 0 else "-")
            
            vals = (
                r.get('region', '-'),
                r['kw'],
                f"{int(r.get('l_imp',0)):,}",
                diff_text,
                f"{int(r['imp']):,}",
                f"{int(r['click']):,}",
                f"{r['CTR']:.2f}%",
                f"{r['CVR']:.1f}%",
                f"{int(r['orders']):,}",
                f"{int(r.get('l_spend',0)):,}",
                sp_diff_text,
                f"{int(r['spend']):,}",
                f"{int(r['sales']):,}",
                f"{int(r['CPC']):,}",
                f"{r['ROAS']:.1f}%",
                f"{r.get('rank',0):.1f}위",
                r.get('pname', '-')
            )
            self.kw_tree.insert("", "end", values=vals, tags=(tag,))

    def _update_diagnosis(self):
        d = self.analyzer.get_ai_diagnosis()
        for w in self.advice_container.winfo_children(): w.destroy()
        if not d: return
        
        self.diag_title.configure(text=f"🛡️ AI 전략 나침반: [{d['status']}]")
        
        # 1. 👑 [최상단] AI 최종 종합 판정 대왕 썸머리 카드 생성
        summary_card = ctk.CTkFrame(self.advice_container, fg_color="#1E1E38", 
                                    border_width=2, border_color="#60A5FA", corner_radius=18)
        summary_card.pack(fill="x", pady=(10, 20))
        
        # 왕관 이모지와 함께 대왕 타이틀
        ctk.CTkLabel(summary_card, text="👑 AI 최종 종합 판정 (Summary)", 
                     font=("Malgun Gothic", 22, "bold"), text_color="#FBBF24").pack(anchor="w", padx=30, pady=(25, 10))
        
        # 종합 진단 본문 텍스트 (줄바꿈 wrap 처리 추가)
        ctk.CTkLabel(summary_card, text=d['briefing'], 
                     font=("Malgun Gothic", 15, "bold"), text_color="white", justify="left", wraplength=850).pack(anchor="w", padx=30, pady=(5, 25))
        
        # 2. [그 아래] 10개 차트 개별 진단 리포트 카드 자동 생성
        for adv in d['advice']:
            card = ctk.CTkFrame(self.advice_container, fg_color="#1A1A2E", corner_radius=15, 
                                border_width=1, border_color="#2E2E4A")
            card.pack(fill="x", pady=10)
            
            # 카드 타이틀
            ctk.CTkLabel(card, text=adv['subject'], font=("Malgun Gothic", 18, "bold"), 
                         text_color="#60A5FA").pack(anchor="w", padx=25, pady=(20, 8))
            
            # 💡 분석 영역 (wrap 처리)
            ctk.CTkLabel(card, text=f"💡 분석: {adv['meaning']}", font=("Malgun Gothic", 14, "bold"), 
                         text_color="#E2E8F0", justify="left", wraplength=850).pack(anchor="w", padx=25, pady=4)
            
            # 📖 전략 (초등생용 비유, wrap 처리)
            ctk.CTkLabel(card, text=f"📖 이렇게 보면 좋은 거 (초등생도 1초 이해!):\n   {adv['easy_story']}", 
                         font=("Malgun Gothic", 13), text_color="#A7F3D0", justify="left", wraplength=850).pack(anchor="w", padx=25, pady=4)
            
            # 🛠️ 세부 해결책 박스
            sol_frame = ctk.CTkFrame(card, fg_color="#0D0D21", corner_radius=10)
            sol_frame.pack(fill="x", padx=25, pady=(10, 20))
            for s in adv['solution']:
                ctk.CTkLabel(sol_frame, text=f"✔️ {s}", font=("Malgun Gothic", 13), 
                             text_color="#94A3B8", justify="left", wraplength=800).pack(anchor="w", padx=15, pady=4)

    def _draw_all_charts(self):
        # 모든 차트 프레임 초기화
        for f in [self.chart_frame_tl, self.chart_frame_tr, self.chart_frame_bl, self.chart_frame_br, self.metrics_scroll]:
            for w in f.winfo_children(): w.destroy()
            
        pd_data = self.analyzer.get_daily_performance()
        if not pd_data['total'].empty:
            df = pd_data['total']
            overall = self.analyzer.get_overall_summary()
            kw_data = self.analyzer.summary_df
            
            # 1. 대시보드 4분할 (성과추이와 겹치지 않는 고유 차트)
            for func, args, frame in [
                (self._render_dash_profit, (df, overall, self.chart_frame_tl), self.chart_frame_tl),
                (self._render_dash_top_keywords, (kw_data, self.chart_frame_tr), self.chart_frame_tr),
                (self._render_dash_kpi_gauge, (overall, self.chart_frame_bl), self.chart_frame_bl),
                (self._render_dashboard_pie, (pd_data['by_region'], self.chart_frame_br), self.chart_frame_br),
            ]:
                try:
                    func(*args)
                except Exception as e:
                    import traceback; traceback.print_exc()
                    ctk.CTkLabel(frame, text=f"⚠️ 차트 오류: {e}", text_color="#EF4444", 
                                font=("Malgun Gothic", 11)).pack(pady=20)
            
            # 2. 성과 추이 탭 전용 대형 10대 차트들 (5×2)
            try:
                self._render_large_trend_chart(df, kw_data, self.metrics_scroll)
            except Exception as e:
                import traceback; traceback.print_exc()
                ctk.CTkLabel(self.metrics_scroll, text=f"⚠️ 추이 차트 오류: {e}", text_color="#EF4444",
                            font=("Malgun Gothic", 11)).pack(pady=20)

    def _render_large_trend_chart(self, df, kw_data, master):
        plt.rcParams['font.family'] = 'Malgun Gothic'
        pe = [path_effects.withStroke(linewidth=2, foreground='black')]
        n = len(df)
        step = 3 if n > 10 else 2 if n > 5 else 1
        fs_title = 15; fs_guide = 8.5; fs_ann = 8; fs_label = 10; fs_tick = 8; fs_leg = 9
        ms = 4; lw = 2
        
        # 10대 차트 출력을 위해 높이를 32인치로 대폭 확장하여 5행 2열 레이아웃을 여유 있게 그립니다.
        fig = Figure(figsize=(18, 32), dpi=100)
        fig.patch.set_facecolor('#0B0B1A')
        
        def add_legend(ax, ax2):
            h1, l1 = ax.get_legend_handles_labels()
            h2, l2 = ax2.get_legend_handles_labels()
            ax.legend(h1+h2, l1+l2, loc='upper left', fontsize=fs_leg, 
                      facecolor='#1A1A2E', edgecolor='#333', labelcolor='white', framealpha=0.8)
        
        def setup_ax(ax):
            ax.set_facecolor('#0B0B1A')
            ax.tick_params(axis='x', labelcolor='#94A3B8', labelsize=fs_tick, rotation=35)
            ax.grid(True, axis='y', color='#1F2937', linestyle='--', alpha=0.4)
        
        # ─── 1. 광고비 vs 광고매출 [좌상 1] ───
        ax1 = fig.add_subplot(521); setup_ax(ax1)
        ax1.set_title("1. 광고비 vs 광고매출 추이", color='white', pad=65, loc='center', fontdict={'size': fs_title, 'weight': 'bold'})
        guide_str1 = (
            "용돈 지출[광고비 막대] = 순수 집행된 광고비   |   열매 수확[광고매출 선] = 광고로 창출한 매출\n"
            "☞ [적자 상태] 광고비 대비 매출 선이 너무 낮음 점검   |   ☞ [안전 구간] 매출 선이 광고비 막대보다 훨씬 높은 상태\n"
            "💡 [이렇게 보면 좋은 것?] 돈 봉투(광고비)는 얇고, 매출 바구니(광고매출)는 뚱뚱하게 솟아오르는 그림이 대정답!"
        )
        ax1.text(0.5, 1.02, guide_str1, transform=ax1.transAxes,
                ha='center', va='bottom', color='#A0AEC0', fontsize=fs_guide, style='normal', weight='bold',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#111122', edgecolor='#FF00FF', alpha=0.95))
        ax1.bar(df['date_s'], df['spend'], color='#EF4444', alpha=0.35, label='■ 광고비')
        ax1.set_ylabel('광고비 (원)', color='#EF4444', weight='bold', fontsize=fs_label)
        ax1.tick_params(axis='y', labelcolor='#EF4444', labelsize=fs_tick)
        
        ax1_2 = ax1.twinx()
        ax1_2.plot(df['date_s'], df['sales'], color='#00E5FF', marker='o', markersize=ms, linewidth=lw, 
                   label='— 광고매출액', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
        ax1_2.set_ylabel('광고매출액 (원)', color='#00E5FF', weight='bold', fontsize=fs_label)
        ax1_2.tick_params(axis='y', labelcolor='#00E5FF', labelsize=fs_tick)
        for i, v in enumerate(df['sales']):
            if v == 0: continue
            offset_y = -14 if i % 2 == 0 else 10
            ax1_2.annotate(self._fmt_val(v, 'won'), (df['date_s'].iloc[i], v), 
                           xytext=(0, offset_y), textcoords="offset points", ha='center', color='#00E5FF', 
                           weight='bold', fontsize=fs_ann, path_effects=pe)
        add_legend(ax1, ax1_2)

        # ─── 2. 클릭수 vs 광고매출 [우상 1] ───
        ax2 = fig.add_subplot(522); setup_ax(ax2)
        ax2.set_title("2. 클릭수 vs 광고매출 추이", color='white', pad=65, loc='center', fontdict={'size': fs_title, 'weight': 'bold'})
        guide_str2 = (
            "손님 입장[클릭수 막대] = 구경하러 들어온 고객 수   |   지갑 오픈[광고매출 선] = 실제 결제한 총 매출액\n"
            "☞ [구경만 함] 클릭은 높은데 매출 선이 바닥 점검   |   ☞ [알짜 손님] 적은 클릭으로도 높은 매출액 달성\n"
            "💡 [이렇게 보면 좋은 것?] 구경꾼(클릭)은 평이하더라도 벌어들인 돈(매출)이 구름 위로 솟아오르는 상황이 최상!"
        )
        ax2.text(0.5, 1.02, guide_str2, transform=ax2.transAxes,
                ha='center', va='bottom', color='#A0AEC0', fontsize=fs_guide, style='normal', weight='bold',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#111122', edgecolor='#FBBF24', alpha=0.95))
        ax2.bar(df['date_s'], df['click'], color='#F59E0B', alpha=0.35, label='■ 클릭수')
        ax2.set_ylabel('클릭수 (회)', color='#F59E0B', weight='bold', fontsize=fs_label)
        ax2.tick_params(axis='y', labelcolor='#F59E0B', labelsize=fs_tick)
        
        ax2_2 = ax2.twinx()
        ax2_2.plot(df['date_s'], df['sales'], color='#10B981', marker='^', linewidth=lw, markersize=ms,
                   label='— 광고매출액', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
        ax2_2.set_ylabel('광고매출액 (원)', color='#10B981', weight='bold', fontsize=fs_label)
        ax2_2.tick_params(axis='y', labelcolor='#10B981', labelsize=fs_tick)
        for i, v in enumerate(df['sales']):
            if v == 0: continue
            offset_y = -14 if i % 2 == 0 else 10
            ax2_2.annotate(self._fmt_val(v, 'won'), (df['date_s'].iloc[i], v), 
                           xytext=(0, offset_y), textcoords="offset points", ha='center', color='#10B981', 
                           weight='bold', fontsize=fs_ann, path_effects=pe)
        add_legend(ax2, ax2_2)

        # ─── 3. 광고비 vs ROAS [좌상 2] ───
        ax3 = fig.add_subplot(523); setup_ax(ax3)
        ax3.set_title("3. 광고비 vs ROAS 추이", color='white', pad=65, loc='center', fontdict={'size': fs_title, 'weight': 'bold'})
        guide_str3 = (
            "투자 비용[광고비 막대] = 광고 투자 원금   |   수익 효율[ROAS 선] = 투자 대비 회수 비율 (적정: 330%↑)\n"
            "☞ [예산 과다] 광고비를 증액할 때 ROAS 선이 꺾이는지 점검   |   ☞ [고효율 수성] 적은 예산으로 고ROAS 유지\n"
            "💡 [이렇게 보면 좋은 것?] 학비(광고비)는 아주 쬐끔 줬는데 성적표(ROAS)는 100점 만점으로 높이 나는 상태가 기적!"
        )
        ax3.text(0.5, 1.02, guide_str3, transform=ax3.transAxes,
                ha='center', va='bottom', color='#A0AEC0', fontsize=fs_guide, style='normal', weight='bold',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#111122', edgecolor='#EC4899', alpha=0.95))
        ax3.bar(df['date_s'], df['spend'], color='#EF4444', alpha=0.35, label='■ 광고비')
        ax3.set_ylabel('광고비 (원)', color='#EF4444', weight='bold', fontsize=fs_label)
        ax3.tick_params(axis='y', labelcolor='#EF4444', labelsize=fs_tick)
        
        ax3_2 = ax3.twinx()
        ax3_2.plot(df['date_s'], df['ROAS'], color='#FF00FF', marker='o', markersize=ms, linewidth=lw, 
                   label='— ROAS%', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
        ax3_2.set_ylabel('ROAS (%)', color='#FF00FF', weight='bold', fontsize=fs_label)
        ax3_2.tick_params(axis='y', labelcolor='#FF00FF', labelsize=fs_tick)
        for i, v in enumerate(df['ROAS']):
            if v == 0: continue
            offset_y = -14 if i % 2 == 0 else 10
            ax3_2.annotate(f"{v:.0f}%", (df['date_s'].iloc[i], v), 
                           xytext=(0, offset_y), textcoords="offset points", ha='center', color='#FF00FF', 
                           weight='bold', fontsize=fs_ann, path_effects=pe)
        add_legend(ax3, ax3_2)

        # ─── 4. 노출수 vs 클릭률(CTR) [우상 2] ───
        ax4 = fig.add_subplot(524); setup_ax(ax4)
        ax4.set_title("4. 노출수 vs 클릭률(CTR) 추이", color='white', pad=65, loc='center', fontdict={'size': fs_title, 'weight': 'bold'})
        guide_str4 = (
            "전단지 배포[노출수 막대] = 고객 눈앞 노출수   |   첫인상 매력[클릭률 선] = 호기심의 비율 (적정: 0.5%↑)\n"
            "☞ [눈길 안 줌] 노출은 많은데 클릭률 선이 바닥 점검   |   ☞ [썸네일 성공] 스치기만 해도 클릭하는 높은 매력\n"
            "💡 [이렇게 보면 좋은 것?] 전단지는 적게 돌렸는데 들어오는 비율(클릭률)이 하늘을 찌르는 알짜배기 형태!"
        )
        ax4.text(0.5, 1.02, guide_str4, transform=ax4.transAxes,
                ha='center', va='bottom', color='#A0AEC0', fontsize=fs_guide, style='normal', weight='bold',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#111122', edgecolor='#3B82F6', alpha=0.95))
        ax4.bar(df['date_s'], df['imp'], color='#60A5FA', alpha=0.35, label='■ 노출수')
        ax4.set_ylabel('노출수 (회)', color='#60A5FA', weight='bold', fontsize=fs_label)
        ax4.tick_params(axis='y', labelcolor='#60A5FA', labelsize=fs_tick)
        
        ax4_2 = ax4.twinx()
        ax4_2.plot(df['date_s'], df['CTR'], color='#22C55E', marker='D', linewidth=lw, markersize=ms,
                   label='— CTR%', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
        ax4_2.set_ylabel('CTR (%)', color='#22C55E', weight='bold', fontsize=fs_label)
        ax4_2.tick_params(axis='y', labelcolor='#22C55E', labelsize=fs_tick)
        for i, v in enumerate(df['CTR']):
            if v == 0: continue
            offset_y = -14 if i % 2 == 0 else 10
            ax4_2.annotate(f"{v:.2f}%", (df['date_s'].iloc[i], v), 
                           xytext=(0, offset_y), textcoords="offset points", ha='center', color='#22C55E', 
                           weight='bold', fontsize=fs_ann, path_effects=pe)
        add_legend(ax4, ax4_2)

        # ─── 5. 클릭률(CTR) vs 전환율(CVR) [좌상 3] ───
        ax5 = fig.add_subplot(525); setup_ax(ax5)
        ax5.set_title("5. CTR 및 CVR 분석", color='white', pad=65, loc='center', fontdict={'size': fs_title, 'weight': 'bold'})
        guide_str5 = (
            "첫인상 매력[CTR 막대] = 대표이미지/가격 매력도   |   설득력 성적[CVR 선] = 상세페이지/리뷰 신뢰도\n"
            "☞ [CTR 낮음] 대표이미지/상품명 개선 필요   |   ☞ [CVR 낮음] 상세페이지/혜택/리뷰 보완 필요\n"
            "💡 [이렇게 보면 좋은 것?] CTR(막대)도 높게 솟구쳐 있고 CVR(선)도 하늘 위로 높게 솟아올라 있을 때가 완벽한 상황!"
        )
        ax5.text(0.5, 1.02, guide_str5, transform=ax5.transAxes,
                ha='center', va='bottom', color='#A0AEC0', fontsize=fs_guide, style='normal', weight='bold',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#111122', edgecolor='#10B981', alpha=0.95))
        ax5.bar(df['date_s'], df['CTR'], color='#10B981', alpha=0.35, label='■ CTR%')
        ax5.set_ylabel('CTR (%)', color='#10B981', weight='bold', fontsize=fs_label)
        ax5.tick_params(axis='y', labelcolor='#10B981', labelsize=fs_tick)
        
        ax5_2 = ax5.twinx()
        cvr = np.where(df['click'] > 0, (df['orders'] / df['click']) * 100, 0)
        ax5_2.plot(df['date_s'], cvr, color='#6366F1', marker='s', linewidth=lw, markersize=ms,
                   label='— CVR%', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
        ax5_2.set_ylabel('CVR (%)', color='#6366F1', weight='bold', fontsize=fs_label)
        ax5_2.tick_params(axis='y', labelcolor='#6366F1', labelsize=fs_tick)
        for i, v in enumerate(cvr):
            if v == 0: continue
            offset_y = -14 if i % 2 == 0 else 10
            ax5_2.annotate(f"{v:.1f}%", (df['date_s'].iloc[i], v), 
                           xytext=(0, offset_y), textcoords="offset points", ha='center', color='#6366F1', 
                           weight='bold', fontsize=fs_ann, path_effects=pe)
        add_legend(ax5, ax5_2)

        # ─── 6. CPC vs ROAS [우상 3] ───
        ax6 = fig.add_subplot(526); setup_ax(ax6)
        ax6.set_title("6. CPC vs ROAS 추이", color='white', pad=65, loc='center', fontdict={'size': fs_title, 'weight': 'bold'})
        guide_str6 = (
            "입장 단가[CPC 막대] = 클릭당 나가는 평균 비용   |   수익 효율[ROAS 선] = 최종 광고 마진 비율\n"
            "☞ [수익 갉아먹음] 경쟁 심화로 CPC 상승 시 ROAS 추락 점검   |   ☞ [저렴한 입장료] 낮은 CPC로 높은 ROAS\n"
            "💡 [이렇게 보면 좋은 것?] 입장료(CPC) 막대는 바닥에 납작 엎드리고, 효도 점수(ROAS)는 하늘 높이 솟구치는 자태!"
        )
        ax6.text(0.5, 1.02, guide_str6, transform=ax6.transAxes,
                ha='center', va='bottom', color='#A0AEC0', fontsize=fs_guide, style='normal', weight='bold',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#111122', edgecolor='#8B5CF6', alpha=0.95))
        cpc = np.where(df['click'] > 0, df['spend'] / df['click'], 0)
        ax6.bar(df['date_s'], cpc, color='#EC4899', alpha=0.35, label='■ CPC')
        ax6.set_ylabel('CPC (원)', color='#EC4899', weight='bold', fontsize=fs_label)
        ax6.tick_params(axis='y', labelcolor='#EC4899', labelsize=fs_tick)
        
        ax6_2 = ax6.twinx()
        ax6_2.plot(df['date_s'], df['ROAS'], color='#34D399', marker='o', markersize=ms, linewidth=lw,
                   label='— ROAS%', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
        ax6_2.set_ylabel('ROAS (%)', color='#34D399', weight='bold', fontsize=fs_label)
        ax6_2.tick_params(axis='y', labelcolor='#34D399', labelsize=fs_tick)
        for i, v in enumerate(df['ROAS']):
            if v == 0: continue
            offset_y = -14 if i % 2 == 0 else 10
            ax6_2.annotate(f"{v:.0f}%", (df['date_s'].iloc[i], v), 
                           xytext=(0, offset_y), textcoords="offset points", ha='center', color='#34D399', 
                           weight='bold', fontsize=fs_ann, path_effects=pe)
        add_legend(ax6, ax6_2)

        # ─── 7. 전환율(CVR) vs ROAS [좌상 4] ───
        ax7 = fig.add_subplot(527); setup_ax(ax7)
        ax7.set_title("7. 전환율(CVR) vs ROAS 추이", color='white', pad=65, loc='center', fontdict={'size': fs_title, 'weight': 'bold'})
        guide_str7 = (
            "구매 전환율[CVR 막대] = 구경꾼 대비 진짜 산 비율   |   수익률[ROAS 선] = 광고비 가성비 점수\n"
            "☞ [효율 동조] CVR이 상승할 때 ROAS도 우상향하는지 확인   |   ☞ [가성비 하락] 전환은 좋은데 마진 대비 예산 과다 점검\n"
            "💡 [이렇게 보면 좋은 것?] 들어와서 결제하는 비율(CVR) 막대도 높고, 광고비 가성비(ROAS) 선도 구름 위를 나는 상황!"
        )
        ax7.text(0.5, 1.02, guide_str7, transform=ax7.transAxes,
                ha='center', va='bottom', color='#A0AEC0', fontsize=fs_guide, style='normal', weight='bold',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#111122', edgecolor='#6366F1', alpha=0.95))
        ax7.bar(df['date_s'], cvr, color='#8B5CF6', alpha=0.35, label='■ CVR%')
        ax7.set_ylabel('CVR (%)', color='#8B5CF6', weight='bold', fontsize=fs_label)
        ax7.tick_params(axis='y', labelcolor='#8B5CF6', labelsize=fs_tick)
        
        ax7_2 = ax7.twinx()
        ax7_2.plot(df['date_s'], df['ROAS'], color='#FF00FF', marker='^', markersize=ms, linewidth=lw,
                   label='— ROAS%', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
        ax7_2.set_ylabel('ROAS (%)', color='#FF00FF', weight='bold', fontsize=fs_label)
        ax7_2.tick_params(axis='y', labelcolor='#FF00FF', labelsize=fs_tick)
        for i, v in enumerate(df['ROAS']):
            if v == 0: continue
            offset_y = -14 if i % 2 == 0 else 10
            ax7_2.annotate(f"{v:.0f}%", (df['date_s'].iloc[i], v), 
                           xytext=(0, offset_y), textcoords="offset points", ha='center', color='#FF00FF', 
                           weight='bold', fontsize=fs_ann, path_effects=pe)
        add_legend(ax7, ax7_2)

        # ─── 8. 날짜별 광고비·광고매출 추이 [우상 4] ───
        ax8 = fig.add_subplot(528); setup_ax(ax8)
        ax8.set_title("8. 날짜별 광고비·광고매출 추이", color='white', pad=65, loc='center', fontdict={'size': fs_title, 'weight': 'bold'})
        guide_str8 = (
            "매일 쓰는 돈[광고비 선] = 집행 광고비 추세   |   매일 버는 돈[광고매출 선] = 매출 발생 추세\n"
            "☞ [적자 구간] 쓴 돈 선이 번 돈 선보다 높이 올라감 점검   |   ☞ [흑자 공간] 두 선의 간격이 멀어질수록 순수익 증대\n"
            "💡 [이렇게 보면 좋은 것?] 광고비 선은 저 밑에 찰싹 붙어있고, 매출액 선은 독수리처럼 구름 위를 유유히 날아가는 모습!"
        )
        ax8.text(0.5, 1.02, guide_str8, transform=ax8.transAxes,
                ha='center', va='bottom', color='#A0AEC0', fontsize=fs_guide, style='normal', weight='bold',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#111122', edgecolor='#34D399', alpha=0.95))
        ax8.plot(df['date_s'], df['spend'], color='#EF4444', marker='s', markersize=ms, linewidth=lw, linestyle='--', label='— 광고비')
        ax8.plot(df['date_s'], df['sales'], color='#00E5FF', marker='o', markersize=ms, linewidth=lw+0.5, label='— 광고매출액', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
        ax8.set_ylabel('금액 (원)', color='white', weight='bold', fontsize=fs_label)
        ax8.tick_params(axis='y', labelcolor='#94A3B8', labelsize=fs_tick)
        for i, v in enumerate(df['sales']):
            if v == 0: continue
            offset_y = -14 if i % 2 == 0 else 10
            ax8.annotate(self._fmt_val(v, 'won'), (df['date_s'].iloc[i], v), 
                         xytext=(0, offset_y), textcoords="offset points", ha='center', color='#00E5FF', 
                         weight='bold', fontsize=fs_ann, path_effects=pe)
        ax8.legend(loc='upper left', fontsize=fs_leg, facecolor='#1A1A2E', edgecolor='#333', labelcolor='white', framealpha=0.8)

        # ─── 9. 날짜별 ROAS 추이 [좌상 5] ───
        ax9 = fig.add_subplot(529); setup_ax(ax9)
        ax9.set_title("9. 날짜별 ROAS 추이", color='white', pad=65, loc='center', fontdict={'size': fs_title, 'weight': 'bold'})
        guide_str9 = (
            "가성비 맥박수[ROAS 선] = 일별 광고 수익 효율   |   기준선[300%/330%] = 적자와 흑자의 생명선\n"
            "☞ [경고등 작동] ROAS 선이 주황 경계선(300%) 아래로 처짐 점검   |   ☞ [건강 상태] 안전선(330%) 위에서 활기차게 노는 상태\n"
            "💡 [이렇게 보면 좋은 것?] 하루도 빠짐없이 꺾은선그래프(ROAS)가 초록 안전선(330%) 위에서 힘차게 파도치는 형태!"
        )
        ax9.text(0.5, 1.02, guide_str9, transform=ax9.transAxes,
                ha='center', va='bottom', color='#A0AEC0', fontsize=fs_guide, style='normal', weight='bold',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#111122', edgecolor='#F59E0B', alpha=0.95))
        ax9.plot(df['date_s'], df['ROAS'], color='#FF00FF', marker='o', markersize=ms+1, linewidth=lw+0.5, label='— ROAS%', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
        ax9.axhline(y=300, color='#F59E0B', linestyle='--', linewidth=1.2, alpha=0.8, label='— 경계선(300%)')
        ax9.axhline(y=330, color='#10B981', linestyle='-', linewidth=1.2, alpha=0.8, label='— 안전선(330%)')
        ax9.set_ylabel('ROAS (%)', color='#FF00FF', weight='bold', fontsize=fs_label)
        ax9.tick_params(axis='y', labelcolor='#FF00FF', labelsize=fs_tick)
        for i, v in enumerate(df['ROAS']):
            if v == 0: continue
            offset_y = -14 if i % 2 == 0 else 10
            ax9.annotate(f"{v:.0f}%", (df['date_s'].iloc[i], v), 
                         xytext=(0, offset_y), textcoords="offset points", ha='center', color='#FF00FF', 
                         weight='bold', fontsize=fs_ann, path_effects=pe)
        ax9.legend(loc='upper left', fontsize=fs_leg, facecolor='#1A1A2E', edgecolor='#333', labelcolor='white', framealpha=0.8)

        # ─── 10. 키워드별 광고비 대비 전환수 [우상 5] ───
        ax10 = fig.add_subplot(5, 2, 10); ax10.set_facecolor('#0B0B1A')
        ax10.tick_params(axis='y', labelcolor='#94A3B8', labelsize=fs_tick)
        ax10.grid(True, axis='y', color='#1F2937', linestyle='--', alpha=0.4)
        ax10.set_title("10. 키워드별 광고비 대비 전환수", color='white', pad=65, loc='center', fontdict={'size': fs_title, 'weight': 'bold'})
        guide_str10 = (
            "우등생 색출[광고비 막대] = 키워드별 집행 비용   |   성적표[전환수 선] = 최종 주문(결제) 건수\n"
            "☞ [식충이 키워드] 밥(광고비)은 엄청 먹는데 성적(주문)은 바닥 점검   |   ☞ [소액 우등생] 돈은 쬐끔 쓰는데 주문은 듬뿍\n"
            "💡 [이렇게 보면 좋은 것?] 광고비(막대) 높이는 난쟁이 똥자루인데, 주문(선)은 거인처럼 우뚝 솟아있는 가성비 대왕 키워드 색출!"
        )
        ax10.text(0.5, 1.02, guide_str10, transform=ax10.transAxes,
                 ha='center', va='bottom', color='#A0AEC0', fontsize=fs_guide, style='normal', weight='bold',
                 bbox=dict(boxstyle='round,pad=0.4', facecolor='#111122', edgecolor='#FB923C', alpha=0.95))
        
        # 키워드 데이터 처리: 광고비 기준 상위 10개 키워드 추출
        if kw_data is not None and not kw_data.empty:
            top_kws = kw_data.sort_values('spend', ascending=False).head(10).copy()
            # 글자 길이가 길면 축약
            top_kws['kw_short'] = top_kws['kw'].apply(lambda x: x[:8] + '..' if len(str(x)) > 8 else x)
            
            x_kws = top_kws['kw_short'].tolist()
            ax10.bar(x_kws, top_kws['spend'], color='#EF4444', alpha=0.35, label='■ 광고비')
            ax10.set_ylabel('광고비 (원)', color='#EF4444', weight='bold', fontsize=fs_label)
            ax10.tick_params(axis='y', labelcolor='#EF4444', labelsize=fs_tick)
            ax10.tick_params(axis='x', labelcolor='white', labelsize=fs_tick, rotation=35)
            
            ax10_2 = ax10.twinx()
            ax10_2.plot(x_kws, top_kws['orders'], color='#10B981', marker='s', markersize=ms, linewidth=lw, label='— 주문수', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
            ax10_2.set_ylabel('주문수 (건)', color='#10B981', weight='bold', fontsize=fs_label)
            ax10_2.tick_params(axis='y', labelcolor='#10B981', labelsize=fs_tick)
            
            for i, v in enumerate(top_kws['orders']):
                if v == 0: continue
                ax10_2.annotate(f"{int(v)}건", (x_kws[i], v), xytext=(0, 10), textcoords="offset points", ha='center', color='#10B981', weight='bold', fontsize=fs_ann, path_effects=pe)
            add_legend(ax10, ax10_2)
        else:
            ax10.text(0.5, 0.5, "표시할 키워드 데이터가 없습니다.", transform=ax10.transAxes, ha='center', va='center', color='#94A3B8', fontsize=12)

        # ─── 모든 서브플롯에 메모 세로 점선 표시 (10번 차트는 키워드 축이므로 세로 메모 점선에서 제외) ───
        all_axes = [ax1, ax2, ax3, ax4, ax5, ax6, ax7, ax8, ax9]
        self._draw_memo_vlines(all_axes, df['date_s'].tolist(), pe, fs_ann)

        fig.subplots_adjust(left=0.06, right=0.94, top=0.96, bottom=0.04, hspace=0.35, wspace=0.35)
        canvas = FigureCanvasTkAgg(fig, master=master); canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        self._add_hover_tooltip(fig, canvas)

    def _add_hover_tooltip(self, fig, canvas):
        """모든 서브플롯에 마우스 호버 툴팁을 추가"""
        annots = {}
        for ax in fig.get_axes():
            annot = ax.annotate("", xy=(0, 0), xytext=(20, 20),
                               textcoords="offset points",
                               bbox=dict(boxstyle="round,pad=0.5", fc="#1E293B", ec="#60A5FA", lw=1.5, alpha=0.95),
                               fontsize=11, color="white", fontfamily="Malgun Gothic", fontweight="bold",
                               arrowprops=dict(arrowstyle="->", color="#60A5FA", lw=1.5),
                               zorder=999)
            annot.set_visible(False)
            annots[ax] = annot

        def _get_clean_label(chk_ax, bar, lbl, is_horiz):
            # 시스템 기본 컨테이너 명칭이거나 비어있는 경우 한글 틱 라벨에서 추적
            if not lbl or '_container' in lbl or lbl.startswith('_'):
                try:
                    if is_horiz:
                        # 가로 막대: Y축 라벨에서 키워드명 가져오기
                        y_val = bar.get_y() + bar.get_height() / 2
                        ticks = chk_ax.get_yticks()
                        tick_labels = [t.get_text() for t in chk_ax.get_yticklabels()]
                        if len(ticks) == len(tick_labels) and len(ticks) > 0:
                            idx = np.argmin([abs(t - y_val) for t in ticks])
                            cand = tick_labels[idx].replace('..', '').strip()
                            if cand: return cand
                    else:
                        # 세로 막대: X축 라벨에서 지면명/지표명 가져오기
                        x_val = bar.get_x() + bar.get_width() / 2
                        ticks = chk_ax.get_xticks()
                        tick_labels = [t.get_text() for t in chk_ax.get_xticklabels()]
                        if len(ticks) == len(tick_labels) and len(ticks) > 0:
                            idx = np.argmin([abs(t - x_val) for t in ticks])
                            cand = tick_labels[idx].replace('..', '').strip()
                            if cand: return cand
                except Exception as e:
                    pass
            
            if lbl:
                lbl = lbl.replace('■ ', '').replace('— ', '').strip()
                if '_container' in lbl: return ''
                return lbl
            return ''

        def _format_val(label, val):
            ll = label.lower() if label else ''
            if 'roas' in ll or 'ctr' in ll or 'cvr' in ll or '%' in label:
                return f"{label}: {val:.2f}%"
            elif '건' in label or '주문' in label or '전환' in label:
                return f"{label}: {int(val):,}건"
            elif '광고비' in label or '매출' in label or '수익' in label or '지출' in label or label in ['총 광고비', '총 매출', '순수익', '적자']:
                return f"{label}: {int(val):,}원"
            else:
                prefix = f"{label}: " if label else ""
                return f"{prefix}{val:,.0f}원" if val > 100 else f"{prefix}{val:,.0f}"

        def on_hover(event):
            vis_changed = False
            
            if event.inaxes is None:
                for annot in annots.values():
                    if annot.get_visible():
                        annot.set_visible(False)
                        vis_changed = True
                if vis_changed:
                    canvas.draw_idle()
                return

            ax = event.inaxes
            
            # 해당 위치의 모든 axes 수집 (twin axes 포함)
            all_axes = [ax]
            for other_ax in fig.get_axes():
                if other_ax is not ax:
                    try:
                        if (abs(other_ax.bbox.x0 - ax.bbox.x0) < 5 and 
                            abs(other_ax.bbox.y0 - ax.bbox.y0) < 5):
                            all_axes.append(other_ax)
                    except:
                        pass

            # 마우스 주변 X축 좌표를 공유하는 후보 데이터 수집
            candidates = []
            
            for chk_ax in all_axes:
                # ── 막대 그래프 확인 ──
                for container in chk_ax.containers:
                    is_horiz = hasattr(container, 'orientation') and container.orientation == 'horizontal'
                    raw_lbl = container.get_label() if hasattr(container, 'get_label') else ''
                    
                    for bar in container:
                        if is_horiz:
                            bx = bar.get_width()  # 수평막대는 너비가 실제 데이터값
                            by = bar.get_y() + bar.get_height() / 2
                            val = bar.custom_val if hasattr(bar, 'custom_val') else bx
                        else:
                            bx = bar.get_x() + bar.get_width() / 2
                            by = bar.get_height()  # 수직막대는 높이가 실제 데이터값
                            val = bar.custom_val if hasattr(bar, 'custom_val') else by
                            
                        try:
                            disp = chk_ax.transData.transform((bx, by))
                            dist_x = abs(event.x - disp[0])
                            dist_y = abs(event.y - disp[1])
                            
                            bbox = bar.get_window_extent()
                            in_bar = bbox.contains(event.x, event.y)
                            
                            # X축 거리가 40px 미만이거나 막대 내부인 경우 후보 포함
                            if in_bar or (dist_x < 40 and dist_y < 250):
                                lbl = _get_clean_label(chk_ax, bar, raw_lbl, is_horiz)
                                candidates.append({
                                    'dist_x': dist_x,
                                    'dist_y': dist_y,
                                    'label': lbl,
                                    'val': val,
                                    'dx': bx,
                                    'dy': by,
                                    'ax': chk_ax,
                                    'type': 'bar'
                                })
                        except:
                            continue

                # ── 선 그래프 확인 ──
                for line in chk_ax.get_lines():
                    xdata = line.get_xdata()
                    ydata = line.get_ydata()
                    if len(xdata) == 0:
                        continue
                    lbl = line.get_label() if line.get_label() else ''
                    lbl = lbl.replace('— ', '')
                    if lbl.startswith('_'):
                        continue
                    try:
                        for idx in range(len(xdata)):
                            disp = chk_ax.transData.transform((float(xdata[idx]), float(ydata[idx])))
                            dist_x = abs(event.x - disp[0])
                            dist_y = abs(event.y - disp[1])
                            
                            # X축 거리가 40px 미만인 경우 후보 포함
                            if dist_x < 40:
                                candidates.append({
                                    'dist_x': dist_x,
                                    'dist_y': dist_y,
                                    'label': lbl,
                                    'val': float(ydata[idx]),
                                    'dx': float(xdata[idx]),
                                    'dy': float(ydata[idx]),
                                    'ax': chk_ax,
                                    'type': 'line'
                                })
                    except (ValueError, TypeError):
                        continue

            if candidates:
                # 가장 X축상으로 근접한 점을 기준으로 필터링
                min_x_dist = min(c['dist_x'] for c in candidates)
                closest_candidates = [c for c in candidates if abs(c['dist_x'] - min_x_dist) < 15]
                
                if closest_candidates:
                    # 중복되지 않는 값 목록 구성
                    lines_text = []
                    seen = set()
                    for c in closest_candidates:
                        text_item = _format_val(c['label'], c['val'])
                        if text_item not in seen:
                            seen.add(text_item)
                            lines_text.append(text_item)
                            
                    if lines_text:
                        text = "\n".join(lines_text)
                        annot = annots[ax]
                        
                        # 대표 앵커 좌표계 설정
                        repr_c = closest_candidates[0]
                        dx, dy, target_ax = repr_c['dx'], repr_c['dy'], repr_c['ax']
                        annot.xy = (dx, dy)
                        
                        if target_ax is not ax:
                            try:
                                disp_pt = target_ax.transData.transform((dx, dy))
                                data_pt = ax.transData.inverted().transform(disp_pt)
                                annot.xy = (data_pt[0], data_pt[1])
                            except:
                                annot.xy = (dx, dy)
                        
                        annot.set_text(text)
                        annot.set_visible(True)
                        vis_changed = True
                        canvas.draw_idle()
                        return

            if annots.get(ax) and annots[ax].get_visible():
                annots[ax].set_visible(False)
                vis_changed = True
                canvas.draw_idle()
            
            # 다른 axes의 annotation 숨기기
            for other_ax, annot in annots.items():
                if other_ax is not ax and annot.get_visible():
                    annot.set_visible(False)
                    vis_changed = True

            if vis_changed:
                canvas.draw_idle()

        fig.canvas.mpl_connect("motion_notify_event", on_hover)

    def _memo_date_to_mmdd(self, date_str):
        """메모 날짜 문자열을 그래프 x축 형식 'MM.DD'로 변환"""
        ds = str(date_str).strip()
        try:
            # YYYY-MM-DD
            if '-' in ds and len(ds) >= 10:
                parts = ds.split('-')
                return f"{int(parts[1]):02d}.{int(parts[2]):02d}"
            # YYMMDD (예: 260428)
            if len(ds) == 6 and ds.isdigit():
                return f"{int(ds[2:4]):02d}.{int(ds[4:6]):02d}"
            # YYYYMMDD (예: 20260428)
            if len(ds) == 8 and ds.isdigit():
                return f"{int(ds[4:6]):02d}.{int(ds[6:8]):02d}"
        except:
            pass
        return None

    def _draw_memo_vlines(self, axes, date_labels, pe, fontsize=8):
        """여러 서브플롯에 메모 날짜 세로 점선과 요약 텍스트 표시"""
        if not self.memos:
            return
        
        memo_colors = ['#FFD700', '#FF6B6B', '#69DB7C', '#74C0FC', '#DA77F2']
        color_idx = 0
        
        for memo_date, memo_text in sorted(self.memos.items()):
            mmdd = self._memo_date_to_mmdd(memo_date)
            if mmdd is None or mmdd not in date_labels:
                continue
            
            x_pos = date_labels.index(mmdd)
            summary = memo_text[:12] + '..' if len(memo_text) > 12 else memo_text
            color = memo_colors[color_idx % len(memo_colors)]
            color_idx += 1
            
            for ax in axes:
                ax.axvline(x=x_pos, color=color, linewidth=1.2, linestyle=':', alpha=0.7, zorder=5)
                ylim = ax.get_ylim()
                y_pos = ylim[1] * 0.92
                ax.text(x_pos, y_pos, summary, rotation=90, va='top', ha='right',
                       color=color, fontsize=fontsize, weight='bold', alpha=0.85,
                       path_effects=pe)

    def _fmt_val(self, v, kind):
        """값을 가독성 좋게 포맷: 원 → 만원/k, % → 소수점"""
        if kind == 'won':
            if abs(v) >= 10000: return f"{v/10000:.1f}만"
            elif abs(v) >= 1000: return f"{v/1000:.0f}k"
            else: return f"{int(v):,}"
        elif kind == 'pct': return f"{v:.1f}%"
        elif kind == 'int': return f"{int(v):,}"
        return str(v)

    def _annotate_smart(self, ax, xs, ys, color, kind, pe, fontsize=8, step=2):
        """중첩 방지: step 간격으로 교대 배치 (위/아래)"""
        for i, v in enumerate(ys):
            if i % step != 0: continue
            if v == 0: continue
            offset_y = 10 if (i // step) % 2 == 0 else -14
            txt = self._fmt_val(v, kind)
            ax.annotate(txt, (xs.iloc[i] if hasattr(xs, 'iloc') else xs[i], ys.iloc[i] if hasattr(ys, 'iloc') else ys[i]),
                        xytext=(0, offset_y), textcoords="offset points", ha='center',
                        color=color, weight='bold', fontsize=fontsize, path_effects=pe)

    # ═══════════════════════════════════════════════════════════════
    # 대시보드 전용 차트 (성과추이와 겹치지 않는 고유 차트)
    # ═══════════════════════════════════════════════════════════════
    
    def _render_dash_profit(self, df, overall, master):
        """💰 수익성 한눈에 보기: 총 광고비 vs 총 매출 비교 + 순수익"""
        plt.rcParams['font.family'] = 'Malgun Gothic'
        pe = [path_effects.withStroke(linewidth=3, foreground='black')]
        
        fig = Figure(figsize=(6.5, 4.5), dpi=95); ax = fig.add_subplot(111)
        fig.patch.set_facecolor('#0B0B1A'); ax.set_facecolor('#0B0B1A')
        ax.set_title("수익성 한눈에 보기", color='white', pad=40, loc='center',
                     fontdict={'size': 16, 'weight': 'bold', 'family': 'Malgun Gothic'})
        ax.text(0.5, 1.01, '매출이 광고비보다 높으면 이익! ROAS 330% 이상이 안전권', 
                transform=ax.transAxes, ha='center', va='bottom', color='#A0AEC0', fontsize=11, style='italic')
        
        spend = overall['spend']
        sales = overall['sales']
        profit = sales - spend
        roas = overall['ROAS']
        
        cats = ['총 광고비', '총 매출']
        vals = [spend, sales]
        colors = ['#EF4444', '#00E5FF']
        bars = ax.bar(cats, vals, color=colors, width=0.5, edgecolor='none', alpha=0.8)
        
        # 순수익 바
        p_color = '#10B981' if profit >= 0 else '#EF4444'
        ax.bar(['순수익'], [profit], color=p_color, width=0.5, alpha=0.8)
        
        # ROAS 표시
        roas_color = '#10B981' if roas >= 330 else '#F59E0B' if roas >= 100 else '#EF4444'
        ax.text(0.97, 0.95, f'ROAS {roas:.0f}%', transform=ax.transAxes, ha='right', va='top',
               fontsize=14, weight='bold', color=roas_color, path_effects=pe,
               bbox=dict(boxstyle='round,pad=0.3', facecolor='#1A1A2E', edgecolor=roas_color, alpha=0.9))
        
        ax.tick_params(axis='y', labelcolor='#94A3B8', labelsize=7)
        ax.tick_params(axis='x', labelcolor='white', labelsize=10)
        ax.grid(True, axis='y', color='#1F2937', linestyle='--', alpha=0.3)
        ax.axhline(y=0, color='#333', linewidth=0.8)
        
        fig.tight_layout(rect=[0, 0, 1, 0.82])
        canvas = FigureCanvasTkAgg(fig, master=master); canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        self._add_hover_tooltip(fig, canvas)

    def _render_dash_top_keywords(self, kw_data, master):
        """🏆 TOP5 효자 키워드: 매출 기여 상위 키워드"""
        plt.rcParams['font.family'] = 'Malgun Gothic'
        pe = [path_effects.withStroke(linewidth=3, foreground='black')]
        
        fig = Figure(figsize=(6.5, 4.5), dpi=95); ax = fig.add_subplot(111)
        fig.patch.set_facecolor('#0B0B1A'); ax.set_facecolor('#0B0B1A')
        ax.set_title("TOP5 효자 키워드", color='white', pad=40, loc='center',
                     fontdict={'size': 16, 'weight': 'bold', 'family': 'Malgun Gothic'})
        ax.text(0.5, 1.01, '매출을 가장 많이 만드는 키워드에 예산을 집중하세요',
                transform=ax.transAxes, ha='center', va='bottom', color='#A0AEC0', fontsize=11, style='italic')
        
        if kw_data is not None and not kw_data.empty:
            top5 = kw_data.nlargest(5, 'sales')[['kw', 'sales', 'spend', 'ROAS']].iloc[::-1]
            
            # 키워드 이름 자르기
            labels = [kw[:8] + '..' if len(str(kw)) > 8 else str(kw) for kw in top5['kw']]
            
            colors_map = []
            for _, r in top5.iterrows():
                if r['ROAS'] >= 330: colors_map.append('#10B981')
                elif r['ROAS'] >= 100: colors_map.append('#F59E0B')
                else: colors_map.append('#EF4444')
            
            # 막대 생성 (상시 텍스트 제거, 호버 툴팁으로 확인 가능)
            bars = ax.barh(labels, top5['sales'].values, color=colors_map, height=0.5, edgecolor='none', alpha=0.8)
        else:
            ax.text(0.5, 0.5, '데이터 없음', transform=ax.transAxes, ha='center', va='center',
                   color='#666', fontsize=14)
        
        ax.tick_params(axis='y', labelcolor='white', labelsize=9)
        ax.tick_params(axis='x', labelcolor='#94A3B8', labelsize=7)
        ax.grid(True, axis='x', color='#1F2937', linestyle='--', alpha=0.3)
        
        fig.tight_layout(rect=[0, 0, 1, 0.82])
        canvas = FigureCanvasTkAgg(fig, master=master); canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        self._add_hover_tooltip(fig, canvas)

    def _render_dash_kpi_gauge(self, overall, master):
        """⚡ 핵심 KPI 건강도: 4대 지표를 직관적 게이지로 표시"""
        plt.rcParams['font.family'] = 'Malgun Gothic'
        pe = [path_effects.withStroke(linewidth=2, foreground='black')]
        
        fig = Figure(figsize=(6.5, 4.5), dpi=95)
        fig.patch.set_facecolor('#0B0B1A')
        
        ax = fig.add_subplot(111)
        ax.set_facecolor('#0B0B1A')
        ax.set_title("광고 핵심 KPI 건강도", color='white', pad=40, loc='center',
                     fontdict={'size': 16, 'weight': 'bold', 'family': 'Malgun Gothic'})
        ax.text(0.5, 1.01, '초록=양호 / 노랑=주의 / 빨강=위험 (기준: 업계 평균)',
               transform=ax.transAxes, ha='center', va='bottom', color='#A0AEC0', fontsize=11, style='italic')
        
        # KPI 정의: (이름, 실제값, 기준값(양호), 최대스케일, 단위, 낮을수록좋은지)
        kpis = [
            ('ROAS', overall['ROAS'], 330, 1000, '%', False),
            ('CTR', overall['CTR'], 0.5, 2.0, '%', False),
            ('CVR', overall['CVR'], 5.0, 20.0, '%', False),
            ('CPC', overall['CPC'], 300, 800, '원', True),
        ]
        
        ax.set_xlim(0, 1.15)
        ax.set_ylim(-0.5, len(kpis) - 0.5)
        ax.set_yticks(range(len(kpis)))
        ax.set_yticklabels([k[0] for k in kpis][::-1], color='white', fontsize=13, weight='bold')
        ax.tick_params(axis='x', bottom=False, labelbottom=False)
        ax.tick_params(axis='y', left=False)
        for sp in ax.spines.values(): sp.set_visible(False)
        
        for idx, (name, val, good, max_v, unit, lower_better) in enumerate(kpis):
            y = len(kpis) - 1 - idx
            fill = min(val / max_v, 1.0) if max_v > 0 else 0
            
            if lower_better:
                if val <= good: color = '#10B981'
                elif val <= good * 2: color = '#F59E0B'
                else: color = '#EF4444'
            else:
                if val >= good: color = '#10B981'
                elif val >= good * 0.5: color = '#F59E0B'
                else: color = '#EF4444'
            
            # 배경 바
            ax.barh(y, 1.0, height=0.45, color='#1F2937', edgecolor='none')
            # 채움 바
            bars = ax.barh(y, fill, height=0.45, color=color, edgecolor='none', alpha=0.85, label=name)
            for bar in bars:
                bar.custom_val = val
            
            # 값 표시
            if unit == '원':
                val_text = f'{int(val):,}{unit}'
            else:
                val_text = f'{val:.1f}{unit}'
            
            ax.text(fill + 0.03 if fill < 0.85 else fill - 0.03, y, val_text, 
                   va='center', ha='left' if fill < 0.85 else 'right',
                   color='white', fontsize=11, weight='bold', path_effects=pe)
            
            # 기준선
            good_pos = min(good / max_v, 1.0) if max_v > 0 else 0
            ax.axvline(x=good_pos, ymin=(y - 0.2 + 0.5) / len(kpis), ymax=(y + 0.2 + 0.5) / len(kpis),
                      color='#FFD700', linewidth=1.5, linestyle='--', alpha=0.7)
        
        fig.tight_layout(rect=[0, 0.02, 1, 0.88])
        canvas = FigureCanvasTkAgg(fig, master=master); canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        self._add_hover_tooltip(fig, canvas)

    def _render_dashboard_dual(self, df, master, title, y1, y2, c1, c2):
        plt.rcParams['font.family'] = 'Malgun Gothic'
        plt.rcParams['axes.unicode_minus'] = False
        pe = [path_effects.withStroke(linewidth=3, foreground='black')]
        
        fig = Figure(figsize=(6.5, 4.5), dpi=95); ax = fig.add_subplot(111)
        fig.patch.set_facecolor('#0B0B1A'); ax.set_facecolor('#0B0B1A')
        ax.set_title(title, color='white', pad=40, loc='center', fontdict={'size': 16, 'weight': 'bold', 'family': 'Malgun Gothic'})
        
        guides = {
            '매출': '매출 상승 시 ROAS도 유지되는지 확인',
            '광고비': '광고비 대비 클릭수 동반 상승이 핵심',
            'CTR': 'CTR=썸네일 매력도, CVR=구매 전환력',
        }
        guide_text = next((v for k, v in guides.items() if k in title), '')
        if guide_text:
            ax.text(0.5, 1.01, guide_text, transform=ax.transAxes,
                   ha='center', va='bottom', color='#A0AEC0', fontsize=11, style='italic')
        
        # y1: 항상 막대 그래프
        y1_vals = df[y1]
        y1_name = {'sales': '매출액', 'spend': '광고비', 'CTR': 'CTR%'}.get(y1, y1)
        ax.bar(df['date_s'], y1_vals, color=c1, alpha=0.35, label=f'■ {y1_name} (막대)')
        y1_kind = 'won' if y1 in ['sales', 'spend'] else 'pct'
        
        y1_label = {'sales': '매출액 (원)', 'spend': '광고비 (원)', 'CTR': 'CTR (%)'}.get(y1, y1)
        ax.set_ylabel(y1_label, color=c1, size=9, weight='bold', fontfamily='Malgun Gothic')
        ax.tick_params(axis='y', labelcolor=c1, labelsize=7)
        ax.tick_params(axis='x', labelcolor='#94A3B8', labelsize=6, rotation=30)
        # y2: 항상 선 그래프
        ax2 = ax.twinx()
        if y2 == 'CVR':
            y2_vals = pd.Series(np.where(df['click'] > 0, (df['orders'] / df['click']) * 100, 0))
            y2_kind = 'pct'; y2_label = 'CVR (%)'; y2_name = 'CVR%'
        else:
            y2_vals = df[y2]
            y2_kind = 'pct' if y2 in ['ROAS', 'CTR'] else 'int'
            y2_label = {'ROAS': 'ROAS (%)', 'click': '클릭수 (회)'}.get(y2, y2)
            y2_name = {'ROAS': 'ROAS%', 'click': '클릭수'}.get(y2, y2)
        
        ax2.plot(df['date_s'], y2_vals, color=c2, marker='o', linewidth=2.5, markersize=5,
                 label=f'— {y2_name} (선)', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
        ax2.set_ylabel(y2_label, color=c2, size=9, weight='bold', fontfamily='Malgun Gothic')
        ax2.tick_params(axis='y', labelcolor=c2, labelsize=7)
        
        # 선 그래프의 모든 데이터 포인트에 100% 상시 값 표시
        for i, v in enumerate(y2_vals):
            if v == 0: continue
            offset_y = -14 if i % 2 == 0 else 10
            txt = self._fmt_val(v, y2_kind)
            ax2.annotate(txt, (df['date_s'].iloc[i], y2_vals.iloc[i] if hasattr(y2_vals, 'iloc') else y2_vals[i]),
                         xytext=(0, offset_y), textcoords="offset points", ha='center',
                         color=c2, weight='bold', fontsize=8, path_effects=pe)
        
        # 범례
        h1, l1 = ax.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        ax.legend(h1+h2, l1+l2, loc='upper left', fontsize=7, 
                  facecolor='#1A1A2E', edgecolor='#333', labelcolor='white', framealpha=0.8)
        
        fig.tight_layout(rect=[0, 0, 1, 0.82])
        canvas = FigureCanvasTkAgg(fig, master=master); canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        self._add_hover_tooltip(fig, canvas)

    def _render_dashboard_pie(self, br_df, master):
        plt.rcParams['font.family'] = 'Malgun Gothic'
        plt.rcParams['axes.unicode_minus'] = False
        pe = [path_effects.withStroke(linewidth=3, foreground='black')]
        
        fig = Figure(figsize=(6.5, 4.5), dpi=95); ax = fig.add_subplot(111)
        fig.patch.set_facecolor('#0B0B1A'); ax.set_facecolor('#0B0B1A')
        ax.set_title("노출 영역별 광고비", color='white', pad=40, loc='center',
                     fontdict={'size': 16, 'weight': 'bold', 'family': 'Malgun Gothic'})
        ax.text(0.5, 1.01, '검색/비검색/오피니언 영역 비중을 보고 노출 전략을 조정하세요',
               transform=ax.transAxes, ha='center', va='bottom', color='#A0AEC0', fontsize=11, style='italic')
        
        if not br_df.empty:
            # 3대 핵심 대표 영역 정의 (데이터가 없더라도 고정 표출)
            target_regions = ['검색 영역', '비검색 영역', '오디언스 플러스(외부 채널) - Product Ad']
            
            s_dict = {reg: 0.0 for reg in target_regions}
            
            raw_s = br_df.groupby('region')['spend'].sum()
            for r_name, val in raw_s.items():
                r_name_str = str(r_name)
                matched = False
                for reg in target_regions:
                    # 키워드 유사도 매칭 (검색, 비검색, 오디언스/외부채널)
                    if (reg in r_name_str) or (r_name_str in reg) or \
                       ('오디언스' in r_name_str and '오디언스' in reg) or \
                       ('비검색' in r_name_str and '비검색' in reg):
                        s_dict[reg] += val
                        matched = True
                        break
                if not matched:
                    s_dict[r_name_str] = val
                        
            s = pd.Series(s_dict)
            
            colors = ['#EC4899', '#8B5CF6', '#3B82F6', '#F59E0B', '#10B981']
            
            # 영역명 친숙하게 매핑 및 길이 압축
            labels = []
            for name in s.index:
                n_str = str(name)
                if '오디언스' in n_str or '외부 채널' in n_str or '오피니언' in n_str:
                    labels.append('오피니언 영역')
                elif len(n_str) > 6:
                    labels.append(n_str[:6] + '..')
                else:
                    labels.append(n_str)
            
            bars = ax.bar(labels, s.values, color=colors[:len(s)], width=0.5, edgecolor='none', alpha=0.85)
            
            ax.set_ylim(0, max(s.max() * 1.25, 10000))
            ax.tick_params(axis='x', labelcolor='white', labelsize=10, rotation=0)
            ax.tick_params(axis='y', labelcolor='#94A3B8', labelsize=8)
            ax.yaxis.set_visible(False)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_visible(False)
            ax.spines['bottom'].set_color('#1F2937')
            ax.grid(True, axis='y', color='#1F2937', linestyle='--', alpha=0.3)
        else:
            ax.text(0.5, 0.5, '데이터 없음', ha='center', va='center', color='#6B7280', 
                   fontsize=14, fontfamily='Malgun Gothic')
        
        fig.tight_layout(rect=[0, 0, 1, 0.82])
        canvas = FigureCanvasTkAgg(fig, master=master); canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        self._add_hover_tooltip(fig, canvas)

    def _init_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0, font=("Malgun Gothic", 10))
        self.context_menu.add_command(label="🎯 타겟 키워드로 이동", command=lambda: self._move_keyword("타겟"))
        self.context_menu.add_command(label="⚙️ 수동 관리로 이동", command=lambda: self._move_keyword("수동"))
        self.context_menu.add_command(label="🚫 제외 키워드로 이동", command=lambda: self._move_keyword("제외"))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="📋 키워드 복사", command=self._menu_copy_keywords)

    def _on_kw_right_click(self, e):
        row_id = self.kw_tree.identify_row(e.y)
        if row_id:
            # 이미 복수 선택된 항목 위에서 우클릭하면 기존 선택 유지
            if row_id not in self.kw_tree.selection():
                self.kw_tree.selection_set(row_id)
            self.context_menu.post(e.x_root, e.y_root)

    def _on_management_right_click(self, e, tree, current_tab):
        row_id = tree.identify_row(e.y)
        if row_id:
            # 이미 선택된 항목 위에서 우클릭하면 기존 복수 선택 유지
            if row_id not in tree.selection():
                tree.selection_set(row_id)
            sel_count = len(tree.selection())
            m = tk.Menu(self, tearoff=0, font=("Malgun Gothic", 10))
            m.add_command(label=f"📋 키워드 복사 ({sel_count}개)", command=lambda: self._copy_keyword_from_tree(tree))
            m.add_command(label="📋 전체 키워드 복사", command=lambda: self._copy_all_keywords_from_tree(tree))
            m.add_separator()
            m.add_command(label="🗑️ 목록에서 삭제", command=lambda: self._delete_from_management(tree, current_tab))
            m.post(e.x_root, e.y_root)

    def _copy_keyword_from_tree(self, tree):
        """선택된 키워드를 클립보드에 복사"""
        sel = tree.selection()
        if not sel:
            return
        keywords = []
        for item in sel:
            vals = tree.item(item, 'values')
            if vals:
                keywords.append(str(vals[0]))
        if keywords:
            text = '\n'.join(keywords)
            self.clipboard_clear()
            self.clipboard_append(text)
            messagebox.showinfo("알림", f"'{keywords[0]}' 등 {len(keywords)}개 키워드가 복사되었습니다." if len(keywords) > 1 else f"'{keywords[0]}' 키워드가 복사되었습니다.")

    def _copy_all_keywords_from_tree(self, tree):
        """트리의 전체 키워드를 클립보드에 복사"""
        all_items = tree.get_children()
        if not all_items:
            messagebox.showwarning("알림", "복사할 키워드가 없습니다.")
            return
        keywords = []
        for item in all_items:
            vals = tree.item(item, 'values')
            if vals:
                keywords.append(str(vals[0]))
        if keywords:
            self.clipboard_clear()
            self.clipboard_append('\n'.join(keywords))
            messagebox.showinfo("알림", f"전체 {len(keywords)}개 키워드가 복사되었습니다.")

    def _move_keyword(self, target_class):
        sel = self.kw_tree.selection()
        if not sel: return
        kw = self.kw_tree.item(sel[0])['values'][1]
        self.keyword_classes[kw] = target_class
        self._save_keyword_classes()
        self._refresh_management_tabs()
        self._populate_kw_tree(self.current_data)
        messagebox.showinfo("완료", f"'{kw}' 키워드가 [{target_class}] 리스트로 이동되었습니다.")

    def _delete_from_management(self, tree, tab_name):
        sel = tree.selection()
        if not sel: return
        kw = tree.item(sel[0])['values'][0]
        if kw in self.keyword_classes:
            del self.keyword_classes[kw]
            self._save_keyword_classes()
            self._refresh_management_tabs()
            self._populate_kw_tree(self.current_data)

    def _refresh_management_tabs(self):
        for name, tree in self.mgmt_trees.items():
            for item in tree.get_children(): tree.delete(item)
            for kw, cls in self.keyword_classes.items():
                if cls == name:
                    tree.insert("", "end", values=(kw, datetime.now().strftime("%Y-%m-%d"), ""))

    def _save_keyword_classes(self):
        with open("keyword_classes.json", "w", encoding="utf-8") as f:
            json.dump(self.keyword_classes, f, ensure_ascii=False, indent=4)

    def _load_keyword_classes(self):
        if os.path.exists("keyword_classes.json"):
            with open("keyword_classes.json", "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_today_memo(self):
        self._save_memo_by_date()

    def _load_memos(self):
        if os.path.exists("ad_memos.json"):
            with open("ad_memos.json", "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _sort_by_column(self, col, reverse):
        l = [(self.kw_tree.set(k, col), k) for k in self.kw_tree.get_children('')]
        try:
            l.sort(key=lambda x: float(re.sub(r'[^0-9.-]', '', str(x[0])) or 0), reverse=reverse)
        except:
            l.sort(reverse=reverse)
        for index, (val, k) in enumerate(l):
            self.kw_tree.move(k, '', index)
        self.kw_tree.heading(col, command=lambda: self._sort_by_column(col, not reverse))

    def _filter_by_status(self, s):
        if self.current_data is None: return
        self.tabview.set("🔍 키워드 분석")
        f_d = self.current_data.copy()
        if s == "rev0": f_d = f_d[f_d['sales'] == 0]
        elif s == "low_roas": f_d = f_d[(f_d['sales'] > 0) & (f_d['ROAS'] < 330)]
        elif s == "rev_plus": f_d = f_d[f_d['sales'] > 0]
        self._populate_kw_tree(f_d)

    def _reset_keyword_filter(self):
        self._populate_kw_tree(self.current_data)
        self.filter_label.configure(text="")
        self.search_result_label.configure(text="")
        self.kw_search_var.set("")

    def _search_keywords(self):
        """키워드열에서 검색어를 포함하는 행만 필터링"""
        query = self.kw_search_var.get().strip()
        if not query:
            messagebox.showwarning("알림", "검색할 키워드를 입력하세요.")
            return
        if self.current_data is None or self.current_data.empty:
            messagebox.showwarning("알림", "먼저 데이터를 분석해주세요.")
            return
        
        filtered = self.current_data[self.current_data['kw'].str.contains(query, case=False, na=False)]
        self._populate_kw_tree(filtered)
        
        total = len(filtered)
        self.filter_label.configure(text=f"🔍 '{query}' 검색 결과")
        self.search_result_label.configure(text=f"{total}개 키워드 발견" if total > 0 else "검색 결과 없음")
    
    def _clear_keyword_search(self):
        """검색 초기화 → 전체 키워드 복원"""
        self._reset_keyword_filter()

    def _on_kw_double_click(self, e):
        sel = self.kw_tree.selection()
        if not sel: return
        pname = self.kw_tree.item(sel[0])['values'][16]
        if pname and pname != "-":
            f_d = self.current_data[self.current_data['pname'] == pname]
            self._populate_kw_tree(f_d)
            self.filter_label.configure(text=f"🔎 필터링 결과: {pname[:25]}...")

    def _menu_copy_keywords(self):
        sel = self.kw_tree.selection()
        if sel:
            keywords = []
            for item in sel:
                vals = self.kw_tree.item(item)['values']
                if vals and len(vals) > 1:
                    keywords.append(str(vals[1]))
            if keywords:
                self.clipboard_clear()
                self.clipboard_append('\n'.join(keywords))
                messagebox.showinfo("알림", f"{len(keywords)}개 키워드가 복사되었습니다.")

    def _choose_file(self):
        f = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if f:
            self.analyzer.file_path = f
            self.filename_label.configure(text=os.path.basename(f))

    def _update_performance_cards(self):
        o = self.analyzer.get_overall_summary()
        if not o: return
        for i, info in self.perf_labels.items():
            key = info['key']; val = o.get(key, 0); unit = info['unit']
            if unit == "원" or unit == "회": text = f"{int(val):,} {unit}"
            else: text = f"{val:.2f} {unit}"
            info['label'].configure(text=text)

    def _populate_summary_table(self):
        for item in self.summary_tree.get_children(): self.summary_tree.delete(item)
        s = self.analyzer.get_region_summary()
        if not s.empty:
            for _, r in s.iterrows():
                vals = (r['region'], f"{int(r['sales']):,}", f"{int(r['spend']):,}", f"{r['ROAS']:.1f}%", f"{int(r['orders']):,}", f"{int(r['click']):,}", f"{int(r['imp']):,}", f"{r['CTR']:.2f}%", f"{r['CVR']:.1f}%", f"{int(r['CPC']):,}")
                self.summary_tree.insert("", "end", values=vals)

if __name__ == "__main__":
    app = AdOptimizerApp()
    app.mainloop()
