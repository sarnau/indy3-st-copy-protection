# -*- coding: utf-8 -*-
"""SCUMM v3 (indy3 / Atari ST) script disassembler."""
import sys

class Dis:
    def __init__(self, d):
        self.d = d
        self.ip = 0
        self.op = 0
        self.unknown = False

    def b(self):
        v = self.d[self.ip]; self.ip += 1; return v
    def w(self):
        v = self.d[self.ip] | (self.d[self.ip+1] << 8); self.ip += 2; return v
    def sw(self):
        v = self.w()
        return v - 0x10000 if v & 0x8000 else v

    # ---- variable reference (handles 0x2000 indirect word) ----
    def varref(self):
        v = self.w()
        extra = ''
        if v & 0x2000:
            a = self.w()
            v &= ~0x2000
            extra = '+[%s]' % (self.vname(a & ~0x2000) if (a & 0x2000) else str(a & 0xFFF))
        return self.vname(v) + extra
    def vname(self, v):
        if v & 0x8000: return 'bit%d' % (v & 0x7FFF)
        if v & 0x4000: return 'local%d' % (v & 0xFFF)
        return 'VAR%d' % v

    def vod_b(self, mask):   # getVarOrDirectByte
        return self.varref() if (self.op & mask) else str(self.b())
    def vod_w(self, mask):   # getVarOrDirectWord
        return self.varref() if (self.op & mask) else str(self.sw())

    def jmp(self):
        o = self.sw()
        return 'goto %04X' % (self.ip + o)

    def args(self):          # 0xFF-terminated word vararg list
        out = []
        while True:
            self.op = self.b()
            if self.op == 0xFF: break
            out.append(self.vod_w(0x80))
        return '[' + ','.join(out) + ']'

    def string(self):
        out = []
        while True:
            c = self.b()
            if c == 0: break
            if c == 0xFF or c == 0xFE:
                k = self.b()
                if k == 1: out.append('\\n')
                elif k == 2: out.append('\\keep')
                elif k == 3: out.append('\\wait')
                elif k == 8: out.append('\\8')
                else:
                    a = self.w()
                    out.append('\\%d(%d)' % (k, a))
            elif 32 <= c < 127: out.append(chr(c))
            else: out.append({0x82:'é',0x85:'à',0x87:'ç',0x8a:'è',0x8e:'Ä',0x94:'ö',
                              0x88:'ê',0x89:'ë',0x93:'ô',0x97:'ù',0x96:'û',0x81:'ü',
                              0x84:'ä',0x86:'å'}.get(c, '<%02X>' % c))
        return '"' + ''.join(out) + '"'

    def parsestring(self):
        out = []
        while True:
            self.op = self.b()
            k = self.op & 0x0F
            if k == 0:   out.append('pos(%s,%s)' % (self.vod_w(0x80), self.vod_w(0x40)))
            elif k == 1: out.append('color(%s)' % self.vod_b(0x80))
            elif k == 2: out.append('clipped(%s)' % self.vod_w(0x80))
            elif k == 3: out.append('restore(%s,%s)' % (self.vod_w(0x80), self.vod_w(0x40)))
            elif k == 4: out.append('center')
            elif k == 6: out.append('left')
            elif k == 7: out.append('overhead')
            elif k == 8: out.append('cd(%s,%s)' % (self.vod_w(0x80), self.vod_w(0x40)))
            elif k == 15:
                out.append('text=' + self.string()); break
            else:
                out.append('?sub%02X' % self.op); break
        return ' '.join(out)

    def actorops(self):
        out = []
        while True:
            self.op = self.b()
            if self.op == 0xFF: break
            k = self.op & 0x1F
            if   k == 0:  out.append('unk0(%s)' % self.vod_b(0x80))
            elif k == 1:  out.append('costume(%s)' % self.vod_b(0x80))
            elif k == 2:  out.append('walkspeed(%s,%s)' % (self.vod_b(0x80), self.vod_b(0x40)))
            elif k == 3:  out.append('sound(%s)' % self.vod_b(0x80))
            elif k == 4:  out.append('walkanim(%s)' % self.vod_b(0x80))
            elif k == 5:  out.append('talkanim(%s,%s)' % (self.vod_b(0x80), self.vod_b(0x40)))
            elif k == 6:  out.append('standanim(%s)' % self.vod_b(0x80))
            elif k == 7:  out.append('anim(%s,%s,%s)' % (self.vod_b(0x80), self.vod_b(0x40), self.vod_b(0x20)))
            elif k == 8:  out.append('init')
            elif k == 9:  out.append('elevation(%s)' % self.vod_w(0x80))
            elif k == 10: out.append('defaultanims')
            elif k == 11: out.append('palette(%s,%s)' % (self.vod_b(0x80), self.vod_b(0x40)))
            elif k == 12: out.append('talkcolor(%s)' % self.vod_b(0x80))
            elif k == 13: out.append('name=' + self.string())
            elif k == 14: out.append('initanim(%s)' % self.vod_b(0x80))
            elif k == 16: out.append('width(%s)' % self.vod_b(0x80))
            elif k == 17: out.append('scale(%s)' % self.vod_b(0x80))
            elif k == 18: out.append('neverZClip')
            elif k == 19: out.append('setZClip(%s)' % self.vod_b(0x80))
            elif k == 20: out.append('ignoreBoxes')
            elif k == 21: out.append('followBoxes')
            elif k == 22: out.append('animSpeed(%s)' % self.vod_b(0x80))
            elif k == 23: out.append('shadow(%s)' % self.vod_b(0x80))
            else: out.append('?ao%02X' % self.op); self.unknown = True; break
        return ' '.join(out)

    def verbops(self):
        out = []
        while True:
            self.op = self.b()
            if self.op == 0xFF: break
            k = self.op & 0x1F
            if   k == 1:  out.append('image(%s)' % self.vod_w(0x80))
            elif k == 2:  out.append('name=' + self.string())
            elif k == 3:  out.append('color(%s)' % self.vod_b(0x80))
            elif k == 4:  out.append('hicolor(%s)' % self.vod_b(0x80))
            elif k == 5:  out.append('at(%s,%s)' % (self.vod_w(0x80), self.vod_w(0x40)))
            elif k == 6:  out.append('on')
            elif k == 7:  out.append('off')
            elif k == 8:  out.append('delete')
            elif k == 9:  out.append('new')
            elif k == 16: out.append('dimcolor(%s)' % self.vod_b(0x80))
            elif k == 17: out.append('dim')
            elif k == 18: out.append('key(%s)' % self.vod_b(0x80))
            elif k == 19: out.append('center')
            elif k == 20: out.append('setToString(%s)' % self.vod_w(0x80))
            elif k == 22: out.append('setToObject(%s,%s)' % (self.vod_w(0x80), self.vod_b(0x40)))
            elif k == 23: out.append('backcolor(%s)' % self.vod_b(0x80))
            else: out.append('?vo%02X' % self.op); self.unknown = True; break
        return ' '.join(out)

    def expression(self):
        dst = self.varref(); out = []
        while True:
            self.op = self.b()
            if self.op == 0xFF: break
            k = self.op & 0x1F
            if   k == 1: out.append(self.vod_w(0x80))
            elif k == 2: out.append('+')
            elif k == 3: out.append('-')
            elif k == 4: out.append('*')
            elif k == 5: out.append('/')
            elif k == 6:
                save = self.ip
                inner = self.one()
                out.append('{' + inner + '}')
            else: out.append('?ex%02X' % self.op); self.unknown = True; break
        return '%s = expr( %s )' % (dst, ' '.join(out))

    def one(self):
        self.op = self.b()
        o = self.op
        lo = o & 0x1F
        # --- comparisons: var, value, jump ---
        cmpname = {0x04:'<=',0x44:'>',0x08:'!=',0x38:'>=',0x78:'<',0x48:'=='}  # SCUMM tests 'b OP var'
        base = o & 0x7F
        if base in cmpname:
            v = self.varref(); val = self.vod_w(0x80)
            return 'if (%s %s %s) ; else %s' % (v, cmpname[base], val, self.jmp())
        if base == 0x28:
            v = self.varref()
            return 'if (%s == 0) ; else %s' % (v, self.jmp()) if o == 0x28 else \
                   'if (%s != 0) ; else %s' % (v, self.jmp())
        if o == 0xa8:
            v = self.varref(); return 'if (%s != 0) ; else %s' % (v, self.jmp())
        if o in (0x00, 0xa0): return 'stopObjectCode'
        if o == 0x80: return 'breakHere'
        if o == 0x18: return self.jmp()
        if lo == 0x01 and o in (0x01,0x21,0x41,0x61,0x81,0xa1,0xc1,0xe1):
            return 'putActor(%s, %s, %s)' % (self.vod_b(0x80), self.vod_w(0x40), self.vod_w(0x20))
        if o in (0x02,0x82): return 'startMusic(%s)' % self.vod_b(0x80)
        if o in (0x20,): return 'stopMusic'
        if o in (0x03,0x83): return '%s = getActorRoom(%s)' % (self.varref(), self.vod_b(0x80))
        if o in (0x07,0x47,0x87,0xc7): return 'setState(%s, %s)' % (self.vod_w(0x80), self.vod_b(0x40))
        if o in (0x09,0x49,0x89,0xc9): return 'faceActor(%s, %s)' % (self.vod_b(0x80), self.vod_w(0x40))
        if o in (0x0a,0x2a,0x4a,0x6a,0x8a,0xaa,0xca,0xea):
            return 'startScript(%s, %s)' % (self.vod_b(0x80), self.args())
        if o in (0x0b,0x4b,0x8b,0xcb):
            return '%s = getVerbEntrypoint(%s, %s)' % (self.varref(), self.vod_w(0x80), self.vod_w(0x40))
        if o in (0x0c,0x8c):
            self.op = self.b(); k = self.op & 0x1F
            nm = {1:'load',2:'load',3:'lock',4:'unlock',5:'nuke'}.get(k, 'res%d' % k)
            if k in (9,10,11,12,13,14): return 'resourceRoutine(%d)' % k
            return 'resource.%s(%s)' % (nm, self.vod_b(0x80))
        if o in (0x11,0x51,0x91,0xd1): return 'animateActor(%s, %s)' % (self.vod_b(0x80), self.vod_b(0x40))
        if o in (0x13,0x53,0x93,0xd3): return 'actorOps(%s): %s' % (self.vod_b(0x80), self.actorops())
        if o in (0x14,0x94): return 'print(%s): %s' % (self.vod_b(0x80), self.parsestring())
        if o == 0xd8: return 'printEgo: %s' % self.parsestring()
        if o in (0x16,0x96): return '%s = getRandomNr(%s)' % (self.varref(), self.vod_b(0x80))
        if o in (0x17,0x97): return '%s &= %s' % (self.varref(), self.vod_w(0x80))
        if o in (0x57,0xd7): return '%s |= %s' % (self.varref(), self.vod_w(0x80))
        if o in (0x1a,0x9a): return '%s = %s' % (self.varref(), self.vod_w(0x80))
        if o in (0x1b,0x9b): return '%s *= %s' % (self.varref(), self.vod_w(0x80))
        if o in (0x3a,0xba): return '%s -= %s' % (self.varref(), self.vod_w(0x80))
        if o in (0x5a,0xda): return '%s += %s' % (self.varref(), self.vod_w(0x80))
        if o in (0x5b,0xdb): return '%s /= %s' % (self.varref(), self.vod_w(0x80))
        if o in (0x1c,0x9c): return 'startSound(%s)' % self.vod_b(0x80)
        if o in (0x3c,0xbc): return 'stopSound(%s)' % self.vod_b(0x80)
        if o in (0x1e,0x3e,0x5e,0x7e,0x9e,0xbe,0xde,0xfe):
            return 'walkActorTo(%s, %s, %s)' % (self.vod_b(0x80), self.vod_w(0x40), self.vod_w(0x20))
        if o in (0x26,0xa6):
            v = self.varref(); n = self.b(); vals = []
            for _ in range(n):
                vals.append(str(self.sw() if (o & 0x80) else self.b()))
            return 'setVarRange(%s, %d, [%s])' % (v, n, ','.join(vals))
        if o in (0x46,): return '%s++' % self.varref()
        if o in (0xc6,): return '%s--' % self.varref()
        if o in (0x2c,):
            self.op = self.b(); k = self.op & 0x1F
            if k in (1,2,3,4,5,6,7,8,9,10): return 'cursorCommand(%d)' % k
            if k == 11: return 'cursor.image(%s,%s,%s)' % (self.vod_b(0x80), self.vod_b(0x40), self.vod_b(0x20))
            if k in (12,13): return 'cursor.%d(%s)' % (k, self.vod_b(0x80))
            if k == 14: return 'charsetColors(%s)' % self.args()
            self.unknown = True; return '?cursor%02X' % self.op
        if o in (0x2e,):
            a = self.b() | (self.b() << 8) | (self.b() << 16); return 'delay(%d)' % a
        if o in (0x33,0x73,0xb3,0xf3):
            a = self.vod_w(0x80); b_ = self.vod_w(0x40)
            self.op = self.b(); k = self.op & 0x1F
            return 'roomOps(%s, %s).%d' % (a, b_, k)
        if o in (0x37,0x77,0xb7,0xf7):
            return 'startObject(%s, %s, %s)' % (self.vod_w(0x80), self.vod_b(0x40), self.args())
        if o in (0x40,): return 'cutscene %s' % self.args()
        if o in (0xc0,): return 'endCutscene'
        if o in (0x60,0xe0): return 'freezeScripts(%s)' % self.vod_b(0x80)
        if o in (0x62,0xe2): return 'stopScript(%s)' % self.vod_b(0x80)
        if o in (0x68,0xe8): return '%s = isScriptRunning(%s)' % (self.varref(), self.vod_b(0x80))
        if o in (0x6b,0xeb): return 'debug(%s)' % self.vod_w(0x80)
        if o in (0x70,0xf0): return 'lights(%s, %d, %d)' % (self.vod_b(0x80), self.b(), self.b())
        if o in (0x72,0xf2): return 'loadRoom(%s)' % self.vod_b(0x80)
        if o in (0x7a,0xfa): return 'verbOps(%s): %s' % (self.vod_b(0x80), self.verbops())
        if o in (0xac,): return self.expression()
        if o in (0x2d,0x6d,0xad,0xed): return 'putActorInRoom(%s, %s)' % (self.vod_b(0x80), self.vod_b(0x40))
        if o in (0x5d,0xdd): return 'setClass(%s, %s)' % (self.vod_w(0x80), self.args())
        if o in (0x1d,0x9d): return 'if classOfIs(%s, %s) ; else %s' % (self.vod_w(0x80), self.args(), self.jmp())
        if o in (0x0f,0x8f): return '%s = getObjectState(%s)' % (self.varref(), self.vod_w(0x80))
        if o in (0x10,0x90): return '%s = getObjectOwner(%s)' % (self.varref(), self.vod_w(0x80))
        if o in (0x29,0x69,0xa9,0xe9): return 'setOwnerOf(%s, %s)' % (self.vod_w(0x80), self.vod_b(0x40))
        if o in (0x31,0xb1): return '%s = getInventoryCount(%s)' % (self.varref(), self.vod_b(0x80))
        if o in (0x35,0x75,0xb5,0xf5): return '%s = findObject(%s, %s)' % (self.varref(), self.vod_b(0x80), self.vod_b(0x40))
        if o in (0x3d,0x7d,0xbd,0xfd): return '%s = findInventory(%s, %s)' % (self.varref(), self.vod_b(0x80), self.vod_b(0x40))
        if o in (0x05,0x45,0x85,0xc5): return 'drawObject(%s, %s, %s)' % (self.vod_w(0x80), self.vod_w(0x40), self.vod_w(0x20))
        if o in (0x25,0x65,0xa5,0xe5): return 'pickupObject(%s)' % self.vod_w(0x80)
        if o in (0x2f,0x6f,0xaf,0xef): return 'if state(%s)==%s ; else %s' % (self.vod_w(0x80), self.vod_b(0x40), self.jmp())
        if o in (0x22,0xa2): return 'saveLoadGame(%s)' % self.vod_b(0x80)
        if o in (0x98,): return 'systemOps(%d)' % self.b()
        if o in (0xae,): return 'waitForMessage'   # v3: standalone, no subopcode
        if o in (0xcc,):
            out=[self.b()]
            while True:
                v=self.b()
                if v==0: break
                out.append(v)
            return 'pseudoRoom(%s)' % out
        if o in (0x0d,0x4d,0x8d,0xcd): return 'walkActorToActor(%s, %s, %d)' % (self.vod_b(0x80), self.vod_b(0x40), self.b())
        if o in (0x0e,0x4e,0x8e,0xce): return 'putActorAtObject(%s, %s)' % (self.vod_b(0x80), self.vod_w(0x40))
        if o in (0x36,0x76,0xb6,0xf6): return 'walkActorToObject(%s, %s)' % (self.vod_b(0x80), self.vod_w(0x40))
        if o in (0x19,0x39,0x59,0x79,0x99,0xb9,0xd9,0xf9):
            st = self.vod_b(0x80)
            return 'doSentence(%s, ...)' % st
        if o in (0x52,0xd2): return 'actorFollowCamera(%s)' % self.vod_b(0x80)
        if o in (0x32,0xb2): return 'setCameraAt(%s)' % self.vod_w(0x80)
        if o in (0x12,0x92): return 'panCameraTo(%s)' % self.vod_w(0x80)
        if o in (0x27,0x67,0xa7,0xe7):
            self.op = self.b(); k = self.op & 0x1F
            if k == 1:
                a = self.vod_b(0x80); return 'string[%s] = %s' % (a, self.string())
            if k == 2: return 'copyString(%s, %s)' % (self.vod_b(0x80), self.vod_b(0x40))
            if k == 3: return 'string[%s][%s] = %s' % (self.vod_b(0x80), self.vod_b(0x40), self.vod_b(0x20))
            if k == 4:
                r = self.varref(); return '%s = string[%s][%s]' % (r, self.vod_b(0x80), self.vod_b(0x40))
            if k == 5: return 'newString(%s, %s)' % (self.vod_b(0x80), self.vod_b(0x40))
            self.unknown = True; return '?stringOps%02X' % self.op
        if o in (0x30,0xb0): return 'setBoxFlags(%s, %d)' % (self.vod_b(0x80), self.b())
        if o in (0x54,0xd4): return 'setObjectName(%s, %s)' % (self.vod_w(0x80), self.string())
        if o in (0x58,): return 'beginOverride/%d' % self.b()
        if o in (0x6e,0xee): return 'stopObjectScript(%s)' % self.vod_w(0x80)
        if o in (0x24,0x64,0xa4,0xe4): return 'loadRoomWithEgo(%s, %s, %d, %d)' % (self.vod_w(0x80), self.vod_b(0x40), self.b(), self.b())
        if o in (0x42,0xc2): return 'chainScript(%s, %s)' % (self.vod_b(0x80), self.args())
        if o in (0x43,0xc3): return '%s = getActorX(%s)' % (self.varref(), self.vod_b(0x80))
        if o in (0x23,0xa3): return '%s = getActorY(%s)' % (self.varref(), self.vod_b(0x80))
        if o in (0x06,0x86): return '%s = getActorElevation(%s)' % (self.varref(), self.vod_b(0x80))
        if o in (0x63,0xe3): return '%s = getActorFacing(%s)' % (self.varref(), self.vod_b(0x80))
        if o in (0x71,0xf1): return '%s = getActorCostume(%s)' % (self.varref(), self.vod_b(0x80))
        if o in (0x7b,0xfb): return '%s = getActorWalkBox(%s)' % (self.varref(), self.vod_b(0x80))
        if o in (0x3b,0xbb): return '%s = getActorScale(%s)' % (self.varref(), self.vod_b(0x80))
        if o in (0x56,0xd6): return '%s = getActorMoving(%s)' % (self.varref(), self.vod_b(0x80))
        if o in (0x6c,0xec): return '%s = getActorWidth(%s)' % (self.varref(), self.vod_b(0x80))
        if o in (0x7c,0xfc): return '%s = isSoundRunning(%s)' % (self.varref(), self.vod_b(0x80))
        if o in (0x34,0x74,0xb4,0xf4): return '%s = getDist(%s, %s)' % (self.varref(), self.vod_w(0x80), self.vod_w(0x40))
        if o in (0x66,0xe6): return '%s = getClosestObjActor(%s)' % (self.varref(), self.vod_w(0x80))
        if o in (0x15,0x55,0x95,0xd5): return '%s = actorFromPos(%s, %s)' % (self.varref(), self.vod_w(0x80), self.vod_w(0x40))
        if o in (0x1f,0x5f,0x9f,0xdf): return 'if actorInBox(%s, %s) ; else %s' % (self.vod_b(0x80), self.vod_b(0x40), self.jmp())
        if o in (0x3f,0x7f,0xbf,0xff): return 'drawBox(%s, %s, ...)' % (self.vod_w(0x80), self.vod_w(0x40))
        if o in (0x5c,0xdc): return 'oldRoomEffect(%s)' % self.vod_w(0x80)
        if o in (0xab,): return 'saveRestoreVerbs(%d)' % self.b()
        if o in (0x50,0xd0): return 'pickupObjectOld(%s)' % self.vod_w(0x80)
        if o in (0x2b,): return 'delayVariable(%s)' % self.varref()
        if o in (0x4c,): return 'soundKludge(%s)' % self.args()
        if o in (0x4f,0xcf): return 'if state(%s)!=%s ; else %s' % (self.vod_w(0x80), self.vod_b(0x40), self.jmp())
        self.unknown = True
        return '??? %02X' % o

def disasm(d, start, end, base=0):
    dis = Dis(d); dis.ip = start; out = []
    while dis.ip < end:
        a = dis.ip
        try:
            t = dis.one()
        except IndexError:
            break
        raw = d[a:dis.ip].hex(' ')
        out.append((a, raw, t))
        if dis.unknown: out.append((dis.ip, '', '*** desync ***')); break
    return out

if __name__ == '__main__':
    f, s, e = sys.argv[1], int(sys.argv[2], 0), int(sys.argv[3], 0)
    d = open(f, 'rb').read()
    for a, raw, t in disasm(d, s, e):
        rw = raw if len(raw) <= 26 else raw[:23] + '...'
        print(f'{a:5d} {a:04X}  {rw:<28} {t}')
