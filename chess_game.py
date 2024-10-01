import chess
import chess.svg
import chess.pgn  # 
from langchain_groq import ChatGroq
import time
import re
import logging
from io import StringIO, BytesIO
from utils import set_custom_css, display_header

class ChessGame:
    def __init__(self,st):
        self.st = st
        self.board = chess.Board()
        self.game_started = False
        self.game_over = False
        self.result = None
        self.move_history = []
        self.undo_stack = []
        self.redo_stack = []
        self.player_white = ''
        self.player_black = ''
        self.player_white_type = 'Human'  
        self.player_black_type = 'AI'     
        self.timer_type = 'No Timer'
        self.timer_white = 0
        self.timer_black = 0
        self.custom_time = 0
        self.last_move_time = None

    def reset(self):
        self.board.reset()
        self.game_started = False
        self.game_over = False
        self.result = None
        self.move_history = []
        self.undo_stack = []
        self.redo_stack = []
        self.player_white = ''
        self.player_black = ''
        self.player_white_type = 'Human'
        self.player_black_type = 'AI'
        self.timer_type = 'No Timer'
        self.timer_white = 0
        self.timer_black = 0
        self.custom_time = 0
        self.last_move_time = None

    def make_move(self, move):
        self.board.push(move)
        self.move_history.append(move.uci())
        self.undo_stack.append(move)
        self.redo_stack.clear()
        self.last_move_time = time.time()
        logging.info(f"Move made: {move.uci()}")

    def undo_move(self):
        if self.undo_stack:
            move = self.undo_stack.pop()
            self.board.pop()
            self.move_history.pop()
            self.redo_stack.append(move)
            self.last_move_time = time.time()
            logging.info(f"Move undone: {move.uci()}")
        else:
            self.st.warning("No moves to undo.")

    def redo_move(self):
        if self.redo_stack:
            move = self.redo_stack.pop()
            self.board.push(move)
            self.move_history.append(move.uci())
            self.undo_stack.append(move)
            self.last_move_time = time.time()
            logging.info(f"Move redone: {move.uci()}")
        else:
            self.st.warning("No moves to redo.")

    def export_pgn(self):
        game = chess.pgn.Game()
        node = game
        temp_board = chess.Board()

        for move_uci in self.move_history:
            move = chess.Move.from_uci(move_uci)
            node = node.add_variation(move)
            temp_board.push(move)

        game.headers["Event"] = "Chess Game"
        game.headers["White"] = self.player_white
        game.headers["Black"] = self.player_black
        game.headers["Result"] = temp_board.result()

        exporter = chess.pgn.StringExporter(headers=True, variations=False, comments=False)
        pgn_string = game.accept(exporter)
        logging.info("Game exported to PGN.")
        return pgn_string

    def import_pgn(self, pgn_text):
        try:
            game = chess.pgn.read_game(StringIO(pgn_text))
            if game is None:
                self.st.error("No game found in the PGN file.")
                logging.error("No game found in the PGN file.")
                return False

            board = game.board()
            move_history = []
            undo_stack = []

            for move in game.mainline_moves():
                board.push(move)
                move_history.append(move.uci())
                undo_stack.append(move)

            self.board = board
            self.move_history = move_history
            self.undo_stack = undo_stack
            self.redo_stack = []
            self.game_started = True
            self.game_over = board.is_game_over()
            self.result = board.result() if board.is_game_over() else None
            logging.info("PGN file imported successfully.")
            return True
        except Exception as e:
            self.st.error(f"Failed to import PGN: {e}")
            logging.error(f"Failed to import PGN: {e}")
            return False

    def format_time(self, seconds):
        """Format the time in seconds to MM:SS format."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    def update_timers(self):
        if self.last_move_time is not None:
            current_time = time.time()
            elapsed_time = current_time - self.last_move_time

            if self.board.turn == chess.WHITE:
                if self.timer_white > 0:
                    self.timer_white = max(self.timer_white - elapsed_time, 0)
                    if self.timer_white == 0:
                        self.game_over = True
                        self.result = f"{self.player_black} wins on time!"
                        logging.info(f"{self.player_black} wins on time.")
            else:
                if self.timer_black > 0:
                    self.timer_black = max(self.timer_black - elapsed_time, 0)
                    if self.timer_black == 0:
                        self.game_over = True
                        self.result = f"{self.player_white} wins on time!"
                        logging.info(f"{self.player_white} wins on time.")
            self.last_move_time = current_time
        else:
            self.last_move_time = time.time()
