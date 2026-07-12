#!/usr/bin/env python3
"""A股数据工具 — 基于 AKShare 的行情、财务、搜索工具。

为 Skills 提供 A 股实时行情、财务数据等数据。
使用 AKShare 封装东方财富/腾讯数据源。

用法（由 Skills 自动调用）：
    python3 tools/ashare_data.py quote 600519                    # 实时行情
    python3 tools/ashare_data.py financials 600519               # 核心财务数据（近5年）
    python3 tools/ashare_data.py valuation 600519                # 估值指标
    python3 tools/ashare_data.py search 茅台                      # 搜索股票代码

需要 Python >= 3.8 + pip install akshare pandas。
"""

import argparse
import os
import sys

# 清除代理环境变量，避免 AKShare 底层 requests 走代理连不上国内数据源
for _key in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"):
    os.environ.pop(_key, None)

import akshare as ak
import pandas as pd


def _fmt_pct(value) -> str:
    if value is None or value == "-" or value == "":
        return "-"
    try:
        return f"{float(value):.2f}%"
    except (ValueError, TypeError):
        return str(value)


# ---------------------------------------------------------------------------
# 命令实现
# ---------------------------------------------------------------------------


def cmd_quote(code: str):
    """实时行情。"""
    code = code.strip().replace(".SH", "").replace(".SZ", "").replace(".BJ", "")
    df = ak.stock_zh_a_spot_em()
    row = df[df["代码"] == code]
    if row.empty:
        print(f"❌ 未找到股票代码 {code}")
        return
    s = row.iloc[0]
    print("=" * 60)
    print(f"实时行情: {s['名称']} ({code})")
    print("=" * 60)
    print(f"  当前价:     {s['最新价']}")
    print(f"  涨跌幅:     {s['涨跌幅']}%")
    print(f"  涨跌额:     {s['涨跌额']}")
    print(f"  今开:       {s['今开']}")
    print(f"  最高:       {s['最高']}")
    print(f"  最低:       {s['最低']}")
    print(f"  昨收:       {s['昨收']}")
    print(f"  成交量:     {s['成交量']} 手")
    print(f"  成交额:     {s['成交额'] / 1e8:.2f} 亿")
    print(f"  换手率:     {s['换手率']}%")
    print(f"  PE(动):     {s['市盈率-动态']}")
    print(f"  PB:         {s['市净率']}")
    print(f"  总市值:     {s['总市值'] / 1e8:.2f} 亿")
    print(f"  流通市值:   {s['流通市值'] / 1e8:.2f} 亿")


def cmd_valuation(code: str):
    """估值指标。"""
    code = code.strip().replace(".SH", "").replace(".SZ", "").replace(".BJ", "")
    df = ak.stock_zh_a_spot_em()
    row = df[df["代码"] == code]
    if row.empty:
        print(f"❌ 未找到股票代码 {code}")
        return
    s = row.iloc[0]
    print("=" * 60)
    print(f"估值指标: {s['名称']} ({code})")
    print("=" * 60)
    print(f"  PE(动态):   {s['市盈率-动态']}")
    print(f"  PB:         {s['市净率']}")
    print(f"  总市值:     {s['总市值'] / 1e8:.2f} 亿")
    print(f"  流通市值:   {s['流通市值'] / 1e8:.2f} 亿")


def cmd_financials(code: str):
    """近5年核心财务数据。"""
    code_clean = code.strip().replace(".SH", "").replace(".SZ", "").replace(".BJ", "")
    market = "SH" if code_clean.startswith(("6", "9", "5")) else "SZ"
    symbol = f"{code_clean}.{market}"

    df = ak.stock_financial_analysis_indicator_em(symbol=symbol, indicator="按报告期")
    if df is None or df.empty:
        print(f"❌ 未获取到 {code_clean} 的财务数据")
        return

    # 筛选年报
    annual = df[df["REPORT_DATE_NAME"].str.contains("年年报", na=False)]
    if annual.empty:
        annual = df  # 如果没有年报，用全部数据

    # 取近5年
    recent = annual.head(5)

    # 获取名称
    spot_df = ak.stock_zh_a_spot_em()
    name_row = spot_df[spot_df["代码"] == code_clean]
    name = name_row.iloc[0]["名称"] if not name_row.empty else code_clean

    print("=" * 60)
    print(f"核心财务数据: {name} ({code_clean})")
    print("=" * 60)

    for _, row in recent.iterrows():
        date = str(row.get("REPORT_DATE", ""))[:10]
        report_name = row.get("REPORT_DATE_NAME", "")
        print(f"\n  --- {date} {report_name} ---")
        rev = row.get("TOTALOPERATEREVE")
        print(f"  营收:           {rev / 1e8:.2f}亿" if pd.notna(rev) else "  营收:           -")
        rev_g = row.get("TOTALOPERATEREVETZ")
        print(f"  营收增速:       {_fmt_pct(rev_g)}" if pd.notna(rev_g) else "  营收增速:       -")
        profit = row.get("PARENTNETPROFIT")
        print(f"  归母净利润:     {profit / 1e8:.2f}亿" if pd.notna(profit) else "  归母净利润:     -")
        profit_g = row.get("PARENTNETPROFITTZ")
        print(f"  净利润增速:     {_fmt_pct(profit_g)}" if pd.notna(profit_g) else "  净利润增速:     -")
        eps = row.get("EPSJB")
        print(f"  基本每股收益:   {eps}" if pd.notna(eps) else "  基本每股收益:   -")
        bps = row.get("BPS")
        print(f"  每股净资产:     {bps:.2f}" if pd.notna(bps) else "  每股净资产:     -")
        roe = row.get("ROEJQ")
        print(f"  ROE(加权):      {_fmt_pct(roe)}" if pd.notna(roe) else "  ROE(加权):      -")


def cmd_search(keyword: str):
    """搜索股票代码。"""
    all_stocks = ak.stock_info_a_code_name()
    matches = all_stocks[all_stocks["name"].str.contains(keyword, na=False)]

    if matches.empty:
        print(f"❌ 未找到匹配 '{keyword}' 的股票")
        return

    print("=" * 60)
    print(f"搜索结果: '{keyword}'")
    print("=" * 60)
    for _, row in matches.head(10).iterrows():
        code = row["code"]
        name = row["name"]
        market = "沪" if code.startswith(("6", "9", "5")) else ("深" if code.startswith(("0", "3", "2")) else "北")
        print(f"  {code} {name} [{market}]")


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="A股数据工具 — AKShare 行情/财务/搜索",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    p_quote = sub.add_parser("quote", help="实时行情")
    p_quote.add_argument("code", help="股票代码，如 600519")

    p_fin = sub.add_parser("financials", help="核心财务数据（近5年）")
    p_fin.add_argument("code", help="股票代码")

    p_val = sub.add_parser("valuation", help="估值指标")
    p_val.add_argument("code", help="股票代码")

    p_search = sub.add_parser("search", help="搜索股票代码")
    p_search.add_argument("keyword", help="公司名或关键词")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    cmds = {
        "quote": lambda: cmd_quote(args.code),
        "financials": lambda: cmd_financials(args.code),
        "valuation": lambda: cmd_valuation(args.code),
        "search": lambda: cmd_search(args.keyword),
    }
    cmds[args.command]()


if __name__ == "__main__":
    main()
