#!/usr/bin/env python3
# ===========================================================================
#  pixelate_me - headless
#  The interesting part of this repo isn't the GPU/canvas plumbing - it is the
#  pure-CPU algorithm buried in run.html: the PixelCrash luminance -> glyph
#  ASCII mapping. It needs no browser and no GPU. This is that algorithm,
#  applied to a video file offline.
#
#  Usage:
#    python3 headless.py in.mp4 out.mp4   # video -> ASCII video
#  Needs ffmpeg + numpy + PIL (opencv-python for fast resize).
# ===========================================================================
import sys, os, subprocess, glob

RAMP = ' .,:;irsXA253hMHGS#9B&@'   # PCRAMPS[0] from run.html, low -> high density

def render_video(src, out, cell=11, width=960, fps=12, secs=6.0):
    import numpy as np, cv2
    from PIL import Image, ImageDraw, ImageFont
    work = '/tmp/pm_work'
    os.makedirs(work + '/in', exist_ok=True); os.makedirs(work + '/out', exist_ok=True)
    for f in glob.glob(work + '/in/*.png') + glob.glob(work + '/out/*.png'): os.remove(f)

    # extract frames
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
        L = r * 0.299 + g * 0.587 + b * 0.114                       # run.html's weighting
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
    print('wrote', out, '(%d frames)' % oi)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('usage: python3 headless.py in.mp4 out.mp4'); sys.exit(1)
    render_video(sys.argv[1], sys.argv[2])
