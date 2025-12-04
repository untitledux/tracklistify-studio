# Tracklistify

Tracklistify is a command-line tool that identifies tracks in DJ mixes or streaming URLs and exports the result in multiple playlist formats. It coordinates Shazam and ACRCloud lookups, manages downloads via `yt-dlp`, and writes outputs to Markdown, JSON, or M3U while handling caching, retries, and rate limits for you.

![Tracklistify banner](docs/assets/banner.png)

## Features
- Uses multiple providers with optional fallback so failed lookups can automatically retry on another service.
- Supports local files or streaming URLs handled by `yt-dlp` downloads.
- Exports tracklists as Markdown, JSON, or M3U playlists in a configurable output directory.
- Async processing with configurable rate limiting, retries, and circuit breaking to protect provider APIs.
- Detailed logging with optional file output for troubleshooting long batch runs.

## Requirements
- Python 3.11–3.13
- `ffmpeg`
- `git`
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) for dependency management

## Installation
```bash
# Clone the repository
git clone https://github.com/betmoar/tracklistify.git
cd tracklistify

# Install dependencies
uv sync
```

## Configuration
Copy the example environment file and adjust values for your environment and providers:

```bash
cp .env.example .env
```

Key settings (all prefixed with `TRACKLISTIFY_`):
- Output paths such as `OUTPUT_DIR`, `CACHE_DIR`, `TEMP_DIR`, and `LOG_DIR` control where results are written.
- Provider credentials and timeouts (e.g., `ACR_ACCESS_KEY`, `ACR_ACCESS_SECRET`, `SHAZAM_TIMEOUT`, `SPOTIFY_CLIENT_ID`).
- Behavior toggles such as `FALLBACK_ENABLED`, rate limit values, retry strategy, and download quality/format.

## Usage
Run the CLI with a local file path or a supported URL:

```bash
uv run tracklistify <input>
```

Common flags:
- `-f, --formats {json,markdown,m3u,all}`: choose output formats (default: `all`).
- `-p, --provider`: select a primary identification provider (e.g., `shazam`).
- `--no-fallback`: disable provider fallback.
- `--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}` and `--log-file PATH`: control logging.
- `-d/--debug` and `-v/--verbose`: increase diagnostic output.

Outputs and cache files default to the directories defined in your `.env` file (e.g., `.tracklistify/output`).

## Development
- Run tests: `uv run pytest`
- Lint with Ruff: `uv run ruff check`
- Format with Ruff: `uv run ruff format`

Contributions are welcome. See `docs/CONTRIBUTING.md` for guidelines.

## License
MIT License. See `LICENSE` for details.
