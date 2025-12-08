# monitor_stock_gui.py
import sys
import os
import csv
import time
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from tkinter import font as tkfont
from PIL import Image, ImageTk
import requests
from io import BytesIO

# 如果 day_index 在上层目录，保持导入
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from day_index import init_create_client, get_price_and_change_percent


class StockMonitorGUI:
	def __init__(self, root):
		self.root = root
		self.root.title("股票实时监控系统")
		self.root.geometry("1000x600")
		
		# 设置窗口图标
		self.set_window_icon()
		
		# 股票数据列表
		self.stock_data = []
		self.stock_widgets = []  # 存储股票行的小部件
		
		# 监控状态
		self.monitoring = False
		self.monitor_thread = None
		
		# 颜色定义
		self.colors = {
			'up': '#e74c3c',  # 红色 - 上涨
			'down': '#2ecc71',  # 绿色 - 下跌
			'neutral': '#7f8c8d',  # 灰色 - 平盘
			'bg': '#2c3e50',  # 深蓝背景
			'card_bg': '#34495e',  # 卡片背景
			'text': '#ecf0f1',  # 浅色文字
			'header': '#3498db',  # 蓝色标题
		}
		
		# 设置窗口背景
		self.root.configure(bg=self.colors['bg'])
		
		# 加载自定义字体
		self.setup_fonts()
		
		# 创建界面
		self.create_widgets()
		
		# 加载股票数据
		self.load_stock_data()
		
		# 窗口关闭事件
		self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
	
	def set_window_icon(self):
		"""设置窗口图标"""
		try:
			# 从网络加载一个股票相关的图标
			icon_url = "https://cdn-icons-png.flaticon.com/512/3079/3079165.png"
			response = requests.get(icon_url, timeout=5)
			img_data = response.content
			image = Image.open(BytesIO(img_data))
			photo = ImageTk.PhotoImage(image)
			self.root.iconphoto(False, photo)
		except:
			# 如果网络图标加载失败，使用默认图标
			pass
	
	def setup_fonts(self):
		"""设置字体"""
		self.title_font = tkfont.Font(family="Microsoft YaHei", size=16, weight="bold")
		self.normal_font = tkfont.Font(family="Microsoft YaHei", size=10)
		self.bold_font = tkfont.Font(family="Microsoft YaHei", size=10, weight="bold")
		self.large_font = tkfont.Font(family="Microsoft YaHei", size=12, weight="bold")
	
	def create_widgets(self):
		"""创建界面组件"""
		# 主框架
		main_frame = tk.Frame(self.root, bg=self.colors['bg'])
		main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
		
		# 标题区域
		title_frame = tk.Frame(main_frame, bg=self.colors['bg'])
		title_frame.pack(fill=tk.X, pady=(0, 10))
		
		tk.Label(
			title_frame,
			text="📈 股票实时监控系统",
			font=self.title_font,
			bg=self.colors['bg'],
			fg=self.colors['text']
		).pack(side=tk.LEFT)
		
		# 控制面板
		control_frame = tk.Frame(main_frame, bg=self.colors['card_bg'], bd=0, relief=tk.RAISED)
		control_frame.pack(fill=tk.X, pady=(0, 10), ipadx=10, ipady=5)
		
		# 控制按钮
		button_frame = tk.Frame(control_frame, bg=self.colors['card_bg'])
		button_frame.pack(side=tk.LEFT, padx=10)
		
		self.start_btn = tk.Button(
			button_frame,
			text="▶ 开始监控",
			command=self.start_monitoring,
			bg="#27ae60",
			fg="white",
			font=self.bold_font,
			padx=20,
			pady=5,
			bd=0,
			cursor="hand2"
		)
		self.start_btn.pack(side=tk.LEFT, padx=5)
		
		self.stop_btn = tk.Button(
			button_frame,
			text="⏸ 停止监控",
			command=self.stop_monitoring,
			bg="#e74c3c",
			fg="white",
			font=self.bold_font,
			padx=20,
			pady=5,
			bd=0,
			state=tk.DISABLED,
			cursor="hand2"
		)
		self.stop_btn.pack(side=tk.LEFT, padx=5)
		
		self.refresh_btn = tk.Button(
			button_frame,
			text="🔄 手动刷新",
			command=self.manual_refresh,
			bg="#3498db",
			fg="white",
			font=self.bold_font,
			padx=20,
			pady=5,
			bd=0,
			cursor="hand2"
		)
		self.refresh_btn.pack(side=tk.LEFT, padx=5)
		
		# 状态显示
		status_frame = tk.Frame(control_frame, bg=self.colors['card_bg'])
		status_frame.pack(side=tk.RIGHT, padx=10)
		
		self.status_label = tk.Label(
			status_frame,
			text="状态: 就绪",
			font=self.normal_font,
			bg=self.colors['card_bg'],
			fg=self.colors['text']
		)
		self.status_label.pack(side=tk.LEFT, padx=5)
		
		self.time_label = tk.Label(
			status_frame,
			text="最后更新: --:--:--",
			font=self.normal_font,
			bg=self.colors['card_bg'],
			fg=self.colors['text']
		)
		self.time_label.pack(side=tk.LEFT, padx=20)
		
		# 股票表格标题
		header_frame = tk.Frame(main_frame, bg=self.colors['header'])
		header_frame.pack(fill=tk.X, pady=(0, 5))
		
		headers = ["股票代码", "股票名称", "当前价格", "涨跌幅", "更新时间"]
		widths = [150, 200, 150, 150, 200]
		
		for i, (header, width) in enumerate(zip(headers, widths)):
			tk.Label(
				header_frame,
				text=header,
				font=self.bold_font,
				bg=self.colors['header'],
				fg="white",
				width=width // 10
			).pack(side=tk.LEFT, padx=2, ipady=5)
		
		# 股票数据显示区域（带滚动条）
		table_frame = tk.Frame(main_frame, bg=self.colors['bg'])
		table_frame.pack(fill=tk.BOTH, expand=True)
		
		# 创建Canvas和滚动条
		self.canvas = tk.Canvas(table_frame, bg=self.colors['bg'], highlightthickness=0)
		scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.canvas.yview)
		
		# 股票行容器
		self.stock_container = tk.Frame(self.canvas, bg=self.colors['bg'])
		self.stock_container.bind(
			"<Configure>",
			lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
		)
		
		# 将容器添加到Canvas
		self.canvas_window = self.canvas.create_window((0, 0), window=self.stock_container, anchor="nw")
		self.canvas.configure(yscrollcommand=scrollbar.set)
		
		# 绑定鼠标滚轮事件
		self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
		
		# 布局Canvas和滚动条
		self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
		scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
		
		# 股票计数
		self.count_label = tk.Label(
			main_frame,
			text="监控股票数量: 0",
			font=self.normal_font,
			bg=self.colors['bg'],
			fg=self.colors['text']
		)
		self.count_label.pack(side=tk.LEFT, pady=5)
		
		# 初始化Tkinter客户端
		self.client = init_create_client()
		
		# 启动定时器更新界面
		self.update_time()
	
	def _on_mousewheel(self, event):
		"""处理鼠标滚轮事件"""
		self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
	
	def load_stock_data(self):
		"""从CSV文件加载股票数据"""
		csv_file = "config.csv"
		if not os.path.exists(csv_file):
			messagebox.showerror("错误", f"找不到配置文件: {csv_file}")
			return
		
		try:
			with open(csv_file, 'r', newline='', encoding='utf-8') as file:
				reader = csv.DictReader(file)
				for row in reader:
					if row.get('code') and row.get('name'):
						self.stock_data.append((row['code'], row['name']))
			
			self.update_stock_count()
			self.create_stock_rows()
		
		except Exception as e:
			messagebox.showerror("错误", f"读取CSV文件时出错: {str(e)}")
	
	def create_stock_rows(self):
		"""创建股票显示行"""
		# 清除现有行
		for widget in self.stock_widgets:
			widget.destroy()
		self.stock_widgets.clear()
		
		# 创建新行
		for i, (code, name) in enumerate(self.stock_data):
			row_frame = tk.Frame(self.stock_container, bg=self.colors['bg'])
			row_frame.pack(fill=tk.X, pady=2)
			
			# 代码标签
			code_label = tk.Label(
				row_frame,
				text=code,
				font=self.bold_font,
				bg=self.colors['bg'],
				fg=self.colors['text'],
				width=20,
				anchor="w"
			)
			code_label.pack(side=tk.LEFT, padx=2)
			
			# 名称标签
			name_label = tk.Label(
				row_frame,
				text=name,
				font=self.normal_font,
				bg=self.colors['bg'],
				fg=self.colors['text'],
				width=25,
				anchor="w"
			)
			name_label.pack(side=tk.LEFT, padx=2)
			
			# 价格标签
			price_label = tk.Label(
				row_frame,
				text="--",
				font=self.large_font,
				bg=self.colors['bg'],
				fg=self.colors['text'],
				width=20
			)
			price_label.pack(side=tk.LEFT, padx=2)
			
			# 涨跌幅标签
			change_label = tk.Label(
				row_frame,
				text="--",
				font=self.large_font,
				bg=self.colors['bg'],
				fg=self.colors['neutral'],
				width=20
			)
			change_label.pack(side=tk.LEFT, padx=2)
			
			# 更新时间标签
			time_label = tk.Label(
				row_frame,
				text="--:--:--",
				font=self.normal_font,
				bg=self.colors['bg'],
				fg=self.colors['text'],
				width=25
			)
			time_label.pack(side=tk.LEFT, padx=2)
			
			# 存储小部件引用
			self.stock_widgets.append({
				'frame': row_frame,
				'code': code_label,
				'name': name_label,
				'price': price_label,
				'change': change_label,
				'time': time_label,
				'data': (code, name)
			})
	
	def update_stock_count(self):
		"""更新股票计数"""
		self.count_label.config(text=f"监控股票数量: {len(self.stock_data)}")
	
	def start_monitoring(self):
		"""开始监控"""
		if not self.stock_data:
			messagebox.showwarning("警告", "没有可监控的股票数据")
			return
		
		if self.monitoring:
			return
		
		self.monitoring = True
		self.start_btn.config(state=tk.DISABLED)
		self.stop_btn.config(state=tk.NORMAL)
		self.status_label.config(text="状态: 监控中...")
		
		# 启动监控线程
		self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
		self.monitor_thread.start()
	
	def stop_monitoring(self):
		"""停止监控"""
		self.monitoring = False
		self.start_btn.config(state=tk.NORMAL)
		self.stop_btn.config(state=tk.DISABLED)
		self.status_label.config(text="状态: 已停止")
	
	def manual_refresh(self):
		"""手动刷新"""
		if not self.stock_data:
			return
		
		# 在单独的线程中刷新，避免界面卡顿
		refresh_thread = threading.Thread(target=self.refresh_stock_data, daemon=True)
		refresh_thread.start()
	
	def refresh_stock_data(self):
		"""刷新股票数据"""
		try:
			for widget in self.stock_widgets:
				code, name = widget['data']
				try:
					price, change = get_price_and_change_percent(code, self.client)
					self.update_stock_row(widget, price, change)
				except Exception as e:
					self.update_stock_row_error(widget, str(e))
			
			self.update_time_label()
		
		except Exception as e:
			# 在主线程中显示错误
			self.root.after(0, lambda: messagebox.showerror("错误", f"刷新数据时出错: {str(e)}"))
	
	def monitor_loop(self):
		"""监控循环"""
		interval = 2  # 2秒间隔
		
		while self.monitoring:
			try:
				for widget in self.stock_widgets:
					if not self.monitoring:
						break
					
					code, name = widget['data']
					try:
						price, change = get_price_and_change_percent(code, self.client)
						# 在主线程中更新界面
						self.root.after(0, self.update_stock_row, widget, price, change)
					except Exception as e:
						self.root.after(0, self.update_stock_row_error, widget, str(e))
				
				# 更新时间
				self.root.after(0, self.update_time_label)
				
				# 等待间隔
				for _ in range(interval * 10):  # 每秒检查10次，以便及时响应停止
					if not self.monitoring:
						break
					time.sleep(0.1)
			
			except Exception as e:
				self.root.after(0, lambda: messagebox.showerror("错误", f"监控过程中出错: {str(e)}"))
				break
	
	def update_stock_row(self, widget, price, change):
		"""更新股票行数据"""
		# 更新价格
		widget['price'].config(text=f"{price:.2f}")
		
		# 更新涨跌幅，设置颜色
		change_text = f"{change:+.2f}%"
		if change > 0:
			color = self.colors['up']
			change_text = f"▲ {change_text}"
		elif change < 0:
			color = self.colors['down']
			change_text = f"▼ {change_text}"
		else:
			color = self.colors['neutral']
			change_text = f"→ {change_text}"
		
		widget['change'].config(text=change_text, fg=color)
		
		# 更新时间
		current_time = datetime.now().strftime("%H:%M:%S")
		widget['time'].config(text=current_time)
	
	def update_stock_row_error(self, widget, error_msg):
		"""更新股票行错误信息"""
		widget['price'].config(text="错误")
		widget['change'].config(text=error_msg[:15], fg=self.colors['neutral'])
		
		current_time = datetime.now().strftime("%H:%M:%S")
		widget['time'].config(text=current_time)
	
	def update_time_label(self):
		"""更新时间标签"""
		current_time = datetime.now().strftime("%H:%M:%S")
		self.time_label.config(text=f"最后更新: {current_time}")
	
	def update_time(self):
		"""更新时间显示（每秒更新一次）"""
		current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		self.root.after(1000, self.update_time)
	
	def on_closing(self):
		"""窗口关闭事件"""
		self.monitoring = False
		if self.monitor_thread:
			self.monitor_thread.join(timeout=1)
		self.root.destroy()


