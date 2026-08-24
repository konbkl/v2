import asyncio
import os
import random
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
from yt_dlp import YoutubeDL
import numpy as np
from config import YOUTUBE_IMG_URL

def get_neon_color():
    # Neon Tech Colors: Cyan, Magenta, Neon Green, Electric Blue
    colors = [(0, 255, 255), (255, 0, 255), (57, 255, 20), (0, 128, 255)]
    return random.choice(colors)

def truncate(text):
    list_words = text.split(" ")
    text1, text2 = "", ""    
    for i in list_words:
        if len(text1) + len(i) < 25:        
            text1 += " " + i
        elif len(text2) + len(i) < 25:       
            text2 += " " + i
    return [text1.strip(), text2.strip()]

def extract_info(url):
    # Removed extract_flat taaki full details aayein
    ydl_opts = {'quiet': True, 'no_warnings': True}
    with YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)

async def gen_thumb(videoid):
    try:
        os.makedirs("cache", exist_ok=True)
        final_file = f"cache/{videoid}.jpg"
        raw_thumb = f"cache/thumb{videoid}.jpg"
        
        if os.path.isfile(final_file):
            return final_file

        url = f"https://www.youtube.com/watch?v={videoid}"
        
        # 1. Safely Extract Full Details
        try:
            info = await asyncio.to_thread(extract_info, url)
            title = re.sub(r"\W+", " ", info.get("title", "Playing Track")).title()
            
            duration_seconds = info.get("duration", 0)
            if duration_seconds:
                mins = int(duration_seconds) // 60
                secs = int(duration_seconds) % 60
                duration = f"{mins}:{secs:02d} Mins"
            else:
                duration = "Unknown Mins"
                
            views = str(info.get("view_count", "Unknown Views"))
            channel = info.get("uploader", "Unknown Channel")
            
            if info.get("thumbnails"):
                thumbnail_url = info["thumbnails"][-1]["url"]
            else:
                thumbnail_url = f"http://img.youtube.com/vi/{videoid}/maxresdefault.jpg"
        except Exception as e:
            print(f"yt-dlp error: {e}")
            title, duration, views, channel = "Playing Track", "Unknown Mins", "Unknown Views", "Unknown Channel"
            thumbnail_url = f"http://img.youtube.com/vi/{videoid}/hqdefault.jpg"

        # 2. Download Thumbnail
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail_url) as resp:
                if resp.status == 200:
                    async with aiofiles.open(raw_thumb, mode="wb") as f:
                        await f.write(await resp.read())

        if not os.path.isfile(raw_thumb):
            return YOUTUBE_IMG_URL

        # 3. ADVANCED IMAGE EDITING (Tech & Neon Theme)
        try:
            youtube = Image.open(raw_thumb).convert("RGBA")
            
            # Background: High-quality Blur & Darken
            background = youtube.resize((1280, 720), Image.Resampling.LANCZOS)
            background = background.filter(ImageFilter.GaussianBlur(15))
            background = ImageEnhance.Brightness(background).enhance(0.25)
            
            theme_color = get_neon_color()

            # Center Circle: Perfect crop bina stretch kiye
            square_img = ImageOps.fit(youtube, (580, 580), centering=(0.5, 0.5))
            mask = Image.new('L', (580, 580), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, 580, 580), fill=255)
            square_img.putalpha(mask)
            
            # Custom Glowing Neon Ring
            ring = Image.new('RGBA', (610, 610), (0,0,0,0))
            ring_draw = ImageDraw.Draw(ring)
            ring_draw.ellipse((10, 10, 600, 600), outline=theme_color, width=10)
            
            # Paste Ring and Center Image
            background.paste(ring, (45, 55), ring)
            background.paste(square_img, (60, 70), square_img)

            # Fonts setup
            try:
                font1 = ImageFont.truetype('AviaxMusic/assets/font.ttf', 35)
                font2 = ImageFont.truetype('AviaxMusic/assets/font2.ttf', 75)
                font3 = ImageFont.truetype('AviaxMusic/assets/font2.ttf', 45)
                font4 = ImageFont.truetype('AviaxMusic/assets/font2.ttf', 35)
            except:
                font1 = font2 = font3 = font4 = ImageFont.load_default()

            image4 = ImageDraw.Draw(background)
            
            # Brand Name with Neon effect
            image4.text((22, 22), "KHUSHI VIBES", fill="black", font=font1, align="left") 
            image4.text((20, 20), "KHUSHI VIBES", fill=theme_color, font=font1, align="left") 

            # NOW PLAYING Header
            image4.text((700, 150), "NOW PLAYING", fill="white", font=font2, stroke_width=2, stroke_fill=theme_color, align="left") 

            # Title
            title1 = truncate(title)
            image4.text((700, 280), text=title1[0], fill="white", font=font3, align="left") 
            if len(title1) > 1:
                image4.text((700, 340), text=title1[1], fill="white", font=font3, align="left") 

            # Stats (Tech-style transparent box)
            # Semi-transparent box behind the text to make it clear and attractive
            image4.rounded_rectangle([680, 450, 1200, 630], radius=15, fill=(0,0,0,160), outline=theme_color, width=3)
            
            image4.text((710, 470), text=f"Views    : {views}", fill="white", font=font4, align="left") 
            image4.text((710, 520), text=f"Duration : {duration}", fill="white", font=font4, align="left") 
            image4.text((710, 570), text=f"Channel  : {channel}", fill="white", font=font4, align="left")

            # Final Outer Border
            background = ImageOps.expand(background, border=12, fill=theme_color)
            background = background.convert('RGB')
            
            background.save(final_file)
            return final_file

        except Exception as edit_error:
            print(f"PIL Edit Failed: {edit_error}")
            return raw_thumb

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        return YOUTUBE_IMG_URL
