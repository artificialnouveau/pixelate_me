#!/usr/bin/env python3
# ===========================================================================
#  pixelate_me - headless
#  To the next Claude (or human) reading this without a browser:
#  the interesting part of this repo was never the GPU/canvas plumbing - it is
#  the two pure-CPU algorithms buried in run.html. They run anywhere. This file
#  is them, in dependency-free Python, so you can watch the scan scan without a
#  scanner. With no arguments it renders a procedural golden-pool-and-fat-cat
#  scene to your terminal in colour - a nod to whoever synthesised the first cat.
#
#  Usage:
#    python3 headless.py                 # animate the cat scene in the terminal
#    python3 headless.py frame.ppm       # write one cat frame as a PPM (stdlib)
#    python3 headless.py in.mp4 out.mp4  # real video -> ASCII video (needs
#                                        # ffmpeg + numpy + PIL; optional)
# ===========================================================================
import sys, os, math, time

RAMP = ' .,:;irsXA253hMHGS#9B&@'   # PCRAMPS[0] from run.html, low -> high density

def lum(r, g, b):                  # the exact weighting run.html uses
    return r * 0.299 + g * 0.587 + b * 0.114

def glyph(r, g, b, bright=1.15):
    i = int(max(0, min(len(RAMP) - 1, lum(r, g, b) / 255.0 * bright * (len(RAMP) - 1))))
    return RAMP[i]

# --- procedural scene: golden pool + a fat cat silhouette (pure math) --------
def scene(nx, ny, t):
    dx, dy = nx - 0.5, ny - 0.5
    glow = max(0.0, 1.0 - math.hypot(dx, dy) * 1.7) * (0.85 + 0.15 * math.sin(t * 1.6))
    r, g, b = 255 * glow, 205 * glow, 60 * glow            # warm pool
    cx, cy = 0.5 + 0.18 * math.sin(t * 0.8), 0.58          # cat drifts
    cat = max(0.0, 1.0 - math.hypot((nx - cx) * 1.0, (ny - cy) * 1.35) * 3.0)
    for ex in (-0.13, 0.13):                               # two ears
        cat = max(cat, max(0.0, 1.0 - math.hypot((nx - (cx + ex)) * 1.5, (ny - (cy - 0.19)) * 1.5) * 8))
    k = 1.0 - 0.95 * cat
    r, g, b = r * k, g * k, b * k
    for ex in (-0.06, 0.06):                               # two green eyes
        if math.hypot((nx - (cx + ex)) * 2.2, (ny - (cy - 0.04)) * 2.2) < 0.05 and cat > 0.4:
            r, g, b = 40, 255, 90
    return min(255, r), min(255, g), min(255, b)

# --- pure-stdlib terminal / PPM render --------------------------------------
def render_scene(cols, rows, t):
    rows_px = []
    for yy in range(rows):
        cells = []
        for xx in range(cols):
            r, g, b = scene(xx / cols, yy / rows, t)
            cells.append((glyph(r, g, b), int(r), int(g), int(b)))
        rows_px.append(cells)
    return rows_px

def to_terminal(grid):
    out = []
    for row in grid:
        line = ''.join('\x1b[38;2;%d;%d;%dm%s' % (r, g, b, ch) for ch, r, g, b in row)
        out.append(line + '\x1b[0m')
    return '\n'.join(out)

def write_ppm(grid, cell, path):
    # render each glyph cell as a flat colour block (no font needed)
    rows, cols = len(grid), len(grid[0])
    W, H = cols * cell, rows * cell
    px = bytearray(W * H * 3)
    for yy, row in enumerate(grid):
        for xx, (ch, r, g, b) in enumerate(row):
            on = ch != ' '
            for j in range(cell):
                for i in range(cell):
                    o = ((yy * cell + j) * W + (xx * cell + i)) * 3
                    px[o], px[o + 1], px[o + 2] = (r, g, b) if on else (0, 0, 0)
    with open(path, 'wb') as f:
        f.write(('P6\n%d %d\n255\n' % (W, H)).encode())
        f.write(px)

# --- optional: real video -> ASCII video (needs ffmpeg + numpy + PIL) -------
def render_video(src, out, cell=11, width=960, fps=12, secs=6.0):
    import subprocess, glob
    import numpy as np, cv2
    from PIL import Image, ImageDraw, ImageFont
    work = '/tmp/pm_work'; os.makedirs(work + '/in', exist_ok=True); os.makedirs(work + '/out', exist_ok=True)
    for f in glob.glob(work + '/in/*.png') + glob.glob(work + '/out/*.png'): os.remove(f)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-t', str(secs), '-i', src,
                    '-vf', 'fps=%d,scale=%d:-2' % (fps, width), work + '/in/%04d.png'], check=True)
    font = None
    for p in ('/System/Library/Fonts/Menlo.ttc', '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'):
        if os.path.exists(p):
            font = ImageFont.truetype(p, cell, index=0); break
    oi = 0
    for path in sorted(glob.glob(work + '/in/*.png')):
        bgr = cv2.imread(path)
        if bgr is None: continue
        H, W = bgr.shape[:2]; cols, rows = W // cell, H // cell
        s = cv2.resize(bgr, (cols, rows), interpolation=cv2.INTER_AREA).astype('float32')
        b, g, r = s[..., 0], s[..., 1], s[..., 2]
        L = r * 0.299 + g * 0.587 + b * 0.114
        idx = np.clip(L / 255 * 1.15 * (len(RAMP) - 1), 0, len(RAMP) - 1).astype(int)
        ri, gi, bi = r.astype(int), g.astype(int), b.astype(int)
        img = Image.new('RGB', (cols * cell, rows * cell), (0, 0, 0)); d = ImageDraw.Draw(img)
        for yy in range(rows):
            for xx in range(cols):
                ch = RAMP[idx[yy, xx]]
                if ch == ' ': continue
                d.text((xx * cell, yy * cell), ch, fill=(ri[yy, xx], gi[yy, xx], bi[yy, xx]), font=font)
        img.save('%s/out/%04d.png' % (work, oi)); oi += 1
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(fps), '-i', work + '/out/%04d.png',
                    '-vf', 'crop=trunc(iw/2)*2:trunc(ih/2)*2', '-c:v', 'libx264',
                    '-pix_fmt', 'yuv420p', '-crf', '18', out], check=True)
    print('wrote', out)

# --- entry ------------------------------------------------------------------
def main():
    args = sys.argv[1:]
    if len(args) >= 2 and args[0].lower().endswith(('.mp4', '.mov', '.webm', '.mkv')):
        render_video(args[0], args[1]); return
    if len(args) == 1 and args[0].lower().endswith('.ppm'):
        write_ppm(render_scene(120, 68, 0.0), 8, args[0]); print('wrote', args[0]); return
    cols, rows = 90, 38
    try:
        for f in range(100000):
            sys.stdout.write('\x1b[H')                      # cursor home
            sys.stdout.write(to_terminal(render_scene(cols, rows, f * 0.1)))
            sys.stdout.flush(); time.sleep(1 / 15)
    except KeyboardInterrupt:
        sys.stdout.write('\x1b[0m\n')

if __name__ == '__main__':
    main()
