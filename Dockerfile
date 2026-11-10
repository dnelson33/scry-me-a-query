FROM python:3.13-slim-bookworm AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build
COPY requirements.txt ./
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt


FROM python:3.13-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

RUN groupadd --system app \
    && useradd --system --gid app --create-home --home-dir /home/app app

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=app:app main.py http_client.py ./
COPY --chown=app:app bot ./bot
COPY --chown=app:app scryfall ./scryfall
COPY --chown=app:app edhrec ./edhrec
COPY --chown=app:app image_utils ./image_utils
COPY --chown=app:app assets ./assets

USER app

# discord.py's run loop turns SIGINT into a graceful gateway close. Docker's
# default is SIGTERM, which would terminate the process without cleanup.
STOPSIGNAL SIGINT

CMD ["python", "main.py"]
