import os
import zipfile
import subprocess
import shutil
import time
from pyrogram import filters
from AviaxMusic import app
from github import Github, GithubException
from config import OWNER_ID  

# FIXED: Ab ye humesha Absolute Path (Pakka Rasta) use karega
TEMP_DIR = os.path.abspath("temp_repos")
os.makedirs(TEMP_DIR, exist_ok=True)

TEMP_CONFIG = {}

def run(cmd, cwd):
    proc = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")
    return proc.stdout

def safe_rm(path):
    try:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
    except Exception:
        pass

def config_valid():
    if not TEMP_CONFIG:
        return False
    if time.time() - TEMP_CONFIG.get("timestamp", 0) > 3600:
        TEMP_CONFIG.clear()
        return False
    return True

@app.on_message(filters.command("gitconfig") & filters.user(OWNER_ID))
async def gitconfig(client, message):
    if len(message.command) < 4:
        return await message.reply(
            "**» ᴜsᴀɢᴇ :-** `/gitconfig username email token`"
        )
    name = message.command[1]
    email = message.command[2]
    token = message.command[3]
    TEMP_CONFIG.update({"name": name, "email": email, "token": token, "timestamp": time.time()})
    await message.reply("✅ **ɢɪᴛʜᴜʙ ᴄᴏɴꜰɪɢ sᴇᴛ sᴜᴄᴄᴇssғᴜʟʟʏ!** (ᴠᴀʟɪᴅ ꜰᴏʀ **60 ᴍɪɴᴜᴛᴇs**)")


