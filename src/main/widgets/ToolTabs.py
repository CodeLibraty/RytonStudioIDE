from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QPlainTextEdit,
                            QTreeView, QTextEdit, QCompleter, QInputDialog, QPushButton,
                            QInputDialog, QMenu, QLineEdit, QMessageBox, QHBoxLayout,
                            QVBoxLayout, QTreeWidget, QTreeWidgetItem, QLabel)
from PyQt6.QtCore import Qt, QUrl, QDir, QProcess, QStringListModel, QTimer, QPoint, QEvent, QDir,QSize
from PyQt6.QtGui import (QSyntaxHighlighter, QTextCursor, QTextCharFormat, QColor, QFont,
                        QStandardItemModel, QStandardItem, QPainter, QFontDatabase,
                        QKeySequence, QShortcut, QPixmap, QFileSystemModel, QIcon)

from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage, QWebEngineSettings

from git import Repo

import platform
import os
import re

def show_error(self, title, message):
    QMessageBox.critical(self, title, message)

def show_info(self, title, message):
    QMessageBox.information(self, title, message)

def show_warning(self, title, message):
    QMessageBox.warning(self, title, message)

class BrowserProfileManager:
    _instance = None

    @classmethod
    def get_profile(cls):
        if cls._instance is None:
            cls._instance = QWebEngineProfile("google_profile")
            cls._instance.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
            cls._instance.setPersistentStoragePath(os.path.expanduser("~/RytonStudio/.browser_data"))
            
            # Set modern Chrome user agent with form factors support
            chrome_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            cls._instance.setHttpUserAgent(chrome_agent)
            
            # Configure settings
            settings = cls._instance.settings()
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.AllowWindowActivationFromJavaScript, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, False)
            settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.DnsPrefetchEnabled, True)
            
            # Set default font family
            settings.setFontFamily(QWebEngineSettings.FontFamily.StandardFont, "DejaVu Sans")
            
        return cls._instance

class WebBrowserTab(QWidget):
    def __init__(self, url="https://github.com"):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Navigation toolbar
        nav_layout = QHBoxLayout()
        
        self.back_btn = QPushButton("←")
        self.back_btn.clicked.connect(lambda: self.web_view.back())
        self.forward_btn = QPushButton("→")
        self.forward_btn.clicked.connect(lambda: self.web_view.forward())
        
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        
        nav_layout.addWidget(self.back_btn)
        nav_layout.addWidget(self.forward_btn)
        nav_layout.addWidget(self.url_bar)
        
        layout.addLayout(nav_layout)
        
        # Browser setup
        self.profile = BrowserProfileManager.get_profile()
        self.web_view = QWebEngineView()
        page = QWebEnginePage(self.profile, self.web_view)
        self.web_view.setPage(page)
        self.web_view.urlChanged.connect(self.update_url)
        
        self.web_view.setUrl(QUrl(url))
        layout.addWidget(self.web_view)

    def navigate_to_url(self):
        url = self.url_bar.text()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        self.web_view.setUrl(QUrl(url))

    def update_url(self, url):
        self.url_bar.setText(url.toString())

