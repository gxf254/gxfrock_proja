import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import calendar

from db import get_connection, init_db
import models


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("本地记账工具")
        self.geometry("860x600")
        self.resizable(True, True)

        self.conn = get_connection()
        init_db(self.conn)

        self._build_nav()
        self._build_pages()
        self._switch_page("add")

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        self.conn.close()
        self.destroy()

    # ── Navigation ───────────────────────────────────────

    def _build_nav(self):
        nav = tk.Frame(self, bg="#f0f0f0", padx=4, pady=4)
        nav.pack(fill=tk.X)

        self._nav_btns = {}
        for key, label in [("add", "记账"), ("list", "流水"),
                           ("summary", "汇总"), ("category", "分类管理")]:
            btn = tk.Button(nav, text=label, width=10, font=("", 11),
                            command=lambda k=key: self._switch_page(k))
            btn.pack(side=tk.LEFT, padx=2)
            self._nav_btns[key] = btn

    def _switch_page(self, key):
        for k, btn in self._nav_btns.items():
            btn.configure(relief=tk.RAISED if k != key else tk.SUNKEN,
                          bg="#e0e0e0" if k != key else "#c0c0ff")
        for page in self._pages.values():
            page.pack_forget()
        page = self._pages[key]
        page.pack(fill=tk.BOTH, expand=True)
        if key == "add":
            self._refresh_add_form()
        elif key == "list":
            self._refresh_trans_list()
        elif key == "summary":
            self._refresh_summary()
        elif key == "category":
            self._refresh_cat_list()

    # ── Pages container ──────────────────────────────────

    def _build_pages(self):
        self._pages = {}
        self._pages["add"] = self._build_add_page()
        self._pages["list"] = self._build_list_page()
        self._pages["summary"] = self._build_summary_page()
        self._pages["category"] = self._build_category_page()

    # ── Page 1: 记账 ─────────────────────────────────────

    def _build_add_page(self):
        page = tk.Frame(self, padx=16, pady=12)

        # type
        row = tk.Frame(page)
        row.pack(fill=tk.X, pady=4)
        tk.Label(row, text="类型:", font=("", 11), width=6).pack(side=tk.LEFT)
        self._add_type = tk.StringVar(value="expense")
        tk.Radiobutton(row, text="收入", variable=self._add_type, value="income",
                       font=("", 11), command=self._on_add_type_change).pack(side=tk.LEFT, padx=8)
        tk.Radiobutton(row, text="支出", variable=self._add_type, value="expense",
                       font=("", 11), command=self._on_add_type_change).pack(side=tk.LEFT, padx=8)

        # category
        row2 = tk.Frame(page)
        row2.pack(fill=tk.X, pady=4)
        tk.Label(row2, text="分类:", font=("", 11), width=6).pack(side=tk.LEFT)
        self._add_category = ttk.Combobox(row2, font=("", 11), state="readonly", width=14)
        self._add_category.pack(side=tk.LEFT)

        # amount
        row3 = tk.Frame(page)
        row3.pack(fill=tk.X, pady=4)
        tk.Label(row3, text="金额:", font=("", 11), width=6).pack(side=tk.LEFT)
        self._add_amount = tk.Entry(row3, font=("", 11), width=16)
        self._add_amount.pack(side=tk.LEFT)

        # date & note
        row4 = tk.Frame(page)
        row4.pack(fill=tk.X, pady=4)
        tk.Label(row4, text="日期:", font=("", 11), width=6).pack(side=tk.LEFT)
        self._add_date = tk.Entry(row4, font=("", 11), width=12)
        self._add_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self._add_date.pack(side=tk.LEFT, padx=(0, 16))
        tk.Label(row4, text="备注:", font=("", 11)).pack(side=tk.LEFT)
        self._add_note = tk.Entry(row4, font=("", 11), width=24)
        self._add_note.pack(side=tk.LEFT)

        # submit
        row5 = tk.Frame(page)
        row5.pack(pady=16)
        tk.Button(row5, text="✓ 确认记账", font=("", 12), width=14,
                  command=self._do_add).pack()

        self._add_status = tk.Label(page, text="", font=("", 10), fg="green")
        self._add_status.pack()

        return page

    def _on_add_type_change(self):
        cat_type = self._add_type.get()
        cats = models.list_categories(self.conn, cat_type)
        self._add_category['values'] = [c['name'] for c in cats]
        if cats:
            self._add_category.current(0)

    def _refresh_add_form(self):
        self._on_add_type_change()
        self._add_amount.delete(0, tk.END)
        self._add_note.delete(0, tk.END)
        self._add_date.delete(0, tk.END)
        self._add_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self._add_status.config(text="")

    def _do_add(self):
        trans_type = self._add_type.get()
        category = self._add_category.get()
        if not category:
            messagebox.showwarning("提示", "请选择一个分类")
            return
        try:
            amount = float(self._add_amount.get())
        except ValueError:
            messagebox.showwarning("提示", "金额必须是数字")
            return
        if amount <= 0:
            messagebox.showwarning("提示", "金额必须大于零")
            return
        date = self._add_date.get().strip()
        if not date:
            messagebox.showwarning("提示", "请输入日期")
            return
        note = self._add_note.get().strip()
        ok, err = models.create_transaction(
            self.conn, trans_type, amount, category, date, note)
        if ok:
            self._add_status.config(text="记账成功!")
            self._add_amount.delete(0, tk.END)
            self._add_note.delete(0, tk.END)
        else:
            messagebox.showerror("错误", err)

    # ── Page 2: 流水 ─────────────────────────────────────

    def _build_list_page(self):
        page = tk.Frame(self, padx=8, pady=8)

        # filter bar
        bar = tk.Frame(page)
        bar.pack(fill=tk.X, pady=(0, 8))

        tk.Label(bar, text="月份:", font=("", 10)).pack(side=tk.LEFT)
        self._list_month = tk.Entry(bar, font=("", 10), width=9)
        self._list_month.insert(0, datetime.now().strftime("%Y-%m"))
        self._list_month.pack(side=tk.LEFT, padx=2)

        tk.Label(bar, text="类型:", font=("", 10)).pack(side=tk.LEFT, padx=(12, 0))
        self._list_type = ttk.Combobox(bar, values=["全部", "收入", "支出"],
                                       font=("", 10), state="readonly", width=6)
        self._list_type.current(0)
        self._list_type.pack(side=tk.LEFT, padx=2)

        tk.Label(bar, text="分类:", font=("", 10)).pack(side=tk.LEFT, padx=(12, 0))
        self._list_cat = ttk.Combobox(bar, font=("", 10), state="readonly", width=8)
        self._list_cat.pack(side=tk.LEFT, padx=2)

        tk.Button(bar, text="查询", font=("", 10), width=6,
                  command=self._refresh_trans_list).pack(side=tk.LEFT, padx=12)

        # treeview
        cols = ("date", "type", "category", "amount", "note")
        self._list_tree = ttk.Treeview(page, columns=cols, show="headings", height=20)
        self._list_tree.heading("date", text="日期")
        self._list_tree.heading("type", text="类型")
        self._list_tree.heading("category", text="分类")
        self._list_tree.heading("amount", text="金额")
        self._list_tree.heading("note", text="备注")
        self._list_tree.column("date", width=100)
        self._list_tree.column("type", width=60)
        self._list_tree.column("category", width=100)
        self._list_tree.column("amount", width=120)
        self._list_tree.column("note", width=300)

        scrollbar = ttk.Scrollbar(page, orient=tk.VERTICAL, command=self._list_tree.yview)
        self._list_tree.configure(yscrollcommand=scrollbar.set)
        self._list_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        return page

    def _refresh_trans_list(self):
        for row in self._list_tree.get_children():
            self._list_tree.delete(row)

        month = self._list_month.get().strip() or None
        trans_type = None
        raw_type = self._list_type.get()
        if raw_type == "收入":
            trans_type = "income"
        elif raw_type == "支出":
            trans_type = "expense"
        category = self._list_cat.get().strip() or None

        cats = models.list_categories(self.conn)
        self._list_cat['values'] = [""] + [c['name'] for c in cats]

        rows = models.query_transactions(self.conn, month, trans_type, category)
        for r in rows:
            label = "收入" if r['type'] == 'income' else "支出"
            sign = "+" if r['type'] == 'income' else "-"
            self._list_tree.insert("", tk.END, values=(
                r['date'],
                label,
                r['category_name'],
                f"{sign}¥{r['amount']:,.2f}",
                r['note'] or ""
            ))

    # ── Page 3: 汇总 ─────────────────────────────────────

    def _build_summary_page(self):
        page = tk.Frame(self, padx=16, pady=12)

        # month selector
        now = datetime.now()
        row = tk.Frame(page)
        row.pack(pady=(0, 12))
        self._sum_month = [now.year, now.month]
        tk.Button(row, text="◀", font=("", 12), width=3,
                  command=self._sum_prev_month).pack(side=tk.LEFT)
        self._sum_label = tk.Label(row, text="", font=("", 14, "bold"), width=14)
        self._sum_label.pack(side=tk.LEFT, padx=8)
        tk.Button(row, text="▶", font=("", 12), width=3,
                  command=self._sum_next_month).pack(side=tk.LEFT)

        # cards
        cards_frame = tk.Frame(page)
        cards_frame.pack(pady=(0, 12))
        self._sum_cards = {}
        for i, (key, color) in enumerate(
            [("income", "#2e7d32"), ("expense", "#c62828"), ("balance", "#1565c0")]):
            frame = tk.Frame(cards_frame, bg=color, width=200, height=90)
            frame.pack_propagate(False)
            frame.pack(side=tk.LEFT, padx=12)
            tk.Label(frame, text="", bg=color, fg="white", font=("", 10)).pack(pady=(10, 0))
            tk.Label(frame, text="", bg=color, fg="white", font=("", 16, "bold")).pack()
            self._sum_cards[key] = frame

        # detail
        detail_frame = tk.Frame(page)
        detail_frame.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(detail_frame)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        tk.Label(left, text="【支出明细】", font=("", 11, "bold")).pack(anchor=tk.W)
        self._sum_exp_list = tk.Text(left, font=("", 10), height=12, state=tk.DISABLED)
        self._sum_exp_list.pack(fill=tk.BOTH, expand=True)

        right = tk.Frame(detail_frame)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0))
        tk.Label(right, text="【收入明细】", font=("", 11, "bold")).pack(anchor=tk.W)
        self._sum_inc_list = tk.Text(right, font=("", 10), height=12, state=tk.DISABLED)
        self._sum_inc_list.pack(fill=tk.BOTH, expand=True)

        return page

    def _refresh_summary(self):
        y, m = self._sum_month
        self._sum_label.config(text=f"{y}年{m:02d}月")
        month = f"{y}-{m:02d}"

        income, expense, inc_cats, exp_cats = models.get_summary(self.conn, month)
        balance = income - expense

        # update cards
        card_data = [
            ("income", "收入合计", f"¥{income:,.2f}"),
            ("expense", "支出合计", f"¥{expense:,.2f}"),
            ("balance", "结    余", f"¥{balance:,.2f}"),
        ]
        for key, title, value in card_data:
            frame = self._sum_cards[key]
            frame.winfo_children()[0].config(text=title)
            frame.winfo_children()[1].config(text=value)

        # update detail texts
        self._sum_exp_list.config(state=tk.NORMAL)
        self._sum_exp_list.delete("1.0", tk.END)
        if exp_cats:
            for cat in exp_cats:
                pct = (cat['total'] / expense * 100) if expense > 0 else 0
                self._sum_exp_list.insert(tk.END,
                    f"  {cat['name']:<6} ¥{cat['total']:>10,.2f} ({pct:5.1f}%)\n")
        else:
            self._sum_exp_list.insert(tk.END, "  暂无支出记录\n")
        self._sum_exp_list.config(state=tk.DISABLED)

        self._sum_inc_list.config(state=tk.NORMAL)
        self._sum_inc_list.delete("1.0", tk.END)
        if inc_cats:
            for cat in inc_cats:
                pct = (cat['total'] / income * 100) if income > 0 else 0
                self._sum_inc_list.insert(tk.END,
                    f"  {cat['name']:<6} ¥{cat['total']:>10,.2f} ({pct:5.1f}%)\n")
        else:
            self._sum_inc_list.insert(tk.END, "  暂无收入记录\n")
        self._sum_inc_list.config(state=tk.DISABLED)

    def _sum_prev_month(self):
        y, m = self._sum_month
        if m == 1:
            self._sum_month = [y - 1, 12]
        else:
            self._sum_month = [y, m - 1]
        self._refresh_summary()

    def _sum_next_month(self):
        y, m = self._sum_month
        if m == 12:
            self._sum_month = [y + 1, 1]
        else:
            self._sum_month = [y, m + 1]
        self._refresh_summary()

    # ── Page 4: 分类管理 ─────────────────────────────────

    def _build_category_page(self):
        page = tk.Frame(self, padx=8, pady=8)

        # buttons
        bar = tk.Frame(page)
        bar.pack(fill=tk.X, pady=(0, 8))
        tk.Button(bar, text="+ 新增分类", font=("", 10), width=12,
                  command=self._cat_add_dialog).pack(side=tk.LEFT)
        tk.Button(bar, text="删除选中", font=("", 10), width=10,
                  command=self._cat_delete).pack(side=tk.LEFT, padx=8)

        # treeview
        cols = ("id", "name", "type", "count")
        self._cat_tree = ttk.Treeview(page, columns=cols, show="headings", height=20)
        self._cat_tree.heading("id", text="ID")
        self._cat_tree.heading("name", text="名称")
        self._cat_tree.heading("type", text="类型")
        self._cat_tree.heading("count", text="交易数")
        self._cat_tree.column("id", width=60)
        self._cat_tree.column("name", width=140)
        self._cat_tree.column("type", width=100)
        self._cat_tree.column("count", width=100)

        scrollbar = ttk.Scrollbar(page, orient=tk.VERTICAL, command=self._cat_tree.yview)
        self._cat_tree.configure(yscrollcommand=scrollbar.set)
        self._cat_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        return page

    def _refresh_cat_list(self):
        for row in self._cat_tree.get_children():
            self._cat_tree.delete(row)
        cats = models.list_categories(self.conn)
        for c in cats:
            label = "收入" if c['type'] == 'income' else "支出"
            count = self.conn.execute(
                "SELECT COUNT(*) FROM transactions WHERE category_id = ?",
                (c['id'],)).fetchone()[0]
            self._cat_tree.insert("", tk.END, values=(
                c['id'], c['name'], label, count
            ))

    def _cat_add_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("新增分类")
        dlg.geometry("260x140")
        dlg.resizable(False, False)

        tk.Label(dlg, text="名称:", font=("", 10)).pack(pady=(12, 0))
        name_var = tk.StringVar()
        tk.Entry(dlg, textvariable=name_var, font=("", 10), width=20).pack(pady=2)

        tk.Label(dlg, text="类型:", font=("", 10)).pack()
        type_var = tk.StringVar(value="expense")
        f = tk.Frame(dlg)
        f.pack()
        tk.Radiobutton(f, text="收入", variable=type_var, value="income").pack(side=tk.LEFT)
        tk.Radiobutton(f, text="支出", variable=type_var, value="expense").pack(side=tk.LEFT)

        def do_add():
            name = name_var.get().strip()
            if not name:
                messagebox.showwarning("提示", "请输入分类名称", parent=dlg)
                return
            ok, err = models.add_category(self.conn, name, type_var.get())
            if ok:
                self._refresh_cat_list()
                dlg.destroy()
            else:
                messagebox.showerror("错误", err, parent=dlg)

        tk.Button(dlg, text="确认添加", command=do_add, font=("", 10)).pack(pady=8)

    def _cat_delete(self):
        sel = self._cat_tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请先选中一个分类")
            return
        name = self._cat_tree.item(sel[0], 'values')[1]
        ok, err = models.delete_category(self.conn, name)
        if ok:
            self._refresh_cat_list()
        else:
            messagebox.showerror("错误", err)


if __name__ == '__main__':
    App().mainloop()
