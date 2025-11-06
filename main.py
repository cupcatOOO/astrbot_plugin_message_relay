from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.message_components import Comp
from astrbot.api.event import filter

@register(
    "astrbot_plugin_message_relay",
    "Your Name",
    "机器人主动向指定会话传话插件",
    "1.0.0",
    "你的仓库地址（可选）"
)
class MessageRelayPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        logger.info("传话插件初始化完成，支持 /relay 指令")

    # 传话指令：/relay 目标会话标识 传话内容
    @filter.command("relay")
    async def relay_message(self, event: AstrMessageEvent, target_umo: str, *message_parts):
        """
        主动向指定会话发送传话消息
        用法：/relay 平台名称:消息类型:会话ID 你要传递的消息
        示例：/relay aiocqhttp:GROUP_MESSAGE:123456 大家记得参加会议
        平台名称参考：aiocqhttp(QQ个人号)、qqofficial(QQ官方接口)、feishu(飞书)等
        消息类型：GROUP_MESSAGE(群聊)、PRIVATE_MESSAGE(私聊)
        """
        # 拼接传话内容
        relay_content = " ".join(message_parts)
        if not relay_content:
            yield event.plain_result("错误：传话内容不能为空！")
            return

        # 构建消息链（带传话标识）
        message_chain = [
            Comp.Plain(text=f"【机器人传话】来自 {event.get_sender_name()} 的消息：\n"),
            Comp.Plain(text=relay_content)
        ]

        try:
            # 调用主动发送消息接口
            send_success = await self.context.send_message(
                session=target_umo,
                message_chain=message_chain
            )
            if send_success:
                yield event.plain_result(f"传话成功！已向 {target_umo} 发送消息")
            else:
                yield event.plain_result(f"传话失败：未找到目标会话或平台不支持主动消息")
        except Exception as e:
            logger.error(f"传话异常：{str(e)}")
            yield event.plain_result(f"传话失败：{str(e)}")

    # 查看用法指令
    @filter.command("relay_help", alias={"传话帮助", "relay用法"})
    async def relay_help(self, event: AstrMessageEvent):
        """查看传话插件的使用方法"""
        help_content = """
【传话插件使用说明】
指令：/relay 目标会话标识 消息内容
示例1（群聊传话）：/relay aiocqhttp:GROUP_MESSAGE:123456 明天10点开会
示例2（私聊传话）：/relay aiocqhttp:PRIVATE_MESSAGE:789012 记得查收文件
支持平台：aiocqhttp、telegram、feishu等（参考平台适配矩阵）
注意：QQ官方接口、钉钉等平台可能不支持主动消息
        """
        yield event.plain_result(help_content.strip())

    async def terminate(self):
        """插件卸载时释放资源"""
        logger.info("传话插件已卸载")
