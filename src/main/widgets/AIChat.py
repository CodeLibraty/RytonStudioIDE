from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QSplitter,
                            QPushButton, QComboBox, QScrollArea, QLabel, QFrame,
                            QLineEdit)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap
import google.generativeai as genai
import anthropic
import os

class AIProvider:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.model = None
        
    def setup_gemini(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        
    def setup_anthropic(self, api_key):
        self.model = anthropic.Anthropic(api_key=api_key)
        
    def generate_response(self, prompt):
        if isinstance(self.model, genai.GenerativeModel):
            response = self.model.generate_content(prompt)
            return response.text
        elif isinstance(self.model, anthropic.Anthropic):
            response = self.model.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text

class MessageWidget(QFrame):
    def __init__(self, text, is_user=False):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background: %s;
                border-radius: 12px;
                margin: 8px 16px;
            }
        """ % ('#2d2d2d' if is_user else '#1e1e1e'))
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        
        # Аватар и имя
        header = QHBoxLayout()
        avatar = QLabel()
        avatar_pixmap = QPixmap("icons/github.svg" if is_user else "icons/terminal.svg")
        avatar.setPixmap(avatar_pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        name = QLabel("You" if is_user else "Cody")
        name.setStyleSheet("color: #c6c6c6; font-weight: bold;")
        
        header.addWidget(avatar)
        header.addWidget(name)
        header.addStretch()
        layout.addLayout(header)
        
        # Сообщение
        message = QTextEdit()
        message.setReadOnly(True)
        message.setMarkdown(text)
        message.setStyleSheet("""
            QTextEdit {
                border: none;
                background: transparent;
                color: #e4e4e4;
                font-size: 14px;
                line-height: 1.5;
            }
        """)
        
        # Настройка размеров
        message.document().setDocumentMargin(0)
        message.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        message.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Вычисляем размер текста
        message.document().adjustSize()
        doc_height = message.document().size().height()
        
        # Устанавливаем размеры с учетом отступов
        message.setMinimumHeight(int(doc_height + 20))
        message.setMaximumHeight(int(doc_height + 20))
        
        layout.addWidget(message)

class AIWorker(QThread):
    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, ai_provider, query):
        super().__init__()
        self.ai_provider = ai_provider
        self.query = query
        
    def run(self):
        try:
            response = self.ai_provider.generate_response(self.query)
            self.response_ready.emit(response)
        except Exception as e:
            self.error_occurred.emit(str(e))

class ChatAssistant(QWidget):
    def __init__(self):
        super().__init__()
        self.ai_provider = AIProvider()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # API ключи
        api_panel = QWidget()
        api_layout = QVBoxLayout(api_panel)
        
        self.model_selector = QComboBox()
        self.model_selector.addItems(["Gemini Pro", "Claude 3"])
        
        self.api_input = QLineEdit()
        self.api_input.setPlaceholderText("Введите API ключ...")
        self.api_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        api_layout.addWidget(QLabel("Модель:"))
        api_layout.addWidget(self.model_selector)
        api_layout.addWidget(QLabel("API ключ:"))
        api_layout.addWidget(self.api_input)
        
        self.connect_btn = QPushButton("Подключить")
        self.connect_btn.clicked.connect(self.setup_model)
        api_layout.addWidget(self.connect_btn)
        
        layout.addWidget(api_panel)
        
        # Чат
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        
        self.chat_area = QScrollArea()
        self.chat_area.setWidgetResizable(True)
        
        messages_widget = QWidget()
        self.messages_layout = QVBoxLayout(messages_widget)
        self.messages_layout.addStretch()
        
        self.chat_area.setWidget(messages_widget)
        chat_layout.addWidget(self.chat_area)
        
        # Ввод сообщения
        input_layout = QHBoxLayout()
        self.input_field = QTextEdit()
        self.input_field.setMaximumHeight(100)
        self.input_field.setPlaceholderText("Введите запрос...")
        
        send_btn = QPushButton(QIcon("icons/send.svg"), "")
        send_btn.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(send_btn)
        
        chat_layout.addLayout(input_layout)
        layout.addWidget(chat_widget)
        
    def setup_model(self):
        api_key = self.api_input.text()
        if not api_key:
            self.add_message("Введите API ключ!", False)
            return
            
        model = self.model_selector.currentText()
        try:
            if model == "Gemini Pro":
                self.ai_provider.setup_gemini(api_key)
            else:
                self.ai_provider.setup_anthropic(api_key)
            self.add_message(f"Модель {model} успешно подключена!", False)
        except Exception as e:
            self.add_message(f"Ошибка подключения: {str(e)}", False)
            
    def send_message(self):
        if not self.ai_provider.model:
            self.add_message("Сначала подключите модель!", False)
            return
            
        text = self.input_field.toPlainText().strip()
        if text:
            self.add_message(text, True)
            self.input_field.clear()
            
            worker = AIWorker(self.ai_provider, text)
            worker.response_ready.connect(lambda x: self.add_message(x, False))
            worker.error_occurred.connect(lambda x: self.add_message(f"Ошибка: {x}", False))
            worker.start()
            
    def add_message(self, text, is_user):
        message = MessageWidget(text, is_user)
        self.messages_layout.insertWidget(self.messages_layout.count()-1, message)
        
    def generate_docs(self, code):
        prompt = f"""Сгенерируй документацию для этого кода:
        {code}
        """
        return self.ai_provider.generate_response(prompt)
