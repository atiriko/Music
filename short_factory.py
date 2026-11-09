#!/usr/bin/env python3
"""
Loomworkz Shorts Factory
Create short-form videos with one screen recording per output by default.
Requires only Python 3.9+ and FFmpeg/FFprobe (brew install ffmpeg on macOS).

Important: This script generates VIDEO FILES, not social uploads.
Use your approved scheduling service to publish; never automate login/browser posting.
"""
import argparse
import csv
import json
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
DEFAULT_BASE = ROOT
FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
]
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".flac"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".mkv"}

def check_tool(cmd):
    if shutil.which(cmd) is None:
        raise SystemExit(f"Missing {cmd}. On Mac, run: brew install ffmpeg")

def get_font(custom=None):
    if custom:
        font = Path(custom).expanduser()
        if not font.exists():
            raise SystemExit(f"Font not found: {font}")
        return font
    for candidate in FONT_CANDIDATES:
        p = Path(candidate)
        if p.exists():
            return p
    raise SystemExit("No usable font found. Provide --font /path/to/bold-font.ttf")

def escape_filter_path(value):
    return str(value).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'").replace(",", "\\,")

def get_info(path):
    p = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-show_entries", "stream=codec_type", "-of", "json", str(path)],
        capture_output=True, text=True
    )
    if p.returncode:
        raise ValueError(f"ffprobe: {p.stderr.strip()}")
    data = json.loads(p.stdout)
    return {
        "duration": float(data.get("format", {}).get("duration", 0) or 0),
        "has_audio": any(s.get("codec_type") == "audio" for s in data.get("streams", []))
    }

def find_source(record_dir, expected):
    stem = Path(expected).stem
    for ext in [".mp4", ".mov", ".m4v", ".mkv", ".MP4", ".MOV"]:
        p = record_dir / (stem + ext)
        if p.is_file():
            return p
    return None

def wrap(text, maxwidth=27, maxlines=3):
    output = textwrap.wrap(text, maxwidth, break_long_words=False,
                           break_on_hyphens=False)
    if len(output) > maxlines:
        output = output[:maxlines]
        output[-1] = output[-1].rstrip(" .,") + "..."
    return "\n".join(output)

def write_overlay(temp_dir, row):
    temp_dir.mkdir(parents=True, exist_ok=True)
    stem = row["video_filename"].rsplit(".", 1)[0]
    paths = []
    for suffix, value in [
        ("hook", wrap(row["hook"], 27, 2)),
        ("sub", wrap(row["supporting_text"], 40, 2)),
        ("question", wrap(row["on_screen_question"], 35, 2))
    ]:
        lines = []
        # Some FFmpeg/font combinations draw a missing-glyph box for '\n'
        # even while moving to the next line. Never send drawtext a newline.
        for index, line in enumerate(value.splitlines()):
            p = temp_dir / f"{stem}_{suffix}_{index}.txt"
            p.write_text(line, encoding="utf-8")
            lines.append(p)
        paths.append(lines)
    return paths

def ffmpeg_filter(hook, sub, question, font):
    font = escape_filter_path(font)
    text_filters = []
    for lines, size, y, spacing in [
        (hook, 68, 133, 80), (sub, 39, 345, 49), (question, 56, 1665, 66)
    ]:
        for index, path in enumerate(lines):
            path = escape_filter_path(path)
            text_filters.append(
                f"drawtext=fontfile='{font}':textfile='{path}':expansion=none:"
                f"fontcolor=white:fontsize={size}:x=(w-text_w)/2:y={y + index * spacing}"
            )
    return (
        "[0:v]setpts=PTS-STARTPTS,split=2[bg0][fg0];"
        "[bg0]scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,setsar=1,boxblur=24:8[bg];"
        "[fg0]scale=980:1250:force_original_aspect_ratio=decrease,"
        "setsar=1[fg];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2:shortest=1,"
        "drawbox=x=0:y=85:w=iw:h=375:color=black@0.72:t=fill,"
        "drawbox=x=0:y=1600:w=iw:h=260:color=black@0.72:t=fill,"
        + ",".join(text_filters) + ",fps=30,format=yuv420p[v]"
    )


def parse_duration(value):
    if value in ("source", "manifest"):
        return value
    try:
        seconds = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError("duration must be source, manifest, or a positive number of seconds")
    if not 0 < seconds < float("inf"):
        raise argparse.ArgumentTypeError("duration must be a positive finite number of seconds")
    return seconds


