# -*- coding: utf-8 -*-
"""路径与常量（P11b 拆分，逐字节搬运）。"""
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # boardlib/ 的上级=项目根
DB = os.path.join(BASE, "data", "board.db")
OUT = os.path.join(BASE, "board.html")

IDX = {
    "sh000001": "上证指数", "sz399001": "深证成指", "sz399006": "创业板指",
    "sh000688": "科创50", "sh000300": "沪深300",
}

