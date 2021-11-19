from enum import IntFlag

import numpy as np


class ChessException(Exception):
    pass


class NotYourTurn(ChessException):
    """The other players move"""


class NoPiecePresent(ChessException):
    """The selected square is empty"""


class IllegalMove(ChessException):
    """The given move is illegal"""""


class InvalidSquare(ChessException):
    """The square is out of the boundaries of the chess board"""


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

bPieces = dict()
for x, y in pieceValues.items():
    bPieces[str.lower(x)] = y + Colour.BLACK
pieceValues.update(bPieces)

# reverse version of the pieces dict
valuePieces = {v: k for k, v in pieceValues.items()}


class Chess:
    board = np.zeros((8, 8), dtype=np.uint8)
    toMove = Colour.WHITE
    enPassantTarget = None
    lastFen = ''
    blackCastle = True
    whiteCastle = True
    check = False

    def move(self, start_not: str, end_not: str):
        start = self.str_to_coor(start_not)
        end = self.str_to_coor(end_not)

        p = self.val_to_piece(self.board[start])

        if not p:
            raise NoPiecePresent('No piece present')

        if p[1] != self.toMove:
            raise NotYourTurn('{colour} to move'.format(colour='White' if self.toMove == Colour.WHITE else 'Black'))

        if end_not not in self.legal_moves(start_not):
            raise IllegalMove('Illegal move')

        self._push_move(start, end, p)

        # Clear possible en passant target, and add new one
        self.enPassantTarget = None
        if p[0] == Piece.PAWN and abs(end[0] - start[0]) == 2:
            self.enPassantTarget = end

        # end move
        if self.toMove == Colour.BLACK:
            self.toMove = Colour.WHITE
        else:
            self.toMove = Colour.BLACK

        if self.in_check(self.toMove):
            self.check = True

    def _push_move(self, start: tuple, end: tuple, p):
        self.lastFen = self.get_fen()

        # Remove pawn if taken en passant
        if self.board[end] == 0 and p[0] == Piece.PAWN and end[1] != start[1]:
            self.board[self.enPassantTarget] = 0

        self.board[end] = self.board[start]
        self.board[start] = 0

    def _pop_move(self):
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

    def legal_moves(self, square_not: str):
        lm = []
        coordinate = self.str_to_coor(square_not)
        rf = self._reachable_fields(coordinate)
        p = self.val_to_piece(self.board[coordinate])
        if not p:
            return lm

        for f in rf:
            # temporarily execute the move
            self._push_move(coordinate, f, p)

            # if the player is in check after the move, its illegal
            if not self.in_check(p[1]):
                lm.append(f)

            # revert the move
            self._pop_move()

        return [self.coor_to_str(i) for i in lm]

    def load_start(self):
        self.set_fen('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR')

    def set_fen(self, fen: str):
        self.board = np.zeros((8, 8), dtype=np.uint8)

        fen_ranks = fen.split('/')
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

    def get_fen(self) -> str:
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

        return '/'.join(fen_ranks)

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
            file = files[square_not[0]]
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
    def val_to_piece(value: int) -> tuple:
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
        if (start[0], start[1] + 1) == self.enPassantTarget:
            fields.append((in_front[0], start[1] + 1))
        if (start[0], start[1] - 1) == self.enPassantTarget:
            fields.append(tuple([in_front[0], start[1] - 1]))

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
        for i in range(start[0] - 1, start[0] + 1):
            for j in range(start[1] - 1, start[1] + 1):
                tar_val = self.board[i, j]
                if tar_val > 0:
                    if self.val_to_piece(tar_val)[1] == colour:
                        continue
                fields.append(tuple([i, j]))
        return fields

    def in_check(self, colour) -> bool:
        # find the kings square
        king_coor = tuple(i[0] for i in np.where(self.board == Piece.KING + colour))

        # find all pieces of opposite colour
        for c in [tuple(i) for i in
                  np.transpose(
                      np.where(np.logical_and(abs(colour - 64) < self.board, self.board < abs(colour - 64) + 64)))]:
            # if the king can be taken by any piece, the move is illegal
            if king_coor in self._reachable_fields(c):
                return True
        return False
