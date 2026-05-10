import models


def _fmt(amount):
    """Format amount to 2 decimal places."""
    return f"{amount:,.2f}"


# ── Category Commands ─────────────────────────────────────

def add_category(conn, name, cat_type):
    ok, err = models.add_category(conn, name, cat_type)
    if ok:
        label = "收入" if cat_type == 'income' else "支出"
        print(f"已添加{label}分类: {name}")
    else:
        print(f"错误: {err}")


def list_categories(conn, cat_type=None):
    rows = models.list_categories(conn, cat_type)
    if not rows:
        print("暂无分类")
        return
    print(f"{'ID':<4} {'分类名':<8} {'类型'}")
    print("-" * 22)
    for r in rows:
        label = "收入" if r['type'] == 'income' else "支出"
        print(f"{r['id']:<4} {r['name']:<8} {label}")


def delete_category(conn, name):
    ok, err = models.delete_category(conn, name)
    if ok:
        print(f"已删除分类: {name}")
    else:
        print(f"错误: {err}")


# ── Transaction Commands ──────────────────────────────────

def add_transaction(conn, trans_type, amount, category, date, note):
    ok, err = models.create_transaction(
        conn, trans_type, amount, category, date, note)
    if ok:
        label = "收入" if trans_type == 'income' else "支出"
        print(f"已记录{label}: {category} ¥{_fmt(amount)} ({date})")
    else:
        print(f"错误: {err}")


def list_transactions(conn, month=None, trans_type=None, category=None):
    rows = models.query_transactions(conn, month, trans_type, category)
    if not rows:
        print("暂无记录")
        return
    print(f"{'ID':<5} {'日期':<12} {'类型':<6} {'分类':<8} {'金额':>10}  {'备注'}")
    print("-" * 64)
    for r in rows:
        label = "收入" if r['type'] == 'income' else "支出"
        sign = "+" if r['type'] == 'income' else "-"
        print(f"{r['id']:<5} {r['date']:<12} {label:<6} {r['category_name']:<8} "
              f"{sign}¥{_fmt(r['amount']):>8}  {r['note']}")


def show_summary(conn, month):
    income, expense, inc_cats, exp_cats = models.get_summary(conn, month)
    balance = income - expense

    year, mon = month.split('-')
    print()
    print("═" * 36)
    print(f"    {year}年{int(mon):02d}月 收支汇总")
    print("═" * 36)
    print(f"  📈 收入合计: ¥{_fmt(income):>11}")
    print(f"  📉 支出合计: ¥{_fmt(expense):>11}")
    print(f"  💰 结    余: ¥{_fmt(balance):>11}")

    if exp_cats:
        print("─" * 36)
        print("  【支出明细】")
        for cat in exp_cats:
            pct = (cat['total'] / expense * 100) if expense > 0 else 0
            print(f"    {cat['name']:<6}   ¥{_fmt(cat['total']):>9} ({pct:5.1f}%)")

    if inc_cats:
        print("─" * 36)
        print("  【收入明细】")
        for cat in inc_cats:
            pct = (cat['total'] / income * 100) if income > 0 else 0
            print(f"    {cat['name']:<6}   ¥{_fmt(cat['total']):>9} ({pct:5.1f}%)")

    print("═" * 36)
    print()
