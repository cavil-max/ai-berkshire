#!/usr/bin/env python3
"""A股数据工具 — 基于 AKShare 的行情、财务、搜索工具。

为 Skills 提供 A 股实时行情、财务数据等数据。
使用 AKShare 封装新浪/东方财富数据源，优先新浪（更稳定），东方财富作为 fallback。

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


def _fmt_yi(value) -> str:
    """格式化为亿元。"""
    if value is None or pd.isna(value):
        return "-"
    try:
        return f"{float(value) / 1e8:.2f}亿"
    except (ValueError, TypeError):
        return "-"


def _to_sina_symbol(code: str) -> str:
    """转为新浪格式：sh600519 / sz000001。"""
    code = code.strip().replace(".SH", "").replace(".SZ", "").replace(".BJ", "")
    if code.startswith(("6", "9", "5")):
        return f"sh{code}"
    return f"sz{code}"


# ---------------------------------------------------------------------------
# 实时行情（Sina 主，EastMoney fallback）
# ---------------------------------------------------------------------------


def _quote_sina(code: str) -> dict | None:
    """从新浪获取实时行情。"""
    sina_sym = _to_sina_symbol(code)
    df = ak.stock_zh_a_spot()
    row = df[df["代码"] == sina_sym]
    if row.empty:
        return None
    s = row.iloc[0]
    return {
        "name": s["名称"],
        "price": s["最新价"],
        "change_pct": s["涨跌幅"],
        "change": s["涨跌额"],
        "open": s["今开"],
        "high": s["最高"],
        "low": s["最低"],
        "prev_close": s["昨收"],
        "volume": s["成交量"],
        "amount": s["成交额"],
    }


def _quote_em(code: str) -> dict | None:
    """从东方财富获取实时行情（含 PE/PB/市值）。"""
    df = ak.stock_zh_a_spot_em()
    row = df[df["代码"] == code]
    if row.empty:
        return None
    s = row.iloc[0]
    return {
        "name": s["名称"],
        "price": s["最新价"],
        "change_pct": s["涨跌幅"],
        "change": s["涨跌额"],
        "open": s["今开"],
        "high": s["最高"],
        "low": s["最低"],
        "prev_close": s["昨收"],
        "volume": s["成交量"],
        "amount": s["成交额"],
        "turnover": s.get("换手率"),
        "pe": s.get("市盈率-动态"),
        "pb": s.get("市净率"),
        "market_cap": s.get("总市值"),
        "circ_market_cap": s.get("流通市值"),
    }


def cmd_quote(code: str):
    """实时行情。优先东方财富（含 PE/PB/市值），失败回退新浪。"""
    code = code.strip().replace(".SH", "").replace(".SZ", "").replace(".BJ", "")

    # 优先东方财富（数据更全）
    try:
        data = _quote_em(code)
        if data:
            print("=" * 60)
            print(f"实时行情: {data['name']} ({code})")
            print("=" * 60)
            print(f"  当前价:     {data['price']}")
            print(f"  涨跌幅:     {data['change_pct']}%")
            print(f"  涨跌额:     {data['change']}")
            print(f"  今开:       {data['open']}")
            print(f"  最高:       {data['high']}")
            print(f"  最低:       {data['low']}")
            print(f"  昨收:       {data['prev_close']}")
            print(f"  成交量:     {data['volume']} 手")
            print(f"  成交额:     {float(data['amount']) / 1e8:.2f} 亿")
            if data.get("turnover") is not None:
                print(f"  换手率:     {data['turnover']}%")
            if data.get("pe") is not None:
                print(f"  PE(动):     {data['pe']}")
            if data.get("pb") is not None:
                print(f"  PB:         {data['pb']}")
            if data.get("market_cap") is not None:
                print(f"  总市值:     {float(data['market_cap']) / 1e8:.2f} 亿")
            if data.get("circ_market_cap") is not None:
                print(f"  流通市值:   {float(data['circ_market_cap']) / 1e8:.2f} 亿")
            return
    except Exception:
        pass  # 东方财富不可用，回退新浪

    # 回退新浪
    try:
        data = _quote_sina(code)
    except Exception as e:
        print(f"❌ 行情获取失败: {e}")
        return

    if not data:
        print(f"❌ 未找到股票代码 {code}")
        return

    print("=" * 60)
    print(f"实时行情: {data['name']} ({code}) [新浪]")
    print("=" * 60)
    print(f"  当前价:     {data['price']}")
    print(f"  涨跌幅:     {data['change_pct']}%")
    print(f"  涨跌额:     {data['change']}")
    print(f"  今开:       {data['open']}")
    print(f"  最高:       {data['high']}")
    print(f"  最低:       {data['low']}")
    print(f"  昨收:       {data['prev_close']}")
    print(f"  成交量:     {data['volume']} 手")
    print(f"  成交额:     {float(data['amount']) / 1e8:.2f} 亿")
    print(f"  (PE/PB/市值需用 valuation 命令获取)")


# ---------------------------------------------------------------------------
# 估值指标（东方财富主，Sina fallback 无 PE/PB）
# ---------------------------------------------------------------------------


def cmd_valuation(code: str):
    """估值指标。优先东方财富，失败时用新浪行情+计算。"""
    code = code.strip().replace(".SH", "").replace(".SZ", "").replace(".BJ", "")

    try:
        data = _quote_em(code)
        if data and data.get("pe") is not None:
            print("=" * 60)
            print(f"估值指标: {data['name']} ({code})")
            print("=" * 60)
            print(f"  PE(动态):   {data['pe']}")
            print(f"  PB:         {data['pb']}")
            print(f"  总市值:     {float(data['market_cap']) / 1e8:.2f} 亿")
            print(f"  流通市值:   {float(data['circ_market_cap']) / 1e8:.2f} 亿")
            return
    except Exception:
        pass

    # 东方财富不可用
    print(f"⚠️ 东方财富数据不可用，无法获取 {code} 的估值指标（PE/PB/市值）。")
    print(f"   可用 quote 命令获取基本行情，或通过 WebSearch 补充估值数据。")


# ---------------------------------------------------------------------------
# 财务数据（Sina 主，EastMoney fallback）
# ---------------------------------------------------------------------------


def _financials_sina(code: str) -> list[dict] | None:
    """从新浪获取利润表数据。"""
    sina_sym = _to_sina_symbol(code)
    try:
        df = ak.stock_financial_report_sina(stock=sina_sym, symbol="利润表")
        if df is None or df.empty:
            return None
        # 筛选年报（报告日以 12-31 结尾）
        df = df[df["报告日"].str.endswith("12-31", na=False)]
        results = []
        for _, row in df.head(5).iterrows():
            results.append({
                "date": str(row.get("报告日", "")),
                "revenue": row.get("一、营业总收入") or row.get("营业总收入"),
                "net_profit": row.get("净利润"),
            })
        return results
    except Exception:
        return None


def _financials_em(code: str) -> list[dict] | None:
    """从东方财富获取财务指标。"""
    code_clean = code.strip().replace(".SH", "").replace(".SZ", "").replace(".BJ", "")
    market = "SH" if code_clean.startswith(("6", "9", "5")) else "SZ"
    symbol = f"{code_clean}.{market}"
    try:
        df = ak.stock_financial_analysis_indicator_em(symbol=symbol, indicator="按报告期")
        if df is None or df.empty:
            return None
        annual = df[df["REPORT_DATE_NAME"].str.contains("年年报", na=False)]
        if annual.empty:
            annual = df
        results = []
        for _, row in annual.head(5).iterrows():
            results.append({
                "date": str(row.get("REPORT_DATE", ""))[:10],
                "report_name": row.get("REPORT_DATE_NAME", ""),
                "revenue": row.get("TOTALOPERATEREVE"),
                "rev_growth": row.get("TOTALOPERATEREVETZ"),
                "net_profit": row.get("PARENTNETPROFIT"),
                "profit_growth": row.get("PARENTNETPROFITTZ"),
                "eps": row.get("EPSJB"),
                "bps": row.get("BPS"),
                "roe": row.get("ROEJQ"),
            })
        return results
    except Exception:
        return None


def cmd_financials(code: str):
    """近5年核心财务数据。优先东方财富（数据更全），失败回退新浪。"""
    code_clean = code.strip().replace(".SH", "").replace(".SZ", "").replace(".BJ", "")

    # 优先东方财富
    data = _financials_em(code_clean)
    if data:
        # 获取名称
        name = code_clean
        try:
            spot = _quote_em(code_clean)
            if spot:
                name = spot["name"]
        except Exception:
            pass

        print("=" * 60)
        print(f"核心财务数据: {name} ({code_clean})")
        print("=" * 60)
        for row in data:
            print(f"\n  --- {row['date']} {row.get('report_name', '')} ---")
            print(f"  营收:           {_fmt_yi(row.get('revenue'))}")
            print(f"  营收增速:       {_fmt_pct(row.get('rev_growth'))}")
            print(f"  归母净利润:     {_fmt_yi(row.get('net_profit'))}")
            print(f"  净利润增速:     {_fmt_pct(row.get('profit_growth'))}")
            eps = row.get("eps")
            print(f"  基本每股收益:   {eps}" if eps is not None else "  基本每股收益:   -")
            bps = row.get("bps")
            print(f"  每股净资产:     {bps:.2f}" if bps is not None else "  每股净资产:     -")
            print(f"  ROE(加权):      {_fmt_pct(row.get('roe'))}")
        return

    # 回退新浪
    print("  [INFO] 东方财富不可用，使用新浪数据源...")
    data = _financials_sina(code_clean)
    if not data:
        print(f"❌ 未获取到 {code_clean} 的财务数据")
        return

    # 获取名称
    name = code_clean
    try:
        spot = _quote_sina(code_clean)
        if spot:
            name = spot["name"]
    except Exception:
        pass

    print("=" * 60)
    print(f"核心财务数据: {name} ({code_clean}) [新浪]")
    print("=" * 60)
    for row in data:
        print(f"\n  --- {row['date']} ---")
        print(f"  营业总收入:     {_fmt_yi(row.get('revenue'))}")
        print(f"  净利润:         {_fmt_yi(row.get('net_profit'))}")
    print("\n  ⚠️ 新浪数据源仅提供营收和净利润，完整指标需东方财富数据源。")


# ---------------------------------------------------------------------------
# 股票搜索
# ---------------------------------------------------------------------------


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