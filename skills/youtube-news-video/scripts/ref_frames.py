#!/usr/bin/env python3
"""Reference breakdown: pull EVERY frame of a reference clip (or a time range / crop of it) at its own
frame rate, and build labelled contact sheets (method adapted from NiazMorshed2007/reanimate and
rossark0/rossark-motion-skill, both MIT; own code).

  .venv/bin/python -I <skill>/scripts/ref_frames.py REF.mp4 --out anim/ref/<name>
        [--start 0] [--end 4] [--crop x:y:w:h] [--fps SOURCE] [--width 1920] [--like OUR_RENDER.mp4]

Writes <out>/frames/0000.png ..., <out>/frames.json (fps, size, start, crop, source),
<out>/sheets/timing_NN.png (every frame, 10 per row, ~2 s per sheet: shows timing, easing, follow-through)
and <out>/sheets/poses.png (2 frames per second: shows the poses).
Use the SAME --start/--end/--crop/--fps on our render (or --like to copy them from another frames.json)
so the comparison measures the animation, not the setup. Prints the probe first.
"""
import argparse, json, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def probe(p):
    j = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                   "stream=width,height,r_frame_rate,nb_frames:format=duration", "-of", "json", str(p)],
                                  capture_output=True, text=True, check=True).stdout)
    s = j["streams"][0]; a, b = s["r_frame_rate"].split("/")
    return {"width": s["width"], "height": s["height"], "fps": float(a) / float(b), "duration": float(j["format"]["duration"])}


def font(size):
    for f in ["/System/Library/Fonts/Supplemental/Arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "C:/Windows/Fonts/arial.ttf"]:
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    return ImageFont.load_default()


def sheet(paths, labels, dest, cols, tile_w):
    ims = [Image.open(p).convert("RGB") for p in paths]
    r = tile_w / ims[0].width; th = int(ims[0].height * r); bar = 22
    rows = (len(ims) + cols - 1) // cols
    out = Image.new("RGB", (cols * tile_w, rows * (th + bar)), (12, 10, 14)); d = ImageDraw.Draw(out); f = font(15)
    for i, (im, lab) in enumerate(zip(ims, labels)):
        x, y = (i % cols) * tile_w, (i // cols) * (th + bar)
        out.paste(im.resize((tile_w, th), Image.LANCZOS), (x, y + bar)); d.text((x + 4, y + 3), lab, font=f, fill=(246, 241, 234))
    out.save(dest)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video"); ap.add_argument("--out", required=True)
    ap.add_argument("--start", type=float, default=0.0); ap.add_argument("--end", type=float)
    ap.add_argument("--crop", help="x:y:w:h in source pixels"); ap.add_argument("--fps", type=float)
    ap.add_argument("--width", type=int, help="scale frames to this width (keep it equal for reference and ours)")
    ap.add_argument("--like", help="copy start/end/crop/fps from another frames.json and resize to its frame size")
    a = ap.parse_args()
    info = probe(a.video)
    print(f"probe: {info['width']}x{info['height']} @ {info['fps']:.3f} fps, {info['duration']:.2f} s")
    if a.like:
        L = json.loads(Path(a.like).read_text())
        a.start, a.end, a.crop, a.fps = L["start"], L["end"], L.get("crop"), L["fps"]
        # always match the reference's frame SIZE, so tracking regions and coordinates mean the same thing
        a.width = L.get("width") or (L.get("frame_size") or [None])[0]
    fps = a.fps or info["fps"]; end = a.end if a.end is not None else info["duration"]
    out = Path(a.out); fr = out / "frames"; sh = out / "sheets"
    fr.mkdir(parents=True, exist_ok=True); sh.mkdir(parents=True, exist_ok=True)
    for old in fr.glob("*.png"):
        old.unlink()
    vf = []
    if a.crop:
        x, y, w, h = a.crop.split(":"); vf.append(f"crop={w}:{h}:{x}:{y}")
    if a.width:
        vf.append(f"scale={a.width}:-2:flags=lanczos")
    vf.append(f"fps={fps}")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a.start:.3f}", "-to", f"{end:.3f}", "-i", str(a.video),
                    "-vf", ",".join(vf), "-start_number", "0", str(fr / "%04d.png")], check=True)
    files = sorted(fr.glob("*.png"))
    if not files:
        sys.exit("no frames extracted (check --start/--end)")
    w, h = Image.open(files[0]).size
    meta = {"source": str(a.video), "fps": fps, "start": a.start, "end": end, "crop": a.crop, "width": a.width,
            "frame_size": [w, h], "frames": len(files)}
    (out / "frames.json").write_text(json.dumps(meta, indent=1))
    per = max(10, int(round(fps * 2 / 10)) * 10)  # ~2 s per timing sheet, whole rows of 10
    tile = 160 if h > w else 220
    n_sheets = 0
    for k in range(0, len(files), per):
        chunk = files[k:k + per]
        sheet(chunk, [f"f{k + i} {a.start + (k + i) / fps:.3f}s" for i in range(len(chunk))], sh / f"timing_{k // per + 1:02d}.png", 10, tile)
        n_sheets += 1
    step = max(1, int(round(fps / 2)))
    pose = files[::step]
    sheet(pose, [f"{a.start + i * step / fps:.2f}s" for i in range(len(pose))], sh / "poses.png", 8, tile + 40)
    print(f"{len(files)} frames ({w}x{h}) at {fps:g} fps -> {fr}; {n_sheets} timing sheets + poses.png in {sh}")


if __name__ == "__main__":
    main()
