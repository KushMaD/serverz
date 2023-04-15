import socket
import threading
from cryptography.fernet import Fernet
import pickle


class ChatServer:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.users_connected = list()
        self.symmetric_key = None

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((ip, port))
        self.server.listen(0)  # Можно установить ограничение, 0 - без ограничений

        threading.Thread(target=self.connect_handler).start()  # В отдельном потоке обрабатываем подключения
        print('Server is working...')

    def connect_handler(self):  # Обработчик подключений
        while True:
            client, address = self.server.accept()
            if client not in self.users_connected:
                self.users_connected.append(client)
                self.get_key()  # Генерируем сессионный ключ

                payload = ["SERVER_OK", f"{self.ip}:{str(self.port)}", self.symmetric_key]
                package = pickle.dumps(payload)
                client.sendall(package)

                threading.Thread(target=self.message_handler, args=(client,)).start()  # В отдельном потоке
                # обрабатываем сообщения нового пользователя

    def message_handler(self, client_socket) -> None:
        while True:
            try:
                message = client_socket.recv(1024)
                pickle_dec = pickle.loads(message)
                msg_status = pickle_dec[0]

            except Exception as e:
                print(e, 'has occurred on receiving')
                self.users_connected.remove(client_socket)
                return

            if msg_status == "ENCRYPT_MESSAGE":
                for client in self.users_connected:
                    client.send(message)

            elif msg_status == "EXIT":
                self.users_connected.remove(client_socket)
                client_socket.close()
                for client in self.users_connected:
                    client.send(message)
                return

    def get_key(self) -> None:
        if self.symmetric_key is None:
            self.symmetric_key = Fernet.generate_key()


if __name__ == "__main__":
    ip = input("Enter server IP: ")
    port = int(input("Enter port: "))
    ChatServer(ip, port)
