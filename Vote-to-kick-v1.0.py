# -*- coding: utf-8 -*-
# Vote to kick 插件 for MCDReforged
# 作者: Tiking-010
# 版本: 1.0
# 依赖: MCDReforged >= 2.0.0

import time
from threading import Timer
from mcdreforged.api.all import *

PLUGIN_METADATA = {
    'id': 'vote_to_kick',
    'version': '1.0.0',
    'name': 'Vote to kick',
    'description': '一个插件，可以让玩家通过投票的方式将其他玩家踢出服务器',
    'author': 'Tiking_',
    'link': 'https://github.com/Tiking-010/vote_to_kick',
    'dependencies': {
        'mcdreforged': '>=2.0.0',
    }
}

# 发起投票的指令前缀
PREFIX = '!!kick'

# 踢出玩家所需的最低同意票数百分比
THRESHOLD = 0.8

# 投票持续的时间（秒）
DURATION = 60

# 两次投票之间的冷却时间（秒）
COOLDOWN = 300

# 投票开始时发送的信息
VOTE_START_MSG = '{0} 发起投票，要将 {1} 踢出服务器，同意输入 #yes，拒绝输入 #no'

# 投票成功时发送的信息
VOTE_SUCCESS_MSG = '投票成功，{0} 被踢出服务器'

# 投票失败时发送的信息
VOTE_FAIL_MSG = '投票失败，{0} 未被踢出服务器'

# 投票取消时发送的信息
VOTE_CANCEL_MSG = '投票取消，{0} 未被踢出服务器'

# 投票玩家人数过低时发送的信息
VOTE_LOW_MSG = '投票玩家人数过低'

# 已经有一个投票在进行中时发送的信息
VOTE_BUSY_MSG = '已经有一个投票在进行中，请稍后再试'

# 指令无效时发送的信息
VOTE_INVALID_MSG = '无效的指令，请输入 {0} [玩家名称] 来发起投票'

# 目标玩家不在线时发送的信息
VOTE_OFFLINE_MSG = '目标玩家不在线，请检查玩家名称是否正确'

# 源玩家试图踢出自己时发送的信息
VOTE_SELF_MSG = '你不能踢出自己，请输入其他玩家的名称'

# 源玩家试图踢出服务器主人时发送的信息
VOTE_OWNER_MSG = '你不能踢出服务器的主人，请尊重服务器的创建者'

# 源玩家试图踢出控制台时发送的信息
VOTE_CONSOLE_MSG = '你不能踢出控制台，请不要搞事情'

# 投票功能正在冷却中时发送的信息
VOTE_COOLDOWN_MSG = '投票功能正在冷却中，请 {0} 秒后再试'

# 全局变量，用来存储投票状态
vote_in_progress = False
vote_source = None
vote_target = None
vote_yes = set()
vote_no = set()
vote_timer = None
vote_cooldown = 0

def on_load(server: ServerInterface, prev_module):
    # 注册投票指令
    server.register_help_message(PREFIX, '发起投票，将其他玩家踢出服务器')
    server.register_command(
        Literal(PREFIX).
        then(
            Text('target').
            runs(lambda src, ctx: vote_start(server, src, ctx['target']))
        ).
        runs(lambda src: vote_invalid(server, src))
    )

def on_user_info(server: ServerInterface, info: Info):
    # 处理投票信息
    if info.is_player and vote_in_progress:
        content = info.content
        if content == '#yes':
            vote_yes.add(info.player)
        elif content == '#no':
            vote_no.add(info.player)

def vote_start(server: ServerInterface, source: CommandSource, target: str):
    # 开始一个投票，将目标玩家踢出服务器
    global vote_in_progress, vote_source, vote_target, vote_yes, vote_no, vote_timer, vote_cooldown
    # 检查冷却时间
    if time.time() < vote_cooldown:
        source.reply(VOTE_COOLDOWN_MSG.format(int(vote_cooldown - time.time())))
        return
    # 检查是否已经有一个投票在进行中
    if vote_in_progress:
        source.reply(VOTE_BUSY_MSG)
        return
    # 检查目标玩家是否有效
    if target == source.player:
        source.reply(VOTE_SELF_MSG)
        return
    if target == server.server_owner:
        source.reply(VOTE_OWNER_MSG)
        return
    if target == '控制台':
        source.reply(VOTE_CONSOLE_MSG)
        return
    if not server.get_player_info(target):
        source.reply(VOTE_OFFLINE_MSG)
        return
    # 初始化投票状态
    vote_in_progress = True
    vote_source = source.player
    vote_target = target
    vote_yes = set()
    vote_no = set()
    # 广播投票信息
    server.say(VOTE_START_MSG.format(vote_source, vote_target))
    # 开始投票计时器
    vote_timer = Timer(DURATION, vote_end, [server])
    vote_timer.start()

def vote_end(server: ServerInterface):
    # 结束投票并检查结果
    global vote_in_progress, vote_source, vote_target, vote_yes, vote_no, vote_timer, vote_cooldown
    # 取消投票计时器
    vote_timer.cancel()
    # 获取在线玩家
    online_players = set(server.get_online_players())
    # 检查是否有足够的玩家参与投票
    if len(online_players) < 2:
        server.say(VOTE_LOW_MSG)
        vote_reset()
        return
    # 计算同意票数的百分比
    yes_percentage = len(vote_yes) / len(online_players)
    # 检查同意票数是否超过阈值
    if yes_percentage >= THRESHOLD:
        # 踢出目标玩家
        server.execute('kick {}'.format(vote_target))
        # 广播成功信息
        server.say(VOTE_SUCCESS_MSG.format(vote_target))
    else:
        # 广播失败信息
        server.say(VOTE_FAIL_MSG.format(vote_target))
    # 重置投票状态
    vote_reset()
    # 设置冷却时间
    vote_cooldown = time.time() + COOLDOWN

def vote_reset():
    # 重置投票状态
    global vote_in_progress, vote_source, vote_target, vote_yes, vote_no, vote_timer
    vote_in_progress = False
    vote_source = None
    vote_target = None
    vote_yes = set()
    vote_no = set()
    vote_timer = None

def vote_invalid(server: ServerInterface, source: CommandSource):
    # 发送无效指令信息
    source.reply(VOTE_INVALID_MSG.format(PREFIX))
