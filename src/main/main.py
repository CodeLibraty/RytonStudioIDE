from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QDialogButtonBox,
                            QHBoxLayout, QTextEdit, QLabel, QToolBar, QPushButton, 
                            QFileDialog, QStatusBar, QTabWidget, QSplitter, QLineEdit, QFrame,
                            QDialog, QTreeWidget, QTreeWidgetItem, QStackedWidget, QFormLayout,
                            QSpinBox, QComboBox, QCheckBox, QColorDialog, QGroupBox, QListWidget,
                            QStackedLayout, QButtonGroup)
from PyQt6.QtCore import Qt, QSize, QSettings
from PyQt6.QtGui import QIcon, QFont, QColor, QTextOption, QShortcut, QKeySequence

from widgets.ToolTabs import CodeEditor, FileManagerTab, TerminalTab, WebBrowserTab, GitWidget
from widgets.AIChat import  ChatAssistant
from widgets.RyteCord import CollaborationWidget

import platform
import time
import signal
import sys
import os

class ColorButton(QPushButton):
    def __init__(self, text, default_color):
        super().__init__(text)
        self._color = default_color
        self.clicked.connect(self.choose_color)
        self.update_style()
        
    def choose_color(self):
        color = QColorDialog.getColor(QColor(self._color))
        if color.isValid():
            self._color = color.name()
            self.update_style()
            
    def color(self):
        return self._color
        
    def update_style(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._color};
                color: {'white' if QColor(self._color).lightness() < 128 else 'black'};
            }}
        """)

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.settings = QSettings('RytonStudio Beta', 'Editor')
        self.setWindowTitle("Настройки")
        self.setGeometry(100, 100, 800, 600)

        # Initialize widgets_map
        self.widgets_map = {}
        # Create main layout first
        self.main_layout = QVBoxLayout(self)
        
        # Create horizontal layout for categories and settings
        self.h_layout = QHBoxLayout()
        
        # Setup categories list
        self.category_list = QListWidget()
        self.category_list.addItems([
            "Редактор",
            "Терминал",
            "Внешний вид",
            "Файлы"
        ])
        self.category_list.setFixedWidth(200)
        self.h_layout.addWidget(self.category_list)
        
        # Setup settings stack
        self.settings_stack = QStackedWidget()
        self.h_layout.addWidget(self.settings_stack)
        
        # Add horizontal layout to main layout
        self.main_layout.addLayout(self.h_layout)
        
        # Setup buttons
        self.button_layout = QHBoxLayout()
        self.apply_btn = QPushButton("Применить")
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Отмена")
        
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.apply_btn)
        self.button_layout.addWidget(self.ok_btn)
        self.button_layout.addWidget(self.cancel_btn)
        
        self.main_layout.addLayout(self.button_layout)
        
        # Setup pages
        self.setup_editor_page()
        self.setup_terminal_page()
        self.setup_appearance_page()
        self.setup_files_page()
        
        # Connect signals
        self.category_list.currentRowChanged.connect(self.settings_stack.setCurrentIndex)
        self.apply_btn.clicked.connect(self.apply_settings)
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        
        # Select first category by default
        self.category_list.setCurrentRow(0)

        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        
        # Left panel with categories
        self.category_list = QListWidget()
        self.category_list.addItems([
            "Редактор",
            "Терминал",
            "Внешний вид",
            "Авто сохранение",
        ])
        self.category_list.setFixedWidth(200)
        layout.addWidget(self.category_list)
        
        # Right panel with settings
        self.settings_stack = QStackedWidget()
        self.setup_editor_page()
        self.setup_terminal_page()
        self.setup_appearance_page()
        self.setup_files_page()
        layout.addWidget(self.settings_stack)
        
        # Connect signals
        self.category_list.currentRowChanged.connect(self.settings_stack.setCurrentIndex)
        
        # Buttons
        button_layout = QHBoxLayout()
        apply_btn = QPushButton("Применить")
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Отмена")
        
        apply_btn.clicked.connect(self.apply_settings)
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(apply_btn)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        
        # Add buttons to main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.settings_stack)
        main_layout.addLayout(button_layout)
        
        layout.addLayout(main_layout)

    def setup_editor_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Font settings
        font_group = QGroupBox("Шрифт")
        font_layout = QFormLayout()
        
        self.font_family = QComboBox()
        self.font_family.addItems(["Consolas", "Fira Code", "JetBrains Mono", "Monaco"])
        
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 32)
        
        font_layout.addRow("Шрифт:", self.font_family)
        font_layout.addRow("Размер:", self.font_size)
        font_group.setLayout(font_layout)
        layout.addWidget(font_group)
        
        # Editor behavior
        behavior_group = QGroupBox("Поведение")
        behavior_layout = QVBoxLayout()
        
        self.auto_indent = QCheckBox("Автоматический отступ")
        self.word_wrap = QCheckBox("Перенос строк")
        self.show_line_numbers = QCheckBox("Показывать номера строк")
        
        behavior_layout.addWidget(self.auto_indent)
        behavior_layout.addWidget(self.word_wrap)
        behavior_layout.addWidget(self.show_line_numbers)
        behavior_group.setLayout(behavior_layout)
        layout.addWidget(behavior_group)
        
        layout.addStretch()
        self.settings_stack.addWidget(page)

    def setup_terminal_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Terminal settings
        terminal_group = QGroupBox("Настройки терминала")
        terminal_layout = QFormLayout()
        
        self.shell_path = QLineEdit()
        self.cursor_style = QComboBox()
        self.cursor_style.addItems(["Block", "Underline", "Line"])
        
        self.terminal_font_size = QSpinBox()
        self.terminal_font_size.setRange(8, 32)
        
        terminal_layout.addRow("Оболочка:", self.shell_path)
        terminal_layout.addRow("Курсор:", self.cursor_style)
        terminal_layout.addRow("Размер шрифта:", self.terminal_font_size)
        
        terminal_group.setLayout(terminal_layout)
        layout.addWidget(terminal_group)
        
        layout.addStretch()
        self.settings_stack.addWidget(page)

    def setup_appearance_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Theme settings
        theme_group = QGroupBox("Тема")
        theme_layout = QVBoxLayout()
        
        self.theme_selector = QComboBox()
        self.theme_selector.addItems(["Dark+", "Light+", "Monokai", "GitHub Dark"])
        
        theme_layout.addWidget(self.theme_selector)
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # Colors with default values
        colors_group = QGroupBox("Цвета")
        colors_layout = QVBoxLayout()
        
        self.editor_bg_color = ColorButton("Цвет фона редактора", "#1E1E1E")
        self.editor_fg_color = ColorButton("Цвет текста редактора", "#D4D4D4")
        self.selection_color = ColorButton("Цвет выделения", "#264F78")
        
        colors_layout.addWidget(self.editor_bg_color)
        colors_layout.addWidget(self.editor_fg_color)
        colors_layout.addWidget(self.selection_color)
        
        colors_group.setLayout(colors_layout)
        layout.addWidget(colors_group)
        
        layout.addStretch()
        self.settings_stack.addWidget(page)

    def setup_files_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Auto-save settings
        autosave_group = QGroupBox("Автосохранение")
        autosave_layout = QVBoxLayout()
        
        self.autosave_enabled = QCheckBox("Включить автосохранение")
        self.autosave_interval = QSpinBox()
        self.autosave_interval.setRange(1, 60)
        self.autosave_interval.setSuffix(" мин")
        
        autosave_layout.addWidget(self.autosave_enabled)
        autosave_layout.addWidget(QLabel("Интервал:"))
        autosave_layout.addWidget(self.autosave_interval)
        
        autosave_group.setLayout(autosave_layout)
        layout.addWidget(autosave_group)
        
        layout.addStretch()
        self.settings_stack.addWidget(page)

    def load_current_settings(self):
        # Load editor settings
        self.font_family.setCurrentText(self.settings.value("editor/font_family", "Consolas"))
        self.font_size.setValue(int(self.settings.value("editor/font_size", 14)))
        self.auto_indent.setChecked(self.settings.value("editor/auto_indent", True, type=bool))
        self.word_wrap.setChecked(self.settings.value("editor/word_wrap", False, type=bool))
        self.show_line_numbers.setChecked(self.settings.value("editor/show_line_numbers", True, type=bool))
        
        # Load terminal settings
        self.shell_path.setText(self.settings.value("terminal/shell", "/bin/bash"))
        self.cursor_style.setCurrentText(self.settings.value("terminal/cursor_style", "Block"))
        self.terminal_font_size.setValue(int(self.settings.value("terminal/font_size", 12)))
        
        # Load appearance settings
        self.theme_selector.setCurrentText(self.settings.value("appearance/theme", "Dark+"))
        
        # Load file settings
        self.autosave_enabled.setChecked(self.settings.value("files/autosave_enabled", False, type=bool))
        self.autosave_interval.setValue(int(self.settings.value("files/autosave_interval", 5)))

    def apply_settings(self):
        # Save editor settings
        self.settings.setValue("editor/font_family", self.font_family.currentText())
        self.settings.setValue("editor/font_size", self.font_size.value())
        self.settings.setValue("editor/auto_indent", self.auto_indent.isChecked())
        self.settings.setValue("editor/word_wrap", self.word_wrap.isChecked())
        self.settings.setValue("editor/show_line_numbers", self.show_line_numbers.isChecked())
        
        # Save terminal settings
        self.settings.setValue("terminal/shell", self.shell_path.text())
        self.settings.setValue("terminal/cursor_style", self.cursor_style.currentText())
        self.settings.setValue("terminal/font_size", self.terminal_font_size.value())
        
        # Save appearance settings
        self.settings.setValue("appearance/theme", self.theme_selector.currentText())
        
        # Save file settings
        self.settings.setValue("files/autosave_enabled", self.autosave_enabled.isChecked())
        self.settings.setValue("files/autosave_interval", self.autosave_interval.value())
        
        # Apply settings to editor
        self.apply_editor_settings()
        self.apply_terminal_settings()
        self.apply_appearance_settings()
        
        self.settings.sync()

    def apply_editor_settings(self):
        if hasattr(self.parent, 'code_editor'):
            font = QFont(self.font_family.currentText(), self.font_size.value())
            self.parent.code_editor.setFont(font)
            self.parent.code_editor.setWordWrapMode(
                QTextOption.WrapMode.WordWrap if self.word_wrap.isChecked() 
                else QTextOption.WrapMode.NoWrap
            )

    def apply_terminal_settings(self):
        if hasattr(self.parent, 'terminal'):
            self.parent.terminal.update_settings(
                shell_path=self.shell_path.text(),
                cursor_style=self.cursor_style.currentText(),
                font_size=self.terminal_font_size.value()
            )

    def apply_appearance_settings(self):
        theme = self.theme_selector.currentText()
        if theme == "Dark+":
            self.apply_dark_theme()
        elif theme == "Light+":
            self.apply_light_theme()
        elif theme == "Monokai":
            self.apply_monokai_theme()
        elif theme == "GitHub Dark":
            self.apply_github_dark_theme()

    def apply_dark_theme(self):
        self.parent.setStyleSheet("""
            QMainWindow, QDialog {
                background-color: #1E1E1E;
                color: #D4D4D4;
            }
            QTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                selection-background-color: #264F78;
            }
        """)

    def apply_light_theme(self):
        self.parent.setStyleSheet("""
            QMainWindow, QDialog {
                background-color: #FFFFFF;
                color: #000000;
            }
            QTextEdit {
                background-color: #FFFFFF;
                color: #000000;
                selection-background-color: #ADD6FF;
            }
        """)

    def apply_monokai_theme(self):
        self.parent.setStyleSheet("""
            QMainWindow, QDialog {
                background-color: #FFFFFF;
                color: #000000;
            }
            QTextEdit {
                background-color: #FFFFFF;
                color: #000000;
                selection-background-color: #ADD6FF;
            }
        """)

    def setup_categories(self):
        categories = {
            "Редактор": [
                ("Шрифт", "font_settings"),
                ("Тема", "theme_settings"),
                ("Стиль кода", "code_style_settings")
            ],
            "Терминал": [
                ("Внешний вид", "terminal_appearance"),
                ("Настройки оболочки", "shell_settings")
            ],
            "Файлы": [
                ("Автосохранение", "autosave_settings"),
                ("Исключения", "exclude_settings")
            ]
        }
        
        for category, items in categories.items():
            cat_item = QTreeWidgetItem([category])
            for name, widget_name in items:
                item = QTreeWidgetItem([name])
                item.setData(0, Qt.ItemDataRole.UserRole, widget_name)
                cat_item.addChild(item)
                settings_widget = self.create_settings_widget(widget_name)
                self.settings_stack.addWidget(settings_widget)
                self.widgets_map[widget_name] = settings_widget
            self.categories.addTopLevelItem(cat_item)

    def change_category(self, current, previous):
        if current:
            widget_name = current.data(0, Qt.ItemDataRole.UserRole)
            if widget_name in self.widgets_map:
                self.settings_stack.setCurrentWidget(self.widgets_map[widget_name])

    def create_settings_widget(self, widget_name):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        if widget_name == "font_settings":
            # Шрифт редактора
            font_group = QGroupBox("Шрифт редактора")
            font_layout = QVBoxLayout()
            
            self.font_family = QComboBox()
            self.font_family.addItems(["Consolas", "Fira Code", "JetBrains Mono"])
            self.font_family.setCurrentText(self.settings.value("editor/font_family", "Consolas"))
            
            self.font_size = QSpinBox()
            self.font_size.setRange(8, 32)
            self.font_size.setValue(int(self.settings.value("editor/font_size", 14)))
            
            font_layout.addWidget(QLabel("Семейство шрифтов"))
            font_layout.addWidget(self.font_family)
            font_layout.addWidget(QLabel("Размер шрифта"))
            font_layout.addWidget(self.font_size)
            font_group.setLayout(font_layout)
            layout.addWidget(font_group)
            
        elif widget_name == "theme_settings":
            # Настройки темы
            theme_group = QGroupBox("Тема оформления")
            theme_layout = QVBoxLayout()
            
            self.theme_select = QComboBox()
            self.theme_select.addItems(["Dark+", "Light+", "Monokai"])
            self.theme_select.setCurrentText(self.settings.value("editor/theme", "Dark+"))
            
            self.bg_color = ColorButton("Цвет фона", self.settings.value("editor/bg_color", "#1E1E1E"))
            self.fg_color = ColorButton("Цвет текста", self.settings.value("editor/fg_color", "#D4D4D4"))
            
            theme_layout.addWidget(QLabel("Тема"))
            theme_layout.addWidget(self.theme_select)
            theme_layout.addWidget(self.bg_color)
            theme_layout.addWidget(self.fg_color)
            theme_group.setLayout(theme_layout)
            layout.addWidget(theme_group)
            
        elif widget_name == "terminal_settings":
            # Настройки терминала
            terminal_group = QGroupBox("Настройки терминала")
            terminal_layout = QVBoxLayout()
            
            self.shell_path = QLineEdit(self.settings.value("terminal/shell", "/bin/bash"))
            self.cursor_style = QComboBox()
            self.cursor_style.addItems(["Block", "Underline", "Line"])
            self.cursor_style.setCurrentText(self.settings.value("terminal/cursor", "Block"))
            
            terminal_layout.addWidget(QLabel("Путь к оболочке"))
            terminal_layout.addWidget(self.shell_path)
            terminal_layout.addWidget(QLabel("Стиль курсора"))
            terminal_layout.addWidget(self.cursor_style)
            terminal_group.setLayout(terminal_layout)
            layout.addWidget(terminal_group)
        
        layout.addStretch()
        return widget
        
    def save_and_close(self):
        self.apply_settings()
        self.accept()

    def load_settings(self):
        self.load_current_settings(self)

class Editor(QMainWindow):
    def __init__(self, project_path=None):
        super().__init__()
        self.current_file = None
        
        if project_path:
            self.current_project = project_path
        else:
            project_path = initialize_workspace()
            if project_path:
                self.current_project = project_path
            else:
                dialog = ProjectSetupDialog()
                if dialog.exec():
                    # Use the exact path from dialog
                    self.current_project = dialog.project_path.text()
                    os.makedirs(self.current_project, exist_ok=True)
                    initialize_project_structure(self.current_project, dialog.project_group.checkedButton().layout().itemAt(1).layout().itemAt(0).widget().text())

        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("RytonStudio IDE - " + os.path.basename(self.current_project))
        self.setGeometry(100, 100, 1000, 700)
        
        # Main central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create main splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Create side toolbar
        self.side_toolbar = QToolBar()
        self.side_toolbar.setOrientation(Qt.Orientation.Vertical)
        self.side_toolbar.setMovable(True)
        self.side_toolbar.setAllowedAreas(Qt.ToolBarArea.LeftToolBarArea | Qt.ToolBarArea.RightToolBarArea)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.side_toolbar)
        
        # Добавляем новые страницы для расширений
        self.extensions_view = QWidget()
        self.debug_view = QWidget()
        self.search_view = QWidget()
        self.git_view = QWidget()
        self.test_view = QWidget()

        # Сначала создаем все базовые виджеты
        self.sidebar_stack = QStackedWidget()
        self.file_manager = FileManagerTab(self.current_project)
        self.extensions_view = QWidget()
        self.debug_view = QWidget()
        self.search_view = QWidget()
        self.git_view = GitWidget(self.current_project)
        self.test_view = QWidget()
        self.github_view = WebBrowserTab("https://github.com")
        self.collab_widget = CollaborationWidget()

        # Создаем stack и добавляем все виджеты
        self.sidebar_stack = QStackedWidget()
        self.sidebar_stack.addWidget(self.file_manager)
        self.sidebar_stack.addWidget(self.extensions_view)
        self.sidebar_stack.addWidget(self.debug_view)
        self.sidebar_stack.addWidget(self.search_view)
        self.sidebar_stack.addWidget(self.git_view)
        self.sidebar_stack.addWidget(self.test_view)
        self.sidebar_stack.addWidget(self.collab_widget)
        self.github_view = WebBrowserTab("https://github.com")
        self.sidebar_stack.addWidget(self.github_view)


        # Добавляем кнопки переключения в боковую панель
        actions = [
#            ("icons/new.svg", "New File", self.new_file),
            ("icons/directory.svg", "Open File", self.open_file),
#            ("icons/save.svg", "Save", self.save_file),
            ("icons/run.svg", "Run", self.run_code),
            ("icons/terminal.svg", "Toggle Terminal", self.toggle_terminal),
#            ("icons/settings.svg", "Settings", self.open_settings),
            ("icons/web.svg", "Toggle Sidebar", self.toggle_sidebar_content),
            ("icons/directory.svg", "Files", lambda: self.sidebar_stack.setCurrentWidget(self.file_manager)),
#            ("icons/extensions.svg", "Extensions", lambda: self.sidebar_stack.setCurrentWidget(self.extensions_view)),
#            ("icons/debug.svg", "Debug", lambda: self.sidebar_stack.setCurrentWidget(self.debug_view)),
#            ("icons/search.svg", "Search", lambda: self.sidebar_stack.setCurrentWidget(self.search_view)),
            ("icons/git.svg", "Git", lambda: self.sidebar_stack.setCurrentWidget(self.git_view)),
            ("icons/collab.svg", "AI Assistant", lambda: self.sidebar_stack.setCurrentWidget(self.chat_assistant)),
            ("icons/chat.svg", "RyteCord Chat", lambda: self.sidebar_stack.setCurrentWidget(self.collab_widget))
#            ("icons/test.svg", "Testing", lambda: self.sidebar_stack.setCurrentWidget(self.test_view))
        ]
        for icon_path, tooltip, handler in actions:
            button = QPushButton()
            button.setIcon(QIcon(icon_path))
            button.setIconSize(QSize(24, 24))
            button.setFixedSize(36, 36)
            button.setToolTip(tooltip)
            button.clicked.connect(handler)
            button.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    border-radius: 18px;
                    padding: 6px;
                }
                QPushButton:hover {
                    background-color: #3d3d3d;
                }
                QPushButton:pressed {
                    background-color: #2d2d2d;
                }
            """)
            self.side_toolbar.addWidget(button)


        
        # Right side container
        right_container = QSplitter(Qt.Orientation.Vertical)
        
        # Editor area with tabs
        self.editor_tabs = QTabWidget()
        self.editor_tabs.setTabsClosable(True)
        self.editor_tabs.tabCloseRequested.connect(self.close_tab)
        self.editor_tabs.setContentsMargins(0, 0, 0, 0)
        
        # Add initial code editor tab
        self.code_editor = CodeEditor()
        self.editor_tabs.addTab(self.code_editor, "untitled")
        
        right_container.addWidget(self.editor_tabs)
        
        # Terminal area
        self.terminal = TerminalTab()
        self.terminal.layout().setContentsMargins(0, 0, 0, 0)
        self.terminal.layout().setSpacing(0)
        right_container.addWidget(self.terminal)

        # В методе setup_ui добавим:
        self.chat_assistant = ChatAssistant()
        self.sidebar_stack.addWidget(self.chat_assistant)
        
        # Add right container to main splitter
        self.main_splitter.addWidget(right_container)
        
        # Set splitter sizes
        self.main_splitter.setSizes([200, 1000])  # File explorer width : Editor width
        right_container.setSizes([600, 200])  # Editor height : Terminal height
        
        main_layout.addWidget(self.main_splitter)
        
        # Status bar with git info and line/column indicators
        self.setup_status_bar()


        # Добавляем стили для боковой панели
        self.side_toolbar.setStyleSheet("""
            QToolBar {
                background-color: #252526;
                border: none;
                spacing: 8px;
                padding: 4px;
            }
        """)

        # Стили для вкладок
        self.editor_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: #1e1e1e;
            }
            
            QTabBar::tab {
                background: #2d2d2d;
                color: #969696;
                padding: 8px 16px;
                border: none;
                min-width: 100px;
            }
            
            QTabBar::tab:selected {
                background: #1e1e1e;
                color: #ffffff;
                border-top: 2px solid #007acc;
            }
            
            QTabBar::tab:hover:!selected {
                background: #2d2d2d;
                color: #ffffff;
            }
            
            QTabBar::close-button {
                image: url(icons/close.svg);
                subcontrol-position: right;
            }
            
            QTabBar::close-button:hover {
                background: #c84e4e;
                border-radius: 6px;
            }
        """)

        # Стили для файлового менеджера
        self.sidebar_stack.setStyleSheet("""
            QStackedWidget {
                background: #252526;
                border: none;
            }
            
            QTreeView {
                background: #252526;
                border: none;
                color: #cccccc;
            }
            
            QTreeView::item {
                padding: 4px;
                border-radius: 4px;
            }
            
            QTreeView::item:hover {
                background: #2a2d2e;
            }
            
            QTreeView::item:selected {
                background: #37373d;
                color: #ffffff;
            }
            
            QHeaderView::section {
                background: #252526;
                color: #cccccc;
                border: none;
                padding: 4px;
            }
        """)

        # Стили для терминала
        self.terminal.setStyleSheet("""
            QWidget {
                background: #1e1e1e;
                color: #d4d4d4;
                border: none;
            }
            
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
                font-family: 'JetBrains Mono', 'Consolas', monospace;
                font-size: 13px;
                padding: 4px;
                selection-background-color: #264f78;
            }
            
            QScrollBar:vertical {
                background: #1e1e1e;
                width: 14px;
                margin: 0px;
            }
            
            QScrollBar::handle:vertical {
                background: #424242;
                min-height: 20px;
                border-radius: 7px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: #4f4f4f;
            }
        """)

        # Стили для сплиттеров
        self.main_splitter.setStyleSheet("""
            QSplitter::handle {
                background: #2d2d2d;
            }
            
            QSplitter::handle:horizontal {
                width: 2px;
            }
            
            QSplitter::handle:vertical {
                height: 2px;
            }
        """)
        # Replace file_manager with sidebar_stack in splitter
        self.main_splitter.insertWidget(0, self.sidebar_stack)

        QShortcut(QKeySequence("Ctrl+N"), self, self.new_file)
        QShortcut(QKeySequence("Ctrl+O"), self, self.open_file)

    def split_vertical(self):
        # Реализация вертикального разделения окна
        pass

    def split_horizontal(self):
        # Реализация горизонтального разделения окна
        pass

    def focus_split(self, direction):
        # Переключение между разделенными окнами
        pass

    def show_command_palette(self):
        # Показать командную палитру
        pass

    def fold_code(self):
        # Свернуть блок кода
        pass

    def unfold_code(self):
        # Развернуть блок кода
        pass

    def goto_line(self):
        # Переход к строке
        line, ok = QInputDialog.getInt(self, "Go to Line", "Line number:", 1, 1, self.document().blockCount())
        if ok:
            cursor = QTextCursor(self.document().findBlockByLineNumber(line - 1))
            self.setTextCursor(cursor)

    def quick_open(self):
        # Быстрое открытие файла
        pass

    def find_in_files(self):
        # Поиск по всем файлам
        pass

    def trigger_suggestions(self):
        # Вызов автодополнения
        self.showCompleter()

    def toggle_sidebar_content(self):
        current = self.sidebar_stack.currentIndex()
        next_index = (current + 1) % self.sidebar_stack.count()
        self.sidebar_stack.setCurrentIndex(next_index)

    def new_file(self):
        new_editor = CodeEditor()
        self.editor_tabs.addTab(new_editor, "untitled")
        self.editor_tabs.setCurrentWidget(new_editor)

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File")
        if file_path:
            self.load_file(file_path)

    def save_file(self):
        print(self)
        current_editor = self.editor_tabs.currentWidget()
        if current_editor:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save As...",
                self.current_project,
                "Ryton files (*.ry);;Python files (*.py);;All Files (*.*)"
            )
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(current_editor.toPlainText())
                # Обновляем имя вкладки
                self.editor_tabs.setTabText(
                    self.editor_tabs.currentIndex(), 
                    os.path.basename(file_path)
                )
                self.status_bar.showMessage(f"Saved: {file_path}", 3000)

    def run_code(self):
        current_editor = self.editor_tabs.currentWidget()
        if current_editor:
            code = current_editor.toPlainText()
            self.terminal.terminal.execute_command(f"/home/rejzi/projects/CLI/RytonLang/dist/ryton_launcher.dist/ryton_launcher.bin {self.current_project}src/main.ry")

    def toggle_terminal(self):
        if self.terminal.isVisible():
            self.terminal.hide()
        else:
            self.terminal.show()

    def close_tab(self, index):
        if self.editor_tabs.count() > 1:
            self.editor_tabs.removeTab(index)

    def load_file(self, file_path):
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            if file_path.endswith('.md'):
                new_editor = MarkdownEditor()  # Используем специальный редактор для MD
            else:
                new_editor = CodeEditor()
                
            new_editor.setPlainText(content)
            editor_widget = new_editor.set_file_type(file_path)
            
            # Добавляем вкладку с правильным виджетом
            self.editor_tabs.addTab(editor_widget, os.path.basename(file_path))
            self.editor_tabs.setCurrentWidget(editor_widget)
            self.current_file = file_path
            self.status_bar.showMessage(f"Opened: {file_path}")
            
        except Exception as e:
            print(f"Loading error: {str(e)}")  # Добавим вывод ошибки в консоль
            self.status_bar.showMessage(f"Error opening file: {str(e)}")

    def open_settings(self):
        settings_dialog = SettingsDialog(self)
        settings_dialog.exec()

    def setup_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.uname = platform.uname()

        self.statusLabel = QLabel(f'{self.uname.system}/{self.uname.node}')
        self.status_bar.addPermanentWidget(self.statusLabel)

    def apply_style(self):
        pass

class ProjectSetupDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Создание нового проекта")
        self.setMinimumWidth(900)
        self.setMinimumHeight(600)
        
        # Основной layout с градиентным фоном
        layout = QHBoxLayout(self)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a1a, stop:1 #2d2d2d);
            }
        """)
        
        # Левая панель с шагами
        steps_panel = QWidget()
        steps_panel.setFixedWidth(250)
        steps_panel.setStyleSheet("""
            QWidget {
                background: rgba(30, 30, 30, 0.7);
                border-right: 1px solid #3d3d3d;
            }
        """)
        
        steps_layout = QVBoxLayout(steps_panel)
        steps_layout.setSpacing(2)
        steps_layout.setContentsMargins(0, 0, 0, 0)
        
        # Заголовок левой панели
        header = QLabel("Создание проекта")
        header.setStyleSheet("""
            QLabel {
                color: #e1e1e1;
                font-size: 18px;
                padding: 20px;
                background: rgba(40, 40, 40, 0.7);
            }
        """)
        steps_layout.addWidget(header)
        
        # Шаги с иконками
        steps = [
            ("Тип проекта", "icons/project.svg"),
            ("Язык", "icons/code.svg"), 
            ("Настройки", "icons/settings.svg"),
            ("Зависимости", "icons/package.svg")
        ]
        
        self.step_buttons = []
        for step_name, icon_path in steps:
            btn = QPushButton(step_name)
            btn.setCheckable(True)
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QSize(24, 24))
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 15px 20px;
                    border: none;
                    color: #b4b4b4;
                    background: transparent;
                    font-size: 14px;
                }
                QPushButton:checked {
                    background: rgba(55, 55, 61, 0.7);
                    color: #ffffff;
                    border-left: 4px solid #007acc;
                }
                QPushButton:hover:!checked {
                    background: rgba(45, 45, 50, 0.7);
                }
            """)
            steps_layout.addWidget(btn)
            self.step_buttons.append(btn)
        
        steps_layout.addStretch()
        
        # Правая панель с контентом
        content_panel = QWidget()
        content_layout = QVBoxLayout(content_panel)
        
        # Стек для страниц
        self.pages_stack = QStackedWidget()
        
        # Страница выбора типа проекта
        project_page = QWidget()
        project_layout = QVBoxLayout(project_page)
        
        project_types = [
            ("CLI Application", "icons/terminal.svg", "Консольное приложение с интерфейсом командной строки"),
            ("GUI Application", "icons/window.svg", "Графическое приложение с пользовательским интерфейсом"),
            ("Web Application", "icons/web.svg", "Веб-приложение с поддержкой HTTP и REST API"),
            ("Library/Framework", "icons/package.svg", "Библиотека или фреймворк для других проектов")
        ]
        
        self.project_group = QButtonGroup(self)

        for name, icon, desc in project_types:
            card = QPushButton()
            card.setCheckable(True)
            self.project_group.addButton(card)
            card.setFixedHeight(100)
            card.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 20px;
                    border: 1px solid #404040;
                    border-radius: 10px;
                    background: rgba(45, 45, 45, 0.7);
                    color: #d4d4d4;
                    margin: 5px 0;
                }
                QPushButton:checked {
                    background: rgba(55, 55, 61, 0.9);
                    border: 2px solid #007acc;
                }
                QPushButton:hover:!checked {
                    background: rgba(50, 50, 55, 0.8);
                    border: 1px solid #505050;
                }
            """)
            
            card_layout = QHBoxLayout(card)
            
            icon_label = QLabel()
            icon_label.setPixmap(QIcon(icon).pixmap(48, 48))
            card_layout.addWidget(icon_label)
            
            text_layout = QVBoxLayout()
            name_label = QLabel(name)
            name_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #ffffff;")
            desc_label = QLabel(desc)
            desc_label.setStyleSheet("color: #b4b4b4; font-size: 13px;")
            desc_label.setWordWrap(True)
            
            text_layout.addWidget(name_label)
            text_layout.addWidget(desc_label)
            
            card_layout.addLayout(text_layout)
            card_layout.addStretch()
            
            project_layout.addWidget(card)
        
        project_layout.addStretch()
        self.pages_stack.addWidget(project_page)
        
        # Добавляем навигационные кнопки
        nav_layout = QHBoxLayout()
        self.back_btn = QPushButton("Назад")
        self.next_btn = QPushButton("Далее")
        
        for btn in [self.back_btn, self.next_btn]:
            btn.setFixedWidth(120)
            btn.setStyleSheet("""
                QPushButton {
                    padding: 10px;
                    background: #007acc;
                    border: none;
                    border-radius: 5px;
                    color: white;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background: #0098ff;
                }
                QPushButton:pressed {
                    background: #005c99;
                }
            """)
        
        nav_layout.addWidget(self.back_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(self.next_btn)

        # Подключаем обработчики
        self.next_btn.clicked.connect(self.next_step)
        self.back_btn.clicked.connect(self.prev_step)
        
        self.current_step = 0
        self.back_btn.setEnabled(False)

        content_layout.addWidget(self.pages_stack)
        content_layout.addLayout(nav_layout)
        
        # Добавляем панели в главный layout
        layout.addWidget(steps_panel)
        layout.addWidget(content_panel, stretch=1)

        # Активируем первый шаг
        self.step_buttons[0].setChecked(True)

        # Создаем все страницы
        self.create_project_type_page()
        self.create_language_page()
        self.create_settings_page()
        self.create_dependencies_page()

        self.project_group.buttonClicked.connect(self.update_project_path)

    def next_step(self):
        # Проверяем, выбран ли тип проекта
        if self.current_step == 0 and not self.project_group.checkedButton():
            QMessageBox.warning(self, "Внимание", "Выберите тип проекта")
            return
            
        if self.current_step < len(self.step_buttons) - 1:
            self.current_step += 1
            self.step_buttons[self.current_step].setChecked(True)
            self.pages_stack.setCurrentIndex(self.current_step)
            
        # Включаем кнопку "Назад" после первого шага
        self.back_btn.setEnabled(True)
        
        # Меняем текст кнопки на последнем шаге
        if self.current_step == len(self.step_buttons) - 1:
            self.next_btn.setText("Создать")
            self.next_btn.clicked.disconnect()
            self.next_btn.clicked.connect(self.create_project)

    def prev_step(self):
        if self.current_step > 0:
            self.current_step -= 1
            self.step_buttons[self.current_step].setChecked(True)
            self.pages_stack.setCurrentIndex(self.current_step)
            
        # Отключаем кнопку "Назад" на первом шаге
        if self.current_step == 0:
            back_btn.setEnabled(False)
            
        # Возвращаем кнопке "Далее" исходное состояние
        if next_btn.text() == "Создать":
            next_btn.setText("Далее")
            next_btn.clicked.disconnect()
            next_btn.clicked.connect(self.next_step)

    def create_project(self):
        # Получаем выбранный тип проекта
        selected_project = self.project_group.checkedButton()
        if selected_project:
            project_type = selected_project.findChild(QLabel).text()
            # Здесь логика создания проекта
            self.accept()

    def update_project_path(self):
        if hasattr(self, 'project_name') and self.project_group.checkedButton():
            button = self.project_group.checkedButton()
            layout = button.layout()
            text_layout = layout.itemAt(1).layout()
            project_type = text_layout.itemAt(0).widget().text()
            print(f"Selected type: {project_type}")  # Отладка
            
            project_name = self.project_name.text()
            base_dir = os.path.expanduser("~/RytonStudio/projects")
            
            type_map = {
                "CLI Application": "CLI",
                "GUI Application": "GUI",
                "Web Application": "WEB",
                "Library/Framework": "LIB"
            }
            
            path_type = type_map.get(project_type, "OTHER")
            print(f"Mapped type: {path_type}")  # Отладка
            
            full_path = os.path.join(base_dir, path_type, project_name)
            print(f"Full path: {full_path}")  # Отладка
            self.project_path.setText(full_path)


    def create_project_type_page(self):
        # Существующий код страницы выбора типа проекта
        pass

    def create_language_page(self):
        language_page = QWidget()
        layout = QVBoxLayout(language_page)
        
        languages = [
            ("Ryton", "icons/ryton.png", "Современный язык высокого уровня для разработки профисионального ПО"),
            ("Zig", "icons/zig.svg", "Низкоуровневый язык с нулевыми накладными расходами")
        ]

        self.language_group = QButtonGroup(self)
        
        for name, icon, desc in languages:
            card = self.create_card(name, icon, desc)
            self.language_group.addButton(card)
            layout.addWidget(card)
            
        layout.addStretch()
        self.pages_stack.addWidget(language_page)

    def create_settings_page(self):
        settings_page = QWidget()
        layout = QVBoxLayout(settings_page)
        
        form = QFormLayout()
        self.project_name = QLineEdit()
        self.project_path = QLineEdit()
        self.project_path.setReadOnly(True)  # Делаем поле только для чтения
        self.version = QLineEdit("0.1.0")
        
        # Обновляем путь при изменении имени проекта
        self.project_name.textChanged.connect(self.update_project_path)
        
        form.addRow("Имя проекта:", self.project_name)
        form.addRow("Путь к проекту:", self.project_path)
        form.addRow("Версия:", self.version)
        
        layout.addLayout(form)
        layout.addStretch()
        self.pages_stack.addWidget(settings_page)

    def create_dependencies_page(self):
        deps_page = QWidget()
        layout = QVBoxLayout(deps_page)
        
        deps_list = QListWidget()
        deps_list.addItems([
            "libs not found",
        ])
        
        layout.addWidget(deps_list)
        self.pages_stack.addWidget(deps_page)

    def create_card(self, name, icon, desc):
        card = QPushButton()
        card.setCheckable(True)
        card.setFixedHeight(100)
        # Существующие стили для карточки
        
        card_layout = QHBoxLayout(card)
        icon_label = QLabel()
        icon_label.setPixmap(QIcon(icon).pixmap(48, 48))
        card_layout.addWidget(icon_label)
        
        text_layout = QVBoxLayout()
        name_label = QLabel(name)
        name_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #ffffff;")
        desc_label = QLabel(desc)
        desc_label.setStyleSheet("color: #b4b4b4; font-size: 13px;")
        desc_label.setWordWrap(True)
        
        text_layout.addWidget(name_label)
        text_layout.addWidget(desc_label)
        
        card_layout.addLayout(text_layout)
        card_layout.addStretch()
        
        return card

class OpenProjectDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Открыть проект")
        self.setMinimumWidth(800)
        self.setMinimumHeight(500)
        
        layout = QVBoxLayout(self)
        
        # Дерево проектов
        self.project_tree = QTreeWidget()
        self.project_tree.setHeaderLabels(["Проект", "Тип", "Последнее изменение"])
        self.project_tree.setStyleSheet("""
            QTreeWidget {
                background: #1e1e1e;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
            }
            QTreeWidget::item {
                padding: 8px;
                border-radius: 4px;
            }
            QTreeWidget::item:hover {
                background: #2d2d2d;
            }
            QTreeWidget::item:selected {
                background: #37373d;
            }
        """)
        
        # Загружаем список проектов
        self.load_projects()
        
        layout.addWidget(self.project_tree)
        
        # Кнопки
        buttons = QHBoxLayout()
        open_btn = QPushButton("Открыть")
        cancel_btn = QPushButton("Отмена")
        
        for btn in [open_btn, cancel_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    padding: 8px 16px;
                    background: #007acc;
                    border: none;
                    border-radius: 4px;
                    color: white;
                }
                QPushButton:hover {
                    background: #0098ff;
                }
            """)
        
        buttons.addStretch()
        buttons.addWidget(open_btn)
        buttons.addWidget(cancel_btn)
        
        layout.addLayout(buttons)
        
        # Подключаем сигналы
        open_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        self.project_tree.itemDoubleClicked.connect(self.accept)

    def load_projects(self):
        base_dir = os.path.expanduser("~/RytonStudio/projects")
        for project_type in ["CLI", "GUI", "WEB", "LIB"]:
            type_path = os.path.join(base_dir, project_type)
            if os.path.exists(type_path):
                for project in os.listdir(type_path):
                    project_path = os.path.join(type_path, project)
                    if os.path.isdir(project_path):
                        item = QTreeWidgetItem([
                            project,
                            project_type,
                            time.strftime("%Y-%m-%d %H:%M", 
                                        time.localtime(os.path.getmtime(project_path)))
                        ])
                        self.project_tree.addTopLevelItem(item)

    def get_selected_project(self):
        item = self.project_tree.currentItem()
        if item:
            project_name = item.text(0)
            project_type = item.text(1)
            return os.path.expanduser(f"~/RytonStudio/projects/{project_type}/{project_name}")
        return None

class RecentProjectDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Последние проекты")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout(self)
        
        # Список последних проектов
        self.recent_list = QListWidget()
        self.recent_list.setStyleSheet("""
            QListWidget {
                background: #1e1e1e;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
            }
            QListWidget::item {
                padding: 12px;
                border-radius: 4px;
            }
            QListWidget::item:hover {
                background: #2d2d2d;
            }
            QListWidget::item:selected {
                background: #37373d;
            }
        """)
        
        self.load_recent_projects()
        layout.addWidget(self.recent_list)
        
        # Кнопки
        buttons = QHBoxLayout()
        open_btn = QPushButton("Открыть")
        cancel_btn = QPushButton("Отмена")
        
        for btn in [open_btn, cancel_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    padding: 8px 16px;
                    background: #007acc;
                    border: none;
                    border-radius: 4px;
                    color: white;
                }
                QPushButton:hover {
                    background: #0098ff;
                }
            """)
        
        buttons.addStretch()
        buttons.addWidget(open_btn)
        buttons.addWidget(cancel_btn)
        
        layout.addLayout(buttons)
        
        # Подключаем сигналы
        open_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        self.recent_list.itemDoubleClicked.connect(self.accept)

    def load_recent_projects(self):
        settings = QSettings('RytonStudio', 'RecentProjects')
        recent_projects = settings.value('projects', [])
        for project in recent_projects:
            if os.path.exists(project):
                name = os.path.basename(project)
                item = QListWidgetItem(f"{name} ({project})")
                item.setData(Qt.ItemDataRole.UserRole, project)
                self.recent_list.addItem(item)

    def get_selected_project(self):
        item = self.recent_list.currentItem()
        if item:
            return item.data(Qt.ItemDataRole.UserRole)
        return None

