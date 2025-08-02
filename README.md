# Spotify Playlist Cover Downloader

A Python script that downloads cover images from your or others Spotify playlists. 
Downloads the highest resolution images available and saves them locally with the playlist name as the filename.

There are two scripts here. 

- [download_my_covers.py](./download_my_covers.py) downloads your playlist images. **Also the private ones!** 
- [download_public_covers.py](./download_public_covers.py) downloads anyone’s **public** playlist images. (takes spotify id as input)

## Features

- Downloads all private and public cover images from playlists you've created
- Downloads all cover images from anyone’s playlists
- Async implementation for fast concurrent downloads
- Sanitizes filenames for filesystem compatibility
- Easy configuration via TOML file

## Installation

### With uv

```shell
uv sync
```

### With pip

```shell
pip install spotipy requests pillow aiohttp asyncio
```

## Setup

0. **Clone the repo** `git clone git@github.com:tintin10q/spotify-playlist-cover-downloader.git` and open a shell in the directory of the repo

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
   python download_public_covers.py spotify_id
   ```
   or depending on if you want to download your own covers including the private ones:
   ```shell
   python download_my_covers.py 
   ```

The first run will open a browser for Spotify authentication. 
Paste the url you where directed to into the program
Subsequent runs use the stored token.

## What Gets Downloaded?

### download_my_covers.py
- Playlists you created (public and private)
- Collaborative playlists you own
- Does not download playlists created by others

### download_public_covers.py
- Public playlists owned by the specified user
- Does not access private playlists
- Only downloads playlists created by that user (not followed playlists)

## Output

Images are saved to a `playlist_covers/` directory:
```
📁 playlist_covers/
└── 📁 <spotify_id>
      ├── Playlist Name 1.jpg
      ├── Another Playlist.png
      └── Third Playlist.webp
```

## Configuration

The [download_my_covers.py](download_my_covers.py) script uses these [OAuth scopes](https://developer.spotify.com/documentation/web-api/concepts/scopes):
- `playlist-read-private` - Access to private playlists
- `playlist-read-collaborative` - Access to collaborative playlists

The other script does not need any OAuth scopes.

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
