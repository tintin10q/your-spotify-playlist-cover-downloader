# Spotify Playlist Cover Downloader

A Python script that downloads cover images from your Spotify playlists. 
Do you want to download the covers from someone else’s playlist? See []()
Downloads the highest resolution images available and saves them locally with the playlist name as the filename.

## Features

- Downloads cover images from playlists you've created
- Async implementation for concurrent downloads
- Batched downloads to respect rate limits
- Handles both your private and public playlists
- Sanitizes filenames for filesystem compatibility
- Supports JPG, PNG, and WebP formats
- Configuration via TOML `spotify_auth.toml` file

## Installation

### uv

```shell
uv sync
```

### pip 

```shell
pip install spotipy requests pillow aiohttp asyncio
```

## Setup

0. Clone the repo and open a shell in the directory of the repo

1. **Create a Spotify App**
   - Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Create a new app
   - Add `http://localhost:8888/callback` as a redirect URI
   - Note your Client ID and Client Secret

2. **Create Configuration File**
   
   Create `spotify_auth.toml` in the same directory:
   ```toml
   client_id = "your_client_id"
   client_secret = "your_client_secret"
   redirect_uri = "http://localhost:8888/callback"  # optional
   ```

3. **Run**
   ```shell
    python download_my_covers.py
   ```
   or with uv
     ```shell
    uv run python download_my_covers.py
     ```
   
The first run will open a browser for Spotify authentication. 
Paste the resulting url into the program.
Subsequent runs use the stored token in `.cache`.

## What It Downloads

- Playlists you created (public and private)
- Collaborative playlists you own
- Does not download playlists created by others

## Output

Images are saved to a `playlist_covers/` directory:
```
playlist_covers/
├── Playlist Name 1.jpg
├── Another Playlist.png
└── Third Playlist.webp
```

## Configuration

The script uses these [OAuth scopes](https://developer.spotify.com/documentation/web-api/concepts/scopes):

- `playlist-read-private` - Access to private playlists
- `playlist-read-collaborative` - Access to collaborative playlists

## Troubleshooting

**File not found error**
- Ensure `spotify_auth.toml` is in the same directory as the script

**Authentication errors**
- Verify Client ID and Secret are correct from the [dashboard](https://developer.spotify.com/dashboard)
- Check that redirect URI is added to your Spotify app settings

**No playlists found**
- Script only downloads playlists you own, not playlists you follow

## Requirements

- Python 3.13+ (earlier will probably work idk)
- Spotify account (free or premium)
- Spotify Developer app credentials

## License

MIT License