#!/usr/bin/env python3
"""
ticket_server.py - 工单管理 MCP Server
基于 MCP 协议实现的工单 CRUD 系统，使用 SQLite 存储
"""

import json
import sqlite3
import sys
import uuid
from datetime import datetime
from typing import Any


DB_PATH = "tickets.db"


def init_database():
    """初始化数据库表结构"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'open',
            user_id TEXT NOT NULL,
            user_name TEXT DEFAULT '',
            platform TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            comments TEXT DEFAULT '[]'
        )
    """)
    conn.commit()
    conn.close()


class TicketMCPServer:
    """工单管理 MCP Server"""

    def __init__(self):
        init_database()

    def handle_request(self, request: dict) -> dict:
        """处理 MCP 请求"""
        method = request.get("method", "")
        req_id = request.get("id")

        handlers = {
            "initialize": self._handle_initialize,
            "tools/list": self._handle_list_tools,
            "tools/call": self._handle_call_tool,
        }

        handler = handlers.get(method)
        if handler:
            result = handler(request)
            return {"jsonrpc": "2.0", "id": req_id, "result": result}

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Unknown method: {method}"},
        }

    def _handle_initialize(self, request: dict) -> dict:
        return {
            "protocolVersion": "2024-11-05",
            "serverInfo": {
                "name": "ticket-server",
                "version": "1.0.0",
            },
            "capabilities": {"tools": {}},
        }

    def _handle_list_tools(self, request: dict) -> dict:
        return {
            "tools": [
                {
                    "name": "create_ticket",
                    "description": "创建新的客服工单",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "工单标题",
                            },
                            "description": {
                                "type": "string",
                                "description": "问题详细描述",
                            },
                            "priority": {
                                "type": "string",
                                "enum": ["low", "medium", "high", "urgent"],
                                "description": "优先级",
                                "default": "medium",
                            },
                            "user_id": {
                                "type": "string",
                                "description": "用户 ID",
                            },
                            "user_name": {
                                "type": "string",
                                "description": "用户名称",
                            },
                            "platform": {
                                "type": "string",
                                "description": "来源平台",
                            },
                        },
                        "required": ["title", "description", "user_id"],
                    },
                },
                {
                    "name": "get_ticket",
                    "description": "根据工单 ID 查询工单详情",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "ticket_id": {
                                "type": "string",
                                "description": "工单 ID",
                            },
                        },
                        "required": ["ticket_id"],
                    },
                },
                {
                    "name": "list_user_tickets",
                    "description": "列出指定用户的所有工单",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "用户 ID",
                            },
                            "status": {
                                "type": "string",
                                "enum": [
                                    "open",
                                    "in_progress",
                                    "resolved",
                                    "closed",
                                ],
                                "description": "按状态过滤",
                            },
                        },
                        "required": ["user_id"],
                    },
                },
                {
                    "name": "update_ticket",
                    "description": "更新工单状态或添加备注",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "ticket_id": {
                                "type": "string",
                                "description": "工单 ID",
                            },
                            "status": {
                                "type": "string",
                                "enum": [
                                    "open",
                                    "in_progress",
                                    "resolved",
                                    "closed",
                                ],
                                "description": "新状态",
                            },
                            "comment": {
                                "type": "string",
                                "description": "更新备注",
                            },
                        },
                        "required": ["ticket_id"],
                    },
                },
            ]
        }

    def _handle_call_tool(self, request: dict) -> dict:
        params = request.get("params", {})
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        tool_handlers = {
            "create_ticket": self._create_ticket,
            "get_ticket": self._get_ticket,
            "list_user_tickets": self._list_user_tickets,
            "update_ticket": self._update_ticket,
        }

        handler = tool_handlers.get(tool_name)
        if not handler:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"未知工具: {tool_name}",
                    }
                ],
                "isError": True,
            }

        try:
            result = handler(arguments)
            return {
                "content": [
                    {"type": "text", "text": json.dumps(result, ensure_ascii=False)}
                ]
            }
        except Exception as e:
            return {
                "content": [{"type": "text", "text": f"执行出错: {str(e)}"}],
                "isError": True,
            }

    def _create_ticket(self, args: dict) -> dict:
        """创建工单"""
        ticket_id = f"TK-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now().isoformat()

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO tickets
                (ticket_id, title, description, priority, status,
                 user_id, user_name, platform, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'open', ?, ?, ?, ?, ?)
            """,
            (
                ticket_id,
                args["title"],
                args["description"],
                args.get("priority", "medium"),
                args["user_id"],
                args.get("user_name", ""),
                args.get("platform", ""),
                now,
                now,
            ),
        )
        conn.commit()
        conn.close()

        return {
            "success": True,
            "ticket_id": ticket_id,
            "message": f"工单 {ticket_id} 创建成功",
            "created_at": now,
        }

    def _get_ticket(self, args: dict) -> dict:
        """查询工单"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM tickets WHERE ticket_id = ?", (args["ticket_id"],)
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return {"success": False, "message": "工单不存在"}

        return {"success": True, "ticket": dict(row)}

    def _list_user_tickets(self, args: dict) -> dict:
        """列出用户工单"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if "status" in args:
            cursor.execute(
                "SELECT * FROM tickets WHERE user_id = ? AND status = ? ORDER BY created_at DESC",
                (args["user_id"], args["status"]),
            )
        else:
            cursor.execute(
                "SELECT * FROM tickets WHERE user_id = ? ORDER BY created_at DESC",
                (args["user_id"],),
            )

        rows = cursor.fetchall()
        conn.close()

        return {
            "success": True,
            "count": len(rows),
            "tickets": [dict(row) for row in rows],
        }

    def _update_ticket(self, args: dict) -> dict:
        """更新工单"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM tickets WHERE ticket_id = ?", (args["ticket_id"],)
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            return {"success": False, "message": "工单不存在"}

        now = datetime.now().isoformat()
        updates = []
        values = []

        if "status" in args:
            updates.append("status = ?")
            values.append(args["status"])

        if "comment" in args:
            comments = json.loads(row["comments"])
            comments.append({
                "text": args["comment"],
                "timestamp": now,
            })
            updates.append("comments = ?")
            values.append(json.dumps(comments, ensure_ascii=False))

        updates.append("updated_at = ?")
        values.append(now)
        values.append(args["ticket_id"])

        cursor.execute(
            f"UPDATE tickets SET {', '.join(updates)} WHERE ticket_id = ?",
            values,
        )
        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": f"工单 {args['ticket_id']} 更新成功",
            "updated_at": now,
        }

    def run(self):
        """启动 MCP Server，通过 stdin/stdout 通信"""
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break

                request = json.loads(line.strip())
                response = self.handle_request(request)
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
            except json.JSONDecodeError:
                continue
            except KeyboardInterrupt:
                break


if __name__ == "__main__":
    server = TicketMCPServer()
    server.run()