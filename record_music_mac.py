from pathlib import Path
from playwright.sync_api import sync_playwright
import argparse, json, queue, random, re, shutil, subprocess, threading, time, wave

BASE = Path(__file__).resolve().parent
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

# These overlays are part of the page, so Playwright includes them in the video.
POINTER_SCRIPT = r"""
(() => {
    const install = () => {
        if (document.getElementById('__recorder_overlay')) return;
        const host = document.createElement('div');
        host.id = '__recorder_overlay';
        host.style.cssText = 'position:fixed;inset:0;z-index:2147483647;pointer-events:none';
        const root = host.attachShadow({mode: 'open'});
        root.innerHTML = `<style>
            * { box-sizing: border-box; }
            #pointer { position:fixed; width:24px; height:24px; border:3px solid white;
                border-radius:50%; background:#ff3d71; box-shadow:0 0 0 3px #2228;
                transform:translate(-50%,-50%); display:none; }
            #label { position:fixed; top:16px; left:16px; max-width:calc(100vw - 32px);
                padding:10px 16px; border-radius:10px; background:#161b22ed;
                color:white; font:600 17px/1.4 system-ui; }
            #focus { position:fixed; border:3px solid #ff3d71; border-radius:6px;
                box-shadow:0 0 0 3px #fff9; display:none; }
            .pulse { position:fixed; width:24px; height:24px; border:4px solid #ff3d71;
                border-radius:50%; animation:pulse .55s ease-out forwards; }
            @keyframes pulse { from { transform:translate(-50%,-50%) scale(1); opacity:1; }
                to { transform:translate(-50%,-50%) scale(3.5); opacity:0; } }
        </style><div id="focus"></div><div id="pointer"></div>
        <div id="label">Preparing music settings</div>`;
        document.documentElement.appendChild(host);
        const pointer = root.querySelector('#pointer');
        const focus = root.querySelector('#focus');
        document.addEventListener('mousemove', e => {
            pointer.style.display = 'block';
            pointer.style.left = e.clientX + 'px';
            pointer.style.top = e.clientY + 'px';
        }, true);
        document.addEventListener('pointerdown', e => {
            const pulse = document.createElement('div');
            pulse.className = 'pulse';
            pulse.style.left = e.clientX + 'px';
            pulse.style.top = e.clientY + 'px';
            root.appendChild(pulse);
            setTimeout(() => pulse.remove(), 600);
        }, true);
        document.addEventListener('scroll', () => focus.style.display = 'none', true);
        window.__recordingAction = (text, box) => {
            const label = root.querySelector('#label');
            label.textContent = text;
            const nearTop = box && box.y < 100;
            label.style.top = nearTop ? 'auto' : '16px';
            label.style.bottom = nearTop ? '16px' : 'auto';
            focus.style.display = box ? 'block' : 'none';
            if (box) Object.assign(focus.style, {
                left: (box.x - 4) + 'px', top: (box.y - 4) + 'px',
                width: (box.width + 8) + 'px', height: (box.height + 8) + 'px'
            });
        };
    };
    if (document.documentElement) install();
    else document.addEventListener('DOMContentLoaded', install, {once:true});
})();
"""


def show_action(page, text, element=None, delay_ms=0):
    box = None
    if element is not None:
        element.scroll_into_view_if_needed()
        box = element.bounding_box()
        if box:
            page.mouse.move(box['x'] + box['width'] / 2,
                            box['y'] + box['height'] / 2)
    page.evaluate("([text, box]) => window.__recordingAction(text, box)", [text, box])
    print(text)
    # Allow at least one video frame to capture the highlight before acting.
    page.wait_for_timeout(max(100, delay_ms))


def control_name(el):
    return el.evaluate("""e => e.getAttribute('aria-label') ||
        (e.labels && Array.from(e.labels, l => {
            const label = l.cloneNode(true);
            label.querySelectorAll('input,select,textarea,button').forEach(n => n.remove());
            return label.textContent.trim();
        }).join(' ')) ||
        e.getAttribute('placeholder') || e.name || e.id || 'setting'""")


