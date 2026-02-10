import sys
import os
import json
import threading
import time
import datetime
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
            "show_alert_dialog": True
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
        self.setWindowTitle('多功能计时器')
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
        
        # 时间显示
        self.timer_display = QLabel('00:00:00')
        self.timer_display.setAlignment(Qt.AlignCenter)
        display_font = QFont()
        display_font.setPointSize(48)
        display_font.setBold(True)
        self.timer_display.setFont(display_font)
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
        
        # 倒计时显示
        self.countdown_display = QLabel('00:00:00')
        self.countdown_display.setAlignment(Qt.AlignCenter)
        display_font = QFont()
        display_font.setPointSize(48)
        display_font.setBold(True)
        self.countdown_display.setFont(display_font)
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
        
        # 加载铃声设置
        if settings['sound_file'] != 'default':
            self.sound_combo.setCurrentText('自定义铃声...')
        
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
        
        self.timer_thread = TimerThread(0, False)
        self.timer_thread.update_signal.connect(self.update_timer_display)
        self.timer_thread.alarm_signal.connect(self.alarm_triggered)
        self.timer_thread.start()
        
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
        
        self.start_timer_btn.setEnabled(True)
        self.pause_timer_btn.setEnabled(False)
        self.pause_timer_btn.setText('暂停')
        self.reset_timer_btn.setEnabled(True)
        
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
        
        # 添加到最近使用列表
        self.add_to_recent_timers(total_seconds)
        
        # 更新系统托盘提示
        if hasattr(self, 'tray_icon'):
            self.tray_icon.setToolTip(f'倒计时: {self.seconds_to_time_str(total_seconds)}')
        
        self.timer_thread = TimerThread(total_seconds, True)
        self.timer_thread.update_signal.connect(self.update_countdown_display)
        self.timer_thread.alarm_signal.connect(self.alarm_triggered)
        self.timer_thread.start()
        
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
        
        self.start_countdown_btn.setEnabled(True)
        self.pause_countdown_btn.setEnabled(False)
        self.pause_countdown_btn.setText('暂停')
        self.reset_countdown_btn.setEnabled(True)
        
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
                QTimer.singleShot(1000, self.reset_timer)
            elif self.current_timer_type == 'countdown':
                QTimer.singleShot(1000, self.reset_countdown)
            
            # 更新系统托盘提示
            if hasattr(self, 'tray_icon'):
                self.tray_icon.setToolTip('多功能计时器')
            
            self.status_bar.showMessage('时间到！')
            print("所有提醒效果已执行完毕")
            
        except Exception as e:
            print(f"闹钟触发过程中出错: {e}")
            import traceback
            traceback.print_exc()
        
    def play_alarm_sound(self):
        """播放闹钟声音"""
        # 这里可以实现播放自定义声音文件
        # 目前使用系统提示音
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
            file_path, _ = QFileDialog.getOpenFileName(
                self, '选择铃声文件', '', 
                '声音文件 (*.wav *.mp3 *.ogg);;所有文件 (*.*)'
            )
            if file_path:
                self.settings_manager.update_setting('sound_file', file_path)
            else:
                self.sound_combo.setCurrentText('默认铃声')
        else:
            self.settings_manager.update_setting('sound_file', 'default')
    
    def test_sound(self):
        """测试声音"""
        if not self.mute_checkbox.isChecked():
            self.play_alarm_sound()
    
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