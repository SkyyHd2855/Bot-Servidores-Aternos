import json
import discord
from discord.ext import commands
from python_aternos import Client, atserver, atwss, Lists

# Configuração do bot
prefix = '!'  # Alterar command_prefix se o desejar
intents = discord.Intents(messages=True, guilds=True, message_content=True)
bot = commands.Bot(command_prefix=prefix, intents=intents)

# arquivo de credenciais
with open('credentials.json') as file:
    data = json.load(file)

# Credenciais para Discord e Aternos
secret_key = data["credentials"]["discord_bot"]
user = data["credentials"]["aternos_user"]
pswd = data["credentials"]["aternos_pwsd"]
channel_id = data["credentials"]["discord_channel"]
srv_ws = data["credentials"]["n_servidor"]

# Para websocket
aternos = Client.from_credentials(user, pswd)
srv_1 = aternos.list_servers()[srv_ws]  # Alterar numero para websocket de servidor
socket = srv_1.wss()

print("Iniciando Bot")


def sesion(user, password):
    """Função para iniciar sesion"""
    return Client.from_credentials(user, password)


def servidores(credentials):
    """Função para obter os servidores"""
    return credentials.list_servers()


def selec_server(srv_no, ctx):
    """Função para selecionar o servidor desejado"""
    try:
        srv_name = int(srv_no) - 1
    except ValueError:
        embed = discord.Embed(
            colour=discord.Colour.dark_red(),
            title="Erro de tipo",
            description=f"Olá {ctx.author.name}! O índice do servidor deve ser um número inteiro",
        )
        return False, embed

    srv_list = servidores(sesion(user=user, password=pswd))
    i = 0
    for srv in srv_list:
        if i == srv_name:
            return srv, False
        i += 1

    # Se o servidor não se encontra na lista
    embed = discord.Embed(
        colour=discord.Colour.dark_red(),
        title="Erro de índice",
        description=f"Olá {ctx.author.name}! O índice do servidor não se encontra na lista de servidores",
    )
    return False, embed


@bot.command(name="servidores", pass_context=True, help="Lista os servidores disponíveis",
             description="Lista de servidores disponíveis")
@commands.has_role("Jugador")  # ROL
async def list_servers(ctx):
    """Manda a lista de servidores registrados"""
    try:
        resp = []
        i = 0
        print("Request: @server_list")
        for srv in servidores(sesion(user=user, password=pswd)):
            resp.append(str(i + 1) + ": " + srv.subdomain)
            i += 1

        embed = discord.Embed(
            colour=discord.Colour.light_gray(),
            title="Servidores",
            description=f"Olá {ctx.author.name}! Os servidores registrados são: \n" + "\n".join(resp),
        )
        await ctx.reply(embed=embed)
    except IndexError:
        await ctx.send("Não existe")


@bot.command(name="jogadores", pass_context=True, help="Lista todos os jogadores no servidor",
             description="Lista de jogadores do servidor")
@commands.has_role("Jugador")  # ROL
async def list_players(ctx, srv_no):
    """Manda a lista de jogadores no servidor"""
    try:
        srv = selec_server(srv_no, ctx)[0]
        embed_error = selec_server(srv_no, ctx)[1]
        if srv:
            players = srv.players(Lists.whl).list_players()
            embed = discord.Embed(
                colour=discord.Colour.greyple(),
                title="Jogadores",
                description=f"Olá {ctx.author.name}! Os jogadores do servidor são:",
            )
            for player in players:
                embed.add_field(name="Jogador", value=player, inline=False)
            await ctx.reply(embed=embed)
        else:
            await ctx.reply(embed=embed_error)
    except IndexError:
        await ctx.send("Não existe")


@bot.command(name="status", pass_context=True, help="Informa o estado atual do servidor mencionado")
@commands.has_role("Jugador")  # ROL
async def status(ctx, srv_no):
    """Manda o status do servidor"""
    try:
        srv = selec_server(srv_no, ctx)[0]
        embed_error = selec_server(srv_no, ctx)[1]
        if srv:
            print("Request: @status " + srv.subdomain)
            if srv.status == "online":
                color = discord.Colour.red()
                estatus = "Ligado"
            elif srv.status == "loading starting":
                color = discord.Colour.yellow()
                estatus = "Carregando, espere só um pouco"
            else:
                color = discord.Colour.red()
                estatus = "Desligado\n\n Você pode ligá-lo com o comando $inicio + o índice do servidor"
            embed = discord.Embed(
                colour=color,
                title="Status do servidor " + srv.subdomain,
                description=f"Olá {ctx.author.name}! \n O servidor está atualmente " + estatus,
            )
            await ctx.reply(embed=embed)
        else:
            await ctx.reply(embed=embed_error)
    except IndexError:
        embed = discord.Embed(
            colour=discord.Colour.dark_red(),
            title="Não existe",
            description=f"Olá {ctx.author.name}! \n O índice: " + srv_no + " não existe, posso mostrar-lhe a lista de "
                                                                         "servidores com o comando $servidores "
        )
        await ctx.reply(embed=embed)


