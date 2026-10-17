import discord
from discord.ext import commands, tasks
import logging
import os

# ==================== CONFIGURAÇÃO ====================
TOKEN = os.environ.get("DISCORD_TOKEN")
PREFIX = "!"
# ======================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VoiceBot")

intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

current_channel = None
should_stay = False


@bot.event
async def on_ready():
    logger.info(f"Logado como {bot.user}")
    print(f"Bot ligado como {bot.user}")
    if not reconnect_loop.is_running():
        reconnect_loop.start()


@bot.command(name="join")
async def join(ctx):
    global current_channel, should_stay

    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("❌ Você precisa estar em um canal de voz.")
        return

    channel = ctx.author.voice.channel

    if ctx.voice_client:
        await ctx.voice_client.disconnect()

    try:
        vc = await channel.connect(reconnect=True, timeout=10.0)
        await vc.guild.change_voice_state(channel=channel, self_mute=True, self_deaf=True)

        current_channel = channel
        should_stay = True

        await ctx.send(f"✅ Entrei em **{channel.name}** e fiquei mutado. Farmando...")
        print(f"Entrou em {channel.name}")
    except Exception as e:
        await ctx.send(f"❌ Erro ao entrar: {e}")
        print(f"Erro: {e}")


@bot.command(name="leave")
async def leave(ctx):
    global should_stay, current_channel

    if not ctx.voice_client:
        await ctx.send("❌ Não estou em nenhum canal.")
        return

    should_stay = False
    current_channel = None
    await ctx.voice_client.disconnect()
    await ctx.send("👋 Saí do canal.")
    print("Saiu do canal")


@bot.command(name="status")
async def status(ctx):
    if ctx.voice_client and ctx.voice_client.is_connected():
        await ctx.send(f"🟢 Estou em **{ctx.voice_client.channel.name}** (mutado).")
    else:
        await ctx.send("🔴 Não estou em nenhum canal.")


@tasks.loop(seconds=15)
async def reconnect_loop():
    global current_channel, should_stay

    if not should_stay or current_channel is None:
        return

    voice_client = discord.utils.get(bot.voice_clients, guild=current_channel.guild)

    if voice_client is None or not voice_client.is_connected():
        print("Caiu... tentando reconectar...")
        try:
            vc = await current_channel.connect(reconnect=True, timeout=10.0)
            await vc.guild.change_voice_state(channel=current_channel, self_mute=True, self_deaf=True)
            print("Reconectado com sucesso!")
        except Exception as e:
            print(f"Falha ao reconectar: {e}")


@reconnect_loop.before_loop
async def before_reconnect():
    await bot.wait_until_ready()


if not TOKEN:
    print("ERRO: DISCORD_TOKEN não foi encontrado nas variáveis de ambiente!")
else:
    bot.run(TOKEN)