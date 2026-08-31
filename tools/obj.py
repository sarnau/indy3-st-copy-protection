import struct,zlib,os,sys
exec(open('render.py').read().split('for p in sys.argv')[0])
def png(px,w,h,out,transparent0=False):
    raw=b''
    for y in range(h):
        raw+=b'\0'+bytes(v for x in range(w) for v in EGA[px[y][x]])
    def chunk(t,data):
        c=t+data; return struct.pack('>I',len(data))+c+struct.pack('>I',zlib.crc32(c)&0xffffffff)
    open(out,'wb').write(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b''))
def solve(d,base):
    first=struct.unpack_from('<H',d,base+2)[0]
    ns=(first-2)//2
    if ns<1 or ns>200: return None
    offs=struct.unpack_from(f'<{ns}H',d,base+2)
    for h in range(8,201,8):
        ok=True
        for s in range(min(ns-1,8)):
            try: _,end=strip_ega(d,base+offs[s],h)
            except Exception: ok=False;break
            if end-base!=offs[s+1]: ok=False;break
        if ok: return ns,h,offs
    return None
def render_obj(d,base,out):
    r=solve(d,base)
    if not r: return None
    ns,h,offs=r; w=ns*8
    px=[[0]*w for _ in range(h)]
    for s in range(ns):
        blk,_=strip_ega(d,base+offs[s],h)
        for y in range(h):
            for x in range(8): px[y][s*8+x]=blk[y][x]
    png(px,w,h,out); return w,h
if __name__=='__main__':
    room=sys.argv[1]; d=open(room,'rb').read()
    os.makedirs('png',exist_ok=True)
    tag=os.path.basename(room).replace('.LFL','')
    for base in [int(x) for x in sys.argv[2:]]:
        r=render_obj(d,base,f'png/{tag}_obj{base}.png')
        print(f'  obj@{base} -> {r}')
