import argparse
import sys

from db import get_connection, init_db
import commands


def main():
    parser = argparse.ArgumentParser(
        description='本地记账工具 — 命令行个人财务管理')
    sub = parser.add_subparsers(dest='command')

    # ── add ────────────────────────────────────────────
    p_add = sub.add_parser('add', help='记一笔账')
    p_add.add_argument('--type', required=True, choices=['income', 'expense'],
                       help='交易类型')
    p_add.add_argument('--amount', required=True, type=float,
                       help='金额')
    p_add.add_argument('--category', required=True, help='分类名称')
    p_add.add_argument('--date', required=True, help='日期 (YYYY-MM-DD)')
    p_add.add_argument('--note', default='', help='备注')

    # ── list ───────────────────────────────────────────
    p_list = sub.add_parser('list', help='查看流水')
    p_list.add_argument('--month', help='月份过滤 (YYYY-MM)')
    p_list.add_argument('--type', choices=['income', 'expense'], help='类型过滤')
    p_list.add_argument('--category', help='分类过滤')

    # ── summary ────────────────────────────────────────
    p_sum = sub.add_parser('summary', help='月度汇总报表')
    p_sum.add_argument('--month', required=True, help='月份 (YYYY-MM)')

    # ── category ───────────────────────────────────────
    p_cat = sub.add_parser('category', help='管理分类')
    cat_sub = p_cat.add_subparsers(dest='cat_action')

    p_cat_add = cat_sub.add_parser('add', help='添加分类')
    p_cat_add.add_argument('name', help='分类名称')
    p_cat_add.add_argument('--type', required=True, choices=['income', 'expense'],
                           help='分类类型')

    cat_sub.add_parser('list', help='列出所有分类')

    p_cat_del = cat_sub.add_parser('delete', help='删除分类')
    p_cat_del.add_argument('name', help='分类名称')

    # ── gui ────────────────────────────────────────────
    sub.add_parser('gui', help='启动图形界面')

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    conn = get_connection()
    init_db(conn)

    try:
        if args.command == 'add':
            commands.add_transaction(
                conn, args.type, args.amount, args.category,
                args.date, args.note)
        elif args.command == 'list':
            commands.list_transactions(
                conn, args.month, args.type, args.category)
        elif args.command == 'summary':
            commands.show_summary(conn, args.month)
        elif args.command == 'category':
            if args.cat_action == 'add':
                commands.add_category(conn, args.name, args.type)
            elif args.cat_action == 'list':
                commands.list_categories(conn)
            elif args.cat_action == 'delete':
                commands.delete_category(conn, args.name)
            else:
                p_cat.print_help()
        elif args.command == 'gui':
            import gui
            conn.close()
            gui.App().mainloop()
            return
    finally:
        conn.close()


if __name__ == '__main__':
    main()
