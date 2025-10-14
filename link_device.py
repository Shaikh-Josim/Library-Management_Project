import json, platform, socket
import qrcode
import traceback

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, Qt, QEvent, QPropertyAnimation, QPoint, QRect, QByteArray, QEasingCurve, QAbstractAnimation
from PyQt6.QtWebSockets import QWebSocketServer, QWebSocket
from PyQt6.QtNetwork import QHostAddress
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QLineEdit, QScrollArea, QDockWidget
from PyQt6.QtGui import QPixmap


class WebSocketServer(QObject):
    message_received = pyqtSignal(str)  # Signal to emit received messages
    client_disconnected = pyqtSignal(bool) #signal to find if device is disconnected

    def __init__(self):
        super().__init__()
        self.clients = []
        self.server = None
        self.IPAddress, self.Port = self.getIPAddressAndPort()
        self.device_info = {
            "deviceInfo":
            {
                "system": platform.system(),        # 'Windows', 'Linux', 'Darwin'
                "version": platform.version(),      # OS version
                "architecture": platform.machine(), # 'AMD64', 'x86_64', etc.
                "node": platform.node(),            # Hostname (often device name)
            }
        }

    def startServer(self):
        self.server = QWebSocketServer("Echo Server", QWebSocketServer.SslMode.NonSecureMode)
        #address = QHostAddress(QHostAddress.SpecialAddress.LocalHost)

        if self.server.listen(QHostAddress(self.IPAddress), self.Port):
            print(f"Server listening on ws://{self.IPAddress}:{self.Port}")
            self.server.newConnection.connect(self.on_new_connection)
        else:
            print("Failed to start server")

        
    def getIPAddressAndPort(self):
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))  # Bind to any available port
            return local_ip,s.getsockname()[1]
        
    def makeQrcodeAndGetResult(self):
        url = "ws://{}:{}".format(self.IPAddress,self.Port)
        qr = qrcode.QRCode(version=1, box_size=10, border=3)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color = 'black', back_color = 'white')
        img = img.resize((236,236))
        img.save('Appdata/qrcode.png')
        return 'Appdata/qrcode.png'

        
    @pyqtSlot()
    def on_new_connection(self):
        socket = self.server.nextPendingConnection()
        socket.sendTextMessage(json.dumps(self.device_info))

        socket.textMessageReceived.connect(self.handle_text_message)
        socket.disconnected.connect(self.handle_disconnect)

        self.clients.append(socket)
        print("Client connected.")

    @pyqtSlot(str)
    def handle_text_message(self, message):
        #socket = self.sender()
        self.message_received.emit(message)

    def sendMsg(self,msg):
        socket = next(iter(self.clients))
        socket.sendTextMessage(json.dumps(msg))
        print(msg," in ws logic")

    def closeServer(self):
        if self.server and self.server.isListening():
            print("Stopping new connections...")
            self.server.pauseAccepting()  # Prevent new connections

            print("Closing active sockets...")
            for socket in self.clients:  # Assuming you track them in a list
                socket.close()  # Sends close frame and disconnects
                socket.deleteLater()  # Safe cleanup

            print("Shutting down server...")
            self.server.close()
            print("WebSocket server closed successfully.")


            

    @pyqtSlot()
    def handle_disconnect(self):
        socket = self.sender()
        if socket in self.clients:
            self.clients.remove(socket)
        socket.deleteLater()
        self.client_disconnected.emit(True)
        print("Client disconnected.")

class FocusSignalLineEdit(QLineEdit):
    on_focus = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self._has_emitted_focus = False

    def focusInEvent(self, event):
        self.on_focus.emit(self.objectName())
        super().focusInEvent(event)
        self._has_emitted_focus = True

    def focusOutEvent(self, event):
        self._has_emitted_focus = False  # Reset flag
        super().focusOutEvent(event)        


class ServerWindow(QMainWindow):
    def __init__(self, server:WebSocketServer):
        super().__init__()
        self.setWindowTitle("WebSocket Server GUI")
        self.server = server
        self.server.message_received.connect(self.display_message)
        self.server.client_disconnected.connect(self.clientDisconnected)
        self.setUi()

        '''self.label = QLabel("Waiting for messages...")
        layout = QVBoxLayout()
        layout.addWidget(self.label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)'''

    @pyqtSlot(str)
    def display_message(self, message):
        msg = json.loads(message)
        print(message)
        if "deviceInfo" in msg:
            print("Client device info:", msg["deviceInfo"])
            self.label.setText(f"CONNECTED WITH DEVICE!!!:\nName: {msg["deviceInfo"]["name"]}\nModel: {msg["deviceInfo"]["model"]}\nOs: {msg["deviceInfo"]["os"]}")
        else:
            obj = next(iter(msg))
            print("obj:",obj)
            target = self.findChild(QLineEdit, obj)
            target.setText(msg[obj])
        
    @pyqtSlot(bool)
    def clientDisconnected(self,disconnected):
        print(disconnected)
        if disconnected:
            self.label.setText("No device is connected at this moment")
            self.button.setEnabled(True)

    def setUi(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.widget = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.scanner_btn = QPushButton("Start Scanning with scanner")
        self.button = QPushButton("Start Async Tasks")
        self.label = QLabel()
        self.label.setFixedSize(200,200)
        self.label2 = QLabel()
        self.l1 = FocusSignalLineEdit()
        self.label.setFocus()
        self.l1.on_focus.connect(self.onFocus)
        l2 = QLineEdit()
        l3 = QLineEdit()
        self.l1.setObjectName('lineedit1')
        l2.setObjectName('lineedit2')
        l3.setObjectName('lineedit3')
        layout.addWidget(self.button)
        layout.addWidget(self.label)
        layout.addWidget(self.label2)
        layout.addWidget(self.l1)
        layout.addWidget(l2)
        layout.addWidget(l3)
        self.widget.setLayout(layout)
        scroll_area.setWidget(self.widget)
        self.setCentralWidget(scroll_area)
        self.label.setWordWrap(True)
        self.label.setText("No device is connected at this moment")
        self.button.clicked.connect(self.startServer)
        

    @pyqtSlot(str)
    def onFocus(self, lineedit_name):
        print(lineedit_name)
        if self.server.clients:
            msg = {lineedit_name: ""}
            self.server.sendMsg(msg=msg)

    def startServer(self):
        self.server.startServer()
        img = self.server.makeQrcodeAndGetResult()
        self.label.setPixmap(QPixmap(img))
        self.label.setAlignment(Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignCenter)
        self.label2.setText("Starting Websocket Server at \n IPAddress:{}\n Port:{}\n".format(self.server.IPAddress,self.server.Port))
        self.button.setEnabled(False)
        



if __name__ == "__main__":
    try:
        app = QApplication([])
        server = WebSocketServer()
        window = ServerWindow(server)
        window.show()

        # Start the Qt event loop
        app.exec()
    except Exception:
        print(traceback.format_exc())
