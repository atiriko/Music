# syntax=docker/dockerfile:1
# The shared Python engine runs inside Pyodide in the visitor's browser.
# Python and Node are build tools; the production image only serves static files.
FROM node:24-bookworm-slim AS build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 \
    PATH="/opt/venv/bin:$PATH"

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates python3 python3-venv \
    && python3 -m venv /opt/venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY mobile/requirements-build.txt /tmp/requirements-build.txt
RUN pip install --no-cache-dir -r /tmp/requirements-build.txt

# Install from the lockfile before copying application sources for layer caching.
COPY mobile/package.json mobile/package-lock.json ./mobile/
RUN cd mobile && npm ci --no-audit --no-fund

COPY . .
WORKDIR /build/mobile
RUN npm run build:web \
    && test -s dist/privacy.html \
    && test -s dist/privacy.css \
    && python /build/deploy/precompress.py /build/mobile/dist

FROM nginx:stable-alpine AS runtime

COPY deploy/nginx.conf /etc/nginx/nginx.conf
COPY --from=build /build/mobile/dist /usr/share/nginx/html

# Custom nginx paths are writable in /tmp; serving does not require root.
USER nginx
EXPOSE 43729

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1:43729/healthz || exit 1

ENTRYPOINT ["nginx"]
CMD ["-g", "daemon off;"]