def scroll_bottom(page):
    page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")


def choose_settings(page, rng, prompt, delay_ms=250):
    for el in page.locator('textarea:visible, input[type="text"]:visible').all():
        hint = " ".join([el.get_attribute("placeholder") or "",
                         el.get_attribute("aria-label") or ""]).lower()
        if any(x in hint for x in ("search", "email", "username", "login")):
            continue
        try:
            show_action(page, "Enter music description", el, delay_ms)
            el.fill(prompt)
            page.wait_for_timeout(delay_ms)
            break
        except Exception as exc:
            print("Could not fill description:", exc)

    for el in page.locator("select:visible").all():
        try:
            choices = el.locator("option").evaluate_all(
                "xs => xs.filter(x => !x.disabled && x.value).map(x => ({value:x.value, label:x.textContent.trim()}))"
            )
            if choices:
                choice = rng.choice(choices)
                show_action(page, f"{control_name(el)}: {choice['label']}", el, delay_ms)
                el.select_option(choice['value'])
                page.wait_for_timeout(delay_ms)
        except Exception as exc:
            print("Could not select setting:", exc)

    groups = {}
    for el in page.locator('input[type="radio"]:visible').all():
        name = el.get_attribute("name")
        if name:
            groups.setdefault(name, []).append(el)
    for group in groups.values():
        try:
            chosen = rng.choice(group)
            show_action(page, f"Select {control_name(chosen)}", chosen, delay_ms)
            chosen.check(timeout=2000)
            page.wait_for_timeout(delay_ms)
        except Exception as exc:
            print("Could not select radio setting:", exc)

    for el in page.locator('input[type="range"]:visible').all():
        try:
            lo, hi, step = el.evaluate(
                "e => [Number(e.min||0), Number(e.max||100), Number(e.step||1)]"
            )
            step = step or 1
            value = lo + rng.randint(0, max(0, int((hi-lo)/step))) * step
            show_action(page, f"{control_name(el)}: {value:g}", el, delay_ms)
            el.evaluate("""(e, v) => {
                const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
                setter.call(e, String(v));
                e.dispatchEvent(new Event('input', {bubbles:true}));
                e.dispatchEvent(new Event('change', {bubbles:true}));
            }""", value)
            page.wait_for_timeout(delay_ms)
        except Exception as exc:
            print("Could not adjust slider:", exc)

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
                    show_action(page, "Play music", button, 150)
                    button.click(timeout=3000)
                    print("Clicked Play")
                    return True
            except Exception:
                pass

        for audio in page.locator("audio").all():
            try:
                show_action(page, "Play music")
                audio.evaluate("(a) => a.play()")
                print("Started HTML audio player")
                return True
            except Exception:
                pass

        page.wait_for_timeout(500)

    return False

def blackhole_input():
    try:
        import sounddevice as sd
    except ImportError:
        raise SystemExit("Install the audio capture dependency: python3 -m pip install sounddevice")
    for index, device in enumerate(sd.query_devices()):
        if "BlackHole 2ch" in device["name"] and device["max_input_channels"] >= 2:
            return index, int(device["default_samplerate"])
    raise SystemExit("BlackHole 2ch not detected. Install BlackHole and restart Terminal.")