class GitWidget(QWidget):
    def __init__(self, project_path):
        super().__init__()
        self.project_path = project_path
        
        try:
            self.repo = Repo(project_path)
        except Exception:
            reply = QMessageBox.question(
                self,
                "Git инициализация",
                "Репозиторий Git не найден. Создать новый?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.repo = Repo.init(project_path)
                self.repo.index.add('*')
                self.repo.index.commit('Initial commit')
                QMessageBox.information(self, "Git", "Репозиторий успешно создан")
            else:
                # Создаем пустой виджет вместо Git-интерфейса
                layout = QVBoxLayout(self)
                label = QLabel("Git не инициализирован")
                init_button = QPushButton("Инициализировать Git")
                init_button.clicked.connect(lambda: self.init_git_later())
                
                layout.addWidget(label)
                layout.addWidget(init_button)
                return

        self.setup_ui()
        self.refresh_status()

    def init_git_later(self):
        self.repo = Repo.init(self.project_path)
        self.repo.index.add('*')
        self.repo.index.commit('Initial commit')
        QMessageBox.information(self, "Git", "Репозиторий успешно создан")
        # Перезагружаем интерфейс
        self.setup_ui()
        self.refresh_status()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Информация о текущей ветке
        self.branch_label = QLabel()
        self.update_branch_label()
        layout.addWidget(self.branch_label)
        
        # Панель инструментов
        toolbar = QHBoxLayout()
        self.sync_btn = self.create_tool_button("icons/sync.svg", "Синхронизировать")
        self.commit_btn = self.create_tool_button("icons/commit.svg", "Commit")
        self.branch_btn = self.create_tool_button("icons/branch.svg", "Ветка")
        
        toolbar.addWidget(self.sync_btn)
        toolbar.addWidget(self.commit_btn)
        toolbar.addWidget(self.branch_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Поле commit message
        self.commit_msg = QLineEdit()
        self.commit_msg.setPlaceholderText("Сообщение коммита")
        layout.addWidget(self.commit_msg)
        
        # Дерево изменений
        self.changes_tree = QTreeWidget()
        self.changes_tree.setHeaderLabels(["Файл", "Статус"])
        self.staged = QTreeWidgetItem(["Staged Changes"])
        self.changes = QTreeWidgetItem(["Changes"])
        self.untracked = QTreeWidgetItem(["Untracked Files"])
        
        self.changes_tree.addTopLevelItem(self.staged)
        self.changes_tree.addTopLevelItem(self.changes)
        self.changes_tree.addTopLevelItem(self.untracked)
        
        self.changes_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.changes_tree.customContextMenuRequested.connect(self.show_context_menu)
        self.changes_tree.itemDoubleClicked.connect(self.show_diff)
        
        layout.addWidget(self.changes_tree)
        
        # Подключаем сигналы
        self.sync_btn.clicked.connect(self.sync_repository)
        self.commit_btn.clicked.connect(self.commit_changes)
        self.branch_btn.clicked.connect(self.manage_branches)

    def update_branch_label(self):
        branch = self.repo.active_branch
        self.branch_label.setText(f"На ветке: {branch.name}")

    def refresh_status(self):
        self.staged.takeChildren()
        self.changes.takeChildren()
        self.untracked.takeChildren()
        
        # Получаем статус файлов
        for item in self.repo.index.diff(None):
            if item.change_type == 'M':
                self.changes.addChild(QTreeWidgetItem([item.a_path, "Modified"]))
            elif item.change_type == 'D':
                self.changes.addChild(QTreeWidgetItem([item.a_path, "Deleted"]))
            elif item.change_type == 'A':
                self.changes.addChild(QTreeWidgetItem([item.a_path, "Added"]))
                
        # Staged файлы
        for item in self.repo.index.diff('HEAD'):
            self.staged.addChild(QTreeWidgetItem([item.a_path, "Staged"]))
            
        # Untracked файлы
        for item in self.repo.untracked_files:
            self.untracked.addChild(QTreeWidgetItem([item, "Untracked"]))

    def stage_file(self, file_path):
        self.repo.index.add([file_path])
        self.refresh_status()

    def unstage_file(self, file_path):
        self.repo.index.remove([file_path])
        self.refresh_status()

    def commit_changes(self):
        if self.commit_msg.text():
            self.repo.index.commit(self.commit_msg.text())
            self.commit_msg.clear()
            self.refresh_status()

    def sync_repository(self):
        # Pull
        origin = self.repo.remotes.origin
        origin.pull()
        # Push
        origin.push()
        self.refresh_status()

    def show_diff(self, item):
        file_path = item.text(0)
        diff = self.repo.git.diff(file_path)
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Diff: {file_path}")
        layout = QVBoxLayout(dialog)
        
        diff_view = QTextEdit()
        diff_view.setPlainText(diff)
        diff_view.setReadOnly(True)
        layout.addWidget(diff_view)
        
        dialog.resize(800, 600)
        dialog.exec()

    def show_context_menu(self, position):
        item = self.changes_tree.itemAt(position)
        if not item or not item.parent():
            return
            
        menu = QMenu()
        file_path = item.text(0)
        
        if item.parent() == self.changes:
            stage_action = menu.addAction("Stage Changes")
            stage_action.triggered.connect(lambda: self.stage_file(file_path))
            
        elif item.parent() == self.staged:
            unstage_action = menu.addAction("Unstage Changes")
            unstage_action.triggered.connect(lambda: self.unstage_file(file_path))
            
        elif item.parent() == self.untracked:
            add_action = menu.addAction("Add to Git")
            add_action.triggered.connect(lambda: self.stage_file(file_path))
            
        menu.exec(self.changes_tree.viewport().mapToGlobal(position))

    def create_tool_button(self, icon_path, tooltip):
        btn = QPushButton()
        btn.setIcon(QIcon(icon_path))
        btn.setIconSize(QSize(24, 24))
        btn.setToolTip(tooltip)
        btn.setFixedSize(36, 36)
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 18px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
        """)
        return btn

class RytonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []


        # VSCode dark theme colors
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569cd6"))  # Blue for keywords
        
        builtin_format = QTextCharFormat()
        builtin_format.setForeground(QColor("#4ec9b0"))  # Teal for built-ins
        
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))  # Orange for strings
        
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6a9955"))  # Green for comments

        keywords = ['init', 'infinit', 'repeat', 'void', 'module import',
                   'func', 'pack', 'if', 'else', 'elif', 'while', 'for', 'in', 
                   'return', 'true', 'false', 'none', 'noop', 'private']
        for word in keywords:
            pattern = f'\\b{word}\\b'
            self.highlighting_rules.append((re.compile(pattern), keyword_format))

        builtin_format = QTextCharFormat()
        builtin_format.setForeground(QColor("#A6E22E"))
        builtins = ['debug', 'error', 'or', 'not', 'and', 'print', 'input', 
                    'Main', 'Sub', 'this']
        for word in builtins:
            pattern = f'\\b{word}\\b'
            self.highlighting_rules.append((re.compile(pattern), builtin_format))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#75715E"))
        self.highlighting_rules.append((re.compile('//[^\n]*'), comment_format))
        self.highlighting_rules.append((re.compile('</.*?/>'), comment_format))

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#E6DB74"))
        self.highlighting_rules.append((re.compile('"[^"\\\\]*(\\\\.[^"\\\\]*)*"'), string_format))
        self.highlighting_rules.append((re.compile("'[^'\\\\]*(\\\\.[^'\\\\]*)*'"), string_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), format)

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)

class RefactoringManager:
    def __init__(self, editor):
        self.editor = editor
        self.suggestions = []

    def suggest_improvements(self):
        """Анализирует код и предлагает улучшения"""
        cursor = self.editor.textCursor()
        text = self.editor.toPlainText()
        line = cursor.blockNumber() + 1
        
        # Анализ длинных функций
        self.check_function_length(text, line)
        # Анализ сложных условий
        self.check_complex_conditions(text, line)
        # Анализ повторяющегося кода
        self.check_code_duplication(text)
        
        return self.suggestions

    def rename_symbol(self, old_name, new_name):
        """Переименовывает переменную/функцию во всем файле"""
        text = self.editor.toPlainText()
        cursor = self.editor.textCursor()
        
        # Сохраняем позицию курсора
        position = cursor.position()
        
        # Находим все вхождения символа
        pattern = r'\b' + old_name + r'\b'
        new_text = re.sub(pattern, new_name, text)
        
        # Обновляем текст
        self.editor.setPlainText(new_text)
        
        # Восстанавливаем позицию курсора
        cursor.setPosition(position)
        self.editor.setTextCursor(cursor)

    def extract_method(self, start_line, end_line, new_name):
        """Извлекает выделенный код в отдельную функцию"""
        cursor = self.editor.textCursor()
        
        # Получаем выделенный текст
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        cursor.movePosition(QTextCursor.MoveOperation.Down, n=start_line-1)
        start = cursor.position()
        cursor.movePosition(QTextCursor.MoveOperation.Down, n=end_line-start_line+1)
        end = cursor.position()
        
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        selected_code = cursor.selectedText()
        
        # Создаем новую функцию
        indent = "    "
        new_function = f"\nfunc {new_name} {{\n{indent}{selected_code}\n}}\n"
        
        # Вставляем функцию и заменяем старый код вызовом
        cursor.removeSelectedText()
        cursor.insertText(f"{new_name}()")
        
        # Добавляем определение функции в конец файла
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(new_function)

class CodeSnippets:
    def __init__(self):
        self.snippets = {
            'func': {
                'prefix': r'func (.*?)',
                'body': ' {\n    $0\n}',
                'description': 'Function declaration'
            },
            'pack': {
                'prefix': 'pack',
                'body': ' {\n    $0\n}',
                'description': 'Package declaration'
            },
            'if': {
                'prefix': 'if',
                'body': ' {\n    $0\n}',
                'description': 'If statement'
            },
            'while': {
                'prefix': 'while',
                'body': ' {\n    $0\n}',
                'description': 'While loop'
            },
            'for': {
                'prefix': 'for',
                'body': ' in $1 {\n    $0\n}',
                'description': 'For loop'
            }
        }

class CodeCompleter(QCompleter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.keywords = [
            'this', 'init', 'infinit', 'repeat', 'void', 'module import',
            'func', 'pack', 'if', 'else', 'elif', 'while', 'for', 'in',
            'return', 'true', 'false', 'none', 'noop', 'debug', 'error',
            'or', 'not', 'and', 'print', 'input', 'sub', 'pylib:', 
            'jvmlib:', 'private'
        ]

        self.dynamic_words = set()
        self.setModel(QStringListModel())
        self.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.update_model()

    def calculate_similarity(self, pattern, word):
        if not pattern or not word:
            return 0
        
        pattern = pattern.lower()
        word = word.lower()
        
        # Находим последовательные совпадения
        i = 0
        j = 0
        matches = 0
        
        while i < len(pattern) and j < len(word):
            if pattern[i] == word[j]:
                matches += 1
                i += 1
            j += 1
            
        # Вычисляем процент совпадения
        similarity = (matches / len(pattern)) * 100
        
        # Бонус за совпадение в начале слова
        if word.startswith(pattern):
            similarity += 20
            
        return similarity

    def update_model(self):
        all_words = list(set(self.keywords + list(self.dynamic_words)))
        self.model().setStringList(sorted(all_words))

class MinimapWidget(QWidget):
    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        self.setFixedWidth(60)
        self.setStyleSheet("background-color: #252526;")
        
        # Create preview text edit
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setFont(QFont("Victor Mono Medium", 2))
        self.preview.setStyleSheet("""
            QPlainTextEdit {
                background-color: transparent;
                color: #6e7681;
                border: none;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.preview)
        
        # Connect signals
        self.editor.verticalScrollBar().valueChanged.connect(self.sync_scroll)
        self.editor.textChanged.connect(self.update_content)
        
    def sync_scroll(self):
        ratio = self.editor.verticalScrollBar().value() / self.editor.verticalScrollBar().maximum()
        self.preview.verticalScrollBar().setValue(int(ratio * self.preview.verticalScrollBar().maximum()))
        
    def update_content(self):
        self.preview.setPlainText(self.editor.toPlainText())

class GhostTextOverlay(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.text = ""
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.hide()

    def paintEvent(self, event):
        if not self.text:
            return
            
        painter = QPainter(self)
        painter.setOpacity(0.25)
        painter.setPen(QColor("#808080"))
        
        cursor_rect = self.editor.cursorRect()
        font_metrics = self.editor.fontMetrics()
        
        # Точное позиционирование текста сразу после курсора
        x = cursor_rect.x() + 20
        y = cursor_rect.y() + font_metrics.ascent()
        
        # Используем тот же шрифт, что и в редакторе
        painter.setFont(self.editor.font())
        painter.drawText(QPoint(x, y), self.text)

class RefactoringManager:
    def __init__(self, editor):
        self.editor = editor
        self.suggestions = []

    def check_function_length(self, text, line):
        """Проверяет длину функций"""
        functions = re.finditer(r'func\s+(\w+)\s*{([^}]*)}', text)
        for func in functions:
            lines = func.group(2).count('\n')
            if lines > 20:
                self.suggestions.append(
                    f"Функция '{func.group(1)}' слишком длинная ({lines} строк). Рекомендуется разбить на части."
                )

    def check_complex_conditions(self, text, line):
        """Проверяет сложность условий"""
        conditions = re.finditer(r'if\s+([^{]+){', text)
        for cond in conditions:
            condition = cond.group(1)
            if condition.count('and') + condition.count('or') > 2:
                self.suggestions.append(
                    f"Сложное условие. Рекомендуется упростить: {condition}"
                )

    def check_code_duplication(self, text):
        """Проверяет повторяющийся код"""
        lines = text.split('\n')
        for i in range(len(lines)):
            for j in range(i + 1, len(lines)):
                if len(lines[i]) > 20 and lines[i] == lines[j]:
                    self.suggestions.append(
                        f"Обнаружен повторяющийся код в строках {i+1} и {j+1}"
                    )

    def suggest_improvements(self):
        """Анализирует код и предлагает улучшения"""
        cursor = self.editor.textCursor()
        text = self.editor.toPlainText()
        line = cursor.blockNumber() + 1
        
        # Анализ длинных функций
        self.check_function_length(text, line)
        # Анализ сложных условий
        self.check_complex_conditions(text, line)
        # Анализ повторяющегося кода
        self.check_code_duplication(text)
        
        return self.suggestions

    def rename_symbol(self, old_name, new_name):
        """Переименовывает переменную/функцию во всем файле"""
        text = self.editor.toPlainText()
        cursor = self.editor.textCursor()
        
        # Сохраняем позицию курсора
        position = cursor.position()
        
        # Находим все вхождения символа
        pattern = r'\b' + old_name + r'\b'
        new_text = re.sub(pattern, new_name, text)
        
        # Обновляем текст
        self.editor.setPlainText(new_text)
        
        # Восстанавливаем позицию курсора
        cursor.setPosition(position)
        self.editor.setTextCursor(cursor)

    def extract_method(self, start_line, end_line, new_name):
        """Извлекает выделенный код в отдельную функцию"""
        cursor = self.editor.textCursor()
        
        # Получаем выделенный текст
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        cursor.movePosition(QTextCursor.MoveOperation.Down, n=start_line-1)
        start = cursor.position()
        cursor.movePosition(QTextCursor.MoveOperation.Down, n=end_line-start_line+1)
        end = cursor.position()
        
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        selected_code = cursor.selectedText()
        
        # Создаем новую функцию
        indent = "    "
        new_function = f"\nfunc {new_name} {{\n{indent}{selected_code}\n}}\n"
        
        # Вставляем функцию и заменяем старый код вызовом
        cursor.removeSelectedText()
        cursor.insertText(f"{new_name}()")
        
        # Добавляем определение функции в конец файла
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(new_function)

class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        font_id = QFontDatabase.addApplicationFont("fonts/JetBrainsMono.ttf")
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        
        custom_font = QFont(font_family, 10)
        self.setFont(custom_font)
        
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                selection-background-color: #264f78;
                selection-color: #ffffff;
            }
        """)
        self.installEventFilter(self)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.highlighter = RytonHighlighter(self.document())
        self.refactoring = RefactoringManager(self)
        
        # Добавляем виджет для номеров строк
        self.line_numbers = LineNumberArea(self)
        
        # Подключаем обновление области номеров строк
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.updateLineNumberAreaWidth(0)
        
        # Устанавливаем отступ для номеров строк
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)
        
        # Дефолтный код остаётся без изменений
        default_code = ''''''
        self.setPlainText(default_code)

        self.completer = CodeCompleter(self)
        self.completer.setWidget(self)
        self.completer.activated.connect(self.insertCompletion)
        
        # Таймер для обновления подсказок
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.update_completions)
        
        # Подключаем обработчик изменения текста
        self.textChanged.connect(self.handle_text_changed)

        self.snippets = CodeSnippets()
        self.ghost_text = None
        self.ghost_visible = False
        self.ghost_format = QTextCharFormat()
        self.ghost_format.setForeground(QColor(128, 128, 128, 128))
        self.ghost_overlay = GhostTextOverlay(self)
        self.current_snippet = None
        self.completer_active = False



        # Добавляем контекстное меню
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        self.setupShortcuts()

    def setupShortcuts(self):
        # VSCode-style shortcuts
        QShortcut(QKeySequence("Ctrl+S"), self, self.save_file)
        QShortcut(QKeySequence("Ctrl+/"), self, self.toggle_comment)
        QShortcut(QKeySequence("Ctrl+Z"), self, self.undo)
        QShortcut(QKeySequence("Ctrl+Y"), self, self.redo)
        QShortcut(QKeySequence("Ctrl+F"), self, self.find)
        QShortcut(QKeySequence("Ctrl+H"), self, self.replace)
        
        # Ryton specific shortcuts
        QShortcut(QKeySequence("Alt+Ctrl+F"), self, self.insert_function)
        QShortcut(QKeySequence("Alt+Ctrl+P"), self, self.insert_pack)
        QShortcut(QKeySequence("Alt+Ctrl+I"), self, self.insert_if)
        QShortcut(QKeySequence("Alt+Ctrl+W"), self, self.insert_while)
        QShortcut(QKeySequence("Alt+Ctrl+R"), self, self.insert_repeat)
        
    def insert_function(self):
        cursor = self.textCursor()
        name, ok = QInputDialog.getText(self, "New Function", "Function name:")
        if ok and name:
            cursor.insertText(f"func {name} {{\n    \n}}")
            cursor.movePosition(QTextCursor.MoveOperation.Up)
            cursor.movePosition(QTextCursor.MoveOperation.Right, n=4)
            self.setTextCursor(cursor)
            
    def insert_pack(self):
        cursor = self.textCursor()
        name, ok = QInputDialog.getText(self, "New Package", "Package name:")
        if ok and name:
            cursor.insertText(f"pack {name} {{\n    \n}}")
            cursor.movePosition(QTextCursor.MoveOperation.Up)
            cursor.movePosition(QTextCursor.MoveOperation.Right, n=4)
            self.setTextCursor(cursor)
            
    def insert_if(self):
        cursor = self.textCursor()
        cursor.insertText("if  {\n    \n}")
        cursor.movePosition(QTextCursor.MoveOperation.Up, n=2)
        cursor.movePosition(QTextCursor.MoveOperation.Right, n=3)
        self.setTextCursor(cursor)
        
    def insert_while(self):
        cursor = self.textCursor()
        cursor.insertText("while  {\n    \n}")
        cursor.movePosition(QTextCursor.MoveOperation.Up, n=2)
        cursor.movePosition(QTextCursor.MoveOperation.Right, n=6)
        self.setTextCursor(cursor)
        
    def insert_repeat(self):
        cursor = self.textCursor()
        cursor.insertText("repeat  {\n    \n}")
        cursor.movePosition(QTextCursor.MoveOperation.Up, n=2)
        cursor.movePosition(QTextCursor.MoveOperation.Right, n=7)
        self.setTextCursor(cursor)
        
    def toggle_comment(self):
        cursor = self.textCursor()
        if cursor.hasSelection():
            start = cursor.selectionStart()
            end = cursor.selectionEnd()
            cursor.setPosition(start)
            first_line = cursor.blockNumber()
            cursor.setPosition(end)
            last_line = cursor.blockNumber()
            
            cursor.beginEditBlock()
            for line in range(first_line, last_line + 1):
                cursor.movePosition(QTextCursor.MoveOperation.Start)
                cursor.movePosition(QTextCursor.MoveOperation.Down, n=line)
                cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
                if cursor.block().text().startswith("//"):
                    cursor.movePosition(QTextCursor.MoveOperation.Right, 
                                     QTextCursor.MoveMode.KeepAnchor, 2)
                    cursor.removeSelectedText()
                else:
                    cursor.insertText("//")
            cursor.endEditBlock()
        else:
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
            if cursor.block().text().startswith("//"):
                cursor.movePosition(QTextCursor.MoveOperation.Right, 
                                 QTextCursor.MoveMode.KeepAnchor, 2)
                cursor.removeSelectedText()
            else:
                cursor.insertText("//")

    def show_context_menu(self, position):
        menu = self.createStandardContextMenu(position)
        menu.addSeparator()
        
        # Добавляем опции рефакторинга
        refactor_menu = menu.addMenu("Рефакторинг")
        
        rename_action = refactor_menu.addAction("Переименовать")
        rename_action.triggered.connect(self.rename_current_symbol)
        
        extract_action = refactor_menu.addAction("Извлечь метод")
        extract_action.triggered.connect(self.extract_selected_code)
        
        # Показываем подсказки по улучшению кода
        suggestions = self.refactoring.suggest_improvements()
        if suggestions:
            suggest_menu = menu.addMenu("Предложения")
            for suggestion in suggestions:
                action = suggest_menu.addAction(suggestion)
                # Добавить обработку действий
        
        menu.exec(self.mapToGlobal(position))

    def rename_current_symbol(self):
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        old_name = cursor.selectedText()
        
        if old_name:
            new_name, ok = QInputDialog.getText(self, 
                                              "Переименовать", 
                                              "Новое имя:", 
                                              text=old_name)
            if ok and new_name:
                self.refactoring.rename_symbol(old_name, new_name)

    def extract_selected_code(self):
        cursor = self.textCursor()
        if cursor.hasSelection():
            start_line = cursor.blockNumber()
            cursor.setPosition(cursor.selectionEnd())
            end_line = cursor.blockNumber()
            
            new_name, ok = QInputDialog.getText(self,
                                              "Извлечь метод",
                                              "Имя новой функции:")
            if ok and new_name:
                self.refactoring.extract_method(start_line, end_line, new_name)

    def eventFilter(self, obj, event):
        if obj is self and event.type() == QEvent.Type.KeyPress:
            return self.handleKeyPress(event)
        return super().eventFilter(obj, event)
        
    def handleKeyPress(self, event):
        # Обработка Enter между {}
        if event.key() == Qt.Key.Key_Return:
            cursor = self.textCursor()
            block = cursor.block()
            text = block.text()
            pos_in_block = cursor.positionInBlock()
            
            # Проверяем символы слева и справа от курсора
            if (pos_in_block > 0 and pos_in_block < len(text) and 
                text[pos_in_block-1] == '{' and text[pos_in_block] == '}'):
                # Получаем текущий отступ
                indent = ''
                for char in text:
                    if char.isspace():
                        indent += char
                    else:
                        break
                        
                # Форматируем вставку
                cursor.beginEditBlock()
                cursor.insertText('\n' + indent + '    ')  # Новая строка с отступом
                pos = cursor.position()  # Запоминаем позицию для курсора
                cursor.insertText('\n' + indent)  # Строка для закрывающей скобки
                cursor.setPosition(pos)  # Возвращаем курсор на среднюю строку
                cursor.endEditBlock()
                self.setTextCursor(cursor)
                return True

        if event.key() == Qt.Key.Key_Tab:
            if self.completer and self.completer.popup().isVisible():
                return False
            if self.current_snippet:
                return False
            cursor = self.textCursor()
            cursor.insertText("    ")
            return True

        pairs = {
            '[': ']',
            '{': '}',
            '(': ')',
            '"': '"',
            "'": "'"
        }
        
        if event.text() in pairs:
            cursor = self.textCursor()
            cursor.insertText(event.text() + pairs[event.text()])
            cursor.movePosition(QTextCursor.MoveOperation.Left)
            self.setTextCursor(cursor)
            return True
            
        return False

    def save_file(self):
        if hasattr(self.parent(), 'save_file'):
            self.parent().save_file()

    def find(self):
        search_text, ok = QInputDialog.getText(self, "Find", "Search for:")
        if ok and search_text:
            cursor = self.textCursor()
            # Сохраняем форматирование для подсветки
            format = QTextCharFormat()
            format.setBackground(QColor("#666666"))
            format.setForeground(QColor("#FFFFFF"))
            
            # Очищаем предыдущие подсветки
            self.setExtraSelections([])
            extra_selections = []
            
            # Ищем все вхождения
            while cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor):
                if cursor.selectedText() == search_text:
                    selection = QTextEdit.ExtraSelection()
                    selection.format = format
                    selection.cursor = QTextCursor(cursor)
                    extra_selections.append(selection)
                cursor.movePosition(QTextCursor.MoveOperation.Right)
                
            self.setExtraSelections(extra_selections)

    def replace(self):
        find_text, ok = QInputDialog.getText(self, "Replace", "Find:")
        if ok and find_text:
            replace_text, ok = QInputDialog.getText(self, "Replace", "Replace with:")
            if ok:
                text = self.toPlainText()
                new_text = text.replace(find_text, replace_text)
                self.setPlainText(new_text)

    def duplicate_line(self):
        cursor = self.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText()
            cursor.insertText(text + "\n" + text)
        else:
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.KeepAnchor)
            text = cursor.selectedText()
            cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
            cursor.insertText("\n" + text)

    def move_line_up(self):
        cursor = self.textCursor()
        if cursor.blockNumber() > 0:
            current_line = cursor.block().text()
            cursor.movePosition(QTextCursor.MoveOperation.Up)
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.KeepAnchor)
            prev_line = cursor.selectedText()
            cursor.removeSelectedText()
            cursor.insertText(current_line)
            cursor.movePosition(QTextCursor.MoveOperation.Down)
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
            cursor.removeSelectedText()
            cursor.insertText(prev_line)
            cursor.movePosition(QTextCursor.MoveOperation.Up)

    def move_line_down(self):
        cursor = self.textCursor()
        if cursor.block().next().isValid():
            current_line = cursor.block().text()
            cursor.movePosition(QTextCursor.MoveOperation.Down)
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.KeepAnchor)
            next_line = cursor.selectedText()
            cursor.removeSelectedText()
            cursor.insertText(current_line)
            cursor.movePosition(QTextCursor.MoveOperation.Up)
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
            cursor.removeSelectedText()
            cursor.insertText(next_line)
            cursor.movePosition(QTextCursor.MoveOperation.Down)

    def indent(self):
        cursor = self.textCursor()
        if cursor.hasSelection():
            start = cursor.selectionStart()
            end = cursor.selectionEnd()
            cursor.setPosition(start)
            first_line = cursor.blockNumber()
            cursor.setPosition(end)
            last_line = cursor.blockNumber()
            
            cursor.beginEditBlock()
            for line in range(first_line, last_line + 1):
                cursor.movePosition(QTextCursor.MoveOperation.Start)
                cursor.movePosition(QTextCursor.MoveOperation.Down, n=line)
                cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
                cursor.insertText("    ")
            cursor.endEditBlock()
        else:
            cursor.insertText("    ")

    def unindent(self):
        cursor = self.textCursor()
        if cursor.hasSelection():
            start = cursor.selectionStart()
            end = cursor.selectionEnd()
            cursor.setPosition(start)
            first_line = cursor.blockNumber()
            cursor.setPosition(end)
            last_line = cursor.blockNumber()
            
            cursor.beginEditBlock()
            for line in range(first_line, last_line + 1):
                cursor.movePosition(QTextCursor.MoveOperation.Start)
                cursor.movePosition(QTextCursor.MoveOperation.Down, n=line)
                cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
                cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 4)
                if cursor.selectedText() == "    ":
                    cursor.removeSelectedText()
            cursor.endEditBlock()


    def handle_text_changed(self):
        self.update_timer.start(280)  # Уменьшаем задержку до 300 мс
        
        current_word = self.textUnderCursor()
        if len(current_word) >= 1:  # Показываем уже при 1 символе
            self.show_suggestions(current_word)

    def update_completions(self):
        # Собираем все слова из текста
        text = self.toPlainText()
        # Ищем функции
        functions = re.findall(r'func\s+([a-zA-Z_]\w*)', text)
        # Ищем классы
        classes = re.findall(r'pack\s+([a-zA-Z_]\w*)', text)
        # Ищем переменные
        variables = re.findall(r'\b([a-zA-Z_]\w*)\s*=', text)
        
        # Обновляем список динамических слов
        self.completer.dynamic_words.update(functions + classes + variables)
        self.completer.update_model()

    def show_suggestions(self, current_word):
        if current_word:
            # Получаем все доступные слова
            all_words = self.completer.model().stringList()
            
            # Проверяем точное совпадение
            if current_word in all_words:
                self.completer.popup().hide()
                return
                
            # Вычисляем совпадения с процентами
            matches = []
            for word in all_words:
                similarity = self.completer.calculate_similarity(current_word, word)
                if similarity >= 40:  # Минимальный порог совпадения
                    matches.append((word, similarity))
            
            # Если нет совпадений, скрываем подсказки
            if not matches:
                self.completer.popup().hide()
                return
                
            # Сортируем и показываем подсказки
            matches.sort(key=lambda x: x[1], reverse=True)
            matching_words = [word for word, _ in matches]
            
            if matching_words:
                self.completer.model().setStringList(matching_words)
                self.completer.setCompletionPrefix(current_word)
                popup = self.completer.popup()
                popup.setCurrentIndex(self.completer.completionModel().index(0, 0))
                
                cr = self.cursorRect()
                cr.setWidth(self.completer.popup().sizeHintForColumn(0) + 
                        self.completer.popup().verticalScrollBar().sizeHint().width())
                self.completer.complete(cr)

    def checkForSnippets(self):
        cursor = self.textCursor()
        line = cursor.block().text()[:cursor.positionInBlock()]
        
        for name, snippet in self.snippets.snippets.items():
            if line.endswith(snippet['prefix']):
                self.showGhostText(snippet['body'])
                return
        
        # Если нет совпадений, очищаем призрачный текст
        if self.ghost_visible:
            self.ghost_visible = False
            self.ghost_text = None
            self.setExtraSelections([])
                

    def showGhostText(self, snippet_text):
        self.ghost_text = snippet_text
        self.ghost_visible = True
        
        # Создаем призрачный текст без плейсхолдеров
        display_text = re.sub(r'\${[^}]+}', '', snippet_text)
        
        # Создаем наложение
        overlay = QTextEdit.ExtraSelection()
        overlay.format = self.ghost_format
        overlay.cursor = self.textCursor()
        overlay.cursor.insertText(display_text)
        
        self.setExtraSelections([overlay])
        
        # Возвращаем курсор в исходную позицию
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Left, n=len(display_text))
        self.setTextCursor(cursor)

    def insertSnippet(self, snippet):
        cursor = self.textCursor()
        # Удаляем триггер
        cursor.movePosition(QTextCursor.MoveOperation.Left, 
                          QTextCursor.MoveMode.KeepAnchor, 
                          len(snippet['prefix']))
        
        # Вставляем тело сниппета
        text = re.sub(r'\${[^}]+}', '', snippet['body'])
        cursor.insertText(text)
        
        # Позиционируем курсор внутри скобок
        cursor.movePosition(QTextCursor.MoveOperation.Left, 
                          QTextCursor.MoveMode.MoveAnchor, 
                          2)  # Перемещаемся внутрь {}
        self.setTextCursor(cursor)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.ghost_overlay.resize(self.size())

    def insertCompletion(self, completion):
        tc = self.textCursor()
        extra = len(completion) - len(self.completer.completionPrefix())
        tc.movePosition(QTextCursor.MoveOperation.Left)
        tc.movePosition(QTextCursor.MoveOperation.EndOfWord)
        tc.insertText(completion[-extra:])
        self.setTextCursor(tc)

    def keyPressEvent(self, event):
        # Обработка Tab для подсказок
        if self.completer and self.completer.popup().isVisible():
            if event.key() == Qt.Key.Key_Tab:
                self.completer.setCurrentRow(self.completer.popup().currentIndex().row())
                self.insertCompletion(self.completer.currentCompletion())
                self.completer.popup().hide()
                event.accept()
                return
                
        # Обработка Tab для сниппетов
        if self.current_snippet and event.key() == Qt.Key.Key_Tab:
            self.insertSnippet(self.current_snippet)
            self.current_snippet = None
            self.ghost_overlay.text = ""
            self.ghost_overlay.hide()
            event.accept()
            return
            
        # Обработка Backspace
        if event.key() == Qt.Key.Key_Backspace:
            self.current_snippet = None
            self.ghost_overlay.text = ""
            self.ghost_overlay.hide()
            
        super().keyPressEvent(event)
        
        # Проверяем снипеты после ввода
        cursor = self.textCursor()
        current_word = cursor.block().text()[:cursor.positionInBlock()]
        
        for name, snippet in self.snippets.snippets.items():
            if current_word.endswith(snippet['prefix']):
                self.current_snippet = snippet
                self.ghost_overlay.text = snippet['body'].replace(snippet['prefix'], '')
                self.ghost_overlay.show()
                self.ghost_overlay.update()
                return

        key = event.key()
        
    def textUnderCursor(self):
        tc = self.textCursor()
        tc.select(QTextCursor.SelectionType.WordUnderCursor)
        return tc.selectedText()

    def showCompleter(self):
        text = self.textUnderCursor()
        if text:
            self.completer.setCompletionPrefix(text)
            popup = self.completer.popup()
            popup.setCurrentIndex(self.completer.completionModel().index(0, 0))
            
            cr = self.cursorRect()
            cr.setWidth(self.completer.popup().sizeHintForColumn(0) + 
                       self.completer.popup().verticalScrollBar().sizeHint().width())
            self.completer.complete(cr)


    def lineNumberAreaWidth(self):
        digits = len(str(self.blockCount()))
        space = 10 + self.fontMetrics().horizontalAdvance('5') * digits
        return space

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.line_numbers.scroll(0, dy)
        else:
            self.line_numbers.update(0, rect.y(), self.line_numbers.width(), rect.height())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_numbers.setGeometry(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height())

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.line_numbers)
        painter.fillRect(event.rect(), QColor("#2F2F2F"))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("#7F7F7F"))
                painter.drawText(0, top, self.line_numbers.width()-5, self.fontMetrics().height(),
                               Qt.AlignmentFlag.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1

class FileManagerTab(QWidget):
    def __init__(self, project_dir="~"):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search files...")
        self.search_bar.textChanged.connect(self.filter_files)
        layout.addWidget(self.search_bar)

        # Tree view with custom model
        self.model = FileSystemModel()

        root_path = os.path.expanduser(project_dir)  # User's home directory
        self.model.setRootPath(root_path)
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(root_path))
        self.tree.setHeaderHidden(True)
        self.tree.setAnimated(True)
        self.tree.setIndentation(15)
        self.tree.setSortingEnabled(True)
        
        self.tree.doubleClicked.connect(self.open_file)

        # Hide size, type, date columns
        for i in range(1, 4):
            self.tree.hideColumn(i)
            
        layout.addWidget(self.tree)
        
        # Context menu
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        
        # Setup icons and styling
        self.setup_style()

    def setup_style(self):
        pass

    def show_context_menu(self, position):
        menu = QMenu()
        
        # Get selected item
        index = self.tree.indexAt(position)
        if index.isValid():
            file_path = self.model.filePath(index)
            
            # Add actions
            new_file = menu.addAction(QIcon("icons/new.svg"), "New File")
            new_folder = menu.addAction(QIcon("icons/directory.svg"), "New Folder")
            menu.addSeparator()
            copy = menu.addAction(QIcon("icons/copy.svg"), "Copy")
            cut = menu.addAction(QIcon("icons/cut.svg"), "Cut")
            paste = menu.addAction(QIcon("icons/paste.svg"), "Paste")
            menu.addSeparator()
            rename = menu.addAction(QIcon("icons/rename.svg"), "Rename")
            delete = menu.addAction(QIcon("icons/delete.svg"), "Delete")
            menu.addSeparator()
            open_terminal = menu.addAction(QIcon("icons/terminal.svg"), "Open in Terminal")
            
            # Connect actions
            new_file.triggered.connect(lambda: self.create_new_file(file_path))
            new_folder.triggered.connect(lambda: self.create_new_folder(file_path))
            copy.triggered.connect(lambda: self.copy_item(file_path))
            cut.triggered.connect(lambda: self.cut_item(file_path))
            paste.triggered.connect(lambda: self.paste_item(file_path))
            rename.triggered.connect(lambda: self.rename_item(file_path))
            delete.triggered.connect(lambda: self.delete_item(file_path))
            open_terminal.triggered.connect(lambda: self.open_in_terminal(file_path))
            
        menu.exec(self.tree.viewport().mapToGlobal(position))

    def open_file(self, index):
        file_path = self.model.filePath(index)
        if os.path.isfile(file_path):
            # Получаем главное окно через иерархию виджетов
            main_window = self.window()
            
            # Создаем новую вкладку редактора
            editor = CodeEditor()
            
            # Читаем и устанавливаем содержимое файла
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                editor.setPlainText(content)
            
            # Добавляем новую вкладку с именем файла
            file_name = os.path.basename(file_path)
            main_window.editor_tabs.addTab(editor, file_name)
            
            # Переключаемся на новую вкладку
            main_window.editor_tabs.setCurrentWidget(editor)


    def create_new_file(self, path):
        parent_dir = os.path.dirname(path) if os.path.isfile(path) else path
        name, ok = QInputDialog.getText(self, "New File", "Enter file name:")
        if ok and name:
            file_path = os.path.join(parent_dir, name)
            with open(file_path, 'w') as f:
                f.write('')
            self.refresh_view()

    def create_new_folder(self, path):
        parent_dir = os.path.dirname(path) if os.path.isfile(path) else path
        name, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:")
        if ok and name:
            folder_path = os.path.join(parent_dir, name)
            os.makedirs(folder_path, exist_ok=True)
            self.refresh_view()

    def copy_item(self, path):
        self.clipboard_path = path
        self.clipboard_action = 'copy'

    def cut_item(self, path):
        self.clipboard_path = path
        self.clipboard_action = 'cut'

    def paste_item(self, target_path):
        if not hasattr(self, 'clipboard_path') or not self.clipboard_path:
            return
            
        target_dir = os.path.dirname(target_path) if os.path.isfile(target_path) else target_path
        source_name = os.path.basename(self.clipboard_path)
        target = os.path.join(target_dir, source_name)
        
        if os.path.exists(self.clipboard_path):
            if os.path.isdir(self.clipboard_path):
                if self.clipboard_action == 'copy':
                    shutil.copytree(self.clipboard_path, target)
                else:
                    shutil.move(self.clipboard_path, target)
            else:
                if self.clipboard_action == 'copy':
                    shutil.copy2(self.clipboard_path, target)
                else:
                    shutil.move(self.clipboard_path, target)
                    
            if self.clipboard_action == 'cut':
                self.clipboard_path = None
            self.refresh_view()

    def rename_item(self, path):
        old_name = os.path.basename(path)
        new_name, ok = QInputDialog.getText(self, "Rename", "Enter new name:", text=old_name)
        if ok and new_name:
            new_path = os.path.join(os.path.dirname(path), new_name)
            os.rename(path, new_path)
            self.refresh_view()

    def delete_item(self, path):
        reply = QMessageBox.question(self, 'Delete', 
                                f'Are you sure you want to delete "{os.path.basename(path)}"?',
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            self.refresh_view()

    def open_in_terminal(self, path):
        target_dir = os.path.dirname(path) if os.path.isfile(path) else path
        terminal = self.parent().findChild(TerminalTab)
        if terminal:
            terminal.terminal.execute_command(f'cd "{target_dir}"')

    def refresh_view(self):
        current_index = self.tree.currentIndex()
        self.model.setRootPath(self.model.rootPath())
        if current_index.isValid():
            self.tree.setCurrentIndex(current_index)

    def filter_files(self, text):
        """Filter files in the tree view based on search text"""
        if not text:
            # If search is empty, show all files
            self.tree.setModel(self.model)
            return
            
        # Create case-insensitive filter
        search_pattern = text.lower()
        
        # Hide items that don't match the search
        for i in range(self.model.rowCount(self.tree.rootIndex())):
            index = self.model.index(i, 0, self.tree.rootIndex())
            item_text = self.model.data(index, Qt.ItemDataRole.DisplayRole).lower()
            
            if search_pattern in item_text:
                self.tree.setRowHidden(i, self.tree.rootIndex(), False)
            else:
                self.tree.setRowHidden(i, self.tree.rootIndex(), True)

class FileSystemModel(QFileSystemModel):
    def __init__(self):
        super().__init__()
        self.setRootPath("")
        self.setFilter(QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot | QDir.Filter.Hidden)
        
        # Custom icons
        self.folder_icon = QIcon("icons/directory.svg")
        self.file_icon = QIcon("icons/code.svg")
        self.image_icon = QIcon("icons/code.svg")
        self.code_icon = QIcon("icons/code.svg")
        
    def data(self, index, role):
        if role == Qt.ItemDataRole.DecorationRole:
            file_info = self.fileInfo(index)
            if file_info.isDir():
                return self.folder_icon
            elif file_info.suffix() in ['jpg', 'png', 'svg']:
                return self.image_icon
            elif file_info.suffix() in ['py', 'zig', 'ry', 'java', 'jar']:
                return self.code_icon
            return self.file_icon
            
        return super().data(index, role)

    def setup_style(self):
        self.setStyleSheet("""
            QTreeView {
                background-color: #252526;
                border: none;
                color: #d4d4d4;
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
            }
            QLineEdit {
                background: #3c3c3c;
                border: none;
                padding: 5px;
                color: #d4d4d4;
                border-radius: 4px;
                margin: 2px;
            }
        """)

    def show_context_menu(self, position):
        menu = QMenu()
        
        # Get selected item
        index = self.tree.indexAt(position)
        if index.isValid():
            file_path = self.model.filePath(index)
            
            # Add actions
            new_file = menu.addAction(QIcon("icons/new-file.svg"), "New File")
            new_folder = menu.addAction(QIcon("icons/new-folder.svg"), "New Folder")
            menu.addSeparator()
            copy = menu.addAction(QIcon("icons/copy.svg"), "Copy")
            cut = menu.addAction(QIcon("icons/cut.svg"), "Cut")
            paste = menu.addAction(QIcon("icons/paste.svg"), "Paste")
            menu.addSeparator()
            rename = menu.addAction(QIcon("icons/rename.svg"), "Rename")
            delete = menu.addAction(QIcon("icons/delete.svg"), "Delete")
            menu.addSeparator()
            open_terminal = menu.addAction(QIcon("icons/terminal.svg"), "Open in Terminal")
            
            # Connect actions
            new_file.triggered.connect(lambda: self.create_new_file(file_path))
            new_folder.triggered.connect(lambda: self.create_new_folder(file_path))
            copy.triggered.connect(lambda: self.copy_item(file_path))
            cut.triggered.connect(lambda: self.cut_item(file_path))
            paste.triggered.connect(lambda: self.paste_item(file_path))
            rename.triggered.connect(lambda: self.rename_item(file_path))
            delete.triggered.connect(lambda: self.delete_item(file_path))
            open_terminal.triggered.connect(lambda: self.open_in_terminal(file_path))
            
        menu.exec(self.tree.viewport().mapToGlobal(position))

    def filter_files(self, text):
        if not text:
            self.model.setNameFilters([])
            return
            
        self.model.setNameFilters([f"*{text}*"])

class CustomTerminal(QTextEdit):
    def __init__(self):
        super().__init__()
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)

        # Настраиваем фоновое изображение
        self.background_image = QPixmap("images/linux.png")  # Путь к изображению
        self.background_opacity = 0.8  # Прозрачность от 0 до 1
        
        # Включаем поддержку прозрачности
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setStyleSheet("""
            QTextEdit {
                color: #ffffff;
                font-family: 'Monospace';
                font-size: 14px;
                padding: 5px;
                background-color: transparent;
            }
        """)

        self.cwd = os.getcwd().replace(f'/home/{os.getlogin()}', '~')
        self.prompt = f"{self.cwd} > "
        self.command_history = []
        self.history_index = 0
        
        self.append_prompt()

    def paintEvent(self, event):
        painter = QPainter(self.viewport())
        painter.setOpacity(self.background_opacity)
        
        # Масштабируем изображение под размер виджета
        scaled_bg = self.background_image.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # Рисуем изображение
        painter.drawPixmap(0, 0, scaled_bg)
        
        # Рисуем полупрозрачный черный фон поверх изображения
        painter.fillRect(self.rect(), QColor(0, 0, 0, 180))
        
        super().paintEvent(event)

    def set_background(self, image_path, opacity=0.8):
        self.background_image = QPixmap(image_path)
        self.background_opacity = opacity
        self.viewport().update()

    def append_prompt(self):
        self.append(self.prompt)
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.setTextCursor(cursor)
        
    def handle_stdout(self):
        data = self.process.readAllStandardOutput().data().decode()
        self.append(data)
        self.append_prompt()
        
    def handle_stderr(self):
        data = self.process.readAllStandardError().data().decode()
        self.append(data)
        self.append_prompt()
        
    def keyPressEvent(self, event):
        cursor = self.textCursor()
        
        if event.key() == Qt.Key.Key_Return:
            command = self.get_current_command()
            if command:
                self.command_history.append(command)
                self.history_index = len(self.command_history)
                self.append("")
                self.execute_command(command)
            else:
                self.append("")
                self.append_prompt()
                
        elif event.key() == Qt.Key.Key_Up:
            self.show_previous_command()
            
        elif event.key() == Qt.Key.Key_Down:
            self.show_next_command()
            
        elif cursor.position() > self.document().lineCount() - 1:
            super().keyPressEvent(event)
            
    def get_current_command(self):
        doc = self.document()
        current_line = doc.findBlockByLineNumber(doc.lineCount() - 1).text()
        return current_line[len(self.prompt):].strip()
        
    def execute_command(self, command):
        self.process.start('/bin/bash', ['-c', command])
        self.process.waitForFinished()
        
    def show_previous_command(self):
        if self.command_history and self.history_index > 0:
            self.history_index -= 1
            self.replace_current_command(self.command_history[self.history_index])
            
    def show_next_command(self):
        if self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.replace_current_command(self.command_history[self.history_index])
            
    def replace_current_command(self, command):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine, QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        cursor.insertText(self.prompt + command)

class CustomTerminal(QTextEdit):
    def __init__(self):
        super().__init__()
        self.process = QProcess()
        
        # Определяем оболочку в зависимости от ОС
        if platform.system() == 'Windows':
            # Для Windows используем PowerShell или CMD
            shell = os.environ.get('COMSPEC', 'cmd.exe')
            self.process.start(shell)
        else:
            # Для Unix-подобных систем берем оболочку из окружения
            shell = os.environ.get('SHELL', '/bin/bash')
            self.process.start(shell)

        # Подключаем обработчики вывода
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        
        # Настраиваем внешний вид
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                font-family: 'Consolas', 'DejaVu Sans Mono', monospace;
                font-size: 14px;
                padding: 5px;
            }
        """)

        # Инициализируем рабочую директорию
        self.cwd = os.path.expanduser('~')
        self.update_prompt()

    def update_prompt(self):
        # Формируем промпт в зависимости от ОС
        if platform.system() == 'Windows':
            self.prompt = f"{self.cwd}>"
        else:
            username = os.environ.get('USER', 'user')
            hostname = platform.node()
            self.prompt = f"{username}@{hostname}:{self.cwd}$ "
        
        self.append(self.prompt)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return:
            command = self.get_current_command()
            if command:
                self.execute_command(command)
            else:
                self.append('\n' + self.prompt)
        elif event.key() == Qt.Key.Key_Backspace:
            cursor = self.textCursor()
            if cursor.position() > len(self.prompt):
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def execute_command(self, command):
        if command.startswith('cd '):
            # Обработка команды cd отдельно
            new_path = command[3:].strip()
            if new_path == '~':
                new_path = os.path.expanduser('~')
            try:
                os.chdir(os.path.expanduser(new_path))
                self.cwd = os.getcwd()
            except Exception as e:
                self.append(f'\nError: {str(e)}')
        else:
            # Выполнение команды через процесс
            self.process.write(f"{command}\n".encode())
        
        self.append('\n')

    def handle_stdout(self):
        data = self.process.readAllStandardOutput().data().decode()
        self.append(data)
        if not data.endswith('\n'):
            self.append('\n')
        self.update_prompt()

    def handle_stderr(self):
        data = self.process.readAllStandardError().data().decode()
        self.append(data)
        if not data.endswith('\n'):
            self.append('\n')
        self.update_prompt()

    def get_current_command(self):
        text = self.toPlainText()
        if text.endswith(self.prompt):
            return ''
        return text.split(self.prompt)[-1].strip()

class TerminalTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.terminal = CustomTerminal()
        layout.addWidget(self.terminal)
    def update_settings(self, shell_path=None, cursor_style=None, font_size=None):
        if shell_path:
            self.environment.shell_path = shell_path
        if cursor_style:
            self.terminal.cursor_color = self.get_cursor_color(cursor_style)
        if font_size:
            self.terminal.font_size = font_size
            
    def get_cursor_color(self, style):
        colors = {
            "Block": [1, 1, 1, 1],
            "Underline": [0.7, 0.7, 1, 1],
            "Line": [0.9, 0.9, 1, 1]
        }
        return colors.get(style, [1, 1, 1, 1])