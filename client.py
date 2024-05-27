import socket
import threading

HOST = "127.0.0.1"
PORT = 1234


class Client:
    def __init__(self):
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect((HOST, PORT))
            threading.Thread(target=self.receive_packets).start()

        except socket.error:
            raise socket.error

    def receive_packets(self):
        while True:
            try:
                messages = self._socket.recv(1024).decode("ascii").split("\n")
                for message in messages:
                    if message == "ENTER_NICKNAME":
                        nickname = input("Nickname: ")
                        self._socket.sendall(nickname.encode("ascii"))

                    elif message == "START_GAME":
                        print("Waiting for server...")

                    elif message == "COORDINATES":
                        coordinates = input("Coordinates: ")
                        self._socket.sendall(coordinates.encode("ascii"))
                    else:
                        print(message)

            except:
                print("An error occurred!")
                self._socket.close()
                break


if __name__ == "__main__":
    client = Client()