def read_stock_data_from_csv(file_path):
	"""
	从CSV文件读取股票代码和名称

	参数:
		file_path: CSV文件路径

	返回:
		list: 包含 (code, name) 元组的列表
	"""
	stock_data = []
	try:
		with open(file_path, 'r', newline='', encoding='utf-8') as file:
			reader = csv.DictReader(file)
			for row in reader:
				if row.get('code') and row.get('name'):
					stock_data.append((row['code'], row['name']))
		return stock_data
	except FileNotFoundError:
		print(f"错误: 找不到文件 {file_path}")
		return []
	except Exception as e:
		print(f"读取CSV文件时出错: {e}")
		return []


def main():
	"""主函数"""
	# 从CSV文件读取股票数据
	csv_file = "config.csv"
	stock_data = read_stock_data_from_csv(csv_file)
	
	if not stock_data:
		print("未找到有效的股票数据，程序退出")
		return
	
	# 创建主窗口
	root = tk.Tk()
	
	# 设置窗口样式
	try:
		# 尝试使用更现代的样式
		style = ttk.Style()
		style.theme_use('clam')
	except:
		pass
	
	# 创建应用实例
	app = StockMonitorGUI(root)
	
	# 运行主循环
	root.mainloop()


if __name__ == "__main__":
	main()