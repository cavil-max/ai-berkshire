#!/usr/bin/env python3
"""美股基本面数据工具 — 使用 edgartools 从 SEC EDGAR 获取 XBRL 数据。

替代通过 Agent WebFetch 抓取 macrotrends.net 的方式，直接从 SEC 官方 API
获取结构化财务数据，更可靠、更准确、有官方支持。

需要 pip install edgartools

用法（由 Skills 自动调用）：
    python3 tools/us_fundamentals.py financials AAPL          # 近5年年报核心数据
    python3 tools/us_fundamentals.py financials NVDA --years 3  # 近3年
    python3 tools/us_fundamentals.py filings AAPL              # 最近 filings 列表
    python3 tools/us_fundamentals.py metrics AAPL              # 关键指标摘要

SEC EDGAR 要求设置身份标识。通过环境变量或代码设置：
    export EDGAR_IDENTITY="Your Name your.email@example.com"
"""

import argparse
import os
import sys

try:
    from edgar import Company, set_identity
except ImportError:
    print("❌ 未安装 edgartools。请运行: pip install edgartools", file=sys.stderr)
    sys.exit(1)


def _init_identity():
    """初始化 SEC EDGAR 身份标识。"""
    identity = os.environ.get("EDGAR_IDENTITY", "")
    if identity:
        set_identity(identity)
    else:
        # 默认身份（SEC 要求 User-Agent 包含联系方式）
        set_identity("AI Berkshire Research research@ai-berkshire.com")


def _fmt_amount(val) -> str:
    """格式化大金额为易读单位。"""
    if val is None:
        return "-"
    try:
        v = float(val)
        if abs(v) >= 1e9:
            return f"{v / 1e9:.2f}B"
        elif abs(v) >= 1e6:
            return f"{v / 1e6:.2f}M"
        elif abs(v) >= 1e3:
            return f"{v / 1e3:.2f}K"
        return f"{v:.2f}"
    except (ValueError, TypeError):
        return str(val)


# XBRL concept 名 → 统一字段名
_INCOME_CONCEPTS = {
    "RevenueFromContractWithCustomerExcludingAssessedTax": "revenue",
    "Revenues": "revenue",
    "Revenue": "revenue",
    "CostOfGoodsAndServicesSold": "cogs",
    "CostOfRevenue": "cogs",
    "GrossProfit": "gross_profit",
    "OperatingIncomeLoss": "op_income",
    "NetIncomeLoss": "net_income",
    "EarningsPerShareBasic": "eps_basic",
    "EarningsPerShareDiluted": "eps_diluted",
}

_BALANCE_CONCEPTS = {
    "Assets": "total_assets",
    "Liabilities": "total_liab",
    "StockholdersEquity": "equity",
}


def _extract_period_data(df, concepts, col_name):
    """从 DataFrame 提取指定列的 XBRL 数据，用 concept 名匹配。"""
    if df is None or col_name not in df.columns:
        return {}
    result = {}
    for concept, field in concepts.items():
        if concept in df.index:
            val = df.loc[concept, col_name]
            if val is not None and str(val) != "nan":
                result[field] = val
    return result


def _get_data_columns(df):
    """获取 DataFrame 中的数据列名（跳过 label/depth 等元数据列）。"""
    if df is None:
        return []
    meta_cols = {"label", "depth", "is_abstract", "is_total", "section", "confidence"}
    return [c for c in df.columns if c not in meta_cols]


def cmd_financials(ticker: str, years: int = 5):
    """获取近 N 年年报核心财务数据。"""
    _init_identity()
    company = Company(ticker.upper())
    print("=" * 60)
    print(f"美股财务数据: {company.name} ({ticker.upper()})")
    print("=" * 60)

    try:
        income = company.income_statement(periods=years, annual=True)
        balance = company.balance_sheet(periods=years, annual=True)
    except Exception as e:
        print(f"  ❌ 获取财务数据失败: {e}")
        return

    if income is None:
        print("  ❌ 无可用的利润表数据")
        return

    income_df = income.to_dataframe()
    balance_df = balance.to_dataframe() if balance else None

    income_cols = _get_data_columns(income_df)
    balance_cols = _get_data_columns(balance_df)

    for col in income_cols[:years]:
        print(f"\n  --- {col} ---")
        inc = _extract_period_data(income_df, _INCOME_CONCEPTS, col)
        rev = inc.get("revenue")
        gp = inc.get("gross_profit")
        op = inc.get("op_income")
        ni = inc.get("net_income")
        eps_b = inc.get("eps_basic")
        eps_d = inc.get("eps_diluted")

        print(f"  营收:           {_fmt_amount(rev)}")
        print(f"  毛利润:         {_fmt_amount(gp)}")
        if rev and gp:
            try:
                gm = float(gp) / float(rev) * 100
                print(f"  毛利率:         {gm:.1f}%")
            except (ValueError, TypeError, ZeroDivisionError):
                pass
        print(f"  营业利润:       {_fmt_amount(op)}")
        print(f"  净利润:         {_fmt_amount(ni)}")
        if rev and ni:
            try:
                nm = float(ni) / float(rev) * 100
                print(f"  净利率:         {nm:.1f}%")
            except (ValueError, TypeError, ZeroDivisionError):
                pass
        print(f"  EPS(基本):      {eps_b}")
        print(f"  EPS(稀释):      {eps_d}")

        # 资产负债表（按列名匹配）
        if balance_df is not None and col in balance_cols:
            bs = _extract_period_data(balance_df, _BALANCE_CONCEPTS, col)
            print(f"  总资产:         {_fmt_amount(bs.get('total_assets'))}")
            print(f"  总负债:         {_fmt_amount(bs.get('total_liab'))}")
            print(f"  股东权益:       {_fmt_amount(bs.get('equity'))}")


