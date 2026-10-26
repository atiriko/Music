# Deploy Music Studio to music.loomwork.com

The Docker image serves the existing web interface using nginx on port **43729**.
Music generation, MIDI, playback, WAV rendering, and SF2 imports run in the
visitor's browser. The image includes Pyodide, NumPy, and all bundled sounds.
No Python API, external synthesizer, database, or instrument download is needed
at runtime. The build needs internet access to install dependencies and fetch
the checksum-verified NumPy WebAssembly package.

## Coolify: Dockerfile from a Git repository

1. Commit and push the application source, the new Docker/deployment files, and
   the instrument assets. Coolify builds the checked-out repository; local
   uncommitted files are not included.
2. In your Coolify project, add an application from that repository and branch.
   Select the **Dockerfile** build strategy.
3. Set **Base Directory / Repository root** to `/`, **Dockerfile Location** to
   `/Dockerfile`, and **Ports Exposes** to `43729`.
   Keep the repository root as the build context: `mobile/` alone does not
   contain the shared Python modules or instrument sources.
4. Point the `music` DNS **A** record in `loomwork.com` to your Coolify server's
   public IPv4 address. Add an AAAA record only if that server also has working
   public IPv6. The proxy needs public HTTP/HTTPS access for routing and TLS.
5. In **Domains**, add HTTPS for **music.loomwork.com**, targeting internal port
   **43729**, with no path prefix. Older Coolify versions use the combined value
   `https://music.loomwork.com:43729`; the public URL remains
   `https://music.loomwork.com`, without `:43729`.
6. Deploy. The image provides its own Docker health check at `/healthz`.
   No environment variables, persistent volumes, or host-port mappings are
   required for this Dockerfile deployment. Coolify handles public HTTPS.
7. Open `https://music.loomwork.com`, generate and play a section, then test MIDI
   and WAV export. Audio starts after a user tap/click. HTTPS is required for
   browser audio worklets outside localhost.

Coolify's current documentation: [Dockerfile builds](https://coolify.io/docs/applications/builds/dockerfile),
[domains](https://coolify.io/docs/core/networking/domains), and
[health checks](https://coolify.io/docs/applications/configuration/health-checks).

## Run locally

From the repository root:

```sh
docker compose up --build -d
```

Open **http://localhost:43729**. Localhost is a browser secure-context exception,
so browser audio can run over local HTTP. Use HTTPS when accessing a remote
server; a plain server-IP URL is unsuitable for audio worklets.

To change the local host port, set `MUSIC_PORT`, for example:

```sh
MUSIC_PORT=43739 docker compose up --build -d
```

The supplied Compose file is a local convenience. For Coolify, the Dockerfile
workflow above avoids exposing a host port alongside its reverse proxy.

```sh
docker compose ps
docker compose logs --tail=100 music
docker compose exec music nginx -t
docker compose down
```

## Storage and updates

Saved projects and imported instruments live in the user's browser storage,
scoped to `https://music.loomwork.com`. They are not sent to this server and do
not automatically sync across devices, browser profiles, or domains. Clearing
site data removes those local copies. Users can export song projects and WAV/MIDI
files; original imported SF2 files are needed when moving projects to another
device. Server redeployments do not clear browser storage.

The container runs nginx as an unprivileged user. It logs to stdout/stderr,
precompresses large assets at build time, caches hashed assets indefinitely,
and revalidates workers/runtime/banks so future deployments can update them.
Missing static assets return 404 rather than the SPA page. Same-origin isolation
headers are included; all application runtime assets are served from this host.

## Deployment checks

With the container running and mobile development dependencies installed:

```sh
cd mobile
npx playwright test --config playwright.web.config.ts
```

The deployment suite checks the actual HTTP server, headers, compression,
WebAssembly MIME type, missing-asset behaviour, and generated audio/MIDI flows.
Set `MUSIC_WEB_URL` to test a different local container port or a deployed URL.
