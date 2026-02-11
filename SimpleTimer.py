import sys
import os
import json
import threading
import time
import datetime
import warnings
import math

warnings.filterwarnings("ignore", category=DeprecationWarning, message="sipPyTypeDict")

from pathlib import Path
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtMultimedia import QSound

# 新增：导入Windows任务栏相关模块
try:
    from PyQt5.QtWinExtras import QWinTaskbarButton, QWinTaskbarProgress
    HAS_WIN_EXTRAS = True
except ImportError:
    HAS_WIN_EXTRAS = False
    print("警告: PyQt5.QtWinExtras 不可用，Windows任务栏进度条功能将不可用")

from PyQt5.QtGui import QIcon, QColor
from datetime import datetime

class ProjectInfo:
    """项目信息元数据（集中管理所有项目相关信息）"""
    VERSION = "2.11.0"
    BUILD_DATE = "2026-06-28"
    from datetime import datetime
    # BUILD_DATE = datetime.now().strftime("%Y-%m-%d")  # 修改为动态获取当前日期
    AUTHOR = "杜玛"
    LICENSE = "MIT"
    COPYRIGHT = "© 永久 杜玛"
    URL = "https://github.com/duma520"
    MAINTAINER_EMAIL = "不提供"
    NAME = "多功能计时器"
    DESCRIPTION = """多功能计时器
主要功能：
1. 计时器功能：正向计时，无限制计时
2. 倒计时功能：设置特定时间进行倒计时
3. 预设功能：常用时间预设，支持自定义预设
4. 多种提醒方式：窗口抖动、窗口闪烁、任务栏闪烁、系统通知等
5. 系统托盘支持：最小化到托盘运行
6. Windows任务栏进度条：显示计时/倒计时进度
7. 自定义铃声：支持多种音频格式
8. 状态颜色指示：不同状态（运行/暂停/停止）使用不同颜色显示
9. 纯时间显示窗口：点击时间标签弹出全屏时间显示窗口，带防烧屏保护
"""

    VERSION_HISTORY = {
        "1.0": "初始化版本 - 基础计时器和倒计时功能",
        "1.1": "修改最小化到托盘的默认情况",
        "1.2": "任务栏进度条问题未解决",
        "2.0": "解决任务栏进度问题",
        "2.1": "解决启动时候就托盘的问题",
        "2.2": "解决90%问题",
        "2.3": "增加多种提醒方式（窗口抖动、窗口闪烁、任务栏闪烁、醒目对话框）",
        "2.4": "解决自定义声音问题，支持更多音频格式",
        "2.5": "解决默认WAV播放问题，优化音频播放器",
        "2.6": "倒计时标签变色功能 - 不同状态显示不同颜色",
        "2.7": "计时器时间标签变色功能 - 统一状态颜色指示",
        "2.8": "修复自定义声音选择问题，优化文件格式验证",
        "2.9": "完善项目信息元数据，增加详细版本历史",
        "2.9.1": "增加关于对话框详细信息，优化用户界面和交互体验",
        "2.10.0": "增加纯时间显示窗口功能，带防烧屏保护和自适应缩放",
        "2.10.1": "优化纯时间显示窗口的防烧屏保护功能，增加更多自定义选项",
        "2.11.0": "优化纯时间显示窗口的字体自适应缩放，提升用户体验"
    }

    HELP_TEXT = """
基本操作指南：

计时器功能：
1. 点击"开始计时"按钮开始正向计时
2. 点击"暂停"按钮暂停计时，再次点击继续
3. 点击"重置"按钮将计时器归零

倒计时功能：
1. 通过小时、分钟、秒数设置倒计时时间
2. 点击"开始倒计时"按钮开始倒计时
3. 使用快速设置按钮快速设置常用时间
4. 最近使用的计时器会自动保存方便下次使用

预设功能：
1. 使用预设的时间快速开始倒计时
2. 可以添加自定义预设名称和时间
3. 预设支持2小时和3小时等长时间设置

提醒设置：
1. 支持多种提醒方式：窗口抖动、窗口闪烁、任务栏闪烁、醒目对话框
2. 可单独开启或关闭各种提醒方式
3.使用"测试提醒效果"按钮预览提醒效果

声音设置：
1. 支持音量调节和静音功能
2. 支持自定义铃声（WAV、MP3、OGG、FLAC、AAC、M4A格式）
3. 使用"测试声音"按钮测试当前铃声

窗口设置：
1. 支持窗口置顶功能
2. 支持最小化到系统托盘运行
3. Windows任务栏显示计时进度条

纯时间显示窗口：
1. 点击计时器或倒计时的显示时间标签可弹出纯时间显示窗口
2. 窗口字体大小随窗口尺寸自动缩放
3. 支持拖拽到其他屏幕显示
4. 支持最大化、全屏显示
5. 内置防烧屏保护功能（像素移动、亮度调节、屏幕保护）
6. 右键菜单提供各种控制选项

系统托盘：
1. 启用"最小化到托盘"后，最小化窗口会隐藏到系统托盘
2. 双击托盘图标恢复窗口显示
3. 右键托盘图标可进行相关操作

任务栏进度条（仅Windows）：
1. 计时器运行时显示不确定模式进度条
2. 倒计时运行时显示确定模式进度条，显示剩余时间百分比
3. 暂停时显示黄色暂停状态
4. 完成时显示100%完成状态
"""

    @classmethod
    def get_metadata(cls) -> dict:
        """获取主要元数据字典"""
        return {
            'name': cls.NAME,
            'version': cls.VERSION,
            'build_date': cls.BUILD_DATE,
            'author': cls.AUTHOR,
            'license': cls.LICENSE,
            'copyright': cls.COPYRIGHT,
            'url': cls.URL,
            'maintainer_email': cls.MAINTAINER_EMAIL
        }

    @classmethod
    def get_header(cls) -> str:
        """生成标准化的项目头信息"""
        return f"{cls.NAME} v{cls.VERSION} | {cls.LICENSE} License | {cls.URL}"

    @classmethod
    def get_about_info(cls):
        """获取ABOUT信息字典"""
        return {
            "name": cls.NAME,
            "version": cls.VERSION,
            "build_date": cls.BUILD_DATE,
            "author": cls.AUTHOR,
            "license": cls.LICENSE,
            "copyright": cls.COPYRIGHT,
            "url": cls.URL,
            "maintainer_email": cls.MAINTAINER_EMAIL,
            "description": cls.DESCRIPTION,
            "features": [
                "计时器功能 - 正向无限计时",
                "倒计时功能 - 可设置具体时间",
                "多种提醒方式 - 窗口抖动、闪烁、任务栏闪烁等",
                "系统托盘支持 - 最小化到托盘运行",
                "Windows任务栏进度条 - 显示计时进度",
                "自定义铃声 - 支持多种音频格式",
                "状态颜色指示 - 运行/暂停/停止不同颜色",
                "预设功能 - 常用时间预设和自定义预设",
                "纯时间显示窗口 - 全屏时间显示，带防烧屏保护"
            ],
            "system_requirements": [
                "操作系统: Windows 7/8/10/11, Linux, macOS",
                "Python: 3.6 或更高版本",
                "PyQt5: 5.15 或更高版本",
                "音频支持: 需要系统音频编解码器支持"
            ],
            "version_history": cls.VERSION_HISTORY,
            "help_text": cls.HELP_TEXT
        }

    @classmethod
    def show_about_dialog(cls, parent=None):
        """显示关于对话框"""
        from PyQt5.QtWidgets import QMessageBox, QTextBrowser
        from PyQt5.QtCore import Qt
        
        about_text = f"""
{cls.get_header()}

{cls.DESCRIPTION}

版本历史：
"""
        for version, desc in cls.VERSION_HISTORY.items():
            about_text += f"\n• v{version}: {desc}"
        
        about_text += f"\n\n主要功能："
        for i, feature in enumerate(cls.get_about_info()["features"], 1):
            about_text += f"\n{i}. {feature}"
        
        about_text += f"\n\n系统要求："
        for req in cls.get_about_info()["system_requirements"]:
            about_text += f"\n• {req}"
        
        about_text += f"\n\n{cls.COPYRIGHT}"
        
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle(f"关于 {cls.NAME}")
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setText(f"<h2>{cls.NAME} v{cls.VERSION}</h2>")
        msg_box.setInformativeText(f"""
<p><b>作者：</b>{cls.AUTHOR}</p>
<p><b>许可证：</b>{cls.LICENSE}</p>
<p><b>构建日期：</b>{cls.BUILD_DATE}</p>
<p><b>项目地址：</b><a href="{cls.URL}">{cls.URL}</a></p>
""")
        
        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(True)
        text_browser.setHtml(f"<pre>{about_text}</pre>")
        text_browser.setMinimumSize(600, 400)
        
        msg_box.layout().addWidget(text_browser, 1, 0, 1, msg_box.layout().columnCount())
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()

