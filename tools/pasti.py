import struct, sys, os

TRK_SECT  = 0x0001
TRK_PROT  = 0x0020
TRK_IMAGE = 0x0040
TRK_SYNC  = 0x0080

FDC_CRC   = 0x08   # CRC error
FDC_RNF   = 0x10   # record not found
FDC_DDM   = 0x20   # deleted data mark
SEC_FUZZY = 0x80   # fuzzy bits present

class Sector:
    __slots__=('off','bitpos','readtime','tr','hd','sc','sz','crc','fdc','res','data')

class Track:
    pass

def parse(path):
    d = open(path,'rb').read()
    assert d[:4]==b'RSY\0', 'not pasti'
    ver,tool,res,ntrk,rev = struct.unpack_from('<HHHBB',d,4)
    p = 16
    tracks=[]
    for i in range(ntrk):
        base=p
        rsize,fuzzy,nsec,flags,tlen,tnum,ttype = struct.unpack_from('<IIHHHBB',d,p)
        t=Track()
        t.rsize,t.fuzzy,t.nsec,t.flags,t.tlen = rsize,fuzzy,nsec,flags,tlen
        t.track = tnum & 0x7f
        t.side  = (tnum>>7)&1
        t.ttype = ttype
        t.offset= base
        q = p+16
        t.sectors=[]
        if flags & TRK_SECT:
            for s in range(nsec):
                sec=Sector()
                (sec.off,sec.bitpos,sec.readtime,sec.tr,sec.hd,sec.sc,sec.sz,
                 sec.crc,sec.fdc,sec.res)=struct.unpack_from('<IHHBBBBHBB',d,q)
                q+=16
                t.sectors.append(sec)
        t.fuzzymask = d[q:q+fuzzy]; q+=fuzzy
        database = q   # sector dataOffsets are relative to here
        t.image=None; t.syncoff=None
        if flags & TRK_IMAGE:
            if flags & TRK_SYNC:
                t.syncoff = struct.unpack_from('<H',d,q)[0]; q+=2
            isize = struct.unpack_from('<H',d,q)[0]; q+=2
            t.image = d[q:q+isize]; q+=isize
            if (q-base)&1: q+=1   # record padded to even
        secbase=database
        if flags & TRK_SECT:
            for sec in t.sectors:
                n = 128<<(sec.sz&3)
                sec.data = d[secbase+sec.off: secbase+sec.off+n]
        else:
            # simple track: nsec sequential 512-byte sectors
            for s in range(nsec):
                sec=Sector()
                sec.off=s*512; sec.bitpos=0; sec.readtime=0
                sec.tr=t.track; sec.hd=t.side; sec.sc=s+1; sec.sz=2
                sec.crc=0; sec.fdc=0; sec.res=0
                sec.data=d[secbase+s*512: secbase+(s+1)*512]
                t.sectors.append(sec)
        tracks.append(t)
        p = base+rsize
    return ver,tool,ntrk,rev,tracks

if __name__=='__main__':
    for path in sys.argv[1:]:
        ver,tool,ntrk,rev,tracks=parse(path)
        print(f'== {os.path.basename(path)}  ver={ver} tool={tool} rev={rev} tracks={ntrk}')
        for t in tracks:
            print(f'  T{t.track:02d}.{t.side} flags={t.flags:04x} nsec={t.nsec:2d} tlen={t.tlen:5d} fuzzy={t.fuzzy:4d} img={"Y" if t.image else "n"} sync={t.syncoff} type={t.ttype}')
