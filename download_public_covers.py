import asyncio
import sys
from itertools import batched
from pathlib import Path

import aiofiles
import httpx
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
import re
import tomllib
from PIL import Image
from io import BytesIO

RATE_LIMIT = 20


def sanitize_filename(filename: str) -> str:
    """Remove or replace characters that are invalid in filenames"""
    # Replace invalid characters with underscores
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    # Limit length to avoid filesystem issues
    return filename[:200] if len(filename) > 200 else filename


def get_largest_image(images):
    """Get the URL of the largest image from Spotify's image array"""
    if not images:
        return None

    # Spotify returns images sorted by size (largest first), but let's be safe
    largest = max(images, key=lambda x: (x.get('width', 0) or 0) * (x.get('height', 0) or 0))
    return largest['url']


async def download_public_playlist_covers(client_id, client_secret, user_id, download_folder='playlist_covers'):
    """
    Download cover images for all public playlists of a given user

    Args:
        client_id: Your Spotify app client ID
        client_secret: Your Spotify app client secret
        user_id: Spotify user ID to download playlists from
        download_folder: Folder to save images (default: 'playlist_covers')
    """

    # Set up Spotify authentication (client credentials for public data)
    client_credentials_manager = SpotifyClientCredentials(
        client_id=client_id,
        client_secret=client_secret
    )
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)


    try:
        # Get user info
        try:
            user = sp.user(user_id)
            print(f"Fetching public playlists for user: {user['display_name']} ({user_id})")
        except Exception:
            print(f"Fetching public playlists for user: {user_id}")

        # Create download folder if it doesn't exist
        download_folder = Path(download_folder) / Path(user_id)
        os.makedirs(download_folder, exist_ok=True)

        # Get all public playlists for the user
        playlists = []
        results = sp.user_playlists(user_id, limit=50)

        while results:
            # Filter for public playlists only (API returns only public when using client credentials)
            playlists.extend(results['items'])
            if results['next']:
                results = sp.next(results)
            else:
                break

        # Filter for playlists owned by the specified user
        user_playlists = [p for p in playlists if p['owner']['id'] == user_id]

        print(f"Found {len(user_playlists)} public playlists")

        if not user_playlists:
            print("No public playlists found for this user")
            return

        successful_downloads = 0
        missing_covers = 0
        missing_url = 0

        async with httpx.AsyncClient() as client:
            async def download_playlist(playlist):
                nonlocal successful_downloads, missing_covers, missing_url
                playlist_name = playlist['name']
                images = playlist.get('images', [])

                if not images:
                    print(f"⚠️  No cover image for playlist: {playlist_name}")
                    missing_covers += 1
                    return

                # Get the largest image URL
                image_url = get_largest_image(images)
                if not image_url:
                    print(f"⚠️  Could not find image URL for playlist: {playlist_name}")
                    missing_url += 1
                    return

                try:
                    # Download the image
                    response = await client.get(image_url, timeout=30)
                    response.raise_for_status()

                    # Determine file extension from content type or URL
                    content_type = response.headers.get('content-type', '')
                    if 'jpeg' in content_type or 'jpg' in content_type:
                        ext = '.jpg'
                    elif 'png' in content_type:
                        ext = '.png'
                    elif 'webp' in content_type:
                        ext = '.webp'
                    else:
                        # Fallback to checking URL or default to jpg
                        if image_url.lower().endswith('.png'):
                            ext = '.png'
                        elif image_url.lower().endswith('.webp'):
                            ext = '.webp'
                        else:
                            ext = '.jpg'

                    # Create safe filename
                    safe_filename = Path(sanitize_filename(playlist_name) + ext)
                    filepath = download_folder / safe_filename

                    # Save the image
                    async with aiofiles.open(filepath, 'wb') as f:
                        await f.write(response.content)

                    # Get image dimensions for confirmation
                    img = Image.open(BytesIO(response.content))
                    width, height = img.size
                    print(f"✅ Downloaded: {playlist_name} ({width}x{height}) -> {safe_filename}")

                    successful_downloads += 1

                except httpx.RequestError as e:
                    print(f"❌ Failed to download {playlist_name}: {e}")
                except Exception as e:
                    print(f"❌ Error processing {playlist_name}: {e}")

            download_jobs = (download_playlist(playlist) for playlist in user_playlists)
            batched_download_jobs = batched(download_jobs, RATE_LIMIT)

            for batch in batched_download_jobs:
                await asyncio.gather(*batch)

        print(f"\n🎉 Download complete! {successful_downloads}/{len(user_playlists)} images downloaded successfully"
              f"{f', {missing_url} missing url' if missing_url else ''}"
              f"{f', {missing_covers} missing covers' if missing_covers else ''}.")
        print(f"Images saved to: {os.path.abspath(download_folder)}")

    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 404:
            print(f"❌ User '{user_id}' not found")
        else:
            print(f"❌ Spotify API error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
        raise


def load_credentials():
    """Load Spotify credentials from spotify_auth.toml file"""
    try:
        with open("spotify_auth.toml", "rb") as f:
            config = tomllib.load(f)

        client_id = config.get("client_id")
        client_secret = config.get("client_secret")

        if not client_id or not client_secret:
            raise ValueError("client_id and client_secret must be provided in spotify_auth.toml")

        return client_id, client_secret

    except FileNotFoundError:
        print("❌ spotify_auth.toml file not found!")
        print("\n📝 Please create a spotify_auth.toml file with the following format:")
        print("""
client_id = "your_client_id_here"
client_secret = "your_client_secret_here"
""")
        print("\n📝 Setup instructions:")
        print("1. Go to https://developer.spotify.com/dashboard")
        print("2. Create a new app")
        print("3. Copy the Client ID and Client Secret")
        print("4. Create the spotify_auth.toml file with your credentials")
        return None, None

    except tomllib.TOMLDecodeError as e:
        print(f"❌ Error reading spotify_auth.toml: {e}")
        return None, None

    except Exception as e:
        print(f"❌ Error loading credentials: {e}")
        return None, None


def main():
    """
    Main function - loads credentials from spotify_auth.toml and user ID from command line
    """

    # Check command line arguments
    if len(sys.argv) != 2:
        filename = Path(sys.argv[0]).name
        print("You did not give me a spotify user id. Whose covers should I download?")
        print("Get someones id by going to their profile and click share.")
        print("The id is the last part of the link: https://open.spotify.com/user/<id_here> (ignore the ?si=.... part)\n")
        print(f"Usage: python {filename} <spotify_user_id>")
        print("\nExample:")
        print(f"  python {filename} spotify")
        print(f"  python {filename} 1234567890")
        sys.exit(1)

    user_id = sys.argv[1]

    client_id, client_secret = load_credentials()

    if not client_id or not client_secret:
        return

    asyncio.run(download_public_playlist_covers(client_id, client_secret, user_id))


if __name__ == "__main__":
    main()