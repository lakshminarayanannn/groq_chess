import chess
import chess.svg
import chess.pgn  
import base64
import os
import random
import json
from langchain_groq import ChatGroq
import time
import re
import logging
from io import StringIO, BytesIO 
from .utils import set_custom_css, display_header

class AIModule:
    def __init__(self, st, model="llama-3.1-8b-instant", temperature=0.1, max_tokens=700):
        try:
            self.st = st
            self.llm = ChatGroq(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
        except Exception as e:
            self.st.error(f"Failed to initialize ChatGroq model: {e}")
            self.st.stop()

    def get_ai_move(self, board, color, mode, max_retries=3):
        """
        Get the AI's move using ChatGroq.
        The AI is prompted differently based on the selected mode.
        """
        previous_invalid_move = None

        legal_moves = [move.uci() for move in board.legal_moves]
        legal_moves_str = ', '.join(legal_moves)

        for attempt in range(max_retries):
            board_matrix = self.get_board_matrix(board)
            board_str = '\n'.join([' '.join(row) for row in board_matrix])

            if previous_invalid_move:
                feedback = (
                    f"The move '{previous_invalid_move}' you provided was invalid or illegal in the current position. "
                    f"Please analyze the board state carefully, think about why your move was invalid, and provide a valid move from the available legal moves."
                )
            else:
                feedback = ""

            if mode == 'Chess Teaching':
                prompt = (
                    f"You are a 2800-rated chess grandmaster playing as {'Black' if color == chess.BLACK else 'White'}. "
                    f"Below is the current state of the chessboard:\n\n"
                    f"{board_str}\n\n"
                    f"The chessboard is represented by a matrix where 'wP' represents a white pawn, 'bK' represents a black king, and so on. "
                    f"Empty squares are shown as '__'. Analyze the board and suggest the best possible move for {'Black' if color == chess.BLACK else 'White'}.\n\n"
                    f"**Available Legal Moves:** {legal_moves_str}\n\n"  
                    f"**Rules for Chess:**\n"
                    f"1. **Pawn Movements:**\n"
                    f"   - Pawns move forward one square. From their initial position, they can move two squares forward.\n"
                    f"   - Pawns capture diagonally forward one square.\n"
                    f"   - En Passant and Promotion rules apply as per standard chess.\n"
                    f"2. **Knights:** Move in an 'L' shape: two squares in one direction and then one square perpendicular. Can jump over other pieces.\n"
                    f"3. **Bishops:** Move diagonally any number of squares. Each bishop remains on its initial color.\n"
                    f"4. **Rooks:** Move horizontally or vertically any number of squares. Involved in castling with the King.\n"
                    f"5. **Queens:** Move horizontally, vertically, or diagonally any number of squares. Combines the power of Rooks and Bishops.\n"
                    f"6. **Kings:** Move one square in any direction. Can perform castling with a Rook under specific conditions.\n"
                    f"7. **Special Moves:** Castling, En Passant, and Promotion as per standard rules.\n"
                    f"8. **Turn Order:** White moves first, followed by Black, alternating turns.\n\n"
                    f"{feedback}\n\n"
                    f"Please provide your move in UCI format (e.g., e2e4) and explain the reasoning behind your move to reinforce the thought process for your opponent's learning.\n\n"
                    f"**Important:** Respond **only** in the following exact format without any additional text or explanations:\n"
                    f"```\nMove: e2e4\nExplanation: Controls the center and opens lines for the bishop and queen.\n```"
                )
            else:  
                prompt = (
                    f"You are a 2800-rated chess grandmaster playing as {'Black' if color == chess.BLACK else 'White'}. "
                    f"Below is the current state of the chessboard:\n\n"
                    f"{board_str}\n\n"
                    f"The chessboard is represented by a matrix where 'wP' represents a white pawn, 'bK' represents a black king, and so on. "
                    f"Empty squares are shown as '__'. Analyze the board and suggest the best possible move for {'Black' if color == chess.BLACK else 'White'}.\n\n"
                    f"**Available Legal Moves:** {legal_moves_str}\n\n"  # Added legal moves
                    f"**Rules for Chess:**\n"
                    f"1. **Pawn Movements:**\n"
                    f"   - Pawns move forward one square. From their initial position, they can move two squares forward.\n"
                    f"   - Pawns capture diagonally forward one square.\n"
                    f"   - En Passant and Promotion rules apply as per standard chess.\n"
                    f"2. **Knights:** Move in an 'L' shape: two squares in one direction and then one square perpendicular. Can jump over other pieces.\n"
                    f"3. **Bishops:** Move diagonally any number of squares. Each bishop remains on its initial color.\n"
                    f"4. **Rooks:** Move horizontally or vertically any number of squares. Involved in castling with the King.\n"
                    f"5. **Queens:** Move horizontally, vertically, or diagonally any number of squares. Combines the power of Rooks and Bishops.\n"
                    f"6. **Kings:** Move one square in any direction. Can perform castling with a Rook under specific conditions.\n"
                    f"7. **Special Moves:** Castling, En Passant, and Promotion as per standard rules.\n"
                    f"8. **Turn Order:** White moves first, followed by Black, alternating turns.\n\n"
                    f"{feedback}\n\n"
                    f"Please provide your move in UCI format (e.g., e2e4).\n\n"
                    f"**Important:** Respond **only** in the following exact format without any additional text or explanations:\n"
                    f"```\nMove: e2e4\n```"
                )

            logging.info(f"AI Prompt (Mode: {mode}, Attempt: {attempt + 1}): {prompt}")

            try:
                response = self.llm.invoke([("system", prompt)])
                response_content = response.content.strip()
                logging.info(f"AI Response (Mode: {mode}, Attempt: {attempt + 1}): {response_content}")

                if mode == 'Chess Teaching':
                   
                    move, explanation = self.parse_teaching_response(response_content, board)
                    if move:
                        return move, explanation
                    else:
                        move_match = re.search(r"Move:\s*([a-h][1-8][a-h][1-8])", response_content, re.IGNORECASE)
                        if move_match:
                            previous_invalid_move = move_match.group(1).strip()
                        else:
                            previous_invalid_move = "unknown"
                        logging.warning(f"AI provided an invalid move on attempt {attempt + 1}. Response: {response_content}")
                        self.st.warning(f"AI provided an invalid move on attempt {attempt + 1}. Sending feedback to AI...")
                else:
                    move = self.parse_playing_response(response_content, board)
                    if move:
                        return move, None
                    else:
                        move_match = re.search(r"Move:\s*([a-h][1-8][a-h][1-8])", response_content, re.IGNORECASE)
                        if move_match:
                            previous_invalid_move = move_match.group(1).strip()
                        else:
                            previous_invalid_move = "unknown"
                        logging.warning(f"AI provided an invalid move on attempt {attempt + 1}. Response: {response_content}")
                        self.st.warning(f"AI provided an invalid move on attempt {attempt + 1}. Sending feedback to AI...")

            except Exception as e:
                logging.error(f"Error obtaining AI move on attempt {attempt + 1}: {e}")
                self.st.warning(f"Error obtaining AI move on attempt {attempt + 1}. Retrying...")

        self.st.warning("AI failed to provide a valid move after multiple attempts. Choosing a random legal move instead.")
        return self.select_random_move(board), None

    def parse_teaching_response(self, response_content, board):
        """
        Parse the AI response in Chess Teaching mode using regular expressions.
        Expected format:
        Move: e2e4
        Explanation: Controls the center and opens lines for the bishop and queen.
        """
        move_pattern = r"Move:\s*([a-h][1-8][a-h][1-8])"
        explanation_pattern = r"Explanation:\s*(.+)"

        move_match = re.search(move_pattern, response_content, re.IGNORECASE)
        explanation_match = re.search(explanation_pattern, response_content, re.IGNORECASE | re.DOTALL)

        if move_match and explanation_match:
            move_str = move_match.group(1)
            explanation = explanation_match.group(1).strip()
            move = self.parse_move(move_str, board)
            if move:
                if move in board.legal_moves:
                    return move, explanation
        logging.warning(f"Failed to parse teaching response. Content received: {response_content}")
        return None, None

    def parse_playing_response(self, response_content, board):
        """
        Parse the AI response in Chess Playing mode.
        Expected format:
        Move: e2e4
        """
        move_pattern = r"Move:\s*([a-h][1-8][a-h][1-8])"

        move_match = re.search(move_pattern, response_content, re.IGNORECASE)

        if move_match:
            move_str = move_match.group(1)
            move = self.parse_move(move_str, board)
            if move and move in board.legal_moves:
                return move
        else:
            potential_moves = re.findall(r'\b([a-h][1-8][a-h][1-8])\b', response_content)
            for pm in potential_moves:
                move = self.parse_move(pm, board)
                if move and move in board.legal_moves:
                    return move
        logging.warning(f"Failed to parse playing response. Content received: {response_content}")
        return None

    def select_random_move(self, board):
        """Select a random legal move from the current board."""
        move = random.choice(list(board.legal_moves))
        self.st.warning(f"Random Move Chosen: {move.uci()}")
        logging.info(f"Random Move Chosen: {move.uci()}")
        return move

    def get_board_matrix(self, board):
        """
        Returns the board as a list of strings representing each row.
        Each piece is represented by 'wP', 'bK', etc., and empty squares as '__'.
        """
        board_matrix = []
        for rank in range(7, -1, -1):  
            row = []
            for file in range(8): 
                square = chess.square(file, rank)
                piece = board.piece_at(square)
                if piece is None:
                    row.append('__')
                else:
                    color = 'w' if piece.color == chess.WHITE else 'b'
                    piece_symbol = piece.symbol().upper()
                    row.append(f"{color}{piece_symbol}")
            board_matrix.append(row)
        return board_matrix

    def parse_move(self, move_str, board):
        """Attempt to parse a move from a string, trying UCI and then SAN."""
        move = None
        try:
            move = chess.Move.from_uci(move_str)
            if move in board.legal_moves:
                return move
        except ValueError:
            pass
        try:
            move = board.parse_san(move_str)
            if move in board.legal_moves:
                return move
        except ValueError:
            pass
        return None

    def suggest_moves(self, board):
        """
        Get AI suggestions for the player's possible moves.
        """
        board_matrix = self.get_board_matrix(board)
        board_str = '\n'.join([' '.join(row) for row in board_matrix])

        legal_moves = [move.uci() for move in board.legal_moves]
        legal_moves_str = ', '.join(legal_moves)

        prompt = (
            f"You are a 2800-rated chess grandmaster. Below is the current state of the chessboard:\n\n"
            f"{board_str}\n\n"
            f"The chessboard is represented by a matrix where 'wP' represents a white pawn, 'bK' represents a black king, and so on. "
            f"Empty squares are shown as '__'. Analyze the board and suggest three strong candidate moves for {'White' if board.turn == chess.WHITE else 'Black'}'s next turn from the available legal moves, along with brief explanations.\n\n"
            f"**Available Legal Moves:** {legal_moves_str}\n\n"  
            f"**Rules for Chess:**\n"
            f"1. **Pawn Movements:**\n"
            f"   - Pawns move forward one square. From their initial position, they can move two squares forward.\n"
            f"   - Pawns capture diagonally forward one square.\n"
            f"   - En Passant and Promotion rules apply as per standard chess.\n"
            f"2. **Knights:** Move in an 'L' shape: two squares in one direction and then one square perpendicular. Can jump over other pieces.\n"
            f"3. **Bishops:** Move diagonally any number of squares. Each bishop remains on its initial color.\n"
            f"4. **Rooks:** Move horizontally or vertically any number of squares. Involved in castling with the King.\n"
            f"5. **Queens:** Move horizontally, vertically, or diagonally any number of squares. Combines the power of Rooks and Bishops.\n"
            f"6. **Kings:** Move one square in any direction. Can perform castling with a Rook under specific conditions.\n"
            f"7. **Special Moves:** Castling, En Passant, and Promotion as per standard rules.\n"
            f"8. **Turn Order:** White moves first, followed by Black, alternating turns.\n\n"
            f"Respond **only** in the following exact JSON format without additional text:\n"
            f"[\n"
            f'  {{"move": "<uci_move>", "explanation": "<reason>"}},\n'
            f'  {{"move": "<uci_move>", "explanation": "<reason>"}},\n'
            f'  {{"move": "<uci_move>", "explanation": "<reason>"}}\n'
            f"]\n\n"
            f"**Example:**\n"
            f"```\n"
            f'[\n'
            f'  {{"move": "e2e4", "explanation": "Controls the center and opens lines for the bishop and queen."}},\n'
            f'  {{"move": "d2d4", "explanation": "Establishes a strong pawn presence in the center."}},\n'
            f'  {{"move": "g1f3", "explanation": "Develops the knight to a natural square, preparing for kingside castling."}}\n'
            f"]\n"
            f"```"
        )

        logging.info(f"AI Suggestions Prompt: {prompt}")

        try:
            response = self.llm.invoke([("system", prompt)])
            response_content = response.content.strip()
            logging.info(f"AI Suggestions Response: {response_content}")

            suggestions = json.loads(response_content)
            if isinstance(suggestions, list) and len(suggestions) == 3:
                valid_suggestions = []
                for suggestion in suggestions:
                    move_str = suggestion.get('move', '').strip()
                    explanation = suggestion.get('explanation', '').strip()
                    move = self.parse_move(move_str, board)
                    if move and explanation and move in board.legal_moves:
                        suggestion['move'] = move.uci() 
                        valid_suggestions.append(suggestion)
                    else:
                        self.st.warning(f"AI suggested an invalid move or missing explanation: {move_str}. It will be skipped.")
                        logging.warning(f"Invalid suggestion: Move={move_str}, Explanation={explanation}")
                if len(valid_suggestions) == 0:
                    self.st.warning("No valid suggestions were provided by the AI.")
                return valid_suggestions
            else:
                self.st.warning("AI did not return a valid suggestions list.")
                logging.warning(f"Invalid suggestions format received: {response_content}")
                return []
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing AI suggestions: {e}")
            self.st.error("Failed to parse AI suggestions. Please try again.")
            return []
        except Exception as e:
            logging.error(f"Error obtaining AI suggestions: {e}")
            self.st.error("An error occurred while obtaining AI suggestions.")
            return []
