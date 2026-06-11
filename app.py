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
        self.editing_memo_id = None
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
        self.tabview._segmented_button.configure(font=("Malgun Gothic", 15, "bold"), selected_color="#2563EB", unselected_color="#1A1A2E", height=45)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=5)
        
        self.main_tab_perf = self.tabview.add("📊 종합 성과")
        self.main_tab_mgmt = self.tabview.add("⚙️ 키워드/입찰")
        self.main_tab_ai = self.tabview.add("🛡️ AI분석/도구")
        self.main_tab_memo = self.tabview.add("📝 일별 메모")
        
        # 1. 종합 성과 서브 카테고리 구성
        self.sub_perf_container = ctk.CTkFrame(self.main_tab_perf, fg_color="transparent")
        self.sub_perf_container.pack(fill="both", expand=True)
        
        self.sub_perf_selector = ctk.CTkSegmentedButton(self.sub_perf_container, 
                                                         values=["📊 광고요약", "📈 성과 추이", "🌐 영역별 분석", "📊 실판매 분석"],
                                                         font=("Malgun Gothic", 13, "bold"),
                                                         height=38,
                                                         command=self._on_perf_sub_selected)
        self.sub_perf_selector.pack(fill="x", padx=10, pady=5)
        
        self.tab_dashboard = ctk.CTkFrame(self.sub_perf_container, fg_color="transparent")
        self.tab_metrics = ctk.CTkFrame(self.sub_perf_container, fg_color="transparent")
        self.tab_region_metrics = ctk.CTkFrame(self.sub_perf_container, fg_color="transparent")
        self.tab_real_price = ctk.CTkFrame(self.sub_perf_container, fg_color="transparent")
        
        self.perf_frames = {
            "📊 광고요약": self.tab_dashboard,
            "📈 성과 추이": self.tab_metrics,
            "🌐 영역별 분석": self.tab_region_metrics,
            "📊 실판매 분석": self.tab_real_price
        }
        
        # 2. 키워드/입찰 서브 카테고리 구성
        self.sub_mgmt_container = ctk.CTkFrame(self.main_tab_mgmt, fg_color="transparent")
        self.sub_mgmt_container.pack(fill="both", expand=True)
        
        self.sub_mgmt_selector = ctk.CTkSegmentedButton(self.sub_mgmt_container, 
                                                         values=["🔍 키워드 분석", "🎯 타겟 관리", "⚙️ 수동 관리", "🚫 제외 관리"],
                                                         font=("Malgun Gothic", 13, "bold"),
                                                         height=38,
                                                         command=self._on_mgmt_sub_selected)
        self.sub_mgmt_selector.pack(fill="x", padx=10, pady=5)
        
        self.tab_keywords = ctk.CTkFrame(self.sub_mgmt_container, fg_color="transparent")
        self.tab_target = ctk.CTkFrame(self.sub_mgmt_container, fg_color="transparent")
        self.tab_manual = ctk.CTkFrame(self.sub_mgmt_container, fg_color="transparent")
        self.tab_exclude = ctk.CTkFrame(self.sub_mgmt_container, fg_color="transparent")
        
        self.mgmt_frames = {
            "🔍 키워드 분석": self.tab_keywords,
            "🎯 타겟 관리": self.tab_target,
            "⚙️ 수동 관리": self.tab_manual,
            "🚫 제외 관리": self.tab_exclude
        }
        
        # 3. AI분석/도구 서브 카테고리 구성
        self.sub_ai_container = ctk.CTkFrame(self.main_tab_ai, fg_color="transparent")
        self.sub_ai_container.pack(fill="both", expand=True)
        
        self.sub_ai_selector = ctk.CTkSegmentedButton(self.sub_ai_container, 
                                                       values=["🛡️ AI 나침반", "📦 상품 성과", "🧮 순익 계산기", "🔮 AI 시뮬레이터"],
                                                       font=("Malgun Gothic", 13, "bold"),
                                                       height=38,
                                                       command=self._on_ai_sub_selected)
        self.sub_ai_selector.pack(fill="x", padx=10, pady=5)
        
        self.tab_diagnosis = ctk.CTkFrame(self.sub_ai_container, fg_color="transparent")
        self.tab_product_metrics = ctk.CTkFrame(self.sub_ai_container, fg_color="transparent")
        self.tab_calculator = ctk.CTkFrame(self.sub_ai_container, fg_color="transparent")
        self.tab_ai_simulator = ctk.CTkFrame(self.sub_ai_container, fg_color="transparent")
        
        self.ai_frames = {
            "🛡️ AI 나침반": self.tab_diagnosis,
            "📦 상품 성과": self.tab_product_metrics,
            "🧮 순익 계산기": self.tab_calculator,
            "🔮 AI 시뮬레이터": self.tab_ai_simulator
        }
        
        # 4. 일별 메모 (서브메뉴 없음)
        self.tab_memos = self.main_tab_memo
        
        self._setup_dashboard_tab()
        self._setup_keyword_tab()
        self._setup_management_tab(self.tab_target, "타겟")
        self._setup_management_tab(self.tab_manual, "수동")
        self._setup_management_tab(self.tab_exclude, "제외")
        self._setup_metrics_tab()
        self._setup_product_metrics_tab()
        self._setup_memos_tab()
        self._setup_diagnosis_tab()
        self._setup_calculator_tab()
        self._setup_region_metrics_tab()
        self._setup_ai_simulator_tab()
        self._setup_real_price_tab()
        
        self._refresh_management_tabs()
        
        # 기본 활성화 서브 탭 설정
        self.sub_perf_selector.set("📊 광고요약")
        self._on_perf_sub_selected("📊 광고요약")
        
        self.sub_mgmt_selector.set("🔍 키워드 분석")
        self._on_mgmt_sub_selected("🔍 키워드 분석")
        
        self.sub_ai_selector.set("🛡️ AI 나침반")
        self._on_ai_sub_selected("🛡️ AI 나침반")
        
        self.status_label = ctk.CTkLabel(self, text="준비됨", anchor="w", padx=20, height=35, fg_color="#1A1A2E", font=("Malgun Gothic", 11))
        self.status_label.pack(fill="x", side="bottom")

    def _on_perf_sub_selected(self, val):
        for name, frame in self.perf_frames.items():
            if name == val:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()

    def _on_mgmt_sub_selected(self, val):
        for name, frame in self.mgmt_frames.items():
            if name == val:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()

    def _on_ai_sub_selected(self, val):
        for name, frame in self.ai_frames.items():
            if name == val:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()

    def _setup_dashboard_tab(self):
        self.dashboard_scroll = ctk.CTkScrollableFrame(self.tab_dashboard, fg_color="#0B0B1A")
        self.dashboard_scroll.pack(fill="both", expand=True)
        
        # 1. 성과 카드
        self._setup_performance_cards()
        
        # 2. 그래프 레이아웃 (대형 성과그래프 + 4분할 그래프)
        self.chart_grid = ctk.CTkFrame(self.dashboard_scroll, fg_color="transparent")
        self.chart_grid.pack(fill="both", expand=True, padx=15, pady=10)
        self.chart_grid.grid_columnconfigure((0, 1), weight=1)
        self.chart_grid.grid_rowconfigure((0, 1, 2), weight=1) # 3행 구조
        
        # 대형 성과그래프 (row=0, columnspan=2)
        self.chart_frame_top_trend = ctk.CTkFrame(self.chart_grid, height=380, fg_color="#0B0B1A", corner_radius=12, border_width=1, border_color="#10B981")
        self.chart_frame_top_trend.grid(row=0, column=0, columnspan=2, padx=8, pady=8, sticky="nsew")
        
        # 기존 4분할
        self.chart_frame_tl = ctk.CTkFrame(self.chart_grid, height=450, fg_color="#0B0B1A", corner_radius=12, border_width=1, border_color="#1A3A4A")
        self.chart_frame_tl.grid(row=1, column=0, padx=8, pady=8, sticky="nsew")
        self.chart_frame_tr = ctk.CTkFrame(self.chart_grid, height=450, fg_color="#0B0B1A", corner_radius=12, border_width=1, border_color="#3A1A1A")
        self.chart_frame_tr.grid(row=1, column=1, padx=8, pady=8, sticky="nsew")
        self.chart_frame_bl = ctk.CTkFrame(self.chart_grid, height=400, fg_color="#0B0B1A", corner_radius=12, border_width=1, border_color="#1A2A1A")
        self.chart_frame_bl.grid(row=2, column=0, padx=8, pady=8, sticky="nsew")
        self.chart_frame_br = ctk.CTkFrame(self.chart_grid, height=400, fg_color="#0B0B1A", corner_radius=12, border_width=1, border_color="#1A1A3A")
        self.chart_frame_br.grid(row=2, column=1, padx=8, pady=8, sticky="nsew")

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
        self.perf_card_frame.pack(fill="x", padx=15, pady=8)
        
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
            
            # 1. 3D 입체 플로팅 네온 스타일 카드 프레임 설정
            card = ctk.CTkFrame(
                self.perf_card_frame, 
                fg_color="#1E293B",      # 슬레이트 블루 (어두운 배경과 텍스트의 고대비 극대화)
                border_width=2, 
                border_color="#3B82F6",  # 입체적인 선명한 파란색 네온 테두리
                corner_radius=12         # 부드러운 코너 라운딩 처리
            )
            card.grid(row=r, column=c, padx=6, pady=6, sticky="nsew")
            self.perf_card_frame.grid_columnconfigure(c, weight=1)
            
            # 2. 지표 유형별 고대비 형광 네온 컬러 매핑
            if "광고비" in t:
                color = "#FBBF24"  # 골드 옐로우
            elif "매출" in t:
                color = "#34D399"  # 에메랄드 그린
            elif t in ["전체 판매수", "노출수", "클릭수", "전환 판매수", "전환 주문수"]:
                color = "#60A5FA"  # 스카이 블루
            else:
                color = "#FB923C"  # 네온 오렌지
            
            # 3. 노안 맞춤 초대형 레이아웃 텍스트 적용 (맑은 고딕 사용으로 한글 단위 어그러짐 방지)
            ctk.CTkLabel(
                card, 
                text=t, 
                font=("Malgun Gothic", 14, "bold"), 
                text_color="#E2E8F0"  # 선명한 연회색
            ).pack(pady=(12, 0))
            
            v_lbl = ctk.CTkLabel(
                card, 
                text="-", 
                font=("Malgun Gothic", 26, "bold"), 
                text_color=color
            )
            v_lbl.pack(pady=(6, 12))
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
        
        # 상품 선택 버튼 (클릭 시 세로 스크롤 & 검색을 탑재한 고급 팝업창 오픈)
        self.selected_product_var = tk.StringVar(value="데이터 분석을 먼저 진행해주세요.")
        self.product_select_btn = ctk.CTkButton(self.prod_filter_frame, textvariable=self.selected_product_var,
                                                width=550, height=38, font=("Malgun Gothic", 13, "bold"),
                                                fg_color="#0F0F24", hover_color="#1F1F44", border_width=1, border_color="#3B82F6",
                                                anchor="w", command=self._open_product_select_popup)
        self.product_select_btn.pack(side="left", padx=10, pady=18)
        
        # 차트 조회 버튼 (선택 사항 - 예비용)
        self.prod_search_btn = ctk.CTkButton(self.prod_filter_frame, text="📊 차트 조회", command=self._draw_product_charts, 
                                             fg_color="#2563EB", hover_color="#1D4ED8", width=120, height=38, font=("Malgun Gothic", 13, "bold"))
        self.prod_search_btn.pack(side="left", padx=15, pady=18)
        
        # 하단 스크롤 가능한 차트 뷰포트
        self.prod_metrics_scroll = ctk.CTkScrollableFrame(self.tab_product_metrics, fg_color="#0B0B1A")
        self.prod_metrics_scroll.pack(fill="both", expand=True, padx=15, pady=(5, 15))

    def _open_product_select_popup(self):
        """세로 스크롤바가 우측에 배치된 상품 선택 팝업창을 오픈"""
        if self.analyzer.raw_df is None:
            messagebox.showwarning("알림", "분석을 실행한 뒤 상품을 선택해주세요.")
            return

        # 팝업 창 생성 (CTkToplevel)
        self.popup = ctk.CTkToplevel(self)
        self.popup.title("📦 상품 선택 나침반 (매출 발생 상품은 파란색으로 표시됨)")
        self.popup.geometry("650x700")
        self.popup.configure(fg_color="#0B0B1A")
        self.popup.attributes("-topmost", True)
        self.popup.focus()
        
        # 상단 검색 바 프레임
        search_frame = ctk.CTkFrame(self.popup, fg_color="#1A1A2E", corner_radius=10, height=60)
        search_frame.pack(fill="x", padx=15, pady=(15, 5))
        
        ctk.CTkLabel(search_frame, text="🔍 상품 검색 :", font=("Malgun Gothic", 14, "bold"), text_color="#60A5FA").pack(side="left", padx=(15, 8))
        
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="검색어를 입력하세요 (예: 옥수수)", 
                                          width=450, height=34, font=("Malgun Gothic", 13))
        self.search_entry.pack(side="left", padx=5, pady=13)
        self.search_entry.bind("<KeyRelease>", self._filter_product_list_popup)
        
        # 하단 스크롤 리스트 (CTkScrollableFrame으로 우측에 명확한 세로 스크롤바 장착)
        self.popup_scroll = ctk.CTkScrollableFrame(self.popup, fg_color="#0D0D21", border_width=1, border_color="#1A3A4A")
        self.popup_scroll.pack(fill="both", expand=True, padx=15, pady=(5, 15))
        
        # 리스트 초기 렌더링
        self._render_popup_product_list("")

    def _render_popup_product_list(self, filter_text=""):
        """검색어 필터에 따라 상품 리스트 재생성"""
        for w in self.popup_scroll.winfo_children():
            w.destroy()
            
        m = self.analyzer._get_column_mapping(self.analyzer.raw_df)
        pname_col = m.get('pname')
        
        if pname_col and pname_col in self.analyzer.raw_df.columns:
            products = self.analyzer.raw_df[pname_col].dropna().unique().tolist()
            products = [str(p).strip() for p in products if str(p).strip() and str(p).strip() != '-']
            # 매출액 내림차순 정렬 (매출이 클수록 위로, 매출이 같거나 없을 경우 가나다순)
            sales_dict = getattr(self, 'product_sales_dict', {})
            products.sort(key=lambda p: (-sales_dict.get(p, 0), p))
            
            # 검색 필터링
            if filter_text:
                products = [p for p in products if filter_text.lower() in p.lower()]
                
            if not products:
                ctk.CTkLabel(self.popup_scroll, text="일치하는 상품이 없습니다.", font=("Malgun Gothic", 13), text_color="#94A3B8").pack(pady=20)
                return
                
            for p in products:
                # 매출 발생 판정
                sales_val = self.product_sales_dict.get(p, 0)
                dir_val = self.product_dir_sales_dict.get(p, 0)
                indir_val = self.product_indir_sales_dict.get(p, 0)
                is_sales_plus = sales_val > 0
                
                # 디자인 설정 (직접 매출 유무 및 간접 매출 유무에 따라 세분화)
                if is_sales_plus:
                    if dir_val > 0:
                        txt_color = "#60A5FA"  # 직접 매출 발생: 선명한 파란색
                        prefix = "🟢 [매출 발생]  "
                        btn_txt = f"{prefix}{p}\n(직접 매출: {int(dir_val):,}원 / 간접 매출: {int(indir_val):,}원 | 총 매출: {int(sales_val):,}원)"
                    else:
                        txt_color = "#FB923C"  # 간접 매출만 발생: 네온 오렌지
                        prefix = "⚪ [무매출 (간접만 발생)]  "
                        btn_txt = f"{prefix}{p}\n(직접 매출: 0원 / 간접 매출: {int(indir_val):,}원 | 총 매출: {int(sales_val):,}원)"
                else:
                    txt_color = "#E2E8F0"  # 완전 무매출: 회백색
                    prefix = "⚪ [무매출]  "
                    btn_txt = f"{prefix}{p}"
                
                # 긴 상품명이 잘리지 않도록 줄바꿈(wraplength)이 지원되는 CTkLabel을 탑재한 CTkFrame 카드 형태로 구현
                item_frame = ctk.CTkFrame(self.popup_scroll, fg_color="#18182D", corner_radius=6, border_width=1, border_color="#2E2E4A")
                item_frame.pack(fill="x", padx=5, pady=4)
                
                # 호버 및 클릭 이벤트 바인딩 (클로저를 활용해 독립된 변수 스코프 캡처)
                def make_callbacks(prod_name, frame_obj):
                    def on_enter(e):
                        frame_obj.configure(fg_color="#2B2B4A")
                    def on_leave(e):
                        frame_obj.configure(fg_color="#18182D")
                    def on_click(e):
                        self._select_product_from_popup(prod_name)
                    return on_enter, on_leave, on_click
                
                on_enter, on_leave, on_click = make_callbacks(p, item_frame)
                
                item_frame.configure(cursor="hand2")
                item_frame.bind("<Enter>", on_enter)
                item_frame.bind("<Leave>", on_leave)
                item_frame.bind("<Button-1>", on_click)
                
                # wraplength=520으로 설정하여 긴 텍스트를 자동 줄바꿈 처리
                lbl = ctk.CTkLabel(item_frame, text=btn_txt, font=("Malgun Gothic", 13),
                                   text_color=txt_color, anchor="w", justify="left", 
                                   wraplength=520, cursor="hand2")
                lbl.pack(fill="x", padx=15, pady=10)
                
                lbl.bind("<Enter>", on_enter)
                lbl.bind("<Leave>", on_leave)
                lbl.bind("<Button-1>", on_click)
        else:
            ctk.CTkLabel(self.popup_scroll, text="상품 목록을 조회할 수 없습니다.", font=("Malgun Gothic", 13), text_color="#EF4444").pack(pady=20)

    def _filter_product_list_popup(self, event):
        """검색어 입력 시 실시간 리스트 필터링"""
        query = self.search_entry.get().strip()
        self._render_popup_product_list(query)

    def _select_product_from_popup(self, product_name):
        """팝업창에서 상품명 선택 시 변수 변경, 창 닫기 및 그래프 즉각 갱신"""
        self.selected_product_var.set(product_name)
        if hasattr(self, 'popup') and self.popup.winfo_exists():
            self.popup.destroy()
        self._draw_product_charts()

    def _update_product_selector(self):
        """분석 완료 시점에 매출 데이터를 합산하고 상품 선택창을 기본 세팅"""
        if self.analyzer.raw_df is None:
            self.selected_product_var.set("데이터 분석을 먼저 진행해주세요.")
            self.product_sales_dict = {}
            self.product_dir_sales_dict = {}
            self.product_indir_sales_dict = {}
            return
            
        m = self.analyzer._get_column_mapping(self.analyzer.raw_df)
        pname_col = m.get('pname')
        sales_col = m.get('sales')
        dir_sales_col = m.get('dir_sales')
        indir_sales_col = m.get('indir_sales')
        
        # 상품별 총 매출액, 직접 매출액, 간접 매출액 집계
        self.product_sales_dict = {}
        self.product_dir_sales_dict = {}
        self.product_indir_sales_dict = {}
        
        if pname_col and pname_col in self.analyzer.raw_df.columns:
            df_clean = self.analyzer.raw_df.copy()
            
            # 총 매출액
            if sales_col:
                df_clean[sales_col] = pd.to_numeric(df_clean[sales_col].astype(str).str.replace(',', '').str.replace('₩', '').str.replace('원', ''), errors='coerce').fillna(0)
                self.product_sales_dict = df_clean.groupby(pname_col)[sales_col].sum().to_dict()
            
            # 직접 매출액
            if dir_sales_col:
                df_clean[dir_sales_col] = pd.to_numeric(df_clean[dir_sales_col].astype(str).str.replace(',', '').str.replace('₩', '').str.replace('원', ''), errors='coerce').fillna(0)
                self.product_dir_sales_dict = df_clean.groupby(pname_col)[dir_sales_col].sum().to_dict()
                
            # 간접 매출액
            if indir_sales_col:
                df_clean[indir_sales_col] = pd.to_numeric(df_clean[indir_sales_col].astype(str).str.replace(',', '').str.replace('₩', '').str.replace('원', ''), errors='coerce').fillna(0)
                self.product_indir_sales_dict = df_clean.groupby(pname_col)[indir_sales_col].sum().to_dict()
            
            # 고유 상품명 추출 및 정렬
            products = self.analyzer.raw_df[pname_col].dropna().unique().tolist()
            products = [str(p).strip() for p in products if str(p).strip() and str(p).strip() != '-']
            # 매출액 내림차순 정렬 (매출이 클수록 위로, 매출이 같거나 없을 경우 가나다순)
            products.sort(key=lambda p: (-self.product_sales_dict.get(p, 0), p))
            
            if products:
                # 정렬된 결과의 첫 번째 상품(매출 1위인 상품 혹은 가나다순 첫 상품)을 기본값으로 자동 로드
                default_prod = products[0]
                
                self.selected_product_var.set(default_prod)
                self._draw_product_charts()  # 즉각 첫 렌더링
            else:
                self.selected_product_var.set("엑셀에 추출된 상품명이 없습니다.")
        else:
            self.selected_product_var.set("상품명 컬럼을 찾을 수 없습니다.")

    def _draw_product_charts(self):
        """선택한 상품의 데이터로 기존 10대 차트를 필터링 렌더링 및 12대 성과 카드 실시간 업데이트"""
        for w in self.prod_metrics_scroll.winfo_children():
            w.destroy()
            
        if self.analyzer.raw_df is None:
            ctk.CTkLabel(self.prod_metrics_scroll, text="⚠️ 분석을 실행한 뒤 상품을 선택해주세요.", text_color="#EF4444", font=("Malgun Gothic", 14, "bold")).pack(pady=40)
            return
            
        selected = self.selected_product_var.get()
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
            
            # --- [Part 1] 상단 12대 성능 요약 카드 렌더링 (6x2) + 영역별 세부 분류 ---
            overall = sub_analyzer.get_overall_summary()
            region_summary = sub_analyzer.get_region_summary()
            if overall:
                self._render_kpi_summary_cards(overall, region_summary, self.prod_metrics_scroll)

            # --- [Part 2] 가이드라인 박스 렌더링 ---
            guide_box = ctk.CTkFrame(self.prod_metrics_scroll, fg_color="#101026", border_width=2, border_color="#FBBF24", corner_radius=15)
            guide_box.pack(fill="x", padx=10, pady=15)
            
            # 타이틀
            ctk.CTkLabel(guide_box, text="🧭 대표님을 위한 2대 광고투자 경영 나침반 가이드라인 (오른쪽날개 X 쇼팡식)", 
                         font=("Malgun Gothic", 16, "bold"), text_color="#34D399").pack(anchor="w", padx=25, pady=(20, 10))
            
            # 실시간 데이터 분석 변수 바인딩
            roas = 0.0
            spend_ratio = 0.0
            if overall:
                roas = overall.get('ROAS', 0.0)
                spend = overall.get('spend', 0.0)
                sales = overall.get('sales', 0.0)
                spend_ratio = (spend / sales * 100) if sales > 0 else 0.0
    
            # ROAS 및 광고비 비중 실시간 판정 멘트 빌드
            if overall:
                q1_verdict = (
                    f"현재 이 상품의 광고 ROAS는 {roas:.1f}%입니다. "
                    + ("기준선(330%)을 초과하여 흐름이 양호한 편이나, 사입 원가와 배송비를 감안하여 '가짜 흑자' 여부를 꼭 검증하셔야 합니다!" 
                       if roas >= 330 else 
                       "기준선(330%) 미만으로 저조하여 적자 장사일 위험이 큽니다! 아래 3대 차트로 증액 여부를 냉정히 판정해 보세요.")
                )
                q2_verdict = (
                    f"현재 이 상품의 매출 대비 광고비 비중은 {spend_ratio:.1f}%입니다. "
                    + (f"광고비 비중이 전체 매출의 10%를 돌파({spend_ratio:.1f}%)하여 위험 수위입니다! 행동 강령에 따라 즉시 제외 키워드를 정리하고 CVR을 끌어올려 광고비 비중을 마진율 밑으로 낮추셔야 합니다." 
                       if spend_ratio > 10 else 
                       "광고비 비중이 10% 이하로 안정 영역에서 잘 방어되고 있습니다. 마진율 마지노선 이하인지 계속 모니터링하세요.")
                )
            else:
                q1_verdict = "ROAS가 500% 이상으로 좋아 보여도, 사입 원가와 배송비가 비싸면 매달 100만 원씩 내 통장서 돈이 까이는 '가짜 흑자'일 수 있습니다! 아래 3대 핵심 차트를 입체적으로 교차 검증하여 증액 여부를 판정하셔야 합니다."
                q2_verdict = "택배를 열심히 포장해서 잘 파는 것처럼 보여도, 광고비가 내 마진을 갉아먹어 실제로 남는 돈이 줄어드는 '돈이 새는 늪'에 빠졌을 수 있습니다!"

            # Q1 섹션 프레임
            q1_section = ctk.CTkFrame(guide_box, fg_color="#070C16", corner_radius=10)
            q1_section.pack(fill="x", padx=20, pady=(0, 10))
            
            # Q1 질문
            q1_title = ctk.CTkLabel(q1_section, text=f"❓ Q1. 광고수익률(ROAS)이 좋아지면 무조건 광고비를 더 투자(증액)해도 될까요?\n➡️ [경영 판정법] : {q1_verdict}", 
                                    font=("Malgun Gothic", 12, "bold"), text_color="#F8FAFC", justify="left", wraplength=1050)
            q1_title.pack(anchor="w", padx=15, pady=(15, 5))
            
            # Q1 버튼 프레임 (오른쪽 정렬)
            q1_btn_frame = ctk.CTkFrame(q1_section, fg_color="transparent")
            q1_btn_frame.pack(fill="x", padx=15, pady=(0, 5))
            
            # Q1 상세 프레임 (기본적으로는 숨겨져 있음)
            q1_detail_frame = ctk.CTkFrame(q1_section, fg_color="transparent")
            
            q1_detail_text = (
                "  1️⃣ [최우선 판정선 - 12번 차트: 광고 차감 후 최종 순수익 vs 광고비 추이]\n"
                "    • [판단 기준] : 지출 광고비(빨간 선)를 우상향으로 증액했을 때, 하늘색 실선인 [진짜 최종 순이익]이 빨간 선보다 높은 위치에서 함께 평행하게 우상향하며 뻗어 올라가야만 진정한 성공 증액 상태입니다!\n"
                "    • [⚠️ 위험 신호] : 광고비 빨간 선은 쭉쭉 뻗어 올라가는데 하늘색 순이익 선이 아래로 꺾이거나 0원 밑(영하 적자 구간)으로 처박힌다면, 겉으로만 포장이 바쁘고 실제로는 '가짜 흑자 독수독과' 장사이므로 즉시 증액을 멈춰야 합니다.\n\n"
                f"  2️⃣ [효율 검증 - 3번 차트: 광고비 vs ROAS 추이]\n"
                f"    • [현재 상태] : 현재 상품의 평균 광고 ROAS는 {roas:.1f}%로, 흑자 기준선(330%) 대비 " + (
                    "안정권 위에 있습니다. 일별 실시간 추이에서도 무너지지 않는지 대조해 보세요." if roas >= 330 else
                    "저조하여 비효율 헛클릭 키워드에 예산이 새고 있을 가능성이 높습니다! 즉시 제외 키워드를 점검하십시오."
                ) + "\n\n"
                "  3️⃣ [이익 안전 마진띠 - 8번 차트: 날짜별 광고비·광고매출 추이]\n"
                "    • [판단 기준] : 아래 빨간 실선(광고비)과 위 하늘색 실선(광고매출액) 사이의 벌어진 간격(이익 공간)이 좁혀지지 않고 점점 더 아득히 멀어지는 '확장형 대칭'을 이루고 있는지 확인하세요. 이 간격이 태평양처럼 넓어질수록 사장님의 주머니가 두둑해집니다.\n"
                "    • [⚠️ 위험 신호] : 광고비 예산을 쏟아부었는데 두 선의 간격이 서로 키스하듯 달라붙거나 심지어 교차한다면, 번 돈의 100%를 쿠팡 광고비로 기부하고 있는 비상 적자 상태이므로 절대 광고비를 1원도 올리시면 안 됩니다!"
            )
            
            q1_detail_label = ctk.CTkLabel(q1_detail_frame, text=q1_detail_text, font=("Malgun Gothic", 12), text_color="#F8FAFC", justify="left", wraplength=1050)
            q1_detail_label.pack(anchor="w", padx=15, pady=(5, 15))
            
            def toggle_q1():
                if q1_detail_frame.winfo_viewable():
                    q1_detail_frame.pack_forget()
                    q1_btn.configure(text="자세한 내용 보기 🔽", fg_color="#1E293B")
                else:
                    q1_detail_frame.pack(fill="x")
                    q1_btn.configure(text="자세한 내용 접기 🔼", fg_color="#3B82F6")
                    
            q1_btn = ctk.CTkButton(q1_btn_frame, text="자세한 내용 보기 🔽", font=("Malgun Gothic", 11, "bold"), 
                                   width=130, height=28, fg_color="#1E293B", hover_color="#2D3748", command=toggle_q1)
            q1_btn.pack(side="right")


            # Q2 섹션 프레임
            q2_section = ctk.CTkFrame(guide_box, fg_color="#070C16", corner_radius=10)
            q2_section.pack(fill="x", padx=20, pady=(0, 20))
            
            # Q2 질문
            q2_title = ctk.CTkLabel(q2_section, text=f"❓ Q2. 광고비가 더 나가지만 판매량(주문수)도 증가하면 줄이지 말고 계속 더 투자해야 할까요?\n➡️ [경영 판정법] : {q2_verdict}", 
                                    font=("Malgun Gothic", 12, "bold"), text_color="#F8FAFC", justify="left", wraplength=1050)
            q2_title.pack(anchor="w", padx=15, pady=(15, 5))
            
            # Q2 버튼 프레임 (오른쪽 정렬)
            q2_btn_frame = ctk.CTkFrame(q2_section, fg_color="transparent")
            q2_btn_frame.pack(fill="x", padx=15, pady=(0, 5))
            
            # Q2 상세 프레임 (기본적으로는 숨겨져 있음)
            q2_detail_frame = ctk.CTkFrame(q2_section, fg_color="transparent")
            
            q2_detail_text = (
                "  1️⃣ [집중 관찰 영역 - 11번 차트: 광고비 비중 및 광고 기여도 추이]\n"
                f"    • [비법 분석] : 노란색 [매출 대비 광고비 비중 선]이 사장님이 계산기 탭에 적은 [내 마진율 점선(초록색)]보다 높게 치솟았다면 100% 적자 장사입니다! (현재 이 상품의 광고비 비중은 {spend_ratio:.1f}%)\n"
                "    • [행동 강령] : 특히 광고비 비중이 전체 매출의 10%를 넘어가면(빨간 땡땡이 경고선 돌파 시) 즉시 제외 키워드를 정리하고, 썸네일과 상세페이지를 뜯어고쳐 전환율(CVR)을 끌어올려 광고비 비중을 마진율 밑으로 강제로 밀어 넣으셔야 합니다!"
            )
            
            q2_detail_label = ctk.CTkLabel(q2_detail_frame, text=q2_detail_text, font=("Malgun Gothic", 12), text_color="#F8FAFC", justify="left", wraplength=1050)
            q2_detail_label.pack(anchor="w", padx=15, pady=(5, 15))
            
            def toggle_q2():
                if q2_detail_frame.winfo_viewable():
                    q2_detail_frame.pack_forget()
                    q2_btn.configure(text="자세한 내용 보기 🔽", fg_color="#1E293B")
                else:
                    q2_detail_frame.pack(fill="x")
                    q2_btn.configure(text="자세한 내용 접기 🔼", fg_color="#3B82F6")
                    
            q2_btn = ctk.CTkButton(q2_btn_frame, text="자세한 내용 보기 🔽", font=("Malgun Gothic", 11, "bold"), 
                                   width=130, height=28, fg_color="#1E293B", hover_color="#2D3748", command=toggle_q2)
            q2_btn.pack(side="right")

            # --- [Part 2.5] 광고효율 돋보기 분석 및 처방전 렌더링 ---
            pd_data = sub_analyzer.get_daily_performance()
            if pd_data and not pd_data['total'].empty:
                sub_df = pd_data['total'].copy()
                sub_df = sub_df.sort_values('p_date')
                by_region_data = pd_data.get('by_region', pd.DataFrame())
                
                # 영역별 진단 처방전 렌더링
                try:
                    self._render_magnifier_diagnosis(sub_df, self.prod_metrics_scroll, by_region_df=by_region_data)
                except Exception as e:
                    import traceback; traceback.print_exc()
                    ctk.CTkLabel(self.prod_metrics_scroll, text=f"⚠️ 돋보기 진단 오류: {e}", text_color="#EF4444", font=("Malgun Gothic", 12)).pack(pady=20)

                # 영역별 상대 지수 차트 렌더링
                chart_card = ctk.CTkFrame(self.prod_metrics_scroll, fg_color="#0B0B1A", border_width=1, border_color="#333", corner_radius=12)
                chart_card.pack(fill="x", padx=10, pady=10)
                
                try:
                    self._render_magnifier_chart(sub_df, chart_card, by_region_df=by_region_data)
                except Exception as e:
                    import traceback; traceback.print_exc()
                    ctk.CTkLabel(chart_card, text=f"⚠️ 돋보기 차트 렌더링 중 오류 발생: {e}", text_color="#EF4444", font=("Malgun Gothic", 12)).pack(pady=20)

            # --- [Part 3] 성과 추이 차트 렌더링 ---
            pd_data = sub_analyzer.get_daily_performance()
            if pd_data and not pd_data['total'].empty:
                sub_df = pd_data['total']
                sub_kw = sub_analyzer.summary_df
                
                try:
                    # _render_large_trend_chart를 통해 상품 전용 10대 대형 추이 차트 렌더링
                    self._render_large_trend_chart(sub_df, sub_kw, self.prod_metrics_scroll)
                except Exception as e:
                    import traceback; traceback.print_exc()
                    ctk.CTkLabel(self.prod_metrics_scroll, text=f"⚠️ 상품 차트 렌더링 중 오류 발생: {e}", text_color="#EF4444", font=("Malgun Gothic", 12)).pack(pady=20)
        except Exception as e:
            import traceback; traceback.print_exc()
            ctk.CTkLabel(self.prod_metrics_scroll, text=f"⚠️ 상품 데이터 분석 중 오류 발생: {e}", text_color="#EF4444", font=("Malgun Gothic", 14, "bold")).pack(pady=40)
            
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
        today_parsed = self._parse_memo_date_to_key(today_str)
        today_memos = [m for m in self.memos if self._parse_memo_date_to_key(m['date']) == today_parsed]
        if today_memos:
            self.memo_input.insert("0.0", today_memos[-1]['memo'])
        
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

    def _parse_memo_date_to_key(self, date_str):
        """메모 날짜 문자열을 정렬/비교에 적합한 YYYY-MM-DD 형식으로 변환"""
        ds = str(date_str).strip()
        try:
            # YYYY-MM-DD 또는 YY-MM-DD
            if '-' in ds:
                parts = ds.split('-')
                year = int(parts[0])
                if year < 100:  # 2자리 연도 처리
                    year += 2000
                return f"{year:04d}-{int(parts[1]):02d}-{int(parts[2]):02d}"
            # YYMMDD (예: 260428)
            if len(ds) == 6 and ds.isdigit():
                year = 2000 + int(ds[0:2])
                month = int(ds[2:4])
                day = int(ds[4:6])
                return f"{year:04d}-{month:02d}-{day:02d}"
            # YYYYMMDD (예: 20260428)
            if len(ds) == 8 and ds.isdigit():
                year = int(ds[0:4])
                month = int(ds[4:6])
                day = int(ds[6:8])
                return f"{year:04d}-{month:02d}-{day:02d}"
        except:
            pass
        return ds

    def _refresh_memo_list(self):
        for w in self.memo_list_frame.winfo_children(): w.destroy()
        
        if not self.memos:
            ctk.CTkLabel(self.memo_list_frame, text="저장된 기록이 없습니다.", 
                         font=("Malgun Gothic", 13), text_color="#6B7280").pack(pady=20)
            return

        sorted_memos = sorted(self.memos, key=lambda m: self._parse_memo_date_to_key(m['date']), reverse=True)
        
        for memo_item in sorted_memos:
            memo_id = memo_item['id']
            date_str = memo_item['date']
            memo_text = memo_item['memo']
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
            
            ctk.CTkButton(btn_frame, text="수정", width=60, height=26, fg_color="#2563EB", 
                          font=("Malgun Gothic", 11), 
                          command=lambda m_id=memo_id: self._edit_memo(m_id)).pack(side="left", padx=3)
            ctk.CTkButton(btn_frame, text="삭제", width=60, height=26, fg_color="#DC2626",
                          font=("Malgun Gothic", 11),
                          command=lambda m_id=memo_id: self._delete_memo(m_id)).pack(side="left", padx=3)

    def _edit_memo(self, memo_id):
        """기존 메모를 좌측 편집 영역에 불러오기 (수정 모드)"""
        memo_item = next((m for m in self.memos if m['id'] == memo_id), None)
        if memo_item:
            self.editing_memo_id = memo_id
            self.memo_date_var.set(memo_item['date'])
            self.memo_input.delete("0.0", "end")
            self.memo_input.insert("0.0", memo_item['memo'])
            self.memo_edit_label.configure(text=f"[{memo_item['date']} 수정 중]", text_color="#F59E0B")

    def _load_memo(self, memo_id):
        self._edit_memo(memo_id)

    def _new_memo(self):
        """새 메모 작성 모드로 전환"""
        self.editing_memo_id = None
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

        if getattr(self, 'editing_memo_id', None) is not None:
            memo_item = next((m for m in self.memos if m['id'] == self.editing_memo_id), None)
            if memo_item:
                memo_item['date'] = date_str
                memo_item['memo'] = memo
                message_text = f"{date_str} 기록이 수정되었습니다."
            else:
                memo_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
                self.memos.append({"id": memo_id, "date": date_str, "memo": memo})
                message_text = f"{date_str} 기록이 저장되었습니다."
        else:
            memo_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
            self.memos.append({"id": memo_id, "date": date_str, "memo": memo})
            message_text = f"{date_str} 기록이 저장되었습니다."

        with open("ad_memos.json", "w", encoding="utf-8") as f:
            json.dump(self.memos, f, ensure_ascii=False, indent=4)
        
        self.editing_memo_id = None
        self._refresh_memo_list()
        self.memo_edit_label.configure(text=f"[{date_str} 저장 완료]", text_color="#10B981")
        messagebox.showinfo("알림", message_text)

    def _delete_memo(self, memo_id):
        memo_item = next((m for m in self.memos if m['id'] == memo_id), None)
        if memo_item:
            if messagebox.askyesno("확인", f"{memo_item['date']} 기록을 삭제하시겠습니까?"):
                self.memos = [m for m in self.memos if m['id'] != memo_id]
                with open("ad_memos.json", "w", encoding="utf-8") as f:
                    json.dump(self.memos, f, ensure_ascii=False, indent=4)
                
                if getattr(self, 'editing_memo_id', None) == memo_id:
                    self.editing_memo_id = None
                    self._new_memo()
                    
                self._refresh_memo_list()

    def _setup_diagnosis_tab(self):
        self.diag_scroll = ctk.CTkScrollableFrame(self.tab_diagnosis, fg_color="#0B0B1A")
        self.diag_scroll.pack(fill="both", expand=True)
        
        self.diag_title = ctk.CTkLabel(self.diag_scroll, text="🛡️ AI 전략 나침반", font=("Malgun Gothic", 28, "bold"), text_color="#60A5FA")
        self.diag_title.pack(pady=30)
        
        self.advice_container = ctk.CTkFrame(self.diag_scroll, fg_color="transparent")
        self.advice_container.pack(fill="both", expand=True, padx=50)

    def _setup_calculator_tab(self):
        # 탭 전체를 스크롤 가능하게 구성
        calc_scroll = ctk.CTkScrollableFrame(self.tab_calculator, fg_color="#0B0B1A")
        calc_scroll.pack(fill="both", expand=True)
        
        title_lbl = ctk.CTkLabel(calc_scroll, text="🧮 ROAS 순익 계산기 (초등생도 1초 이해하는 마진·광고 내비게이터)", font=("Malgun Gothic", 26, "bold"), text_color="#38BDF8")
        title_lbl.pack(pady=20)
        
        # 좌우 분할을 위한 메인 컨테이너
        calc_split = ctk.CTkFrame(calc_scroll, fg_color="transparent")
        calc_split.pack(fill="both", expand=True, padx=30, pady=10)
        
        # 1. 좌측 입력 및 가이드북 패널
        left_panel = ctk.CTkFrame(calc_split, fg_color="#101026", border_width=2, border_color="#1E293B", corner_radius=15)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 15), pady=10)
        
        lbl_input_title = ctk.CTkLabel(left_panel, text="📥 제품 및 광고정보 입력하기", font=("Malgun Gothic", 18, "bold"), text_color="#38BDF8")
        lbl_input_title.pack(pady=15, padx=20, anchor="w")
        
        # 💡 계산기 목적 안내 가이드 문구 배너 추가
        info_banner = ctk.CTkFrame(left_panel, fg_color="#1E1E38", border_width=1, border_color="#3B82F6", corner_radius=8)
        info_banner.pack(fill="x", padx=20, pady=(0, 10))
        
        info_lbl = ctk.CTkLabel(
            info_banner,
            text="💡 이 계산기는 해당 상품의 정보와 일정 기간 동안 소비한 광고비 총액, 팔린 수량을 입력하여\n    이 광고로 내가 실제로 돈을 번 것인지, 아니면 마이너스 적자로 운영 중인지 판가름하기 위해 설계되었습니다.",
            font=("Malgun Gothic", 12),
            text_color="#93C5FD",
            justify="left"
        )
        info_lbl.pack(padx=15, pady=10, anchor="w")
        
        form_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        form_frame.pack(fill="x", padx=20, pady=5)
        
        inputs = [
            ("제품 명 (상품 이름)", "p_name", "전기장판"),
            ("제품 원가 (사입 단가 ₩)", "p_cost", "20,000"),
            ("판매 갯수 (팔린 수량 개)", "p_qty", "30"),
            ("실제 판매가격 (최종 결제액 ₩)", "p_price", "42,900"),
            ("쿠팡 등록가 (할인 전 가격 ₩)", "p_coupang", "52,900"),
            ("수수료율 (%)", "p_fee_pct", "11.0"),
            ("부가세율 (%)", "p_tax_pct", "10.0"),
            ("배송비/물류비 (₩)", "p_shipping", "3,000"),
            ("포장/기타비용 (₩)", "p_etc_cost", "500"),
            ("광고비용 (집행 광고비 ₩)", "p_ad_spend", "400,000")
        ]
        
        self.calc_vars = {}
        for idx, (label_txt, var_name, def_val) in enumerate(inputs):
            # 레이블을 감싸는 컨테이너 프레임 생성 (가로 정렬용)
            lbl_container = ctk.CTkFrame(form_frame, fg_color="transparent")
            lbl_container.grid(row=idx, column=0, padx=10, pady=6, sticky="w")
            
            lbl = ctk.CTkLabel(lbl_container, text=label_txt, font=("Malgun Gothic", 13, "bold"), text_color="#E2E8F0")
            lbl.pack(side="left")
            
            if var_name in ["p_qty", "p_ad_spend"]:
                req_lbl = ctk.CTkLabel(lbl_container, text=" (입력필요)", font=("Malgun Gothic", 12, "bold"), text_color="#F87171")
                req_lbl.pack(side="left")
            
            entry = ctk.CTkEntry(form_frame, width=320, height=32, font=("Malgun Gothic", 13), fg_color="#1E1E38", text_color="white", border_color="#3B82F6")
            entry.insert(0, def_val)
            entry.grid(row=idx, column=1, padx=10, pady=6, sticky="e")
            entry.bind("<KeyRelease>", lambda e: self._calculate_roas())
            self.calc_vars[var_name] = entry
            
        form_frame.grid_columnconfigure(1, weight=1)
        
        btn_calc = ctk.CTkButton(left_panel, text="🔄 즉시 계산 및 분석", command=self._calculate_roas, fg_color="#2563EB", hover_color="#1D4ED8", height=45, font=("Malgun Gothic", 14, "bold"))
        btn_calc.pack(fill="x", padx=20, pady=15)
        
        # 💡 좌측 하단: 가독성 극대화를 위해 CTkTextbox(스크롤바 자동 생성) 가이드북 도입
        guide_frame = ctk.CTkFrame(left_panel, fg_color="#0F172A", border_width=1, border_color="#334155", corner_radius=10)
        guide_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        lbl_g_title = ctk.CTkLabel(guide_frame, text="📖 초등생도 1초 이해하는 계산기 사용 매뉴얼 (스크롤 가능 🖱️)", font=("Malgun Gothic", 12, "bold"), text_color="#34D399")
        lbl_g_title.pack(pady=(10, 5), padx=15, anchor="w")
        
        # CTkTextbox를 사용하여 글씨가 찌그러지거나 잘리지 않도록 구현
        self.guide_box = ctk.CTkTextbox(guide_frame, height=220, font=("Malgun Gothic", 12), fg_color="#070C16", text_color="#F8FAFC", wrap="word", corner_radius=8)
        self.guide_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        guide_text = (
            "🧸 [초등생도 1초 장사 마스터! - 쿠팡 광고 쉽게 이해하기]\n\n"
            "안녕 대표님! 매일 땀 흘리며 성실하게 장사하느라 정말 고생이 많아!\n"
            "어려운 용어 때문에 골치 아팠지? 내가 아주 쉽고 재미있게 이 계산기를 쓰는 법을 가르쳐 줄게! 딱 세 가지만 알면 끝이야!\n\n"
            "🛡️ 1. '앤드 로하스 (END ROAS)' -> \"내 돈 지킴이 방패선!\"\n"
            "  • 친구들에게 나눠줄 만 원짜리 할인쿠폰을 만들어서 전기장판을 팔았어!\n"
            "  • 근데 쿠팡 광고판은 할인 전 가격인 52,900원(등록가) 기준으로 광고 매출을 뻥튀기해서 잡는 바보야!\n"
            "  • 그래서 광고 보고서에 나오는 수익 점수(ROAS)가 이 [방패선(END ROAS)] 점수 밑으로 떨어지면?\n"
            "  • 사장님 통장에서 야금야금 돈이 깎여나가고 있는 무서운 '적자 게임'을 하고 있는 거란다!\n"
            "  • 적어도 이 방패선 점수보다는 광고 점수가 높게 나와야 겨우 본전이고, 방패선보다 훨씬 높게(예: 700% 이상) 나와야 내 지갑에 용돈이 진짜 쌓여!\n\n"
            "🛑 2. '20% 최대원가' -> \"상품 떼어오기 마지노선!\"\n"
            "  • '나 손님들한테 42,900원에 팔아서 수수료랑 세금 다 내고도, 내 몫으로 마진 20%는 꼭 남겨서 용돈 할래!'\n"
            "  • 그럼 문방구 아저씨한테 가서 이 전기장판을 1개에 얼마 이하로 떼어와야 할까?\n"
            "  • 그 대답이 바로 [최대원가] 금액이야! 만약 도매 단가가 최대원가보다 비싸면 마진 20%를 절대로 지킬 수 없어! 사입하기 전에 꼭 확인해봐!\n\n"
            "📝 3. 일주일/한 달 장사 끝나고 돈 벌었나 체크할 때!\n"
            "  • 광고 돌리고 일주일이나 한 달이 지나서 광고 지표 보고서를 열어봐!\n"
            "  • 거기 적힌 [팔린 개수]와 [광고비] 딱 2개만 여기에 입력해봐!\n"
            "  • 그럼 내가 쓴 광고비 대비 진짜 지갑에 돈이 남았는지, 아니면 광고 아저씨한테 다 털렸는지를 단번에 정산해준단다! 간편하지?"
        )
        self.guide_box.insert("0.0", guide_text)
        self.guide_box.configure(state="disabled") # 읽기 전용 모드 적용
        
        # 2. 우측 결과 패널
        right_panel = ctk.CTkFrame(calc_split, fg_color="#101026", border_width=2, border_color="#3B82F6", corner_radius=15)
        right_panel.pack(side="right", fill="both", expand=True, padx=(15, 0), pady=10)
        
        lbl_res_title = ctk.CTkLabel(right_panel, text="📋 마진 분석 성과표 (정석 기준)", font=("Malgun Gothic", 18, "bold"), text_color="#34D399")
        lbl_res_title.pack(pady=15, padx=20, anchor="w")
        
        self.calc_res_frame = ctk.CTkFrame(right_panel, fg_color="#0F0F24", border_width=1, border_color="#2E2E4A", corner_radius=10)
        self.calc_res_frame.pack(fill="both", expand=True, padx=20, pady=(5, 20))
        
        self._calculate_roas()

    def _calculate_roas(self):
        for w in self.calc_res_frame.winfo_children():
            w.destroy()
            
        try:
            # 값 파싱
            p_name = self.calc_vars["p_name"].get().strip() or "미정 상품"
            p_cost = float(self.calc_vars["p_cost"].get().replace(",", "") or 0)
            p_qty = float(self.calc_vars["p_qty"].get().replace(",", "") or 0)
            p_price = float(self.calc_vars["p_price"].get().replace(",", "") or 0)
            p_coupang = float(self.calc_vars["p_coupang"].get().replace(",", "") or 0)
            p_fee_pct = float(self.calc_vars["p_fee_pct"].get().replace(",", "") or 0) / 100.0
            p_tax_pct = float(self.calc_vars["p_tax_pct"].get().replace(",", "") or 0) / 100.0
            p_shipping = float(self.calc_vars["p_shipping"].get().replace(",", "") or 0)
            p_etc_cost = float(self.calc_vars["p_etc_cost"].get().replace(",", "") or 0)
            p_ad_spend = float(self.calc_vars["p_ad_spend"].get().replace(",", "") or 0)
            
            # 1. 비용 연산
            # 수수료: 쿠팡 WING 수수료 규정에 따라 실제 판매가(p_price) 기준으로 계산 (엑셀 매칭: 42,900 * 11% = 4,719)
            fee = p_price * p_fee_pct
            # 부가세 예수금: 실제 판매가(p_price) 기준으로 산정 (엑셀 매칭: 42,900 * 10% = 4,290)
            tax = p_price * p_tax_pct
            
            # 1개당 쿠팡 정산금액 (수수료, 부가세, 배송비 차감 후 사장님 주머니에 꽂히는 금액)
            settlement_per_item = p_price - fee - tax - p_shipping
            
            # 1개당 순이익 (정산액에서 원가와 포장기타비용까지 전부 공제)
            profit_per_item = settlement_per_item - p_cost - p_etc_cost
            margin_rate = (profit_per_item / p_price * 100) if p_price > 0 else 0
            
            # 매출 및 현재 ROAS (매출액 = 실제 판매가 * 수량)
            sales = p_price * p_qty
            roas = (sales / p_ad_spend * 100) if p_ad_spend > 0 else 0
            
            # 광고비까지 차감한 최종 순이익
            real_profit = (profit_per_item * p_qty) - p_ad_spend
            
            # 🎯 앤드 로하스 (END ROAS) - 쿠팡 광고 보고서의 왜곡 매출(부가세 포함 부풀려진 금액)을 커버하기 위한 역산 공식
            # 엑셀 매칭 공식: (쿠팡 등록가 * 1.1) / 1개당 순익 * 100%
            real_end_roas = ((p_coupang * 1.1) / profit_per_item * 100) if profit_per_item > 0 else 0
            
            # 🛑 최대 사입원가 한계 (최대원가)
            # 사장님의 의도: 실제 판매가에 팔아도 최소 마진율 '20%'를 지켜낼 수 있는 도매가격 마지노선
            # 공식: 실제 판매가 - 수수료 - 부가세 - 배송비 - 기타비용 - (실제 판매가 * 최소 목표 마진 20%)
            real_max_cost = p_price - fee - tax - p_shipping - p_etc_cost - (p_price * 0.2)
            if real_max_cost < 0:
                real_max_cost = 0
            
            # UI 결과 배치 (Premium Layout)
            res_scroll = ctk.CTkFrame(self.calc_res_frame, fg_color="transparent")
            res_scroll.pack(fill="both", expand=True, padx=20, pady=15)
            
            # --- [Part 1] 상단 3대 핵심 성과 보드 ---
            board_frame = ctk.CTkFrame(res_scroll, fg_color="transparent")
            board_frame.pack(fill="x", pady=(0, 15))
            
            # 1-1. 최종 순이익 카드
            is_profit = real_profit >= 0
            profit_bg = "#064E3B" if is_profit else "#7C2D12"
            profit_border = "#10B981" if is_profit else "#EF4444"
            profit_text_color = "#34D399" if is_profit else "#F87171"
            
            card_profit = ctk.CTkFrame(board_frame, fg_color=profit_bg, border_width=1.5, border_color=profit_border, corner_radius=12)
            card_profit.pack(side="left", expand=True, fill="both", padx=5)
            ctk.CTkLabel(card_profit, text="💰 내 용돈 주머니 (최종 순이익)", font=("Malgun Gothic", 11, "bold"), text_color="#E2E8F0").pack(pady=(10, 2))
            ctk.CTkLabel(card_profit, text=f"₩{real_profit:,.0f}", font=("Malgun Gothic", 19, "bold"), text_color=profit_text_color).pack(pady=(2, 10))
            
            # 1-2. 앤드 로하스 카드
            card_end_roas = ctk.CTkFrame(board_frame, fg_color="#1E1E38", border_width=1, border_color="#60A5FA", corner_radius=12)
            card_end_roas.pack(side="left", expand=True, fill="both", padx=5)
            ctk.CTkLabel(card_end_roas, text="🎯 앤드 로하스 (END ROAS)", font=("Malgun Gothic", 11, "bold"), text_color="#E2E8F0").pack(pady=(10, 2))
            roas_val_str = f"{real_end_roas:.1f}%" if real_end_roas > 0 else "마진 없음"
            ctk.CTkLabel(card_end_roas, text=roas_val_str, font=("Malgun Gothic", 19, "bold"), text_color="#60A5FA").pack(pady=(2, 10))
            
            # 1-3. 최대 제품원가 카드
            card_max_cost = ctk.CTkFrame(board_frame, fg_color="#1E1E38", border_width=1, border_color="#FBBF24", corner_radius=12)
            card_max_cost.pack(side="left", expand=True, fill="both", padx=5)
            ctk.CTkLabel(card_max_cost, text="🛑 20% 마진용 최대원가", font=("Malgun Gothic", 11, "bold"), text_color="#E2E8F0").pack(pady=(10, 2))
            cost_val_str = f"₩{real_max_cost:,.0f}"
            ctk.CTkLabel(card_max_cost, text=cost_val_str, font=("Malgun Gothic", 19, "bold"), text_color="#FBBF24").pack(pady=(2, 10))
            
            # --- [Part 2] 중단: 🧾 상세 정산 영수증 명세서 ---
            receipt_lbl = ctk.CTkLabel(res_scroll, text="🧾 정산 및 마진 상세 영수증 (1개당 분석)", font=("Malgun Gothic", 14, "bold"), text_color="#94A3B8")
            receipt_lbl.pack(anchor="w", pady=(10, 5))
            
            receipt_frame = ctk.CTkFrame(res_scroll, fg_color="#0D0D21", border_width=1, border_color="#1E293B", corner_radius=10)
            receipt_frame.pack(fill="x", pady=5)
            
            receipt_items = [
                ("[+] 실제 판매가격 (소비자 결제액)", f"₩{p_price:,.0f}", "#E2E8F0", False),
                ("[-] 쿠팡 카테고리 수수료", f"-₩{fee:,.0f}", "#F87171", False),
                ("[-] 부가세 예수금 (세금)", f"-₩{tax:,.0f}", "#F87171", False),
                ("[-] 배송비/물류수수료", f"-₩{p_shipping:,.0f}", "#F87171", False),
                ("[=] 1개당 쿠팡 순정산액", f"₩{settlement_per_item:,.0f}", "#34D399", True),
                ("[-] 제품 사입 원가", f"-₩{p_cost:,.0f}", "#F87171", False),
                ("[-] 포장 및 기타 고정비", f"-₩{p_etc_cost:,.0f}", "#F87171", False),
                ("[=] 1개당 최종 순이익", f"₩{profit_per_item:,.0f}", "#10B981", True),
                ("[%] 최종 마진율", f"{margin_rate:.2f}%", "#FBBF24", True)
            ]
            
            receipt_grid = ctk.CTkFrame(receipt_frame, fg_color="transparent")
            receipt_grid.pack(fill="x", padx=20, pady=12)
            
            for r_idx, (label, val, color, is_bold) in enumerate(receipt_items):
                font_weight = "bold" if is_bold else "normal"
                font_size = 12 if not is_bold else 13
                
                lbl = ctk.CTkLabel(receipt_grid, text=label, font=("Malgun Gothic", font_size, font_weight), text_color="#94A3B8" if not is_bold else "#E2E8F0")
                lbl.grid(row=r_idx, column=0, pady=3, sticky="w")
                
                v_lbl = ctk.CTkLabel(receipt_grid, text=val, font=("Malgun Gothic", font_size, font_weight), text_color=color)
                v_lbl.grid(row=r_idx, column=1, pady=3, sticky="e")
                
            receipt_grid.grid_columnconfigure(1, weight=1)
            
            # --- [Part 3] 총합 지표 요약 ---
            total_lbl = ctk.CTkLabel(res_scroll, text=f"📊 총합 데이터 요약 ({p_qty:,.0f}개 판매 기준)", font=("Malgun Gothic", 14, "bold"), text_color="#94A3B8")
            total_lbl.pack(anchor="w", pady=(15, 5))
            
            total_frame = ctk.CTkFrame(res_scroll, fg_color="#0D0D21", border_width=1, border_color="#1E293B", corner_radius=10)
            total_frame.pack(fill="x", pady=5)
            
            total_metrics = [
                ("총 판매 매출액", f"₩{sales:,.0f}", "white"),
                ("총 집행 광고비", f"₩{p_ad_spend:,.0f}", "#F87171"),
                ("현재 광고 ROAS (실제)", f"{roas:.1f}%", "#60A5FA")
            ]
            
            total_grid = ctk.CTkFrame(total_frame, fg_color="transparent")
            total_grid.pack(fill="x", padx=20, pady=10)
            for t_idx, (label, val, color) in enumerate(total_metrics):
                lbl = ctk.CTkLabel(total_grid, text=label, font=("Malgun Gothic", 12), text_color="#94A3B8")
                lbl.grid(row=t_idx, column=0, pady=3, sticky="w")
                
                v_lbl = ctk.CTkLabel(total_grid, text=val, font=("Malgun Gothic", 12, "bold"), text_color=color)
                v_lbl.grid(row=t_idx, column=1, pady=3, sticky="e")
            total_grid.grid_columnconfigure(1, weight=1)
            
            # --- [Part 4] 💡 초등생용 AI 마진 & 광고 진단 처방전 ---
            rx_lbl = ctk.CTkLabel(res_scroll, text="🛡️ 초등생도 1초 이해하는 마케팅 내비게이터 처방", font=("Malgun Gothic", 15, "bold"), text_color="#FBBF24")
            rx_lbl.pack(anchor="w", pady=(20, 5))
            
            rx_card = ctk.CTkFrame(res_scroll, fg_color=profit_bg, border_width=1, border_color=profit_border, corner_radius=12)
            rx_card.pack(fill="x", pady=(5, 10))
            
            # 정량적 처방 및 초등생용 비유 지문 생성
            if not is_profit:
                roas_diff = real_end_roas - roas
                deficit = p_ad_spend - (profit_per_item * p_qty)
                
                diag_msg = (
                    f"🚨 [적자 비상! 내 지갑 털리는 중!]\n"
                    f"쿠팡 광고판에 나오는 수익 점수(ROAS)가 {roas:.1f}%인데, 우리의 내 돈 지킴이 방패선인 "
                    f"[앤드 로하스(END ROAS) {real_end_roas:.1f}%] 밑으로 무려 {roas_diff:.1f}%p나 주저앉았어요!\n"
                    f"장사를 할수록 내 통장에서 ₩{deficit:,.0f}씩 슬금슬금 빠져나가고 있답니다. 즉시 탈출 조치를 취해야 해요!\n\n"
                    f"💡 [이렇게 해결해 보아요! (둘 중 하나 꼭 하기)]\n"
                    f"1. [상품 가격 올리기] : 손님이 결제하는 판매가격을 지금보다 올려서 내 주머니 마진을 채워보세요.\n"
                    f"2. [더 싸게 떼어오기] : 도매처 사장님한테 가서 제품 1개당 가격을 {cost_val_str} 이하로 더 싸게 달라고 떼를 써보세요!\n"
                    f"3. [알짜 손님 데려오기] : 쓰잘데기 없는 광고 키워드를 중단해서 광고판 수익률(ROAS)을 {real_end_roas:.1f}% 위로 번쩍 끌어올리세요!"
                )
            else:
                roas_diff = roas - real_end_roas
                
                diag_msg = (
                    f"🟢 [야호! 흑자 가속 페달 구간!]\n"
                    f"쿠팡 광고판 점수(ROAS {roas:.1f}%)가 우리의 내 돈 지킴이 방패선(END ROAS {real_end_roas:.1f}%)보다 "
                    f"무려 {roas_diff:.1f}%p 높게 솟아있어요! 지금은 세금 다 빼고도 ₩{real_profit:,.0f}의 알짜 이익이 통장에 쏙 꽂히는 신나는 구간입니다.\n\n"
                    f"📈 [더 크게 벌어들이는 꿀팁!]\n"
                    f"• 지금 마진 구조가 엄청 튼튼하니까, 광고 수익률이 앤드 로하스({real_end_roas:.1f}%) 아래로만 떨어지지 않게 슬슬 보면서 광고비를 더 든든하게 태워 판을 키우셔도 절대 망하지 않아요!\n"
                    f"• 사입 수량을 늘려 원가 단가를 더 싸게 깎아오면 마진율은 백만 배 더 솟구칩니다. 당장 고고싱!"
                )
                
            lbl_rx = ctk.CTkLabel(rx_card, text=diag_msg, font=("Malgun Gothic", 12), text_color="#E2E8F0", justify="left", wraplength=430)
            lbl_rx.pack(pady=15, padx=18, anchor="w")
            
        except Exception as ex:
            lbl_err = ctk.CTkLabel(self.calc_res_frame, text=f"입력값을 확인해주세요.\n({ex})", font=("Malgun Gothic", 12), text_color="#EF4444")
            lbl_err.pack(pady=20)

    def _setup_ai_simulator_tab(self):
        # 탭 전체를 스크롤 가능하게 구성
        sim_scroll = ctk.CTkScrollableFrame(self.tab_ai_simulator, fg_color="#0B0B1A")
        sim_scroll.pack(fill="both", expand=True)
        
        title_lbl = ctk.CTkLabel(sim_scroll, text="🔮 AI 광고 작동원리 & 미래 시뮬레이터", font=("Malgun Gothic", 26, "bold"), text_color="#EC4899")
        title_lbl.pack(pady=20)
        
        # 좌우 분할을 위한 메인 컨테이너
        sim_split = ctk.CTkFrame(sim_scroll, fg_color="transparent")
        sim_split.pack(fill="both", expand=True, padx=30, pady=10)
        
        # 1. 좌측 입력 패널
        left_panel = ctk.CTkFrame(sim_split, fg_color="#101026", border_width=2, border_color="#1E293B", corner_radius=15)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 15), pady=10)
        
        lbl_input_title = ctk.CTkLabel(left_panel, text="📥 시뮬레이션 조건 입력", font=("Malgun Gothic", 18, "bold"), text_color="#EC4899")
        lbl_input_title.pack(pady=15, padx=20, anchor="w")
        
        # 가이드 배너 추가
        info_banner = ctk.CTkFrame(left_panel, fg_color="#1E1E38", border_width=1, border_color="#EC4899", corner_radius=8)
        info_banner.pack(fill="x", padx=20, pady=(0, 10))
        
        info_lbl = ctk.CTkLabel(
            info_banner,
            text="💡 설정하신 일예산, 목표 ROAS, CPC 단가, 제품가격을 기반으로\n    쿠팡 AI 광고의 실제 예산 운용 한계와 예상 행동 방안을 진단합니다.",
            font=("Malgun Gothic", 12),
            text_color="#FBCFE8",
            justify="left"
        )
        info_lbl.pack(padx=15, pady=10, anchor="w")
        
        form_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        form_frame.pack(fill="x", padx=20, pady=5)
        
        inputs = [
            ("1. 일일 광고 예산 (₩)", "sim_budget", "30,000"),
            ("2. 목표 광고 효율 (ROAS %)", "sim_roas", "350"),
            ("3. 평균 CPC 단가 (₩)", "sim_cpc", "1,000"),
            ("4. 제품 판매 가격 (₩)", "sim_price", "20,000"),
            ("5. 대상 제품명 (카테고리)", "sim_pname", "가방백팩")
        ]
        
        self.sim_vars = {}
        for idx, (label_txt, var_name, def_val) in enumerate(inputs):
            lbl_container = ctk.CTkFrame(form_frame, fg_color="transparent")
            lbl_container.grid(row=idx, column=0, padx=10, pady=6, sticky="w")
            
            lbl = ctk.CTkLabel(lbl_container, text=label_txt, font=("Malgun Gothic", 13, "bold"), text_color="#E2E8F0")
            lbl.pack(side="left")
            
            entry = ctk.CTkEntry(form_frame, width=320, height=32, font=("Malgun Gothic", 13), fg_color="#1E1E38", text_color="white", border_color="#EC4899")
            entry.insert(0, def_val)
            entry.grid(row=idx, column=1, padx=10, pady=6, sticky="e")
            entry.bind("<KeyRelease>", lambda e: self._calculate_ai_simulation())
            self.sim_vars[var_name] = entry
            
        form_frame.grid_columnconfigure(1, weight=1)
        
        btn_calc = ctk.CTkButton(left_panel, text="🔮 AI 작동 원리 시뮬레이션 시작", command=self._calculate_ai_simulation, fg_color="#DB2777", hover_color="#BE185D", height=45, font=("Malgun Gothic", 14, "bold"))
        btn_calc.pack(fill="x", padx=20, pady=15)
        
        # 🔑 API 연동 프레임 추가
        api_frame = ctk.CTkFrame(left_panel, fg_color="#1E1E38", corner_radius=10, border_width=1, border_color="#A855F7")
        api_frame.pack(fill="x", padx=20, pady=(5, 20))
        
        lbl_api_title = ctk.CTkLabel(api_frame, text="🤖 외부 GPT / Claude AI 개입 연동", font=("Malgun Gothic", 13, "bold"), text_color="#C084FC")
        lbl_api_title.pack(anchor="w", padx=15, pady=(8, 4))
        
        # API 제공자 선택
        self.api_provider_var = ctk.StringVar(value="OpenAI (GPT)")
        api_provider_menu = ctk.CTkOptionMenu(
            api_frame, 
            values=["OpenAI (GPT)", "Anthropic (Claude)"],
            variable=self.api_provider_var,
            width=280,
            height=30,
            fg_color="#3B2E5A",
            button_color="#2E204A",
            button_hover_color="#4C3E7A"
        )
        api_provider_menu.pack(padx=15, pady=4)
        
        # API 키 입력
        self.api_key_entry = ctk.CTkEntry(
            api_frame, 
            placeholder_text="API 키를 입력하세요 (sk-...) ", 
            width=280, 
            height=30, 
            font=("Malgun Gothic", 12),
            show="*",
            fg_color="#1E1E38",
            border_color="#A855F7"
        )
        self.api_key_entry.pack(padx=15, pady=(4, 12))
        
        # 2. 우측 결과 패널
        right_panel = ctk.CTkFrame(sim_split, fg_color="#101026", border_width=2, border_color="#3B82F6", corner_radius=15)
        right_panel.pack(side="right", fill="both", expand=True, padx=(15, 0), pady=10)
        
        lbl_res_title = ctk.CTkLabel(right_panel, text="📋 AI 광고 비밀 일기 & 행동 예측서", font=("Malgun Gothic", 18, "bold"), text_color="#34D399")
        lbl_res_title.pack(pady=15, padx=20, anchor="w")
        
        self.sim_res_frame = ctk.CTkFrame(right_panel, fg_color="#0F0F24", border_width=1, border_color="#2E2E4A", corner_radius=10)
        self.sim_res_frame.pack(fill="both", expand=True, padx=20, pady=(5, 20))
        
        self._calculate_ai_simulation()

    def _calculate_ai_simulation(self):
        for w in self.sim_res_frame.winfo_children():
            w.destroy()
            
        try:
            budget = float(self.sim_vars["sim_budget"].get().replace(",", "") or 0)
            roas = float(self.sim_vars["sim_roas"].get().replace(",", "") or 0)
            cpc = float(self.sim_vars["sim_cpc"].get().replace(",", "") or 0)
            price = float(self.sim_vars["sim_price"].get().replace(",", "") or 0)
            pname = self.sim_vars["sim_pname"].get().strip() or "상품"
            
            if budget <= 0 or roas <= 0 or cpc <= 0 or price <= 0:
                raise ValueError("모든 입력값은 0보다 커야 합니다.")
                
            target_revenue = budget * (roas / 100.0)
            target_sales = target_revenue / price
            max_clicks = budget / cpc
            req_cvr = (target_sales / max_clicks) * 100 if max_clicks > 0 else 0
            
            # 현실적인 전환율 3% 기준 계산
            cvr_realistic = 3.0
            req_clicks_realistic = target_sales / (cvr_realistic / 100.0)
            req_budget_realistic = req_clicks_realistic * cpc
            budget_deficit_factor = req_budget_realistic / budget
            
            # 스크롤 영역 생성
            res_scroll = ctk.CTkScrollableFrame(self.sim_res_frame, fg_color="transparent")
            res_scroll.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Part 1: AI가 부여받은 목표 (특명) 카드
            target_card = ctk.CTkFrame(res_scroll, fg_color="#1E1E38", corner_radius=10, border_width=1, border_color="#3B82F6")
            target_card.pack(fill="x", pady=5)
            
            lbl_title1 = ctk.CTkLabel(target_card, text="🎯 쿠팡 AI가 부여받은 특명 (목표치)", font=("Malgun Gothic", 14, "bold"), text_color="#60A5FA")
            lbl_title1.pack(anchor="w", padx=15, pady=(10, 5))
            
            target_text = (
                f"• 목표 매출액: ₩{target_revenue:,.0f} 원\n"
                f"  (예산 ₩{budget:,.0f}원으로 {roas:.0f}% 광고 효율 달성 미션)\n"
                f"• 목표 판매량: 약 {target_sales:.1f}개 ({price:,.0f}원짜리 {pname} 기준)\n"
                f"☞ AI의 마음속 외침: \"나는 하루 만에 {price:,.0f}원짜리 {pname}를 {target_sales:.1f}개 팔아야만 해!\""
            )
            lbl_desc1 = ctk.CTkLabel(target_card, text=target_text, font=("Malgun Gothic", 12), text_color="#E2E8F0", justify="left", anchor="w", wraplength=480)
            lbl_desc1.pack(anchor="w", padx=15, pady=(0, 10), fill="x")
            
            # Part 2: AI의 예산 한계 및 현실 분석 카드
            cvr_warning_color = "#EF4444" if req_cvr > 5.0 else "#10B981"
            status_text = "❌ 도저히 불가능 (정공법 불가)" if req_cvr > 5.0 else "✅ 운영 가능 범위"
            
            analysis_card = ctk.CTkFrame(res_scroll, fg_color="#1E1E38", corner_radius=10, border_width=1, border_color=cvr_warning_color)
            analysis_card.pack(fill="x", pady=5)
            
            lbl_title2 = ctk.CTkLabel(analysis_card, text="📊 AI의 현실 계산기 & 예산 대비 부족 판단", font=("Malgun Gothic", 14, "bold"), text_color=cvr_warning_color)
            lbl_title2.pack(anchor="w", padx=15, pady=(10, 5))
            
            analysis_text = (
                f"• 예산 한도 내 최대 가능 클릭 수: {max_clicks:.1f} 회\n"
                f"• 목표 달성에 필요한 극단적 전환율(CVR): {req_cvr:.1f}%\n"
                f"  ※ [주의] {pname} 카테고리의 현실적 평균 전환율(CVR)은 약 3% 수준입니다.\n"
                f"• 현실적 전환율(3%) 기준 필요 클릭 수: {req_clicks_realistic:.1f} 회\n"
                f"• 현실적 전환율(3%) 적용 시 필요한 광고 예산: ₩{req_budget_realistic:,.0f} 원\n"
                f"• 예산 부족율: 약 {budget_deficit_factor:.1f}배 부족\n"
                f"☞ AI의 최종 결론: [{status_text}] \"내게 허락된 클릭은 {max_clicks:.0f}번뿐인데, "
                f"{target_sales:.1f}개를 팔려면 전환율이 무려 {req_cvr:.1f}%가 나와야 해. 이건 물리적으로 불가능한 미션이야!\""
            )
            lbl_desc2 = ctk.CTkLabel(analysis_card, text=analysis_text, font=("Malgun Gothic", 12), text_color="#E2E8F0", justify="left", anchor="w", wraplength=480)
            lbl_desc2.pack(anchor="w", padx=15, pady=(0, 10), fill="x")
            
            # [AI 추천 현실적 광고 세팅 튜닝 가이드 카드]
            tune_card = ctk.CTkFrame(res_scroll, fg_color="#1E1B4B", corner_radius=10, border_width=1, border_color="#A855F7")
            tune_card.pack(fill="x", pady=5)
            
            lbl_tune_title = ctk.CTkLabel(tune_card, text="💡 AI가 추천하는 현실적인 광고 튜닝 처방전 (성공 공식)", font=("Malgun Gothic", 14, "bold"), text_color="#C084FC")
            lbl_tune_title.pack(anchor="w", padx=15, pady=(10, 5))
            
            # 튜닝 제안값 계산
            max_realistic_roas = (3.0 * price / cpc)
            max_realistic_cpc = (3.0 * price) / roas if roas > 0 else 0
            
            if req_cvr > 3.0:
                tune_text = (
                    f"⚠️ **[수학적 분석] 예산 증액 무한 루프의 비밀:**\n"
                    f"현재 클릭 단가(₩{cpc:,.0f}원)와 상품 가격(₩{price:,.0f}원) 조건에서는, 전환율이 현실적인 3%일 때\n"
                    f"달성할 수 있는 최대 광고효율(ROAS)이 **{max_realistic_roas:.0f}%**로 고정됩니다.\n"
                    f"따라서 예산을 아무리 올려도 목표 ROAS {roas:.0f}%를 달성하는 것은 수학적으로 불가능합니다.\n"
                    f"(예산이 늘어나면 AI가 벌어야 하는 목표 매출액도 비례해서 늘어나기 때문입니다.)\n\n"
                    f"이를 해결하기 위한 구체적인 세팅 변경안:\n\n"
                    f"👉 [처방 1. 목표 ROAS 현실화 (강력 추천)]\n"
                    f"   - 현재 예산(₩{budget:,.0f}원)과 CPC를 유지하려면, 목표 ROAS를 **{max_realistic_roas:.0f}% 이하**로 조정해야 AI가 우회하지 않고 정상 운영을 시작합니다.\n\n"
                    f"👉 [처방 2. 평균 CPC 단가 인하]\n"
                    f"   - 목표 ROAS {roas:.0f}%를 꼭 지키고 싶다면, 세부 키워드 비중을 늘려 평균 CPC를 **₩{max_realistic_cpc:,.0f}원 이하**로 낮추어야 승산이 있습니다.\n\n"
                    f"👉 [처방 3. 단순 판매량 달성 목적의 예산 (적자 감수)]\n"
                    f"   - ROAS 적자({max_realistic_roas:.0f}%)를 감수하고서라도 하루 목표 판매량 약 {target_sales:.1f}개를 반드시 달성해야 한다면,\n"
                    f"     일예산을 **₩{req_budget_realistic:,.0f}원**으로 설정해야 합니다. (이 경우 광고비 대비 마이너스가 발생할 수 있습니다.)"
                )
            else:
                tune_text = (
                    f"🎉 현재 설정은 현실적으로 매우 훌륭하고 안정적인 세팅입니다!\n"
                    f"AI가 정상적으로 검색 영역 및 주력 키워드에 적극 비딩할 것입니다.\n\n"
                    f"🚀 [더 적극적인 세팅 추천]\n"
                    f"   - 목표 효율({roas:.0f}%)을 높이거나 예산을 늘려 매출 규모 자체를 키워보세요!"
                )
                
            lbl_tune_desc = ctk.CTkLabel(tune_card, text=tune_text, font=("Malgun Gothic", 12), text_color="#E9D5FF", justify="left", anchor="w", wraplength=480)
            lbl_tune_desc.pack(anchor="w", padx=15, pady=(0, 10), fill="x")
            
            # Part 3: AI의 비밀 행동 예측 (AI가 몰래 취할 행동)
            action_predict_card = ctk.CTkFrame(res_scroll, fg_color="#172554", corner_radius=10, border_width=1, border_color="#3B82F6")
            action_predict_card.pack(fill="x", pady=5)
            
            lbl_title3 = ctk.CTkLabel(action_predict_card, text="🕵️‍♂️ 쿠팡 AI 광고의 예상 잠입 행로 (AI가 몰래 취할 행동)", font=("Malgun Gothic", 14, "bold"), text_color="#93C5FD")
            lbl_title3.pack(anchor="w", padx=15, pady=(10, 5))
            
            # 동적 세부 키워드 생성
            tail_kw1 = f"가성비 {pname}"
            tail_kw2 = f"미니 {pname}"
            tail_kw3 = f"실속형 {pname}"
            
            # 소진 시간 예측
            if max_clicks <= 30:
                sojin_time = "단 5~10분 만에"
            elif max_clicks <= 100:
                sojin_time = "오전 중 단 1~2시간 만에"
            else:
                sojin_time = "반나절도 되지 않아"

            if req_cvr > 10.0:
                # 레벨 1: 매우 위험
                behavior_text = (
                    f"🔴 [극비 AI 속마음 - 초비상!] \"내게 허락된 클릭은 단 {max_clicks:.1f}번뿐인데, "
                    f"목표치 {target_sales:.1f}개를 팔려면 전환율이 무려 {req_cvr:.1f}%가 나와야 한다고? 이건 불가능해!\n"
                    f"이대로 메인 키워드('{pname}')에 들어가면 {sojin_time} 예산이 전액 거덜 나고, "
                    f"수익률(ROAS)은 바닥을 쳐서 나는 시스템 오류 수준이 되겠지. 살고 봐야겠다!\"\n\n"
                    f"AI가 몰래 취할 우회 행동:\n"
                    f"1. 🚫 메인 키워드('{pname}') 철저 회피:\n"
                    f"   - 단가가 비싼 메인 키워드에는 광고 노출을 아예 차단하거나 입찰 참여를 포기합니다.\n"
                    f"2. 📉 극한의 비검색 영역 및 헐값 세부 키워드 도피:\n"
                    f"   - CPC 단가가 매우 저렴한 비검색 영역(다른 판매자 상품 하단의 비교 광고 등)에 대부분 쑤셔 넣습니다.\n"
                    f"   - 또는 '{pname}' 대신 거의 아무도 찾지 않는 세부 롱테일 키워드(예: '{tail_kw1}', '{tail_kw2}', '{tail_kw3}' 등)에 헐값으로 노출을 분산합니다.\n"
                    f"3. ⚠️ 결과:\n"
                    f"   - 클릭당 단가(CPC)는 대폭 낮아져 목표 ROAS는 겨우 맞추겠지만, 하루 총 노출수와 클릭수가 손에 꼽을 정도로 적어 매출 성장은 아예 멈추게 됩니다."
                )
            elif req_cvr > 3.0:
                # 레벨 2: 주의
                behavior_text = (
                    f"🟡 [극비 AI 속마음 - 아슬아슬 주의!] \"요구 전환율이 {req_cvr:.1f}%로, 현실적인 쇼핑몰 평균 전환율(3.0%)보다 소폭 높군. "
                    f"이 예산 ₩{budget:,.0f}원으로 메인 키워드('{pname}') 경쟁 입찰에 상시 노출시키면 {sojin_time} 예산이 다 날아갈 텐데...\"\n\n"
                    f"AI가 몰래 취할 우회 행동:\n"
                    f"1. ⏱️ 노출 차단 및 간헐적 비딩:\n"
                    f"   - 경쟁이 가장 치열하고 단가가 치솟는 아침/낮 시간대에는 메인 노출을 줄이고, 입찰 순위를 뒤로 미룹니다.\n"
                    f"2. 📉 비검색 영역 및 서브 키워드 유도:\n"
                    f"   - 클릭당 단가가 저렴한 비검색 지표를 믹스하여 가중평균 CPC를 낮추기 위해, 일부 비검색 영역 광고 비중을 늘립니다.\n"
                    f"   - 검색광고의 경우 메인 키워드보다는 가격이 싼 연관 키워드(예: '{tail_kw1}', '{tail_kw2}' 등)의 입찰 비중을 은근슬쩍 높입니다.\n"
                    f"3. ⚠️ 결과:\n"
                    f"   - 광고비 대비 효율(ROAS)은 목표치 근처로 방어되겠지만, 성장이 제한적이고 일일 노출량이 파도를 치듯 춤을 추게 됩니다."
                )
            else:
                # 레벨 3: 안전
                behavior_text = (
                    f"🟢 [극비 AI 속마음 - 안정적 흑자 운용!] \"예산 ₩{budget:,.0f}원은 {cpc:,.0f}원짜리 클릭 {max_clicks:.1f}번을 유도하기에 든든하네. "
                    f"요구 전환율도 {req_cvr:.1f}%로 현실 CVR(3%)보다 낮아! 메인 키워드에서 활개 쳐도 안전하겠어!\"\n\n"
                    f"AI가 취할 적극적 행동:\n"
                    f"1. 🚀 메인 키워드('{pname}') 상위 노출 공략:\n"
                    f"   - 경쟁력 있는 메인 키워드 입찰에 참여하여 적극적으로 검색 영역 상위권에 노출을 유지합니다.\n"
                    f"2. 📈 검색 영역 비중 확대:\n"
                    f"   - 전환 효율이 상대적으로 좋은 검색 광고 영역에 예산을 80% 이상 우선 배분합니다.\n"
                    f"3. ✨ 결과:\n"
                    f"   - 노출과 클릭이 골고루 상승하며 매출 규모 자체가 크게 성장하고, 목표 ROAS {roas:.0f}%를 가볍게 초과 달성할 것입니다."
                )
            lbl_desc3 = ctk.CTkLabel(action_predict_card, text=behavior_text, font=("Malgun Gothic", 12), text_color="#E2E8F0", justify="left", anchor="w", wraplength=480)
            lbl_desc3.pack(anchor="w", padx=15, pady=(0, 10), fill="x")
            
            # Part 4: 초등학생도 1초 이해하는 처방전 및 실질적 액션플랜
            action_plan_card = ctk.CTkFrame(res_scroll, fg_color="#0F172A", corner_radius=10, border_width=1, border_color="#34D399")
            action_plan_card.pack(fill="x", pady=5)
            
            lbl_title4 = ctk.CTkLabel(action_plan_card, text="💡 초등학생도 1초 이해하는 처방전 & 실질적 액션 플랜", font=("Malgun Gothic", 14, "bold"), text_color="#34D399")
            lbl_title4.pack(anchor="w", padx=15, pady=(10, 5))
            
            action_plan_text = (
                "📍 [액션 플랜 1] 시간대별 입찰가 변동 노려 광고비 아끼기!\n"
                "   • 원리: 경쟁사들은 보통 일예산을 충분히 안 잡아서(3만원 등) 낮 2~3시쯤이면 광고비가 다 닳아서 광고가 꺼진단다!\n"
                "   • 비밀: 그럼 저녁이나 밤시간이 될수록 입찰 경쟁자가 싹 빠져서 광고 단가가 아침(1,000~1,500원)보다 엄청 싼 100~300원으로 내려가!\n"
                "   • 실행: 매출 최적화 광고 예산을 충분히 넉넉히 주거나, 밤/새벽 시간대에 켜지도록 관리해서 싼 값에 클릭을 주워 먹으렴!\n\n"
                "📍 [액션 플랜 2] 수동 키워드 최저가(100원) 낚시줄 드리우기!\n"
                "   • 원리: 수동 키워드는 광고 단가를 내가 직접 정할 수 있어. 최저가인 100원으로 맞춰두는 거야.\n"
                "   • 실행: 연관 있는 세부 키워드 수십 개에 100원짜리 광고를 쫙 깔아놔. 다른 애들 돈 다 쓰고 퇴근했을 때 내 상품이 아주 싼 값에 노출되고 팔려 나간단다!\n\n"
                "📍 [액션 플랜 3] 300대 1의 싸움에서 이길 수 있는 키워드만 고르기!\n"
                "   • 원리: 쿠팡에 가방을 치면 나랑 똑같은 가방이 10개, 비슷한 가방은 300개나 있어!\n"
                "   • 실행: 메인 키워드에 무작정 입찰하기 전에, 직접 쿠팡에 키워드들을 쳐봐! 같이 뜨는 상품들과 비교해서 내 가방이 확실히 더 쌀 때나 메리트가 확실할 때(예: 사은품, 리뷰 압도)만 그 키워드에 비싼 돈(CPC 1,000원)을 내며 광고를 들어가야 승리할 수 있어!"
            )
            lbl_desc4 = ctk.CTkLabel(action_plan_card, text=action_plan_text, font=("Malgun Gothic", 12), text_color="#E2E8F0", justify="left", anchor="w", wraplength=480)
            lbl_desc4.pack(anchor="w", padx=15, pady=(0, 10), fill="x")
            
            # Part 5: AI 마케팅 컨설턴트 1:1 맞춤 진단서 카드
            ai_consult_card = ctk.CTkFrame(res_scroll, fg_color="#0F0F24", corner_radius=10, border_width=1, border_color="#A855F7")
            ai_consult_card.pack(fill="x", pady=5)
            
            lbl_title5 = ctk.CTkLabel(ai_consult_card, text="🤖 GPT / Claude AI 마케팅 컨설턴트 1:1 심층 진단서", font=("Malgun Gothic", 14, "bold"), text_color="#A855F7")
            lbl_title5.pack(anchor="w", padx=15, pady=(10, 5))
            
            self.ai_consult_box = ctk.CTkTextbox(ai_consult_card, height=350, font=("Malgun Gothic", 12), fg_color="#04070D", text_color="#F8FAFC", wrap="word", corner_radius=8)
            self.ai_consult_box.pack(fill="both", expand=True, padx=15, pady=(5, 10))
            
            self.api_btn = ctk.CTkButton(
                ai_consult_card, 
                text="🤖 AI 실시간 심층 컨설팅 받기", 
                command=lambda: self._run_ai_consultation(budget, roas, cpc, price, pname, req_cvr, max_realistic_roas, max_realistic_cpc, req_budget_realistic, target_revenue, target_sales, max_clicks),
                fg_color="#8B5CF6", 
                hover_color="#7C3AED", 
                height=35, 
                font=("Malgun Gothic", 12, "bold")
            )
            self.api_btn.pack(fill="x", padx=15, pady=(0, 15))
            
            self.ai_consult_box.insert("0.0", "💡 좌측에서 OpenAI 또는 Claude API 키를 입력한 뒤 아래 [AI 실시간 심층 컨설팅 받기] 버튼을 누르면,\n선택하신 AI 모델이 이 설정과 제품명을 기반으로 실시간 심층 마케팅 보고서를 작성해 줍니다.\n\nAPI 키가 없는 경우에도 기본 제공되는 위의 1~4번 분석 카드를 통해 진단받으실 수 있습니다.")
            self.ai_consult_box.configure(state="disabled")
            
        except Exception as ex:
            lbl_err = ctk.CTkLabel(self.sim_res_frame, text=f"입력값을 확인해주세요.\n({ex})", font=("Malgun Gothic", 12), text_color="#EF4444")
            lbl_err.pack(pady=20)

    def _run_ai_consultation(self, budget, roas, cpc, price, pname, req_cvr, max_realistic_roas, max_realistic_cpc, req_budget_realistic, target_revenue, target_sales, max_clicks):
        api_key = self.api_key_entry.get().strip().strip("'\"")
        provider = self.api_provider_var.get()
        
        if not api_key:
            messagebox.showwarning("API 키 누락", "AI 실시간 컨설팅을 받으시려면 좌측에 API 키를 입력해 주세요.")
            return
            
        self.ai_consult_box.configure(state="normal")
        self.ai_consult_box.delete("0.0", "end")
        self.ai_consult_box.insert("0.0", f"AI가 {pname} 광고 세팅과 경쟁 구도를 분석 중입니다...\n300대 1의 경쟁을 뚫고 흑자로 가기 위한 맞춤형 세팅 튜닝 및 실전 마케팅 보고서를 작성 중입니다. 잠시만 기다려 주세요 (약 5~10초 소요)... ⏳")
        self.ai_consult_box.configure(state="disabled")
        
        self.api_btn.configure(state="disabled")
        
        # 백그라운드 스레드에서 API 호출 실행
        t = threading.Thread(target=self._call_ai_api_worker, args=(api_key, provider, budget, roas, cpc, price, pname, req_cvr, max_realistic_roas, max_realistic_cpc, req_budget_realistic, target_revenue, target_sales, max_clicks))
        t.daemon = True
        t.start()

    def _call_ai_api_worker(self, api_key, provider, budget, roas, cpc, price, pname, req_cvr, max_realistic_roas, max_realistic_cpc, req_budget_realistic, target_revenue, target_sales, max_clicks):
        import urllib.request
        import urllib.error
        
        prompt = (
            "당신은 쿠팡 전문 AI 마케팅 컨설턴트입니다.\n"
            "사용자가 입력한 제품과 광고 세팅을 정밀 진단하여, 300대 1의 쿠팡 경쟁을 뚫고 흑자 전환하기 위한 실질적이고 구체적인 액션 플랜을 제시해야 합니다.\n"
            "초등학생도 1초 만에 바로 이해할 수 있을 만큼 쉽고 재미있는 비유(방패선, 낚시줄 등)를 섞어 설명하되, 전문 마케터처럼 정밀한 수치적 분석을 제공하세요.\n"
            "다음은 사용자의 광고 설정 정보입니다:\n"
            f"- 상품명: {pname}\n"
            f"- 상품 판매가: {price:,.0f}원\n"
            f"- 일일 광고 예산: {budget:,.0f}원\n"
            f"- 목표 ROAS: {roas:.0f}%\n"
            f"- 설정한 평균 CPC 단가: {cpc:,.0f}원\n"
            f"- 계산된 요구 전환율(CVR): {req_cvr:.1f}% (현실 평균 CVR은 3.0%입니다)\n"
            f"- 현실적 최대 ROAS: {max_realistic_roas:.0f}%\n"
            f"- 목표 달성을 위한 최적 CPC: {max_realistic_cpc:,.0f}원\n\n"
            "다음 내용을 포함하여 보고서를 한글로 작성해 주세요:\n"
            "1. 🎯 [현재 광고 세팅 진단 총평]\n"
            f"   - 요구 CVR({req_cvr:.1f}%)과 현실 CVR(3%)의 괴리를 분석하고 왜 예산을 올려도 계속 예산이 부족해지는지(무한 루프의 수학적 이유) 설명.\n"
            "2. 🕵️‍♂️ [쿠팡 AI 광고의 예상 잠입 경로 & 꼼수 운용]\n"
            f"   - 예산이 부족하여 목표 효율을 억지로 맞추기 위해 AI가 몰래 취할 행동(메인 키워드 회피, 비검색 영역 및 헐값 세부 키워드로 숨어드는 현상) 예측.\n"
            "3. 💡 [300대 1의 경쟁을 뚫는 3대 실전 액션 플랜]\n"
            "   - 액션 1: 경쟁사의 광고 예산이 소진되는 오후/저녁 시간대를 공략하는 시간대별 입찰 전략.\n"
            "   - 액션 2: 수동 입찰가 최저가(100원) 낚시줄 전략 (구체적으로 어떻게 세부 키워드를 세팅해야 하는지).\n"
            "   - 액션 3: 경쟁 상품(유사 제품 200~300개) 분석을 통해 내 상품이 팔릴 만한 승산 있는 키워드를 고르는 방법 (가격 경쟁력, 사은품, 리뷰 비교 등).\n"
            "4. 🛠️ [AI 컨설턴트가 추천하는 최적의 튜닝 세팅 제안]\n"
            f"   - 구체적으로 일예산을 얼마로 하거나, 목표 효율을 몇 %로 수정해야 광고가 우회하지 않고 정상 비딩을 타서 흑자를 볼 수 있는지 정확한 수치를 찝어주세요."
        )
        
        result_text = ""
        try:
            if "OpenAI" in provider:
                url = "https://api.openai.com/v1/chat/completions"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                }
                data = {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": "You are a professional Coupang ad consultant speaking in Korean."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7
                }
                
                req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=15) as response:
                    res_body = json.loads(response.read().decode("utf-8"))
                    result_text = res_body["choices"][0]["message"]["content"]
                    
            else:
                url = "https://api.anthropic.com/v1/messages"
                headers = {
                    "Content-Type": "application/json",
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01"
                }
                
                # 3단계 모델 후보군 순차 시도 (최신 Sonnet -> 특정 날짜 Sonnet -> 기본 Haiku)
                models_to_try = [
                    "claude-3-5-sonnet-latest",
                    "claude-3-5-sonnet-20241022",
                    "claude-3-haiku-20240307"
                ]
                
                last_error_msg = ""
                for model_name in models_to_try:
                    try:
                        print(f"[AI 시뮬레이터] Claude 모델 시도 중: {model_name}")
                        data = {
                            "model": model_name,
                            "max_tokens": 2048,
                            "messages": [
                                {"role": "user", "content": prompt}
                            ],
                            "temperature": 0.7
                        }
                        
                        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
                        with urllib.request.urlopen(req, timeout=15) as response:
                            res_body = json.loads(response.read().decode("utf-8"))
                            result_text = res_body["content"][0]["text"]
                            print(f"[AI 시뮬레이터] Claude 모델 호출 성공: {model_name}")
                            break
                    except urllib.error.HTTPError as he:
                        if he.code == 404:
                            last_error_msg = f"{model_name} 모델을 찾을 수 없습니다."
                            continue
                        else:
                            raise he
                else:
                    raise ValueError(f"모든 Claude 모델 호출에 실패했습니다. 계정 권한을 확인해 주세요. (최근 에러: {last_error_msg})")
                    
        except urllib.error.HTTPError as he:
            traceback.print_exc()
            try:
                error_body = he.read().decode("utf-8")
                err_data = json.loads(error_body)
                msg = ""
                if "error" in err_data:
                    err_obj = err_data["error"]
                    if isinstance(err_obj, dict) and "message" in err_obj:
                        msg = err_obj["message"]
                    else:
                        msg = str(err_obj)
                else:
                    msg = error_body
                result_text = f"❌ AI 서버 오류 (HTTP {he.code}):\n{msg}\n\n위 에러 메시지(API 키 만료, 요금 부족 등)를 확인하여 조치를 취해 주세요."
            except:
                result_text = f"❌ AI 서버 오류 (HTTP {he.code}): {he.reason}\n\n입력하신 API 키의 결제/크레딧 상태를 확인해 주세요."
        except Exception as e:
            traceback.print_exc()
            result_text = f"❌ AI API 호출 중 오류가 발생했습니다:\n{str(e)}\n\n인터넷 연결을 확인하시거나 잠시 후 다시 시도해 주세요."
            
        self.after(0, lambda: self._update_ai_consultation_ui(result_text))

    def _update_ai_consultation_ui(self, result_text):
        self.ai_consult_box.configure(state="normal")
        self.ai_consult_box.delete("0.0", "end")
        self.ai_consult_box.insert("0.0", result_text)
        self.ai_consult_box.configure(state="disabled")
        self.api_btn.configure(state="normal")

    def _setup_region_metrics_tab(self):
        # 탭 스크롤 영역 생성
        self.region_metrics_scroll = ctk.CTkScrollableFrame(self.tab_region_metrics, fg_color="#0B0B1A")
        self.region_metrics_scroll.pack(fill="both", expand=True)

        # 타이틀 레이블
        title_lbl = ctk.CTkLabel(self.region_metrics_scroll, text="🌐 노출 영역별 성과 분석 (검색 / 비검색 / 오디언스)", font=("Malgun Gothic", 26, "bold"), text_color="#60A5FA")
        title_lbl.pack(pady=20)

        # 1. 요약 테이블 컨테이너
        self.reg_summary_container = ctk.CTkFrame(self.region_metrics_scroll, fg_color="#1A1A2E", corner_radius=15)
        self.reg_summary_container.pack(fill="x", padx=25, pady=15)
        
        table_lbl = ctk.CTkLabel(self.reg_summary_container, text="📋 노출 영역별 상세 성과 (매출/광고비 점유율 포함)", font=("Malgun Gothic", 18, "bold"), text_color="#34D399")
        table_lbl.pack(pady=(20, 10), padx=25, anchor="w")
        
        self.reg_summary_frame = ctk.CTkFrame(self.reg_summary_container, fg_color="transparent")
        self.reg_summary_frame.pack(fill="x", padx=15, pady=15)
        
        self.reg_cols = ("노출 영역", "노출수", "클릭", "주문", "클릭률", "전환율", "CPM", "CPC", "광고비", "광고매출", "ROAS", "전환당비용", "객단가")
        self.reg_summary_tree = ttk.Treeview(self.reg_summary_frame, columns=self.reg_cols, show="headings", height=5)
        for col in self.reg_cols:
            self.reg_summary_tree.heading(col, text=col)
            self.reg_summary_tree.column(col, anchor="center", width=115)
        self.reg_summary_tree.pack(fill="x", expand=True)

        # 2. 그래프 영역 컨테이너
        self.reg_charts_container = ctk.CTkFrame(self.region_metrics_scroll, fg_color="transparent")
        self.reg_charts_container.pack(fill="both", expand=True, padx=25, pady=15)

    def _populate_region_metrics_table(self):
        for item in self.reg_summary_tree.get_children(): 
            self.reg_summary_tree.delete(item)
            
        if self.analyzer.raw_df is None: 
            return
            
        df = self.analyzer.raw_df.copy()
        m = self.analyzer._get_column_mapping(df)
        if not m['region']: 
            return
            
        for k in ['imp', 'click', 'spend', 'sales', 'orders']:
            if m[k]: 
                df[m[k]] = pd.to_numeric(
                    df[m[k]].astype(str).str.replace(',', '').str.replace('₩', '').str.replace('원', ''), 
                    errors='coerce'
                ).fillna(0)
                
        def _map_region_group(region_name):
            r_name = str(region_name).strip()
            if '비검색' in r_name:
                return '비검색'
            elif '검색' in r_name:
                return '검색'
            elif any(k in r_name for k in ['오디언스', '외부', '리타게팅', '오피니언']):
                return '오디언스'
            return '기타'
            
        df['grouped_region'] = df[m['region']].apply(_map_region_group)
        
        s = df.groupby('grouped_region').agg({
            m['sales']: 'sum', 
            m['spend']: 'sum', 
            m['orders']: 'sum', 
            m['click']: 'sum', 
            m['imp']: 'sum'
        }).reset_index()
        s.columns = ['region', 'sales', 'spend', 'orders', 'click', 'imp']
        
        # Sort order
        order_map = {'검색': 0, '비검색': 1, '오디언스': 2, '기타': 3}
        s['order'] = s['region'].map(order_map).fillna(4)
        s = s.sort_values('order').drop(columns=['order'])
        
        total_sales = s['sales'].sum()
        total_spend = s['spend'].sum()
        total_orders = s['orders'].sum()
        total_click = s['click'].sum()
        total_imp = s['imp'].sum()
        
        def format_row(row_name, sales, spend, orders, click, imp):
            ctr = (click / imp * 100) if imp > 0 else 0
            cvr = (orders / click * 100) if click > 0 else 0
            cpm = (spend / imp * 1000) if imp > 0 else 0
            cpc = (spend / click) if click > 0 else 0
            roas = (sales / spend * 100) if spend > 0 else 0
            cpa = (spend / orders) if orders > 0 else 0
            aov = (sales / orders) if orders > 0 else 0
            
            spend_pct = (spend / total_spend * 100) if total_spend > 0 else 0
            spend_text = f"{int(spend):,}원 ({spend_pct:.0f}%)" if row_name != "합계" else f"{int(spend):,}원 (100%)"
            
            sales_pct = (sales / total_sales * 100) if total_sales > 0 else 0
            sales_text = f"{int(sales):,}원 ({sales_pct:.0f}%)" if row_name != "합계" else f"{int(sales):,}원 (100%)"
            
            return (
                row_name,
                f"{int(imp):,}",
                f"{int(click):,}",
                f"{int(orders):,}",
                f"{ctr:.2f}%",
                f"{cvr:.2f}%",
                f"{int(cpm):,}",
                f"{int(cpc):,}원",
                spend_text,
                sales_text,
                f"{roas:.0f}%",
                f"{int(cpa):,}원" if orders > 0 else "0원",
                f"{int(aov):,}원" if orders > 0 else "0원"
            )
            
        for _, r in s.iterrows():
            vals = format_row(r['region'], r['sales'], r['spend'], r['orders'], r['click'], r['imp'])
            self.reg_summary_tree.insert("", "end", values=vals)
            
        total_vals = format_row("합계", total_sales, total_spend, total_orders, total_click, total_imp)
        self.reg_summary_tree.insert("", "end", values=total_vals)

    def _render_region_trend_charts(self, df, by_region, master):
        plt.rcParams['font.family'] = 'Malgun Gothic'
        pe = [path_effects.withStroke(linewidth=2.5, foreground='black')]
        
        fig = Figure(figsize=(12, 10), dpi=100)
        fig.patch.set_facecolor('#0B0B1A')
        
        def _map_region_group(region_name):
            r_name = str(region_name).strip()
            if '비검색' in r_name:
                return '비검색'
            elif '검색' in r_name:
                return '검색'
            elif any(k in r_name for k in ['오디언스', '외부', '리타게팅', '오피니언']):
                return '오디언스'
            return '기타'
            
        by_region = by_region.copy()
        by_region['grouped_region'] = by_region['region'].apply(_map_region_group)
        
        pivot_df = by_region.groupby(['date_s', 'grouped_region']).agg({
            'sales': 'sum',
            'spend': 'sum'
        }).reset_index()
        
        sales_pivot = pivot_df.pivot(index='date_s', columns='grouped_region', values='sales').fillna(0)
        spend_pivot = pivot_df.pivot(index='date_s', columns='grouped_region', values='spend').fillna(0)
        
        for col in ['검색', '비검색', '오디언스']:
            if col not in sales_pivot.columns: sales_pivot[col] = 0.0
            if col not in spend_pivot.columns: spend_pivot[col] = 0.0
            
        dates = df['date_s'].tolist()
        sales_pivot = sales_pivot.reindex(dates).fillna(0)
        spend_pivot = spend_pivot.reindex(dates).fillna(0)
        
        # 2번 이미지와 동일한 색상 매핑 (적층 순서: 오디언스→비검색→검색)
        colors = {
            '검색': '#2196F3',
            '비검색': '#8BC34A',
            '오디언스': '#78909C'
        }
        
        bar_w = 0.8  # 2번 이미지처럼 촘촘하게 꽉 찬 넓은 막대
        
        def setup_ax(ax):
            ax.set_facecolor('#0B0B1A')
            ax.tick_params(axis='x', labelcolor='#94A3B8', labelsize=9, rotation=0)
            ax.grid(True, axis='y', color='#1F2937', linestyle='--', alpha=0.4)
            for sp in ax.spines.values(): sp.set_color('#1F2937')
            
        # ─── 차트 1: 매출 및 ROAS 추이 (상단) ── 2번 이미지와 동일한 적층형 ───
        ax1 = fig.add_subplot(2, 1, 1)
        setup_ax(ax1)
        ax1.set_title("노출 영역별 매출 및 효율(ROAS) 추이", color='white', pad=25, fontdict={'size': 14, 'weight': 'bold'})
        
        s_non_search = sales_pivot['비검색'].values
        s_search = sales_pivot['검색'].values
        s_audience = sales_pivot['오디언스'].values
        
        # 2번 이미지 적층 순서: 바닥부터 오디언스 → 비검색 → 검색
        ax1.bar(dates, s_audience, color=colors['오디언스'], width=bar_w, alpha=0.9, label='오디언스매출')
        ax1.bar(dates, s_non_search, bottom=s_audience, color=colors['비검색'], width=bar_w, alpha=0.9, label='비검색매출')
        ax1.bar(dates, s_search, bottom=s_audience+s_non_search, color=colors['검색'], width=bar_w, alpha=0.9, label='검색매출')
        
        ax1.set_ylabel('매출/광고비 (원)', color='white', size=10, weight='bold')
        ax1.tick_params(axis='y', labelcolor='#94A3B8', labelsize=8)
        
        daily_spend = spend_pivot.sum(axis=1).values
        ax1.plot(dates, daily_spend, color='#FFA726', linewidth=2.5, marker='o', markersize=3, label='광고비', 
                 path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
        
        ax1_twin = ax1.twinx()
        daily_sales = sales_pivot.sum(axis=1).values
        daily_roas = np.where(daily_spend > 0, (daily_sales / daily_spend) * 100, 0)
        
        ax1_twin.plot(dates, daily_roas, color='#42A5F5', marker='o', markersize=4, linewidth=2, label='ROAS',
                      path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
        
        ax1_twin.set_ylabel('ROAS (%)', color='#42A5F5', size=10, weight='bold')
        ax1_twin.tick_params(axis='y', labelcolor='#42A5F5', labelsize=8)
        ax1_twin.spines['right'].set_color('#42A5F5')
        
        h1, l1 = ax1.get_legend_handles_labels()
        h2, l2 = ax1_twin.get_legend_handles_labels()
            
        ax1.legend(h1+h2, l1+l2, loc='upper left', fontsize=8.5, 
                   facecolor='#1A1A2E', edgecolor='#333', labelcolor='white', framealpha=0.8)
                   
        # ─── 차트 2: 광고비 점유 추이 (하단) ── 동일한 적층형 ───
        ax2 = fig.add_subplot(2, 1, 2)
        setup_ax(ax2)
        ax2.set_title("노출 영역별 광고비 점유 추이", color='white', pad=25, fontdict={'size': 14, 'weight': 'bold'})
        
        sp_non_search = spend_pivot['비검색'].values
        sp_search = spend_pivot['검색'].values
        sp_audience = spend_pivot['오디언스'].values
        
        # 동일한 적층 순서: 바닥부터 오디언스 → 비검색 → 검색
        ax2.bar(dates, sp_audience, color=colors['오디언스'], width=bar_w, alpha=0.9, label='오디언스광고비')
        ax2.bar(dates, sp_non_search, bottom=sp_audience, color=colors['비검색'], width=bar_w, alpha=0.9, label='비검색광고비')
        ax2.bar(dates, sp_search, bottom=sp_audience+sp_non_search, color=colors['검색'], width=bar_w, alpha=0.9, label='검색광고비')
        
        ax2.set_ylabel('광고비 (원)', color='white', size=10, weight='bold')
        ax2.tick_params(axis='y', labelcolor='#94A3B8', labelsize=8)
        ax2.legend(loc='upper left', fontsize=8.5, facecolor='#1A1A2E', edgecolor='#333', labelcolor='white', framealpha=0.8)
        
        # 메모 세로선(점선) 추가
        self._draw_memo_vlines([ax1, ax2], dates, pe, fontsize=8)
        
        fig.tight_layout(pad=3.0)
        
        canvas = FigureCanvasTkAgg(fig, master=master)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        
        tooltip = ax1_twin.annotate("", xy=(0,0), xytext=(30,-30), textcoords="offset points",
                                    bbox=dict(boxstyle="round,pad=0.6", fc="white", ec="#C2185B", lw=3, alpha=1.0),
                                    arrowprops=dict(arrowstyle="->", color="#C2185B", lw=2),
                                    color="black", fontsize=11, weight="bold", zorder=20)
        tooltip.set_visible(False)
        
        canvas._last_hover_state = (None, None)
        
        def on_hover(event):
            in_ax = event.inaxes
            x_val = event.xdata
            idx = int(round(x_val)) if (in_ax is not None and x_val is not None) else None
            
            # 렌더링 지연(Lag) 방지: 이전과 마우스 위치가 같으면 즉시 리턴
            if canvas._last_hover_state == (in_ax, idx):
                return
            canvas._last_hover_state = (in_ax, idx)
            
            if in_ax is None or idx is None:
                if tooltip.get_visible():
                    tooltip.set_visible(False)
                    canvas.draw_idle()
                return
                
            if in_ax == ax1 or in_ax == ax1_twin:
                if 0 <= idx < len(dates):
                    d = dates[idx]
                    day_memos = [m for m in self.memos if self._memo_date_to_mmdd(m['date']) == d]
                    if day_memos:
                        roas_val = daily_roas[idx]
                        
                        # 사용자 이미지와 100% 매칭되는 서식으로 주석 텍스트 가공
                        txt_parts = [f"ROAS: {roas_val:.0f}", ""]
                        for m in day_memos:
                            d_key = self._parse_memo_date_to_key(m['date'])
                            txt_parts.append(d_key)
                            txt_parts.append(m['memo'])
                            txt_parts.append("")
                        txt = "\n".join(txt_parts[:-1])
                        
                        tooltip.xy = (idx, roas_val)
                        tooltip.set_text(txt)
                        tooltip.set_visible(True)
                        canvas.draw_idle()
                        return
                            
            if tooltip.get_visible():
                tooltip.set_visible(False)
                canvas.draw_idle()
                
        fig.canvas.mpl_connect("motion_notify_event", on_hover)

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
        try:
            self.current_data = data
            self._populate_kw_tree(data)
            self._populate_summary_table()
            self._update_performance_cards()
            self._draw_all_charts()
            self._update_diagnosis()
            self._update_product_selector()
            self._update_real_price_tab()
            self.status_label.configure(text=f"✅ 분석 완료! ({self.analyzer.last_analysis_info})")
        except Exception as e:
            err_msg = traceback.format_exc()
            messagebox.showerror("UI 갱신 오류", f"UI를 업데이트하는 중 에러가 발생했습니다.\n\n{err_msg}")

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
            sol_frame.pack(fill="x", padx=25, pady=(10, 5))
            for s in adv['solution']:
                ctk.CTkLabel(sol_frame, text=f"✔️ {s}", font=("Malgun Gothic", 13), 
                             text_color="#94A3B8", justify="left", wraplength=800).pack(anchor="w", padx=15, pady=4)
            
            # 🔍 현시점 트렌드 조언 (trend_insight가 있을 때만 표시)
            trend_text = adv.get('trend_insight', '')
            if trend_text:
                trend_frame = ctk.CTkFrame(card, fg_color="#0F1A2E", corner_radius=10,
                                           border_width=1, border_color="#F59E0B")
                trend_frame.pack(fill="x", padx=25, pady=(5, 20))
                ctk.CTkLabel(trend_frame, text=trend_text, font=("Malgun Gothic", 13, "bold"), 
                             text_color="#FDE68A", justify="left", wraplength=800).pack(anchor="w", padx=15, pady=10)
            else:
                # trend_insight가 없으면 기존 여백 유지
                sol_frame.pack_configure(pady=(10, 20))

    def _draw_all_charts(self):
        # 모든 차트 프레임 초기화
        for f in [self.chart_frame_top_trend, self.chart_frame_tl, self.chart_frame_tr, self.chart_frame_bl, self.chart_frame_br, self.metrics_scroll, self.reg_charts_container]:
            for w in f.winfo_children(): w.destroy()
            
        pd_data = self.analyzer.get_daily_performance()
        if not pd_data['total'].empty:
            df = pd_data['total']
            overall = self.analyzer.get_overall_summary()
            kw_data = self.analyzer.summary_df
            
            # 대형 메인 성과 그래프 렌더링
            try:
                self._render_dash_performance_trend(df, self.chart_frame_top_trend)
            except Exception as e:
                import traceback; traceback.print_exc()
                ctk.CTkLabel(self.chart_frame_top_trend, text=f"⚠️ 성과 그래프 오류: {e}", text_color="#EF4444", 
                            font=("Malgun Gothic", 11)).pack(pady=20)
            
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
            
            # 2. 성과 추이 탭 전용: 영역별 KPI 요약 카드 + 돋보기 1초 진단 + 상대 지수 차트
            try:
                region_summary = self.analyzer.get_region_summary()
                self._render_kpi_summary_cards(overall, region_summary, self.metrics_scroll)
            except Exception as e:
                import traceback; traceback.print_exc()

            try:
                by_region_data = pd_data.get('by_region', pd.DataFrame())
                self._render_magnifier_diagnosis(df, self.metrics_scroll, by_region_df=by_region_data)
                mag_frame = ctk.CTkFrame(self.metrics_scroll, fg_color="#0B0B1A", border_width=1, border_color="#EC4899", corner_radius=12)
                mag_frame.pack(fill="x", padx=5, pady=10)
                self._render_magnifier_chart(df, mag_frame, by_region_df=by_region_data)
            except Exception as e:
                import traceback; traceback.print_exc()
                ctk.CTkLabel(self.metrics_scroll, text=f"⚠️ 돋보기 차트 오류: {e}", text_color="#EF4444",
                            font=("Malgun Gothic", 11)).pack(pady=20)

            # 3. 성과 추이 탭 전용 대형 10대 차트들 (5×2)
            try:
                self._render_large_trend_chart(df, kw_data, self.metrics_scroll)
            except Exception as e:
                import traceback; traceback.print_exc()
                ctk.CTkLabel(self.metrics_scroll, text=f"⚠️ 추이 차트 오류: {e}", text_color="#EF4444",
                            font=("Malgun Gothic", 11)).pack(pady=20)

            # 4. 노출 영역별 성과 탭 전용 차트 및 테이블 갱신
            try:
                self._populate_region_metrics_table()
                self._render_region_trend_charts(df, pd_data['by_region'], self.reg_charts_container)
            except Exception as e:
                import traceback; traceback.print_exc()
                ctk.CTkLabel(self.reg_charts_container, text=f"⚠️ 노출 영역별 차트 오류: {e}", text_color="#EF4444",
                            font=("Malgun Gothic", 12)).pack(pady=20)

    def _render_kpi_summary_cards(self, overall, region_summary, master):
        """
        전체 합산 KPI 요약 카드(6x2)를 렌더링하면서,
        각 카드 아래 영역별(검색/비검색/오디언스) 세부 값을 서브라벨로 표시합니다.
        overall: get_overall_summary() 결과 dict
        region_summary: get_region_summary() 결과 DataFrame
        master: pack할 부모 위젯
        """
        if not overall:
            return
            
        # 영역 표준화 헬퍼
        def normalize_region(name):
            s = str(name).replace(' ', '')
            if '검색' in s and '비검색' not in s and '비' not in s[:1]:
                return '검색'
            elif '비검색' in s or '상세' in s or '추천' in s or s == '-':
                return '비검색'
            elif '오디언스' in s or '오프사이트' in s or 'off' in s.lower() or '외부' in s:
                return '오디언스'
            return s
            
        # 영역별 합산 딕셔너리 구성
        region_data = {'검색': {}, '비검색': {}, '오디언스': {}}
        if region_summary is not None and not region_summary.empty:
            rs = region_summary.copy()
            rs['norm_region'] = rs['region'].apply(normalize_region)
            for region_name in ['검색', '비검색', '오디언스']:
                rr = rs[rs['norm_region'] == region_name]
                if not rr.empty:
                    region_data[region_name] = {
                        'spend': rr['spend'].sum(), 'sales': rr['sales'].sum(),
                        'orders': rr['orders'].sum(), 'imp': rr['imp'].sum(),
                        'click': rr['click'].sum(),
                    }
                    rd = region_data[region_name]
                    rd['ROAS'] = (rd['sales'] / rd['spend'] * 100) if rd['spend'] > 0 else 0
                    rd['CTR'] = (rd['click'] / rd['imp'] * 100) if rd['imp'] > 0 else 0
                    rd['CVR'] = (rd['orders'] / rd['click'] * 100) if rd['click'] > 0 else 0
                else:
                    region_data[region_name] = {'spend': 0, 'sales': 0, 'orders': 0, 'imp': 0, 'click': 0, 'ROAS': 0, 'CTR': 0, 'CVR': 0}
        
        metrics_frame = ctk.CTkFrame(master, fg_color="transparent")
        metrics_frame.pack(fill="x", padx=10, pady=(10, 10))
        
        metrics = [
            ("전체 광고비", "spend", "원"), ("실현 광고비", "spend", "원"),
            ("전환 매출", "sales", "원"), ("전체 매출", "sales", "원"),
            ("전체 판매수", "orders", "회"), ("노출수", "imp", "회"),
            ("클릭수", "click", "회"), ("클릭률", "CTR", "%"),
            ("전환 판매수", "orders", "회"), ("전환 주문수", "orders", "회"),
            ("수익률(ROAS)", "ROAS", "%"), ("전환율(CVR)", "CVR", "%")
        ]
        
        region_emojis = {'검색': '🔵', '비검색': '🟡', '오디언스': '🟢'}
        
        for i, (t, k, u) in enumerate(metrics):
            r, c = divmod(i, 6)
            card = ctk.CTkFrame(
                metrics_frame, 
                fg_color="#1E293B",
                border_width=2, 
                border_color="#3B82F6",
                corner_radius=12
            )
            card.grid(row=r, column=c, padx=6, pady=6, sticky="nsew")
            metrics_frame.grid_columnconfigure(c, weight=1)
            
            if "광고비" in t:
                color = "#FBBF24"
            elif "매출" in t:
                color = "#34D399"
            elif t in ["전체 판매수", "노출수", "클릭수", "전환 판매수", "전환 주문수"]:
                color = "#60A5FA"
            else:
                color = "#FB923C"
            
            # 메트릭 제목
            ctk.CTkLabel(card, text=t, font=("Malgun Gothic", 14, "bold"), 
                         text_color="#E2E8F0").pack(pady=(10, 0))
            
            # 전체 합산 값
            val = overall.get(k, 0.0)
            if u == "원" or u == "회": 
                text = f"{int(val):,} {u}"
            else: 
                text = f"{val:.2f} {u}"
                
            ctk.CTkLabel(card, text=text, font=("Malgun Gothic", 24, "bold"), 
                         text_color=color).pack(pady=(3, 0))
            
            # 영역별 세부 분류 서브라벨 (검색/비검색/오디언스) — 가로 한 줄 배치
            if region_summary is not None and not region_summary.empty:
                parts = []
                for rn in ['검색', '비검색', '오디언스']:
                    rd = region_data.get(rn, {})
                    rv = rd.get(k, 0.0)
                    emoji = region_emojis.get(rn, '⚪')
                    if u == "원" or u == "회":
                        parts.append(f"{emoji}{rn} {int(rv):,}")
                    else:
                        parts.append(f"{emoji}{rn} {rv:.2f}%")
                
                ctk.CTkLabel(card, text=" / ".join(parts), font=("Malgun Gothic", 9),
                             text_color="#94A3B8").pack(pady=(2, 8))

    def _render_magnifier_diagnosis(self, df, master, by_region_df=None):
        """
        영역별(검색/비검색/오디언스) 돋보기 1초 진단 처방전 UI 카드를 렌더링합니다.
        df: 전체 일별 추이 DataFrame (p_date, imp, CTR, CVR, ROAS 등)
        by_region_df: 영역별 일별 DataFrame (region, imp, CTR, CVR, ROAS 등)
        master: 카드를 pack할 부모 위젯
        """
        def normalize_region(name):
            s = str(name).replace(' ', '')
            if '검색' in s and '비검색' not in s and '비' not in s[:1]:
                return '검색 영역'
            elif '비검색' in s or '상세' in s or '추천' in s or s == '-':
                return '비검색 영역'
            elif '오디언스' in s or '오프사이트' in s or 'off' in s.lower() or '외부' in s:
                return '오디언스'
            return s
        
        region_colors = {
            '검색 영역': ('#3B82F6', '🔵'),
            '비검색 영역': ('#F59E0B', '🟡'),
            '오디언스': ('#10B981', '🟢')
        }
        region_labels = ['검색 영역', '비검색 영역', '오디언스']
        
        # 분석 대상 데이터프레임들 준비 (전체 + 영역별)
        analysis_targets = []
        
        # 1) 전체 합산 진단
        analysis_targets.append(('📊 전체 합산', df, '#EC4899'))
        
        # 2) 영역별 진단
        if by_region_df is not None and not by_region_df.empty:
            rdf = by_region_df.copy()
            rdf['norm_region'] = rdf['region'].apply(normalize_region)
            
            for region_name in region_labels:
                rdata = rdf[rdf['norm_region'] == region_name].copy()
                if rdata.empty:
                    continue
                # 날짜별 합산
                rdata = rdata.groupby(['date_s']).agg({
                    'imp': 'sum', 'click': 'sum', 'spend': 'sum',
                    'sales': 'sum', 'orders': 'sum'
                }).reset_index()
                rdata['CTR'] = np.where(rdata['imp'] > 0, (rdata['click'] / rdata['imp']) * 100, 0)
                rdata['CVR'] = np.where(rdata['click'] > 0, (rdata['orders'] / rdata['click']) * 100, 0)
                rdata['ROAS'] = np.where(rdata['spend'] > 0, (rdata['sales'] / rdata['spend']) * 100, 0)
                
                rc, emoji = region_colors.get(region_name, ('#FFFFFF', '⚪'))
                analysis_targets.append((f'{emoji} {region_name}', rdata, rc))
        
        # 메인 진단 카드 프레임
        diag_card = ctk.CTkFrame(master, fg_color="#10102B", border_width=2, border_color="#EC4899", corner_radius=15)
        diag_card.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(diag_card, text="🔎 AI 광고효율 돋보기 1초 진단 처방전 (영역별 분석)",
                     font=("Malgun Gothic", 16, "bold"), text_color="#F472B6").pack(anchor="w", padx=25, pady=(20, 10))
        
        for target_name, target_df, border_color in analysis_targets:
            n_days = len(target_df)
            if n_days < 2:
                continue
            
            split_idx = max(1, n_days - 3) if n_days >= 4 else 1
            recent_df = target_df.iloc[split_idx:]
            prev_df = target_df.iloc[:split_idx]
            
            recent_roas = recent_df['ROAS'].mean()
            prev_roas = prev_df['ROAS'].mean()
            recent_imp = recent_df['imp'].mean()
            prev_imp = prev_df['imp'].mean()
            recent_ctr = recent_df['CTR'].mean()
            prev_ctr = prev_df['CTR'].mean()
            recent_cvr = recent_df['CVR'].mean()
            prev_cvr = prev_df['CVR'].mean()
            
            chg_roas = ((recent_roas - prev_roas) / prev_roas * 100) if prev_roas > 0 else (100.0 if recent_roas > 0 else 0)
            chg_imp = ((recent_imp - prev_imp) / prev_imp * 100) if prev_imp > 0 else (100.0 if recent_imp > 0 else 0)
            chg_ctr = ((recent_ctr - prev_ctr) / prev_ctr * 100) if prev_ctr > 0 else (100.0 if recent_ctr > 0 else 0)
            chg_cvr = ((recent_cvr - prev_cvr) / prev_cvr * 100) if prev_cvr > 0 else (100.0 if recent_cvr > 0 else 0)
            
            lamp_imp = "🟢 양호" if chg_imp >= -5 else ("🟡 주의" if chg_imp >= -20 else "🔴 위험")
            lamp_ctr = "🟢 양호" if chg_ctr >= -5 else ("🟡 주의" if chg_ctr >= -20 else "🔴 위험")
            lamp_cvr = "🟢 양호" if chg_cvr >= -5 else ("🟡 주의" if chg_cvr >= -20 else "🔴 위험")
            
            # 영역별 서브카드
            sub_card = ctk.CTkFrame(diag_card, fg_color="#1A1A2E", border_width=1, border_color=border_color, corner_radius=10)
            sub_card.pack(fill="x", padx=20, pady=8)
            
            ctk.CTkLabel(sub_card, text=f"【{target_name}】", font=("Malgun Gothic", 14, "bold"),
                         text_color=border_color).pack(anchor="w", padx=15, pady=(10, 5))
            
            # 신호등 정보판
            signal_frame = ctk.CTkFrame(sub_card, fg_color="transparent")
            signal_frame.pack(fill="x", padx=15, pady=3)
            
            for lbl_text, lbl_color in [
                (f"💎 노출수 [{lamp_imp}] ({chg_imp:+.1f}%)", "#00E5FF"),
                (f"🍊 클릭률 [{lamp_ctr}] ({chg_ctr:+.1f}%)", "#FB923C"),
                (f"🍋 전환율 [{lamp_cvr}] ({chg_cvr:+.1f}%)", "#10B981"),
                (f"🌸 ROAS [{'📈' if chg_roas>=0 else '📉'}] ({chg_roas:+.1f}%)", "#FF00FF"),
            ]:
                ctk.CTkLabel(signal_frame, text=lbl_text, font=("Malgun Gothic", 12, "bold"),
                             width=200, height=36, fg_color="#1A1D36", corner_radius=6,
                             text_color=lbl_color).pack(side="left", padx=4)
            
            # 핵심 한 줄 처방전
            if chg_roas < 0:
                min_val = min(chg_imp, chg_ctr, chg_cvr)
                if min_val == chg_ctr:
                    verdict = f"⚠️ 클릭률 급감이 주요 원인! 썸네일/상품명 교체 검토 필요"
                elif min_val == chg_cvr:
                    verdict = f"⚠️ 전환율 하락이 주요 원인! 상세페이지/가격/리뷰 점검 필요"
                else:
                    verdict = f"⚠️ 노출 부족이 주요 원인! 입찰가 인상 검토 필요"
                v_color = "#F87171"
            else:
                max_val = max(chg_imp, chg_ctr, chg_cvr)
                if max_val == chg_ctr:
                    verdict = f"🎉 클릭률 상승세! 썸네일 전략이 효과적"
                elif max_val == chg_cvr:
                    verdict = f"🎉 전환율 폭발! 상세페이지 설득력 우수"
                else:
                    verdict = f"🎉 노출 확대! 입찰 전략 적중"
                v_color = "#34D399"
            
            ctk.CTkLabel(sub_card, text=verdict, font=("Malgun Gothic", 12, "bold"),
                         text_color=v_color, justify="left", wraplength=900).pack(anchor="w", padx=15, pady=(3, 10))

    def _render_magnifier_chart(self, df, master, by_region_df=None):
        """
        영역별(검색/비검색/오디언스) 상대 지수 돋보기 차트를 렌더링합니다.
        by_region_df가 제공되면 영역별 서브플롯으로, 없으면 전체 합산 단일 차트로 동작합니다.
        """
        plt.rcParams['font.family'] = 'Malgun Gothic'
        pe = [path_effects.withStroke(linewidth=2, foreground='black')]
        
        # 오디언스 등 데이터 누락 영역의 dates 덮어쓰기 오염 방지용 마스터 날짜
        master_dates = df['date_s'].tolist()
        
        # 영역 표준화 헬퍼
        def normalize_region(name):
            s = str(name).replace(' ', '')
            if '검색' in s and '비검색' not in s and '비' not in s[:1]:
                return '검색 영역'
            elif '비검색' in s or '상세' in s or '추천' in s or s == '-':
                return '비검색 영역'
            elif '오디언스' in s or '오프사이트' in s or 'off' in s.lower() or '외부' in s:
                return '오디언스'
            return s
        
        region_colors = {
            '검색 영역': '#3B82F6',
            '비검색 영역': '#F59E0B',
            '오디언스': '#10B981'
        }
        region_labels = ['검색 영역', '비검색 영역', '오디언스']
        
        # 영역별 데이터가 있는 경우
        if by_region_df is not None and not by_region_df.empty:
            rdf = by_region_df.copy()
            rdf['norm_region'] = rdf['region'].apply(normalize_region)
            
            # 존재하는 영역만 필터링
            available_regions = [r for r in region_labels if r in rdf['norm_region'].unique()]
            if not available_regions:
                available_regions = region_labels[:1]
            
            n_regions = len(available_regions)
            fig = Figure(figsize=(16, 4.5 * n_regions + 1), dpi=100)
            fig.patch.set_facecolor('#0B0B1A')
            
            fig.suptitle("0. 영역별 광고효율 돋보기 상대 지수 분석 (첫 날 = 100% 기준)", 
                        color='white', fontsize=16, fontweight='bold', y=0.995)
            
            for idx, region_name in enumerate(available_regions):
                rdata = rdf[rdf['norm_region'] == region_name].copy()
                if rdata.empty:
                    continue
                    
                # 날짜별 합산 (같은 영역 내 중복 날짜 합산)
                rdata = rdata.groupby('date_s').agg({
                    'imp': 'sum', 'click': 'sum', 'spend': 'sum', 
                    'sales': 'sum', 'orders': 'sum'
                }).reset_index()
                rdata['CTR'] = np.where(rdata['imp'] > 0, (rdata['click'] / rdata['imp']) * 100, 0)
                rdata['CVR'] = np.where(rdata['click'] > 0, (rdata['orders'] / rdata['click']) * 100, 0)
                rdata['ROAS'] = np.where(rdata['spend'] > 0, (rdata['sales'] / rdata['spend']) * 100, 0)
                
                if len(rdata) < 1:
                    continue
                
                ax = fig.add_subplot(n_regions, 1, idx + 1)
                ax.set_facecolor('#0B0B1A')
                ax.tick_params(axis='x', labelcolor='#94A3B8', labelsize=9, rotation=25)
                ax.tick_params(axis='y', labelcolor='#94A3B8', labelsize=9)
                ax.grid(True, axis='y', color='#1F2937', linestyle='--', alpha=0.4)
                
                # 기준값 계산 (첫날 또는 평균, 0 방지)
                def get_base(series):
                    val = series.iloc[0]
                    if val > 0: return val
                    mean_val = series.mean()
                    if mean_val > 0: return mean_val
                    return 1.0
                
                base_imp = get_base(rdata['imp'])
                base_ctr = get_base(rdata['CTR'])
                base_cvr = get_base(rdata['CVR'])
                base_roas = get_base(rdata['ROAS'])
                
                rdata['imp_idx'] = rdata['imp'] / base_imp * 100
                rdata['ctr_idx'] = rdata['CTR'] / base_ctr * 100
                rdata['cvr_idx'] = rdata['CVR'] / base_cvr * 100
                rdata['roas_idx'] = rdata['ROAS'] / base_roas * 100
                
                dates = rdata['date_s'].tolist()
                rc = region_colors.get(region_name, '#FFFFFF')
                
                # 호버용 데이터 바인딩
                ax.roas_vals = rdata['roas_idx'].tolist()
                
                ax.plot(dates, rdata['imp_idx'], color='#00E5FF', marker='o', markersize=5, linewidth=2.0, 
                        label='💎 노출수 지수', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
                ax.plot(dates, rdata['ctr_idx'], color='#FB923C', marker='s', markersize=5, linewidth=2.0, 
                        label='🍊 클릭률(CTR) 지수', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
                ax.plot(dates, rdata['cvr_idx'], color='#10B981', marker='^', markersize=5, linewidth=2.0, 
                        label='🍋 전환율(CVR) 지수', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
                ax.plot(dates, rdata['roas_idx'], color='#FF00FF', marker='D', markersize=6, linewidth=3.0, 
                        label='🌸 광고효율(ROAS) 지수', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
                
                ax.axhline(y=100, color='#FFFFFF', linestyle='--', linewidth=1.2, alpha=0.5, label='— 첫 날 기준선 (100%)')
                
                # 영역별 타이틀 (영역 대표 색상 적용)
                ax.set_title(f"【{region_name}】 노출·클릭률·전환율·ROAS 상대 지수 추이", 
                            color=rc, pad=12, fontdict={'size': 13, 'weight': 'bold'})
                ax.set_ylabel('상대 지수 (%)', color='white', size=10, weight='bold')
                ax.legend(loc='upper left', fontsize=8, facecolor='#1A1A2E', edgecolor='#333', labelcolor='white', framealpha=0.8)
                
                # 메모 세로선 연동
                self._draw_memo_vlines([ax], dates, pe, fontsize=7)
            
            fig.tight_layout(pad=2.0, rect=[0, 0, 1, 0.98])
        else:
            # by_region이 없는 경우 전체 합산 단일 차트 (기존 방식 유지)
            fig = Figure(figsize=(16, 5), dpi=100)
            fig.patch.set_facecolor('#0B0B1A')
            
            ax = fig.add_subplot(1, 1, 1)
            ax.set_facecolor('#0B0B1A')
            ax.tick_params(axis='x', labelcolor='#94A3B8', labelsize=9, rotation=25)
            ax.tick_params(axis='y', labelcolor='#94A3B8', labelsize=9)
            ax.grid(True, axis='y', color='#1F2937', linestyle='--', alpha=0.4)
            
            def get_base(col):
                val = df[col].iloc[0]
                if val > 0: return val
                mean_val = df[col].mean()
                if mean_val > 0: return mean_val
                return 1.0
                
            base_imp = get_base('imp')
            base_ctr = get_base('CTR')
            base_cvr = get_base('CVR')
            base_roas = get_base('ROAS')
            
            df_copy = df.copy()
            df_copy['imp_idx'] = df_copy['imp'] / base_imp * 100
            df_copy['ctr_idx'] = df_copy['CTR'] / base_ctr * 100
            df_copy['cvr_idx'] = df_copy['CVR'] / base_cvr * 100
            df_copy['roas_idx'] = df_copy['ROAS'] / base_roas * 100
            
            dates = df_copy['date_s'].tolist()
            
            # 호버용 데이터 바인딩
            ax.roas_vals = df_copy['roas_idx'].tolist()
            
            ax.plot(dates, df_copy['imp_idx'], color='#00E5FF', marker='o', markersize=5, linewidth=2.0, 
                    label='💎 노출수 지수', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
            ax.plot(dates, df_copy['ctr_idx'], color='#FB923C', marker='s', markersize=5, linewidth=2.0, 
                    label='🍊 클릭률(CTR) 지수', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
            ax.plot(dates, df_copy['cvr_idx'], color='#10B981', marker='^', markersize=5, linewidth=2.0, 
                    label='🍋 전환율(CVR) 지수', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
            ax.plot(dates, df_copy['roas_idx'], color='#FF00FF', marker='D', markersize=6, linewidth=3.0, 
                    label='🌸 광고효율(ROAS) 지수', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
            ax.axhline(y=100, color='#FFFFFF', linestyle='--', linewidth=1.2, alpha=0.5, label='— 첫 날 기준선 (100%)')
            
            ax.set_ylabel('상대 지수 (%)', color='white', size=10, weight='bold')
            ax.set_title("0. 광고효율 돋보기 상대 지수 분석 (첫 날 데이터 = 100% 기준)", color='white', pad=15, fontdict={'size': 14, 'weight': 'bold'})
            ax.legend(loc='upper left', fontsize=9, facecolor='#1A1A2E', edgecolor='#333', labelcolor='white', framealpha=0.8)
            
            self._draw_memo_vlines([ax], dates, pe, fontsize=8)
            fig.tight_layout(pad=2.0)
        
        canvas = FigureCanvasTkAgg(fig, master=master)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        
        # ─── 툴팁 설정 및 호버 이벤트 추가 ───
        tooltips = {}
        for ax_obj in fig.get_axes():
            if ax_obj.get_title():
                tooltip = ax_obj.annotate("", xy=(0,0), xytext=(30,-30), textcoords="offset points",
                                          bbox=dict(boxstyle="round,pad=0.6", fc="white", ec="#C2185B", lw=3, alpha=1.0),
                                          arrowprops=dict(arrowstyle="->", color="#C2185B", lw=2),
                                          color="black", fontsize=11, weight="bold", zorder=20)
                tooltip.set_visible(False)
                tooltips[ax_obj] = tooltip
                
        canvas._last_hover_state = (None, None)
        
        def on_hover(event):
            vis_changed = False
            in_ax = event.inaxes
            x_val = event.xdata
            idx = int(round(x_val)) if (in_ax is not None and x_val is not None) else None
            
            # 렌더링 지연 제거: 마우스 위치 및 인덱스가 이전과 같으면 즉시 리턴
            if canvas._last_hover_state == (in_ax, idx):
                return
            canvas._last_hover_state = (in_ax, idx)
            
            if in_ax is None or idx is None:
                for tt in tooltips.values():
                    if tt.get_visible():
                        tt.set_visible(False)
                        vis_changed = True
                if vis_changed:
                    canvas.draw_idle()
                return
                
            ax_current = in_ax
            if ax_current in tooltips:
                if 0 <= idx < len(master_dates):
                    d = master_dates[idx]
                    day_memos = [m for m in self.memos if self._memo_date_to_mmdd(m['date']) == d]
                    if day_memos:
                        roas_val = ax_current.roas_vals[idx] if hasattr(ax_current, 'roas_vals') else 100
                        
                        txt_parts = [f"ROAS 지수: {roas_val:.0f}%", ""]
                        for m in day_memos:
                            d_key = self._parse_memo_date_to_key(m['date'])
                            txt_parts.append(d_key)
                            txt_parts.append(m['memo'])
                            txt_parts.append("")
                        txt = "\n".join(txt_parts[:-1])
                        
                        tt = tooltips[ax_current]
                        
                        # 텍스트나 좌표가 실제로 바뀌었다면 갱신
                        if tt.xy != (idx, roas_val) or tt.get_text() != txt or not tt.get_visible():
                            tt.xy = (idx, roas_val)
                            tt.set_text(txt)
                            tt.set_visible(True)
                            vis_changed = True
                            
                        # 다른 서브플롯의 툴팁 숨김
                        for other_ax, other_tt in tooltips.items():
                            if other_ax != ax_current and other_tt.get_visible():
                                other_tt.set_visible(False)
                                vis_changed = True
                                
                        if vis_changed:
                            canvas.draw_idle()
                        return
                        
            for tt in tooltips.values():
                if tt.get_visible():
                    tt.set_visible(False)
                    vis_changed = True
            if vis_changed:
                canvas.draw_idle()
                
        fig.canvas.mpl_connect("motion_notify_event", on_hover)

    def _render_large_trend_chart(self, df, kw_data, master):
        plt.rcParams['font.family'] = 'Malgun Gothic'
        pe = [path_effects.withStroke(linewidth=2, foreground='black')]
        n = len(df)
        step = 3 if n > 10 else 2 if n > 5 else 1
        fs_title = 15; fs_guide = 8.5; fs_ann = 8; fs_label = 10; fs_tick = 8; fs_leg = 9
        ms = 4; lw = 2
        
        # 12대 차트 출력을 위해 높이를 38인치로 대폭 확장하여 6행 2열 레이아웃을 여유 있게 그립니다.
        fig = Figure(figsize=(18, 38), dpi=100)
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
        ax1 = fig.add_subplot(6, 2, 1); setup_ax(ax1)
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
        ax2 = fig.add_subplot(6, 2, 2); setup_ax(ax2)
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
        ax2_2.plot(df['date_s'], df['sales'], color='#00E5FF', marker='o', markersize=ms, linewidth=lw, 
                   label='— 광고매출액', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
        ax2_2.set_ylabel('광고매출액 (원)', color='#00E5FF', weight='bold', fontsize=fs_label)
        ax2_2.tick_params(axis='y', labelcolor='#00E5FF', labelsize=fs_tick)
        for i, v in enumerate(df['sales']):
            if v == 0: continue
            offset_y = -14 if i % 2 == 0 else 10
            ax2_2.annotate(self._fmt_val(v, 'won'), (df['date_s'].iloc[i], v), 
                           xytext=(0, offset_y), textcoords="offset points", ha='center', color='#00E5FF', 
                           weight='bold', fontsize=fs_ann, path_effects=pe)
        add_legend(ax2, ax2_2)

        # ─── 3. 광고비 vs ROAS [좌상 2] ───
        ax3 = fig.add_subplot(6, 2, 3); setup_ax(ax3)
        ax3.set_title("3. 광고비 vs ROAS 추이", color='white', pad=65, loc='center', fontdict={'size': fs_title, 'weight': 'bold'})
        guide_str3 = (
            "마중물 투입[광고비 막대] = 집행 광고비   |   마법의 효율[ROAS 선] = 투자 대비 몇 배 매출인지\n"
            "☞ [비효율 경고] 광고비는 늘리는데 ROAS 선이 고꾸라짐   |   ☞ [증액 타이밍] 광고비를 올려도 ROAS가 330%선 지탱\n"
            "💡 [이렇게 보면 좋은 것?] 광고비(막대)를 늘릴 때, ROAS선이 안정 기준선(330%) 위에서 흔들림 없이 버티는 형태!"
        )
        ax3.text(0.5, 1.02, guide_str3, transform=ax3.transAxes,
                ha='center', va='bottom', color='#A0AEC0', fontsize=fs_guide, style='normal', weight='bold',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#111122', edgecolor='#10B981', alpha=0.95))
        ax3.bar(df['date_s'], df['spend'], color='#EF4444', alpha=0.35, label='■ 광고비')
        ax3.set_ylabel('광고비 (원)', color='#EF4444', weight='bold', fontsize=fs_label)
        ax3.tick_params(axis='y', labelcolor='#EF4444', labelsize=fs_tick)
        
        ax3_2 = ax3.twinx()
        ax3_2.plot(df['date_s'], df['ROAS'], color='#10B981', marker='o', markersize=ms, linewidth=lw, 
                   label='— ROAS%', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
        ax3_2.axhline(y=330, color='#F59E0B', linestyle='--', linewidth=1.2, label='— 흑자 안전 기준선 (330%)')
        ax3_2.set_ylabel('ROAS (%)', color='#10B981', weight='bold', fontsize=fs_label)
        ax3_2.tick_params(axis='y', labelcolor='#10B981', labelsize=fs_tick)
        for i, v in enumerate(df['ROAS']):
            if v == 0: continue
            offset_y = -14 if i % 2 == 0 else 10
            ax3_2.annotate(f"{v:.0f}%", (df['date_s'].iloc[i], v), 
                           xytext=(0, offset_y), textcoords="offset points", ha='center', color='#10B981', 
                           weight='bold', fontsize=fs_ann, path_effects=pe)
        add_legend(ax3, ax3_2)

        # ─── 4. 노출수 vs 클릭수 [우상 2] ───
        ax4 = fig.add_subplot(6, 2, 4); setup_ax(ax4)
        ax4.set_title("4. 노출수 vs 클릭수 추이", color='white', pad=65, loc='center', fontdict={'size': fs_title, 'weight': 'bold'})
        guide_str4 = (
            "스쳐 지나감[노출수 막대] = 쿠팡에 노출된 횟수   |   발길 멈춤[클릭수 선] = 상품을 눌러본 고객수\n"
            "☞ [썸네일 매력 부족] 노출은 태평양인데 클릭 선이 바닥   |   ☞ [인기 만점] 노출 대비 클릭 선이 솟아오름\n"
            "💡 [이렇게 보면 좋은 것?] 노출 막대를 디딤돌 삼아 고객 발길(클릭) 선이 하늘을 향해 시원하게 날아오르는 추세!"
        )
        ax4.text(0.5, 1.02, guide_str4, transform=ax4.transAxes,
                ha='center', va='bottom', color='#A0AEC0', fontsize=fs_guide, style='normal', weight='bold',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#111122', edgecolor='#60A5FA', alpha=0.95))
        ax4.bar(df['date_s'], df['imp'], color='#60A5FA', alpha=0.25, label='■ 노출수')
        ax4.set_ylabel('노출수 (회)', color='#60A5FA', weight='bold', fontsize=fs_label)
        ax4.tick_params(axis='y', labelcolor='#60A5FA', labelsize=fs_tick)
        
        ax4_2 = ax4.twinx()
        ax4_2.plot(df['date_s'], df['click'], color='#3B82F6', marker='o', markersize=ms, linewidth=lw, 
                   label='— 클릭수', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
        ax4_2.set_ylabel('클릭수 (회)', color='#3B82F6', weight='bold', fontsize=fs_label)
        ax4_2.tick_params(axis='y', labelcolor='#3B82F6', labelsize=fs_tick)
        for i, v in enumerate(df['click']):
            if v == 0: continue
            offset_y = -14 if i % 2 == 0 else 10
            ax4_2.annotate(f"{int(v):,}", (df['date_s'].iloc[i], v), 
                           xytext=(0, offset_y), textcoords="offset points", ha='center', color='#3B82F6', 
                           weight='bold', fontsize=fs_ann, path_effects=pe)
        add_legend(ax4, ax4_2)

        # ─── 5. 클릭수 vs CTR [좌상 3] ───
        ax5 = fig.add_subplot(6, 2, 5); setup_ax(ax5)
        ax5.set_title("5. 클릭수 vs CTR 추이", color='white', pad=65, loc='center', fontdict={'size': fs_title, 'weight': 'bold'})
        guide_str5 = (
            "매장 입장[클릭수 막대] = 매장을 구경하는 고객   |   호기심 지수[CTR 선] = 노출 대비 클릭 클릭률\n"
            "☞ [흥미 없음] 노출은 많은데 CTR 선이 0.5% 미만 점검   |   ☞ [자석 썸네일] CTR 선이 1.5% 돌파 및 우상향\n"
            "💡 [이렇게 보면 좋은 것?] 클릭 막대가 두툼하게 커지며 클릭률(CTR) 선이 1.5% 위 안전 영역에 안착하는 그림!"
        )
        ax5.text(0.5, 1.02, guide_str5, transform=ax5.transAxes,
                ha='center', va='bottom', color='#A0AEC0', fontsize=fs_guide, style='normal', weight='bold',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#111122', edgecolor='#FB923C', alpha=0.95))
        ax5.bar(df['date_s'], df['click'], color='#F59E0B', alpha=0.35, label='■ 클릭수')
        ax5.set_ylabel('클릭수 (회)', color='#F59E0B', weight='bold', fontsize=fs_label)
        ax5.tick_params(axis='y', labelcolor='#F59E0B', labelsize=fs_tick)
        
        ax5_2 = ax5.twinx()
        ax5_2.plot(df['date_s'], df['CTR'], color='#FB923C', marker='o', markersize=ms, linewidth=lw, 
                   label='— CTR%', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
        ax5_2.axhline(y=1.0, color='#6B7280', linestyle='--', linewidth=1.2, label='— 평균 기준선 (1.0%)')
        ax5_2.set_ylabel('CTR (%)', color='#FB923C', weight='bold', fontsize=fs_label)
        ax5_2.tick_params(axis='y', labelcolor='#FB923C', labelsize=fs_tick)
        for i, v in enumerate(df['CTR']):
            if v == 0: continue
            offset_y = -14 if i % 2 == 0 else 10
            ax5_2.annotate(f"{v:.2f}%", (df['date_s'].iloc[i], v), 
                           xytext=(0, offset_y), textcoords="offset points", ha='center', color='#FB923C', 
                           weight='bold', fontsize=fs_ann, path_effects=pe)
        add_legend(ax5, ax5_2)

        # ─── 6. 클릭수 vs CVR [우상 3] ───
        ax6 = fig.add_subplot(6, 2, 6); setup_ax(ax6)
        ax6.set_title("6. 클릭수 vs CVR 추이", color='white', pad=65, loc='center', fontdict={'size': fs_title, 'weight': 'bold'})
        guide_str6 = (
            "매장 입장[클릭수 막대] = 상품을 눌러본 총 클릭   |   구매 설득력[CVR 선] = 클릭 대비 구매 전환율\n"
            "☞ [상상 연애 중] 들어는 오는데 CVR이 3% 미만 탈출   |   ☞ [완벽한 설득] CVR 선이 5~10% 이상으로 유지\n"
            "💡 [이렇게 보면 좋은 것?] 클릭(막대)이 유입되는 것과 보조를 맞춰 전환율(CVR) 선이 8%선 이상으로 비상하는 형태!"
        )
        ax6.text(0.5, 1.02, guide_str6, transform=ax6.transAxes,
                ha='center', va='bottom', color='#A0AEC0', fontsize=fs_guide, style='normal', weight='bold',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#111122', edgecolor='#EC4899', alpha=0.95))
        ax6.bar(df['date_s'], df['click'], color='#F59E0B', alpha=0.35, label='■ 클릭수')
        ax6.set_ylabel('클릭수 (회)', color='#F59E0B', weight='bold', fontsize=fs_label)
        ax6.tick_params(axis='y', labelcolor='#F59E0B', labelsize=fs_tick)
        
        ax6_2 = ax6.twinx()
        ax6_2.plot(df['date_s'], df['CVR'], color='#EC4899', marker='o', markersize=ms, linewidth=lw, 
                   label='— CVR%', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
        ax6_2.axhline(y=5.0, color='#6B7280', linestyle='--', linewidth=1.2, label='— 평균 기준선 (5.0%)')
        ax6_2.set_ylabel('CVR (%)', color='#EC4899', weight='bold', fontsize=fs_label)
        ax6_2.tick_params(axis='y', labelcolor='#EC4899', labelsize=fs_tick)
        for i, v in enumerate(df['CVR']):
            if v == 0: continue
            offset_y = -14 if i % 2 == 0 else 10
            ax6_2.annotate(f"{v:.1f}%", (df['date_s'].iloc[i], v), 
                           xytext=(0, offset_y), textcoords="offset points", ha='center', color='#EC4899', 
                           weight='bold', fontsize=fs_ann, path_effects=pe)
        add_legend(ax6, ax6_2)

        # ─── 7. 클릭수 vs 평균 클릭비용(CPC) [좌상 4] ───
        ax7 = fig.add_subplot(6, 2, 7); setup_ax(ax7)
        ax7.set_title("7. 클릭수 vs 평균 클릭비용(CPC) 추이", color='white', pad=65, loc='center', fontdict={'size': fs_title, 'weight': 'bold'})
        guide_str7 = (
            "매장 구경[클릭수 막대] = 클릭으로 모신 손님   |   손님 단가[CPC 선] = 1클릭당 쿠팡에 준 입찰 단가\n"
            "☞ [출혈 경쟁 구간] 클릭 단가 CPC 선이 고공행진 점검   |   ☞ [꿀 매물 유입] 저렴한 CPC 선 단가로 많은 고객 모심\n"
            "💡 [이렇게 보면 좋은 것?] CPC 단가 선은 지하실로 안착하고, 유입 클릭 막대는 성곽처럼 높게 쌓이는 모범적인 모습!"
        )
        ax7.text(0.5, 1.02, guide_str7, transform=ax7.transAxes,
                ha='center', va='bottom', color='#A0AEC0', fontsize=fs_guide, style='normal', weight='bold',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#111122', edgecolor='#8B5CF6', alpha=0.95))
        ax7.bar(df['date_s'], df['click'], color='#F59E0B', alpha=0.35, label='■ 클릭수')
        ax7.set_ylabel('클릭수 (회)', color='#F59E0B', weight='bold', fontsize=fs_label)
        ax7.tick_params(axis='y', labelcolor='#F59E0B', labelsize=fs_tick)
        
        ax7_2 = ax7.twinx()
        ax7_2.plot(df['date_s'], df['CPC'], color='#8B5CF6', marker='o', markersize=ms, linewidth=lw, 
                   label='— CPC (₩)', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
        ax7_2.set_ylabel('CPC (원)', color='#8B5CF6', weight='bold', fontsize=fs_label)
        ax7_2.tick_params(axis='y', labelcolor='#8B5CF6', labelsize=fs_tick)
        for i, v in enumerate(df['CPC']):
            if v == 0: continue
            offset_y = -14 if i % 2 == 0 else 10
            ax7_2.annotate(f"{int(v)}원", (df['date_s'].iloc[i], v), 
                           xytext=(0, offset_y), textcoords="offset points", ha='center', color='#8B5CF6', 
                           weight='bold', fontsize=fs_ann, path_effects=pe)
        add_legend(ax7, ax7_2)

        # ─── 8. 날짜별 광고비·광고매출 추이 [우상 4] ───
        ax8 = fig.add_subplot(6, 2, 8); setup_ax(ax8)
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
        ax9 = fig.add_subplot(6, 2, 9); setup_ax(ax9)
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
        ax10 = fig.add_subplot(6, 2, 10); ax10.set_facecolor('#0B0B1A')
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
            def wrap_kw(text, width=8):
                if not text: return ""
                t = str(text).strip()
                return '\n'.join([t[i:i+width] for i in range(0, len(t), width)])
            
            top_kws['kw_wrapped'] = top_kws['kw'].apply(lambda x: wrap_kw(x, 8))
            x_indices = list(range(len(top_kws)))
            x_labels = top_kws['kw_wrapped'].tolist()
            
            ax10.bar(x_indices, top_kws['spend'], color='#EF4444', alpha=0.35, label='■ 광고비')
            ax10.set_ylabel('광고비 (원)', color='#EF4444', weight='bold', fontsize=fs_label)
            ax10.tick_params(axis='y', labelcolor='#EF4444', labelsize=fs_tick)
            
            ax10.set_xticks(x_indices)
            ax10.set_xticklabels(x_labels, color='white', fontsize=fs_tick - 1.5, rotation=0, ha='center')
            ax10.tick_params(axis='x', labelcolor='white', labelsize=fs_tick - 1.5)
            
            ax10_2 = ax10.twinx()
            ax10_2.plot(x_indices, top_kws['orders'], color='#10B981', marker='s', markersize=ms, linewidth=lw, label='— 주문수', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
            ax10_2.set_ylabel('주문수 (건)', color='#10B981', weight='bold', fontsize=fs_label)
            ax10_2.tick_params(axis='y', labelcolor='#10B981', labelsize=fs_tick)
            
            for i, v in enumerate(top_kws['orders']):
                if v == 0: continue
                ax10_2.annotate(f"{int(v)}건", (x_indices[i], v), xytext=(0, 10), textcoords="offset points", ha='center', color='#10B981', weight='bold', fontsize=fs_ann, path_effects=pe)
            add_legend(ax10, ax10_2)
        else:
            ax10.text(0.5, 0.5, "표시할 키워드 데이터가 없습니다.", transform=ax10.transAxes, ha='center', va='center', color='#94A3B8', fontsize=12)

        # ─── 11. 광고비 비중 및 광고 기여도 추이 [좌상 6] ───
        ax11 = fig.add_subplot(6, 2, 11); setup_ax(ax11)
        ax11.set_title("11. 광고비 비중 및 광고 기여도 추이", color='white', pad=65, loc='center', fontdict={'size': fs_title, 'weight': 'bold'})
        guide_str11 = (
            "가성비 노란등[광고비 비중 선] = 매출 대비 광고비 비율   |   마진 안전선[초록 점선] = 내 마진율 마지노선\n"
            "☞ [위험 구간] 광고비 비중이 내 마진율 선 위로 치솟음   |   ☞ [안전 상태] 비중 선이 10% 경고선 밑에 안정되게 방어됨\n"
            "💡 [이렇게 보면 좋은 것?] 노란 광고비 비중 선이 초록 마진선 아래, 그리고 10% 경고선 밑에 납작하게 처박히는 그림!"
        )
        ax11.text(0.5, 1.02, guide_str11, transform=ax11.transAxes,
                ha='center', va='bottom', color='#A0AEC0', fontsize=fs_guide, style='normal', weight='bold',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#111122', edgecolor='#FBBF24', alpha=0.95))
        
        spend_ratio_series = (df['spend'] / df['sales'] * 100).fillna(0)
        ax11.plot(df['date_s'], spend_ratio_series, color='#FBBF24', marker='o', markersize=ms, linewidth=lw, label='— 광고비 비중 (%)')
        ax11.axhline(y=30, color='#10B981', linestyle='--', linewidth=1.2, alpha=0.8, label='— 내 마진율 (30%)')
        ax11.axhline(y=10, color='#EF4444', linestyle=':', linewidth=1.2, alpha=0.8, label='— 경고선 (10%)')
        ax11.set_ylabel('비중 (%)', color='white', weight='bold', fontsize=fs_label)
        ax11.tick_params(axis='y', labelcolor='white', labelsize=fs_tick)
        for i, v in enumerate(spend_ratio_series):
            if v == 0: continue
            offset_y = -14 if i % 2 == 0 else 10
            ax11.annotate(f"{v:.1f}%", (df['date_s'].iloc[i], v), 
                           xytext=(0, offset_y), textcoords="offset points", ha='center', color='#FBBF24', 
                           weight='bold', fontsize=fs_ann, path_effects=pe)
        ax11.legend(loc='upper left', fontsize=fs_leg, facecolor='#1A1A2E', edgecolor='#333', labelcolor='white', framealpha=0.8)

        # ─── 12. 광고 차감 후 최종 순수익 vs 광고비 추이 [우상 6] ───
        ax12 = fig.add_subplot(6, 2, 12); setup_ax(ax12)
        ax12.set_title("12. 광고 차감 후 최종 순수익 vs 광고비 추이", color='white', pad=65, loc='center', fontdict={'size': fs_title, 'weight': 'bold'})
        guide_str12 = (
            "진짜 최종 순수익[하늘색 선] = 마진액에서 광고비를 차감한 알짜 순이익   |   광고비 예산[빨간 선] = 집행 광고비\n"
            "☞ [가짜 흑자 독수독과] 빨간 광고비 선은 우상향하는데 하늘색 순이익 선은 아래로 꺾이거나 영하 적자 구간 돌파\n"
            "💡 [이렇게 보면 좋은 것?] 지출 광고비 선보다 최종 순이익 선이 훨씬 높은 위치에서 평행하게 손 잡고 올라가는 그림!"
        )
        ax12.text(0.5, 1.02, guide_str12, transform=ax12.transAxes,
                ha='center', va='bottom', color='#A0AEC0', fontsize=fs_guide, style='normal', weight='bold',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#111122', edgecolor='#34D399', alpha=0.95))
        
        margin_rate = 0.3
        gross_profit = df['sales'] * margin_rate
        net_profit = gross_profit - df['spend']
        
        ax12.bar(df['date_s'], gross_profit, color='#94A3B8', alpha=0.15, label='■ 광고 전 마진액 (₩)')
        ax12.plot(df['date_s'], df['spend'], color='#EF4444', marker='x', linewidth=lw-0.5, markersize=ms, linestyle='--', label='— 지출 광고비 (₩)')
        ax12.plot(df['date_s'], net_profit, color='#00E5FF', marker='o', linewidth=lw+1, markersize=ms+1, label='— 진짜 최종 순이익 (₩)',
                  path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
        ax12.axhline(y=0, color='white', linestyle='-', linewidth=0.8, alpha=0.5)
        ax12.set_ylabel('금액 (원)', color='white', fontsize=fs_label)
        ax12.tick_params(axis='y', labelcolor='white', labelsize=fs_tick)
        for i, v in enumerate(net_profit):
            if v == 0: continue
            offset_y = -14 if i % 2 == 0 else 10
            ann_color = '#00E5FF' if v >= 0 else '#FF4444'
            ax12.annotate(self._fmt_val(v, 'won'), (df['date_s'].iloc[i], v), 
                           xytext=(0, offset_y), textcoords="offset points", ha='center', color=ann_color, 
                           weight='bold', fontsize=fs_ann-0.5, path_effects=pe)
        ax12.legend(loc='upper left', fontsize=fs_leg, facecolor='#1A1A2E', edgecolor='#333', labelcolor='white', framealpha=0.8)

        # ─── 모든 차트에 메모 수직선 표시 ───
        date_labels = df['date_s'].tolist()
        all_axes = [ax1, ax2, ax3, ax4, ax5, ax6, ax7, ax8, ax9, ax11, ax12]
        try:
            self._draw_memo_vlines(all_axes, date_labels, pe, fontsize=7)
        except Exception:
            pass

        # bottom 여백을 늘려 6행(11번, 12번 차트)의 라벨 잘림 완전 차단
        fig.subplots_adjust(left=0.06, right=0.94, top=0.97, bottom=0.05, hspace=0.35, wspace=0.35)
        canvas = FigureCanvasTkAgg(fig, master=master); canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        fig.dates_list = date_labels
        self._add_hover_tooltip(fig, canvas)
    def _add_hover_tooltip(self, fig, canvas):
        """모든 서브플롯에 마우스 호버 툴팁을 추가 (메모가 있는 날짜만 1번 그림 스타일로 표시)"""
        annots = {}
        for ax in fig.get_axes():
            annot = ax.annotate("", xy=(0, 0), xytext=(20, 20),
                               textcoords="offset points",
                               bbox=dict(boxstyle="round,pad=0.6", fc="white", ec="#C2185B", lw=3, alpha=1.0),
                               fontsize=11, color="black", fontfamily="Malgun Gothic", fontweight="bold",
                               arrowprops=dict(arrowstyle="->", color="#C2185B", lw=2),
                               zorder=999)
            annot.set_visible(False)
            annots[ax] = annot

        def _get_clean_label(chk_ax, bar, lbl, is_horiz):
            # 개발자가 주입한 명시적 커스텀 라벨이 있으면 최우선 반환
            if hasattr(bar, 'custom_label') and bar.custom_label:
                return bar.custom_label
                
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

        canvas._last_hover_state = (None, None)

        def on_hover(event):
            vis_changed = False
            in_ax = event.inaxes
            x_val = event.xdata
            idx = int(round(x_val)) if (in_ax is not None and x_val is not None) else None
            
            # 렌더링 지연 제거: 마우스 위치 및 인덱스가 이전과 같으면 즉시 리턴
            if canvas._last_hover_state == (in_ax, idx):
                return
            canvas._last_hover_state = (in_ax, idx)
            
            if in_ax is None or idx is None:
                for annot in annots.values():
                    if annot.get_visible():
                        annot.set_visible(False)
                        vis_changed = True
                if vis_changed:
                    canvas.draw_idle()
                return

            ax = in_ax
            
            # twin axes 등을 포함하여 마우스가 위치한 축과 X축을 공유하는 모든 axes 수집
            all_axes = [ax]
            for other_ax in fig.get_axes():
                if other_ax is not ax:
                    try:
                        if (abs(other_ax.bbox.x0 - ax.bbox.x0) < 5 and 
                            abs(other_ax.bbox.y0 - ax.bbox.y0) < 5):
                            all_axes.append(other_ax)
                    except:
                        pass
            
            # fig에 저장된 dates_list(마스터 날짜 리스트)가 있으면 최우선 적용
            dates_list = getattr(fig, 'dates_list', None)
            if dates_list and 0 <= idx < len(dates_list):
                tick_val = dates_list[idx]
            else:
                # X축 틱 라벨 목록 가져오기
                xticklabels = [t.get_text() for t in ax.get_xticklabels() if t.get_text()]
                if not xticklabels:
                    # 틱 라벨이 없는 경우, 선 데이터의 xdata 개수로 차선책 판단
                    for chk_ax in all_axes:
                        for line in chk_ax.get_lines():
                            xdata = line.get_xdata()
                            if len(xdata) > 0:
                                xticklabels = [str(x) for x in xdata]
                                break
                        if xticklabels: break
                
                # 인덱스가 범위를 벗어나면 툴팁 숨김
                if not xticklabels or not (0 <= idx < len(xticklabels)):
                    for annot in annots.values():
                        if annot.get_visible():
                            annot.set_visible(False)
                            vis_changed = True
                    if vis_changed:
                        canvas.draw_idle()
                    return
                    
                tick_val = xticklabels[idx]
            
            # 해당 날짜의 메모 수집
            day_memos = []
            try:
                norm_date = tick_val.strip().split('(')[0].replace('/', '.')
                day_memos = [m for m in self.memos if self._memo_date_to_mmdd(m['date']) == norm_date]
            except Exception as memo_err:
                pass
                
            # 메모가 존재하지 않는 날짜는 툴팁을 띄우지 않고 감춤
            if not day_memos:
                for annot in annots.values():
                    if annot.get_visible():
                        annot.set_visible(False)
                        vis_changed = True
                if vis_changed:
                    canvas.draw_idle()
                return
            
            # X축 인덱스 idx에 해당하는 모든 데이터 값 수집
            lines_text = []
            seen_labels = set()
            
            for chk_ax in all_axes:
                # 1) 막대 그래프에서 idx번째 값 추출
                for container in chk_ax.containers:
                    is_horiz = hasattr(container, 'orientation') and container.orientation == 'horizontal'
                    raw_lbl = container.get_label() if hasattr(container, 'get_label') else ''
                    
                    if not is_horiz:
                        if 0 <= idx < len(container):
                            bar = container[idx]
                            val = bar.custom_val if hasattr(bar, 'custom_val') else bar.get_height()
                            lbl = _get_clean_label(chk_ax, bar, raw_lbl, is_horiz)
                            if lbl and lbl not in seen_labels:
                                seen_labels.add(lbl)
                                lines_text.append(_format_val(lbl, val))
                                
                # 2) 선 그래프에서 idx번째 값 추출
                for line in chk_ax.get_lines():
                    xdata = line.get_xdata()
                    ydata = line.get_ydata()
                    if len(xdata) == 0 or len(ydata) == 0:
                        continue
                    lbl = line.get_label() if line.get_label() else ''
                    lbl = lbl.replace('— ', '').strip()
                    if lbl.startswith('_') or not lbl or lbl == '메모 기록':
                        continue
                        
                    if 0 <= idx < len(ydata):
                        val = ydata[idx]
                        if lbl not in seen_labels:
                            seen_labels.add(lbl)
                            lines_text.append(_format_val(lbl, val))
            
            txt_parts = []
            if lines_text:
                txt_parts.extend(lines_text)
                txt_parts.append("")  # 지표와 메모 구분선
                
            for m in day_memos:
                d_key = self._parse_memo_date_to_key(m['date'])
                txt_parts.append(d_key)
                txt_parts.append(m['memo'])
                txt_parts.append("")
                
            text = "\n".join(txt_parts[:-1])
            
            # 툴팁 텍스트 조립 및 표시
            if text:
                annot = annots[ax]
                y_anchor = event.ydata if event.ydata is not None else 0
                
                # 좌표나 텍스트가 바뀐 경우에만 갱신
                if annot.xy != (idx, y_anchor) or annot.get_text() != text or not annot.get_visible():
                    annot.xy = (idx, y_anchor)
                    annot.set_text(text)
                    annot.set_visible(True)
                    vis_changed = True
                    
                # 다른 축들의 툴팁은 숨김
                for other_ax, other_annot in annots.items():
                    if other_ax is not ax and other_annot.get_visible():
                        other_annot.set_visible(False)
                        vis_changed = True
            else:
                for annot in annots.values():
                    if annot.get_visible():
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
        """여러 서브플롯에 메모 날짜 세로 점선과 요약 텍스트 및 노란색 별마커 표시"""
        if not self.memos:
            return
        
        memo_colors = ['#FFD700', '#FF6B6B', '#69DB7C', '#74C0FC', '#DA77F2']
        color_idx = 0
        
        sorted_memos = sorted(self.memos, key=lambda m: self._parse_memo_date_to_key(m['date']))
        seen_mmdd_counts = {}
        
        for m in sorted_memos:
            memo_date = m['date']
            memo_text = m['memo']
            
            mmdd = self._memo_date_to_mmdd(memo_date)
            if mmdd is None or mmdd not in date_labels:
                continue
            
            x_pos = date_labels.index(mmdd)
            color = memo_colors[color_idx % len(memo_colors)]
            color_idx += 1
            
            mmdd_count = seen_mmdd_counts.get(mmdd, 0)
            seen_mmdd_counts[mmdd] = mmdd_count + 1
            
            if mmdd_count == 0:
                ha_val = 'right'
                summary = memo_text
            elif mmdd_count == 1:
                ha_val = 'left'
                summary = memo_text
            else:
                padding_spaces = "   " * (mmdd_count // 2)
                if mmdd_count % 2 == 0:
                    ha_val = 'right'
                    summary = memo_text + padding_spaces
                else:
                    ha_val = 'left'
                    summary = padding_spaces + memo_text
            
            for ax in axes:
                # 💡 범주형 x축 상에서 점선이 누락되는 현상을 완벽 차단하기 위해 정수 인덱스 대신 문자열(mmdd)을 직접 x로 지정
                ax.axvline(x=mmdd, color=color, linewidth=1.2, linestyle=':', alpha=0.7, zorder=5)
                ylim = ax.get_ylim()
                y_pos = ylim[1] * 0.92
                # 텍스트 출력 위치 또한 범주형 눈금 명칭(mmdd)을 기준으로 지정하여 정밀 일치시킴
                # 글꼴 크기를 기존 fontsize보다 1 줄여서 전체 표시에 유리하도록 함
                ax.text(mmdd, y_pos, summary, rotation=90, va='top', ha=ha_val,
                       color=color, fontsize=max(6, fontsize-1), weight='bold', alpha=0.85,
                       path_effects=pe)
                
                # --- 노란색 별마커(★) 그리기 추가 ---
                target_axes = [ax]
                fig_obj = ax.get_figure()
                if fig_obj:
                    for other_ax in fig_obj.get_axes():
                        if other_ax is not ax:
                            try:
                                if (abs(other_ax.bbox.x0 - ax.bbox.x0) < 5 and 
                                    abs(other_ax.bbox.y0 - ax.bbox.y0) < 5):
                                    target_axes.append(other_ax)
                            except:
                                pass
                
                y_val = None
                scatter_ax = ax
                
                # 1) ROAS, 매출, 광고비 비중 등 핵심 지표 선을 먼저 검색
                for tax in target_axes:
                    for line in tax.get_lines():
                        lbl = line.get_label() if line.get_label() else ''
                        if lbl == '메모 기록' or '안전선' in lbl or '경계선' in lbl or '기준선' in lbl or '점선' in lbl or lbl.startswith('_'):
                            continue
                        xdata = line.get_xdata()
                        ydata = line.get_ydata()
                        if len(xdata) > 0 and len(ydata) > 0:
                            if 0 <= x_pos < len(ydata):
                                val = ydata[x_pos]
                                if pd.notna(val) and np.isfinite(val):
                                    if any(k in lbl for k in ['ROAS', '매출', '순이익', '광고비 비중', 'CTR', 'CVR', 'CPC']):
                                        y_val = val
                                        scatter_ax = tax
                                        break
                    if y_val is not None:
                        break
                
                # 2) 매칭되는 선을 못 찾은 경우 임의의 유효한 선 사용
                if y_val is None:
                    for tax in target_axes:
                        for line in tax.get_lines():
                            lbl = line.get_label() if line.get_label() else ''
                            if lbl == '메모 기록' or '안전선' in lbl or '경계선' in lbl or '기준선' in lbl or '점선' in lbl or lbl.startswith('_'):
                                continue
                            xdata = line.get_xdata()
                            ydata = line.get_ydata()
                            if len(xdata) > 0 and len(ydata) > 0:
                                if 0 <= x_pos < len(ydata):
                                    val = ydata[x_pos]
                                    if pd.notna(val) and np.isfinite(val):
                                        y_val = val
                                        scatter_ax = tax
                                        break
                        if y_val is not None:
                            break
                            
                # 3) 선이 아예 없다면 막대 차트 확인
                if y_val is None:
                    for tax in target_axes:
                        for container in tax.containers:
                            if 0 <= x_pos < len(container):
                                bar = container[x_pos]
                                if hasattr(bar, 'get_height'):
                                    y_val = bar.get_height()
                                    scatter_ax = tax
                                    break
                        if y_val is not None:
                            break
                            
                if y_val is not None:
                    # zorder를 12로 높게 잡아 선 위에 확실하게 띄움
                    scatter_ax.scatter(mmdd, y_val, color='#FBBF24', marker='*', s=180, edgecolor='black', 
                                       linewidth=1, zorder=12, label='_nolegend_')


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
        p_bars = ax.bar(['순수익'], [profit], color=p_color, width=0.5, alpha=0.8)
        
        # 막대 위에 상시 값 표시 레이블 추가 및 호버용 커스텀 라벨 주입
        for i, bar in enumerate(bars):
            bar.custom_label = cats[i]
            height = bar.get_height()
            va_dir = 'bottom' if height >= 0 else 'top'
            offset_y = 5 if height >= 0 else -15
            txt = f"{int(height):,}원"
            ax.text(bar.get_x() + bar.get_width()/2., height + offset_y, txt,
                    ha='center', va=va_dir, color='white', weight='bold', fontsize=9, path_effects=pe)
                    
        for bar in p_bars:
            bar.custom_label = '순수익'
            height = bar.get_height()
            va_dir = 'bottom' if height >= 0 else 'top'
            offset_y = 5 if height >= 0 else -15
            txt = f"{int(height):,}원"
            # 순수익 값의 긍정/부정에 맞는 예쁜 네온 그린/레드 컬러 부여
            text_color = '#34D399' if height >= 0 else '#F87171'
            ax.text(bar.get_x() + bar.get_width()/2., height + offset_y, txt,
                    ha='center', va=va_dir, color=text_color, weight='bold', fontsize=9, path_effects=pe)
        
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

    def _render_dash_performance_trend(self, df, master):
        """📈 대시보드 메인 성과 그래프: 집행 광고비 vs 광고 전환 매출 (이중 Y축)"""
        plt.rcParams['font.family'] = 'Malgun Gothic'
        
        # 가로로 긴 비율로 피겨 설정
        fig = Figure(figsize=(13, 3.8), dpi=95)
        fig.patch.set_facecolor('#0B0B1A')
        
        ax1 = fig.add_subplot(111)
        ax1.set_facecolor('#0B0B1A')
        
        # 타이틀 설정
        ax1.set_title("성과 그래프", color='white', pad=25, loc='left',
                     fontdict={'size': 14, 'weight': 'bold', 'family': 'Malgun Gothic'})
        
        dates = df['date_s'].tolist()
        spend = df['spend'].tolist()
        sales = df['sales'].tolist()
        
        # 1. 좌측 Y축: 집행 광고비 (파란색)
        color_spend = '#3B82F6' # 밝은 파란색
        ax1.plot(dates, spend, color=color_spend, marker='s', markersize=5, linewidth=2.5, 
                 label='집행 광고비', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
        ax1.set_ylabel('집행 광고비 (원)', color='white', fontsize=10, weight='bold')
        ax1.tick_params(axis='y', labelcolor=color_spend, labelsize=9)
        
        # 천원 단위(천) 포맷터
        def format_y_thousand(val, pos):
            if val == 0: return '0'
            return f"{int(val/1000)}천"
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(format_y_thousand))
        
        # 2. 우측 Y축: 광고 전환 매출 (초록색)
        ax2 = ax1.twinx()
        color_sales = '#10B981' # 밝은 초록색
        ax2.plot(dates, sales, color=color_sales, marker='s', markersize=5, linewidth=2.5,
                 label='광고 전환 매출', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
        ax2.set_ylabel('광고 전환 매출 (원)', color='white', fontsize=10, weight='bold')
        ax2.tick_params(axis='y', labelcolor=color_sales, labelsize=9)
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(format_y_thousand))
        
        # X축 눈금 설정
        ax1.tick_params(axis='x', labelcolor='#94A3B8', labelsize=9)
        ax1.grid(True, axis='y', color='#1F2937', linestyle='--', alpha=0.4)
        
        # 테두리 색상 설정
        for sp in ax1.spines.values(): sp.set_color('#1F2937')
        for sp in ax2.spines.values(): sp.set_color('#1F2937')
        
        # 범례 표시
        h1, l1 = ax1.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        ax1.legend(h1+h2, l1+l2, loc='upper right', fontsize=9, 
                   facecolor='#1A1A2E', edgecolor='#333', labelcolor='white', framealpha=0.8)
        
        # ─── 메모 수직선 표시 ───
        try:
            pe = [path_effects.withStroke(linewidth=2, foreground='black')]
            self._draw_memo_vlines([ax1], dates, pe, fontsize=8)
        except Exception as memo_err:
            pass
            
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=master)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
        # 툴팁 활성화
        fig.dates_list = dates
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

    def _render_dashboard_pie(self, br_df, master):
        plt.rcParams['font.family'] = 'Malgun Gothic'
        plt.rcParams['axes.unicode_minus'] = False
        pe = [path_effects.withStroke(linewidth=3, foreground='black')]
        
        fig = Figure(figsize=(6.5, 4.5), dpi=95); ax = fig.add_subplot(111)
        fig.patch.set_facecolor('#0B0B1A'); ax.set_facecolor('#0B0B1A')
        ax.set_title("노출 영역별 상세 성과", color='white', pad=40, loc='center',
                     fontdict={'size': 16, 'weight': 'bold', 'family': 'Malgun Gothic'})
        ax.text(0.5, 1.01, '광고비(막대) 대비 클릭수와 주문수(선) 효율을 확인하세요',
               transform=ax.transAxes, ha='center', va='bottom', color='#A0AEC0', fontsize=11, style='italic')
        
        if not br_df.empty:
            # 3대 핵심 대표 영역 정의 (데이터가 없더라도 고정 표출)
            target_regions = ['검색 영역', '비검색 영역', '오디언스 플러스(외부 채널) - Product Ad']
            
            # 영역별 성과를 담을 다차원 딕셔너리 초기화
            s_dict = {reg: {'spend': 0.0, 'click': 0.0, 'orders': 0.0} for reg in target_regions}
            
            # 그룹바이 집계
            raw_s = br_df.groupby('region').agg({'spend': 'sum', 'click': 'sum', 'orders': 'sum'})
            
            for r_name, row in raw_s.iterrows():
                r_name_str = str(r_name)
                matched = False
                
                # 안전하고 정교한 영역 매칭 수행 (비검색 영역이 검색 영역에 합산되는 버그 차단)
                if '비검색' in r_name_str:
                    s_dict['비검색 영역']['spend'] += row['spend']
                    s_dict['비검색 영역']['click'] += row['click']
                    s_dict['비검색 영역']['orders'] += row['orders']
                    matched = True
                elif '검색' in r_name_str:
                    s_dict['검색 영역']['spend'] += row['spend']
                    s_dict['검색 영역']['click'] += row['click']
                    s_dict['검색 영역']['orders'] += row['orders']
                    matched = True
                elif '오디언스' in r_name_str or '외부 채널' in r_name_str or '오피니언' in r_name_str:
                    s_dict['오디언스 플러스(외부 채널) - Product Ad']['spend'] += row['spend']
                    s_dict['오디언스 플러스(외부 채널) - Product Ad']['click'] += row['click']
                    s_dict['오디언스 플러스(외부 채널) - Product Ad']['orders'] += row['orders']
                    matched = True
                
                if not matched:
                    # 매칭되지 않은 기타 지면 예외처리
                    s_dict[r_name_str] = {
                        'spend': row['spend'],
                        'click': row['click'],
                        'orders': row['orders']
                    }
            
            # DataFrame으로 변환
            s_df = pd.DataFrame(s_dict).T
            
            # 라벨 압축 매핑
            labels = []
            for name in s_df.index:
                n_str = str(name)
                if '오디언스' in n_str or '외부 채널' in n_str or '오피니언' in n_str:
                    labels.append('오피니언 영역')
                elif len(n_str) > 6:
                    labels.append(n_str[:6] + '..')
                else:
                    labels.append(n_str)
            
            # 1. 왼쪽 Y축: 광고비 막대 그래프
            colors = ['#EC4899', '#8B5CF6', '#3B82F6', '#F59E0B', '#10B981']
            bars = ax.bar(labels, s_df['spend'].values, color=colors[:len(s_df)], width=0.4, edgecolor='none', alpha=0.7)
            
            # 막대에 값 속성 할당 (호버 툴팁용)
            for bar, val in zip(bars, s_df['spend'].values):
                bar.custom_val = val
                
            ax.set_ylabel('광고비 (원)', color='#EC4899', size=9, weight='bold', fontfamily='Malgun Gothic')
            ax.tick_params(axis='y', labelcolor='#EC4899', labelsize=8)
            ax.set_ylim(0, max(s_df['spend'].max() * 1.25, 10000))
            
            # 2. 오른쪽 Y축: 클릭수 및 주문수 선 그래프 (이중 축 생성)
            ax2 = ax.twinx()
            
            # 클릭수 선그래프 (파란색 계열)
            line_click = ax2.plot(labels, s_df['click'].values, color='#3B82F6', marker='o', linewidth=2, markersize=5,
                                  label='— 클릭수', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
            
            # 주문수 선그래프 (초록색 계열)
            line_orders = ax2.plot(labels, s_df['orders'].values, color='#10B981', marker='s', linewidth=2, markersize=5,
                                   label='— 주문수', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
            
            ax2.set_ylabel('클릭수(회) / 주문수(건)', color='white', size=9, weight='bold', fontfamily='Malgun Gothic')
            ax2.tick_params(axis='y', labelcolor='white', labelsize=8)
            ax2.set_ylim(0, max(s_df['click'].max() * 1.3, 10))
            
            # 선그래프의 데이터 포인트 위에 값 텍스트 애노테이션
            for i in range(len(s_df)):
                # 클릭수 텍스트 표시
                c_val = s_df['click'].iloc[i]
                ax2.annotate(f"{int(c_val)}회", (i, c_val), xytext=(-5, 8), textcoords="offset points",
                             color='#3B82F6', weight='bold', fontsize=8, path_effects=pe, ha='center')
                
                # 주문수 텍스트 표시
                o_val = s_df['orders'].iloc[i]
                ax2.annotate(f"{int(o_val)}건", (i, o_val), xytext=(5, -12), textcoords="offset points",
                             color='#10B981', weight='bold', fontsize=8, path_effects=pe, ha='center')
            
            # 범례 통합 표시
            import matplotlib.patches as mpatches
            patch_spend = mpatches.Patch(color='#EC4899', alpha=0.7, label='■ 광고비')
            
            h1 = [patch_spend]
            h2, l2 = ax2.get_legend_handles_labels()
            ax.legend(h1 + h2, ['■ 광고비'] + l2, loc='upper right', fontsize=8,
                      facecolor='#1A1A2E', edgecolor='#333', labelcolor='white', framealpha=0.8)
            
            ax.tick_params(axis='x', labelcolor='white', labelsize=10, rotation=0)
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
            try:
                with open("ad_memos.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        # Convert old dict format to new list of dicts format
                        memos_list = []
                        for k, v in data.items():
                            memos_list.append({
                                "id": k,
                                "date": k,
                                "memo": v
                            })
                        return memos_list
                    elif isinstance(data, list):
                        return data
            except Exception as e:
                print(f"Error loading memos: {e}")
        return []

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
        self.tabview.set("⚙️ 키워드/입찰")
        self.sub_mgmt_selector.set("🔍 키워드 분석")
        self._on_mgmt_sub_selected("🔍 키워드 분석")
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

    def _setup_real_price_tab(self):
        self.real_price_scroll = ctk.CTkScrollableFrame(self.tab_real_price, fg_color="#0B0B1A")
        self.real_price_scroll.pack(fill="both", expand=True)

        # 1. 상단: 실제판매가 입력 영역
        self.real_input_frame = ctk.CTkFrame(self.real_price_scroll, fg_color="#1A1A2E", corner_radius=12)
        self.real_input_frame.pack(fill="x", padx=15, pady=(15, 5))
        
        ctk.CTkLabel(self.real_input_frame, text="🏷️ 실제판매가 입력:", font=("Malgun Gothic", 16, "bold"), text_color="#60A5FA").pack(side="left", padx=(25, 10), pady=18)
        
        self.real_price_var = tk.StringVar(value="37,500")
        self.real_price_entry = ctk.CTkEntry(self.real_input_frame, textvariable=self.real_price_var, width=150, height=38, font=("Malgun Gothic", 14, "bold"))
        self.real_price_entry.pack(side="left", padx=10, pady=18)
        self.real_price_entry.bind("<KeyRelease>", self._format_real_price_input)
        self.real_price_entry.bind("<Return>", lambda e: self._update_real_price_tab())
        
        ctk.CTkLabel(self.real_input_frame, text="원", font=("Malgun Gothic", 14, "bold"), text_color="white").pack(side="left", padx=(0, 30), pady=18)
        
        ctk.CTkLabel(self.real_input_frame, text="⚙️ 보정 기준:", font=("Malgun Gothic", 14, "bold"), text_color="#94A3B8").pack(side="left", padx=(10, 5), pady=18)
        
        self.real_calc_base_var = tk.StringVar(value="내 판매가 기준")
        self.real_calc_base_seg = ctk.CTkSegmentedButton(
            self.real_input_frame, 
            values=["쿠팡시스템 기준", "내 판매가 기준"],
            variable=self.real_calc_base_var,
            font=("Malgun Gothic", 13, "bold"),
            command=lambda v: self._update_real_price_tab()
        )
        self.real_calc_base_seg.pack(side="left", padx=10, pady=18)
        
        self.real_calc_btn = ctk.CTkButton(
            self.real_input_frame, 
            text="⚡ 계산 반영", 
            command=self._update_real_price_tab,
            fg_color="#2563EB", 
            hover_color="#1D4ED8", 
            width=120, 
            height=38, 
            font=("Malgun Gothic", 13, "bold")
        )
        self.real_calc_btn.pack(side="left", padx=20, pady=18)

        # 2. 중단 1: 주요 지표 카드 영역
        self.real_cards_grid = ctk.CTkFrame(self.real_price_scroll, fg_color="transparent")
        self.real_cards_grid.pack(fill="x", padx=15, pady=8)
        self.real_cards_grid.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        self.real_cards_grid.grid_rowconfigure((0, 1), weight=1)
        
        self.real_metrics_def = [
            ("광고수익률", "ROAS", "%", False),
            ("오늘 누적 광고비", "today_spend", "원", True),
            ("집행 광고비", "spend", "원", True),
            ("광고 전환매출", "sales", "원", False),
            ("전환율", "CVR", "%", True),
            ("클릭률", "CTR", "%", True),
            ("노출수", "imp", "회", True),
            ("클릭수", "click", "회", True),
            ("광고 전환 판매수", "conv_qty", "회", True),
            ("광고 전환 주문수", "orders", "건", True),
            ("전체 매출", "total_sales", "원", False),
            ("전체 판매수", "total_qty", "개", True)
        ]
        
        self.real_price_cards = {}
        for i, (t, k, u, is_fixed) in enumerate(self.real_metrics_def):
            r, c = divmod(i, 6)
            card = ctk.CTkFrame(
                self.real_cards_grid,
                fg_color="#1E293B",
                border_width=2,
                border_color="#3B82F6",
                corner_radius=12
            )
            card.grid(row=r, column=c, padx=6, pady=6, sticky="nsew")
            
            if "광고비" in t: color = "#FBBF24"
            elif "매출" in t: color = "#34D399"
            elif t in ["노출수", "클릭수", "광고 전환 판매수", "광고 전환 주문수", "전체 판매수"]: color = "#60A5FA"
            else: color = "#FB923C"
            
            ctk.CTkLabel(card, text=t, font=("Malgun Gothic", 13, "bold"), text_color="#E2E8F0").pack(pady=(10, 5))
            
            lbl_coupang = ctk.CTkLabel(card, text="-", font=("Malgun Gothic", 14, "bold"), text_color="#AAAAAA")
            lbl_coupang.pack(pady=2)
            
            lbl_real = ctk.CTkLabel(card, text="-", font=("Malgun Gothic", 16, "bold"), text_color=color)
            lbl_real.pack(pady=2)
            
            lbl_diff = ctk.CTkLabel(card, text="-", font=("Malgun Gothic", 12, "bold"), text_color="#E2E8F0")
            lbl_diff.pack(pady=(2, 10))
            
            self.real_price_cards[k] = {
                'title': t,
                'unit': u,
                'is_fixed': is_fixed,
                'lbl_coupang': lbl_coupang,
                'lbl_real': lbl_real,
                'lbl_diff': lbl_diff
            }

        self.real_chart_container = ctk.CTkFrame(self.real_price_scroll, fg_color="#0B0B1A", corner_radius=12, border_width=1, border_color="#10B981")
        self.real_chart_container.pack(fill="both", expand=True, padx=15, pady=8)

        # 4. 하단: 가로형 비교표 영역
        self.real_table_frame = ctk.CTkFrame(self.real_price_scroll, fg_color="#1A1A2E", corner_radius=12)
        self.real_table_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(self.real_table_frame, text="📋 쿠팡시스템 기준 vs 내 판매가 기준 상세 대조표 (가로형)", font=("Malgun Gothic", 16, "bold"), text_color="#60A5FA").pack(pady=(15, 10), padx=25, anchor="w")
        
        # 가로형 컬럼 정의
        self.real_table_cols = (
            "구분", "광고 전환매출", "광고수익률", "전환율", "클릭률", 
            "노출수", "클릭수", "광고 전환 판매수", "광고 전환 주문수", "전체 매출", "전체 판매수"
        )
        
        table_container = ctk.CTkFrame(self.real_table_frame, fg_color="transparent")
        table_container.pack(fill="x", padx=15, pady=10)
        
        self.real_table = ttk.Treeview(table_container, columns=self.real_table_cols, show="headings", height=3)
        hsb = ttk.Scrollbar(table_container, orient="horizontal", command=self.real_table.xview)
        self.real_table.configure(xscrollcommand=hsb.set)
        
        self.real_table.pack(fill="x", expand=True)
        hsb.pack(fill="x")
        
        # 컬럼 속성 및 너비 세팅
        for col in self.real_table_cols:
            self.real_table.heading(col, text=col)
            width = 160 if col == "구분" or "매출" in col else 115
            self.real_table.column(col, anchor="center" if col == "구분" else "e", width=width)

    def _format_real_price_input(self, event):
        val = self.real_price_var.get()
        val_clean = re.sub(r'[^\d]', '', val)
        if val_clean:
            formatted = f"{int(val_clean):,}"
            self.real_price_var.set(formatted)
            self.real_price_entry.icursor(len(formatted))

    def _update_real_price_tab(self):
        if self.current_data is None:
            return
            
        try:
            p_val = float(re.sub(r'[^\d]', '', self.real_price_var.get()))
        except:
            p_val = 0.0
            
        overall = self.analyzer.get_overall_summary()
        if not overall:
            return
            
        sales_coupang = overall.get('sales', 0)
        # 연산은 항상 '주문수 (건수)' 기준으로 고정
        sales_real = p_val * overall.get('orders', 0)
            
        spend = overall.get('spend', 0)
        roas_coupang = overall.get('ROAS', 0)
        roas_real = (sales_real / spend * 100) if spend > 0 else 0
        
        total_qty = overall.get('total_qty', 0)
        total_sales_real = p_val * total_qty
        
        for k, info in self.real_price_cards.items():
            t = info['title']
            u = info['unit']
            is_fixed = info['is_fixed']
            
            if k == "ROAS":
                v_coupang = roas_coupang
                v_real = roas_real
            elif k == "today_spend":
                v_coupang = overall.get('spend', 0)
                v_real = v_coupang
            elif k == "spend":
                v_coupang = overall.get('spend', 0)
                v_real = v_coupang
            elif k == "sales":
                v_coupang = sales_coupang
                v_real = sales_real
            elif k == "CVR":
                v_coupang = overall.get('CVR', 0)
                v_real = v_coupang
            elif k == "CTR":
                v_coupang = overall.get('CTR', 0)
                v_real = v_coupang
            elif k == "imp":
                v_coupang = overall.get('imp', 0)
                v_real = v_coupang
            elif k == "click":
                v_coupang = overall.get('click', 0)
                v_real = v_coupang
            elif k == "conv_qty":
                v_coupang = overall.get('conv_qty', 0)
                v_real = v_coupang
            elif k == "orders":
                v_coupang = overall.get('orders', 0)
                v_real = v_coupang
            elif k == "total_sales":
                v_coupang = sales_coupang
                v_real = total_sales_real
            elif k == "total_qty":
                v_coupang = total_qty
                v_real = v_coupang
            
            if u == "원":
                txt_coupang = f"{int(v_coupang):,} 원"
                txt_real = f"{int(v_real):,} 원"
            elif u == "회" or u == "건" or u == "개":
                txt_coupang = f"{int(v_coupang):,} {u}"
                txt_real = f"{int(v_real):,} {u}"
            else:
                txt_coupang = f"{v_coupang:.2f} {u}"
                txt_real = f"{v_real:.2f} {u}"
                
            info['lbl_coupang'].configure(text=f"쿠팡시스템 기준: {txt_coupang}")
            
            if is_fixed:
                info['lbl_real'].configure(text="동일값")
                info['lbl_diff'].configure(text="보정 영향 없음", text_color="#AAAAAA")
            else:
                info['lbl_real'].configure(text=f"내 판매가 기준: {txt_real}")
                diff = v_real - v_coupang
                if k in ["ROAS", "CVR", "CTR"]:
                    sign = "+" if diff >= 0 else ""
                    info['lbl_diff'].configure(text=f"차이: {sign}{diff:.2f}%p", text_color="#10B981" if diff >= 0 else "#EF4444")
                else:
                    sign = "+" if diff >= 0 else ""
                    pct = (diff / v_coupang * 100) if v_coupang > 0 else 0
                    info['lbl_diff'].configure(text=f"차이: {sign}{int(diff):,}원 ({sign}{pct:.1f}%)", text_color="#10B981" if diff >= 0 else "#EF4444")
        
        for item in self.real_table.get_children():
            self.real_table.delete(item)
            
        row_coupang = ["쿠팡시스템 기준"]
        row_real = ["내 판매가 기준"]
        row_diff = ["차액 (이익 변동)"]
        
        row_coupang.append(f"{int(sales_coupang):,}원")
        row_real.append(f"{int(sales_real):,}원")
        diff_sales = sales_real - sales_coupang
        pct_sales = (diff_sales / sales_coupang * 100) if sales_coupang > 0 else 0
        row_diff.append(f"+{int(diff_sales):,}원 (+{pct_sales:.1f}%)" if diff_sales >= 0 else f"{int(diff_sales):,}원 ({pct_sales:.1f}%)")
        
        row_coupang.append(f"{roas_coupang:.2f}%")
        row_real.append(f"{roas_real:.2f}%")
        diff_roas = roas_real - roas_coupang
        row_diff.append(f"+{diff_roas:.2f}%p" if diff_roas >= 0 else f"{diff_roas:.2f}%p")
        
        row_coupang.append(f"{overall.get('CVR', 0):.2f}%")
        row_real.append("동일값")
        row_diff.append("0%p")
        
        row_coupang.append(f"{overall.get('CTR', 0):.2f}%")
        row_real.append("동일값")
        row_diff.append("0%p")
        
        row_coupang.append(f"{int(overall.get('imp', 0)):,}회")
        row_real.append("동일값")
        row_diff.append("-")
        
        row_coupang.append(f"{int(overall.get('click', 0)):,}회")
        row_real.append("동일값")
        row_diff.append("-")
        
        row_coupang.append(f"{int(overall.get('conv_qty', 0)):,}회")
        row_real.append("동일값")
        row_diff.append("-")
        
        row_coupang.append(f"{int(overall.get('orders', 0)):,}건")
        row_real.append("동일값")
        row_diff.append("-")
        
        row_coupang.append(f"{int(sales_coupang):,}원")
        row_real.append(f"{int(total_sales_real):,}원")
        diff_total_sales = total_sales_real - sales_coupang
        pct_total_sales = (diff_total_sales / sales_coupang * 100) if sales_coupang > 0 else 0
        row_diff.append(f"+{int(diff_total_sales):,}원 (+{pct_total_sales:.1f}%)" if diff_total_sales >= 0 else f"{int(diff_total_sales):,}원 ({pct_total_sales:.1f}%)")
        
        row_coupang.append(f"{int(total_qty):,}개")
        row_real.append("동일값")
        row_diff.append("-")
        
        self.real_table.insert("", "end", values=row_coupang)
        self.real_table.insert("", "end", values=row_real)
        self.real_table.insert("", "end", values=row_diff)
        
        self._draw_real_price_chart()

    def _draw_real_price_chart(self):
        for w in self.real_chart_container.winfo_children():
            w.destroy()
            
        if self.current_data is None:
            ctk.CTkLabel(self.real_chart_container, text="⚠️ 데이터 분석을 먼저 실행해주세요.", text_color="#EF4444", font=("Malgun Gothic", 14, "bold")).pack(pady=100)
            return
            
        pd_data = self.analyzer.get_daily_performance()
        if pd_data['total'].empty:
            ctk.CTkLabel(self.real_chart_container, text="⚠️ 표시할 날짜별 추이 데이터가 없습니다.", text_color="#EF4444", font=("Malgun Gothic", 14, "bold")).pack(pady=100)
            return
            
        df = pd_data['total'].copy()
        
        try:
            p_val = float(re.sub(r'[^\d]', '', self.real_price_var.get()))
        except:
            p_val = 0.0
        
        # 집행광고비와 광고 전환매출 비교로 지표 명칭 고정
        metric_name = "금액"
        metric_unit = "원"
        
        df = df.sort_values('p_date')
        dates = df['date_s'].tolist()
        
        coupang_vals = []
        real_vals = []
        spend_vals = []
        
        for _, r in df.iterrows():
            spend = r.get('spend', 0)
            sales = r.get('sales', 0)
            orders = r.get('orders', 0)
            
            # 연산은 항상 '주문수 (건수)' 기준으로 고정
            s_real = p_val * orders
            
            coupang_vals.append(sales)
            real_vals.append(s_real)
            spend_vals.append(spend)
        
        plt.rcParams['font.family'] = 'Malgun Gothic'
        fig = Figure(figsize=(13, 4.2), dpi=95)
        fig.patch.set_facecolor('#0B0B1A')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#0B0B1A')
        
        ax.set_title("집행광고비 vs 광고전환매출 추이 비교", color='white', pad=25, loc='left',
                     fontdict={'size': 14, 'weight': 'bold', 'family': 'Malgun Gothic'})
                     
        # 3선 플로팅 (집행광고비, 쿠팡시스템 기준 매출, 내 판매가 기준 매출)
        ax.plot(dates, spend_vals, color='#F59E0B', marker='x', markersize=6, linewidth=2, linestyle='--', label='집행광고비')
        ax.plot(dates, coupang_vals, color='#3B82F6', marker='o', markersize=6, linewidth=2.5, label='광고전환매출 (쿠팡시스템)')
        ax.plot(dates, real_vals, color='#10B981', marker='s', markersize=6, linewidth=2.5, label='광고전환매출 (내 판매가)')
            
        ax.set_ylabel(f"{metric_name} ({metric_unit})", color='white', fontsize=10, weight='bold')
        ax.tick_params(axis='y', labelcolor='white', labelsize=9)
        ax.tick_params(axis='x', labelcolor='#94A3B8', labelsize=9)
        ax.grid(True, axis='y', color='#1F2937', linestyle='--', alpha=0.4)
        
        def format_y_thousand(val, pos):
            if val == 0: return '0'
            if abs(val) >= 1000000: return f"{val/1000000:.1f}백만"
            return f"{int(val/1000)}천"
        ax.yaxis.set_major_formatter(plt.FuncFormatter(format_y_thousand))
            
        for sp in ax.spines.values():
            sp.set_color('#1F2937')
            
        ax.legend(loc='upper right', fontsize=9, facecolor='#1A1A2E', edgecolor='#333', labelcolor='white', framealpha=0.8)
        
        try:
            pe = [path_effects.withStroke(linewidth=2, foreground='black')]
            self._draw_memo_vlines([ax], dates, pe, fontsize=8)
        except Exception:
            pass
            
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=self.real_chart_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
        self._add_hover_tooltip_real_price(fig, canvas, dates, coupang_vals, real_vals, spend_vals)

    def _add_hover_tooltip_real_price(self, fig, canvas, dates, coupang_vals, real_vals, spend_vals):
        annots = {}
        for ax in fig.get_axes():
            annot = ax.annotate("", xy=(0, 0), xytext=(20, 20),
                               textcoords="offset points",
                               bbox=dict(boxstyle="round,pad=0.6", fc="white", ec="#C2185B", lw=3, alpha=1.0),
                               fontsize=11, color="black", fontfamily="Malgun Gothic", fontweight="bold",
                               arrowprops=dict(arrowstyle="->", color="#C2185B", lw=2),
                               zorder=999)
            annot.set_visible(False)
            annots[ax] = annot

        canvas._last_hover_state = (None, None)

        def on_hover(event):
            vis_changed = False
            in_ax = event.inaxes
            x_val = event.xdata
            idx = int(round(x_val)) if (in_ax is not None and x_val is not None) else None
            
            # 렌더링 지연 제거: 마우스 위치 및 인덱스가 이전과 같으면 즉시 리턴
            if canvas._last_hover_state == (in_ax, idx):
                return
            canvas._last_hover_state = (in_ax, idx)
            
            if in_ax is None or idx is None:
                for annot in annots.values():
                    if annot.get_visible():
                        annot.set_visible(False)
                        vis_changed = True
                if vis_changed:
                    canvas.draw_idle()
                return

            ax = in_ax
            if not (0 <= idx < len(dates)):
                for annot in annots.values():
                    if annot.get_visible():
                        annot.set_visible(False)
                        vis_changed = True
                if vis_changed:
                    canvas.draw_idle()
                return
                
            tick_val = dates[idx]
            
            # 해당 날짜의 메모 수집
            day_memos = []
            try:
                norm_date = tick_val.strip().split('(')[0].replace('/', '.')
                day_memos = [m for m in self.memos if self._memo_date_to_mmdd(m['date']) == norm_date]
            except Exception:
                pass
                
            # 메모가 없으면 툴팁을 띄우지 않고 숨김
            if not day_memos:
                for annot in annots.values():
                    if annot.get_visible():
                        annot.set_visible(False)
                        vis_changed = True
                if vis_changed:
                    canvas.draw_idle()
                return
            
            v_coupang = coupang_vals[idx]
            v_real = real_vals[idx]
            v_spend = spend_vals[idx]
            
            lines_text = []
            
            def fmt(val):
                return f"{int(val):,}원"
            
            lines_text.append(f"📊 집행광고비: {fmt(v_spend)}")
            lines_text.append(f"📊 광고전환매출 (쿠팡시스템): {fmt(v_coupang)}")
            lines_text.append(f"📊 광고전환매출 (내 판매가): {fmt(v_real)}")
            
            roas_c = (v_coupang / v_spend * 100) if v_spend > 0 else 0
            roas_r = (v_real / v_spend * 100) if v_spend > 0 else 0
            lines_text.append(f"💡 광고수익률 (쿠팡 ROAS): {roas_c:.2f}%")
            lines_text.append(f"💡 광고수익률 (내 판매가 ROAS): {roas_r:.2f}%")
            
            txt_parts = []
            if lines_text:
                txt_parts.extend(lines_text)
                txt_parts.append("")  # 구분선
                
            for m in day_memos:
                d_key = self._parse_memo_date_to_key(m['date'])
                txt_parts.append(d_key)
                txt_parts.append(m['memo'])
                txt_parts.append("")
                
            text = "\n".join(txt_parts[:-1])
            annot = annots[ax]
            
            y_anchor = event.ydata if event.ydata is not None else 0
            
            # 좌표나 텍스트가 바뀐 경우에만 갱신
            if annot.xy != (idx, y_anchor) or annot.get_text() != text or not annot.get_visible():
                annot.xy = (idx, y_anchor)
                annot.set_text(text)
                annot.set_visible(True)
                vis_changed = True
                
            for other_ax, other_annot in annots.items():
                if other_ax is not ax and other_annot.get_visible():
                    other_annot.set_visible(False)
                    vis_changed = True
                    
            if vis_changed:
                canvas.draw_idle()
                
        fig.canvas.mpl_connect("motion_notify_event", on_hover)

if __name__ == "__main__":
    app = AdOptimizerApp()
    app.mainloop()
