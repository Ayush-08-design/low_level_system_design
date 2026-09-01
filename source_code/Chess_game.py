from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, List, Tuple


# ==========================================
# 1. Enums & Value Objects
# ==========================================

class Color(Enum):
    WHITE = "White"
    BLACK = "Black"


class GameStatus(Enum):
    ACTIVE = "Active"
    WHITE_WIN = "White Won"
    BLACK_WIN = "Black Won"
    STALEMATE = "Stalemate"


class Position:
    """Represents a coordinate (row, col) on an 8x8 chess board (0-indexed)."""
    def __init__(self, row: int, col: int):
        self.row = row
        self.col = col

    def is_valid(self) -> bool: # validates position on the board only boundary
        return 0 <= self.row < 8 and 0 <= self.col < 8

    def __eq__(self, other) -> bool:
        return isinstance(other, Position) and self.row == other.row and self.col == other.col

    def __repr__(self):
        # Convert to standard algebraic notation (e.g., Position(7, 4) -> 'e1')
        col_name = chr(ord('a') + self.col)
        row_name = str(8 - self.row)
        return f"{col_name}{row_name}"


# ==========================================
# 2. Piece Hierarchy (Polymorphism)
# ==========================================

class Piece(ABC):
    """Abstract base class for all chess pieces."""
    def __init__(self, color: Color, symbol: str):
        self.color = color
        self.symbol = symbol
        self.has_moved = False

    @abstractmethod # all new classes inherit this abstract class will need to implement this abstract method
    def can_move(self, board: 'Board', start: Position, end: Position) -> bool:
        """Determines if the piece can theoretically move from start to end."""
        pass

    def __str__(self):
        return self.symbol


class Pawn(Piece):
    def __init__(self, color: Color):
        symbol = "♟" if color == Color.BLACK else "♙"
        super().__init__(color, symbol)

    def can_move(self, board: 'Board', start: Position, end: Position) -> bool:
        direction = 1 if self.color == Color.BLACK else -1
        row_diff = end.row - start.row
        col_diff = abs(end.col - start.col)

        target_piece = board.get_piece(end)

        # Standard 1-square forward move
        if col_diff == 0 and row_diff == direction and target_piece is None:
            return True

        # Initial 2-square forward move
        if col_diff == 0 and row_diff == 2 * direction and not self.has_moved:
            intermediate = Position(start.row + direction, start.col)
            if board.get_piece(intermediate) is None and target_piece is None:
                return True

        # Diagonal capture
        if col_diff == 1 and row_diff == direction and target_piece is not None:
            return target_piece.color != self.color

        return False


class Knight(Piece):
    def __init__(self, color: Color):
        symbol = "♞" if color == Color.BLACK else "♘"
        super().__init__(color, symbol)

    def can_move(self, board: 'Board', start: Position, end: Position) -> bool:
        row_diff = abs(end.row - start.row)
        col_diff = abs(end.col - start.col)
        # L-shape: (2, 1) or (1, 2)
        if (row_diff, col_diff) in [(1, 2), (2, 1)]:
            target = board.get_piece(end)
            return target is None or target.color != self.color
        return False


class Bishop(Piece):
    def __init__(self, color: Color):
        symbol = "♝" if color == Color.BLACK else "♗"
        super().__init__(color, symbol)

    def can_move(self, board: 'Board', start: Position, end: Position) -> bool:
        if abs(end.row - start.row) == abs(end.col - start.col):
            if board.is_path_clear(start, end):
                target = board.get_piece(end)
                return target is None or target.color != self.color
        return False


class Rook(Piece):
    def __init__(self, color: Color):
        symbol = "♜" if color == Color.BLACK else "♖"
        super().__init__(color, symbol)

    def can_move(self, board: 'Board', start: Position, end: Position) -> bool:
        if start.row == end.row or start.col == end.col:
            if board.is_path_clear(start, end):
                target = board.get_piece(end)
                return target is None or target.color != self.color
        return False


class Queen(Piece):
    def __init__(self, color: Color):
        symbol = "♛" if color == Color.BLACK else "♕"
        super().__init__(color, symbol)

    def can_move(self, board: 'Board', start: Position, end: Position) -> bool:
        # Queen combines Rook (straight) and Bishop (diagonal) movement
        is_straight = (start.row == end.row or start.col == end.col)
        is_diagonal = (abs(end.row - start.row) == abs(end.col - start.col))

        if (is_straight or is_diagonal) and board.is_path_clear(start, end):
            target = board.get_piece(end)
            return target is None or target.color != self.color
        return False


class King(Piece):
    def __init__(self, color: Color):
        symbol = "♚" if color == Color.BLACK else "♔"
        super().__init__(color, symbol)

    def can_move(self, board: 'Board', start: Position, end: Position) -> bool:
        row_diff = abs(end.row - start.row)
        col_diff = abs(end.col - start.col)
        # King moves 1 square in any direction
        if max(row_diff, col_diff) == 1:
            target = board.get_piece(end)
            return target is None or target.color != self.color
        return False


# ==========================================
# 3. Board & Move Management
# ==========================================

class Move:
    """Encapsulates a single move record."""
    def __init__(self, start: Position, end: Position, piece_moved: Piece, piece_captured: Optional[Piece] = None):
        self.start = start
        self.end = end
        self.piece_moved = piece_moved
        self.piece_captured = piece_captured

    def __repr__(self):
        capture_str = f" x {self.piece_captured}" if self.piece_captured else ""
        return f"{self.piece_moved} from {self.start} to {self.end}{capture_str}"