def cmd_metrics(ticker: str):
    """关键指标摘要（最近一期）。"""
    _init_identity()
    company = Company(ticker.upper())
    print("=" * 60)
    print(f"关键指标: {company.name} ({ticker.upper()})")
    print("=" * 60)

    try:
        income = company.income_statement(periods=1, annual=True)
        balance = company.balance_sheet(periods=1, annual=True)
    except Exception as e:
        print(f"  ❌ 获取数据失败: {e}")
        return

    if income is None:
        print("  ❌ 无可用数据")
        return

    income_df = income.to_dataframe()
    balance_df = balance.to_dataframe() if balance else None
    income_cols = _get_data_columns(income_df)
    if not income_cols:
        print("  ❌ 无可用数据列")
        return
    period = income_cols[0]

    print(f"\n  报告期:         {period}")
    print(f"  公司名:         {company.name}")
    print(f"  流通股:         {company.shares_outstanding:,}" if company.shares_outstanding else "  流通股:         -")

    inc = _extract_period_data(income_df, _INCOME_CONCEPTS, period)
    revenue = inc.get("revenue")
    net_income = inc.get("net_income")
    eps = inc.get("eps_diluted") or inc.get("eps_basic")

    print(f"  营收:           {_fmt_amount(revenue)}")
    print(f"  净利润:         {_fmt_amount(net_income)}")
    print(f"  EPS:            {eps}")

    if revenue and net_income:
        try:
            nm = float(net_income) / float(revenue) * 100
            print(f"  净利率:         {nm:.1f}%")
        except (ValueError, TypeError, ZeroDivisionError):
            pass

    if balance_df is not None:
        balance_cols = _get_data_columns(balance_df)
        if balance_cols and period in balance_cols:
            bs = _extract_period_data(balance_df, _BALANCE_CONCEPTS, period)
            total_assets = bs.get("total_assets")
            equity = bs.get("equity")
            print(f"  总资产:         {_fmt_amount(total_assets)}")
            print(f"  股东权益:       {_fmt_amount(equity)}")
            if total_assets and equity:
                try:
                    debt_ratio = (float(total_assets) - float(equity)) / float(total_assets) * 100
                    print(f"  资产负债率:     {debt_ratio:.1f}%")
                except (ValueError, TypeError, ZeroDivisionError):
                    pass


def cmd_filings(ticker: str, count: int = 10):
    """列出最近的 SEC filings。"""
    _init_identity()
    company = Company(ticker.upper())
    print("=" * 60)
    print(f"SEC Filings: {company.name} ({ticker.upper()})")
    print("=" * 60)

    try:
        filings = company.get_filings()
    except Exception as e:
        print(f"  ❌ 获取 filings 失败: {e}")
        return

    print(f"\n  最近 {count} 个 filings:\n")
    print(f"  {'日期':<12} {'类型':<8} {'Accession Number'}")
    print(f"  {'-'*12} {'-'*8} {'-'*20}")
    for i, f in enumerate(filings[:count]):
        print(f"  {str(f.filing_date):<12} {f.form:<8} {f.accession_number}")


def main():
    ap = argparse.ArgumentParser(description="美股基本面数据工具（SEC EDGAR）")
    sub = ap.add_subparsers(dest="command", required=True)

    p_fin = sub.add_parser("financials", help="近 N 年年报核心财务数据")
    p_fin.add_argument("ticker", type=str, help="股票代码（如 AAPL, NVDA）")
    p_fin.add_argument("--years", type=int, default=5, help="年数（默认 5）")

    p_met = sub.add_parser("metrics", help="关键指标摘要（最近一期）")
    p_met.add_argument("ticker", type=str, help="股票代码")

    p_fil = sub.add_parser("filings", help="列出最近的 SEC filings")
    p_fil.add_argument("ticker", type=str, help="股票代码")
    p_fil.add_argument("--count", type=int, default=10, help="显示数量（默认 10）")

    args = ap.parse_args()

    if args.command == "financials":
        cmd_financials(args.ticker, args.years)
    elif args.command == "metrics":
        cmd_metrics(args.ticker)
    elif args.command == "filings":
        cmd_filings(args.ticker, args.count)


if __name__ == "__main__":
    main()
