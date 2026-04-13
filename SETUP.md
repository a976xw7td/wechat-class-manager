# SETUP — wechat_bridge.py

## 环境要求

- macOS（Apple Silicon 或 Intel）
- Python 3.10+
- Node.js 16+（用于安装 wechat-cli）
- 微信 Mac 客户端已安装并登录

## 安装步骤

### 1. 安装 wechat-cli

```bash
npm install -g @canghe_ai/wechat-cli
```

### 2. 初始化（需要微信在运行中）

```bash
sudo wechat-cli init
```

按提示选择你的微信账号数据目录。

> **注意：** 如果 init 提示需要对微信重新签名，按照提示退出微信、重新打开再执行一次即可。如果微信无法打开，运行以下命令修复签名后重试：
> ```bash
> sudo codesign --force --deep --sign - /Applications/WeChat.app
> ```

### 3. 验证安装

```bash
wechat-cli sessions
```

能看到群聊列表说明安装成功。

## 使用方法

```bash
python wechat_bridge.py --group "群名称" --days 7 --output messages.jsonl
```

参数说明：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--group` | 微信群名称（必填） | - |
| `--days` | 提取最近几天的消息 | 7 |
| `--output` | 输出文件路径 | messages.jsonl |

## 输出格式

每行一条消息（JSON Lines 格式）：

```json
{
  "msg_id": "唯一消息ID",
  "timestamp": "2026-04-12T22:40:00+08:00",
  "sender": {
    "wechat_id": "发送者ID",
    "nickname": "昵称"
  },
  "type": "text|image|file|voice|link|system",
  "content": "消息内容",
  "media_ref": "附件路径（如有）",
  "reply_to": "被回复消息ID（如有）"
}
```

## 消息类型说明

| type | 含义 |
|------|------|
| text | 文字消息 |
| image | 图片 |
| file | 文件 |
| voice | 语音 |
| link | 链接/小程序 |
| system | 系统通知 |