def initialize_project_structure(project_path, project_type):
    """Create project structure based on type"""
    # Map the display names to internal types
    type_map = {
        "CLI Application": "CLI",
        "GUI Application": "GUI", 
        "Web Application": "WEB",
        "Library/Framework": "LIB"
    }
    
    internal_type = type_map.get(project_type, "CLI")
    
    if internal_type == "CLI":
        dirs = [
            "src",
            "src/tests",
            "docs",
            "src/resources"
        ]
        files = {
            "src/main.ry": "",
            "README.md": f"# CLI Project\n\nDescription of your project",
            "requirements.txt": "",
            "build.ry": ""
        }
    
    elif internal_type == "GUI":
        dirs = [
            "src",
            "src/widgets",
            "src/resources",
            "src/resources/fonts", 
            "src/resources/images",
            "src/resources/icons",
            "src/tests",
            "docs"
        ]
        files = {
            "src/main.ry": "",
            "src/widgets/widget.ry": "",
            "README.md": f"# GUI Project\n\nDescription of your project",
            "requirements.txt": "",
            "build.ry": ""
        }
    
    elif internal_type == "WEB":
        dirs = [
            "src",
            "src/templates",
            "src/static/css",
            "src/static",
            "src/static/images",
            "src/tests",
            "docs"
        ]
        files = {
            "src/app.ry": "",
            "src/templates/base.html": "<!DOCTYPE html>\n<html>\n<head>\n    <title>Web Project</title>\n</head>\n<body>\n    {% block content %}{% endblock %}\n</body>\n</html>",
            "README.md": f"# Web Project\n\nDescription of your project",
            "requirements.txt": ""
        }
    
    elif internal_type == "LIB":
        dirs = [
            "src",
            "src/lib",
            "examples",
            "tests",
            "docs"
        ]
        files = {
            "src/lib.ry": "",
            "README.md": f"# Library Project\n\nDescription of your library",
            "requirements.txt": ""
        }

    # Create directories
    for dir_path in dirs:
        os.makedirs(os.path.join(project_path, dir_path), exist_ok=True)

    # Create files with content
    for file_path, content in files.items():
        full_path = os.path.join(project_path, file_path)
        with open(full_path, 'w') as f:
            f.write(content)

