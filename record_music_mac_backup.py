from pathlib import Path
from playwright.sync_api import sync_playwright
import argparse, random, re, shutil, subprocess, time

BASE = Path.home() / "Desktop/Music"
SITE = "https://music.loomworkz.com"
RAW = BASE / "browser_raw"
OUT = BASE / "assets/music/recordings"

RAW.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)

PROMPTS = [
    "Lo-fi hip hop, mellow piano, rainy evening",
    "Energetic electronic gaming soundtrack",
    "Uplifting acoustic guitar, warm summer feeling",
    "Smooth jazz cafe, piano and brushed drums",
    "Dramatic cinematic orchestral adventure",
    "Retro synthwave, neon night, driving bass",
    "Peaceful ambient meditation, soft synth pads",
    "Upbeat tropical house, bright melodies",
    "Funky bass groove with lively drums",
    "Epic fantasy adventure soundtrack",
]

def scroll_bottom(page):
    page.evaluate(
        "window.scrollTo(0, document.documentElement.scrollHeight)"
    )
    page.mouse.wheel(0, 10000)
    page.wait_for_timeout(1000)

def choose_settings(page, rng, prompt):
    for el in page.locator(
        'textarea:visible, input[type="text"]:visible'
    ).all():
        hint = " ".join([
            el.get_attribute("placeholder") or "",
            el.get_attribute("aria-label") or ""
        ]).lower()

        if any(x in hint for x in (
            "search", "email", "username", "login"
        )):
            continue
        try:
            el.fill(prompt, timeout=2000)
            print("Entered prompt:", prompt)
            break
        except Exception:
            pass

    for el in page.locator("select:visible").all():
        try:
            opts = el.locator("option").evaluate_all(
                "(xs) => xs.filter(x => "
                "!x.disabled && x.value).map(x => x.value)"
            )
            if opts:
                el.select_option(rng.choice(opts))
        except Exception:
            pass

    groups = {}
    for el in page.locator(
        'input[type="radio"]:visible'
    ).all():
        name = el.get_attribute("name")
        if name:
            groups.setdefault(name, []).append(el)

    for group in groups.values():
        try:
            rng.choice(group).check(timeout=2000)
        except Exception:
            pass

    for el in page.locator(
        'input[type="range"]:visible'
    ).all():
        try:
            lo, hi, step = el.evaluate(
                "(e) => [Number(e.min||0), "
                "Number(e.max||100), Number(e.step||1)]"
            )
            step = step or 1
            value = lo + rng.randint(
                0, max(0, int((hi-lo)/step))
            ) * step

            el.evaluate("""(e, v) => {
                const setter =
                  Object.getOwnPropertyDescriptor(
                    HTMLInputElement.prototype,
                    'value'
                  ).set;
                setter.call(e, String(v));
                e.dispatchEvent(
                  new Event('input', {bubbles:true})
                );
                e.dispatchEvent(
                  new Event('change', {bubbles:true})
                );
            }""", value)
        except Exception:
            pass

def is_playing(page):
    try:
        return page.locator("audio").evaluate_all(
            "(xs) => xs.some(a => !a.paused && !a.ended)"
        )
    except Exception:
        return False

def start_playback(page, timeout):
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        scroll_bottom(page)

        if is_playing(page):
            print("Audio is already playing")
            return True

        pause = page.get_by_role(
            "button",
            name=re.compile(r"\bpause\b", re.I)
        )
        for button in pause.all():
            if button.is_visible():
                print("Player is already active")
                return True

        players = page.get_by_role(
            "button",
            name=re.compile(
                r"\b(play|listen|preview)\b", re.I
            )
        ).all()

        players += page.locator(
            'button[title*="play" i], '
            '[role="button"][title*="play" i]'
        ).all()

        for button in reversed(players):
            try:
                if button.is_visible() and button.is_enabled():
                    button.scroll_into_view_if_needed()
                    button.click(timeout=3000)
                    print("Clicked Play")
                    return True
            except Exception:
                pass

        for audio in page.locator("audio").all():
            try:
                audio.evaluate("(a) => a.play()")
                print("Started HTML audio player")
                return True
            except Exception:
                pass

        page.wait_for_timeout(2000)

    return False

