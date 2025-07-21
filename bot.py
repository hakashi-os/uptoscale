import discord
from discord.ext import commands
from discord import app_commands
import subprocess
import os
import shutil
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
tree = bot.tree

@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")
    try:
        synced = await tree.sync()
        print(f"🔄 Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

@tree.command(name="upscale", description="Upscale an attached MP4 video using Real-ESRGAN.")
@app_commands.describe(video="Attach a video file (MP4)")
async def upscale(interaction: discord.Interaction, video: discord.Attachment):
    await interaction.response.send_message("📥 Downloading video...")
    await video.save("input.mp4")

    os.makedirs("frames", exist_ok=True)
    os.makedirs("results", exist_ok=True)

    await interaction.followup.send("🎬 Extracting frames...")
    extract_proc = subprocess.run("ffmpeg -i input.mp4 frames/frame_%04d.png", shell=True, capture_output=True, text=True)
    if extract_proc.returncode != 0:
        await interaction.followup.send(f"❌ Frame extraction failed: {extract_proc.stderr}")
        return

    await interaction.followup.send("🧠 Upscaling with Real-ESRGAN...")
    upscale_proc = subprocess.run("python Real-ESRGAN/inference_realesrgan.py -n RealESRGAN_x4plus -i frames --outscale 4", shell=True, capture_output=True, text=True)
    if upscale_proc.returncode != 0:
        await interaction.followup.send(f"❌ Upscaling failed: {upscale_proc.stderr}")
        return

    await interaction.followup.send("🎞️ Rebuilding video...")
    rebuild_proc = subprocess.run("ffmpeg -r 30 -i results/frame_%04d_out.png -c:v libx264 -pix_fmt yuv420p output.mp4", shell=True, capture_output=True, text=True)
    if rebuild_proc.returncode != 0:
        await interaction.followup.send(f"❌ Video rebuild failed: {rebuild_proc.stderr}")
        return

    if os.path.exists("output.mp4"):
        await interaction.followup.send("✅ Done! Here is your upscaled video:", file=discord.File("output.mp4"))
    else:
        await interaction.followup.send("❌ Something went wrong. No output.mp4 file found.")

    # Cleanup
    shutil.rmtree("frames", ignore_errors=True)
    shutil.rmtree("results", ignore_errors=True)
    if os.path.exists("input.mp4"): os.remove("input.mp4")
    if os.path.exists("output.mp4"): os.remove("output.mp4")

bot.run(TOKEN)
