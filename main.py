from chess import Chess

if __name__ == '__main__':
    c = Chess()
    c.load_start()
    print(c)
    c.move(c.str_to_coor('E2'), c.str_to_coor('E4'))
    c.move(c.str_to_coor('E7'), c.str_to_coor('E5'))
    c.move(c.str_to_coor('F2'), c.str_to_coor('F4'))
    c.move(c.str_to_coor('F7'), c.str_to_coor('F6'))
    c.move(c.str_to_coor('G1'), c.str_to_coor('F3'))
    c.move(c.str_to_coor('A7'), c.str_to_coor('A5'))
    c.move(c.str_to_coor('A2'), c.str_to_coor('A3'))
    c.move(c.str_to_coor('A5'), c.str_to_coor('A4'))
    c.move(c.str_to_coor('B2'), c.str_to_coor('B4'))

    print(c)
    while True:
        print('Type move or figure')
        txt = input()
        fields = txt.split(' ')
        if len(fields) > 1:
            c.move(c.str_to_coor(fields[0]), c.str_to_coor(fields[1]))
            print(c)
        else:
            print('moves:')
            print(map(c.coor_to_str, c.legal_moves(c.str_to_coor(txt))))