def initialize_workspace():
    base_dir = os.path.expanduser("~/RytonStudio")
    projects_dir = os.path.join(base_dir, "projects")
    
    # Create base directories
    for dir_type in ["CLI", "GUI", "WEB"]:
        dir_path = os.path.join(projects_dir, dir_type)
        os.makedirs(dir_path, exist_ok=True)
    
    # Show project setup dialog if no recent projects
    if not os.listdir(projects_dir):
        dialog = ProjectSetupDialog()
        if dialog.exec():
            project_name = dialog.name_input.text()
            project_type = dialog.type_combo.currentText()
            project_path = os.path.join(projects_dir, project_type, project_name)
            os.makedirs(project_path)
            return project_path
    return None

def main():
    from qt_material import apply_stylesheet
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    app.setStyleSheet("""
            QMainWindow, QDialog {
            background-color: #1E1E1E;
            color: #D4D4D4;
        }
        QTextEdit {
            background-color: #1E1E1E;
            color: #D4D4D4;
            selection-background-color: #264F78;
        }
        QTabWidget::pane {
            border: none;
        }
        
        QTabBar::tab {
            padding: 8px 16px;
        }
        
        QStatusBar {
            background-color: #2d2d2d;
        }
    """)

    # Add signal handlers
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    
    project_path = initialize_workspace()
    if len(sys.argv) > 1:
        if sys.argv[1] == "--open":
            dialog = OpenProjectDialog()
            if dialog.exec():
                project_path = dialog.get_selected_project()
                if project_path:
                    editor = Editor(project_path)
                    editor.show()
        elif sys.argv[1] == "--recent":
            dialog = RecentProjectDialog()
            if dialog.exec():
                project_path = dialog.get_selected_project()
                if project_path:
                    editor = Editor(project_path)
                    editor.show()
        elif sys.argv[1] == "--project" and len(sys.argv) > 3:
            # Формат: --project <тип> <имя>
            project_type = sys.argv[2]
            project_name = sys.argv[3]
            base_dir = os.path.expanduser("~/RytonStudio/projects")
            project_path = os.path.join(base_dir, project_type, project_name)
            
            if os.path.exists(project_path):
                editor = Editor(project_path)
                editor.show()
            else:
                print(f"Проект {project_name} типа {project_type} не найден")
                sys.exit(1)
    else:
        editor = Editor()
        editor.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