class Board:
    """Manages the 8x8 board state and piece queries."""
    def __init__(self):
        self.grid: List[List[Optional[Piece]]] = [[None for _ in range(8)] for _ in range(8)]
        self._setup_initial_pieces()

    def get_piece(self, pos: Position) -> Optional[Piece]:
        if not pos.is_valid():
            return None
        return self.grid[pos.row][pos.col]

    def set_piece(self, pos: Position, piece: Optional[Piece]):
        if pos.is_valid():
            self.grid[pos.row][pos.col] = piece

    def is_path_clear(self, start: Position, end: Position) -> bool:
        """Verifies no pieces block the line between start and end (exclusive)."""
        row_step = 0 if start.row == end.row else (1 if end.row > start.row else -1)
        col_step = 0 if start.col == end.col else (1 if end.col > start.col else -1)

        curr_row = start.row + row_step
        curr_col = start.col + col_step

        while (curr_row, curr_col) != (end.row, end.col):
            if self.grid[curr_row][curr_col] is not None:
                return False
            curr_row += row_step
            curr_col += col_step
        return True

    def find_king(self, color: Color) -> Optional[Position]:
        for r in range(8):
            for c in range(8):
                piece = self.grid[r][c]
                if isinstance(piece, King) and piece.color == color:
                    return Position(r, c)
        return None

    def _setup_initial_pieces(self):
        # Setup Major/Minor pieces for Black (Row 0) and White (Row 7)
        piece_order = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
        for col, piece_cls in enumerate(piece_order):
            self.grid[0][col] = piece_cls(Color.BLACK)
            self.grid[7][col] = piece_cls(Color.WHITE)

        # Setup Pawns
        for col in range(8):
            self.grid[1][col] = Pawn(Color.BLACK)
            self.grid[6][col] = Pawn(Color.WHITE)

    def display(self):
        print("\n    a   b   c   d   e   f   g   h")
        print("  +---+---+---+---+---+---+---+---+")
        for r in range(8):
            row_str = f"{8 - r} |"
            for c in range(8):
                piece = self.grid[r][c]
                symbol = str(piece) if piece else " "
                row_str += f" {symbol} |"
            print(row_str + f" {8 - r}")
            print("  +---+---+---+---+---+---+---+---+")
        print("    a   b   c   d   e   f   g   h\n")


# ==========================================
# 4. Game Controller (State & Rules)
# ==========================================

class Player:
    def __init__(self, name: str, color: Color):
        self.name = name
        self.color = color


class ChessGame:
    """Coordinates turn flow, validates check constraints, and tracks game state."""
    def __init__(self, white_player: Player, black_player: Player):
        self.board = Board()
        self.players = {Color.WHITE: white_player, Color.BLACK: black_player}
        self.current_turn = Color.WHITE
        self.status = GameStatus.ACTIVE
        self.move_history: List[Move] = []

    def is_in_check(self, color: Color) -> bool:
        """Checks if the King of the specified color is under direct attack."""
        king_pos = self.board.find_king(color)
        if not king_pos:
            return False

        opp_color = Color.BLACK if color == Color.WHITE else Color.WHITE

        # Check if any opposing piece has a valid attack trajectory to the king
        for r in range(8):
            for c in range(8):
                piece = self.board.get_piece(Position(r, c))
                if piece and piece.color == opp_color:
                    if piece.can_move(self.board, Position(r, c), king_pos):
                        return True
        return False

    def make_move(self, start: Position, end: Position) -> bool:
        """Validates and executes a move."""
        if self.status != GameStatus.ACTIVE:
            print(f"Game over: {self.status.value}")
            return False

        piece = self.board.get_piece(start)

        # 1. Basic validation
        if not piece:
            print("No piece at source position.")
            return False
        if piece.color != self.current_turn:
            print(f"It is {self.current_turn.value}'s turn.")
            return False
        if not piece.can_move(self.board, start, end):
            print("Illegal piece movement.")
            return False

        # 2. Prevent moving into Check (Simulate move)
        captured = self.board.get_piece(end)
        self.board.set_piece(end, piece)
        self.board.set_piece(start, None)

        if self.is_in_check(self.current_turn):
            # Undo move if it leaves the player in check
            self.board.set_piece(start, piece)
            self.board.set_piece(end, captured)
            print("Move invalid: Leaves King in check.")
            return False

        # 3. Finalize Move
        piece.has_moved = True
        move = Move(start, end, piece, captured)
        self.move_history.append(move)

        # 4. Switch Turns
        self.current_turn = Color.BLACK if self.current_turn == Color.WHITE else Color.WHITE
        return True
    
    
# Testing
    
if __name__ == "__main__":
    p1 = Player("Alice", Color.WHITE)
    p2 = Player("Bob", Color.BLACK)
    game = ChessGame(p1, p2)

    game.board.display()

    # Move White Pawn from e2 (6, 4) to e4 (4, 4)
    print("Moving White Pawn e2 -> e4:")
    game.make_move(Position(6, 4), Position(4, 4))
    game.board.display()

    # Move Black Pawn from e7 (1, 4) to e5 (3, 4)
    print("Moving Black Pawn e7 -> e5:")
    game.make_move(Position(1, 4), Position(3, 4))
    game.board.display()

    # Move White Knight from g1 (7, 6) to f3 (5, 5)
    print("Moving White Knight g1 -> f3:")
    game.make_move(Position(7, 6), Position(5, 5))
    game.board.display()