# 新增：纯时间显示窗口类
class TimeDisplayWindow(QMainWindow):
    """纯时间显示窗口，带防烧屏保护和自适应缩放"""
    
    def __init__(self, parent=None, timer_type='timer', initial_time='00:00:00'):
        super().__init__(parent)
        self.parent_timer = parent
        self.timer_type = timer_type  # 'timer' 或 'countdown'
        self.current_time = initial_time
        
        # 防烧屏相关设置
        self.burn_in_protection_enabled = True
        self.pixel_shift_interval = 300  # 像素移动间隔（秒）
        self.pixel_shift_distance = 2    # 像素移动距离（像素）
        self.brightness_reduction = 0.85 # 亮度减少比例
        self.screensaver_timeout = 600   # 屏幕保护启动时间（秒）
        
        # 状态变量
        self.last_pixel_shift_time = time.time()
        self.last_activity_time = time.time()
        self.pixel_shift_x = 0
        self.pixel_shift_y = 0
        self.is_screensaver_active = False
        self.is_fullscreen = False
        self.original_brightness = 1.0
        
        # 屏幕保护定时器
        self.screensaver_timer = QTimer(self)
        self.screensaver_timer.timeout.connect(self.check_screensaver)
        self.screensaver_timer.start(1000)  # 每秒检查一次
        
        # 像素移动定时器
        self.pixel_shift_timer = QTimer(self)
        self.pixel_shift_timer.timeout.connect(self.apply_pixel_shift)
        if self.burn_in_protection_enabled:
            self.pixel_shift_timer.start(self.pixel_shift_interval * 1000)
        
        # 初始化UI
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle(f"纯时间显示 - {self.timer_type}")

        # 选项1：完整的窗口控制按钮
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowStaysOnTopHint |
            Qt.WindowSystemMenuHint |      # 系统菜单
            Qt.WindowMinimizeButtonHint |  # 最小化按钮
            Qt.WindowMaximizeButtonHint |  # 最大化按钮
            Qt.WindowCloseButtonHint       # 关闭按钮
        )
        
        # 设置背景色为黑色（更适合长时间显示）
        self.setStyleSheet("background-color: black;")
        
        # 中央部件
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        central_widget.setStyleSheet("background-color: black;")
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
    
        # 修改1：设置为简洁模式（更小的边距）
        main_layout.setContentsMargins(5, 5, 5, 5)  # 从20改为5
        main_layout.setSpacing(0)
        
        # 时间显示标签
        self.time_label = QLabel(self.current_time)
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setObjectName("timeLabel")
        
        # 初始字体大小设置为较小值，后续会根据窗口大小自动调整
        self.font_size = 50  # 从100改为50，让resizeEvent来处理
        font = QFont("Arial", self.font_size, QFont.Bold)
        self.time_label.setFont(font)
        
        # 设置文本颜色（根据计时器类型）
        if self.timer_type == 'timer':
            self.time_label.setStyleSheet("color: #2196F3;")
        else:
            self.time_label.setStyleSheet("color: #FF5722;")
        
        main_layout.addWidget(self.time_label, 1)  # 添加拉伸因子为1
        
        # 修改2：默认隐藏状态标签（简洁模式）
        self.status_label = QLabel("点击右键显示菜单 | 防烧屏保护已启用")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #888888; font-size: 12px; margin-top: 10px;")
        self.status_label.hide()  # 默认隐藏状态标签
        main_layout.addWidget(self.status_label)
        
        # 设置初始窗口大小
        self.resize(800, 400)
        
        # 启用鼠标跟踪
        self.setMouseTracking(True)
        central_widget.setMouseTracking(True)
        self.time_label.setMouseTracking(True)
        
        # 设置上下文菜单策略
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        # 立即调整字体大小以适应窗口
        QTimer.singleShot(100, self.adjust_font_size)

    def update_time(self, time_str, progress=0):
        """更新时间显示"""
        self.current_time = time_str
        self.time_label.setText(time_str)
        
        # 更新时间后重新调整字体大小
        self.adjust_font_size()
        
        # 更新最后活动时间
        self.last_activity_time = time.time()
        
    def update_time_style(self, state):
        """根据状态更新时间显示样式"""
        color_map = {
            'stopped': '#2196F3',
            'running': '#4CAF50',
            'paused': '#FF9800'
        }
        
        color = color_map.get(state, '#2196F3')
        self.time_label.setStyleSheet(f"color: {color};")
        
    def resizeEvent(self, event):
        """窗口大小改变事件 - 自适应字体大小"""
        super().resizeEvent(event)
        self.adjust_font_size()
        
    def adjust_font_size(self):
        """根据窗口大小调整字体大小，让字体填满窗口"""
        # 获取窗口和标签的尺寸
        window_width = self.width()
        window_height = self.height()
        
        # 计算基于文本长度和窗口尺寸的字体大小
        text = self.time_label.text()
        text_length = len(text.replace(':', ''))
        
        # 计算方法1：基于宽度（主要限制因素）
        # 假设每个字符的平均宽度是字体大小的一半
        # 我们想要文本占据窗口宽度的80%
        target_width = window_width * 0.8
        font_size_by_width = int(target_width / (text_length * 0.6))
        
        # 计算方法2：基于高度
        # 我们想要文本占据窗口高度的70%
        target_height = window_height * 0.7
        font_size_by_height = int(target_height * 0.9)  # 字体大小约为高度的0.9倍
        
        # 取两个计算结果的较小值，确保文本不会超出窗口
        new_font_size = min(font_size_by_width, font_size_by_height)
        
        # 设置最小和最大字体大小限制
        min_font_size = 20
        max_font_size = 500  # 增加最大字体大小限制
        
        if new_font_size < min_font_size:
            new_font_size = min_font_size
        elif new_font_size > max_font_size:
            new_font_size = max_font_size
        
        # 如果字体大小有显著变化才更新
        if abs(new_font_size - self.font_size) > 5 or new_font_size != self.font_size:
            self.font_size = new_font_size
            
            # 应用新字体
            font = QFont("Arial", self.font_size, QFont.Bold)
            
            # 设置字体平滑和抗锯齿
            font.setHintingPreference(QFont.PreferFullHinting)
            
            # 确保字体不会太大导致布局问题
            font_metrics = QFontMetrics(font)
            text_width = font_metrics.width(text)
            text_height = font_metrics.height()
            
            # 如果文本太大，逐步减小字体直到合适
            while (text_width > window_width * 0.9 or text_height > window_height * 0.9) and self.font_size > min_font_size:
                self.font_size -= 1
                font = QFont("Arial", self.font_size, QFont.Bold)
                font_metrics = QFontMetrics(font)
                text_width = font_metrics.width(text)
                text_height = font_metrics.height()
            
            self.time_label.setFont(font)
            
            # 强制更新布局
            self.time_label.adjustSize()
            self.update()
        
    def show_context_menu(self, position):
        """显示上下文菜单"""
        menu = QMenu(self)
        
        # 设置菜单样式 - 使用系统默认样式或自定义浅色样式
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                color: black;
                border: 1px solid #ccc;
            }
            QMenu::item {
                padding: 5px 20px 5px 20px;
            }
            QMenu::item:selected {
                background-color: #0078d7;
                color: white;
            }
            QMenu::item:disabled {
                color: gray;
            }
        """)
        
        # 显示模式选项
        mode_menu = QMenu("显示模式")
        mode_menu.setStyleSheet("""
            QMenu {
                background-color: white;
                color: black;
                border: 1px solid #ccc;
            }
            QMenu::item:selected {
                background-color: #0078d7;
                color: white;
            }
        """)
        
        normal_action = QAction("正常模式", self)
        normal_action.triggered.connect(lambda: self.set_display_mode('normal'))
        mode_menu.addAction(normal_action)
        
        minimal_action = QAction("简洁模式", self)
        minimal_action.triggered.connect(lambda: self.set_display_mode('minimal'))
        mode_menu.addAction(minimal_action)
        
        menu.addMenu(mode_menu)
        
        menu.addSeparator()
        
        # 窗口控制选项
        if not self.is_fullscreen:
            fullscreen_action = QAction("全屏显示", self)
            fullscreen_action.triggered.connect(self.toggle_fullscreen)
            menu.addAction(fullscreen_action)
        else:
            exit_fullscreen_action = QAction("退出全屏", self)
            exit_fullscreen_action.triggered.connect(self.toggle_fullscreen)
            menu.addAction(exit_fullscreen_action)
        
        maximize_action = QAction("最大化", self)
        maximize_action.triggered.connect(self.toggle_maximize)
        menu.addAction(maximize_action)
        
        menu.addSeparator()
        
        # 防烧屏设置
        burnin_menu = QMenu("防烧屏设置")
        burnin_menu.setStyleSheet("""
            QMenu {
                background-color: white;
                color: black;
                border: 1px solid #ccc;
            }
            QMenu::item:selected {
                background-color: #0078d7;
                color: white;
            }
        """)
        
        burnin_toggle = QAction("启用防烧屏保护", self)
        burnin_toggle.setCheckable(True)
        burnin_toggle.setChecked(self.burn_in_protection_enabled)
        burnin_toggle.triggered.connect(self.toggle_burnin_protection)
        burnin_menu.addAction(burnin_toggle)
        
        burnin_menu.addSeparator()
        
        shift_fast = QAction("快速像素移动 (60秒)", self)
        shift_fast.triggered.connect(lambda: self.set_pixel_shift_interval(60))
        burnin_menu.addAction(shift_fast)
        
        shift_medium = QAction("中速像素移动 (5分钟)", self)
        shift_medium.triggered.connect(lambda: self.set_pixel_shift_interval(300))
        burnin_menu.addAction(shift_medium)
        
        shift_slow = QAction("慢速像素移动 (15分钟)", self)
        shift_slow.triggered.connect(lambda: self.set_pixel_shift_interval(900))
        burnin_menu.addAction(shift_slow)
        
        menu.addMenu(burnin_menu)
        
        menu.addSeparator()
        
        # 颜色主题
        color_menu = QMenu("颜色主题")
        color_menu.setStyleSheet("""
            QMenu {
                background-color: white;
                color: black;
                border: 1px solid #ccc;
            }
            QMenu::item:selected {
                background-color: #0078d7;
                color: white;
            }
        """)
        
        blue_action = QAction("蓝色主题", self)
        blue_action.triggered.connect(lambda: self.set_color_theme('blue'))
        color_menu.addAction(blue_action)
        
        green_action = QAction("绿色主题", self)
        green_action.triggered.connect(lambda: self.set_color_theme('green'))
        color_menu.addAction(green_action)
        
        red_action = QAction("红色主题", self)
        red_action.triggered.connect(lambda: self.set_color_theme('red'))
        color_menu.addAction(red_action)
        
        white_action = QAction("白色主题", self)
        white_action.triggered.connect(lambda: self.set_color_theme('white'))
        color_menu.addAction(white_action)
        
        custom_action = QAction("自定义颜色...", self)
        custom_action.triggered.connect(self.choose_custom_color)
        color_menu.addAction(custom_action)
        
        menu.addMenu(color_menu)
        
        menu.addSeparator()
        
        # 关闭窗口
        close_action = QAction("关闭窗口", self)
        close_action.triggered.connect(self.close)
        menu.addAction(close_action)
        
        # 显示菜单
        menu.exec_(self.mapToGlobal(position))
        
    def set_display_mode(self, mode):
        """设置显示模式"""
        if mode == 'minimal':
            # 简洁模式：隐藏状态标签，调整边距
            self.status_label.hide()
            self.centralWidget().layout().setContentsMargins(5, 5, 5, 5)
        else:
            # 正常模式：显示状态标签，恢复边距
            self.status_label.show()
            self.centralWidget().layout().setContentsMargins(20, 20, 20, 20)
        
        self.adjust_font_size()
        
    def toggle_fullscreen(self):
        """切换全屏模式"""
        if not self.is_fullscreen:
            self.showFullScreen()
            self.is_fullscreen = True
            self.status_label.setText("全屏模式 | 按ESC退出全屏")
        else:
            self.showNormal()
            self.is_fullscreen = False
            self.status_label.setText("点击右键显示菜单 | 防烧屏保护已启用")
        
    def toggle_maximize(self):
        """切换最大化"""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
            
    def toggle_burnin_protection(self, enabled):
        """切换防烧屏保护"""
        self.burn_in_protection_enabled = enabled
        
        if enabled:
            self.pixel_shift_timer.start(self.pixel_shift_interval * 1000)
            self.status_label.setText("点击右键显示菜单 | 防烧屏保护已启用")
        else:
            self.pixel_shift_timer.stop()
            # 重置像素偏移
            self.pixel_shift_x = 0
            self.pixel_shift_y = 0
            self.time_label.setGeometry(self.time_label.x() - self.pixel_shift_x, 
                                      self.time_label.y() - self.pixel_shift_y,
                                      self.time_label.width(), 
                                      self.time_label.height())
            self.status_label.setText("点击右键显示菜单 | 防烧屏保护已禁用")
            
    def set_pixel_shift_interval(self, interval):
        """设置像素移动间隔"""
        self.pixel_shift_interval = interval
        
        if self.burn_in_protection_enabled:
            self.pixel_shift_timer.stop()
            self.pixel_shift_timer.start(interval * 1000)
            
        self.status_label.setText(f"点击右键显示菜单 | 防烧屏保护: {interval}秒间隔")
        
    def set_color_theme(self, theme):
        """设置颜色主题"""
        color_map = {
            'blue': '#2196F3',
            'green': '#4CAF50',
            'red': '#F44336',
            'white': '#FFFFFF'
        }
        
        color = color_map.get(theme, '#2196F3')
        self.time_label.setStyleSheet(f"color: {color};")
        
    def choose_custom_color(self):
        """选择自定义颜色"""
        color = QColorDialog.getColor()
        if color.isValid():
            self.time_label.setStyleSheet(f"color: {color.name()};")
            
    def apply_pixel_shift(self):
        """应用像素移动防烧屏保护"""
        if not self.burn_in_protection_enabled or self.is_screensaver_active:
            return
            
        # 在有限的范围内移动像素
        self.pixel_shift_x = (self.pixel_shift_x + self.pixel_shift_distance) % (self.pixel_shift_distance * 4)
        self.pixel_shift_y = (self.pixel_shift_y + self.pixel_shift_distance) % (self.pixel_shift_distance * 4)
        
        # 轻微移动标签位置
        self.time_label.move(20 + self.pixel_shift_x, 20 + self.pixel_shift_y)
        
        # 记录移动时间
        self.last_pixel_shift_time = time.time()
        
    def check_screensaver(self):
        """检查是否需要启动屏幕保护"""
        if not self.burn_in_protection_enabled:
            return
            
        current_time = time.time()
        idle_time = current_time - self.last_activity_time
        
        # 如果空闲时间超过阈值，启动屏幕保护
        if idle_time > self.screensaver_timeout and not self.is_screensaver_active:
            self.activate_screensaver()
        elif idle_time <= self.screensaver_timeout and self.is_screensaver_active:
            self.deactivate_screensaver()
            
    def activate_screensaver(self):
        """激活屏幕保护"""
        self.is_screensaver_active = True
        
        # 保存原始亮度
        self.original_brightness = 1.0
        
        # 降低亮度
        self.apply_brightness_reduction()
        
        # 停止像素移动
        self.pixel_shift_timer.stop()
        
        # 更新状态
        self.status_label.setText("屏幕保护已激活 | 移动鼠标或按键退出")
        
    def deactivate_screensaver(self):
        """停用屏幕保护"""
        self.is_screensaver_active = False
        
        # 恢复亮度
        self.restore_brightness()
        
        # 重新启动像素移动
        if self.burn_in_protection_enabled:
            self.pixel_shift_timer.start(self.pixel_shift_interval * 1000)
            
        # 更新状态
        self.status_label.setText("点击右键显示菜单 | 防烧屏保护已启用")
        
    def apply_brightness_reduction(self):
        """应用亮度减少"""
        # 这里使用CSS滤镜来降低亮度
        self.time_label.setStyleSheet(
            self.time_label.styleSheet() + 
            f" opacity: {self.brightness_reduction};"
        )
        
    def restore_brightness(self):
        """恢复原始亮度"""
        # 移除亮度滤镜
        style = self.time_label.styleSheet()
        if "opacity:" in style:
            # 移除opacity属性
            lines = style.split(';')
            lines = [line for line in lines if not line.strip().startswith('opacity:')]
            new_style = ';'.join(lines)
            self.time_label.setStyleSheet(new_style)
            
    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 用于检测活动"""
        super().mouseMoveEvent(event)
        self.last_activity_time = time.time()
        
    def keyPressEvent(self, event):
        """按键事件"""
        super().keyPressEvent(event)
        
        # ESC键退出全屏
        if event.key() == Qt.Key_Escape and self.is_fullscreen:
            self.toggle_fullscreen()
            
        # 空格键切换显示模式
        elif event.key() == Qt.Key_Space:
            if self.status_label.isVisible():
                self.set_display_mode('minimal')
            else:
                self.set_display_mode('normal')
                
        # F11键切换全屏
        elif event.key() == Qt.Key_F11:
            self.toggle_fullscreen()
            
        # 更新最后活动时间
        self.last_activity_time = time.time()
        
    def closeEvent(self, event):
        """关闭事件"""
        # 停止所有定时器
        self.screensaver_timer.stop()
        self.pixel_shift_timer.stop()
        
        # 通知父窗口
        if self.parent_timer:
            self.parent_timer.time_display_window = None
            
        event.accept()