@bot.command(name="iniciar", pass_context=True, help="Inicia o servidor mencionado")
@commands.has_role("Jugador")  # ROl
async def start(ctx, srv_no):
    """Inicia o servidor"""
    await socket.connect()
    try:
        srv = selec_server(srv_no, ctx)[0]
        embed_error = selec_server(srv_no, ctx)[1]
        if srv:
            print("Request: @start  " + srv.subdomain)
            if srv.status != "online":
                srv.start()
                embed = discord.Embed(
                    colour=discord.Colour.dark_green(),
                    title="Ligar " + srv.subdomain,
                    description=f"Olá {ctx.author.name}! \nSerá iniciado o servidor: " + srv.subdomain
                )
                await ctx.reply(embed=embed)
            else:
                embed = discord.Embed(
                    colour=discord.Colour.green(),
                    title="Ligar " + srv.subdomain,
                    description=f"Olá {ctx.author.name}! \nO servidor: " + srv.subdomain + " está ativo!"
                )
                await ctx.reply(embed=embed)
        else:
            await ctx.reply(embed=embed_error)
    except IndexError:
        await ctx.send("Não existe")


@bot.command(name="reiniciar", pass_context=True, help="Reinicia o servidor mencionado")
@commands.has_role("Administrador")  # ROL
async def restart(ctx, srv_no):
    """Reinicia o servidor"""
    try:
        srv = selec_server(srv_no, ctx)[0]
        embed_error = selec_server(srv_no, ctx)[1]
        if srv:
            print("Request: @restart  " + srv.subdomain)
            if srv.status != "online":
                embed = discord.Embed(
                    colour=discord.Colour.green(),
                    title="Iniciar" + srv.subdomain,
                    description=f"Olá {ctx.author.name}! \nO servidor: " + srv.subdomain + " será iniciado"
                )
                await ctx.reply(embed=embed)
                srv.start()
            else:
                embed = discord.Embed(
                    colour=discord.Colour.green(),
                    title="Reiniciar" + srv.subdomain,
                    description=f"Olá {ctx.author.name}! \nO servidor: " + srv.subdomain + " será reiniciado"
                )
                await ctx.reply(embed=embed)
                srv.restart()
        else:
            await ctx.reply(embed=embed_error)
    except IndexError:
        await ctx.send("Não existe")


@bot.command(name="parar", pass_context=True, help="Para o servidor mencionado. FUNÇÃO REQUERIDA: Administrador de MCS")
@commands.has_role("Administrador")  # Você pode mudar o papel que pode parar o servidor
async def stop(ctx, srv_no):
    """Apaga o servidor"""
    try:
        srv = selec_server(srv_no, ctx)[0]
        embed_error = selec_server(srv_no, ctx)[1]
        if srv:
            print("Request: @stop   " + srv.subdomain)
            if srv.status != "online":
                embed = discord.Embed(
                    colour=discord.Colour.green(),
                    title="Parar" + srv.subdomain,
                    description=f"Olá {ctx.author.name}! \nO servidor: " + srv.subdomain + " está desligado"
                )
                await ctx.reply(embed=embed)
            else:
                embed = discord.Embed(
                    colour=discord.Colour.green(),
                    title="Parar" + srv.subdomain,
                    description=f"Olá {ctx.author.name}! \nO servidor: " + srv.subdomain + " será desligado"
                )
                await ctx.reply(embed=embed)
                srv.stop()
        else:
            await ctx.reply(embed=embed_error)
    except IndexError:
        await ctx.send("Não existe")


