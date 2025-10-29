# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.12.10
FROM python:${PYTHON_VERSION}-slim as base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV NLTK_DATA=/usr/share/nltk_data

WORKDIR /app

# Create a non-privileged user with a real home directory
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/home/appuser" \
    --shell "/bin/bash" \
    --uid "${UID}" \
    appuser \
    && mkdir -p /home/appuser \
    && chown appuser:appuser /home/appuser

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

# Install additional packages
RUN pip install --no-cache-dir sentence-transformers pdfplumber==0.11.4 nltk textblob

# Download NLTK data to system-wide directory
RUN python -m nltk.downloader -d /usr/share/nltk_data punkt punkt_tab wordnet averaged_perceptron_tagger

# Switch to non-privileged user
USER appuser

COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
