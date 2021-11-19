from chess import Chess

if __name__ == '__main__':
    c = Chess()
    c.load_start()
    print(c)
    c.move('E2', 'E4')
    c.move('E7', 'E5')
    c.move('F2', 'F4')
    c.move('F7', 'F6')
    c.move('G1', 'F3')
    c.move('A7', 'A5')
    c.move('A2', 'A3')
    c.move('A5', 'A4')
    c.move('B2', 'B4')

    print(c)
    while True:
        print('Type move or figure')
        txt = input()
        fields = txt.split(' ')
        if len(fields) > 1:
            c.move(fields[0], fields[1])
            print(c)
        else:
            print('moves:')
            print(c.legal_moves(txt))
