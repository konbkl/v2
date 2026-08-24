import asyncio
import os
import random
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
from youtubesearchpython.__future__ import VideosSearch
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

async def gen_thumb(videoid):
    try:
        os.makedirs("cache", exist_ok=True)
        final_file = f"cache/{videoid}.jpg"
        raw_thumb = f"cache/thumb{videoid}.jpg"
        
        if os.path.isfile(final_file):
            return final_file

        url = f"https://www.youtube.com/watch?v={videoid}"
        
        title = "Unknown Title"
        duration = "Unknown Mins"
        views = "Unknown Views"
        channel = "Unknown Channel"

        # 1. Main Search (youtubesearchpython)
        try:
            results = VideosSearch(url, limit=1)
            search_data = (await results.next())["result"]
            if search_data:
                result = search_data[0]
                title = result.get("title", title)
                title = re.sub(r"\W+", " ", title).title()
                duration = result.get("duration", duration)
                views = result.get("viewCount", {}).get("short", views)
                channel = result.get("channel", {}).get("name", channel)
        except Exception as e:
            print(f"Search API Blocked: {e}")

        # 2. HTML Scraping Fallback (Agar API block ho jaye toh bhi Title nikal lega)
        if title == "Unknown Title":
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                        html = await resp.text()
                        title_match = re.search(r'<title>(.*?)</title>', html)
                        if title_match:
                            title = title_match.group(1).replace(" - YouTube", "")
                            title = re.sub(r"\W+", " ", title).title()
            except:
                title = "Playing Track"

        # 3. Download Thumbnail
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://img.youtube.com/vi/{videoid}/maxresdefault.jpg") as resp:
                if resp.status == 200:
                    async with aiofiles.open(raw_thumb, mode="wb") as f:
                        await f.write(await resp.read())
                else:
                    async with session.get(f"http://img.youtube.com/vi/{videoid}/hqdefault.jpg") as resp2:
                        if resp2.status == 200:
                            async with aiofiles.open(raw_thumb, mode="wb") as f:
                                await f.write(await resp2.read())

        if not os.path.isfile(raw_thumb):
            return YOUTUBE_IMG_URL

        # 4. ADVANCED IMAGE EDITING
        try:
            youtube = Image.open(raw_thumb).convert("RGBA")
            
            # Background Blur & Darken
            background = youtube.resize((1280, 720), Image.Resampling.LANCZOS)
            background = background.filter(ImageFilter.GaussianBlur(15))
            background = ImageEnhance.Brightness(background).enhance(0.25)
            
            theme_color = get_neon_color()

            # Center Circle (No Stretch)
            square_img = ImageOps.fit(youtube, (580, 580), centering=(0.5, 0.5))
            mask = Image.new('L', (580, 580), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, 580, 580), fill=255)
            square_img.putalpha(mask)
            
            # Glowing Neon Ring
            ring = Image.new('RGBA', (610, 610), (0,0,0,0))
            ring_draw = ImageDraw.Draw(ring)
            ring_draw.ellipse((10, 10, 600, 600), outline=theme_color, width=10)
            
            # Paste Ring and Center Image
            background.paste(ring, (45, 55), ring)
            background.paste(square_img, (60, 70), square_img)

            # Fonts setup
            try:
                font1 = ImageFont.truetype('AviaxMusic/assets/font.ttf', 30)
                font2 = ImageFont.truetype('AviaxMusic/assets/font2.ttf', 70)
                font3 = ImageFont.truetype('AviaxMusic/assets/font2.ttf', 45)
                font4 = ImageFont.truetype('AviaxMusic/assets/font2.ttf', 35)
            except:
                font1 = font2 = font3 = font4 = ImageFont.load_default()

            image4 = ImageDraw.Draw(background)
            
            # Brand Name
            image4.text((22, 22), "KHUSHI VIBES", fill="black", font=font1, align="left") 
            image4.text((20, 20), "KHUSHI VIBES", fill=theme_color, font=font1, align="left") 

            # LAYOUT RE-DESIGN (Jaisa aapne manga)
            
            # NOW PLAYING Header (Upar)
            image4.text((700, 100), "NOW PLAYING", fill="white", font=font2, stroke_width=2, stroke_fill=theme_color, align="left") 

            # Title (Uske just niche)
            title1 = truncate(title)
            image4.text((700, 200), text=title1[0], fill="white", font=font3, align="left") 
            if len(title1) > 1:
                image4.text((700, 255), text=title1[1], fill="white", font=font3, align="left") 

            # Teeno Stats Title ke exact niche
            image4.text((700, 330), text=f"Views    : {views}", fill="white", font=font4, align="left") 
            image4.text((700, 380), text=f"Duration : {duration}", fill="white", font=font4, align="left") 
            image4.text((700, 430), text=f"Channel  : {channel}", fill="white", font=font4, align="left")

            # SUPER STYLISH PLAY BUTTON (Bottom Right - Jaha pehle box tha)
            play_x, play_y = 800, 500
            play_size = 140
            
            # Play Button Outer Circle
            image4.ellipse([play_x, play_y, play_x + play_size, play_y + play_size], outline=theme_color, width=6)
            
            # Play Button Inner Triangle
            tri_x = play_x + 50
            tri_y = play_y + 35
            image4.polygon([
                (tri_x, tri_y),            # Top point
                (tri_x, tri_y + 70),       # Bottom point
                (tri_x + 55, tri_y + 35)   # Right point
            ], fill=theme_color)

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
