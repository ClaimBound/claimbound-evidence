#!/usr/bin/env python3
"""Generate the Protocolith logo assets (isometric monolith on strata slabs) as plain SVG.

Writes into docs/assets/protocolith/: logo-mark.svg, logo-mark-dark.svg, favicon.svg (simplified: two slabs, no ticks),
logo.svg and logo-dark.svg (horizontal lockups; the wordmark paths are kept from the existing files) and replaces the mark
inside social-preview.svg. The tick heights come from the SHA-256 of "protocolith". Standard library only.
PNG files are rendered from the SVGs with any SVG rasterizer (for example `qlmanage -t -s 512` on macOS).
"""
import math,hashlib,sys
K=math.sqrt(3)/2
def P(x,y,z): return ((x-y)*K, (x+y)*0.5 - z)
def poly(pts,fill,extra=""):
    return '<polygon points="%s" fill="%s"%s/>'%(" ".join("%.2f,%.2f"%p for p in pts),fill,extra)
def block(x0,y0,z0,w,d,h,top,left,right,stroke):
    A=lambda x,y,z:P(x0+x,y0+y,z0+z)
    out=[]
    out.append(poly([A(w,0,0),A(w,d,0),A(w,d,h),A(w,0,h)],right,f' stroke="{stroke}" stroke-width="0.6"'))
    out.append(poly([A(0,d,0),A(w,d,0),A(w,d,h),A(0,d,h)],left,f' stroke="{stroke}" stroke-width="0.6"'))
    out.append(poly([A(0,0,h),A(w,0,h),A(w,d,h),A(0,d,h)],top,f' stroke="{stroke}" stroke-width="0.6"'))
    return "".join(out)
def build(dark=False, simple=False):
    if dark: ink="#0E141B"; pal=[("#7FA6DE","#4F7DB8","#2B4C7A"),("#6C97D1","#436FA8","#25446E"),("#5F8CC6","#3B6399","#203D63"),("#527FB8","#335A8C","#1B3556")]; cap=("#A9C5EE","#5B8AC9","#2F5486"); amber="#F0B545"; tick="#C8D9F2"
    else: ink="#0E141B"; pal=[("#6C97D1","#436FA8","#25446E"),("#5F8CC6","#3B6399","#203D63"),("#527FB8","#335A8C","#1B3556"),("#4673A9","#2D5282","#17304F")]; cap=("#8FB3E6","#3E6BA8","#1F3A5F"); amber="#E8B04A"; tick="#B4CBEA"
    digits=hashlib.sha256(b"protocolith").hexdigest()
    parts=[]; S=104; H=9 if not simple else 16; z=0
    # strata, bottom first, slight horizontal stagger from the hash digits
    for k,(t,l,r) in enumerate(pal[:2] if simple else pal):
        off=(int(digits[k],16)-7.5)*0.55
        parts.append(block(off,0,z,S,S,H,t,l,r,ink if False else "#0B1624"))
        # hash ticks on the right face of this slab
        for j in range(0 if simple else 6):
            hh=2+int(digits[k*6+j+4],16)/15*4.2
            y=12+j*14
            x=S+off
            p1=P(x,y,z+1.2); p2=P(x,y,z+1.2+hh)
            parts.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" stroke-width="1.6" stroke-linecap="round" opacity="0.85"/>'%(p1[0],p1[1],p2[0],p2[1],tick))
        z+=H
    # monolith cap
    w=46; d=46; h=88; ox=29; oy=29
    parts.append(block(ox,oy,z,w,d,h,cap[0],cap[1],cap[2],"#0B1624"))
    # amber head line along the top front edges of the monolith
    a=P(ox,oy+d,z+h); b=P(ox+w,oy+d,z+h); c=P(ox+w,oy,z+h)
    parts.append('<polyline points="%.2f,%.2f %.2f,%.2f %.2f,%.2f" fill="none" stroke="%s" stroke-width="2.2" stroke-linejoin="round"/>'%(a[0],a[1],b[0],b[1],c[0],c[1],amber))
    # carved amber P on the left face
    o=P(ox,oy+d,z)  # face origin (u=0,v=0)
    tr=f'matrix({K:.4f} 0.5 0 -1 {o[0]:.3f} {o[1]:.3f})'
    g=('M10,20H21V36H29C37,36 41,42 41,50C41,58 37,64 29,64H10ZM21,44H28C31,44 32,46 32,50C32,54 31,56 28,56H21Z')
    parts.append(f'<path transform="{tr}" fill-rule="evenodd" fill="{amber}" d="{g}"/>')
    body="".join(parts)
    xs=[float(x) for x in __import__("re").findall(r'(-?\d+\.\d+),(-?\d+\.\d+)',body) for x in [x[0]]]
    return body
