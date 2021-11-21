import math
import tkinter as tk
from PIL import Image, ImageTk
from chess import *
import speech_recognition as sr

numbers = dict()
numbers[1] = 'one'
numbers[2] = 'two'
numbers[3] = 'three'
numbers[4] = 'four'
numbers[5] = 'five'
numbers[6] = 'six'
numbers[7] = 'seven'
numbers[8] = 'eight'

letters = dict()
letters['a'] = 'alpha'
letters['b'] = 'bravo'
letters['c'] = 'charlie'
letters['d'] = 'delta'
letters['e'] = 'echo'
letters['f'] = 'foxtrot'
letters['g'] = 'golf'
letters['h'] = 'hotel'


class BoardGui(tk.Frame):
    chess: Chess = None
    selected_piece = None

    r = sr.Recognizer()

    piece_img = {}

    rows = 8
    columns = 8

    def __init__(self, parent, board, square_size=64):
        self.square_size = square_size
        self.parent = parent
        self.chess = board

        canvas_width = self.columns * square_size
        canvas_height = self.rows * square_size

        tk.Frame.__init__(self, parent)
        self.canvas = tk.Canvas(self, width=canvas_width, height=canvas_height, background='grey')
        self.canvas.pack(side='top', fill='both', anchor='c', expand=True)

        self.board_layout = ImageTk.PhotoImage(Image.open('img/board.png').resize((canvas_width, canvas_height)))
        self.canvas.create_image(1, 1, image=self.board_layout, tags='board', anchor='nw')

        self.canvas.bind('<Button-1>', self.click)

        self.control_bar = tk.Frame(self, height=64)

        self.btn_reset = tk.Button(self.control_bar, text='Reset', fg='black', command=self.reset)
        self.btn_reset.pack(side=tk.LEFT, in_=self.control_bar)

        self.btn_dictate = tk.Button(self.control_bar, text='Dictate', fg='black', command=self.dictate_move)
        self.btn_dictate.pack(side=tk.LEFT, in_=self.control_bar)

        self.label_message = tk.Label(self.control_bar, text='Hi!', fg='black')
        self.label_message.pack(side=tk.LEFT, expand=0, in_=self.control_bar)

        self.button_quit = tk.Button(self.control_bar, text='Quit', fg='black', command=self.parent.destroy)
        self.button_quit.pack(side=tk.RIGHT, in_=self.control_bar)

        self.control_bar.pack(expand=False, fill='x', side='bottom')

        for p in pieceValues:
            colour = 'white' if p.isupper() else 'black'
            self.piece_img[p] = ImageTk.PhotoImage(
                Image.open(f'img/{p}_{colour}.png').resize((square_size - 4, square_size - 4)))

        self.reset()

    def click(self, event):
        col = math.floor(event.x / self.square_size)
        row = math.floor(8 - (event.y / self.square_size))
        clicked = tuple([row, col])

        self.canvas.delete('move')

        if self.chess.get_piece(clicked) is not None and \
                self.chess.get_piece(clicked)[1] == self.chess.toMove:
            self.selected_piece = clicked
            self.draw_moves(self.chess.legal_moves(clicked))
        elif self.selected_piece:
            self.exec_move(self.selected_piece, clicked)

    def dictate_move(self):
        text = ''
        try:
            self.update_label('Listening...')
            with sr.Microphone() as source:
                audio = self.r.listen(source, timeout=5, phrase_time_limit=8)
            self.update_label('Processing...')
            text = ''.join(self.r.recognize_google(audio)).lower()

            # remove spaces, replace non-numeric numbers and nato letters
            for n, ns in numbers.items():
                text = text.replace(ns, str(n))

            for letter, nato in letters.items():
                text = text.replace(nato, letter)

            text_trimmed = text.replace(' ', '')

            if len(text_trimmed) < 4:
                raise InvalidSquare
            else:
                start = self.chess.str_to_coor(text_trimmed[0:2])
                end = self.chess.str_to_coor(text_trimmed[2:4])
                self.exec_move(start, end)
        except InvalidSquare:
            self.update_label(f'Move not recognized: "{text}"')
        except sr.UnknownValueError or sr.WaitTimeoutError:
            self.update_label("Could not understand audio")
        except sr.RequestError as e:
            self.update_label("Could not request results from Google Speech Recognition service; {0}".format(e))

    def exec_move(self, start, end):
        try:
            self.chess.move(start, end)

            # indicate last move
            self.canvas.delete('last_move')
            self.colour_square(start, 'yellow2', 'last_move')
            self.colour_square(end, 'yellow3', 'last_move')

            self.update_label('White to move' if self.chess.toMove == Colour.WHITE else 'Black to move')
        except IllegalMove as e:
            self.update_label(str(e))
        except ChessException as e:
            self.update_label(str(e))

        self.selected_piece = None
        self.draw_pieces()

    def draw_pieces(self):
        self.canvas.delete('piece')
        for ri, r in enumerate(self.chess.board):
            for fi, f in enumerate(r):
                if f == 0:
                    continue
                piece_tag = f'{valuePieces[f]}{fi}{ri}'

                center = self.coor_to_square_center((ri, fi))
                self.canvas.create_image(center[0], center[1], image=self.piece_img[valuePieces[f]],
                                         tags=(piece_tag, 'piece'),
                                         anchor='c')

    def draw_moves(self, coors):
        w = self.square_size / 10
        for c in map(self.coor_to_square_center, coors):
            self.canvas.create_oval(c[0] - w, c[1] - w, c[0] + w, c[1] + w, fill='yellow green', outline='yellow green',
                                    tags='move')

    def colour_square(self, coor, colour, tag):
        x0 = coor[1] * self.square_size + 1
        y0 = ((7 - coor[0]) * self.square_size) + self.square_size - 1
        x1 = ((coor[1] + 1) * self.square_size) - 1
        y1 = (7 - coor[0]) * self.square_size + 1
        self.canvas.create_rectangle(x0, y0, x1, y1, fill=colour, outline=colour, tags=tag)

    def reset(self):
        self.canvas.delete('last_move')
        self.chess.load_start()
        self.update_label('White to move')
        self.draw_pieces()

    def coor_to_square_center(self, coor) -> tuple:
        x = (coor[1] * self.square_size) + int(self.square_size / 2)
        y = (7 - coor[0]) * self.square_size + int(self.square_size / 2)
        return x, y

    def update_label(self, text: str):
        self.label_message.config(text=text)
        self.label_message.update()


def display(chessboard):
    root = tk.Tk()
    root.title('Chess')

    gui = BoardGui(root, chessboard)
    gui.pack(side='top', fill='both', expand='true', padx=4, pady=4)
    gui.draw_pieces()

    # root.resizable(0,0)
    root.mainloop()


if __name__ == '__main__':
    b = Chess()
    display(b)
