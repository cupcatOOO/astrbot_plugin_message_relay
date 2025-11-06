from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
# 兼容处理：适配不同版本的组件导入
try:
    from astrbot.api.message_components import Component as Comp
except ImportError:
    try:
        from astrbot.api.message_components import Comp
    except ImportError:
        # 若仍导入失败，使用基础消息构造方式
        Comp = None

@register(
    "astrbot_plugin_message_relay",
    "cupcatOOO",
    "机器人主动向指定会话传话插件",
    "1.0.1",  # 版本更新：修复组件导入问题
    "https://github.com/cupcatOOO/astrbot_plugin_message_relay"
)
class MessageRelayPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        logger.info("传话插件（修复版）初始化完成，支持 /relay 指令")

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

        # 兼容不同版本的消息构造方式
        if Comp and hasattr(Comp, "Plain"):
            # 方式1：使用组件构造（兼容大部分版本）
            message_chain = [
                Comp.Plain(text=f"【机器人传话】来自 {event.get_sender_name()} 的消息：\n"),
                Comp.Plain(text=relay_content)
            ]
        else:
            # 方式2：直接使用纯文本消息（最低兼容版本）
            message_chain = f"【机器人传话】来自 {event.get_sender_name()} 的消息：\n{relay_content}"

        try:
            # 调用主动发送消息接口（兼容不同版本的参数传递）
            if isinstance(message_chain, list):
                send_success = await self.context.send_message(
                    session=target_umo,
                    message_chain=message_chain
                )
            else:
                # 若平台只支持纯文本，直接传递字符串
                send_success = await self.context.send_message(
                    session=target_umo,
                    message=message_chain  # 部分版本参数名为 message 而非 message_chain
                )
            
            if send_success:
                yield event.plain_result(f"传话成功！已向 {target_umo} 发送消息")
            else:
                yield event.plain_result(f"传话失败：未找到目标会话或平台不支持主动消息")
        except Exception as e:
            # 捕获参数名不匹配的异常（兼容 message/message_chain 差异）
            if "message_chain" in str(e) and "message" not in str(e):
                try:
                    send_success = await self.context.send_message(
                        session=target_umo,
                        message=message_chain
                    )
                    yield event.plain_result(f"传话成功！已向 {target_umo} 发送消息")
                except Exception as e2:
                    logger.error(f"兼容模式传话异常：{str(e2)}")
                    yield event.plain_result(f"传话失败：{str(e2)}")
            else:
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
        logger.info("传话插件（修复版）已卸载")
