###
### THIS PYTHON FILE WILL ACT AS A SERVER FOR THE FLASK APPLICATION THAT RUNS TIGERENGINE AND COMMUNICATES WITH CHESSBUDDY
### V1.0
### (c) INERTIA ROBOTICS
###

from flask import Flask, request, jsonify
import subprocess
import threading
import os

class UCIEngine:
    def __init__(self, engine_path):
        self.process = subprocess.Popen(
            [engine_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        self.lock = threading.Lock()  # thread-safe access

        self.send_command("uci")
        self.wait_for("uciok")
        self.send_command("isready")
        self.wait_for("readyok")

    def send_command(self, cmd):
        print(f">>> {cmd}")
        self.process.stdin.write(cmd + '\n')
        self.process.stdin.flush()

    def wait_for(self, keyword):
        """Reads lines until a line with 'keyword' is found."""
        while True:
            line = self.process.stdout.readline().strip()
            print(f"<<< {line}")
            if keyword in line:
                return line

    def get_best_move(self, position_string):
        with self.lock:
            self.send_command(f"position {position_string}")
            self.send_command("go -v")
            while True:
                line = self.process.stdout.readline().strip()
                print(f"<<< {line}")
                if line.startswith("bestmove"):
                    return line.split()[1]


def create_app():
    app = Flask(__name__)

    engine_path = "./src/engine_executables/v7/TigerEngine"

    # start engine
    engine = UCIEngine(engine_path)


    @app.route('/')
    def home():
        return "TigerEngine server is running."

    @app.route('/get_move', methods=['POST'])
    def get_move():
        data = request.get_json()
        fen = data.get("fen", "").strip()
        moves = data.get("moves", "").strip()

        if not fen:
            return jsonify({"error": "FEN not provided"}), 400

        try:
            # Determine whether to use startpos or fen
            if fen == "startpos":
                position = "startpos"
            else:
                position = f"fen {fen}"

            if moves:
                position += f" moves {moves}"

            best_move = engine.get_best_move(position)
            return jsonify({"move": best_move})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return app

app = create_app()