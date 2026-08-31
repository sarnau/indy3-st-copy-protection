#!/usr/bin/env python3
"""Disable the Translation Table check in Indiana Jones and the Last Crusade
(Atari ST, SCUMM v3).  Edits 92.LFL in place inside a raw 720 KB .st image.

Two modes:

  skip    (default)  Remove the test completely.  Room 92 never starts the
                     protection driver, so there is no prompt and no symbol
                     entry; the scene reports "done, passed" the moment it
                     loads.  2 edits.

  accept             Keep the scene, accept any four symbols.  The verdict
                     branch is redirected through the arm that clears the
                     failure flag and then falls into the success arm.
                     4 edits (the loop is stored twice in the file).

Both clear the failure flag, which matters: room 76 tests it after the scene
and Marcus says either "Good work, Indy!" or "I'm disappointed in you!".

Usage:  python3 patch_protection.py disk1.st [skip|accept]
"""
import struct, sys, shutil

# (offset in decoded 92.LFL, expected bytes, replacement)
SKIP = [
    (14521, bytes([0x0A, 0xCA, 0xFF]),             bytes([0x18, 0x00, 0x00])),
    (14529, bytes([0x1A, 0x39, 0x00, 0x00, 0x00]), bytes([0x1A, 0x39, 0x00, 0x01, 0x00])),
]
ACCEPT = []
for _base in (0, 1015):                       # the verify loop appears twice
    ACCEPT += [
        (15155 + _base, bytes([0xA8, 0xE4, 0x85]), bytes([0x18, 0x1B, 0x00])),
        (15195 + _base, bytes([0x18, 0x05, 0x00]), bytes([0x18, 0x00, 0x00])),
    ]

def locate(img, name=b'92      LFL'):
    bps, spc = struct.unpack_from('<HB', img, 11)
    res = struct.unpack_from('<H', img, 14)[0]; nfat = img[16]
    ndir = struct.unpack_from('<H', img, 17)[0]; spf = struct.unpack_from('<H', img, 22)[0]
    root = res + nfat * spf
    data = root + (ndir * 32 + bps - 1) // bps
    fat = img[res*bps:(res+spf)*bps]
    def nxt(c):
        o = c * 3 // 2; v = fat[o] | (fat[o+1] << 8)
        return (v >> 4) if c & 1 else (v & 0xFFF)
    for i in range(ndir):
        e = img[root*bps + i*32: root*bps + i*32 + 32]
        if e[0:11] == name:
            cl = struct.unpack_from('<H', e, 26)[0]
            chain = []
            while 2 <= cl < 0xFFF0 and cl < 0xFF0:
                chain.append(cl); cl = nxt(cl)
            return chain, data, spc, bps
    raise SystemExit('92.LFL not found - is this disk 1?')

def main(path, mode):
    edits = {'skip': SKIP, 'accept': ACCEPT}[mode]
    shutil.copy(path, path + '.bak')
    img = bytearray(open(path, 'rb').read())
    chain, data, spc, bps = locate(img)
    cl = spc * bps
    to_image = lambda off: (data + (chain[off // cl] - 2) * spc) * bps + off % cl
    done = skipped = 0
    for off, want, new in edits:
        io = to_image(off)
        cur = bytes(b ^ 0xFF for b in img[io:io+len(want)])   # .LFL is XOR 0xFF on disk
        if cur == new:
            print(f'  {off}: already patched'); continue
        if cur != want:
            print(f'  {off}: expected {want.hex(" ")}, found {cur.hex(" ")} - SKIPPED')
            skipped += 1; continue
        img[io:io+len(new)] = bytes(b ^ 0xFF for b in new)
        print(f'  {off} (image 0x{io:X}): {cur.hex(" ")} -> {new.hex(" ")}')
        done += 1
    open(path, 'wb').write(bytes(img))
    print(f"mode '{mode}': {done} edit(s) applied"
          + (f', {skipped} skipped' if skipped else '')
          + f'. Original saved as {path}.bak')

if __name__ == '__main__':
    if not 2 <= len(sys.argv) <= 3: raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else 'skip')
