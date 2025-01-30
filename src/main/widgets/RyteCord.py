from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                            QPushButton, QListWidget, QTextEdit, QTabWidget, QApplication)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QEvent
from PyQt6.QtGui import QIcon
import asyncio
import socket
import wave
from aiortc import RTCSessionDescription, MediaStreamTrack, RTCIceServer
from aiortc.rtcpeerconnection import RTCPeerConnection, RTCConfiguration
from aiortc.contrib.media import MediaPlayer, MediaRecorder

from zeroconf import Zeroconf, ServiceInfo

class P2PNetwork(QThread):
    message_received = pyqtSignal(str, str)
    peer_connected = pyqtSignal(str, str)
    connection_status = pyqtSignal(str)

    def __init__(self, port=5000):
        super().__init__()
        self.port = port
        self.running = True
        self.peers = {}
        
        # Конфигурация ICE для P2P
        self.config = RTCConfiguration([
            RTCIceServer(urls="stun:stun.l.google.com:19302"),
            RTCIceServer(urls="stun:stun1.l.google.com:19302")
        ])
        
        # Создаем TCP сервер для входящих подключений
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(('', port))
        self.server.listen(5)
        self.server.setblocking(False)
        
        self.username = socket.gethostname()

    def connect_to_peer(self, ip_address):
        # Проверяем, не пытаемся ли подключиться к себе
        if ip_address in ['127.0.0.1', 'localhost']:
            self.connection_status.emit("Нельзя подключиться к собственному IP")
            return False
            
        try:
            peer_connection = RTCPeerConnection(self.config)
            data_channel = peer_connection.createDataChannel("chat")
            
            # Добавляем подробный лог
            self.connection_status.emit(f"Попытка подключения к {ip_address}...")
            
            @data_channel.on("open")
            def on_open():
                self.peers[ip_address] = (peer_connection, data_channel)
                self.peer_connected.emit(f"Peer@{ip_address}", ip_address)
                self.connection_status.emit(f"Подключено к {ip_address}")
                
            @data_channel.on("error")
            def on_error(error):
                self.connection_status.emit(f"Ошибка соединения: {str(error)}")
                
            return True
            
        except Exception as e:
            self.connection_status.emit(f"Детали ошибки: {str(e)}")
            return False
            
        except Exception as e:
            self.connection_status.emit(f"Ошибка подключения: {str(e)}")
            return False

    def send_message(self, peer_addr, message):
        if peer_addr in self.peers:
            _, channel = self.peers[peer_addr]
            try:
                channel.send(message)
                return True
            except:
                return False
        return False

class VoiceCallHandler(QThread):
    def __init__(self):
        super().__init__()
        self.pc = RTCPeerConnection()
        
    def start_stream(self):
        # Используем встроенный микрофон через aiortc
        player = MediaPlayer('/dev/default', format='pulse')
        self.pc.addTrack(player.audio)

class PeerDiscovery(QThread):
    peer_found = pyqtSignal(str, str)
    
    def __init__(self):
        super().__init__()
        self.zeroconf = Zeroconf()
        
    def run(self):
        info = ServiceInfo(
            "_rytonide._tcp.local.",
            f"RytonIDE Peer_{socket.gethostname()}._rytonide._tcp.local.",
            addresses=[socket.inet_aton(socket.gethostbyname(socket.gethostname()))],
            port=9090,
            properties={}
        )
        self.zeroconf.register_service(info)

class CollaborationWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.peers = {}
        self.current_call = None
        self.setup_ui()
        self.start_discovery()
        self.setup_network()
        
    def setup_network(self):
        self.network = P2PNetwork()
        self.network.message_received.connect(self.handle_message)
        self.network.peer_connected.connect(self.add_peer)
        self.network.connection_status.connect(self.update_status)
        self.network.start()
   
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Панель подключения
        connect_panel = QHBoxLayout()
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Введите IP адрес пира...")
        self.connect_btn = QPushButton("Подключиться")
        self.connect_btn.clicked.connect(self.connect_to_peer)
        
        connect_panel.addWidget(self.ip_input)
        connect_panel.addWidget(self.connect_btn)
        layout.addLayout(connect_panel)
        
        # Статус подключения
        self.status_label = QLabel("Готов к подключению")
        self.status_label.setStyleSheet("color: #888;")
        layout.addWidget(self.status_label)
                
        # Заголовок
        header = QLabel("Collaboration")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #e4e4e4;")
        layout.addWidget(header)
        
        # Список пиров
        self.peer_list = QListWidget()
        self.peer_list.setStyleSheet("""
            QListWidget {
                background: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 4px;
                color: #e4e4e4;
            }
            QListWidget::item:hover {
                background: #3d3d3d;
            }
        """)
        layout.addWidget(self.peer_list)
        
        # Табы для чата и звонков
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #404040;
                background: #2d2d2d;
                border-radius: 4px;
            }
            QTabBar::tab {
                background: #252526;
                color: #e4e4e4;
                padding: 8px 16px;
                border: none;
            }
            QTabBar::tab:selected {
                background: #2d2d2d;
                border-bottom: 2px solid #007acc;
            }
        """)
        
        # Вкладка чата
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setStyleSheet("""
            QTextEdit {
                background: #2d2d2d;
                border: none;
                color: #e4e4e4;
            }
        """)
        chat_layout.addWidget(self.chat_area)
        
        # Поле ввода с кнопкой отправки
        message_layout = QHBoxLayout()
        self.message_input = QTextEdit()
        self.message_input.setMaximumHeight(60)
        self.message_input.setPlaceholderText("Написать сообщение...")
        self.message_input.setStyleSheet("""
            QTextEdit {
                background: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 4px;
                color: #e4e4e4;
            }
        """)
        
        self.send_btn = QPushButton(QIcon("icons/send.svg"), "")
        self.send_btn.setFixedSize(36, 36)
        self.send_btn.clicked.connect(self.send_message)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 18px;
                padding: 8px;
            }
            QPushButton:hover {
                background: #3d3d3d;
            }
        """)
        
        message_layout.addWidget(self.message_input)
        message_layout.addWidget(self.send_btn)
        chat_layout.addLayout(message_layout)
        
        # Вкладка звонков
        call_widget = QWidget()
        call_layout = QVBoxLayout(call_widget)
        
        # Статус звонка
        self.call_status = QLabel("Нет активного звонка")
        self.call_status.setStyleSheet("color: #e4e4e4;")
        call_layout.addWidget(self.call_status)
        
        # Кнопки управления звонком
        call_controls = QHBoxLayout()
        
        self.call_btn = QPushButton(QIcon("icons/call.svg"), "Позвонить")
        self.call_btn.clicked.connect(self.start_call)
        self.hangup_btn = QPushButton(QIcon("icons/hangup.svg"), "Завершить")
        self.hangup_btn.clicked.connect(self.end_call)
        self.hangup_btn.setEnabled(False)
        
        for btn in [self.call_btn, self.hangup_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background: #2d2d2d;
                    border: 1px solid #404040;
                    border-radius: 4px;
                    color: #e4e4e4;
                    padding: 8px 16px;
                }
                QPushButton:hover {
                    background: #3d3d3d;
                }
                QPushButton:disabled {
                    background: #252526;
                    color: #666666;
                }
            """)
            call_controls.addWidget(btn)
            
        call_layout.addLayout(call_controls)
        call_layout.addStretch()
        
        # Добавляем вкладки
        self.tabs.addTab(chat_widget, QIcon("icons/chat.svg"), "Чат")
        self.tabs.addTab(call_widget, QIcon("icons/call.svg"), "Звонок")
        layout.addWidget(self.tabs)
        
        # Добавляем обработку Enter для сообщений
        self.message_input.installEventFilter(self)

        # Добавляем отображение IP
        ip_info = QHBoxLayout()
        ip_label = QLabel("Ваш IP:")
        self.ip_display = QLabel(self.get_local_ip())
        self.ip_display.setStyleSheet("""
            QLabel {
                background: #2d2d2d;
                padding: 4px 8px;
                border-radius: 4px;
                color: #4CAF50;
            }
        """)
        
        copy_ip_btn = QPushButton(QIcon("icons/copy.svg"), "")
        copy_ip_btn.setFixedSize(24, 24)
        copy_ip_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.ip_display.text()))
        copy_ip_btn.setToolTip("Копировать IP")
        
        ip_info.addWidget(ip_label)
        ip_info.addWidget(self.ip_display)
        ip_info.addWidget(copy_ip_btn)
        ip_info.addStretch()
        
        layout.insertLayout(0, ip_info)  # Добавляем в начало layout

    def start_call(self):
        selected = self.peer_list.currentItem()
        if selected:
            self.call_status.setText(f"Звоним {selected.text()}...")
            self.call_btn.setEnabled(False)
            self.hangup_btn.setEnabled(True)
            self.current_call = VoiceCallHandler()
            self.current_call.start()
            
    def end_call(self):
        if self.current_call:
            self.current_call.stop()
            self.current_call = None
            self.call_status.setText("Нет активного звонка")
            self.call_btn.setEnabled(True)
            self.hangup_btn.setEnabled(False)

    def start_discovery(self):
        self.discovery = PeerDiscovery()
        self.discovery.peer_found.connect(self.add_peer)
        self.discovery.start()
        
    def add_peer(self, name, address):
        if name not in self.peers:
            self.peers[name] = address
            self.peer_list.addItem(name)
            
    def start_call(self):
        if not self.current_call:
            selected = self.peer_list.currentItem()
            if selected:
                peer = self.peers[selected.text()]
                self.current_call = VoiceCallHandler()
                self.current_call.start()
                
    def open_chat(self):
        selected = self.peer_list.currentItem()
        if selected:
            self.chat_area.clear()
            # Открываем чат с выбранным пиром
            

    def connect_to_peer(self):
        ip = self.ip_input.text().strip()
        if ip:
            if self.network.connect_to_peer(ip):
                self.ip_input.clear()
                self.status_label.setText(f"Подключаемся к {ip}...")
            else:
                self.status_label.setText("Ошибка подключения")

    def update_status(self, status):
        self.status_label.setText(status)

    def send_message(self):
        text = self.message_input.toPlainText().strip()
        if text:
            selected = self.peer_list.currentItem()
            if selected:
                peer_addr = self.peers[selected.text()]
                if self.network.send_message(peer_addr, text):
                    self.chat_area.append(f"<span style='color: #4CAF50'>Вы:</span> {text}")
                    self.message_input.clear()
                else:
                    self.chat_area.append("<span style='color: #f44336'>Ошибка отправки!</span>")

    def handle_message(self, sender, message):
        self.chat_area.append(f"<span style='color: #2196F3'>{sender}:</span> {message}")

    def get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        except:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip