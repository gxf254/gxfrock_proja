import sqlite3
import calendar


# ── Category ──────────────────────────────────────────────

def add_category(conn, name, cat_type):
    try:
        conn.execute(
            "INSERT INTO categories (name, type) VALUES (?, ?)",
            (name, cat_type))
        conn.commit()
        return True, None
    except sqlite3.IntegrityError:
        return False, f"分类 '{name}' 已存在"


def list_categories(conn, cat_type=None):
    if cat_type:
        return conn.execute(
            "SELECT * FROM categories WHERE type = ? ORDER BY id",
            (cat_type,)).fetchall()
    return conn.execute(
        "SELECT * FROM categories ORDER BY type, id").fetchall()


def delete_category(conn, name):
    cat = conn.execute(
        "SELECT id FROM categories WHERE name = ?", (name,)).fetchone()
    if not cat:
        return False, f"分类 '{name}' 不存在"
    used = conn.execute(
        "SELECT COUNT(*) FROM transactions WHERE category_id = ?",
        (cat['id'],)).fetchone()[0]
    if used > 0:
        return False, f"分类 '{name}' 下有 {used} 条交易记录，无法删除"
    conn.execute("DELETE FROM categories WHERE id = ?", (cat['id'],))
    conn.commit()
    return True, None


# ── Transaction ───────────────────────────────────────────

def create_transaction(conn, trans_type, amount, category_name, date, note):
    cat = conn.execute(
        "SELECT id, type FROM categories WHERE name = ?",
        (category_name,)).fetchone()
    if not cat:
        return False, f"分类 '{category_name}' 不存在，请先创建"
    if cat['type'] != trans_type:
        label = "收入" if trans_type == 'income' else "支出"
        cat_label = "收入" if cat['type'] == 'income' else "支出"
        return False, f"分类 '{category_name}' 是{cat_label}分类，不能用于{label}交易"
    conn.execute(
        "INSERT INTO transactions (type, amount, category_id, date, note) "
        "VALUES (?, ?, ?, ?, ?)",
        (trans_type, amount, cat['id'], date, note))
    conn.commit()
    return True, None


def query_transactions(conn, month=None, trans_type=None, category=None):
    sql = ("SELECT t.*, c.name as category_name "
           "FROM transactions t JOIN categories c ON t.category_id = c.id "
           "WHERE 1=1")
    params = []
    if month:
        sql += " AND t.date LIKE ?"
        params.append(f"{month}%")
    if trans_type:
        sql += " AND t.type = ?"
        params.append(trans_type)
    if category:
        sql += " AND c.name = ?"
        params.append(category)
    sql += " ORDER BY t.date DESC, t.id DESC"
    return conn.execute(sql, params).fetchall()


def get_summary(conn, month):
    params = [f"{month}%"]

    income_total = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM transactions "
        "WHERE type = 'income' AND date LIKE ?", params).fetchone()[0]

    expense_total = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM transactions "
        "WHERE type = 'expense' AND date LIKE ?", params).fetchone()[0]

    income_by_cat = conn.execute(
        "SELECT c.name, SUM(t.amount) as total "
        "FROM transactions t JOIN categories c ON t.category_id = c.id "
        "WHERE t.type = 'income' AND t.date LIKE ? "
        "GROUP BY c.name ORDER BY total DESC", params).fetchall()

    expense_by_cat = conn.execute(
        "SELECT c.name, SUM(t.amount) as total "
        "FROM transactions t JOIN categories c ON t.category_id = c.id "
        "WHERE t.type = 'expense' AND t.date LIKE ? "
        "GROUP BY c.name ORDER BY total DESC", params).fetchall()

    return income_total, expense_total, income_by_cat, expense_by_cat