def clip_window(row, available_duration, duration="source"):
    if available_duration < 5:
        raise ValueError("Screen recording must be at least 5 seconds long.")
    if duration == "source":
        return 0.0, available_duration
    target = float(row.get("duration_sec") or available_duration) if duration == "manifest" else float(duration)
    if not 0 < target < float("inf"):
        raise ValueError("Clip duration must be a positive finite number of seconds.")
    length = min(target, available_duration)
    wanted_start = max(0, float(row.get("start_offset_sec") or 0))
    start = min(wanted_start, max(0, available_duration - length))
    return start, length


def create_video(row, source, audio_file, output, temp_dir, font, preset, duration="source"):
    source_info = get_info(source)
    start, length = clip_window(row, source_info["duration"], duration)
    overlays = write_overlay(temp_dir, row)
    filt = ffmpeg_filter(*overlays, font)
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-ss", f"{start:.3f}", "-t", f"{length:.3f}",
        "-i", str(source),
    ]
    if audio_file:
        cmd.extend(["-stream_loop", "-1", "-i", str(audio_file)])
    cmd.extend(["-filter_complex", filt, "-map", "[v]"])
    if audio_file:
        cmd.extend(["-map", "1:a:0", "-af",
                    f"afade=t=in:st=0:d=0.2,afade=t=out:st={max(0, length-0.8):.2f}:d=0.8"])
    elif source_info["has_audio"]:
        cmd.extend(["-map", "0:a:0"])
    else:
        raise ValueError("No sound found. Add an audio file to assets/<project>/audio or record with audio.")
    cmd.extend([
        "-t", f"{length:.3f}", "-r", "30",
        "-c:v", "libx264", "-preset", preset, "-crf", "22",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
        "-movflags", "+faststart", str(output)
    ])
    # Publish the finished file only after encoding succeeds. A failed rerender
    # must not replace or delete a usable existing video.
    partial = output.with_name(output.stem + ".partial" + output.suffix)
    cmd[-1] = str(partial)
    finished = subprocess.run(cmd, capture_output=True, text=True)
    if finished.returncode:
        partial.unlink(missing_ok=True)
        raise ValueError("FFmpeg render failed:\n" + finished.stderr[-2500:])
    partial.replace(output)
    return start, length

def load_manifest(project):
    manifest_path = ROOT / f"{project}_100_video_plan.csv"
    if not manifest_path.is_file():
        raise SystemExit(f"Missing manifest next to script: {manifest_path}")
    with manifest_path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

def map_sources(rows, project, mode="sequence"):
    """Match output numbers to recording numbers, independent of batch offsets."""
    mapped = []
    for row in rows:
        row = dict(row)
        if mode == "sequence":
            number = int(Path(row["video_filename"]).stem.rsplit("_", 1)[1])
            row["source_file"] = f"{project}_{number:02d}.mp4"
        elif mode != "manifest":
            raise ValueError(f"Unknown source mode: {mode}")
        mapped.append(row)
    return mapped


