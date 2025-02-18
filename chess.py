from enum import IntFlag
import re
import numpy as np


class ChessException(Exception):
    pass


class NotYourTurn(ChessException):
    """The other players move"""


class NoPiecePresent(ChessException):
    """The selected square is empty"""


class IllegalMove(ChessException):
    """The given move is illegal"""


class InvalidSquare(ChessException):
    """The square is out of the boundaries of the chess board"""


class DrawException(ChessException):
    """The game is over: draw"""


class CheckmateException(ChessException):
    """The game is over: checkmate"""


class Piece(IntFlag):
    PAWN = 1
    KNIGHT = 2
    BISHOP = 4
    ROOK = 8
    QUEEN = 16
    KING = 32


class Colour(IntFlag):
    WHITE = 0
    BLACK = 64

    def opposite(self):
        if self == Colour.WHITE:
            return Colour.BLACK
        else:
            return Colour.WHITE

    def __str__(self):
        if self == 0:
            return 'White'
        else:
            return 'Black'


files = dict()
files['A'] = 0
files['B'] = 1
files['C'] = 2
files['D'] = 3
files['E'] = 4
files['F'] = 5
files['G'] = 6
files['H'] = 7

ranks = dict()
ranks['1'] = 0
ranks['2'] = 1
ranks['3'] = 2
ranks['4'] = 3
ranks['5'] = 4
ranks['6'] = 5
ranks['7'] = 6
ranks['8'] = 7

pieceValues = dict()
pieceValues['P'] = Piece.PAWN + Colour.WHITE
pieceValues['N'] = Piece.KNIGHT + Colour.WHITE
pieceValues['B'] = Piece.BISHOP + Colour.WHITE
pieceValues['R'] = Piece.ROOK + Colour.WHITE
pieceValues['Q'] = Piece.QUEEN + Colour.WHITE
pieceValues['K'] = Piece.KING + Colour.WHITE
pieceValues['p'] = Piece.PAWN + Colour.BLACK
pieceValues['n'] = Piece.KNIGHT + Colour.BLACK
pieceValues['b'] = Piece.BISHOP + Colour.BLACK
pieceValues['r'] = Piece.ROOK + Colour.BLACK
pieceValues['q'] = Piece.QUEEN + Colour.BLACK
pieceValues['k'] = Piece.KING + Colour.BLACK

# reverse version of the pieces dict
valuePieces = {v: k for k, v in pieceValues.items()}