# ==========================================
# SMART COMMAND: CREATE OR UPDATE REPO
# ==========================================
@app.on_message(filters.command(["gitupload", "gt", "gitupdate", "gu"]) & filters.user(OWNER_ID))
async def gitupload(client, message):
    if len(message.command) < 2:
        return await message.reply(
            "**» ᴜsᴀɢᴇ :-** `/gitupload repo_name private/public branch_name` **(ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴢɪᴘ ғɪʟᴇ)**"
        )

    if not config_valid():
        return await message.reply("**⚠️ ᴄᴏɴꜰɪɢ ᴇxᴘɪʀᴇᴅ ᴏʀ ɴᴏᴛ sᴇᴛ!**\n\n**» ᴘʟᴇᴀsᴇ ʀᴜɴ** `/gitconfig` **ғɪʀsᴛ.**")

    GITHUB_NAME = TEMP_CONFIG["name"]
    GITHUB_EMAIL = TEMP_CONFIG["email"]
    GITHUB_TOKEN = TEMP_CONFIG["token"]
    g = Github(GITHUB_TOKEN)

    repo_name = message.command[1]
    visibility = message.command[2].lower() if len(message.command) >= 3 else "public"
    is_private = visibility == "private"
    branch_name = message.command[3] if len(message.command) >= 4 else "main"

    replied = message.reply_to_message
    if not (replied and replied.document and replied.document.file_name.endswith(".zip")):
        return await message.reply("⚠️ ᴘʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ **ᴢɪᴘ** ғɪʟᴇ!")

    # FIXED: Repo name ko safe banaya taaki Organization slashes (/) folder break na karein
    safe_repo_name = repo_name.replace("/", "_").replace("\\", "_")

    zip_path = os.path.join(TEMP_DIR, replied.document.file_name)
    extract_root = os.path.join(TEMP_DIR, f"{safe_repo_name}_extract")
    final_path = os.path.join(TEMP_DIR, f"{safe_repo_name}_final")
    clone_path = os.path.join(TEMP_DIR, f"{safe_repo_name}_clone")

    safe_rm(zip_path)
    safe_rm(extract_root)
    safe_rm(final_path)
    safe_rm(clone_path)

    status = await message.reply("**⏳ ᴘʀᴏᴄᴇssɪɴɢ ʏᴏᴜʀ ʀᴇqᴜᴇsᴛ...**")

    try:
        user = g.get_user()
        
        # SMART CHECK: Check if repo exists (Supports Organization repos too)
        repo_exists = False
        try:
            if "/" in repo_name:
                repo = g.get_repo(repo_name)
            else:
                repo = user.get_repo(repo_name)
            repo_exists = True
        except GithubException as e:
            if e.status == 404:
                repo_exists = False
            else:
                raise e

        # Extracting Zip File
        await replied.download(file_name=zip_path)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_root)

        inner_items = os.listdir(extract_root)
        inner_dirs = [d for d in inner_items if os.path.isdir(os.path.join(extract_root, d))]
        inner_files = [f for f in inner_items if os.path.isfile(os.path.join(extract_root, f))]

        if len(inner_dirs) == 1 and not inner_files:
            shutil.move(os.path.join(extract_root, inner_dirs[0]), final_path)
        else:
            shutil.move(extract_root, final_path)

        for root, dirs, _ in os.walk(final_path):
            if ".git" in dirs:
                safe_rm(os.path.join(root, ".git"))

        if repo_exists:
            # ==> UPDATE EXISTING REPO
            remote_url = repo.clone_url.replace("https://", f"https://{GITHUB_TOKEN}@")
            run(["git", "clone", remote_url, clone_path], cwd=TEMP_DIR)

            for item in os.listdir(final_path):
                s = os.path.join(final_path, item)
                d = os.path.join(clone_path, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)

            run(["git", "config", "user.email", GITHUB_EMAIL], cwd=clone_path)
            run(["git", "config", "user.name", GITHUB_NAME], cwd=clone_path)

            try:
                run(["git", "checkout", branch_name], cwd=clone_path)
            except RuntimeError:
                run(["git", "checkout", "-b", branch_name], cwd=clone_path)

            run(["git", "add", "."], cwd=clone_path)

            status_out = subprocess.run(["git", "status", "--porcelain"], cwd=clone_path, text=True, capture_output=True)
            if status_out.stdout.strip():
                run(["git", "commit", "-m", "🚀 ᴜᴘᴅᴀᴛᴇᴅ ᴠɪᴀ :- ɪsᴛᴋʜᴀʀ ʙᴏᴛs 🌺"], cwd=clone_path)
                run(["git", "push", "origin", branch_name], cwd=clone_path)
            
            action_text = "ᴜᴘᴅᴀᴛᴇᴅ"

        else:
            # ==> CREATE NEW REPO
            if "/" in repo_name:
                await status.delete()
                return await message.reply("❌ **ᴇʀʀᴏʀ :-** Naya Organization repo bot se direct create nahi ho sakta. Pehle khali repo GitHub par banayein, fir update karein.")
                
            repo = user.create_repo(repo_name, private=is_private, description="🎉 sᴏᴜʀᴄᴇ ᴄᴏᴅᴇ ᴜᴘʟᴏᴀᴅ ʙʏ :- ɪsᴛᴋʜᴀʀ ʙᴏᴛs 🌺", auto_init=False)

            run(["git", "init"], cwd=final_path)
            run(["git", "config", "user.email", GITHUB_EMAIL], cwd=final_path)
            run(["git", "config", "user.name", GITHUB_NAME], cwd=final_path)
            remote_url = repo.clone_url.replace("https://", f"https://{GITHUB_TOKEN}@")
            run(["git", "remote", "add", "origin", remote_url], cwd=final_path)
            run(["git", "add", "."], cwd=final_path)

            status_out = subprocess.run(["git", "status", "--porcelain"], cwd=final_path, text=True, capture_output=True)
            if status_out.stdout.strip():
                run(["git", "commit", "-m", "ɪsᴛᴋʜᴀʀ ʙᴏᴛs !!"], cwd=final_path)
            else:
                run(["git", "commit", "--allow-empty", "-m", "ɪsᴛᴋʜᴀʀ ʙᴏᴛs !!"], cwd=final_path)

            run(["git", "branch", "-M", branch_name], cwd=final_path)
            run(["git", "push", "-u", "origin", branch_name], cwd=final_path)
            
            action_text = "ᴜᴘʟᴏᴀᴅᴇᴅ (ɴᴇᴡ)"

    except Exception as e:
        safe_rm(zip_path)
        safe_rm(extract_root)
        safe_rm(final_path)
        safe_rm(clone_path)
        await status.delete()
        return await message.reply(f"❌** ᴇʀʀᴏʀ :-** `{e}`")

    safe_rm(zip_path)
    safe_rm(extract_root)
    safe_rm(final_path)
    safe_rm(clone_path)
    await status.delete()
    
    await message.reply(
        f"✅ **ʀᴇᴘᴏ** `{repo_name}` **{action_text} sᴜᴄᴄᴇssғᴜʟʟʏ!**\n\n"
        f"🔒 **ᴠɪsɪʙɪʟɪᴛʏ :-** `{'Private' if is_private else 'Public'}`\n"
        f"🌿 **ʙʀᴀɴᴄʜ :-** `{branch_name}`\n\n"
        f"🔗 **ᴜʀʟ :-** {repo.html_url}"
    )