@bot.command(name="info", pass_context=True, help="Informa os detalhes sobre o servidor mencionado")
@commands.has_role("Jugador")  # ROL
async def getinfo(ctx, srv_no):
    """Retorna a principal informação do servidor"""
    try:
        srv = selec_server(srv_no, ctx)[0]
        embed_error = selec_server(srv_no, ctx)[1]
        if srv:
            embed = discord.Embed(
                colour=discord.Colour.blue(),
                title="Informação do servidor: " + srv.subdomain,
                # description=f"Olá {ctx.author.name}! \nAqui está a informação do servidor"
            )
            embed.add_field(name="Nome", value=srv.subdomain, inline=False)
            embed.add_field(name="Domínio", value=srv.domain, inline=False)
            embed.add_field(name="Status", value=srv.status)
            embed.add_field(name="Porta", value=str(srv.port))
            if srv.edition == atserver.Edition.bedrock:
                embed.add_field(name="Edição", value="Bedrock")
            else:
                embed.add_field(name="Edição", value="Java")
            embed.add_field(name="Minecraft", value=srv.software + srv.version, inline=False)
            await ctx.reply(embed=embed)
            print("Request: @getinfo")
            print('*** ' + srv.domain + ' ***' + '\n' +
                  '*** Address: ' + srv.address + ' ***' + '\n' +
                  '*** Status: ' + srv.status + ' ***' + '\n' +
                  '*** Port: ' + str(srv.port) + ' ***' + '\n' +
                  '*** Name: ' + srv.subdomain + ' ***' + '\n' +
                  '*** Minecraft: ' + srv.software + srv.version + ' ***' + '\n' +
                  '*** Bedrock: ' + str(srv.edition == atserver.Edition.bedrock) + ' ***' + '\n' +
                  '*** Java: ' + str(srv.edition == atserver.Edition.java) + ' ***')
        else:
            await ctx.reply(embed=embed_error)
    except IndexError:
        await ctx.send("Não existe")


@bot.event  # para eventos
async def on_command_error(ctx, error):
    print(ctx)
    if isinstance(error, (commands.MissingRole, commands.MissingAnyRole)):
        await ctx.reply(embed=discord.Embed(
            colour=discord.Colour.red(),
            title="Não tens permissão"
        ))
    elif isinstance(error, commands.CommandNotFound):
        await ctx.reply(embed=discord.Embed(
            colour=discord.Colour.red(),
            title="O comando não existe"
            # description=f"Hola {ctx.author.name}! \nAqui está a informação do servidor"
        ))
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.reply(embed=discord.Embed(
            colour=discord.Colour.red(),
            title="Mencione um servidor",
            description="Ex: " + prefix + "iniciar 1"
        ))
    else:
        await ctx.reply(embed=discord.Embed(
            colour=discord.Colour.red(),
            title="Erro",
        ))
        print(error)


@socket.wssreceiver(atwss.Streams.console)
async def console(msg):
    """Função que retorna a consola de aternos ao iniciar e parar, para vê-la completa imprima msg"""
    # print(msg)
    if 'Done' in msg:
        # if 'Timings Reset' in msg: 			# Se não funciona com Timings reset, altere para Done
        embed = discord.Embed(
            colour=discord.Colour.green(),
            title="O servidor " + srv_1.subdomain + " está ligado",
            description="BOA SORTE!"
        )
        await bot.get_channel(channel_id).send(embed=embed)
    if 'Stopping server' in msg:
        embed = discord.Embed(
            colour=discord.Colour.red(),
            title="O servidor " + srv_1.subdomain + " desligou"
        )
        await bot.get_channel(channel_id).send(embed=embed)


# Mensagem quando o bot está online
@bot.event
async def on_ready():
    """Define o status (atividade e presença) do bot e envia a mensagem de inicialização."""

    # --- Configuração de Status e Atividade ---
    # 1. Defina o tipo de atividade
    atividade_tipo = discord.ActivityType.playing 
    
    # 2. Defina a mensagem que aparecerá (a descrição da atividade)
    mensagem_atividade = f"com {prefix}servidores | By .gg/Visionario e SkyyHd285"
    
    # 3. Defina o status de presença (online, idle, dnd, invisible)
    status_presenca = discord.Status.online
    
    # 4. Aplica a mudança de presença
    await bot.change_presence(
        activity=discord.Activity(type=atividade_tipo, name=mensagem_atividade),
        status=status_presenca
    )
    
    # -------------------------------------------
    
    print(f"Bot conectado como {bot.user} e com status atualizado!")
    
    # Código para enviar a mensagem de inicialização (mantido do original)
    embed = discord.Embed(
        colour=discord.Colour.purple(),
        title="O Bot está online!",
        description="Estes são os seus comandos:"
    )
    embed.add_field(name=prefix + "servidores", value="Mostra a lista de servidores", inline=False)
    embed.add_field(name=prefix + "info [n° do servidor]", value="Mostra as informações do servidor selecionado",
                    inline=False)
    embed.add_field(name=prefix + "status [n° do servidor]", value="Mostra o estado do servidor selecionado ",
                    inline=False)
    embed.add_field(name=prefix + "iniciar [n° do servidor]", value="Inicia o servidor selecionado (terá que "
                                                                    "esperar que inicie. avisará quando "
                                                                    "tiver iniciado por completo) ", inline=False)
    embed.add_field(name=prefix + "jogadores [n° do servidor]", value="Mostra os jogadores registados do servidor", inline=False)
    
    canal = bot.get_channel(channel_id)
    if canal:
        await canal.send(embed=embed)
    else:
        print(f"ERRO: Canal com ID {channel_id} não encontrado.")


# corre o bot com a chave de discord
bot.run(secret_key)