from astrbot.api.event import filter, MessageEvent, EventResult  # 兼容旧版 Event 命名
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

@register(
    "astrbot_plugin_message_relay",
    "cupcatOOO",
    "机器人主动向指定会话传话插件",
    "1.0.2",  # 版本更新：彻底移除 Comp 依赖
    "https://github.com/cupcatOOO/astrbot_plugin_message_relay"
)
class MessageRelayPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        logger.info("传话插件（无依赖版）初始化完成，支持 /relay 指令")

    # 核心传话指令：完全纯文本实现，无任何组件依赖
    @filter.command("relay")
    async def relay_message(self, event: MessageEvent, target_umo: str, *message_parts):
        """
        主动向指定会话发送传话消息（纯文本版）
        用法：/relay 平台名称:消息类型:会话ID 你要传递的消息
        示例：/relay aiocqhttp:GROUP_MESSAGE:123456 大家记得参加会议
        平台名称参考：aiocqhttp(QQ个人号)、qqofficial(QQ官方接口)、feishu(飞书)等
        消息类型：GROUP_MESSAGE(群聊)、PRIVATE_MESSAGE(私聊)
        """
        # 拼接传话内容（处理多段消息）
        relay_content = " ".join(message_parts)
        if not relay_content:
            # 直接返回纯文本结果，不使用任何组件
            yield EventResult(text="错误：传话内容不能为空！")
            return

        # 构造纯文本消息（带来源标识，清晰明了）
        sender_name = getattr(event, "sender_name", "未知用户")  # 兼容不同版本的 sender 字段
        if not sender_name or sender_name == "未知用户":
            sender_name = getattr(event, "get_sender_name", lambda: "未知用户")()  # 降级获取 sender 名称
        
        # 最终纯文本消息内容（无任何组件依赖）
        final_message = f"【机器人传话】\n发送者：{sender_name}\n消息内容：{relay_content}"

        try:
            # 优先尝试 message_chain 参数（兼容新版）
            try:
                send_success = await self.context.send_message(
                    session=target_umo,
                    message_chain=final_message  # 即使是纯文本，部分版本仍要求用 message_chain
                )
            except Exception as e1:
                # 若 message_chain 报错，切换为 message 参数（兼容旧版）
                if "message_chain" in str(e1) or "参数" in str(e1):
                    send_success = await self.context.send_message(
                        session=target_umo,
                        message=final_message  # 旧版常用参数名
                    )
                else:
                    raise e1  # 非参数问题，抛出原异常
            
            if send_success:
                yield EventResult(text=f"✅ 传话成功！已向 {target_umo} 发送消息")
            else:
                yield EventResult(text=f"❌ 传话失败：未找到目标会话或平台不支持主动消息")
        except Exception as e:
            logger.error(f"传话核心异常：{str(e)}")
            yield EventResult(text=f"❌ 传话失败：{str(e)}\n请检查：1.目标会话标识格式 2.平台是否支持主动消息")

    # 帮助指令（纯文本响应）
    @filter.command("relay_help", alias={"传话帮助", "relay用法"})
    async def relay_help(self, event: MessageEvent):
        """查看传话插件的使用方法（无依赖版）"""
        help_text = """
📢 传话插件使用说明（纯文本无依赖版）
核心指令：/relay 目标会话标识 消息内容
—————— 示例用法 ——————
1. 群聊传话：/relay aiocqhttp:GROUP_MESSAGE:123456 明天10点开会
2. 私聊传话：/relay aiocqhttp:PRIVATE_MESSAGE:789012 记得查收文件
—————— 关键说明 ——————
• 会话标识格式：平台名称:消息类型:会话ID
• 支持平台：aiocqhttp(QQ个人号)、telegram、feishu等
• 不支持：QQ官方接口、钉钉、企业微信（无主动消息权限）
• 会话ID获取：群聊=群号，私聊=对方用户ID（如QQ号）
—————— 常见问题 ——————
❓ 提示“未找到会话”：检查平台名称/消息类型/会话ID是否全部正确
❓ 提示“不支持主动消息”：目标平台无主动推送权限，无法传话
        """
        yield EventResult(text=help_text.strip())

    async def terminate(self):
        """插件卸载时释放资源"""
        logger.info("传话插件（无依赖版）已卸载")