class BlackHoleRecorder:
    """Keep native CoreAudio sample buffers intact, with disk I/O off the callback."""

    def __init__(self, path, device, log_path):
        self.path = Path(path)
        self.device, self.rate = device
        self.log_path = Path(log_path)
        self.buffers = queue.SimpleQueue()
        self.ready = threading.Event()
        self.error = None
        self.statuses = []
        self.frames = 0
        self.stream = None
        self.writer = None

    def _callback(self, data, frames, timing, status):
        if status:
            self.statuses.append(str(status))
        self.buffers.put(bytes(data))

    def _write(self):
        try:
            with self.path.open("wb") as file:
                with wave.open(file, "wb") as wav:
                    wav.setnchannels(2)
                    wav.setsampwidth(2)
                    wav.setframerate(self.rate)
                    while True:
                        data = self.buffers.get()
                        if data is None:
                            break
                        wav.writeframesraw(data)
                        self.frames += len(data) // 4
                        if not self.ready.is_set():
                            file.flush()
                            self.ready.set()
        except Exception as exc:
            self.error = f"Could not write audio: {exc}"
            self.ready.set()

    def __enter__(self):
        import sounddevice as sd
        self.writer = threading.Thread(target=self._write, name="audio-writer", daemon=True)
        self.writer.start()
        try:
            self.stream = sd.RawInputStream(
                device=self.device, samplerate=self.rate, channels=2,
                dtype="int16", blocksize=0, latency="high", callback=self._callback
            )
            self.stream.start()
            if not self.ready.wait(timeout=15):
                raise RuntimeError("BlackHole audio capture did not become ready")
            if self.error:
                raise RuntimeError(self.error)
        except Exception as exc:
            if not self.error:
                self.error = str(exc)
            self.__exit__(None, None, None)
            raise
        return self

    def __exit__(self, exc_type, exc, traceback):
        try:
            if self.stream is not None:
                try:
                    self.stream.stop()
                finally:
                    self.stream.close()
        finally:
            self.buffers.put(None)
            if self.writer is not None:
                self.writer.join()
            if self.statuses:
                self.error = "Audio input lost samples: " + "; ".join(self.statuses)
            self.log_path.write_text((self.error or "Capture completed without input overflows") + "\n")


def sync_marker(page):
    # A shared physical event measures capture latency instead of guessing it
    # from subprocess startup. Both calibration screens are excluded from export.
    page.goto("about:blank")
    stamp = page.evaluate("""async () => {
        document.documentElement.style.background = '#000';
        const overlay = document.getElementById('__recorder_overlay');
        if (overlay) overlay.style.visibility = 'hidden';
        const context = new AudioContext();
        await context.resume();
        const oscillator = context.createOscillator();
        const gain = context.createGain();
        oscillator.frequency.value = 997;
        gain.gain.value = 0.35;
        oscillator.connect(gain).connect(context.destination);
        const start = context.currentTime + 0.15;
        oscillator.start(start);
        oscillator.stop(start + 0.4);
        const stamp = await new Promise(resolve => {
            const frame = () => {
                if (context.currentTime < start) return requestAnimationFrame(frame);
                document.documentElement.style.background = '#00ff00';
                resolve(performance.timeOrigin + performance.now());
            };
            requestAnimationFrame(frame);
        });
        await new Promise(resolve => setTimeout(resolve, 400));
        document.documentElement.style.background = '#000';
        await new Promise(resolve => setTimeout(resolve, 200));
        await context.close();
        return stamp;
    }""")
    # Convert the browser's wall clock timestamp to Python's monotonic clock.
    return stamp / 1000 + (time.monotonic() - time.time())


def _runs(mask, minimum):
    import numpy as np
    edges = np.diff(np.r_[False, mask, False].astype(int))
    starts = np.flatnonzero(edges == 1)
    ends = np.flatnonzero(edges == -1)
    return [(int(a), int(b)) for a, b in zip(starts, ends) if b - a >= minimum]


