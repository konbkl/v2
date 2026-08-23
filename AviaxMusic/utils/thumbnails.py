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

def make_col():
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    return image.resize((newWidth, newHeight))

def truncate(text):
    list_words = text.split(" ")
    text1, text2 = "", ""    
    for i in list_words:
        if len(text1) + len(i) < 30:        
            text1 += " " + i
        elif len(text2) + len(i) < 30:       
            text2 += " " + i
    return [text1.strip(), text2.strip()]

# yt-dlp se details nikalne ka function (Bypasses IP Block)
def extract_info(url):
    ydl_opts = {'quiet': True, 'no_warnings': True, 'extract_flat': True}
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
        
        # 1. Safely Extract Details with yt-dlp
        try:
            info = await asyncio.to_thread(extract_info, url)
            title = re.sub(r"\W+", " ", info.get("title", "Playing Track")).title()
            
            # Format duration properly
            duration_seconds = info.get("duration", 0)
            if duration_seconds:
                mins = int(duration_seconds) // 60
                secs = int(duration_seconds) % 60
                duration = f"{mins}:{secs:02d} Mins"
            else:
                duration = "Unknown Mins"
                
            views = str(info.get("view_count", "Unknown Views"))
            channel = info.get("uploader", "Unknown Channel")
            
            # Get best thumbnail URL
            if info.get("thumbnails"):
                thumbnail_url = info["thumbnails"][-1]["url"]
            else:
                thumbnail_url = f"http://img.youtube.com/vi/{videoid}/maxresdefault.jpg"
        except Exception as e:
            print(f"yt-dlp extract error: {e}")
            title = "Playing Track"
            duration = "Unknown Mins"
            views = "Unknown Views"
            channel = "Unknown Channel"
            thumbnail_url = f"http://img.youtube.com/vi/{videoid}/hqdefault.jpg"

        # 2. Download Thumbnail
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail_url) as resp:
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

        # 3. Image Editing Block
        try:
            youtube = Image.open(raw_thumb)
            image1 = changeImageSize(1280, 720, youtube)
            image2 = image1.convert("RGBA")
            background = image2.filter(filter=ImageFilter.BoxBlur(30))
            enhancer = ImageEnhance.Brightness(background)
            image2 = enhancer.enhance(0.6)

            if os.path.isfile("AviaxMusic/assets/circle.png"):
                circle = Image.open("AviaxMusic/assets/circle.png").convert('RGBA')
                color = make_col()
                data = np.array(circle)
                red, green, blue, alpha = data.T
                white_areas = (red == 255) & (blue == 255) & (green == 255)
                data[..., :-1][white_areas.T] = color
                circle = Image.fromarray(data)
                
                image3 = image1.crop((280, 0, 1000, 720))
                lum_img = Image.new('L', [720, 720], 0)
                draw = ImageDraw.Draw(lum_img)
                draw.pieslice([(0, 0), (720, 720)], 0, 360, fill=255, outline="white")
                img_arr = np.array(image3)
                lum_img_arr = np.array(lum_img)
                final_img_arr = np.dstack((img_arr, lum_img_arr))
                image3 = Image.fromarray(final_img_arr).resize((600, 600))

                image2.paste(image3, (50, 70), mask=image3)
                image2.paste(circle, (0, 0), mask=circle)

            try:
                font1 = ImageFont.truetype('AviaxMusic/assets/font.ttf', 30)
                font2 = ImageFont.truetype('AviaxMusic/assets/font2.ttf', 70)
                font3 = ImageFont.truetype('AviaxMusic/assets/font2.ttf', 40)
                font4 = ImageFont.truetype('AviaxMusic/assets/font2.ttf', 35)
            except:
                font1 = font2 = font3 = font4 = ImageFont.load_default()

            image4 = ImageDraw.Draw(image2)
            image4.text((10, 10), "KHUSHI VIBES", fill="white", font=font1, align="left") 
            image4.text((670, 150), "NOW PLAYING", fill="white", font=font2, stroke_width=2, stroke_fill="white", align="left") 

            title1 = truncate(title)
            image4.text((670, 300), text=title1[0], fill="white", stroke_width=1, stroke_fill="white", font=font3, align="left") 
            if len(title1) > 1:
                image4.text((670, 350), text=title1[1], fill="white", stroke_width=1, stroke_fill="white", font=font3, align="left") 

            image4.text((670, 450), text=f"Views : {views}", fill="white", font=font4, align="left") 
            image4.text((670, 500), text=f"Duration : {duration}", fill="white", font=font4, align="left") 
            image4.text((670, 550), text=f"Channel : {channel}", fill="white", font=font4, align="left")

            image2 = ImageOps.expand(image2, border=20, fill=make_col())
            image2 = image2.convert('RGB')
            image2.save(final_file)
            return final_file

        except Exception as edit_error:
            print(f"PIL Edit Failed: {edit_error}")
            return raw_thumb

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        return YOUTUBE_IMG_URL
