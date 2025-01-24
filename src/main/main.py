from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QDialogButtonBox,
                            QHBoxLayout, QTextEdit, QLabel, QToolBar, QPushButton, 
                            QFileDialog, QStatusBar, QTabWidget, QSplitter, QLineEdit, QFrame,
                            QDialog, QTreeWidget, QTreeWidgetItem, QStackedWidget, QFormLayout,
                            QSpinBox, QComboBox, QCheckBox, QColorDialog, QGroupBox, QListWidget)
from PyQt6.QtCore import Qt, QSize, QSettings
from PyQt6.QtGui import QIcon, QFont, QColor, QTextOption
from widgets.ToolTabs import CodeEditor, FileManagerTab, TerminalTab, WebBrowserTab, GitWidget

import platform
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
    def __init__(self):
        super().__init__()
        self.current_file = None
        project_path = initialize_workspace()
        if project_path:
            self.current_project = project_path
        else:
            dialog = ProjectSetupDialog()
            if dialog.exec():
                project_name = dialog.name_input.text()
                project_type = dialog.type_combo.currentText()
                base_dir = os.path.expanduser("~/RytonStudio/projects")
                self.current_project = os.path.join(base_dir, project_type, project_name)
                os.makedirs(self.current_project, exist_ok=True)
                initialize_project_structure(self.current_project, dialog.type_combo.currentText())
        
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("RytonStudio IDE")
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

        # Создаем stack и добавляем все виджеты
        self.sidebar_stack = QStackedWidget()
        self.sidebar_stack.addWidget(self.file_manager)
        self.sidebar_stack.addWidget(self.extensions_view)
        self.sidebar_stack.addWidget(self.debug_view)
        self.sidebar_stack.addWidget(self.search_view)
        self.sidebar_stack.addWidget(self.git_view)
        self.sidebar_stack.addWidget(self.test_view)
        self.github_view = WebBrowserTab("https://github.com")
        self.sidebar_stack.addWidget(self.github_view)


        # Добавляем кнопки переключения в боковую панель
        actions = [
            ("icons/new.svg", "New File", self.new_file),
            ("icons/directory.svg", "Open File", self.open_file),
            ("icons/save.svg", "Save", self.save_file),
            ("icons/run.svg", "Run", self.run_code),
            ("icons/terminal.svg", "Toggle Terminal", self.toggle_terminal),
            ("icons/settings.svg", "Settings", self.open_settings),
            ("icons/web.svg", "Toggle Sidebar", self.toggle_sidebar_content),
            ("icons/directory.svg", "Files", lambda: self.sidebar_stack.setCurrentWidget(self.file_manager)),
            ("icons/extensions.svg", "Extensions", lambda: self.sidebar_stack.setCurrentWidget(self.extensions_view)),
            ("icons/debug.svg", "Debug", lambda: self.sidebar_stack.setCurrentWidget(self.debug_view)),
            ("icons/search.svg", "Search", lambda: self.sidebar_stack.setCurrentWidget(self.search_view)),
            ("icons/git.svg", "Git", lambda: self.sidebar_stack.setCurrentWidget(self.git_view)),
            ("icons/test.svg", "Testing", lambda: self.sidebar_stack.setCurrentWidget(self.test_view))
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
        
        # Add right container to main splitter
        self.main_splitter.addWidget(right_container)
        
        # Set splitter sizes
        self.main_splitter.setSizes([200, 1000])  # File explorer width : Editor width
        right_container.setSizes([600, 200])  # Editor height : Terminal height
        
        main_layout.addWidget(self.main_splitter)
        
        # Status bar with git info and line/column indicators
        self.setup_status_bar()

        # Replace file_manager with sidebar_stack in splitter
        self.main_splitter.insertWidget(0, self.sidebar_stack)

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
        current_editor = self.editor_tabs.currentWidget()
        if not self.current_file:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save File")
            if file_path:
                self.current_file = file_path
        if self.current_file:
            with open(self.current_file, 'w') as f:
                f.write(current_editor.toPlainText())
            self.status_bar.showMessage(f"Saved: {self.current_file}")

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
            new_editor = CodeEditor()
            new_editor.setPlainText(content)
            self.editor_tabs.addTab(new_editor, os.path.basename(file_path))
            self.editor_tabs.setCurrentWidget(new_editor)
            self.current_file = file_path
            self.status_bar.showMessage(f"Opened: {file_path}")
        except Exception as e:
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
        self.setWindowTitle("Create New Project")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # Recent project button
        self.recent_btn = QPushButton("Open Recent Project")
        self.recent_btn.clicked.connect(self.open_recent)
        layout.addWidget(self.recent_btn)
        
        # Select project button
        self.select_btn = QPushButton("Select Project")
        self.select_btn.clicked.connect(self.select_project)
        layout.addWidget(self.select_btn)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)
        
        # Existing dialog content...
        name_layout = QHBoxLayout()
        name_label = QLabel("Project name:")
        self.name_input = QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        type_layout = QHBoxLayout()
        type_label = QLabel("Project type:")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["CLI", "GUI", "WEB"])
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def open_recent(self):
        base_dir = os.path.expanduser("~/RytonStudio/projects")
        # Get most recent project
        recent = self.get_most_recent_project(base_dir)
        if recent:
            self.selected_project = recent
            self.accept()

    def select_project(self):
        base_dir = os.path.expanduser("~/RytonStudio/projects")
        project_dir = QFileDialog.getExistingDirectory(self, "Select Project", base_dir)
        if project_dir:
            self.selected_project = project_dir
            self.accept()

    def get_most_recent_project(self, base_dir):
        projects = []
        for root, dirs, files in os.walk(base_dir):
            if "project.ryt" in files:
                projects.append((os.path.getmtime(root), root))
        if projects:
            return sorted(projects, reverse=True)[0][1]
        return None

def initialize_project_structure(project_path, project_type):
    """Create project structure based on type"""
    if project_type == "CLI":
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
    
    elif project_type == "GUI":
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
    
    elif project_type == "WEB":
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
    editor = Editor()
    editor.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
