import json, platform, socket
import qrcode
import traceback

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt6.QtWebSockets import QWebSocketServer
from PyQt6.QtNetwork import QHostAddress
from PyQt6.QtWidgets import QApplication



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



if __name__ == "__main__":
    try:
        app = QApplication([])
        server = WebSocketServer()
        app.exec()
    except Exception:
        print(traceback.format_exc())
