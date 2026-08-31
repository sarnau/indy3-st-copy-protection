def answers(row, col, sec):
    """row=VAR103 1..26 (letter A..Z), col=VAR104 1..7, sec=VAR105 1..4.
    Returns the 4 expected symbol numbers in entry order (VAR99,VAR100,VAR101,VAR102)."""
    v103, v104, v105 = row, col, sec
    l0, l1 = v104, v105
    while True:                       # l0 = col + 17*sec
        l0 += 17; l1 -= 1
        if l1 == 0: break
    l0 += v103
    l0 += v103
    if v104 >= 3: l0 -= 2
    l0 += v103
    if v103 < 5:  l0 += 3
    l0 += 12
    while True:
        l0 -= 9
        if l0 < 12: break
    v101 = l0

    l0 += v104; l0 += v103; l0 += 19
    if v103 > 7: l0 -= 5
    l0 += 7
    while True:
        l0 -= 7
        if l0 < 8: break
    l0 += 19
    if l0 <= v101: l0 += v101
    while True:
        l0 -= 12
        if l0 <= 11: break
    v102 = l0

    l0 += v104; l0 += v104; l0 += v104; l0 += v103; l0 += 14
    if v103 < 10: l0 += v103
    while True:
        l0 -= 5
        if l0 < 10: break
    if l0 != v102: l0 += v101
    l0 += 23
    while True:
        l0 -= 12
        if l0 < 12: break
    v100 = l0

    l0 += v104; l0 += v104; l0 += v104; l0 += v103; l0 += 13
    if v104 > 7: l0 += 6           # dead: col never exceeds 7
    while True:
        l0 -= 8
        if l0 < 17: break
    if l0 > v100: l0 += v102
    l0 += 14
    while True:
        l0 -= 12
        if l0 <= 11: break
    v99 = l0
    return v99, v100, v101, v102

if __name__ == '__main__':
    vals = {i: set() for i in range(4)}
    for s in range(1, 5):
        for r in range(1, 27):
            for c in range(1, 8):
                a = answers(r, c, s)
                for i, v in enumerate(a): vals[i].add(v)
    print('cells:', 4*26*7)
    for i, nm in enumerate(('VAR99 (1st)','VAR100 (2nd)','VAR101 (3rd)','VAR102 (4th)')):
        print(f'  {nm:<14} range {min(vals[i])}..{max(vals[i])}  distinct={len(vals[i])}')
    print()
    print('Section 1, rows A-F:')
    print('      ' + ''.join(f'col{c:<6}' for c in range(1,8)))
    for r in range(1, 7):
        cells = []
        for c in range(1, 8):
            cells.append('-'.join(f'{v:2d}' for v in answers(r, c, 1)))
        print(f'   {chr(64+r)}  ' + '  '.join(cells))
