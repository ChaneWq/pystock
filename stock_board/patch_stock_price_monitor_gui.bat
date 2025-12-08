@echo off
chcp 65001 > nul
echo 正在运行Python脚本...
d:
cd D:\wu\pystock\stock_board
python patch_stock_price_monitor_gui.py
pause