

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, Message

import config
from config import BANNED_USERS
from strings import get_command
from StrangerMusic import YouTube, app
from StrangerMusic.core.call import Stranger
from StrangerMusic.misc import db
from StrangerMusic.utils.database import get_loop
from StrangerMusic.utils.decorators import AdminRightsCheck
from StrangerMusic.utils.inline.play import (stream_markup,
                                          telegram_markup)
from StrangerMusic.utils.thumbnails import gen_thumb
from config import autoclean

# Commands
SKIP_COMMAND = get_command("SKIP_COMMAND")


@app.on_message(
    filters.command(SKIP_COMMAND)
    & filters.group
    & ~BANNED_USERS
)
@AdminRightsCheck
async def skip(cli, message: Message, _, chat_id):
    if not len(message.command) < 2:
        loop = await get_loop(chat_id)
        if loop != 0:
            return await message.reply_text(_["admin_12"])
        state = message.text.split(None, 1)[1].strip()
        if state.isnumeric():
            state = int(state)
            check = db.get(chat_id)
            if check:
                count = len(check)
                if count > 2:
                    count = int(count - 1)
                    if 1 <= state <= count:
                        for x in range(state):
                            popped = None
                            try:
                                popped = check.pop(0)
                            except:
                                return await message.reply_text(
                                    _["admin_16"]
                                )
                            if popped:
                                if config.AUTO_DOWNLOADS_CLEAR == str(True):
                                    rem = popped["file"]
                                    autoclean.remove(rem)
                            if not check:
                                try:
                                    await message.reply_text(
                                        _["admin_10"].format(
                                            message.from_user.first_name,message.chat.title
                                        )
                                    )
                                    await Stranger.stop_stream(chat_id)
                                except:
                                    return
                                break
                    else:
                        return await message.reply_text(
                            _["admin_15"].format(count)
                        )
                else:
                    return await message.reply_text(_["admin_14"])
            else:
                return await message.reply_text(_["queue_2"])
        else:
            return await message.reply_text(_["admin_13"])
    else:
        check = db.get(chat_id)
        popped = None
        try:
            popped = check.pop(0)
            if popped:
                if config.AUTO_DOWNLOADS_CLEAR == str(True):
                    rem = popped["file"]
                    autoclean.remove(rem)
            if not check:
                await message.reply_text(
                    _["admin_10"].format(message.from_user.first_name,message.chat.title)
                )
                try:
                    return await Stranger.stop_stream(chat_id)
                except:
                    return
        except:
            try:
                await message.reply_text(
                    _["admin_10"].format(message.from_user.first_name,message.chat.title)
                )
                return await Stranger.stop_stream(chat_id)
            except:
                return
    queued = check[0]["file"]
    title = (check[0]["title"]).title()
    user = check[0]["by"]
    user_idd=check[0]["user_id"]
    streamtype = check[0]["streamtype"]
    videoid = check[0]["vidid"]
    status = True if str(streamtype) == "video" else None
    if "live_" in queued:
        n, link = await YouTube.video(videoid, True)
        if n == 0:
            return await message.reply_text(
                _["admin_11"].format(title)
            )
        try:
            await Stranger.skip_stream(chat_id, link, video=status)
        except Exception:
            return await message.reply_text(_["call_9"])
        button = telegram_markup(_, chat_id)
        img = await gen_thumb(videoid,user_idd)
        run = await message.reply_photo(
            photo=img,
            caption=_["stream_1"].format(
                title[:30],
                f"https://t.me/{app.username}?start=info_{videoid}",
                check[0]["dur"],
                user,
            ),
            reply_markup=InlineKeyboardMarkup(button),
        )
        db[chat_id][0]["mystic"] = run
        db[chat_id][0]["markup"] = "tg"
    elif "vid_" in queued:
        mystic = await message.reply_text(
            _["call_10"], disable_web_page_preview=True
        )
        try:
            file_path, direct = await YouTube.download(
                videoid,
                mystic,
                videoid=True,
                video=status,
            )
        except:
            return await mystic.edit_text(_["call_9"])
        try:
            await Stranger.skip_stream(chat_id, file_path, video=status)
        except Exception:
            return await mystic.edit_text(_["call_9"])
        button = stream_markup(_, videoid, chat_id)
        img = await gen_thumb(videoid,user_idd)
        run = await message.reply_photo(
            photo=img,
            caption=_["stream_1"].format(
                title[:30],
                f"https://t.me/{app.username}?start=info_{videoid}",
                check[0]["dur"],
                user,
            ),
            reply_markup=InlineKeyboardMarkup(button),
        )
        db[chat_id][0]["mystic"] = run
        db[chat_id][0]["markup"] = "stream"
        await mystic.delete()
    elif "index_" in queued:
        try:
            await Stranger.skip_stream(chat_id, videoid, video=status)
        except Exception:
            return await message.reply_text(_["call_9"])
        button = telegram_markup(_, chat_id)
        run = await message.reply_photo(
            photo=config.STREAM_IMG_URL,
            caption=_["stream_2"].format(user),
            reply_markup=InlineKeyboardMarkup(button),
        )
        db[chat_id][0]["mystic"] = run
        db[chat_id][0]["markup"] = "tg"
    else:
        try:
            await Stranger.skip_stream(chat_id, queued, video=status)
        except Exception:
            return await message.reply_text(_["call_9"])
        if videoid == "telegram":
            button = telegram_markup(_, chat_id)
            run = await message.reply_photo(
                photo=config.TELEGRAM_AUDIO_URL
                if str(streamtype) == "audio"
                else config.TELEGRAM_VIDEO_URL,
                caption=_["stream_3"].format(
                    title, check[0]["dur"], user
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
        elif videoid == "soundcloud":
            button = telegram_markup(_, chat_id)
            run = await message.reply_photo(
                photo=config.SOUNCLOUD_IMG_URL
                if str(streamtype) == "audio"
                else config.TELEGRAM_VIDEO_URL,
                caption=_["stream_3"].format(
                    title, check[0]["dur"], user
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
        else:
            button = stream_markup(_, videoid, chat_id)
            img = await gen_thumb(videoid,user_idd)
            run = await message.reply_photo(
                photo=img,
                caption=_["stream_1"].format(
                    title[:30],
                    f"https://t.me/{app.username}?start=info_{videoid}",
                    check[0]["dur"],
                    user,
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"