class Chess:
    board = np.zeros((8, 8), dtype=np.uint8)
    moves = dict()

    toMove = Colour.WHITE
    enPassantTarget = None

    long_castle = dict()
    long_castle[Colour.WHITE] = True
    long_castle[Colour.BLACK] = True
    short_castle = dict()
    short_castle[Colour.WHITE] = True
    short_castle[Colour.BLACK] = True

    halfMoveClock = 0
    moveCounter = 1

    lastFen = ''

    def move(self, start: tuple, end: tuple, promote_to: Piece = Piece.QUEEN) -> tuple:
        capture = False
        p = self.val_to_piece(self.board[start])

        if not p:
            raise NoPiecePresent('No piece present')

        if p[1] != self.toMove:
            raise NotYourTurn(f'{p[1]} to move')

        if end not in self.legal_moves(start):
            raise IllegalMove('Illegal move')

        # For fifty move rule
        if self.board[end] != 0:
            capture = True

        self._push_move(start, end, p, promote_to)

        # Clear previous en passant target
        self.enPassantTarget = None

        # Add new en passant target when a double pawn move was made
        if p[0] == Piece.PAWN and end[0] - start[0] == 2:
            self.enPassantTarget = (start[0] + 1, start[1])
        if p[0] == Piece.PAWN and end[0] - start[0] == -2:
            self.enPassantTarget = (start[0] - 1, start[1])

        # Remove castling privileges when either the rook or king has moved
        if p[0] == Piece.KING:
            self.long_castle[p[1]] = self.short_castle[p[1]] = False

        if start in map(self.str_to_coor, ('A1', 'A8')):
            self.long_castle[p[1]] = False
        if start in map(self.str_to_coor, ('H1', 'H8')):
            self.short_castle[p[1]] = False

        self.toMove = self.toMove.opposite()

        if capture or p[0] == Piece.PAWN:
            self.halfMoveClock = 0
        else:
            self.halfMoveClock += 1

        if self.toMove == Colour.WHITE:
            self.moveCounter += 1

        # Record move
        self.moves[self._half_move_counter] = self.get_fen()

        # Win / Draw Categories
        if self._repetition():
            raise DrawException('Threefold repetition: Draw!')

        legal_moves = 0
        for piece_coors in self._get_pieces_by_colour(self.toMove):
            legal_moves += len(self.legal_moves(piece_coors))
        if legal_moves == 0:
            if self.in_check(self.toMove):
                raise CheckmateException(f'Checkmate: {self.toMove.opposite()} wins!')
            else:
                raise DrawException('Stalemate: Draw!')

        if self.halfMoveClock >= 50:
            raise DrawException('Fifty move rule: Draw!')

        return start, end

    def move_notation(self, notation: str) -> tuple:
        """Move in algebraic notation"""
        # Castling king side
        if 'O-O' == notation:
            if self.toMove == Colour.WHITE:
                return self.move(self.str_to_coor('E1'), self.str_to_coor('G1'))
            else:
                return self.move(self.str_to_coor('E8'), self.str_to_coor('G8'))

        # Castling queen side
        if 'O-O-O' == notation:
            if self.toMove == Colour.WHITE:
                return self.move(self.str_to_coor('E1'), self.str_to_coor('C1'))
            else:
                return self.move(self.str_to_coor('E8'), self.str_to_coor('C8'))

        match = re.search('^([KQBNR])?([abcdefg])?([12345678])?x?([abcdefgh][12345678])', notation)

        if match is None:
            raise ChessException(f'Invalid move: {notation}')

        eligible_pieces = []

        piece_str = match.group(1)
        dis_file = None if match.group(2) is None or piece_str is None else files[match.group(2).upper()]
        dis_rank = None if match.group(3) is None else ranks[match.group(3)]
        dest = self.str_to_coor(match.group(4))

        # Pawn moves dont have a piece declaration
        if piece_str is None:
            piece_str = 'P'

        if self.toMove == Colour.BLACK:
            piece_str = piece_str.lower()
        for i in np.transpose(np.where(self.board == pieceValues[piece_str])):
            if dest in self.legal_moves(tuple(i)):
                eligible_pieces.append(tuple(i))

        if len(eligible_pieces) > 1:
            if dis_rank is not None:
                eligible_pieces[:] = [x for x in eligible_pieces if x[0] == dis_rank]
            if dis_file is not None:
                eligible_pieces[:] = [x for x in eligible_pieces if x[1] == dis_file]

        if len(eligible_pieces) == 0:
            raise ChessException(f'Illegal move: {notation}')
        if len(eligible_pieces) > 1:
            raise ChessException(f'Ambiguous move: {notation}')

        return self.move(eligible_pieces[0], dest)

    def _push_move(self, start: tuple, end: tuple, p, promote_to: Piece = Piece.QUEEN):
        """Execute a move on the board"""
        self.lastFen = self.get_fen()

        # Remove pawn if taken en passant
        if p[0] == Piece.PAWN and end == self.enPassantTarget:
            self.board[start[0], self.enPassantTarget[1]] = 0

        # Place rook when castling
        if p[0] == Piece.KING and end[1] - start[1] == 2:
            self.board[(start[0], start[1] + 1)] = self.board[(start[0], 7)]
            self.board[(start[0], 7)] = 0
        if p[0] == Piece.KING and end[1] - start[1] == -2:
            self.board[(start[0], start[1] - 1)] = self.board[(start[0], 0)]
            self.board[(start[0], 0)] = 0

        self.board[end] = self.board[start]
        self.board[start] = 0

        # Promote Pawn if at the end of the board
        if p[0] == Piece.PAWN and end[0] in (0, 7):
            self.board[end] = self.piece_to_val(promote_to, p[1])

    def _pop_move(self):
        """Revert the last modification to the board"""
        self.set_fen(self.lastFen)

    def _reachable_fields(self, coordinate: tuple):
        fields = []
        p = self.val_to_piece(self.board[coordinate])
        if not p:
            return fields

        if p[0] == Piece.PAWN:
            return self._pawn_fields(coordinate, p[1])
        elif p[0] == Piece.KNIGHT:
            return self._knight_fields(coordinate, p[1])
        elif p[0] == Piece.BISHOP:
            return self._bishop_fields(coordinate, p[1])
        elif p[0] == Piece.ROOK:
            return self._rook_fields(coordinate, p[1])
        elif p[0] == Piece.QUEEN:
            fields = self._bishop_fields(coordinate, p[1])
            fields.extend(self._rook_fields(coordinate, p[1]))
        elif p[0] == Piece.KING:
            fields = self._king_fields(coordinate, p[1])
        return fields

    def legal_moves(self, coordinate: tuple) -> list:
        lm = []
        rf = self._reachable_fields(coordinate)
        p = self.val_to_piece(self.board[coordinate])
        if not p:
            return lm

        # add castling fields
        if p[0] == Piece.KING:
            if self.short_castle[p[1]] and \
                    self.board[(coordinate[0], coordinate[1] + 1)] == 0 and \
                    self.board[(coordinate[0], coordinate[1] + 2)] == 0:
                rf.append((coordinate[0], coordinate[1] + 2))
            if self.long_castle[p[1]] and \
                    self.board[(coordinate[0], coordinate[1] - 1)] == 0 and \
                    self.board[(coordinate[0], coordinate[1] - 2)] == 0 and \
                    self.board[(coordinate[0], coordinate[1] - 3)] == 0:
                rf.append((coordinate[0], coordinate[1] - 2))

        for f in rf:
            # temporarily execute the move
            self._push_move(coordinate, f, p)

            # if the player is in check after the move, its illegal
            if not self.in_check(p[1]):
                lm.append(f)

            # revert the move
            self._pop_move()

        # castling is not allowed through a check field
        if p[0] == Piece.KING:
            if (coordinate[0], coordinate[1] + 2) in lm and \
                    (coordinate[0], coordinate[1] + 1) not in lm:
                lm.remove((coordinate[0], coordinate[1] + 2))
            if (coordinate[0], coordinate[1] - 2) in lm and \
                    (coordinate[0], coordinate[1] - 1) not in lm:
                lm.remove((coordinate[0], coordinate[1] - 2))

        return lm

    def load_start(self):
        self.set_fen('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1')

    def set_fen(self, fen: str):
        fen_blocks = fen.strip().split(' ')
        if len(fen_blocks) != 6:
            raise ChessException('Invalid FEN')

        self.board = np.zeros((8, 8), dtype=np.uint8)

        fen_ranks = fen_blocks[0].split('/')
        rank = 0
        for r in reversed(fen_ranks):
            file = 0
            for f in r:
                try:
                    file += int(f)
                except ValueError:
                    value = pieceValues[f]
                    self.board[rank, file] = value
                    file += 1
            rank += 1

        # Set active Colour
        if fen_blocks[1] == 'w':
            self.toMove = Colour.WHITE
        elif fen_blocks[1] == 'b':
            self.toMove = Colour.BLACK

        # Castling availability
        self.short_castle[Colour.WHITE] = True if 'K' in fen_blocks[2] else False
        self.long_castle[Colour.WHITE] = True if 'Q' in fen_blocks[2] else False
        self.short_castle[Colour.BLACK] = True if 'k' in fen_blocks[2] else False
        self.long_castle[Colour.BLACK] = True if 'q' in fen_blocks[2] else False

        if fen_blocks[3] != '-':
            self.enPassantTarget = self.str_to_coor(fen_blocks[3])
        else:
            self.enPassantTarget = None

        self.halfMoveClock = int(fen_blocks[4])
        self.moveCounter = int(fen_blocks[5])

        self.moves[self._half_move_counter] = fen

    def get_fen(self) -> str:
        fen = []
        fen_ranks = []

        for rank in reversed(self.board):
            r = ''
            zeros = 0

            for square in rank:
                if square in valuePieces:
                    if zeros > 0:
                        r += str(zeros)
                        zeros = 0
                    r = r + valuePieces[square]
                else:
                    zeros += 1
            if zeros > 0:
                r += str(zeros)
            fen_ranks.append(r)

        fen.append('/'.join(fen_ranks))
        fen.append('w' if self.toMove == Colour.WHITE else 'b')

        castling_avail = ''
        if self.short_castle[Colour.WHITE]:
            castling_avail += 'K'
        if self.long_castle[Colour.WHITE]:
            castling_avail += 'Q'
        if self.short_castle[Colour.BLACK]:
            castling_avail += 'k'
        if self.long_castle[Colour.BLACK]:
            castling_avail += 'q'

        if castling_avail == '':
            castling_avail = '-'
        fen.append(castling_avail)

        fen.append('-' if self.enPassantTarget is None else self.coor_to_str(self.enPassantTarget))

        fen.append(str(self.halfMoveClock))
        fen.append(str(self.moveCounter))

        return ' '.join(fen)

    def revert_move(self):
        """Revert the last executed move"""
        if (self._half_move_counter - 1) in self.moves.keys():
            self.set_fen(self.moves[self._half_move_counter - 1])
        else:
            self.load_start()

    def get_piece(self, coordinate: tuple) -> tuple or None:
        try:
            return self.val_to_piece(self.board[coordinate])
        except IndexError:
            return None

    @property
    def _half_move_counter(self):
        if self.toMove == Colour.WHITE:
            return (self.moveCounter - 1) * 2
        else:
            return (self.moveCounter - 1) * 2 + 1

    def _repetition(self) -> bool:
        # get all fen strings without the counters
        board_state = list(map(lambda x: x.split(' ')[:3], self.moves.values()))
        current = self.moves[self._half_move_counter].split(' ')[:3]

        # if a position was repeated 3 times -> draw
        count = board_state.count(current)
        if count > 2:
            return True
        return False

    def __repr__(self) -> str:
        layout = ""
        for r in reversed(self.board):
            for f in r:
                square = '-'
                if f in valuePieces:
                    square = valuePieces[f]
                layout += square
            layout += '\n'
        return layout

    @staticmethod
    def str_to_coor(square_not: str) -> tuple:
        try:
            file = files[str.upper(square_not[0])]
            rank = ranks[square_not[1]]
        except KeyError:
            raise InvalidSquare(f'Invalid square: {square_not}')
        return rank, file

    @staticmethod
    def coor_to_str(coordinate: tuple) -> str:
        try:
            rank = [r for r, v in ranks.items() if v == coordinate[0]][0]
            file = [f for f, v in files.items() if v == coordinate[1]][0]
        except KeyError:
            raise InvalidSquare(f'Invalid coordinate: {coordinate}')
        return str(file) + str(rank)

    @staticmethod
    def val_to_piece(value: int) -> tuple or None:
        if value == 0:
            return None
        if value > 64:
            c = Colour.BLACK
        else:
            c = Colour.WHITE
        value -= c
        for k, v in Piece.__members__.items():
            if v == value:
                return v, c
        raise ChessException('Invalid piece value')

    @staticmethod
    def piece_to_val(p: Piece, c: Colour) -> int:
        return p + c

    def _pawn_fields(self, start, colour) -> list:
        fields = []
        if colour == Colour.WHITE:
            in_front = (start[0] + 1, start[1])
            in_front2 = (start[0] + 2, start[1])
            start_rank = ranks['2']
        else:
            in_front = (start[0] - 1, start[1])
            in_front2 = (start[0] - 2, start[1])
            start_rank = ranks['7']

        if self.board[in_front] == 0:
            fields.append(in_front)
            if start[0] == start_rank:
                if self.board[in_front2] == 0:
                    fields.append(in_front2)

        # Check the diagonals for opponent pieces
        diag1 = (in_front[0], in_front[1] - 1)
        diag2 = (in_front[0], in_front[1] + 1)

        if in_front[1] > 0 and self.board[diag1] > 0:
            if self.val_to_piece(self.board[diag1])[1] != colour:
                fields.append(diag1)
        if in_front[1] < 7 and self.board[diag2] > 0:
            if self.val_to_piece(self.board[diag2])[1] != colour:
                fields.append(diag2)

        # En passant
        if self.enPassantTarget in (diag1, diag2):
            fields.append(self.enPassantTarget)

        return fields

    def _knight_fields(self, start, colour) -> list:
        fields = []
        knights_move = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (-1, 2), (1, -2), (-1, -2)]

        for k in knights_move:
            tar = (start[0] + k[0], start[1] + k[1])
            if tar[0] not in ranks.values() or \
                    tar[1] not in files.values():
                continue

            if self.board[tar] > 0:
                if self.val_to_piece(self.board[tar])[1] == colour:
                    continue
            fields.append(tar)
        return fields

    def _bishop_fields(self, start, colour) -> list:
        fields = []
        direction = [lambda b: (b[0] + 1, b[1] + 1),
                     lambda b: (b[0] + 1, b[1] - 1),
                     lambda b: (b[0] - 1, b[1] + 1),
                     lambda b: (b[0] - 1, b[1] - 1)]

        for move in direction:
            cur = start
            while True:
                cur = move(cur)
                if not cur[0] in ranks.values() or \
                        not cur[1] in files.values():
                    break
                tar_val = self.board[cur]
                if tar_val > 0:
                    if self.val_to_piece(tar_val)[1] == colour:
                        break
                    else:
                        fields.append(cur)
                        break
                fields.append(cur)
        return fields

    def _rook_fields(self, start, colour) -> list:
        fields = []

        direction = [lambda b: (b[0], b[1] + 1),
                     lambda b: (b[0], b[1] - 1),
                     lambda b: (b[0] + 1, b[1]),
                     lambda b: (b[0] - 1, b[1])]

        for move in direction:
            cur = start
            while True:
                cur = move(cur)
                if not cur[0] in ranks.values() or \
                        not cur[1] in files.values():
                    break
                tar_val = self.board[cur]
                if tar_val > 0:
                    if self.val_to_piece(tar_val)[1] == colour:
                        break
                    else:
                        fields.append(cur)
                        break
                fields.append(cur)
        return fields

    def _king_fields(self, start, colour) -> list:
        fields = []
        for i in range(max(start[0] - 1, 0), min(start[0] + 2, 8)):
            for j in range(max(start[1] - 1, 0), min(start[1] + 2, 8)):
                tar_val = self.board[i, j]
                if tar_val > 0:
                    if self.val_to_piece(tar_val)[1] == colour:
                        continue
                fields.append(tuple([i, j]))
        return fields

    def _get_pieces_by_colour(self, colour: Colour) -> list:
        return [tuple(i) for i in
                np.transpose(
                    np.where(
                        np.logical_and(self.board > colour,
                                       self.board < colour + 64)))]

    def in_check(self, colour) -> bool:
        # find the kings square
        king_coor = tuple(i[0] for i in np.where(self.board == Piece.KING + colour))

        # find all pieces of opposite colour
        for c in self._get_pieces_by_colour(colour.opposite()):
            # if the king can be taken by any piece, the move is illegal
            if king_coor in self._reachable_fields(c):
                return True
        return False