def svg(dark=False, simple=False):
    body=build(dark, simple)
    import re
    pts=[(float(a),float(b)) for a,b in re.findall(r'(-?\d+\.\d+),(-?\d+\.\d+)',body)]
    for m in re.finditer(r'x1="(-?\d+\.\d+)" y1="(-?\d+\.\d+)" x2="(-?\d+\.\d+)" y2="(-?\d+\.\d+)"',body):
        pts+= [(float(m[1]),float(m[2])),(float(m[3]),float(m[4]))]
    minx=min(p[0] for p in pts); maxx=max(p[0] for p in pts); miny=min(p[1] for p in pts); maxy=max(p[1] for p in pts)
    sc=232/max(maxx-minx,maxy-miny); tx=128-(minx+maxx)/2*sc; ty=128-(miny+maxy)/2*sc
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256" role="img" aria-labelledby="t d"><title id="t">Protocolith mark</title>'
            '<desc id="d">An isometric monolith with an amber P carved in its face, standing on four strata slabs whose edges carry hash-like ticks, one slab per ledger layer.</desc>'
            f'<g transform="translate({tx:.2f},{ty:.2f}) scale({sc:.4f})">{body}</g></svg>\n')

import pathlib, re
OUT = pathlib.Path(__file__).resolve().parent.parent / "docs" / "assets" / "protocolith"
(OUT / "logo-mark.svg").write_text(svg(False), encoding="utf-8")
(OUT / "logo-mark-dark.svg").write_text(svg(True), encoding="utf-8")
(OUT / "favicon.svg").write_text(svg(False, True).replace("Protocolith mark", "Protocolith favicon"), encoding="utf-8")

def inner_of(s):
    return re.search(r"<g transform=.*</g>", s, re.S).group(0)

DESC_OLD = re.compile(r'<desc id="d">.*?</desc>', re.S)
DESC_NEW = '<desc id="d">An isometric monolith with an amber P carved in its face, standing on four strata slabs whose edges carry hash-like ticks.</desc>'
MARK_OPEN, MARK_CLOSE = "<!--mark-->", "<!--/mark-->"
for name, dark in (("logo.svg", False), ("logo-dark.svg", True)):
    path = OUT / name
    text = path.read_text(encoding="utf-8")
    mark = MARK_OPEN + '<g transform="translate(4,0) scale(0.78)">' + inner_of(svg(dark)) + "</g>" + MARK_CLOSE
    if MARK_OPEN in text:
        text = re.sub(re.escape(MARK_OPEN) + ".*?" + re.escape(MARK_CLOSE), lambda m: mark, text, flags=re.S)
    else:
        i = text.index('<g transform="translate(20,20)">')
        j = text.index("</g>", i)
        text = text[:i] + mark + text[j + 4:]
    path.write_text(DESC_OLD.sub(DESC_NEW, text, count=1), encoding="utf-8")

social = OUT / "social-preview.svg"
text = social.read_text(encoding="utf-8")
mark = MARK_OPEN + '<g transform="translate(113,128) scale(1.17)">' + inner_of(svg(True)) + "</g>" + MARK_CLOSE
if MARK_OPEN in text:
    text = re.sub(re.escape(MARK_OPEN) + ".*?" + re.escape(MARK_CLOSE), lambda m: mark, text, flags=re.S)
else:
    i = text.index('<g transform="translate(113.5,125) scale(1.875)">')
    j = text.index("</g>", i)
    text = text[:i] + mark + text[j + 4:]
social.write_text(text, encoding="utf-8")
print("wrote logo assets")
