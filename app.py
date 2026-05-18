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
        self.tab_memos = self.tabview.add("📝 일별 기록 / 메모")
        self.tab_diagnosis = self.tabview.add("🛡️ AI 전략 나침반")
        
        self._setup_dashboard_tab()
        self._setup_keyword_tab()
        self._setup_management_tab(self.tab_target, "타겟")
        self._setup_management_tab(self.tab_manual, "수동")
        self._setup_management_tab(self.tab_exclude, "제외")
        self._setup_metrics_tab()
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
        for adv in d['advice']:
            card = ctk.CTkFrame(self.advice_container, fg_color="#1A1A2E", corner_radius=15)
            card.pack(fill="x", pady=10)
            ctk.CTkLabel(card, text=adv['subject'], font=("Malgun Gothic", 20, "bold"), text_color="#60A5FA").pack(anchor="w", padx=25, pady=(20, 10))
            ctk.CTkLabel(card, text=f"💡 분석: {adv['meaning']}", font=("Malgun Gothic", 15)).pack(anchor="w", padx=25, pady=5)
            ctk.CTkLabel(card, text=f"📖 전략: {adv['easy_story']}", font=("Malgun Gothic", 14), text_color="#94A3B8").pack(anchor="w", padx=25, pady=5)
            
            sol_frame = ctk.CTkFrame(card, fg_color="#0B0B1A", corner_radius=10)
            sol_frame.pack(fill="x", padx=25, pady=(10, 20))
            for s in adv['solution']:
                ctk.CTkLabel(sol_frame, text=f"✔️ {s}", font=("Malgun Gothic", 14)).pack(anchor="w", padx=15, pady=5)

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
            
            # 2. 성과 추이 탭 전용 대형 차트들 (2×2)
            try:
                self._render_large_trend_chart(df, self.metrics_scroll)
            except Exception as e:
                import traceback; traceback.print_exc()
                ctk.CTkLabel(self.metrics_scroll, text=f"⚠️ 추이 차트 오류: {e}", text_color="#EF4444",
                            font=("Malgun Gothic", 11)).pack(pady=20)

    def _render_large_trend_chart(self, df, master):
        plt.rcParams['font.family'] = 'Malgun Gothic'
        pe = [path_effects.withStroke(linewidth=2, foreground='black')]
        n = len(df)
        step = 3 if n > 10 else 2 if n > 5 else 1
        fs_title = 15; fs_guide = 10; fs_ann = 8; fs_label = 10; fs_tick = 8; fs_leg = 9
        ms = 4; lw = 2
        
        fig = Figure(figsize=(18, 18), dpi=100)
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
        
        # ─── 1. 매출(막대) + ROAS(선) [좌상] ───
        ax1 = fig.add_subplot(321); setup_ax(ax1)
        ax1.set_title("매출 및 ROAS 추이", color='white', pad=30, loc='center', fontdict={'size': fs_title, 'weight': 'bold'})
        ax1.text(0.5, 1.01, '매출 상승 시 ROAS도 유지되는지 확인', transform=ax1.transAxes,
                ha='center', va='bottom', color='#A0AEC0', fontsize=fs_guide, style='italic')
        ax1.bar(df['date_s'], df['sales'], color='#00E5FF', alpha=0.35, label='■ 매출액')
        ax1.set_ylabel('매출액 (원)', color='#00E5FF', weight='bold', fontsize=fs_label)
        ax1.tick_params(axis='y', labelcolor='#00E5FF', labelsize=fs_tick)
        for i, v in enumerate(df['sales']):
            if i % step != 0 or v == 0: continue
            ax1.annotate(self._fmt_val(v, 'won'), (df['date_s'].iloc[i], v),
                         xytext=(0, 4), textcoords="offset points", ha='center',
                         color='#00E5FF', weight='bold', fontsize=fs_ann, path_effects=pe)
        ax1_2 = ax1.twinx()
        ax1_2.plot(df['date_s'], df['ROAS'], color='#FF00FF', marker='o', markersize=ms, linewidth=lw, 
                   label='— ROAS%', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
        ax1_2.set_ylabel('ROAS (%)', color='#FF00FF', weight='bold', fontsize=fs_label)
        ax1_2.tick_params(axis='y', labelcolor='#FF00FF', labelsize=fs_tick)
        for i, v in enumerate(df['ROAS']):
            if i % step != step - 1 or v == 0: continue
            offset_y = 10 if (i // step) % 2 == 0 else -14
            ax1_2.annotate(f"{v:.0f}%", (df['date_s'].iloc[i], v), 
                           xytext=(0, offset_y), textcoords="offset points", ha='center', color='#FF00FF', 
                           weight='bold', fontsize=fs_ann, path_effects=pe)
        add_legend(ax1, ax1_2)

        # ─── 2. 광고비(막대) + 클릭수(선) [우상] ───
        ax2 = fig.add_subplot(322); setup_ax(ax2)
        ax2.set_title("광고비 및 클릭 효율", color='white', pad=30, loc='center', fontdict={'size': fs_title, 'weight': 'bold'})
        ax2.text(0.5, 1.01, '광고비 대비 클릭수 동반 상승이 핵심', transform=ax2.transAxes,
                ha='center', va='bottom', color='#A0AEC0', fontsize=fs_guide, style='italic')
        ax2.bar(df['date_s'], df['spend'], color='#EF4444', alpha=0.35, label='■ 광고비')
        ax2.set_ylabel('광고비 (원)', color='#EF4444', weight='bold', fontsize=fs_label)
        ax2.tick_params(axis='y', labelcolor='#EF4444', labelsize=fs_tick)
        for i, v in enumerate(df['spend']):
            if i % step != 0 or v == 0: continue
            ax2.annotate(self._fmt_val(v, 'won'), (df['date_s'].iloc[i], v), 
                         xytext=(0, 4), textcoords="offset points", ha='center', 
                         color='#EF4444', weight='bold', fontsize=fs_ann, path_effects=pe)
        ax2_2 = ax2.twinx()
        ax2_2.plot(df['date_s'], df['click'], color='#F59E0B', marker='^', linewidth=lw, markersize=ms,
                   label='— 클릭수', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
        ax2_2.set_ylabel('클릭수 (회)', color='#F59E0B', weight='bold', fontsize=fs_label)
        ax2_2.tick_params(axis='y', labelcolor='#F59E0B', labelsize=fs_tick)
        for i, v in enumerate(df['click']):
            if i % step != step - 1 or v == 0: continue
            offset_y = -14 if (i // step) % 2 == 0 else 10
            ax2_2.annotate(f"{int(v):,}", (df['date_s'].iloc[i], v), 
                           xytext=(0, offset_y), textcoords="offset points", ha='center', 
                           color='#F59E0B', weight='bold', fontsize=fs_ann, path_effects=pe)
        add_legend(ax2, ax2_2)

        # ─── 3. CTR(막대) + CVR(선) [좌하] ───
        ax3 = fig.add_subplot(323); setup_ax(ax3)
        ax3.set_title("CTR 및 CVR 분석", color='white', pad=30, loc='center', fontdict={'size': fs_title, 'weight': 'bold'})
        ax3.text(0.5, 1.01, 'CTR=썸네일 매력도, CVR=구매 전환력', transform=ax3.transAxes,
                ha='center', va='bottom', color='#A0AEC0', fontsize=fs_guide, style='italic')
        ax3.bar(df['date_s'], df['CTR'], color='#10B981', alpha=0.35, label='■ CTR%')
        ax3.set_ylabel('CTR (%)', color='#10B981', weight='bold', fontsize=fs_label)
        ax3.tick_params(axis='y', labelcolor='#10B981', labelsize=fs_tick)
        for i, v in enumerate(df['CTR']):
            if i % step != 0: continue
            ax3.annotate(f"{v:.2f}%", (df['date_s'].iloc[i], v), 
                         xytext=(0, 4), textcoords="offset points", ha='center', 
                         color='#10B981', weight='bold', fontsize=fs_ann, path_effects=pe)
        ax3_2 = ax3.twinx()
        cvr = np.where(df['click'] > 0, (df['orders'] / df['click']) * 100, 0)
        ax3_2.plot(df['date_s'], cvr, color='#6366F1', marker='D', linewidth=lw, markersize=ms,
                   label='— CVR%', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
        ax3_2.set_ylabel('CVR (%)', color='#6366F1', weight='bold', fontsize=fs_label)
        ax3_2.tick_params(axis='y', labelcolor='#6366F1', labelsize=fs_tick)
        for i, v in enumerate(cvr):
            if i % step != step - 1 or v == 0: continue
            offset_y = -14 if (i // step) % 2 == 0 else 10
            ax3_2.annotate(f"{v:.1f}%", (df['date_s'].iloc[i], v), 
                           xytext=(0, offset_y), textcoords="offset points", ha='center', 
                           color='#6366F1', weight='bold', fontsize=fs_ann, path_effects=pe)
        add_legend(ax3, ax3_2)

        # ─── 4. CPC(막대) + CPA(선) [우하] ───
        ax4 = fig.add_subplot(324); setup_ax(ax4)
        ax4.set_title("CPC 및 CPA", color='white', pad=30, loc='center', fontdict={'size': fs_title, 'weight': 'bold'})
        ax4.text(0.5, 1.01, 'CPC와 CPA가 낮을수록 효율적!', transform=ax4.transAxes,
                ha='center', va='bottom', color='#A0AEC0', fontsize=fs_guide, style='italic')
        cpc = np.where(df['click'] > 0, df['spend'] / df['click'], 0)
        ax4.bar(df['date_s'], cpc, color='#EC4899', alpha=0.35, label='■ CPC')
        ax4.set_ylabel('CPC (원)', color='#EC4899', weight='bold', fontsize=fs_label)
        ax4.tick_params(axis='y', labelcolor='#EC4899', labelsize=fs_tick)
        for i, v in enumerate(cpc):
            if i % step != 0 or v == 0: continue
            ax4.annotate(self._fmt_val(v, 'won'), (df['date_s'].iloc[i], v), 
                         xytext=(0, 4), textcoords="offset points", ha='center', 
                         color='#EC4899', weight='bold', fontsize=fs_ann, path_effects=pe)
        ax4_2 = ax4.twinx()
        cpa = np.where(df['orders'] > 0, df['spend'] / df['orders'], 0)
        ax4_2.plot(df['date_s'], cpa, color='#8B5CF6', marker='h', markersize=ms+1, linewidth=lw,
                   label='— CPA', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
        ax4_2.set_ylabel('CPA (원)', color='#8B5CF6', weight='bold', fontsize=fs_label)
        ax4_2.tick_params(axis='y', labelcolor='#8B5CF6', labelsize=fs_tick)
        for i, v in enumerate(cpa):
            if i % step != step - 1 or v == 0: continue
            offset_y = -14 if (i // step) % 2 == 0 else 10
            ax4_2.annotate(self._fmt_val(v, 'won'), (df['date_s'].iloc[i], v), 
                           xytext=(0, offset_y), textcoords="offset points", ha='center', 
                           color='#8B5CF6', weight='bold', fontsize=fs_ann, path_effects=pe)
        add_legend(ax4, ax4_2)

        # ─── 5. 클릭수(막대) + 전환건수(선) [좌하] ───
        ax5 = fig.add_subplot(325); setup_ax(ax5)
        ax5.set_title("클릭수 및 전환건수", color='white', pad=30, loc='center', fontdict={'size': fs_title, 'weight': 'bold'})
        ax5.text(0.5, 1.01, '클릭이 실제 주문으로 이어지는지 확인', transform=ax5.transAxes,
                ha='center', va='bottom', color='#A0AEC0', fontsize=fs_guide, style='italic')
        ax5.bar(df['date_s'], df['click'], color='#F59E0B', alpha=0.35, label='■ 클릭수')
        ax5.set_ylabel('클릭수 (회)', color='#F59E0B', weight='bold', fontsize=fs_label)
        ax5.tick_params(axis='y', labelcolor='#F59E0B', labelsize=fs_tick)
        for i, v in enumerate(df['click']):
            if i % step != 0 or v == 0: continue
            ax5.annotate(f"{int(v):,}", (df['date_s'].iloc[i], v),
                         xytext=(0, 4), textcoords="offset points", ha='center',
                         color='#F59E0B', weight='bold', fontsize=fs_ann, path_effects=pe)
        ax5_2 = ax5.twinx()
        ax5_2.plot(df['date_s'], df['orders'], color='#34D399', marker='s', linewidth=lw, markersize=ms,
                   label='— 전환건수', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
        ax5_2.set_ylabel('전환건수 (건)', color='#34D399', weight='bold', fontsize=fs_label)
        ax5_2.tick_params(axis='y', labelcolor='#34D399', labelsize=fs_tick)
        for i, v in enumerate(df['orders']):
            if i % step != step - 1 or v == 0: continue
            offset_y = -14 if (i // step) % 2 == 0 else 10
            ax5_2.annotate(f"{int(v):,}건", (df['date_s'].iloc[i], v),
                           xytext=(0, offset_y), textcoords="offset points", ha='center',
                           color='#34D399', weight='bold', fontsize=fs_ann, path_effects=pe)
        add_legend(ax5, ax5_2)

        # ─── 6. 노출수(막대) + 전환건수(선) [우하] ───
        ax6 = fig.add_subplot(326); setup_ax(ax6)
        ax6.set_title("노출수 및 전환건수", color='white', pad=30, loc='center', fontdict={'size': fs_title, 'weight': 'bold'})
        ax6.text(0.5, 1.01, '노출이 실제 주문으로 연결되는지 확인', transform=ax6.transAxes,
                ha='center', va='bottom', color='#A0AEC0', fontsize=fs_guide, style='italic')
        ax6.bar(df['date_s'], df['imp'], color='#60A5FA', alpha=0.35, label='■ 노출수')
        ax6.set_ylabel('노출수 (회)', color='#60A5FA', weight='bold', fontsize=fs_label)
        ax6.tick_params(axis='y', labelcolor='#60A5FA', labelsize=fs_tick)
        for i, v in enumerate(df['imp']):
            if i % step != 0 or v == 0: continue
            ax6.annotate(self._fmt_val(v, 'int'), (df['date_s'].iloc[i], v),
                         xytext=(0, 4), textcoords="offset points", ha='center',
                         color='#60A5FA', weight='bold', fontsize=fs_ann, path_effects=pe)
        ax6_2 = ax6.twinx()
        ax6_2.plot(df['date_s'], df['orders'], color='#FB923C', marker='o', linewidth=lw, markersize=ms,
                   label='— 전환건수', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
        ax6_2.set_ylabel('전환건수 (건)', color='#FB923C', weight='bold', fontsize=fs_label)
        ax6_2.tick_params(axis='y', labelcolor='#FB923C', labelsize=fs_tick)
        for i, v in enumerate(df['orders']):
            if i % step != step - 1 or v == 0: continue
            offset_y = -14 if (i // step) % 2 == 0 else 10
            ax6_2.annotate(f"{int(v):,}건", (df['date_s'].iloc[i], v),
                           xytext=(0, offset_y), textcoords="offset points", ha='center',
                           color='#FB923C', weight='bold', fontsize=fs_ann, path_effects=pe)
        add_legend(ax6, ax6_2)

        # ─── 모든 서브플롯에 메모 세로 점선 표시 ───
        all_axes = [ax1, ax2, ax3, ax4, ax5, ax6]
        self._draw_memo_vlines(all_axes, df['date_s'].tolist(), pe, fs_ann)

        fig.subplots_adjust(left=0.06, right=0.94, top=0.94, bottom=0.05, hspace=0.40, wspace=0.35)
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

        def _format_val(label, val):
            ll = label.lower()
            if 'roas' in ll or 'ctr' in ll or 'cvr' in ll or '%' in label:
                return f"{label}: {val:.2f}%"
            elif '건' in label or '주문' in label or '전환' in label:
                return f"{label}: {int(val):,}건"
            else:
                return f"{label}: {val:,.0f}" if label else f"{val:,.0f}"

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
            min_dist = float('inf')
            best = None  # (data_x, data_y, label, target_ax)
            
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

            for chk_ax in all_axes:
                # ── 막대 그래프 확인 ──
                for container in chk_ax.containers:
                    lbl = container.get_label() if hasattr(container, 'get_label') else ''
                    lbl = lbl.replace('■ ', '') if lbl else ''
                    for bar in container:
                        bx = bar.get_x() + bar.get_width() / 2
                        by = bar.get_height()
                        if by == 0:
                            continue
                        try:
                            disp = chk_ax.transData.transform((bx, by))
                            dist = ((event.x - disp[0])**2 + (event.y - disp[1])**2)**0.5
                            
                            # display 상의 bounding box를 직접 구해서 마우스가 막대 영역 내에 있는지 정확하게 판정
                            renderer = canvas.get_width_height() # canvas 렌더러 대신 window extent 사용
                            bbox = bar.get_window_extent()
                            in_bar = bbox.contains(event.x, event.y)
                            
                            if in_bar or dist < 25:
                                eff_dist = dist * 0.8  # 막대 우선순위
                                if eff_dist < min_dist:
                                    min_dist = eff_dist
                                    best = (bx, by, lbl, chk_ax)
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
                            dist = ((event.x - disp[0])**2 + (event.y - disp[1])**2)**0.5
                            if dist < min_dist and dist < 40:
                                min_dist = dist
                                best = (float(xdata[idx]), float(ydata[idx]), lbl, chk_ax)
                    except (ValueError, TypeError):
                        continue

            if best and min_dist < 50:
                dx, dy, label, target_ax = best
                text = _format_val(label, dy)
                annot = annots[ax]
                annot.xy = (dx, dy)
                # twin axes인 경우 좌표 변환
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
            else:
                if annots.get(ax) and annots[ax].get_visible():
                    annots[ax].set_visible(False)
                    vis_changed = True
            
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
        
        # 막대 위에 금액 표시
        for bar, v in zip(bars, vals):
            ax.annotate(self._fmt_val(v, 'won'), (bar.get_x() + bar.get_width()/2, bar.get_height()),
                       xytext=(0, 8), textcoords="offset points", ha='center',
                       color='white', weight='bold', fontsize=12, path_effects=pe)
        
        # 순수익 바
        p_color = '#10B981' if profit >= 0 else '#EF4444'
        p_label = f'순수익: {self._fmt_val(abs(profit), "won")}' if profit >= 0 else f'적자: {self._fmt_val(abs(profit), "won")}'
        ax.bar(['순수익'], [profit], color=p_color, width=0.5, alpha=0.8)
        ax.annotate(p_label, (2, max(profit, 0)),
                   xytext=(0, 8), textcoords="offset points", ha='center',
                   color=p_color, weight='bold', fontsize=11, path_effects=pe)
        
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
            
            bars = ax.barh(labels, top5['sales'].values, color=colors_map, height=0.5, edgecolor='none', alpha=0.8)
            
            for bar, (_, r) in zip(bars, top5.iterrows()):
                w = bar.get_width()
                ax.annotate(f'{self._fmt_val(w, "won")}  ROAS:{r["ROAS"]:.0f}%', 
                           (w, bar.get_y() + bar.get_height()/2),
                           xytext=(5, 0), textcoords="offset points", ha='left', va='center',
                           color='white', weight='bold', fontsize=8, path_effects=pe)
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
            ax.barh(y, fill, height=0.45, color=color, edgecolor='none', alpha=0.85)
            
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
        ax.grid(True, axis='y', color='#1F2937', linestyle='--', alpha=0.3)
        
        step = 2 if len(df) > 6 else 1
        self._annotate_smart(ax, df['date_s'], y1_vals, c1, y1_kind, pe, fontsize=7, step=step)
        
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
        
        for i, v in enumerate(y2_vals):
            if i % step != (step - 1) % step or v == 0: continue
            offset_y = -14 if (i // step) % 2 == 0 else 10
            txt = self._fmt_val(v, y2_kind)
            ax2.annotate(txt, (df['date_s'].iloc[i], y2_vals.iloc[i] if hasattr(y2_vals, 'iloc') else y2_vals[i]),
                         xytext=(0, offset_y), textcoords="offset points", ha='center',
                         color=c2, weight='bold', fontsize=7, path_effects=pe)
        
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
        ax.text(0.5, 1.01, '검색/비검색 영역 비중을 보고 노출 전략을 조정하세요',
               transform=ax.transAxes, ha='center', va='bottom', color='#A0AEC0', fontsize=11, style='italic')
        if not br_df.empty:
            s = br_df.groupby('region')['spend'].sum().sort_values(ascending=False)
            colors = ['#EC4899', '#8B5CF6', '#3B82F6', '#F59E0B', '#10B981']
            
            # 영역명 줄이기
            labels = []
            for name in s.index:
                if len(str(name)) > 6:
                    labels.append(str(name)[:6] + '..')
                else:
                    labels.append(str(name))
            
            bars = ax.bar(labels, s.values, color=colors[:len(s)], width=0.5, edgecolor='none', alpha=0.85)
            
            for bar, val in zip(bars, s.values):
                ax.annotate(f"{int(val):,}원", 
                           (bar.get_x() + bar.get_width()/2, bar.get_height()),
                           xytext=(0, 8), textcoords="offset points", ha='center',
                           color='#FBBF24', fontsize=11, weight='bold', 
                           fontfamily='Malgun Gothic', path_effects=pe)
            
            ax.set_ylim(0, s.max() * 1.25)
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
