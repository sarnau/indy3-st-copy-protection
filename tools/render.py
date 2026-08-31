import struct,sys,os,zlib
EGA=[(0,0,0),(0,0,170),(0,170,0),(0,170,170),(170,0,0),(170,0,170),(170,85,0),(170,170,170),
     (85,85,85),(85,85,255),(85,255,85),(85,255,255),(255,85,85),(255,85,255),(255,255,85),(255,255,255)]

def strip_ega(src,i,height):
    """returns 8-wide column block as list of rows(8 vals), and new index"""
    out=[[0]*8 for _ in range(height)]
    x=0;y=0
    while x<8:
        color=src[i]; i+=1
        if color & 0x80:
            run=color & 0x3f
            if color & 0x40:
                color=src[i]; i+=1
                if run==0: run=src[i]; i+=1
                for z in range(run):
                    out[y][x] = (color & 0xf) if (z&1) else (color>>4)
                    y+=1
                    if y>=height: y=0; x+=1
                    if x>=8: return out,i
            else:
                if run==0: run=src[i]; i+=1
                for z in range(run):
                    out[y][x] = out[y][x-1] if x>0 else 0
                    y+=1
                    if y>=height: y=0; x+=1
                    if x>=8: return out,i
        else:
            run=color>>4
            if run==0: run=src[i]; i+=1
            for z in range(run):
                out[y][x]=color & 0xf
                y+=1
                if y>=height: y=0; x+=1
                if x>=8: return out,i
    return out,i

def render(path,out):
    d=open(path,'rb').read()
    w,h=struct.unpack_from('<HH',d,4)
    off=struct.unpack_from('<H',d,10)[0]
    ns=w//8
    blocksize=struct.unpack_from('<H',d,off)[0]
    offs=struct.unpack_from(f'<{ns}H',d,off+2)
    px=[[0]*w for _ in range(h)]
    for s in range(ns):
        blk,_=strip_ega(d,off+offs[s],h)
        for y in range(h):
            for x in range(8):
                px[y][s*8+x]=blk[y][x]
    # write PNG
    raw=b''
    for y in range(h):
        raw+=b'\0'+bytes(v for x in range(w) for v in EGA[px[y][x]])
    def chunk(t,data):
        c=t+data
        return struct.pack('>I',len(data))+c+struct.pack('>I',zlib.crc32(c)&0xffffffff)
    png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
    open(out,'wb').write(png)
    return w,h

for p in sys.argv[1:]:
    o='png/'+os.path.basename(p).replace('.LFL','.png')
    os.makedirs('png',exist_ok=True)
    try:
        w,h=render(p,o); print(f'{p} -> {o}  {w}x{h}')
    except Exception as e:
        print(f'{p} FAILED: {type(e).__name__}: {e}')
