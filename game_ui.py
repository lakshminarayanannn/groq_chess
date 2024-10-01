import chess
import chess.svg
import chess.pgn  
import base64
from langchain_groq import ChatGroq
import time
import re
import logging
from io import StringIO, BytesIO  
from chess_game import ChessGame
from ai_module import AIModule
from utils import set_custom_css, display_header

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode()
        return encoded
    except FileNotFoundError:
        return None

class GameUI:
    def __init__(self, game: ChessGame, ai_module: AIModule, st):
        self.st = st
        self.game = game
        self.ai_module = ai_module
        self.mode = 'Chess Playing' 
        self.ai_explanation = ''
        self.suggestions = []
        set_custom_css(self)
        display_header(self)
        self.st.write("---")

    def render_board(self, board, size=400):
        svg = chess.svg.board(board=board, size=size)
        b64 = base64.b64encode(svg.encode('utf-8')).decode()
        html_img = f'<img src="data:image/svg+xml;base64,{b64}" />'
        self.st.markdown(html_img, unsafe_allow_html=True)

    def generate_move_history_table(self):
        import html
        moves = self.game.move_history
        temp_board = chess.Board()
        move_list = []
        move_number = 1
        move_pairs = [moves[i:i+2] for i in range(0, len(moves), 2)]
        for pair in move_pairs:
            white_move_san = ''
            black_move_san = ''
            try:
                if len(pair) >=1:
                    move = chess.Move.from_uci(pair[0])
                    san_move = temp_board.san(move)
                    temp_board.push(move)
                    white_move_san = san_move
            except ValueError:
                white_move_san = "Invalid Move"
            try:
                if len(pair) == 2:
                    move = chess.Move.from_uci(pair[1])
                    san_move = temp_board.san(move)
                    temp_board.push(move)
                    black_move_san = san_move
            except ValueError:
                black_move_san = "Invalid Move"
            move_list.append({'Move': move_number, 'White': white_move_san, 'Black': black_move_san})
            move_number +=1
        table_html = '<div class="move-history-table">'
        table_html += '<table>'
        table_html += '<tr><th>Move</th><th>White</th><th>Black</th></tr>'
        for row in move_list:
            table_html += f"<tr><td>{row['Move']}</td><td>{html.escape(row['White'])}</td><td>{html.escape(row['Black'])}</td></tr>"
        table_html += '</table></div>'
        return table_html

    def initial_setup(self):
        self.st.header("Game Setup")
        with self.st.form("setup_form"):
            col1, col2 = self.st.columns(2)
            with col1:
                self.st.markdown("### White Player")
                player_white_type = self.st.radio("Select White Player Type:", options=['Human', 'AI'], key='player_white_type_input')
                if player_white_type == 'Human':
                    player_white = self.st.text_input("White Player Name:", key="player_white_input")
                else:
                    player_white = 'AI'
            with col2:
                self.st.markdown("### Black Player")
                player_black_type = self.st.radio("Select Black Player Type:", options=['Human', 'AI'], key='player_black_type_input')
                if player_black_type == 'Human':
                    player_black = self.st.text_input("Black Player Name:", key="player_black_input")
                else:
                    player_black = 'AI'
            self.st.markdown("### Timer Settings")
            timer_type = self.st.selectbox(
                "Select Timer Option:",
                ('No Timer', '1 Minute', '5 Minutes', '10 Minutes', 'Custom Minutes'),
                key="timer_type_input"
            )
            if timer_type == 'Custom Minutes':
                custom_time = self.st.number_input(
                    "Enter Custom Time (in minutes):",
                    min_value=1,
                    max_value=60,
                    value=5,
                    step=1,
                    key="custom_time_input"
                )
            else:
                custom_time = 0
            self.st.markdown("### Import Game")
            uploaded_pgn = self.st.file_uploader("Upload a PGN file to import a game:", type=["pgn"])
            submitted = self.st.form_submit_button("Start Game")
            if submitted:
                if player_white_type == 'Human' and not player_white.strip():
                    self.st.error("Please enter a name for the White player.")
                elif player_black_type == 'Human' and not player_black.strip():
                    self.st.error("Please enter a name for the Black player.")
                else:
                    self.game.player_white_type = player_white_type
                    self.game.player_black_type = player_black_type
                    self.game.player_white = player_white.strip() if player_white_type == 'Human' else 'AI'
                    self.game.player_black = player_black.strip() if player_black_type == 'Human' else 'AI'
                    self.game.timer_type = timer_type
                    self.game.custom_time = custom_time
                    if timer_type == '1 Minute':
                        self.game.timer_white = 60 
                        self.game.timer_black = 60
                    elif timer_type == '5 Minutes':
                        self.game.timer_white = 300 
                        self.game.timer_black = 300
                    elif timer_type == '10 Minutes':
                        self.game.timer_white = 600 
                        self.game.timer_black = 600
                    elif timer_type == 'Custom Minutes':
                        self.game.timer_white = custom_time * 60
                        self.game.timer_black = custom_time * 60
                    else: 
                        self.game.timer_white = 0
                        self.game.timer_black = 0
                    self.game.last_move_time = time.time()
                    self.game.game_started = True
                    if uploaded_pgn is not None:
                        pgn_text = uploaded_pgn.read().decode('utf-8')
                        success = self.game.import_pgn(pgn_text)
                        if success:
                            self.st.success("PGN file imported successfully.")
                        else:
                            self.st.error("Failed to import PGN file.")
                    self.st.rerun()

    def main_game(self):
        board = self.game.board
        set_custom_css(self)
        display_header(self)
        self.game.update_timers()
        mode_col, main_col, suggestions_col = self.st.columns([1, 3, 2])
        with mode_col:
            self.st.write("### Mode")
            mode = self.st.radio(
                "Select Mode:",
                ('Chess Playing', 'Chess Teaching'),
                index=0,  
                key='mode_radio'
            )
            self.mode = mode
            self.st.write("### Actions")
            if self.st.button("Undo Move"):
                self.game.undo_move()
                self.st.rerun()
            if self.st.button("Redo Move"):
                self.game.redo_move()
                self.st.rerun()
            self.st.write("### Export Game")
            if self.st.button("Download PGN"):
                pgn_string = self.game.export_pgn()
                b64_pgn = base64.b64encode(pgn_string.encode()).decode()
                href = f'<a href="data:text/plain;base64,{b64_pgn}" download="game.pgn">Click here to download your PGN file</a>'
                self.st.markdown(href, unsafe_allow_html=True)
                logging.info("PGN file downloaded by user.")
        with main_col:
            col_white, col_black = self.st.columns(2)
            with col_white:
                self.st.markdown(f"**{self.game.player_white} (White)**")
                if self.game.timer_white > 0:
                    self.st.markdown(f"Timer: **{self.game.format_time(self.game.timer_white)}**")
                else:
                    self.st.markdown("Timer: **No Timer**")
            with col_black:
                self.st.markdown(f"**{self.game.player_black} (Black)**")
                if self.game.timer_black > 0:
                    self.st.markdown(f"Timer: **{self.game.format_time(self.game.timer_black)}**")
                else:
                    self.st.markdown("Timer: **No Timer**")
            self.render_board(board)
            self.st.write("### Move History")
            move_history_html = self.generate_move_history_table()
            self.st.markdown(move_history_html, unsafe_allow_html=True)
            if board.is_game_over():
                self.game.game_over = True
                result = board.result(claim_draw=True)
                if result == '1-0':
                    self.game.result = f"{self.game.player_white} wins!"
                elif result == '0-1':
                    self.game.result = f"{self.game.player_black} wins!"
                else:
                    self.game.result = "It's a draw!"
                self.st.write("### 🏁 Game Over")
                self.st.write(f"**Result:** {self.game.result}")
                logging.info(f"Game Over: {self.game.result}")
                if self.st.button("Restart Game"):
                    self.reset_game()
                    self.st.rerun()
                self.st.stop()
            if board.turn == chess.WHITE:
                player_type = self.game.player_white_type
                player_name = self.game.player_white
                self.st.write(f"### **{player_name}'s Turn (White)**")
                if player_type == 'Human':
                    move_col, make_move_col, suggestions_button_col = self.st.columns([2, 1, 1])
                    with move_col:
                        user_move = self.st.text_input("Enter move (UCI or SAN format):", key="user_move_white")
                    with make_move_col:
                        if self.st.button("Make Move", key="make_move_white"):
                            move = self.ai_module.parse_move(user_move.strip(), board)
                            if move:
                                self.game.make_move(move)
                                self.suggestions = []
                                self.st.rerun()
                            else:
                                self.st.error("Invalid or illegal move. Please try again.")
                                logging.warning(f"Invalid move entered by {player_name}: {user_move.strip()}")
                    with suggestions_button_col:
                        if self.mode == 'Chess Teaching':
                            if self.st.button("Get AI Suggestions", key="get_suggestions_white"):
                                self.suggestions = self.ai_module.suggest_moves(board)
                                logging.info("AI Suggestions requested by user.")
                else:
                    with self.st.spinner(f"{player_name} (AI) is thinking..."):
                        ai_move, explanation = self.ai_module.get_ai_move(board, chess.WHITE, self.mode)
                        if ai_move:
                            self.game.make_move(ai_move)
                            self.st.success(f"{player_name} (AI) plays: **{ai_move.uci()}**")
                            logging.info(f"AI played move: {ai_move.uci()}")
                            if self.mode == 'Chess Teaching' and explanation:
                                self.st.markdown(f"**Explanation:** {explanation}")
                            self.st.rerun()
            else:
                player_type = self.game.player_black_type
                player_name = self.game.player_black
                self.st.write(f"### **{player_name}'s Turn (Black)**")
                if player_type == 'Human':
                    move_col, make_move_col = self.st.columns([2, 1])
                    with move_col:
                        user_move = self.st.text_input("Enter move (UCI or SAN format):", key="user_move_black")
                    with make_move_col:
                        if self.st.button("Make Move", key="make_move_black"):
                            move = self.ai_module.parse_move(user_move.strip(), board)
                            if move:
                                self.game.make_move(move)
                                self.suggestions = []
                                self.st.rerun()
                            else:
                                self.st.error("Invalid or illegal move. Please try again.")
                                logging.warning(f"Invalid move entered by {player_name}: {user_move.strip()}")
                else:
                    with self.st.spinner(f"{player_name} (AI) is thinking..."):
                        ai_move, explanation = self.ai_module.get_ai_move(board, chess.BLACK, self.mode)
                        if ai_move:
                            self.game.make_move(ai_move)
                            self.st.success(f"{player_name} (AI) plays: **{ai_move.uci()}**")
                            logging.info(f"AI played move: {ai_move.uci()}")
                            if self.mode == 'Chess Teaching' and explanation:
                                self.st.markdown(f"**Explanation:** {explanation}")
                            self.st.rerun()
        with suggestions_col:
            if self.mode == 'Chess Teaching' and self.suggestions:
                self.st.write("### AI Move Suggestions:")
                for i, suggestion in enumerate(self.suggestions):
                    suggestion_col, preview_col = self.st.columns([1, 1.5])
                    with suggestion_col:
                        if self.st.button(f"Play {suggestion['move']}", key=f"suggestion_move_{i}"):
                            move = self.ai_module.parse_move(suggestion['move'], board)
                            if move:
                                self.game.make_move(move)
                                self.suggestions = []
                                self.st.rerun()
                            else:
                                self.st.error("Invalid move selected from suggestions.")
                                logging.warning(f"Invalid suggestion move selected: {suggestion['move']}")
                        self.st.markdown(f"<div class='small-font'>{suggestion['explanation']}</div>", unsafe_allow_html=True)
                    with preview_col:
                        temp_board = board.copy()
                        move = self.ai_module.parse_move(suggestion['move'], temp_board)
                        if move:
                            temp_board.push(move)
                            self.render_board(temp_board, size=200)
                        else:
                            self.st.write("Invalid move preview.")
                    self.st.markdown("<div class='suggestion-separator'></div>", unsafe_allow_html=True)

    def reset_game(self):
        self.game.reset()
        self.mode = 'Chess Playing'
        self.ai_explanation = ''
        self.suggestions = []
        logging.info("Game has been reset.")