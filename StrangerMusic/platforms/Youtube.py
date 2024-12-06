import asyncio
import json
import os
import time
import re
import glob
import random
from typing import Union

import aiohttp
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch

import config
from StrangerMusic.utils.database import is_on_off
from StrangerMusic.utils.formatters import time_to_seconds
from config import file_cache

async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, errorz = await proc.communicate()
    if errorz:
        if (
            "unavailable videos are hidden"
            in (errorz.decode("utf-8")).lower()
        ):
            return out.decode("utf-8")
        else:
            return errorz.decode("utf-8")
    return out.decode("utf-8")


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(
            r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])"
        )
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': 'https://tubed.okflix.top',
            'Referer': 'https://tubed.okflix.top/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Connection': 'keep-alive',
        }
        self._download_semaphore = asyncio.Semaphore(2)  # Reduced to 2 concurrent downloads

    async def exists(
        self, link: str, videoid: Union[bool, str] = None
    ):
        if videoid:
            link = self.base + link
        if re.search(self.regex, link):
            return True
        else:
            return False

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        text = ""
        offset = None
        length = None
        for message in messages:
            if offset:
                break
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        offset, length = entity.offset, entity.length

                        break
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        if offset in (None,):
            return None
        return text[offset : offset + length]

    async def details(
        self, link: str, videoid: Union[bool, str] = None
    ):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            vidid = result["id"]
            if str(duration_min) == "None":
                duration_sec = 0
            else:
                duration_sec = int(time_to_seconds(duration_min))
        return title, duration_min, duration_sec, thumbnail, vidid

    async def url_videoid(self, link: str):
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            vidid = result["id"]
        return vidid

    async def title(
        self, link: str, videoid: Union[bool, str] = None
    ):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
        return title

    async def duration(
        self, link: str, videoid: Union[bool, str] = None
    ):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            duration = result["duration"]
        return duration

    async def thumbnail(
        self, link: str, videoid: Union[bool, str] = None
    ):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        return thumbnail

    async def video(
        self, link: str, videoid: Union[bool, str] = None
    ):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        ytld_cmd = [
            "yt-dlp",
            "-g",
            "-f",
            "best[height<=?720][width<=?1280]",
            f"{link}",
        ]
        proc = await asyncio.create_subprocess_exec(
            *ytld_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if stdout:
            return 1, stdout.decode().split("\n")[0]
        else:
            return 0, stderr.decode()

    async def playlist(
        self, link, limit, user_id, videoid: Union[bool, str] = None
    ):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
        # playlist = await shell_cmd(
        #     f"yt-dlp -i --get-id --flat-playlist --cookies {cookie_txt_file()} --playlist-end {limit} --skip-download {link}"
        # )
        playlist = await shell_cmd(
            f"yt-dlp -i --compat-options no-youtube-unavailable-videos "
            f'--get-id --flat-playlist --playlist-end {limit} --skip-download "{link}" '
            f"2>/dev/null"
        )
        try:
            result = [key for key in playlist.split("\n") if key]
        except:
            result = []
        return result

    async def track(
        self, link: str, videoid: Union[bool, str] = None
    ):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            vidid = result["id"]
            yturl = result["link"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        track_details = {
            "title": title,
            "link": yturl,
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumbnail,
        }
        return track_details, vidid

    async def formats(
        self, link: str, videoid: Union[bool, str] = None
    ):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        ytdl_opts = {"quiet": True}
        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        with ydl:
            formats_available = []
            r = ydl.extract_info(link, download=False)
            for format in r["formats"]:
                try:
                    str(format["format"])
                except:
                    continue
                if not "dash" in str(format["format"]).lower():
                    try:
                        format["format"]
                        format["filesize"]
                        format["format_id"]
                        format["ext"]
                        format["format_note"]
                    except:
                        continue
                    formats_available.append(
                        {
                            "format": format["format"],
                            "filesize": format["filesize"],
                            "format_id": format["format_id"],
                            "ext": format["ext"],
                            "format_note": format["format_note"],
                            "yturl": link,
                        }
                    )
        return formats_available, link

    async def slider(
        self,
        link: str,
        query_type: int,
        videoid: Union[bool, str] = None,
    ):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        a = VideosSearch(link, limit=10)
        result = (await a.next()).get("result")
        title = result[query_type]["title"]
        duration_min = result[query_type]["duration"]
        vidid = result[query_type]["id"]
        thumbnail = result[query_type]["thumbnails"][0]["url"].split(
            "?"
        )[0]
        return title, duration_min, thumbnail, vidid

    async def download_from_tubed(self, link: str, title: str = None, max_retries: int = 3) -> tuple[str, bool]:
        """Download audio from tubed.okflix.top endpoint with retry logic"""
        try:
            download_url = f"https://tubed.okflix.top/{config.TUBED_API}/{link}.mp3"
            output_file = os.path.join("downloads", f"{link}.mp3")
            
            os.makedirs("downloads", exist_ok=True)
            
            if os.path.exists(output_file):
                file_cache[output_file] = time.time()  # Refresh cache time for existing file
                return output_file, True

            async with self._download_semaphore:
                for retry in range(max_retries):
                    try:
                        async with aiohttp.ClientSession(headers=self._headers) as session:
                            async with session.head(download_url) as head_response:
                                if head_response.status != 200:
                                    if retry < max_retries - 1:
                                        await asyncio.sleep(2 ** retry)
                                        continue
                                    return None, False

                            async with session.get(download_url) as response:
                                if response.status == 200:
                                    try:
                                        with open(output_file, "wb") as f:
                                            async for chunk in response.content.iter_chunked(8192):
                                                if not chunk:
                                                    break
                                                f.write(chunk)
                                        
                                        if os.path.getsize(output_file) > 0:
                                            file_cache[output_file] = time.time()   # Add new file to cache
                                            return output_file, True
                                        else:
                                            os.remove(output_file)
                                            if retry < max_retries - 1:
                                                await asyncio.sleep(2 ** retry)
                                                continue
                                            return None, False
                                    except Exception:
                                        if os.path.exists(output_file):
                                            os.remove(output_file)
                                        if retry < max_retries - 1:
                                            await asyncio.sleep(2 ** retry)
                                            continue
                                        return None, False
                    except aiohttp.ClientError:
                        if retry < max_retries - 1:
                            await asyncio.sleep(2 ** retry)
                            continue
                        return None, False

                return None, False

        except Exception:
            return None, False

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> str:
        """Main download method that uses tubed endpoint exclusively"""
        try:
            if video or songvideo:
                return None
            if not videoid:
                link  = await self.url_videoid(link)
            downloaded_file, success = await self.download_from_tubed(link, title)
            if success:
                return downloaded_file, True
            return None

        except Exception:
            return None