def stop_ffmpeg(proc):
    if proc.poll() is None:
        try:
            proc.stdin.write(b"q\n")
            proc.stdin.flush()
            proc.wait(timeout=15)
        except Exception:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument(
        "--generate-timeout", type=int, default=240
    )
    parser.add_argument(
        "--play-seconds", type=int, default=35
    )
    args = parser.parse_args()

    if not shutil.which("ffmpeg"):
        raise SystemExit("Install ffmpeg with brew first")

    devices = subprocess.run(
        ["ffmpeg", "-f", "avfoundation",
         "-list_devices", "true", "-i", ""],
        capture_output=True, text=True
    ).stderr

    if "BlackHole 2ch" not in devices:
        raise SystemExit(
            "BlackHole 2ch not detected. "
            "Install BlackHole and restart Terminal."
        )

    with sync_playwright() as pw:
        browser = pw.chromium.launch_persistent_context(
            str(BASE / ".music_browser_profile"),
            headless=False,
            viewport={"width":720, "height":1280},
            record_video_dir=str(RAW),
            record_video_size={"width":720, "height":1280}
        )

        for old in browser.pages:
            old.close()

        for number in range(
            args.start, args.start + args.count
        ):
            target = OUT / f"music_{number:02d}.mp4"

            if target.exists():
                print("Already exists:", target)
                continue

            print(f"\nRecording session {number}")

            audio_file = RAW / f"music_{number:02d}.wav"
            full_file = RAW / f"music_{number:02d}_full.mp4"
            log_file = RAW / f"audio_{number:02d}.log"

            video_start = time.monotonic()
            page = browser.new_page()
            video = page.video

            audio_start = time.monotonic()
            played_at = None

            with log_file.open("wb") as log:
                proc = subprocess.Popen(
                    [
                        "ffmpeg", "-y",
                        "-hide_banner",
                        "-loglevel", "warning",
                        "-f", "avfoundation",
                        "-thread_queue_size", "1024",
                        "-i", ":BlackHole 2ch",
                        "-ar", "48000",
                        "-ac", "2",
                        "-c:a", "pcm_s16le",
                        str(audio_file)
                    ],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=log
                )

                try:
                    page.goto(
                        SITE,
                        wait_until="domcontentloaded",
                        timeout=60000
                    )
                    page.wait_for_timeout(4000)

                    choose_settings(
                        page,
                        random.Random(number),
                        PROMPTS[
                            (number - 1) % len(PROMPTS)
                        ]
                    )

                    print("Scrolling to bottom...")
                    scroll_bottom(page)

                    generate = page.get_by_role(
                        "button",
                        name=re.compile(
                            r"\b(generate|create music|make music)\b",
                            re.I
                        )
                    ).first

                    generate.scroll_into_view_if_needed()
                    generate.click(timeout=15000)

                    print("Clicked Generate")
                    print("Waiting for the music player...")

                    success = start_playback(
                        page, args.generate_timeout
                    )

                    if not success:
                        raise RuntimeError(
                            "Music player not found"
                        )

                    played_at = time.monotonic()
                    print("Recording actual playback...")

                    page.wait_for_timeout(
                        args.play_seconds * 1000
                    )

                except Exception as exc:
                    print("Recording error:", exc)
                    try:
                        page.screenshot(
                            path=str(
                                RAW / f"error_{number:02d}.png"
                            ),
                            full_page=True
                        )
                    except Exception:
                        pass

                finally:
                    page.close()
                    stop_ffmpeg(proc)

            if played_at is None:
                print("No completed clip. Check browser_raw.")
                continue

            if (
                proc.returncode != 0
                or not audio_file.exists()
                or audio_file.stat().st_size < 1024
            ):
                print("Audio recording failed:", log_file)
                continue

            # Align the separately captured audio
            # with the browser recording.
            offset = max(0, audio_start - video_start)

            subprocess.run([
                "ffmpeg", "-y", "-loglevel", "error",
                "-i", str(video.path()),
                "-itsoffset", f"{offset:.3f}",
                "-i", str(audio_file),
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                str(full_file)
            ], check=True)

            # Make the usable short start just
            # before the music begins playing.
            start_at = max(
                0, played_at - video_start - 2
            )

            subprocess.run([
                "ffmpeg", "-y", "-loglevel", "error",
                "-ss", f"{start_at:.2f}",
                "-i", str(full_file),
                "-t", str(args.play_seconds + 2),
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "23",
                "-c:a", "aac",
                "-b:a", "192k",
                "-movflags", "+faststart",
                str(target)
            ], check=True)

            print("SAVED:", target)

        browser.close()

if __name__ == "__main__":
    main()
