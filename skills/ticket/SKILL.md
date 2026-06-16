# 工单管理技能

## 描述
通过 MCP Server 创建、查询和更新工单。

## 可用工具（来自 ticket_server MCP）

### create_ticket
创建新工单。

参数：
- `title` (string, 必填): 工单标题
- `description` (string, 必填): 问题描述
- `priority` (string): 优先级 - low/medium/high/urgent
- `user_id` (string, 必填): 用户 ID
- `user_name` (string): 用户名称
- `platform` (string): 来源平台

### get_ticket
查询工单状态。

参数：
- `ticket_id` (string, 必填): 工单 ID

### list_user_tickets
列出用户的所有工单。

参数：
- `user_id` (string, 必填): 用户 ID
- `status` (string): 过滤状态 - open/in_progress/resolved/closed

### update_ticket
更新工单状态。

参数：
- `ticket_id` (string, 必填): 工单 ID
- `status` (string): 新状态
- `comment` (string): 更新备注

## 使用场景

1. **用户问题无法通过 FAQ 解决** → 创建 medium 优先级工单
2. **用户投诉或紧急问题** → 创建 urgent 优先级工单
3. **用户询问之前的问题** → 查询工单状态
4. **用户确认问题已解决** → 更新工单为 resolved