#!/usr/bin/env python3
"""
message_router.py - 多平台消息路由器
将不同平台的消息统一转发给 Nanobot 处理
"""

import json
import os
import subprocess
from datetime import datetime

from flask import Flask, request, jsonify

app = Flask(__name__)


class NanobotBridge:
    """Nanobot 交互桥接器"""

    @staticmethod
    def send_to_nanobot(prompt: str) -> str:
        """将消息发送给 Nanobot 并获取回复"""
        try:
            result = subprocess.run(
                ["nanobot", "chat", "--config", "config.json", prompt],
                capture_output=True,
                text=True,
                timeout=60,
            )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            return "抱歉，处理超时了，请稍后再试。"
        except Exception as e:
            return f"系统暂时出了点问题，请稍后再试。(错误码: {hash(str(e)) % 10000})"


# ==================== 飞书接入 ====================

@app.route("/webhook/feishu", methods=["POST"])
def feishu_webhook():
    """飞书消息接收端点"""
    data = request.json

    if data.get("type") == "url_verification":
        return jsonify({"challenge": data.get("challenge")})

    event = data.get("event", {})
    message = event.get("message", {})
    content = json.loads(message.get("content", "{}"))
    text = content.get("text", "").strip()

    if not text:
        return jsonify({"code": 0})

    sender = event.get("sender", {})
    user_id = sender.get("sender_id", {}).get("user_id", "unknown")

    prompt = (
        f"[来源: 飞书] [用户ID: {user_id}]\n\n"
        f"用户提问: {text}"
    )

    reply = NanobotBridge.send_to_nanobot(prompt)

    feishu_reply(message.get("message_id"), reply)

    return jsonify({"code": 0})


def feishu_reply(message_id: str, text: str):
    """回复飞书消息"""
    import urllib.request

    token = get_feishu_tenant_token()
    url = f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/reply"
    payload = {
        "content": json.dumps({"text": text}),
        "msg_type": "text",
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
    )
    urllib.request.urlopen(req, timeout=10)


def get_feishu_tenant_token() -> str:
    """获取飞书 tenant_access_token"""
    import urllib.request

    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = {
        "app_id": os.getenv("FEISHU_APP_ID"),
        "app_secret": os.getenv("FEISHU_APP_SECRET"),
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read())
        return result.get("tenant_access_token", "")


# ==================== 钉钉接入 ====================

@app.route("/webhook/dingtalk", methods=["POST"])
def dingtalk_webhook():
    """钉钉消息接收端点"""
    data = request.json
    text = data.get("text", {}).get("content", "").strip()

    if not text:
        return jsonify({"msgtype": "empty"})

    user_id = data.get("senderStaffId", "unknown")

    prompt = (
        f"[来源: 钉钉] [用户ID: {user_id}]\n\n"
        f"用户提问: {text}"
    )

    reply = NanobotBridge.send_to_nanobot(prompt)

    session_webhook = data.get("sessionWebhook", "")
    if session_webhook:
        dingtalk_reply(session_webhook, reply)

    return jsonify({"msgtype": "text", "text": {"content": reply}})


def dingtalk_reply(webhook_url: str, text: str):
    """通过 sessionWebhook 回复钉钉消息"""
    import urllib.request

    payload = {"msgtype": "text", "text": {"content": text}}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
    )
    urllib.request.urlopen(req, timeout=10)


# ==================== Telegram 接入 ====================

@app.route("/webhook/telegram", methods=["POST"])
def telegram_webhook():
    """Telegram 消息接收端点"""
    data = request.json
    message = data.get("message", {})
    text = message.get("text", "").strip()

    if not text or text.startswith("/start"):
        return jsonify({"ok": True})

    chat_id = message.get("chat", {}).get("id")
    user = message.get("from", {})
    user_name = user.get("first_name", "")

    prompt = (
        f"[来源: Telegram] [用户: {user_name}({user.get('id', '')})]\n\n"
        f"用户提问: {text}"
    )

    reply = NanobotBridge.send_to_nanobot(prompt)

    telegram_reply(chat_id, reply)

    return jsonify({"ok": True})


def telegram_reply(chat_id: int, text: str):
    """回复 Telegram 消息"""
    import urllib.request

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    urllib.request.urlopen(req, timeout=10)


# ==================== 健康检查 ====================

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "platforms": {
            "feishu": bool(os.getenv("FEISHU_APP_ID")),
            "dingtalk": bool(os.getenv("DINGTALK_APP_KEY")),
            "telegram": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
        },
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)