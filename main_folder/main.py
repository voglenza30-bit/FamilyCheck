import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog, ttk
import os
import json
import re
from datetime import datetime

class FamilyPsycheApp:
    def __init__(self, root):
        self.root = root
        self.root.title("가족 종합 임상 진단 시스템 V46.0 - 통합 분석 솔루션")
        self.root.geometry("1100x950")
        self.root.configure(bg="#f8fafc")
        
        self.user_info = {}
        self.results = {}
        self.temp_answers = {}
        
        self._load_data_from_files()
        self._init_ui()

    def _load_data_from_files(self):
        def read_file(filename):
            if os.path.exists(filename):
                try:
                    with open(filename, "r", encoding="utf-8") as f:
                        return [line.strip() for line in f.readlines() if line.strip()]
                except: return []
            return []
        
        def read_json_db(filename):
            if os.path.exists(filename):
                try:
                    with open(filename, "r", encoding="utf-8") as f:
                        return json.load(f)
                except: return {}
            return {}
        
        self.db_wechsler = read_file("wechsler.txt")
        self.db_mbti = read_file("mbti.txt")
        self.db_tci = read_file("tci.txt")
        self.db_mmpi = read_file("mmpi.txt")
        self.db_clinical = read_file("clinical.txt")
        
        self.db_mbti_result = read_json_db("result_mbti.json")
        self.db_iq_result = read_json_db("result_iq.json")
        self.db_tci_result = read_json_db("result_tci.json")
        self.db_clinical_result = read_json_db("result_clinical.json")

    def _init_ui(self):
        header = tk.Frame(self.root, bg="#0f172a", height=150)
        header.pack(fill="x")
        tk.Label(header, text="PSYCHOLOGICAL SOLUTION ENGINE V46.0", font=("Arial", 10, "bold"), fg="#94a3b8", bg="#0f172a").pack(pady=(30, 0))
        tk.Label(header, text="가족 종합 임상 정밀 진단 시스템", font=("Malgun Gothic", 28, "bold"), fg="white", bg="#0f172a").pack()

        container = tk.Frame(self.root, bg="#f8fafc", padx=50, pady=30)
        container.pack(expand=True, fill="both")

        self.info_card = tk.Frame(container, bg="white", padx=35, pady=25, highlightthickness=1, highlightbackground="#e2e8f0")
        self.info_card.pack(fill="x", pady=10)
        self.lbl_profile = tk.Label(self.info_card, text="피검자 정보를 등록하거나 기존 파일을 불러오세요.", font=("Malgun Gothic", 12), bg="white", fg="#64748b")
        self.lbl_profile.pack(side="left")
        
        btn_group = tk.Frame(self.info_card, bg="white")
        btn_group.pack(side="right")
        tk.Button(btn_group, text="이어하기", command=self.resume_progress, bg="#64748b", fg="white", font=("Malgun Gothic", 10, "bold"), padx=15, pady=5).pack(side="left", padx=5)
        tk.Button(btn_group, text="신규 등록", command=self.setup_profile, bg="#2563eb", fg="white", font=("Malgun Gothic", 10, "bold"), padx=15, pady=5).pack(side="left")

        grid_frame = tk.Frame(container, bg="#f8fafc")
        grid_frame.pack(fill="x", pady=40)
        
        self.menu_items = [
            ("웩슬러 지능", self.db_wechsler, "IQ"), ("MBTI 성격", self.db_mbti, "MBTI"),
            ("TCI 기질", self.db_tci, "TCI"), ("MMPI 핵심", self.db_mmpi, "MMPI"),
            ("임상 선별", self.db_clinical, "CLINICAL")
        ]

        for i, (name, db, cat) in enumerate(self.menu_items):
            btn = tk.Button(grid_frame, text=name, font=("Malgun Gothic", 12, "bold"), width=16, height=3, bg="white", relief="groove",
                            command=lambda d=db, t=name, c=cat: self.open_survey(t, d, c))
            btn.grid(row=0, column=i, padx=7)

        tk.Button(container, text="📂 보관함: 저장된 과거 보고서 열람 및 인쇄", font=("Malgun Gothic", 14, "bold"), bg="#475569", fg="white", height=2, command=self.open_archive).pack(fill="x", pady=(0, 15))
        tk.Button(container, text="프리미엄 정밀 보고서 발행 (현재 피검자)", font=("Malgun Gothic", 18, "bold"), bg="#10b981", fg="white", height=3, command=self.generate_report).pack(fill="x")

    def setup_profile(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("피검자 등록")
        dialog.geometry("400x500")
        dialog.transient(self.root); dialog.grab_set(); dialog.focus_force()      
        
        fields = [("성명", "name"), ("생년월일", "birth"), ("성별", "gender"), ("관계", "rel")]
        entries = {}
        for i, (label, key) in enumerate(fields):
            tk.Label(dialog, text=label).pack(pady=(10, 0))
            ent = tk.Entry(dialog, font=("Malgun Gothic", 12)); ent.pack(pady=5, padx=30, fill="x")
            entries[key] = ent
        def save():
            self.user_info = {k: v.get().strip() for k, v in entries.items()}
            self.temp_answers = {cat[2]: {} for cat in self.menu_items}
            self.lbl_profile.config(text=f"▶ 진행중인 피검자: {self.user_info['name']}님", fg="#1e293b")
            dialog.destroy()
        tk.Button(dialog, text="확인", command=save, bg="#0f172a", fg="white").pack(pady=30)

    def save_current_progress(self):
        if not self.user_info: return
        data = {"user_info": self.user_info, "temp_answers": self.temp_answers, "results": self.results}
        with open(f"progress_{self.user_info['name']}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def resume_progress(self):
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if path:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.user_info, self.temp_answers, self.results = data["user_info"], data["temp_answers"], data.get("results", {})
                self.lbl_profile.config(text=f"▶ 이어하기: {self.user_info['name']}님", fg="#2563eb")

    def open_survey(self, title, questions, category):
        if not self.user_info: messagebox.showwarning("알림", "정보를 먼저 등록하세요."); return
        if not questions: messagebox.showinfo("알림", f"{title} 문항 데이터 파일이 없습니다."); return
        
        win = tk.Toplevel(self.root)
        win.title(title); win.geometry("1000x900")
        win.transient(self.root); win.grab_set(); win.focus_force()

        canvas = tk.Canvas(win, bg="#f8fafc", highlightthickness=0)
        scrollbar = ttk.Scrollbar(win, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#f8fafc")
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw", width=950)
        canvas.configure(yscrollcommand=scrollbar.set)
        win.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        vars = []; saved_data = self.temp_answers.get(category, {})
        
        for i, q in enumerate(questions):
            clean_q = re.sub(r'^[\d\s\.]+', '', q.strip())
            q_card = tk.Frame(scroll_frame, bg="white", padx=30, pady=20, highlightthickness=1, highlightbackground="#e2e8f0")
            q_card.pack(fill="x", pady=10, padx=50)
            
            tk.Label(q_card, text=f"문항 {i+1}", font=("Arial", 9, "bold"), fg="#2563eb", bg="white").pack(anchor="w")
            tk.Label(q_card, text=clean_q, font=("Malgun Gothic", 12), bg="white", wraplength=800, justify="left").pack(anchor="w", pady=(5, 10))
            
            v = tk.IntVar(value=saved_data.get(str(i), -1)); vars.append(v)
            opt_frame = tk.Frame(q_card, bg="white"); opt_frame.pack(anchor="w")
            
            opts = [("그렇다", 1), ("아니다", 0)] if category in ["MMPI", "CLINICAL"] else [("전혀아님", 0), ("아님", 1), ("보통", 2), ("그렇다", 3), ("매우", 4)]
            for text, val in opts:
                tk.Radiobutton(opt_frame, text=text, variable=v, value=val, bg="white", 
                               command=lambda c=category, idx=i, var=v: self.update_temp(c, idx, var.get())).pack(side="left", padx=15)
        
        def finish():
            if any(v.get() == -1 for v in vars):
                if messagebox.askyesno("미완료", "저장하고 닫을까요?"): self.save_current_progress(); win.destroy()
            else:
                self.results[category] = sum(v.get() for v in vars); self.save_current_progress(); win.destroy()
        
        canvas.pack(side="left", expand=True, fill="both"); scrollbar.pack(side="right", fill="y")
        tk.Button(win, text="완료 및 결과 저장", command=finish, bg="#1e293b", fg="white", height=2, font=("Malgun Gothic", 11, "bold")).pack(fill="x", side="bottom")

    def update_temp(self, cat, idx, val):
        if cat not in self.temp_answers: self.temp_answers[cat] = {}
        self.temp_answers[cat][str(idx)] = val; self.save_current_progress()

    def get_visual_bar(self, score, max_score):
        if max_score == 0: max_score = 1
        percentage = min((score / max_score) * 100, 100)
        filled = int(percentage / 5)
        return f"[{'█' * filled}{'░' * (20 - filled)}] {percentage:.1f}%"

    # --- 분석 엔진 ---
    def analyze_iq(self, score):
        max_v = len(self.db_wechsler) * 4 if self.db_wechsler else 400
        fsiq = int((score / max_v) * 60 + 80)
        percentile = min(99, int((fsiq - 80) / 60 * 99))
        metric = f"추정 FSIQ: {fsiq} (백분위: {percentile}%)"
        key = "superior" if fsiq >= 120 else ("high_average" if fsiq >= 100 else "average")
        data = self.db_iq_result.get(key, ["결과 정보 없음", "데이터 파일을 확인하세요."])
        return metric, data

    def analyze_mbti(self, score):
        answers = self.temp_answers.get("MBTI", {})
        d_scores = {"E": 0, "I": 0, "S": 0, "N": 0, "T": 0, "F": 0, "J": 0, "P": 0}
        for idx_str, val in answers.items():
            idx = int(idx_str)
            if 0 <= idx <= 4: d_scores["E"] += val; d_scores["I"] += (4 - val)
            elif 5 <= idx <= 9: d_scores["S"] += val; d_scores["N"] += (4 - val)
            elif 10 <= idx <= 14: d_scores["T"] += val; d_scores["F"] += (4 - val)
            else: d_scores["J"] += val; d_scores["P"] += (4 - val)
        mbti_type = "".join([
            "E" if d_scores["E"] >= d_scores["I"] else "I",
            "S" if d_scores["S"] >= d_scores["N"] else "N",
            "T" if d_scores["T"] >= d_scores["F"] else "F",
            "J" if d_scores["J"] >= d_scores["P"] else "P"
        ])
        metric = f"도출 유형: {mbti_type}"
        return metric, self.db_mbti_result.get(mbti_type, self.db_mbti_result.get("DEFAULT", {}))

    def analyze_tci(self, score):
        max_v = len(self.db_tci) * 4 if self.db_tci else 560
        t_score = int(((score - (max_v/2)) / (max_v/4)) * 10 + 50)
        t_score = max(20, min(80, t_score))
        metric = f"T-Score: {t_score}"
        key = "high" if t_score >= 65 else ("low" if t_score <= 40 else "moderate")
        return metric, self.db_tci_result.get(key, self.db_tci_result.get("DEFAULT", {}))

    def analyze_clinical(self, score, cat_name, max_q):
        max_v = max_q if max_q > 0 else 100
        ratio = score / max_v
        metric = f"위험 지수: {int(ratio*100)} / 100"
        key = "elevated" if ratio >= 0.7 else ("borderline" if ratio >= 0.4 else "normal")
        return metric, self.db_clinical_result.get(key, self.db_clinical_result.get("DEFAULT", {}))

    # --- 통합 출력 렌더러 ---
    def format_section(self, title, metric, data):
        res = f"▶ {title}\n"
        # 데이터가 딕셔너리(상세형)인 경우
        if isinstance(data, dict):
            res += f" - 결과: {data.get('title', '정보 없음')} ({metric})\n"
            res += f"   \"{data.get('summary', '')}\"\n\n"
            if data.get('features'):
                res += "  [주요 특징]\n"
                for f in data['features']: res += f"   · {f}\n"
            if data.get('strengths'):
                res += "\n  [핵심 강점]\n"
                for s in data['strengths']: res += f"   · {s}\n"
            if data.get('cautions'):
                res += "\n  [주의 및 보완점]\n"
                for c in data['cautions']: res += f"   · {c}\n"
        # 데이터가 리스트(단순형)인 경우 (예: IQ)
        else:
            res += f" - 수준: {data[0]} ({metric})\n"
            res += f" - 해석: {data[1]}\n"
        return res + "\n"

    def print_file(self, filepath):
        try: os.startfile(os.path.abspath(filepath), "print")
        except Exception as e: messagebox.showerror("오류", f"인쇄 실패: {e}")

    def display_report_window(self, window_title, report_content, filepath):
        rep_win = tk.Toplevel(self.root); rep_win.title(window_title); rep_win.geometry("900x800")
        rep_win.transient(self.root); rep_win.grab_set(); rep_win.focus_force()
        txt = scrolledtext.ScrolledText(rep_win, padx=30, pady=30, font=("Malgun Gothic", 11), spacing1=5, spacing2=2)
        txt.pack(expand=True, fill="both"); txt.insert(tk.END, report_content); txt.config(state="disabled") 
        btn_frame = tk.Frame(rep_win, bg="#e2e8f0", pady=10); btn_frame.pack(fill="x", side="bottom")
        tk.Button(btn_frame, text="🖨️ 인쇄하기", font=("Malgun Gothic", 12, "bold"), bg="#3b82f6", fg="white", width=20, height=2, command=lambda: self.print_file(filepath)).pack(side="left", padx=20)
        tk.Button(btn_frame, text="닫기", font=("Malgun Gothic", 12), bg="#475569", fg="white", width=15, height=2, command=rep_win.destroy).pack(side="right", padx=20)

    def open_archive(self):
        archive_win = tk.Toplevel(self.root); archive_win.title("보관함"); archive_win.geometry("500x600")
        archive_win.transient(self.root); archive_win.grab_set()
        report_files = [f for f in os.listdir('.') if f.startswith('PREMIUM_REPORT_') and f.endswith('.txt')]
        listbox = tk.Listbox(archive_win, font=("Malgun Gothic", 12), selectbackground="#3b82f6"); listbox.pack(expand=True, fill="both", padx=30, pady=10)
        for f in report_files: listbox.insert(tk.END, f)
        def open_selected():
            selection = listbox.curselection()
            if not selection: return
            selected_file = listbox.get(selection[0])
            with open(selected_file, "r", encoding="utf-8") as f: content = f.read()
            self.display_report_window(f"열람: {selected_file}", content, selected_file)
        listbox.bind('<Double-1>', lambda e: open_selected())
        tk.Button(archive_win, text="보고서 열기", font=("Malgun Gothic", 12, "bold"), bg="#10b981", fg="white", height=2, command=open_selected).pack(fill="x", padx=30, pady=20)

    def generate_report(self):
        if not self.results: messagebox.showwarning("알림", "결과 데이터가 없습니다."); return
        u = self.user_info
        r = "="*70 + "\n               종합 임상 심리 정밀 보고서 (V46.0)\n" + "="*70 + "\n\n"
        r += f"[1. 피검자 정보]\n - 성명: {u.get('name')} | 연령: {u.get('birth')} | 관계: {u.get('rel')}\n\n"
        r += "[2. 지표 요약]\n" + "-"*70 + "\n"
        max_scores = {"IQ": len(self.db_wechsler)*4, "MBTI": len(self.db_mbti)*4, "TCI": len(self.db_tci)*4, "MMPI": len(self.db_mmpi), "CLINICAL": len(self.db_clinical)}
        for cat_id, score in self.results.items():
            r += f"{cat_id:<14} | {score:3d} / {max_scores.get(cat_id, 100):<10} | {self.get_visual_bar(score, max_scores.get(cat_id, 100))}\n"
        r += "-"*70 + "\n\n[3. 정밀 분석 결과]\n" + "="*70 + "\n"
        
        if "IQ" in self.results: r += self.format_section("웩슬러 지능(IQ)", *self.analyze_iq(self.results["IQ"]))
        if "MBTI" in self.results: r += self.format_section("MBTI 성격", *self.analyze_mbti(self.results["MBTI"]))
        if "TCI" in self.results: r += self.format_section("TCI 기질", *self.analyze_tci(self.results["TCI"]))
        if "MMPI" in self.results: r += self.format_section("MMPI 핵심", *self.analyze_clinical(self.results["MMPI"], "MMPI", max_scores["MMPI"]))
        if "CLINICAL" in self.results: r += self.format_section("임상 선별", *self.analyze_clinical(self.results["CLINICAL"], "CLINICAL", max_scores["CLINICAL"]))

        r += "="*70 + "\n * 위 분석은 알고리즘 기반 추정치로, 전문 상담가의 자문을 권장합니다.\n" + "="*70
        file_name = f"PREMIUM_REPORT_{u.get('name', 'USER')}.txt"
        with open(file_name, "w", encoding="utf-8") as f: f.write(r)
        self.display_report_window("정밀 분석 보고서", r, file_name)

if __name__ == "__main__":
    root = tk.Tk(); app = FamilyPsycheApp(root); root.mainloop()