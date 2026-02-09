# test_taskbar_progress.py
import sys
import time
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# 尝试导入Windows任务栏相关模块
try:
    from PyQt5.QtWinExtras import QWinTaskbarButton, QWinTaskbarProgress
    HAS_WIN_EXTRAS = True
    print("✓ PyQt5.QtWinExtras 模块可用")
except ImportError as e:
    HAS_WIN_EXTRAS = False
    print(f"✗ PyQt5.QtWinExtras 模块不可用: {e}")

class TaskbarTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.taskbar_button = None
        self.taskbar_progress = None
        
        self.init_ui()
        self.init_taskbar_progress()
        
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle('任务栏进度条测试程序')
        self.setGeometry(300, 300, 400, 300)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # 标题
        title_label = QLabel('Windows 任务栏进度条测试')
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 系统信息
        info_text = f"""
        系统平台: {sys.platform}
        PyQt5.QtWinExtras: {'可用' if HAS_WIN_EXTRAS else '不可用'}
        """
        info_label = QLabel(info_text)
        info_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(info_label)
        
        # 进度条控制
        control_group = QGroupBox('进度控制')
        control_layout = QVBoxLayout()
        
        # 本地进度条
        self.local_progress = QProgressBar()
        self.local_progress.setRange(0, 100)
        control_layout.addWidget(QLabel('本地进度条:'))
        control_layout.addWidget(self.local_progress)
        
        # 进度滑块
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setRange(0, 100)
        self.progress_slider.valueChanged.connect(self.update_progress)
        control_layout.addWidget(QLabel('进度控制:'))
        control_layout.addWidget(self.progress_slider)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        
        # 显示任务栏进度条按钮
        self.show_btn = QPushButton('显示任务栏进度条')
        self.show_btn.clicked.connect(self.show_taskbar_progress)
        button_layout.addWidget(self.show_btn)
        
        # 隐藏按钮
        self.hide_btn = QPushButton('隐藏任务栏进度条')
        self.hide_btn.clicked.connect(self.hide_taskbar_progress)
        button_layout.addWidget(self.hide_btn)
        
        # 不确定模式按钮
        self.indeterminate_btn = QPushButton('不确定模式')
        self.indeterminate_btn.clicked.connect(self.set_indeterminate_mode)
        button_layout.addWidget(self.indeterminate_btn)
        
        layout.addLayout(button_layout)
        
        # 测试按钮
        test_layout = QHBoxLayout()
        
        # 测试动画
        self.animate_btn = QPushButton('测试动画 (0-100%)')
        self.animate_btn.clicked.connect(self.test_animation)
        test_layout.addWidget(self.animate_btn)
        
        # 暂停/恢复
        self.pause_btn = QPushButton('暂停')
        self.pause_btn.clicked.connect(self.toggle_pause)
        test_layout.addWidget(self.pause_btn)
        
        layout.addLayout(test_layout)
        
        # 状态信息
        self.status_label = QLabel('状态: 就绪')
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # 日志文本框
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(100)
        self.log_text.setReadOnly(True)
        layout.addWidget(QLabel('日志:'))
        layout.addWidget(self.log_text)
        
        layout.addStretch()
        
    def init_taskbar_progress(self):
        """初始化任务栏进度条"""
        self.log_message("正在初始化任务栏进度条...")
        
        if sys.platform != 'win32':
            self.log_message(f"✗ 非Windows系统 ({sys.platform})，任务栏进度条仅支持Windows")
            return
            
        if not HAS_WIN_EXTRAS:
            self.log_message("✗ PyQt5.QtWinExtras 模块不可用")
            return
            
        try:
            # 创建任务栏按钮
            self.taskbar_button = QWinTaskbarButton(self)
            self.log_message(f"✓ 创建任务栏按钮: {self.taskbar_button}")
            
            # 获取进度条对象
            self.taskbar_progress = self.taskbar_button.progress()
            self.log_message(f"✓ 创建进度条对象: {self.taskbar_progress}")
            
            # 初始状态
            self.taskbar_progress.setVisible(False)
            self.taskbar_progress.setRange(0, 100)
            self.taskbar_progress.setValue(0)
            
            self.log_message("✓ 任务栏进度条初始化完成")
            self.status_label.setText('状态: 任务栏进度条已初始化')
            
        except Exception as e:
            self.log_message(f"✗ 初始化失败: {e}")
            import traceback
            self.log_message(traceback.format_exc())
            self.taskbar_button = None
            self.taskbar_progress = None
            
    def log_message(self, message):
        """添加日志消息"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        self.log_text.append(log_entry)
        
    def showEvent(self, event):
        """窗口显示事件"""
        super().showEvent(event)
        
        # 窗口显示后设置任务栏按钮的窗口关联
        self.setup_window_handle()
        
    def setup_window_handle(self):
        """设置窗口句柄关联"""
        if not self.taskbar_button:
            self.log_message("✗ 无法设置窗口句柄: 任务栏按钮不存在")
            return
            
        try:
            # 获取窗口句柄
            window_handle = self.windowHandle()
            if window_handle:
                # 设置关联
                self.taskbar_button.setWindow(window_handle)
                self.log_message(f"✓ 设置窗口句柄关联: {window_handle}")
                self.status_label.setText('状态: 窗口句柄已关联')
                
                # 测试一下
                QTimer.singleShot(500, self.test_initial_progress)
            else:
                self.log_message("✗ 无法获取窗口句柄")
                
        except Exception as e:
            self.log_message(f"✗ 设置窗口句柄失败: {e}")
            
    def test_initial_progress(self):
        """初始测试"""
        if self.taskbar_progress:
            try:
                self.taskbar_progress.setVisible(True)
                self.taskbar_progress.setValue(25)
                self.taskbar_progress.resume()
                self.log_message("✓ 初始测试: 显示25%进度")
                
                # 3秒后重置
                QTimer.singleShot(3000, lambda: self.taskbar_progress.setValue(0))
                
            except Exception as e:
                self.log_message(f"✗ 初始测试失败: {e}")
                
    def update_progress(self, value):
        """更新进度"""
        self.local_progress.setValue(value)
        
        if self.taskbar_progress:
            try:
                self.taskbar_progress.setValue(value)
                self.log_message(f"更新进度: {value}%")
            except Exception as e:
                self.log_message(f"✗ 更新任务栏进度失败: {e}")
                
    def show_taskbar_progress(self):
        """显示任务栏进度条"""
        if self.taskbar_progress:
            try:
                self.taskbar_progress.setVisible(True)
                self.taskbar_progress.resume()
                self.log_message("✓ 显示任务栏进度条")
                self.status_label.setText('状态: 任务栏进度条显示中')
            except Exception as e:
                self.log_message(f"✗ 显示失败: {e}")
        else:
            self.log_message("✗ 任务栏进度条不可用")
            
    def hide_taskbar_progress(self):
        """隐藏任务栏进度条"""
        if self.taskbar_progress:
            try:
                self.taskbar_progress.setVisible(False)
                self.taskbar_progress.stop()
                self.log_message("✓ 隐藏任务栏进度条")
                self.status_label.setText('状态: 任务栏进度条已隐藏')
            except Exception as e:
                self.log_message(f"✗ 隐藏失败: {e}")
                
    def set_indeterminate_mode(self):
        """设置为不确定模式"""
        if self.taskbar_progress:
            try:
                self.taskbar_progress.setRange(0, 0)  # 0-0 表示不确定模式
                self.taskbar_progress.setVisible(True)
                self.taskbar_progress.resume()
                self.log_message("✓ 设置为不确定模式 (动画)")
                self.status_label.setText('状态: 不确定模式动画')
            except Exception as e:
                self.log_message(f"✗ 设置不确定模式失败: {e}")
                
    def test_animation(self):
        """测试动画"""
        if not self.taskbar_progress:
            self.log_message("✗ 无法测试: 任务栏进度条不可用")
            return
            
        self.log_message("开始测试动画...")
        
        # 重置为确定模式
        self.taskbar_progress.setRange(0, 100)
        self.taskbar_progress.setVisible(True)
        self.taskbar_progress.resume()
        
        # 创建动画定时器
        self.animation_value = 0
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_step)
        self.animation_timer.start(50)  # 每50ms更新一次
        
        self.log_message("✓ 开始动画测试")
        
    def animate_step(self):
        """动画步骤"""
        if self.animation_value > 100:
            self.animation_timer.stop()
            self.log_message("✓ 动画测试完成")
            self.status_label.setText('状态: 动画测试完成')
            return
            
        if self.taskbar_progress:
            try:
                self.taskbar_progress.setValue(self.animation_value)
                self.local_progress.setValue(self.animation_value)
                self.progress_slider.setValue(self.animation_value)
                self.animation_value += 2
            except Exception as e:
                self.log_message(f"✗ 动画出错: {e}")
                self.animation_timer.stop()
                
    def toggle_pause(self):
        """暂停/恢复"""
        if not self.taskbar_progress:
            self.log_message("✗ 无法暂停: 任务栏进度条不可用")
            return
            
        try:
            if self.taskbar_progress.isPaused():
                self.taskbar_progress.resume()
                self.pause_btn.setText('暂停')
                self.log_message("✓ 恢复进度条")
                self.status_label.setText('状态: 运行中')
            else:
                self.taskbar_progress.pause()
                self.pause_btn.setText('恢复')
                self.log_message("✓ 暂停进度条")
                self.status_label.setText('状态: 已暂停')
        except Exception as e:
            self.log_message(f"✗ 暂停/恢复失败: {e}")

def main():
    app = QApplication(sys.argv)
    
    # 打印更多信息
    print("=" * 50)
    print("任务栏进度条测试程序")
    print("=" * 50)
    print(f"Python版本: {sys.version}")
    print(f"PyQt5版本: {QDate.currentDate().toString()}")
    
    # 测试各种可能的导入方式
    print("\n尝试导入QtWinExtras模块...")
    try:
        import PyQt5.QtWinExtras
        print(f"模块路径: {PyQt5.QtWinExtras.__file__}")
    except Exception as e:
        print(f"导入失败: {e}")
    
    window = TaskbarTestWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()