def measure_sync(video_file, audio_file):
    import numpy as np
    # Playwright records at 25 fps. Resampling explicitly makes the decoded
    # sample index a timestamp, even if input frames have irregular timestamps.
    pixels = subprocess.check_output([
        "ffmpeg", "-v", "error", "-i", str(video_file), "-an",
        "-vf", "fps=25,scale=1:1", "-pix_fmt", "rgb24", "-f", "rawvideo", "-"
    ])
    colors = np.frombuffer(pixels, dtype=np.uint8).reshape(-1, 3)
    green = (colors[:, 1] > 200) & (colors[:, 0] < 40) & (colors[:, 2] < 40)
    video_marks = _runs(green, 5)
    with wave.open(str(audio_file), "rb") as wav:
        if wav.getsampwidth() != 2:
            raise RuntimeError("Sync measurement requires 16-bit PCM audio")
        rate, channels = wav.getframerate(), wav.getnchannels()
        samples = np.frombuffer(wav.readframes(wav.getnframes()), dtype='<i2')
    mono = samples.reshape(-1, channels).astype(np.float32).mean(axis=1) / 32768
    size = int(rate * 0.02)
    blocks = mono[:len(mono) // size * size].reshape(-1, size)
    reference = np.exp(-2j * np.pi * 997 * np.arange(size) / rate)
    strength = np.abs(blocks @ reference) * 2 / size
    # Allow for the user's output volume; calibration is near each end.
    edge_blocks = max(1, int(3 * rate / size))
    peak = min(strength[:edge_blocks].max(initial=0),
               strength[-edge_blocks:].max(initial=0))
    audio_marks = _runs(strength > max(0.01, peak * 0.4), 10)
    if len(video_marks) != 2 or len(audio_marks) < 2:
        raise RuntimeError("Sync markers missing. Check that browser audio is routed to BlackHole 2ch.")
    v0, v1 = video_marks[0][0] / 25, video_marks[-1][0] / 25
    a0, a1 = audio_marks[0][0] * size / rate, audio_marks[-1][0] * size / rate
    speed = (a1 - a0) / (v1 - v0)
    if not 0.95 <= speed <= 1.05:
        raise RuntimeError(f"Capture clocks disagree by too much ({speed:.4f}); raw files kept")
    return {"offset": v0 - a0 / speed, "audio_speed": speed,
            "video_marker": v0, "video_marker_end": video_marks[0][1] / 25,
            "video_end_marker": v1, "video_duration": len(colors) / 25}


def export_recording(video_file, audio_file, full_file, target, offset,
                     generate_seconds, play_seconds_start, duration,
                     audio_speed=1.0, intro_min=0.0, video_duration=None):
    partial_target = target.with_name(target.stem + ".partial.mp4")
    # Normalize audio onto the video timeline BEFORE making cuts. Explicit
    # silence preserves alignment when a cut starts before audio capture did.
    audio_filters = ["asetpts=PTS-STARTPTS", f"atempo={audio_speed:.9f}"]
    if offset >= 0:
        audio_filters.append(f"adelay={offset * 1000:.3f}:all=1")
    else:
        audio_filters.extend([f"atrim=start={-offset:.6f}", "asetpts=PTS-STARTPTS"])
    if video_duration is not None:
        audio_filters.append(f"apad=whole_dur={video_duration:.6f}")
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(video_file), "-i", str(audio_file),
        "-map", "0:v:0", "-map", "1:a:0",
        "-af", ",".join(audio_filters),
        "-c:v", "copy", "-c:a", "pcm_s16le",
        *(["-t", f"{video_duration:.6f}"] if video_duration is not None else []),
        str(full_file)
    ], check=True)

    # Show the last 30 seconds of settings,
    # then jump directly to music playback.
    intro_end = max(
        1.0, generate_seconds + 1
    )
    intro_start = max(intro_min, intro_end - 30)
    play_start = max(
        0, play_seconds_start - 2
    )

    filters = (
        f"[0:v]trim=start={intro_start:.3f}:"
        f"end={intro_end:.3f},"
        "setpts=PTS-STARTPTS[v0];"
        f"[0:a]atrim=start={intro_start:.3f}:"
        f"end={intro_end:.3f},"
        "asetpts=PTS-STARTPTS[a0];"
        f"[0:v]trim=start={play_start:.3f}:"
        f"duration={duration + 2},"
        "setpts=PTS-STARTPTS[v1];"
        f"[0:a]atrim=start={play_start:.3f}:"
        f"duration={duration + 2},"
        "asetpts=PTS-STARTPTS[a1];"
        "[v0][a0][v1][a1]"
        "concat=n=2:v=1:a=1[v][a]"
    )

    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(full_file),
        "-filter_complex", filters,
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        str(partial_target)
    ], check=True)

    partial_target.replace(target)


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
    parser.add_argument(
        "--setting-delay", type=float, default=0.25,
        help="Pause before and after each setting change, in seconds (default: 0.25)"
    )
    parser.add_argument(
        "--settings-preview", type=float, default=1.0,
        help="Hold the settings before Generate, in seconds (default: 1)"
    )
    args = parser.parse_args()
    if args.count < 1 or args.start < 1 or args.play_seconds <= 0 or args.generate_timeout <= 0:
        parser.error("start, count, play-seconds, and generate-timeout must be positive")
    if args.setting_delay < 0 or args.settings_preview < 0:
        parser.error("setting-delay and settings-preview cannot be negative")

    if not shutil.which("ffmpeg"):
        raise SystemExit("Install ffmpeg with brew first")

    audio_device = blackhole_input()

    with sync_playwright() as pw:
        browser = pw.chromium.launch_persistent_context(
            str(BASE / ".music_browser_profile"),
            headless=False,
            args=["--autoplay-policy=no-user-gesture-required"],
            viewport={"width":720, "height":1280},
            record_video_dir=str(RAW),
            record_video_size={"width":720, "height":1280}
        )

        browser.add_init_script(POINTER_SCRIPT)

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
            full_file = RAW / f"music_{number:02d}_full.mkv"
            log_file = RAW / f"audio_{number:02d}.log"

            page = browser.new_page()
            video = page.video

            marker_time = None
            played_at = None
            generate_at = None
            completed = False

            with BlackHoleRecorder(audio_file, audio_device, log_file) as capture:
                try:
                    print("Waiting for audio capture, then measuring sync...")
                    marker_time = sync_marker(page)
                    page.goto(
                        SITE,
                        wait_until="domcontentloaded",
                        timeout=60000
                    )
                    page.get_by_role(
                        "button", name=re.compile(r"\b(generate|create music|make music)\b", re.I)
                    ).first.wait_for(state="visible", timeout=30000)

                    choose_settings(
                        page,
                        random.Random(number),
                        PROMPTS[
                            (number - 1) % len(PROMPTS)
                        ],
                        delay_ms=int(args.setting_delay * 1000)
                    )

                    show_action(page, "Settings ready")
                    page.wait_for_timeout(args.settings_preview * 1000)

                    generate = page.get_by_role(
                        "button",
                        name=re.compile(
                            r"\b(generate|create music|make music)\b",
                            re.I
                        )
                    ).first

                    show_action(page, "Generate music", generate, 250)
                    generate_at = time.monotonic()
                    generate.click(timeout=15000)

                    print("Clicked Generate")
                    show_action(page, "Generating music — waiting for the player")

                    success = start_playback(
                        page, args.generate_timeout
                    )

                    if not success:
                        raise RuntimeError(
                            "Music player not found"
                        )

                    played_at = time.monotonic()
                    show_action(page, "Recording music playback")

                    page.wait_for_timeout(
                        args.play_seconds * 1000
                    )
                    sync_marker(page)
                    completed = True

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

            if not completed:
                print("No completed clip. Check browser_raw.")
                continue

            if (
                capture.error
                or not audio_file.exists()
                or audio_file.stat().st_size < 1024
            ):
                print("Audio recording failed:", log_file)
                continue

            try:
                sync = measure_sync(video.path(), audio_file)
                video_origin = marker_time - sync["video_marker"]
                metadata = dict(sync, video_file=str(video.path()),
                                generate_seconds=generate_at - video_origin,
                                play_seconds_start=played_at - video_origin,
                                duration=args.play_seconds)
                (RAW / f"music_{number:02d}_sync.json").write_text(json.dumps(metadata, indent=2))
                print(f"Measured audio offset: {sync['offset']:+.3f}s; clock ratio: {sync['audio_speed']:.6f}")
                export_recording(
                    video.path(), audio_file, full_file, target, sync["offset"],
                    metadata["generate_seconds"], metadata["play_seconds_start"],
                    args.play_seconds, audio_speed=sync["audio_speed"],
                    intro_min=sync["video_marker_end"] + 0.25,
                    video_duration=sync["video_duration"]
                )
            except (subprocess.CalledProcessError, RuntimeError) as exc:
                print(f"Export failed: {exc}. Raw recordings kept in {RAW}")
                continue

            print("SAVED:", target)

        browser.close()

if __name__ == "__main__":
    main()