# 马卡龙色系定义
class MacaronColors_12:
    # 粉色系
    SAKURA_PINK = QColor('#FFB7CE')  # 樱花粉
    ROSE_PINK = QColor('#FF9AA2')    # 玫瑰粉
    # 蓝色系
    SKY_BLUE = QColor('#A2E1F6')     # 天空蓝
    LILAC_MIST = QColor('#E6E6FA')   # 淡丁香
    # 绿色系
    MINT_GREEN = QColor('#B5EAD7')   # 薄荷绿
    APPLE_GREEN = QColor('#D4F1C7')  # 苹果绿
    # 黄色/橙色系
    LEMON_YELLOW = QColor('#FFEAA5') # 柠檬黄
    BUTTER_CREAM = QColor('#FFF8B8') # 奶油黄
    PEACH_ORANGE = QColor('#FFDAC1') # 蜜桃橙
    # 紫色系
    LAVENDER = QColor('#C7CEEA')     # 薰衣草紫
    TARO_PURPLE = QColor('#D8BFD8')  # 香芋紫
    # 中性色
    CARAMEL_CREAM = QColor('#F0E6DD') # 焦糖奶霜




class TimerThread(QThread):
    """计时器线程"""
    update_signal = pyqtSignal(str, int)  # 更新时间信号
    alarm_signal = pyqtSignal()  # 闹钟信号
    
    def __init__(self, duration_seconds, is_countdown=False):
        super().__init__()
        self.duration = duration_seconds
        self.is_countdown = is_countdown
        self.is_running = True
        self.is_paused = False
        self.pause_lock = threading.Lock()
        self.elapsed = 0
        
    def run(self):
        if self.is_countdown:
            remaining = self.duration
            while remaining > 0 and self.is_running:
                if not self.is_paused:
                    mins, secs = divmod(remaining, 60)
                    hours, mins = divmod(mins, 60)
                    time_str = f"{hours:02d}:{mins:02d}:{secs:02d}"
                    
                    # 修复：计算剩余时间的百分比，从100%递减到0%
                    if self.duration > 0:
                        progress = int((self.duration - remaining) * 100 / self.duration)
                        # 确保进度不超过100%
                        progress = min(progress, 100)
                    else:
                        progress = 0
                    
                    self.update_signal.emit(time_str, progress)
                    remaining -= 1
                    time.sleep(1)
                else:
                    time.sleep(0.1)
                    
            if remaining == 0:
                # 时间到，发送100%的进度
                self.update_signal.emit("00:00:00", 100)
                self.alarm_signal.emit()
        else:
            self.elapsed = 0
            while self.is_running:
                if not self.is_paused:
                    mins, secs = divmod(self.elapsed, 60)
                    hours, mins = divmod(mins, 60)
                    time_str = f"{hours:02d}:{mins:02d}:{secs:02d}"
                    
                    # 计时器模式：计算已用时间的百分比
                    if self.duration > 0:
                        progress = min(self.elapsed * 100 // max(self.duration, 1), 100)
                    else:
                        # 无限制计时器，每60秒一个周期
                        progress = self.elapsed % 60 * 100 // 60
                    
                    self.update_signal.emit(time_str, progress)
                    self.elapsed += 1
                    time.sleep(1)
                else:
                    time.sleep(0.1)
    
    def pause(self):
        self.is_paused = True
        
    def resume(self):
        self.is_paused = False
        
    def stop(self):
        self.is_running = False

class SettingsManager:
    """设置管理器"""
    def __init__(self):
        self.settings_file = "timer_settings.json"
        self.default_settings = {
            "window_geometry": None,
            "window_state": None,
            "volume": 100,
            "muted": False,
            "sound_file": "default",
            "preset_timers": {
                "5分钟": 300,
                "10分钟": 600,
                "15分钟": 900,
                "25分钟": 1500,
                "30分钟": 1800,
                "45分钟": 2700,
                "1小时": 3600,
                # 新增：2小时和3小时预设
                "2小时": 7200,
                "3小时": 10800
            },
            "recent_timers": [],
            "always_on_top": False,
            # 新增：最小化到托盘选项，默认值为 False
            "minimize_to_tray": False,
            # 新增：提醒方式设置
            "window_shake": True,
            "window_flash": True,
            "taskbar_flash": True,
            "show_alert_dialog": True,
            # 新增：纯时间显示窗口设置
            "time_display_window_geometry": None,
            "time_display_burnin_protection": True,
            "time_display_pixel_shift_interval": 300,
            "time_display_color_theme": "auto"
        }
        self.settings = self.load_settings()
    
    def load_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # 合并默认设置和加载的设置
                    settings = self.default_settings.copy()
                    settings.update(loaded)
                    return settings
        except Exception as e:
            print(f"加载设置失败: {e}")
        return self.default_settings.copy()
    
    def save_settings(self):
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存设置失败: {e}")
            return False
    
    def update_setting(self, key, value):
        self.settings[key] = value
        self.save_settings()

class CustomProgressBar(QProgressBar):
    """自定义进度条，显示更多信息"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(True)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QProgressBar {
                border: 2px solid #2196F3;
                border-radius: 5px;
                text-align: center;
                background-color: #f0f0f0;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
                border-radius: 3px;
            }
        """)

class TimerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings_manager = SettingsManager()
        self.timer_thread = None
        self.alarm_sound = None
        self.current_timer_type = None
        self.current_duration = 0
        
        # 新增：纯时间显示窗口
        self.time_display_window = None

        # 新增：初始化标记
        self._is_initializing = False

        # 新增：倒计时状态变量
        self.countdown_state = 'stopped'  # 'stopped', 'running', 'paused'

        # 新增：倒计时状态变量
        self.countdown_state = 'stopped'  # 'stopped', 'running', 'paused'

        # 新增：计时器状态变量
        self.timer_state = 'stopped'  # 'stopped', 'running', 'paused'
    
        # 新增：音频播放器
        self.media_player = None
        self.init_audio_player()
                
        # 初始化属性，避免AttributeError
        self.tray_icon = None
        self.taskbar_button = None
        self.taskbar_progress = None
        
        # 新增：动画相关属性
        self.shake_animation = None
        self.flash_timer = None
        self.flash_count = 0
        self.taskbar_timer = None
        self.original_style = ""
        
        self.init_ui()
        self.load_settings()
        
        # 初始化任务栏进度条
        self.init_taskbar_progress()
    
    def init_ui(self):
        """初始化界面"""
        # self.setWindowTitle('多功能计时器')
        self.setWindowTitle(f"{ProjectInfo.NAME} {ProjectInfo.VERSION} (Build: {ProjectInfo.BUILD_DATE})")
        self.setMinimumSize(800, 600)
        
        # 设置图标
        if os.path.exists('icon.ico'):
            self.setWindowIcon(QIcon('icon.ico'))
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel('多功能计时器')
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2196F3; padding: 10px;")
        main_layout.addWidget(title_label)
        
        # 选项卡
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: white;
            }
            QTabBar::tab {
                background: #f0f0f0;
                padding: 10px 20px;
                margin-right: 2px;
                border: 1px solid #ccc;
                border-bottom: none;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background: white;
                font-weight: bold;
            }
        """)
        
        # 创建各个标签页
        self.create_timer_tab()
        self.create_countdown_tab()
        self.create_preset_tab()
        self.create_settings_tab()
        
        main_layout.addWidget(self.tab_widget)
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('就绪')
        
        # 系统托盘最小化处理
        self.installEventFilter(self)
        
    def create_timer_tab(self):
        """创建计时器标签页"""
        timer_tab = QWidget()
        layout = QVBoxLayout(timer_tab)
        layout.setSpacing(15)
        
        # 时间显示 - 添加点击事件
        self.timer_display = QLabel('00:00:00')
        self.timer_display.setAlignment(Qt.AlignCenter)
        display_font = QFont()
        display_font.setPointSize(48)
        display_font.setBold(True)
        self.timer_display.setFont(display_font)
        # 修改这里的样式设置，使用动态样式
        self.timer_display.setObjectName('timerDisplay')  # 添加对象名称以便CSS选择
        self.update_timer_display_style()  # 调用方法更新样式
        layout.addWidget(self.timer_display)
        self.timer_display.setStyleSheet("""
            QLabel {
                color: #2196F3;
                background-color: #f8f9fa;
                border: 2px solid #2196F3;
                border-radius: 10px;
                padding: 20px;
                margin: 10px;
            }
        """)
        
        # 新增：为时间显示标签添加鼠标点击事件
        self.timer_display.mousePressEvent = self.on_timer_display_clicked
        
        layout.addWidget(self.timer_display)
        
        # 进度条
        self.timer_progress = CustomProgressBar()
        self.timer_progress.setRange(0, 100)
        layout.addWidget(self.timer_progress)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        
        self.start_timer_btn = QPushButton('开始计时')
        self.start_timer_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.start_timer_btn.clicked.connect(self.start_timer)
        self.start_timer_btn.setMinimumHeight(40)
        
        self.pause_timer_btn = QPushButton('暂停')
        self.pause_timer_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        self.pause_timer_btn.clicked.connect(self.pause_timer)
        self.pause_timer_btn.setMinimumHeight(40)
        self.pause_timer_btn.setEnabled(False)
        
        self.reset_timer_btn = QPushButton('重置')
        self.reset_timer_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.reset_timer_btn.clicked.connect(self.reset_timer)
        self.reset_timer_btn.setMinimumHeight(40)
        
        button_layout.addWidget(self.start_timer_btn)
        button_layout.addWidget(self.pause_timer_btn)
        button_layout.addWidget(self.reset_timer_btn)
        
        layout.addLayout(button_layout)
        
        # 最近计时器
        recent_group = QGroupBox('最近使用的计时器')
        recent_layout = QVBoxLayout()
        
        self.recent_list = QListWidget()
        self.recent_list.itemClicked.connect(self.select_recent_timer)
        recent_layout.addWidget(self.recent_list)
        
        recent_group.setLayout(recent_layout)
        layout.addWidget(recent_group)
        
        self.tab_widget.addTab(timer_tab, "⏱️ 计时器")
        
    def create_countdown_tab(self):
        """创建倒计时标签页"""
        countdown_tab = QWidget()
        layout = QVBoxLayout(countdown_tab)
        layout.setSpacing(15)
        
        # 时间输入
        time_group = QGroupBox('设置倒计时时间')
        time_layout = QGridLayout()
        
        self.hour_spin = QSpinBox()
        self.hour_spin.setRange(0, 23)
        self.hour_spin.setSuffix(' 小时')
        self.hour_spin.setMinimumHeight(35)
        
        self.minute_spin = QSpinBox()
        self.minute_spin.setRange(0, 59)
        self.minute_spin.setSuffix(' 分钟')
        self.minute_spin.setMinimumHeight(35)
        
        self.second_spin = QSpinBox()
        self.second_spin.setRange(0, 59)
        self.second_spin.setSuffix(' 秒')
        self.second_spin.setMinimumHeight(35)
        
        time_layout.addWidget(QLabel('小时:'), 0, 0)
        time_layout.addWidget(self.hour_spin, 0, 1)
        time_layout.addWidget(QLabel('分钟:'), 1, 0)
        time_layout.addWidget(self.minute_spin, 1, 1)
        time_layout.addWidget(QLabel('秒:'), 2, 0)
        time_layout.addWidget(self.second_spin, 2, 1)
        
        time_group.setLayout(time_layout)
        layout.addWidget(time_group)
        
        # 倒计时显示 - 添加点击事件
        self.countdown_display = QLabel('00:00:00')
        self.countdown_display.setAlignment(Qt.AlignCenter)
        display_font = QFont()
        display_font.setPointSize(48)
        display_font.setBold(True)
        self.countdown_display.setFont(display_font)
        # 修改这里的样式设置，使用动态样式
        self.countdown_display.setObjectName('countdownDisplay')  # 添加对象名称以便CSS选择
        self.update_countdown_display_style()  # 调用方法更新样式
        self.countdown_display.setStyleSheet("""
            QLabel {
                color: #FF5722;
                background-color: #fff3e0;
                border: 2px solid #FF5722;
                border-radius: 10px;
                padding: 20px;
                margin: 10px;
            }
        """)
        
        # 新增：为倒计时显示标签添加鼠标点击事件
        self.countdown_display.mousePressEvent = self.on_countdown_display_clicked
        
        layout.addWidget(self.countdown_display)
        
        # 倒计时进度条
        self.countdown_progress = CustomProgressBar()
        self.countdown_progress.setRange(0, 100)
        layout.addWidget(self.countdown_progress)
        
        # 控制按钮
        countdown_btn_layout = QHBoxLayout()
        
        self.start_countdown_btn = QPushButton('开始倒计时')
        self.start_countdown_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.start_countdown_btn.clicked.connect(self.start_countdown)
        self.start_countdown_btn.setMinimumHeight(40)
        
        self.pause_countdown_btn = QPushButton('暂停')
        self.pause_countdown_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        self.pause_countdown_btn.clicked.connect(self.pause_countdown)
        self.pause_countdown_btn.setMinimumHeight(40)
        self.pause_countdown_btn.setEnabled(False)
        
        self.reset_countdown_btn = QPushButton('重置')
        self.reset_countdown_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.reset_countdown_btn.clicked.connect(self.reset_countdown)
        self.reset_countdown_btn.setMinimumHeight(40)
        
        countdown_btn_layout.addWidget(self.start_countdown_btn)
        countdown_btn_layout.addWidget(self.pause_countdown_btn)
        countdown_btn_layout.addWidget(self.reset_countdown_btn)
        
        layout.addLayout(countdown_btn_layout)
        
        # 预设时间按钮
        preset_group = QGroupBox('快速设置')
        preset_layout = QGridLayout()
        
        # 修改后的快速时间设置，包含2小时和3小时
        quick_times = [
            ('5分钟', 300), ('10分钟', 600), ('15分钟', 900),
            ('25分钟', 1500), ('30分钟', 1800), ('1小时', 3600),
            ('2小时', 7200), ('3小时', 10800)  # 新增
        ]
        
        row, col = 0, 0
        for text, seconds in quick_times:
            btn = QPushButton(text)
            btn.clicked.connect(lambda checked, s=seconds: self.set_countdown_time(s))
            preset_layout.addWidget(btn, row, col)
            col += 1
            if col > 2:
                col = 0
                row += 1
        
        preset_group.setLayout(preset_layout)
        layout.addWidget(preset_group)
        
        self.tab_widget.addTab(countdown_tab, "⏰ 倒计时")
        
    def create_preset_tab(self):
        """创建预设标签页"""
        preset_tab = QWidget()
        layout = QVBoxLayout(preset_tab)
        
        preset_group = QGroupBox('预设计时器')
        preset_layout = QGridLayout()
        
        self.preset_buttons = []
        row, col = 0, 0
        
        preset_timers = self.settings_manager.settings['preset_timers']
        
        for name, seconds in preset_timers.items():
            btn = QPushButton(f"{name}\n({self.seconds_to_time_str(seconds)})")
            btn.setMinimumHeight(60)
            btn.clicked.connect(lambda checked, s=seconds, n=name: self.use_preset_timer(s, n))
            preset_layout.addWidget(btn, row, col)
            self.preset_buttons.append(btn)
            col += 1
            if col > 2:
                col = 0
                row += 1
        
        preset_group.setLayout(preset_layout)
        layout.addWidget(preset_group)
        
        # 自定义预设
        custom_group = QGroupBox('自定义预设')
        custom_layout = QGridLayout()
        
        custom_layout.addWidget(QLabel('名称:'), 0, 0)
        self.preset_name_edit = QLineEdit()
        custom_layout.addWidget(self.preset_name_edit, 0, 1)
        
        custom_layout.addWidget(QLabel('时间(秒):'), 1, 0)
        self.preset_time_edit = QSpinBox()
        self.preset_time_edit.setRange(1, 86400)
        custom_layout.addWidget(self.preset_time_edit, 1, 1)
        
        add_preset_btn = QPushButton('添加预设')
        add_preset_btn.clicked.connect(self.add_preset_timer)
        custom_layout.addWidget(add_preset_btn, 2, 0, 1, 2)
        
        custom_group.setLayout(custom_layout)
        layout.addWidget(custom_group)
        
        layout.addStretch()
        self.tab_widget.addTab(preset_tab, "⭐ 预设")
        
    def create_settings_tab(self):
        """创建设置标签页"""
        settings_tab = QWidget()
        layout = QVBoxLayout(settings_tab)
        
        # 声音设置
        sound_group = QGroupBox('声音设置')
        sound_layout = QVBoxLayout()
        
        # 静音选项
        self.mute_checkbox = QCheckBox('静音')
        self.mute_checkbox.stateChanged.connect(self.toggle_mute)
        sound_layout.addWidget(self.mute_checkbox)
        
        # 音量控制
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel('音量:'))
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.valueChanged.connect(self.change_volume)
        volume_layout.addWidget(self.volume_slider)
        
        self.volume_label = QLabel('100%')
        volume_layout.addWidget(self.volume_label)
        
        sound_layout.addLayout(volume_layout)
        
        # 铃声选择
        sound_layout.addWidget(QLabel('选择铃声:'))
        
        self.sound_combo = QComboBox()
        self.sound_combo.addItem('默认铃声')
        self.sound_combo.addItem('自定义铃声...')
        self.sound_combo.currentTextChanged.connect(self.change_sound)
        sound_layout.addWidget(self.sound_combo)
        
        # 测试声音按钮
        test_sound_btn = QPushButton('测试声音')
        test_sound_btn.clicked.connect(self.test_sound)
        sound_layout.addWidget(test_sound_btn)
        
        sound_group.setLayout(sound_layout)
        layout.addWidget(sound_group)
        
        # 新增：提醒方式设置
        alarm_group = QGroupBox('提醒方式设置')
        alarm_layout = QVBoxLayout()
        
        self.window_shake_checkbox = QCheckBox('窗口抖动提醒')
        self.window_shake_checkbox.stateChanged.connect(self.toggle_window_shake)
        alarm_layout.addWidget(self.window_shake_checkbox)
        
        self.window_flash_checkbox = QCheckBox('窗口闪烁提醒')
        self.window_flash_checkbox.stateChanged.connect(self.toggle_window_flash)
        alarm_layout.addWidget(self.window_flash_checkbox)
        
        self.taskbar_flash_checkbox = QCheckBox('任务栏闪烁提醒')
        self.taskbar_flash_checkbox.stateChanged.connect(self.toggle_taskbar_flash)
        self.taskbar_flash_checkbox.setEnabled(sys.platform == 'win32')
        if sys.platform != 'win32':
            self.taskbar_flash_checkbox.setToolTip('仅Windows系统可用')
        alarm_layout.addWidget(self.taskbar_flash_checkbox)
        
        self.alert_dialog_checkbox = QCheckBox('显示醒目提醒对话框')
        self.alert_dialog_checkbox.stateChanged.connect(self.toggle_alert_dialog)
        alarm_layout.addWidget(self.alert_dialog_checkbox)
        
        # 测试提醒按钮
        test_alarm_btn = QPushButton('测试提醒效果')
        test_alarm_btn.clicked.connect(self.test_alarm_effects)
        alarm_layout.addWidget(test_alarm_btn)
        
        alarm_group.setLayout(alarm_layout)
        layout.addWidget(alarm_group)
        
        # 窗口设置
        window_group = QGroupBox('窗口设置')
        window_layout = QVBoxLayout()
        
        self.always_on_top_checkbox = QCheckBox('窗口置顶')
        self.always_on_top_checkbox.stateChanged.connect(self.toggle_always_on_top)
        window_layout.addWidget(self.always_on_top_checkbox)
    
        # 新增：最小化到托盘选项
        self.minimize_to_tray_checkbox = QCheckBox('最小化到托盘')
        self.minimize_to_tray_checkbox.stateChanged.connect(self.toggle_minimize_to_tray)
        window_layout.addWidget(self.minimize_to_tray_checkbox)
    
        window_group.setLayout(window_layout)
        layout.addWidget(window_group)
        
        # 重置设置
        reset_group = QGroupBox('重置设置')
        reset_layout = QHBoxLayout()
        
        reset_btn = QPushButton('重置为默认设置')
        reset_btn.clicked.connect(self.reset_settings)
        reset_btn.setStyleSheet("background-color: #f44336; color: white;")
        reset_layout.addWidget(reset_btn)
        
        reset_group.setLayout(reset_layout)
        layout.addWidget(reset_group)
        
        layout.addStretch()
        self.tab_widget.addTab(settings_tab, "⚙️ 设置")

        # 创建关于标签页
        self.create_about_tab()
    
    # 新增：时间显示标签点击事件处理
    def on_timer_display_clicked(self, event):
        """计时器时间显示标签点击事件"""
        if event.button() == Qt.LeftButton:
            self.show_time_display_window('timer', self.timer_display.text())
            
    def on_countdown_display_clicked(self, event):
        """倒计时时间显示标签点击事件"""
        if event.button() == Qt.LeftButton:
            current_text = self.countdown_display.text()
            # 如果显示的是00:00:00，使用设置的时间
            if current_text == '00:00:00':
                hours = self.hour_spin.value()
                minutes = self.minute_spin.value()
                seconds = self.second_spin.value()
                total_seconds = hours * 3600 + minutes * 60 + seconds
                current_text = self.seconds_to_time_str(total_seconds)
            self.show_time_display_window('countdown', current_text)
            
    def show_time_display_window(self, timer_type, initial_time):
        """显示纯时间显示窗口"""
        # 如果窗口已存在，先关闭
        if self.time_display_window:
            self.time_display_window.close()
            
        # 创建新窗口
        self.time_display_window = TimeDisplayWindow(self, timer_type, initial_time)
        
        # 加载保存的窗口位置和大小
        saved_geometry = self.settings_manager.settings.get('time_display_window_geometry')
        if saved_geometry:
            self.time_display_window.restoreGeometry(QByteArray.fromHex(saved_geometry.encode()))
        else:
            # 默认位置：主屏幕的右侧
            screen_geometry = QApplication.desktop().screenGeometry()
            default_width = screen_geometry.width() // 3
            default_height = screen_geometry.height() // 2
            x = screen_geometry.width() - default_width - 50
            y = screen_geometry.height() // 2 - default_height // 2
            self.time_display_window.setGeometry(x, y, default_width, default_height)
        
        # 设置防烧屏保护
        burnin_enabled = self.settings_manager.settings.get('time_display_burnin_protection', True)
        self.time_display_window.burn_in_protection_enabled = burnin_enabled
        
        # 设置像素移动间隔
        shift_interval = self.settings_manager.settings.get('time_display_pixel_shift_interval', 300)
        self.time_display_window.pixel_shift_interval = shift_interval
        
        # 设置颜色主题
        color_theme = self.settings_manager.settings.get('time_display_color_theme', 'auto')
        if color_theme != 'auto':
            self.time_display_window.set_color_theme(color_theme)
        
        # 连接时间更新信号
        if timer_type == 'timer' and self.timer_thread:
            # 断开之前的连接
            try:
                self.timer_thread.update_signal.disconnect()
            except:
                pass
            # 重新连接，同时更新主窗口和时间显示窗口
            self.timer_thread.update_signal.connect(self.update_timer_display)
            self.timer_thread.update_signal.connect(
                lambda t, p: self.time_display_window.update_time(t, p)
            )
            # 更新状态
            self.time_display_window.update_time_style(self.timer_state)
        elif timer_type == 'countdown' and self.timer_thread:
            # 断开之前的连接
            try:
                self.timer_thread.update_signal.disconnect()
            except:
                pass
            # 重新连接，同时更新主窗口和时间显示窗口
            self.timer_thread.update_signal.connect(self.update_countdown_display)
            self.timer_thread.update_signal.connect(
                lambda t, p: self.time_display_window.update_time(t, p)
            )
            # 更新状态
            self.time_display_window.update_time_style(self.countdown_state)
        
        # 显示窗口
        self.time_display_window.show()
        
        # 修改：延迟调整字体大小，确保窗口已完全显示
        QTimer.singleShot(100, self.time_display_window.adjust_font_size)
        
        # 状态栏提示
        self.status_bar.showMessage(f'纯时间显示窗口已打开 - {timer_type}')
        
    def save_time_display_window_geometry(self):
        """保存纯时间显示窗口的几何信息"""
        if self.time_display_window:
            geometry = self.time_display_window.saveGeometry().toHex().data().decode()
            self.settings_manager.update_setting('time_display_window_geometry', geometry)
            
    def setup_tray_icon(self):
        """设置系统托盘图标"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            
            if os.path.exists('icon.ico'):
                self.tray_icon.setIcon(QIcon('icon.ico'))
            else:
                self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
            
            # 创建托盘菜单
            tray_menu = QMenu()
            
            show_action = tray_menu.addAction("显示窗口")
            show_action.triggered.connect(self.show_window)
            
            # 新增：显示时间显示窗口选项
            if self.time_display_window:
                hide_time_display_action = tray_menu.addAction("隐藏时间显示窗口")
                hide_time_display_action.triggered.connect(self.time_display_window.hide)
            else:
                show_time_display_action = tray_menu.addAction("显示时间显示窗口")
                show_time_display_action.triggered.connect(
                    lambda: self.show_time_display_window(
                        self.current_timer_type or 'timer',
                        self.timer_display.text()
                    )
                )
            
            tray_menu.addSeparator()
            
            quit_action = tray_menu.addAction("退出")
            quit_action.triggered.connect(self.close_application)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()
            
            # 托盘图标点击事件
            self.tray_icon.activated.connect(self.tray_icon_activated)

    def tray_icon_activated(self, reason):
        """托盘图标激活事件"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window()
    
    def show_window(self):
        """显示窗口"""
        self.showNormal()
        self.activateWindow()
        self.raise_()
    
    def closeEvent(self, event):
        """关闭事件"""
        try:
            # 保存时间显示窗口的几何信息
            self.save_time_display_window_geometry()
            
            # 清理资源
            self.cleanup_resources()
            
            # 获取最小化到托盘的设置
            minimize_to_tray = self.settings_manager.settings.get('minimize_to_tray', False)
        
            # 确保托盘图标已初始化
            if not hasattr(self, 'tray_icon') or not self.tray_icon:
                self.setup_tray_icon()
        
            # 如果启用了最小化到托盘，并且托盘图标可用
            if minimize_to_tray and hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
                self.hide()
                event.ignore()
                self.tray_icon.showMessage(
                    '多功能计时器',
                    '程序已最小化到系统托盘',
                    QSystemTrayIcon.Information,
                    2000
                )
            else:
                # 否则正常关闭程序
                self.save_current_settings()
                event.accept()
                
        except Exception as e:
            print(f"关闭事件处理失败: {e}")
            event.accept()
    
    def changeEvent(self, event):
        """窗口状态改变事件"""
        if event.type() == QEvent.WindowStateChange:
            # 获取最小化到托盘的设置
            minimize_to_tray = self.settings_manager.settings.get('minimize_to_tray', False)
            
            # 如果启用了最小化到托盘，并且窗口被最小化
            if minimize_to_tray and self.isMinimized() and hasattr(self, 'tray_icon'):
                self.hide()
                self.tray_icon.showMessage(
                    '多功能计时器',
                    '程序已最小化到系统托盘',
                    QSystemTrayIcon.Information,
                    2000
                )
            
            # 新增：窗口最小化时显示任务栏进度条
            if self.isMinimized():
                # 如果计时器正在运行，显示进度条
                if self.timer_thread and self.timer_thread.isRunning():
                    self.show_taskbar_progress(True)
                else:
                    self.show_taskbar_progress(False)
            else:
                # 窗口恢复时，如果计时器没有运行，隐藏进度条
                if not (self.timer_thread and self.timer_thread.isRunning()):
                    self.show_taskbar_progress(False)

    def showEvent(self, event):
        """窗口显示事件"""
        super().showEvent(event)
        
        # 窗口显示后初始化托盘图标
        if not self.tray_icon:
            self.setup_tray_icon()
        
        # 窗口显示后设置任务栏按钮的窗口关联
        self.setup_taskbar_window_handle()
    
        # 新增：窗口显示后检查是否需要立即最小化到托盘
        # 只有在第一次显示窗口时才检查
        if not hasattr(self, '_initial_minimize_check_done'):
            self._initial_minimize_check_done = True
            self.check_initial_minimize_to_tray()

    def check_initial_minimize_to_tray(self):
        """检查是否需要初始最小化到托盘"""
        # 获取设置中的最小化到托盘选项
        minimize_to_tray = self.settings_manager.settings.get('minimize_to_tray', False)
        
        if minimize_to_tray:
            # 如果设置了最小化到托盘，先初始化托盘图标
            if not self.tray_icon:
                self.setup_tray_icon()
            
            # 延迟最小化，确保窗口已经显示
            QTimer.singleShot(100, self.minimize_to_tray_after_startup)
        else:
            # 如果不需要最小化到托盘，只初始化托盘图标但不最小化
            if not self.tray_icon:
                self.setup_tray_icon()

    def minimize_to_tray_after_startup(self):
        """启动后最小化到托盘"""
        if hasattr(self, 'tray_icon') and self.tray_icon and self.tray_icon.isVisible():
            self.hide()
            self.tray_icon.showMessage(
                '多功能计时器',
                '程序已最小化到系统托盘',
                QSystemTrayIcon.Information,
                2000
            )

    def load_settings(self):
        """加载设置"""
        settings = self.settings_manager.settings
        
        # 加载窗口状态
        if settings['window_geometry']:
            self.restoreGeometry(QByteArray.fromHex(settings['window_geometry'].encode()))
        if settings['window_state']:
            self.restoreState(QByteArray.fromHex(settings['window_state'].encode()))
        
        # 加载声音设置
        self.mute_checkbox.setChecked(settings['muted'])
        self.volume_slider.setValue(settings['volume'])
        self.volume_label.setText(f"{settings['volume']}%")
        
        # 加载铃声设置 - 设置初始化标记
        self._is_initializing = True
        try:
            if settings['sound_file'] != 'default':
                self.sound_combo.setCurrentText('自定义铃声...')
                # 这里会自动触发 change_sound 方法
            else:
                self.sound_combo.setCurrentText('默认铃声')
        finally:
            self._is_initializing = False
        
        # 加载窗口置顶设置
        self.always_on_top_checkbox.setChecked(settings['always_on_top'])
        self.toggle_always_on_top()

        # 新增：加载最小化到托盘设置
        self.minimize_to_tray_checkbox.setChecked(settings.get('minimize_to_tray', False))

        # 加载提醒方式设置
        if 'window_shake' in settings:
            self.window_shake_checkbox.setChecked(settings['window_shake'])
        if 'window_flash' in settings:
            self.window_flash_checkbox.setChecked(settings['window_flash'])
        if 'taskbar_flash' in settings:
            self.taskbar_flash_checkbox.setChecked(settings['taskbar_flash'])
        if 'show_alert_dialog' in settings:
            self.alert_dialog_checkbox.setChecked(settings['show_alert_dialog'])

        # 加载最近计时器
        self.update_recent_list()
    
    def save_current_settings(self):
        """保存当前设置"""
        self.settings_manager.update_setting('window_geometry', self.saveGeometry().toHex().data().decode())
        self.settings_manager.update_setting('window_state', self.saveState().toHex().data().decode())
        self.settings_manager.update_setting('muted', self.mute_checkbox.isChecked())
        self.settings_manager.update_setting('volume', self.volume_slider.value())
        self.settings_manager.update_setting('always_on_top', self.always_on_top_checkbox.isChecked())
        # 新增：保存最小化到托盘设置
        self.settings_manager.update_setting('minimize_to_tray', self.minimize_to_tray_checkbox.isChecked())
        # 新增：保存提醒方式设置
        self.settings_manager.update_setting('window_shake', self.window_shake_checkbox.isChecked())
        self.settings_manager.update_setting('window_flash', self.window_flash_checkbox.isChecked())
        self.settings_manager.update_setting('taskbar_flash', self.taskbar_flash_checkbox.isChecked())
        self.settings_manager.update_setting('show_alert_dialog', self.alert_dialog_checkbox.isChecked())
    
    def start_timer(self):
        """开始计时"""
        print("开始计时器，尝试显示任务栏进度条")

        if self.timer_thread and self.timer_thread.isRunning():
            self.timer_thread.stop()
        
        self.current_timer_type = 'timer'
        self.current_duration = 0  # 计时器没有固定时长

        # 更新计时器状态为运行中
        self.timer_state = 'running'
        self.update_timer_display_style()

        self.timer_thread = TimerThread(0, False)
        self.timer_thread.update_signal.connect(self.update_timer_display)
        self.timer_thread.alarm_signal.connect(self.alarm_triggered)
        self.timer_thread.start()
        
        # 新增：如果时间显示窗口存在，连接信号
        if self.time_display_window:
            # 断开之前的连接（如果存在）
            try:
                self.timer_thread.update_signal.disconnect()
            except:
                pass
            # 重新连接，同时更新主窗口和时间显示窗口
            self.timer_thread.update_signal.connect(self.update_timer_display)
            self.timer_thread.update_signal.connect(
                lambda t, p: self.time_display_window.update_time(t, p) 
                if self.time_display_window else None
            )
            self.time_display_window.update_time_style('running')
        
        self.start_timer_btn.setEnabled(False)
        self.pause_timer_btn.setEnabled(True)
        self.reset_timer_btn.setEnabled(True)
        self.status_bar.showMessage('计时器运行中...')
        
        # 新增：显示任务栏进度条（不确定模式）
        print("调用 show_taskbar_progress 显示进度条")
        self.show_taskbar_progress(True, 'indeterminate')
    
    def pause_timer(self):
        """暂停计时"""
        if self.timer_thread and self.timer_thread.isRunning():
            if not self.timer_thread.is_paused:
                self.timer_thread.pause()
                self.pause_timer_btn.setText('继续')
                self.status_bar.showMessage('计时器已暂停')
            
                # 更新计时器状态为暂停
                self.timer_state = 'paused'
                self.update_timer_display_style()
            
                # 新增：如果时间显示窗口存在，更新状态
                if self.time_display_window:
                    self.time_display_window.update_time_style('paused')
            
                # 新增：暂停时显示黄色进度条
                if hasattr(self, 'taskbar_progress') and self.taskbar_progress:
                    try:
                        self.taskbar_progress.pause()
                    except Exception as e:
                        print(f"暂停任务栏进度条失败: {e}")
            else:
                self.timer_thread.resume()
                self.pause_timer_btn.setText('暂停')
                self.status_bar.showMessage('计时器运行中...')
            
                # 更新计时器状态为运行中
                self.timer_state = 'running'
                self.update_timer_display_style()

                # 新增：如果时间显示窗口存在，更新状态
                if self.time_display_window:
                    self.time_display_window.update_time_style('running')
            
                # 新增：恢复时继续显示进度条
                if hasattr(self, 'taskbar_progress') and self.taskbar_progress:
                    try:
                        self.taskbar_progress.resume()
                    except Exception as e:
                        print(f"恢复任务栏进度条失败: {e}")
    
    def reset_timer(self):
        """重置计时"""
        if self.timer_thread:
            self.timer_thread.stop()
        
        self.timer_display.setText('00:00:00')
        self.timer_progress.setValue(0)
    
        # 更新计时器状态为停止
        self.timer_state = 'stopped'
        self.update_timer_display_style()
    
        self.start_timer_btn.setEnabled(True)
        self.pause_timer_btn.setEnabled(False)
        self.pause_timer_btn.setText('暂停')
        self.reset_timer_btn.setEnabled(True)
        
        # 新增：如果时间显示窗口存在，更新状态
        if self.time_display_window:
            self.time_display_window.update_time('00:00:00')
            self.time_display_window.update_time_style('stopped')
        
        # 新增：隐藏任务栏进度
        self.show_taskbar_progress(False)
        
        self.status_bar.showMessage('计时器已重置')
    
    def start_countdown(self):
        """开始倒计时"""
        hours = self.hour_spin.value()
        minutes = self.minute_spin.value()
        seconds = self.second_spin.value()
        
        total_seconds = hours * 3600 + minutes * 60 + seconds
        
        if total_seconds <= 0:
            QMessageBox.warning(self, '警告', '请设置大于0的时间')
            return
        
        if self.timer_thread and self.timer_thread.isRunning():
            self.timer_thread.stop()
        
        self.current_timer_type = 'countdown'
        self.current_duration = total_seconds

        # 更新倒计时状态为运行中
        self.countdown_state = 'running'
        self.update_countdown_display_style()
        
        # 添加到最近使用列表
        self.add_to_recent_timers(total_seconds)
        
        # 更新系统托盘提示
        if hasattr(self, 'tray_icon'):
            self.tray_icon.setToolTip(f'倒计时: {self.seconds_to_time_str(total_seconds)}')
        
        self.timer_thread = TimerThread(total_seconds, True)
        self.timer_thread.update_signal.connect(self.update_countdown_display)
        self.timer_thread.alarm_signal.connect(self.alarm_triggered)
        self.timer_thread.start()
        
        # 新增：如果时间显示窗口存在，连接信号
        if self.time_display_window:
            # 断开之前的连接（如果存在）
            try:
                self.timer_thread.update_signal.disconnect()
            except:
                pass
            # 重新连接，同时更新主窗口和时间显示窗口
            self.timer_thread.update_signal.connect(self.update_countdown_display)
            self.timer_thread.update_signal.connect(
                lambda t, p: self.time_display_window.update_time(t, p) 
                if self.time_display_window else None
            )
            self.time_display_window.update_time_style('running')
        
        self.start_countdown_btn.setEnabled(False)
        self.pause_countdown_btn.setEnabled(True)
        self.reset_countdown_btn.setEnabled(True)
        self.status_bar.showMessage(f'倒计时开始: {self.seconds_to_time_str(total_seconds)}')
        
        # 新增：显示任务栏进度条（确定模式，从0开始）
        print(f"开始倒计时，显示任务栏进度条，总时长: {total_seconds}秒")
        self.show_taskbar_progress(True, 'determinate')
        self.update_taskbar_progress(0)
        
    def pause_countdown(self):
        """暂停倒计时"""
        if self.timer_thread and self.timer_thread.isRunning():
            if not self.timer_thread.is_paused:
                self.timer_thread.pause()
                self.pause_countdown_btn.setText('继续')
                self.status_bar.showMessage('倒计时已暂停')
            
                # 更新倒计时状态为暂停
                self.countdown_state = 'paused'
                self.update_countdown_display_style()
            
                # 新增：如果时间显示窗口存在，更新状态
                if self.time_display_window:
                    self.time_display_window.update_time_style('paused')
            
                # 新增：暂停时显示黄色进度条
                if self.taskbar_progress:
                    try:
                        self.taskbar_progress.pause()
                    except Exception as e:
                        print(f"暂停任务栏进度条失败: {e}")
            else:
                self.timer_thread.resume()
                self.pause_countdown_btn.setText('暂停')
                self.status_bar.showMessage('倒计时运行中...')
            
                # 更新倒计时状态为运行中
                self.countdown_state = 'running'
                self.update_countdown_display_style()
            
                # 新增：如果时间显示窗口存在，更新状态
                if self.time_display_window:
                    self.time_display_window.update_time_style('running')
            
                # 新增：恢复时继续显示进度条
                if self.taskbar_progress:
                    try:
                        self.taskbar_progress.resume()
                    except Exception as e:
                        print(f"恢复任务栏进度条失败: {e}")
    
    def reset_countdown(self):
        """重置倒计时"""
        if self.timer_thread:
            self.timer_thread.stop()
        
        hours = self.hour_spin.value()
        minutes = self.minute_spin.value()
        seconds = self.second_spin.value()
        total_seconds = hours * 3600 + minutes * 60 + seconds
        
        self.countdown_display.setText(self.seconds_to_time_str(total_seconds))
        # 重置进度条为0%
        self.countdown_progress.setValue(0)
    
        # 更新倒计时状态为停止
        self.countdown_state = 'stopped'
        self.update_countdown_display_style()
    
        self.start_countdown_btn.setEnabled(True)
        self.pause_countdown_btn.setEnabled(False)
        self.pause_countdown_btn.setText('暂停')
        self.reset_countdown_btn.setEnabled(True)
        
        # 新增：如果时间显示窗口存在，更新状态
        if self.time_display_window:
            self.time_display_window.update_time(self.seconds_to_time_str(total_seconds))
            self.time_display_window.update_time_style('stopped')
        
        # 更新系统托盘提示
        if hasattr(self, 'tray_icon'):
            self.tray_icon.setToolTip('多功能计时器')
        
        # 新增：隐藏任务栏进度
        self.show_taskbar_progress(False)
        
        self.status_bar.showMessage('倒计时已重置')
    
    def set_countdown_time(self, seconds):
        """设置倒计时时间"""
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        self.hour_spin.setValue(hours)
        self.minute_spin.setValue(minutes)
        self.second_spin.setValue(seconds)
        
        self.countdown_display.setText(self.seconds_to_time_str(seconds))
    
        # 设置时间时更新样式为停止状态（蓝色）
        self.countdown_state = 'stopped'
        self.update_countdown_display_style()

        # 新增：如果时间显示窗口存在，更新时间
        if self.time_display_window and self.current_timer_type == 'countdown':
            self.time_display_window.update_time(self.seconds_to_time_str(seconds))

    def update_timer_display(self, time_str, progress):
        """更新计时器显示"""
        self.timer_display.setText(time_str)
        self.timer_progress.setValue(progress)
        
        # 更新系统托盘提示
        if hasattr(self, 'tray_icon') and self.current_timer_type == 'timer':
            self.tray_icon.setToolTip(f'计时器: {time_str}')
        
        # 新增：更新任务栏进度
        if hasattr(self, 'taskbar_progress') and self.taskbar_progress:
            # 计时器没有固定时长，使用不确定模式
            if progress >= 100:
                # 如果超过100%，重置为不确定模式
                self.show_taskbar_progress(True, 'indeterminate')
            else:
                # 显示具体进度
                self.update_taskbar_progress(progress)
    
    def update_countdown_display(self, time_str, progress):
        """更新倒计时显示"""
        self.countdown_display.setText(time_str)
        self.countdown_progress.setValue(progress)
        
        # 更新系统托盘提示
        if hasattr(self, 'tray_icon') and self.current_timer_type == 'countdown':
            self.tray_icon.setToolTip(f'倒计时: {time_str}')
        
        # 新增：更新任务栏进度
        if self.taskbar_progress:
            self.update_taskbar_progress(progress)
    
    # ===== 新增：多种提醒方式 =====
    
    def shake_window(self, duration=1000, intensity=5):
        """窗口抖动效果"""
        try:
            original_pos = self.pos()
            self.shake_animation = QPropertyAnimation(self, b"pos")
            self.shake_animation.setDuration(duration)
            self.shake_animation.setLoopCount(2)  # 循环2次
            
            # 创建关键帧
            key_values = [
                (0, original_pos),
                (0.1, original_pos + QPoint(intensity, intensity)),
                (0.2, original_pos + QPoint(-intensity, 0)),
                (0.3, original_pos + QPoint(0, -intensity)),
                (0.4, original_pos + QPoint(-intensity, 0)),
                (0.5, original_pos + QPoint(intensity, intensity)),
                (0.6, original_pos + QPoint(0, -intensity)),
                (0.7, original_pos + QPoint(-intensity, intensity)),
                (0.8, original_pos + QPoint(intensity, 0)),
                (0.9, original_pos + QPoint(0, intensity)),
                (1.0, original_pos)
            ]
            
            for key, value in key_values:
                self.shake_animation.setKeyValueAt(key, value)
            
            self.shake_animation.start()
            print("窗口抖动效果已启动")
        except Exception as e:
            print(f"窗口抖动失败: {e}")
    
    def flash_window(self, times=5, interval=300):
        """窗口闪烁效果"""
        try:
            if self.flash_timer and self.flash_timer.isActive():
                self.flash_timer.stop()
            
            self.flash_count = 0
            self.flash_times = times * 2  # 闪烁和恢复各算一次
            
            # 保存原始样式
            self.original_style = self.styleSheet() if hasattr(self, 'original_style') and self.original_style else ""
            
            def flash():
                if self.flash_count < self.flash_times:
                    if self.flash_count % 2 == 0:
                        # 红色边框闪烁
                        self.setStyleSheet("""
                            QMainWindow {
                                border: 5px solid #ff4444;
                            }
                        """)
                    else:
                        # 恢复原始样式
                        if self.original_style:
                            self.setStyleSheet(self.original_style)
                        else:
                            self.setStyleSheet("")
                    
                    self.flash_count += 1
                else:
                    if self.flash_timer:
                        self.flash_timer.stop()
                    if self.original_style:
                        self.setStyleSheet(self.original_style)
            
            self.flash_timer = QTimer()
            self.flash_timer.timeout.connect(flash)
            self.flash_timer.start(interval)
            print("窗口闪烁效果已启动")
        except Exception as e:
            print(f"窗口闪烁失败: {e}")
    
    def flash_taskbar(self, times=10, interval=500):
        """任务栏图标闪烁提醒（仅Windows）"""
        if sys.platform == 'win32':
            try:
                import ctypes
                
                def flash_icon(flash=True):
                    try:
                        if flash:
                            # 闪烁窗口
                            ctypes.windll.user32.FlashWindow(int(self.winId()), True)
                        else:
                            # 停止闪烁
                            ctypes.windll.user32.FlashWindow(int(self.winId()), False)
                    except Exception as e:
                        print(f"FlashWindow调用失败: {e}")
                
                # 停止现有的计时器
                if self.taskbar_timer and self.taskbar_timer.isActive():
                    self.taskbar_timer.stop()
                
                # 开始闪烁
                self.flash_count = 0
                self.taskbar_timer = QTimer()
                
                def taskbar_flash():
                    if self.flash_count < times * 2:
                        flash_icon(self.flash_count % 2 == 0)
                        self.flash_count += 1
                    else:
                        if self.taskbar_timer:
                            self.taskbar_timer.stop()
                        flash_icon(False)
                
                self.taskbar_timer.timeout.connect(taskbar_flash)
                self.taskbar_timer.start(interval)
                print("任务栏闪烁效果已启动")
            except Exception as e:
                print(f"任务栏闪烁失败: {e}")
    
    def show_system_notification(self, title="时间到！", message="计时器/倒计时已结束"):
        """显示系统通知"""
        try:
            if hasattr(self, 'tray_icon') and self.tray_icon and QSystemTrayIcon.isSystemTrayAvailable():
                # 使用系统托盘图标显示通知
                self.tray_icon.showMessage(
                    title,
                    message,
                    QSystemTrayIcon.Critical,  # 使用严重级别图标
                    5000  # 显示5秒
                )
                print("系统通知已发送")
            else:
                # 如果没有托盘图标，则使用QMessageBox
                QMessageBox.warning(self, title, message)
        except Exception as e:
            print(f"显示系统通知失败: {e}")
    
    def show_alert_dialog(self):
        """显示更醒目的提醒对话框"""
        try:
            # 创建自定义对话框
            dialog = QDialog(self)
            dialog.setWindowTitle("⏰ 时间到！")
            dialog.setWindowFlags(
                Qt.Dialog | 
                Qt.WindowStaysOnTopHint | 
                Qt.CustomizeWindowHint | 
                Qt.WindowTitleHint
            )
            dialog.setModal(True)
            
            # 设置大小
            dialog.setFixedSize(400, 250)
            
            # 设置背景色和样式
            dialog.setStyleSheet("""
                QDialog {
                    background-color: #ff4444;
                    border: 3px solid #ff0000;
                    border-radius: 10px;
                }
                QLabel {
                    color: white;
                }
                QPushButton {
                    background-color: white;
                    color: #ff4444;
                    border: 2px solid white;
                    border-radius: 5px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #ffeeee;
                }
            """)
            
            layout = QVBoxLayout(dialog)
            layout.setSpacing(20)
            layout.setContentsMargins(30, 30, 30, 30)
            
            # 大图标
            icon_label = QLabel()
            icon_pixmap = self.style().standardIcon(QStyle.SP_MessageBoxWarning).pixmap(64, 64)
            icon_label.setPixmap(icon_pixmap)
            icon_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(icon_label)
            
            # 标题
            title_label = QLabel("时间到！")
            title_label.setAlignment(Qt.AlignCenter)
            title_font = QFont()
            title_font.setPointSize(24)
            title_font.setBold(True)
            title_label.setFont(title_font)
            layout.addWidget(title_label)
            
            # 消息
            timer_type = "倒计时" if self.current_timer_type == 'countdown' else "计时器"
            message_label = QLabel(f"{timer_type}已结束")
            message_label.setAlignment(Qt.AlignCenter)
            message_font = QFont()
            message_font.setPointSize(16)
            message_label.setFont(message_font)
            layout.addWidget(message_label)
            
            # 按钮
            button_box = QDialogButtonBox(QDialogButtonBox.Ok)
            button_box.accepted.connect(dialog.accept)
            button_box.setCenterButtons(True)
            ok_button = button_box.button(QDialogButtonBox.Ok)
            ok_button.setText("知道了")
            ok_button.setMinimumSize(100, 40)
            
            layout.addWidget(button_box)
            
            # 设置对话框位置（屏幕中央）
            screen_geometry = QApplication.desktop().screenGeometry()
            dialog.move(
                (screen_geometry.width() - dialog.width()) // 2,
                (screen_geometry.height() - dialog.height()) // 2
            )
            
            # 显示对话框
            dialog.exec_()
            print("醒目提醒对话框已显示")
        except Exception as e:
            print(f"显示提醒对话框失败: {e}")
    
    def test_alarm_effects(self):
        """测试提醒效果"""
        try:
            # 暂时禁用声音，避免测试时发出声音
            original_mute_state = self.mute_checkbox.isChecked()
            self.mute_checkbox.setChecked(True)
            
            # 测试各种提醒效果
            self.show_system_notification("测试提醒", "正在测试提醒效果...")
            
            if self.window_shake_checkbox.isChecked():
                self.shake_window(duration=800, intensity=5)
            
            if self.window_flash_checkbox.isChecked():
                self.flash_window(times=3, interval=200)
            
            if self.taskbar_flash_checkbox.isChecked() and sys.platform == 'win32':
                self.flash_taskbar(times=4, interval=300)
            
            if self.alert_dialog_checkbox.isChecked():
                QTimer.singleShot(1000, self.show_alert_dialog)
            
            # 恢复原来的静音状态
            QTimer.singleShot(2000, lambda: self.mute_checkbox.setChecked(original_mute_state))
            
            self.status_bar.showMessage('提醒效果测试中...')
        except Exception as e:
            print(f"测试提醒效果失败: {e}")
    
    def toggle_window_shake(self, state):
        """切换窗口抖动设置"""
        self.settings_manager.update_setting('window_shake', bool(state))
    
    def toggle_window_flash(self, state):
        """切换窗口闪烁设置"""
        self.settings_manager.update_setting('window_flash', bool(state))
    
    def toggle_taskbar_flash(self, state):
        """切换任务栏闪烁设置"""
        self.settings_manager.update_setting('taskbar_flash', bool(state))
    
    def toggle_alert_dialog(self, state):
        """切换提醒对话框设置"""
        self.settings_manager.update_setting('show_alert_dialog', bool(state))
            
    def alarm_triggered(self):
        """闹钟触发"""
        try:
            print("闹钟触发，开始执行提醒效果")
            
            # 显示窗口到最前面
            self.show_window()
            
            # 播放声音（如果不静音）
            if not self.mute_checkbox.isChecked():
                self.play_alarm_sound()
            
            # 更新进度条为100%
            if self.current_timer_type == 'countdown':
                self.countdown_progress.setValue(100)
            elif self.current_timer_type == 'timer':
                self.timer_progress.setValue(100)
            
            # ===== 新增多种提醒方式 =====
            
            # 1. 窗口抖动（如果启用）
            if self.window_shake_checkbox.isChecked():
                self.shake_window(duration=1500, intensity=8)
            
            # 2. 窗口闪烁（如果启用）
            if self.window_flash_checkbox.isChecked():
                self.flash_window(times=6, interval=250)
            
            # 3. 系统通知（总是显示）
            timer_type = "倒计时" if self.current_timer_type == 'countdown' else "计时器"
            self.show_system_notification(
                title="⏰ 时间到！", 
                message=f"{timer_type}已结束"
            )
            
            # 4. 任务栏闪烁（Windows，如果启用）
            if (self.taskbar_flash_checkbox.isChecked() and 
                sys.platform == 'win32'):
                self.flash_taskbar(times=8, interval=400)
            
            # 5. 显示醒目的弹窗（如果启用）
            if self.alert_dialog_checkbox.isChecked():
                QTimer.singleShot(500, self.show_alert_dialog)
            
            # ===== 原有功能保持 =====
            
            # 新增：时间到时显示绿色完成状态
            if hasattr(self, 'taskbar_progress') and self.taskbar_progress:
                try:
                    self.update_taskbar_progress(100)
                    QTimer.singleShot(3000, lambda: self.show_taskbar_progress(False))
                except Exception as e:
                    print(f"设置任务栏完成状态失败: {e}")
            
            # 重置对应的控件
            if self.current_timer_type == 'timer':
                # 时间到时显示红色（停止状态）
                self.timer_state = 'stopped'
                self.update_timer_display_style()
                QTimer.singleShot(1000, self.reset_timer)
            elif self.current_timer_type == 'countdown':
                # 时间到时显示红色（停止状态）
                self.countdown_state = 'stopped'
                self.update_countdown_display_style()
                QTimer.singleShot(1000, self.reset_countdown)
            
            # 更新系统托盘提示
            if hasattr(self, 'tray_icon'):
                self.tray_icon.setToolTip('多功能计时器')
            
            # 新增：更新时间显示窗口
            if self.time_display_window:
                self.time_display_window.update_time_style('stopped')
            
            self.status_bar.showMessage('时间到！')
            print("所有提醒效果已执行完毕")
            
        except Exception as e:
            print(f"闹钟触发过程中出错: {e}")
            import traceback
            traceback.print_exc()
        
    def play_alarm_sound(self):
        """播放闹钟声音"""
        try:
            sound_file = self.settings_manager.settings.get('sound_file', 'default')
            volume = self.settings_manager.settings.get('volume', 100)
            
            if sound_file != 'default' and os.path.exists(sound_file):
                # 检查文件格式
                supported_formats = ['.wav', '.mp3', '.ogg', '.flac', '.aac', '.m4a']
                file_ext = os.path.splitext(sound_file)[1].lower()
                
                if file_ext in supported_formats:
                    try:
                        # 优先使用QMediaPlayer（如果可用）
                        if self.media_player and hasattr(self.media_player, 'setMedia'):
                            from PyQt5.QtCore import QUrl
                            from PyQt5.QtMultimedia import QMediaContent
                            
                            # 设置音量
                            self.media_player.setVolume(volume)
                            
                            # 创建媒体内容
                            media_content = QMediaContent(QUrl.fromLocalFile(sound_file))
                            self.media_player.setMedia(media_content)
                            
                            # 播放
                            self.media_player.play()
                            print(f"使用QMediaPlayer播放: {os.path.basename(sound_file)}")
                            
                            # 监听播放完成
                            self.media_player.mediaStatusChanged.connect(
                                lambda status: print(f"播放状态: {status}")
                            )
                            
                        elif sound_file.lower().endswith('.wav'):
                            # 回退到QSound（只支持WAV）
                            sound = QSound(sound_file)
                            sound.play()
                            print(f"使用QSound播放WAV文件: {sound_file}")
                        else:
                            # 对于其他格式，使用系统默认播放器
                            print(f"使用系统播放器: {sound_file}")
                            QApplication.beep()
                            
                    except Exception as e:
                        print(f"播放自定义声音失败: {e}，使用系统提示音")
                        QApplication.beep()
                else:
                    print(f"不支持的文件格式: {sound_file}，使用系统提示音")
                    QApplication.beep()
            else:
                # 使用系统提示音
                QApplication.beep()
                print("播放默认系统提示音")
                
        except Exception as e:
            print(f"播放声音失败: {e}")
            QApplication.beep()
    
    def toggle_mute(self, state):
        """切换静音"""
        self.settings_manager.update_setting('muted', bool(state))
    
    def change_volume(self, value):
        """改变音量"""
        self.volume_label.setText(f"{value}%")
        self.settings_manager.update_setting('volume', value)
    
    def change_sound(self, sound_name):
        """改变铃声"""
        if sound_name == '自定义铃声...':
            # 检查是否是程序初始化阶段
            if hasattr(self, '_is_initializing') and self._is_initializing:
                # 初始化阶段，直接设置而不弹出对话框
                sound_file = self.settings_manager.settings.get('sound_file', 'default')
                if sound_file != 'default' and os.path.exists(sound_file):
                    # 验证文件格式
                    supported_extensions = ['.wav', '.mp3', '.ogg', '.flac', '.aac', '.m4a']
                    file_ext = os.path.splitext(sound_file)[1].lower()
                    if file_ext not in supported_extensions:
                        # 不支持的格式，恢复默认
                        self.settings_manager.update_setting('sound_file', 'default')
                        self.sound_combo.setCurrentText('默认铃声')
                        print(f"不支持的音频格式: {file_ext}，已恢复默认铃声")
                else:
                    # 文件不存在，恢复默认
                    self.settings_manager.update_setting('sound_file', 'default')
                    self.sound_combo.setCurrentText('默认铃声')
                    print("自定义铃声文件不存在，已恢复默认铃声")
            else:
                # 用户交互：打开文件选择对话框
                self._select_custom_sound()
        else:
            self.settings_manager.update_setting('sound_file', 'default')

    def _select_custom_sound(self):
        """选择自定义铃声文件"""
        # 定义支持的音频格式
        supported_formats = [
            '所有文件 (*.*)',
            'WAV文件 (*.wav)',
            'MP3文件 (*.mp3)',
            'OGG文件 (*.ogg)',
            'FLAC文件 (*.flac)',
            'AAC文件 (*.aac *.m4a)'
        ]
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, '选择铃声文件', '',
            ';;'.join(supported_formats)
        )
        
        if file_path:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                QMessageBox.warning(self, '错误', '文件不存在！')
                self.sound_combo.setCurrentText('默认铃声')
                return
                
            # 检查文件大小（限制在10MB以内）
            file_size = os.path.getsize(file_path)
            if file_size > 10 * 1024 * 1024:  # 10MB
                QMessageBox.warning(
                    self, '文件过大',
                    '音频文件过大（超过10MB），请选择较小的文件。'
                )
                self.sound_combo.setCurrentText('默认铃声')
                return
            
            # 检查文件格式
            supported_extensions = ['.wav', '.mp3', '.ogg', '.flac', '.aac', '.m4a']
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext in supported_extensions:
                self.settings_manager.update_setting('sound_file', file_path)
                self.status_bar.showMessage(f'已选择自定义铃声: {os.path.basename(file_path)}')
                
                # 测试播放
                QTimer.singleShot(500, self.test_sound)
            else:
                QMessageBox.warning(
                    self, '不支持的格式',
                    f'不支持的文件格式: {file_ext}\n'
                    f'支持的格式: {", ".join(supported_extensions)}'
                )
                self.sound_combo.setCurrentText('默认铃声')
        else:
            self.sound_combo.setCurrentText('默认铃声')
    
    def test_sound(self):
        """测试声音"""
        try:
            # 临时关闭静音，播放测试声音
            original_mute_state = self.mute_checkbox.isChecked()
            
            # 如果当前是静音状态，临时取消静音
            if original_mute_state:
                self.mute_checkbox.setChecked(False)
            
            # 播放声音（添加超时保护）
            self.play_alarm_sound()
            
            # 设置超时恢复
            def restore_mute_state():
                if original_mute_state:
                    self.mute_checkbox.setChecked(original_mute_state)
            
            # 3秒后恢复静音状态
            QTimer.singleShot(3000, restore_mute_state)
            
            self.status_bar.showMessage('正在测试声音...')
            
        except Exception as e:
            print(f"测试声音失败: {e}")
            self.status_bar.showMessage('测试声音失败')
    
    def toggle_always_on_top(self):
        """切换窗口置顶"""
        always_on_top = self.always_on_top_checkbox.isChecked()
        if always_on_top:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        self.show()
        self.settings_manager.update_setting('always_on_top', always_on_top)
    
    def use_preset_timer(self, seconds, name):
        """使用预设计时器"""
        # 切换到倒计时标签页
        self.tab_widget.setCurrentIndex(1)
        
        # 设置时间
        self.set_countdown_time(seconds)
        
        # 开始倒计时
        self.start_countdown()
        
        self.status_bar.showMessage(f'使用预设: {name}')
    
    def add_preset_timer(self):
        """添加预设计时器"""
        name = self.preset_name_edit.text().strip()
        seconds = self.preset_time_edit.value()
        
        if not name:
            QMessageBox.warning(self, '警告', '请输入预设名称')
            return
        
        preset_timers = self.settings_manager.settings['preset_timers']
        preset_timers[name] = seconds
        self.settings_manager.update_setting('preset_timers', preset_timers)
        
        # 刷新预设列表
        self.refresh_preset_buttons()
        
        self.preset_name_edit.clear()
        self.status_bar.showMessage(f'预设 "{name}" 已添加')
    
    def refresh_preset_buttons(self):
        """刷新预设按钮"""
        # 清除现有按钮
        for button in self.preset_buttons:
            button.deleteLater()
        self.preset_buttons.clear()
        
        # 获取当前预设
        preset_timers = self.settings_manager.settings['preset_timers']
        
        # 重新创建按钮
        parent_widget = self.preset_buttons[0].parent() if self.preset_buttons else None
        if parent_widget:
            layout = parent_widget.layout()
            row, col = 0, 0
            
            for name, seconds in preset_timers.items():
                btn = QPushButton(f"{name}\n({self.seconds_to_time_str(seconds)})")
                btn.setMinimumHeight(60)
                btn.clicked.connect(lambda checked, s=seconds, n=name: self.use_preset_timer(s, n))
                layout.addWidget(btn, row, col)
                self.preset_buttons.append(btn)
                col += 1
                if col > 2:
                    col = 0
                    row += 1
    
    def add_to_recent_timers(self, seconds):
        """添加到最近计时器"""
        recent_timers = self.settings_manager.settings.get('recent_timers', [])
        
        # 移除重复项
        if seconds in recent_timers:
            recent_timers.remove(seconds)
        
        # 添加到开头
        recent_timers.insert(0, seconds)
        
        # 只保留最近的10个
        recent_timers = recent_timers[:10]
        
        self.settings_manager.update_setting('recent_timers', recent_timers)
        self.update_recent_list()
    
    def update_recent_list(self):
        """更新最近计时器列表"""
        self.recent_list.clear()
        recent_timers = self.settings_manager.settings.get('recent_timers', [])
        
        for seconds in recent_timers:
            item_text = f"{self.seconds_to_time_str(seconds)}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, seconds)
            self.recent_list.addItem(item)
    
    def select_recent_timer(self, item):
        """选择最近计时器"""
        seconds = item.data(Qt.UserRole)
        self.set_countdown_time(seconds)
        self.tab_widget.setCurrentIndex(1)  # 切换到倒计时标签页
    
    def reset_settings(self):
        """重置设置"""
        reply = QMessageBox.question(
            self, '确认重置',
            '确定要重置所有设置为默认值吗？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.settings_manager.settings = self.settings_manager.default_settings.copy()
            self.settings_manager.save_settings()
            self.load_settings()
            
            QMessageBox.information(self, '完成', '设置已重置为默认值')
    
    def seconds_to_time_str(self, seconds):
        """秒数转换为时间字符串"""
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def close_application(self):
        """关闭应用程序"""
        self.save_current_settings()
        QApplication.quit()

    def toggle_minimize_to_tray(self, state):
        """切换最小化到托盘设置"""
        self.settings_manager.update_setting('minimize_to_tray', bool(state))

    def init_taskbar_progress(self):
        """初始化任务栏进度条（Windows特效）"""
        # 先确保属性存在，即使初始化失败
        self.taskbar_button = None
        self.taskbar_progress = None
        
        try:
            # 检查是否在Windows系统上并且支持任务栏进度条
            if sys.platform == 'win32' and HAS_WIN_EXTRAS:
                print("系统支持Windows任务栏进度条，正在初始化...")
                
                # 创建任务栏按钮和进度条
                self.taskbar_button = QWinTaskbarButton(self)
                self.taskbar_progress = self.taskbar_button.progress()
                
                if self.taskbar_progress:
                    # 初始化进度条状态
                    self.taskbar_progress.setVisible(False)
                    self.taskbar_progress.setRange(0, 100)
                    self.taskbar_progress.setValue(0)
                    print(f"Windows任务栏进度条对象创建成功: {self.taskbar_progress}")
                else:
                    print("警告: 无法创建任务栏进度条对象")
            else:
                if sys.platform != 'win32':
                    print("非Windows系统，任务栏进度条不可用")
                elif not HAS_WIN_EXTRAS:
                    print("Windows系统但缺少QtWinExtras支持，任务栏进度条不可用")
                    
        except Exception as e:
            print(f"初始化任务栏进度条失败: {e}")
            import traceback
            traceback.print_exc()
            # 确保属性为None
            self.taskbar_button = None
            self.taskbar_progress = None

    def show_taskbar_progress(self, show=True, mode='determinate'):
        """显示或隐藏任务栏进度条"""
        # 安全检查
        if not hasattr(self, 'taskbar_progress') or not self.taskbar_progress:
            print("任务栏进度条不可用，无法显示/隐藏")
            return
            
        try:
            if show:
                # 确保窗口句柄已设置
                if hasattr(self.taskbar_button, 'window') and not self.taskbar_button.window():
                    self.setup_taskbar_window_handle()
                
                self.taskbar_progress.setVisible(True)
                if mode == 'indeterminate':
                    self.taskbar_progress.setRange(0, 0)  # 不确定模式
                    self.taskbar_progress.resume()
                    print("任务栏进度条: 显示不确定模式动画")
                elif mode == 'determinate':
                    self.taskbar_progress.setRange(0, 100)  # 确定模式
                    self.taskbar_progress.resume()
                    print("任务栏进度条: 显示确定模式")
            else:
                self.taskbar_progress.setVisible(False)
                self.taskbar_progress.stop()
                print("任务栏进度条: 隐藏")
        except Exception as e:
            print(f"控制任务栏进度条失败: {e}")
            import traceback
            traceback.print_exc()
    
    def update_taskbar_progress(self, value, maximum=100):
        """更新任务栏进度条（确定模式）
        
        Args:
            value: 当前进度值
            maximum: 最大值，默认为100
        """
        # 安全检查
        if not hasattr(self, 'taskbar_progress') or not self.taskbar_progress:
            print("任务栏进度条不可用，无法更新")
            return
            
        try:
            # 确保进度条可见
            if not self.taskbar_progress.isVisible():
                self.taskbar_progress.setVisible(True)
            
            # 更新进度值
            self.taskbar_progress.setRange(0, maximum)
            self.taskbar_progress.setValue(value)
            
            # 确保处于活动状态
            self.taskbar_progress.resume()
            
            print(f"任务栏进度条更新: {value}/{maximum}")
        except Exception as e:
            print(f"更新任务栏进度条失败: {e}")
            import traceback
            traceback.print_exc()

    def setup_taskbar_window_handle(self):
        """设置任务栏进度条的窗口句柄"""
        try:
            if HAS_WIN_EXTRAS and hasattr(self, 'taskbar_button') and self.taskbar_button:
                # 获取窗口的本地句柄
                window_handle = self.windowHandle()
                if window_handle:
                    # 设置窗口关联
                    self.taskbar_button.setWindow(window_handle)
                    print(f"任务栏进度条窗口关联设置成功: window={window_handle}")
                    
                    # 测试进度条功能
                    QTimer.singleShot(500, self.test_taskbar_progress)
                else:
                    print("警告: 无法获取窗口句柄，等待下一次尝试...")
                    # 延迟重试
                    QTimer.singleShot(100, self.setup_taskbar_window_handle)
            else:
                if not HAS_WIN_EXTRAS:
                    print("警告: PyQt5.QtWinExtras 不可用")
                elif not hasattr(self, 'taskbar_button') or not self.taskbar_button:
                    print("警告: 任务栏按钮未初始化")
        except Exception as e:
            print(f"设置任务栏进度条窗口关联失败: {e}")
            import traceback
            traceback.print_exc()

    def test_taskbar_progress(self):
        """测试任务栏进度条功能"""
        if hasattr(self, 'taskbar_progress') and self.taskbar_progress:
            try:
                # 显示进度条并设置为50%以测试
                self.taskbar_progress.setVisible(True)
                self.taskbar_progress.setRange(0, 100)
                self.taskbar_progress.setValue(50)
                self.taskbar_progress.resume()
                
                print("任务栏进度条测试: 显示50%进度")
                
                # 3秒后重置
                QTimer.singleShot(3000, lambda: self.taskbar_progress.setValue(0))
                QTimer.singleShot(3000, lambda: self.taskbar_progress.setVisible(False))
                
            except Exception as e:
                print(f"测试任务栏进度条失败: {e}")

    def init_audio_player(self):
        """初始化音频播放器"""
        try:
            # 尝试使用QMediaPlayer（支持更多格式）
            from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
            from PyQt5.QtCore import QUrl
            
            self.media_player = QMediaPlayer()
            self.media_player.setVolume(100)
            print("QMediaPlayer初始化成功，支持更多音频格式")
        except ImportError as e:
            print(f"QMediaPlayer不可用: {e}")
            self.media_player = None

    def handle_audio_error(self, error):
        """处理音频播放错误"""
        error_messages = {
            0: "没有错误",
            1: "资源错误",
            2: "格式错误",
            3: "网络错误",
            4: "访问被拒绝",
            5: "服务缺失"
        }
        
        error_msg = error_messages.get(error, f"未知错误: {error}")
        print(f"音频播放错误: {error_msg}")
        
        # 回退到系统提示音
        QApplication.beep()

    def cleanup_resources(self):
        """清理资源"""
        try:
            # 停止计时器线程
            if self.timer_thread and self.timer_thread.isRunning():
                self.timer_thread.stop()
                self.timer_thread.wait(2000)  # 等待2秒
            
            # 停止音频播放
            if self.media_player:
                self.media_player.stop()
                
            # 停止所有动画
            if self.shake_animation:
                self.shake_animation.stop()
                
            if self.flash_timer and self.flash_timer.isActive():
                self.flash_timer.stop()
                
            if self.taskbar_timer and self.taskbar_timer.isActive():
                self.taskbar_timer.stop()
                
            # 关闭时间显示窗口
            if self.time_display_window:
                self.time_display_window.close()
                
        except Exception as e:
            print(f"清理资源时出错: {e}")

    def update_countdown_display_style(self):
        """更新倒计时显示的样式"""
        if self.countdown_state == 'stopped':
            # 未开始：蓝色（计时器一样的蓝色）
            style = """
                QLabel#countdownDisplay {
                    color: #2196F3;
                    background-color: #f8f9fa;
                    border: 2px solid #2196F3;
                    border-radius: 10px;
                    padding: 20px;
                    margin: 10px;
                }
            """
        elif self.countdown_state == 'running':
            # 运行中：绿色
            style = """
                QLabel#countdownDisplay {
                    color: #4CAF50;
                    background-color: #f1f8e9;
                    border: 2px solid #4CAF50;
                    border-radius: 10px;
                    padding: 20px;
                    margin: 10px;
                }
            """
        elif self.countdown_state == 'paused':
            # 暂停：黄色
            style = """
                QLabel#countdownDisplay {
                    color: #FF9800;
                    background-color: #fff8e1;
                    border: 2px solid #FF9800;
                    border-radius: 10px;
                    padding: 20px;
                    margin: 10px;
                }
            """
        else:
            # 默认：红色（停止状态）
            style = """
                QLabel#countdownDisplay {
                    color: #FF5722;
                    background-color: #fff3e0;
                    border: 2px solid #FF5722;
                    border-radius: 10px;
                    padding: 20px;
                    margin: 10px;
                }
            """
        
        self.countdown_display.setStyleSheet(style)

    def update_timer_display_style(self):
        """更新计时器显示的样式"""
        if self.timer_state == 'stopped':
            # 未开始：蓝色
            style = """
                QLabel#timerDisplay {
                    color: #2196F3;
                    background-color: #f8f9fa;
                    border: 2px solid #2196F3;
                    border-radius: 10px;
                    padding: 20px;
                    margin: 10px;
                }
            """
        elif self.timer_state == 'running':
            # 运行中：绿色
            style = """
                QLabel#timerDisplay {
                    color: #4CAF50;
                    background-color: #f1f8e9;
                    border: 2px solid #4CAF50;
                    border-radius: 10px;
                    padding: 20px;
                    margin: 10px;
                }
            """
        elif self.timer_state == 'paused':
            # 暂停：黄色
            style = """
                QLabel#timerDisplay {
                    color: #FF9800;
                    background-color: #fff8e1;
                    border: 2px solid #FF9800;
                    border-radius: 10px;
                    padding: 20px;
                    margin: 10px;
                }
            """
        else:
            # 默认：蓝色
            style = """
                QLabel#timerDisplay {
                    color: #2196F3;
                    background-color: #f8f9fa;
                    border: 2px solid #2196F3;
                    border-radius: 10px;
                    padding: 20px;
                    margin: 10px;
                }
            """
        
        self.timer_display.setStyleSheet(style)

    def create_about_tab(self):
        """创建关于标签页"""
        about_tab = QWidget()
        layout = QVBoxLayout(about_tab)
        layout.setSpacing(15)
        
        # 项目图标和标题
        header_layout = QHBoxLayout()
        
        # 图标
        if os.path.exists('icon.ico'):
            icon_label = QLabel()
            icon_pixmap = QIcon('icon.ico').pixmap(64, 64)
            icon_label.setPixmap(icon_pixmap)
            header_layout.addWidget(icon_label)
        else:
            # 使用默认图标
            icon_label = QLabel()
            icon_pixmap = self.style().standardIcon(QStyle.SP_ComputerIcon).pixmap(64, 64)
            icon_label.setPixmap(icon_pixmap)
            header_layout.addWidget(icon_label)
        
        # 标题和版本
        title_layout = QVBoxLayout()
        
        title_label = QLabel(f"<h2>{ProjectInfo.NAME}</h2>")
        title_label.setTextFormat(Qt.RichText)
        title_layout.addWidget(title_label)
        
        version_label = QLabel(f"<b>版本:</b> {ProjectInfo.VERSION}")
        version_label.setTextFormat(Qt.RichText)
        title_layout.addWidget(version_label)
        
        build_label = QLabel(f"<b>构建日期:</b> {ProjectInfo.BUILD_DATE}")
        build_label.setTextFormat(Qt.RichText)
        title_layout.addWidget(build_label)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        # 作者信息
        author_group = QGroupBox("作者信息")
        author_layout = QVBoxLayout()
        
        author_info = QTextBrowser()
        author_info.setMaximumHeight(100)
        author_info.setHtml(f"""
        <p><b>作者:</b> {ProjectInfo.AUTHOR}</p>
        <p><b>许可证:</b> {ProjectInfo.LICENSE}</p>
        <p><b>版权所有:</b> {ProjectInfo.COPYRIGHT}</p>
        <p><b>项目地址:</b> <a href="{ProjectInfo.URL}">{ProjectInfo.URL}</a></p>
        <p><b>维护者邮箱:</b> {ProjectInfo.MAINTAINER_EMAIL}</p>
        """)
        author_info.setOpenExternalLinks(True)
        author_info.setReadOnly(True)
        author_layout.addWidget(author_info)
        
        author_group.setLayout(author_layout)
        layout.addWidget(author_group)
        
        # 版本历史
        history_group = QGroupBox("版本历史")
        history_layout = QVBoxLayout()
        
        history_text = QTextBrowser()
        history_text.setMaximumHeight(200)
        history_html = "<ul>"
        for version, desc in sorted(ProjectInfo.VERSION_HISTORY.items(), key=lambda x: [int(i) for i in x[0].split('.')]):
            history_html += f"<li><b>v{version}:</b> {desc}</li>"
        history_html += "</ul>"
        history_text.setHtml(history_html)
        history_text.setReadOnly(True)
        history_layout.addWidget(history_text)
        
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)
        
        # 主要功能
        features_group = QGroupBox("主要功能")
        features_layout = QVBoxLayout()
        
        features_text = QTextBrowser()
        features_text.setMaximumHeight(150)
        features_html = "<ul>"
        for i, feature in enumerate(ProjectInfo.get_about_info()["features"], 1):
            features_html += f"<li>{feature}</li>"
        features_html += "</ul>"
        features_text.setHtml(features_html)
        features_text.setReadOnly(True)
        features_layout.addWidget(features_text)
        
        features_group.setLayout(features_layout)
        layout.addWidget(features_group)
        
        # 系统要求
        requirements_group = QGroupBox("系统要求")
        requirements_layout = QVBoxLayout()
        
        requirements_text = QTextBrowser()
        requirements_text.setMaximumHeight(100)
        requirements_html = "<ul>"
        for req in ProjectInfo.get_about_info()["system_requirements"]:
            requirements_html += f"<li>{req}</li>"
        requirements_html += "</ul>"
        requirements_text.setHtml(requirements_html)
        requirements_text.setReadOnly(True)
        requirements_layout.addWidget(requirements_text)
        
        requirements_group.setLayout(requirements_layout)
        layout.addWidget(requirements_group)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 查看详细帮助按钮
        help_btn = QPushButton("📖 查看详细帮助")
        help_btn.clicked.connect(self.show_help_dialog)
        help_btn.setMinimumHeight(40)
        button_layout.addWidget(help_btn)
        
        # 详细关于信息按钮
        about_detail_btn = QPushButton("ℹ️ 详细关于信息")
        about_detail_btn.clicked.connect(self.show_about_detail_dialog)
        about_detail_btn.setMinimumHeight(40)
        button_layout.addWidget(about_detail_btn)
        
        layout.addLayout(button_layout)
        
        layout.addStretch()
        self.tab_widget.addTab(about_tab, "ℹ️ 关于")
        
    def show_help_dialog(self):
        """显示详细帮助对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{ProjectInfo.NAME} - 帮助")
        dialog.setMinimumSize(700, 500)
        
        layout = QVBoxLayout(dialog)
        
        # 使用文本浏览器显示帮助内容
        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(True)
        text_browser.setHtml(f"""
        <h1>{ProjectInfo.NAME} 使用帮助</h1>
        <pre>{ProjectInfo.HELP_TEXT}</pre>
        """)
        
        layout.addWidget(text_browser)
        
        # 关闭按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.exec_()

    def show_about_detail_dialog(self):
        """显示详细的关于对话框"""
        ProjectInfo.show_about_dialog(self)

def main():
    app = QApplication(sys.argv)
    app.setApplicationName('多功能计时器')
    
    # 设置中文字体
    font = QFont('Microsoft YaHei', 10)
    app.setFont(font)
    
    window = TimerWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()