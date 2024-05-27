import random
import socket
import threading

HOST = "127.0.0.1"
PORT = 1234
MAX_NO_PLAYERS = 3

# 00A0000000
# 1111100020
# 0010002020
# 011100222B
# 0000002020
# 0000000020
# 0003330000
# 0000300000
# 0033333000
# 0000C00000


class Server:
    def __init__(self):
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.bind((HOST, PORT))
            self._socket.listen()
            self._game_state = 0
            self._lock = threading.Lock()
        except socket.error:
            raise socket.error

        self._clients = []
        self._addresses = []
        self._nicknames = []

    def broadcast(self, message, excluded_client=None):
        with self._lock:
            for client in self._clients:
                if client != excluded_client:
                    client.sendall(message)

    def handle_connection(self, client):
        while True:
            with self._lock:
                game_state = self._game_state

            if game_state == 1:
                try:
                    message = client.recv(1024).decode("ascii")
                    print(message)
                except:
                    with self._lock:
                        index = self._clients.index(client)

                        self._clients.remove(client)
                        client.close()

                        nickname = self._nicknames[index]
                        self.broadcast(
                            f"{nickname} has disconnected! Waiting for {MAX_NO_PLAYERS - len(self._clients)} more players.\n"
                            .encode("ascii")
                        )
                        self._nicknames.remove(nickname)

                        address = self._addresses[index]
                        print(f"Client {str(address)} disconnected.\n")
                        self._addresses.remove(address)

                        break

    def receive_connections(self):
        waiting_for_connections = True
        while waiting_for_connections:
            client, address = self._socket.accept()
            print(f"New client connected: {str(address)}.\n")

            client.sendall("ENTER_NICKNAME\n".encode("ascii"))
            nickname = client.recv(1024).decode("ascii")

            with self._lock:
                self._nicknames.append(nickname)
            self._clients.append(client)
            self._addresses.append(address)

            if len(self._clients) == MAX_NO_PLAYERS:
                self.broadcast(
                    "Game starting...\n"
                    .encode("ascii")
                )
                waiting_for_connections = False
                self._game_state = 1
                self.start_game()

            client.sendall(
                f"Welcome to the server! There are currently {len(self._clients)} players connected".encode("ascii")
            )

            print(f"Client {str(address)} has set their nickname to {nickname}")
            self.broadcast(
                f"{nickname} has connected! Waiting for {MAX_NO_PLAYERS - len(self._clients)} more players."
                .encode("ascii"),
                excluded_client=client
            )

    def start_game(self):
        game_matrix = [
            ['0', '0', 'A', '0', '0', '0', '0', '0', '0', '0'],
            ['1', '1', '1', '1', '1', '0', '0', '0', '2', '0'],
            ['0', '0', '1', '0', '0', '0', '2', '0', '2', '0'],
            ['0', '1', '1', '1', '0', '0', '2', '2', '2', 'B'],
            ['0', '0', '0', '0', '0', '0', '2', '0', '2', '0'],
            ['0', '0', '0', '0', '0', '0', '0', '0', '2', '0'],
            ['0', '0', '0', '3', '3', '3', '0', '0', '0', '0'],
            ['0', '0', '0', '0', '3', '0', '0', '0', '0', '0'],
            ['0', '0', '3', '3', '3', '3', '3', '0', '0', '0'],
            ['0', '0', '0', '0', 'C', '0', '0', '0', '0', '0'],
        ]

        plane_heads = ['A', 'B', 'C']
        planes_alive = 3

        self.broadcast("START_GAME\n".encode("ascii"))

        # load map config
        self.broadcast("Map loaded!\n".encode("ascii"))

        current_player_index = 0
        game_ongoing = True
        game_finished = False
        game_interrupted = False

        while game_ongoing:
            current_client = self._clients[current_player_index]
            current_player_nickname = self._nicknames[current_player_index]

            self.broadcast(
                f"{current_player_nickname}'s turn. Enter the coordinates you want to bomb.\n".encode("ascii"),
                excluded_client=current_client)
            current_client.sendall("COORDINATES".encode("ascii"))

            coordinates = current_client.recv(1024).decode("ascii")
            print(f"{current_player_nickname}: Coordinates {coordinates}")

            c_x, c_y = map(lambda x: int(x), coordinates.split(" "))

            if game_matrix[c_x][c_y] == '0':
                self.broadcast("0\n".encode("ascii"))
            else:
                if game_matrix[c_x][c_y] == '1':
                    self.broadcast("1\n".encode("ascii"))
                elif game_matrix[c_x][c_y] in plane_heads:
                    self.broadcast("X\n".encode("ascii"))
                    planes_alive = planes_alive - 1

                game_matrix[c_x][c_y] = '0'

            if planes_alive == 0:
                game_ongoing = False
                game_finished = True
                self.broadcast(f"{current_player_nickname} has won! Restarting game...\n".encode("ascii"))

            else:
                current_player_index += 1
                if current_player_index >= len(self._clients):
                    current_player_index = 0

        if game_finished:
            self.start_game()


if __name__ == "__main__":
    server = Server()
    print(f"Server listening on port {PORT}")
    server.receive_connections()