def export_queue(project, rows, rendered_dir, public_base, base):
    queue = base / "posting_queues" / project
    queue.mkdir(parents=True, exist_ok=True)
    public_base = (public_base or "").strip()
    if public_base and not public_base.lower().startswith("https://"):
        raise SystemExit("--public-base-url must be an HTTPS URL that serves the files directly.")
    records = []
    for row in rows:
        output = rendered_dir / row["video_filename"]
        if not output.is_file():
            continue
        media_url = (public_base.rstrip("/") + "/" + quote(output.name)) if public_base else ""
        records.append({
            "ID":row["id"],
            "MP4 local file":str(output),
            "Caption":row["caption"] + "\n" + row["hashtags"],
            "Direct video URL":media_url,
            "Facebook": "TRUE",
            "Instagram": "TRUE",
            "TikTok": "TRUE",
            "YouTube": "TRUE",
            "YouTube Short Title":row["hook"][:100]
        })
    # Always export a generic tracker compatible with an existing automation.
    fields=["ID","MP4 local file","Caption","Direct video URL",
            "Facebook","Instagram","TikTok","YouTube","YouTube Short Title"]
    with (queue / "publishing_manifest.csv").open("w", encoding="utf-8", newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(records)
    # Metricool Autolist CSV requires two columns: text and URL to the video.
    # Import only once URLs resolve; otherwise use manual file upload.
    if public_base:
        for i in range(0, len(records), 50):
            batch = records[i:i+50]
            dest = queue / f"metricool_autolist_{i//50+1}.csv"
            with dest.open("w", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                w.writerow(["Text","Picture Url 1"])
                for item in batch:
                    w.writerow([item["Caption"], item["Direct video URL"]])
    print(f"Queue exported: {len(records)} rendered clips -> {queue}")
    if not public_base:
        print("No public URLs provided. Upload MP4s manually in your scheduler,")
        print("or upload them to HTTPS storage, then rerun with --public-base-url.")
    return len(records)

def main():
    parser=argparse.ArgumentParser(description="Create 100 vertical Shorts/Reels/TikToks from screen recordings")
    parser.add_argument("--base",type=Path,default=DEFAULT_BASE,
                        help="Your Mac workspace (default: /Users/macbook/Desktop/Music)")
    parser.add_argument("--project",choices=["music","game","all"],default="music")
    parser.add_argument("--source-mode", choices=["sequence", "manifest"], default="sequence",
                        help="Use recording 01 for output 001, etc. (default); manifest restores the original reuse plan")
    parser.add_argument("--limit",type=int,default=None,help="Render only this many clips to test")
    parser.add_argument("--offset",type=int,default=0,help="Start at this clip number, 0 based")
    parser.add_argument("--font",default=None,help="Path to a bold TTF or TTC font")
    parser.add_argument("--duration", type=parse_duration, default="source", metavar="source|manifest|SECONDS",
                        help="Keep the full source by default; use manifest for planned cuts, or set a length in seconds")
    parser.add_argument("--preset",default="veryfast",choices=["ultrafast","superfast","veryfast","faster","fast","medium"])
    parser.add_argument("--public-base-url",default="",help="Public HTTPS folder of the rendered MP4s")
    parser.add_argument("--only-export",action="store_true",help="Only generate upload CSVs for existing MP4s")
    parser.add_argument("--dry-run",action="store_true",help="Check files and show work planned")
    parser.add_argument("--force",action="store_true",help="Re-render existing videos")
    args=parser.parse_args()
    base=args.base.expanduser()
    if args.offset < 0 or (args.limit is not None and args.limit <= 0):
        parser.error("--offset >= 0 and --limit > 0 required")
    projects = ["music","game"] if args.project=="all" else [args.project]
    check_tool("ffprobe")
    if not (args.dry_run or args.only_export):
        check_tool("ffmpeg")
        font=get_font(args.font)
    else:
        font=None
    for project in projects:
        project_rows=map_sources(load_manifest(project), project, args.source_mode)
        record_dir=base/"assets"/project/"recordings"
        audio_dir=base/"assets"/project/"audio"
        rendered_dir=base/"rendered"/project
        temp_dir=base/"work"/"overlay_text"/project
        for directory in [record_dir,audio_dir,rendered_dir,temp_dir]:
            directory.mkdir(parents=True,exist_ok=True)
        tracks=sorted([p for p in audio_dir.iterdir() if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS])
        subset=project_rows[args.offset:]
        if args.limit is not None:
            subset=subset[:args.limit]
        print(f"\nPROJECT {project.upper()} - {len(subset)} clip(s)")
        ok=skipped=missing=0
        for row in subset:
            source = find_source(record_dir,row["source_file"])
            output = rendered_dir/row["video_filename"]
            if args.only_export:
                continue
            if not source:
                print(f"  MISSING {row['source_file']} (for {row['video_filename']})")
                missing+=1
                continue
            if output.is_file() and not args.force:
                skipped+=1
                continue
            if args.dry_run:
                start, length = clip_window(row, get_info(source)["duration"], args.duration)
                print(f"  READY {row['video_filename']} <= {source.name} ({length:.1f}s, start {start:.1f}s)")
                ok+=1
                continue
            # Each variation hears a different audio sample when multiple exist.
            audio_file=tracks[(int(row["variant"])-1 + (int(row["source_file"].split("_")[1].split(".")[0])-1)) % len(tracks)] if tracks else None
            try:
                start,dur=create_video(row,source,audio_file,output,temp_dir,font,args.preset,args.duration)
                print(f"  DONE {output.name} <= {source.name} ({dur:.1f}s, start {start:.1f}s)")
                ok+=1
            except Exception as e:
                print(f"  ERROR {row['video_filename']}: {e}")
        print(f"Result: rendered/ready={ok}, skipped-existing={skipped}, missing-recordings={missing}")
        if not args.dry_run:
            export_queue(project,project_rows,rendered_dir,args.public_base_url,base)
            print("Note: Queue files do not post automatically. Link your approved scheduler or Autolist.")
    return 0

if __name__=="__main__":
    sys.exit(main())
