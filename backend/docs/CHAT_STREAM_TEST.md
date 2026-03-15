# 流式对话接口测试说明

## 为什么 Postman 里看不到流式内容？

Postman 对 **Server-Sent Events (SSE)** 流式响应的支持有限，经常出现：

- 状态码 200 OK，但 Body 里没有内容
- 只显示 “Connection closed” / “Connected to the URL”

这是客户端的显示问题，不是服务端没返回数据。服务端会按 SSE 规范持续推送 `data: ...` 行。

## 如何验证服务端确实在流式返回？

用 **curl** 在终端里请求，可以直接看到逐行输出：

```bash
curl -N -X POST "http://127.0.0.1:8866/api/v1/chat/completions" ^
  -H "Content-Type: application/json" ^
  -d "{\"model\":\"gpt-5.2\",\"messages\":[{\"role\":\"user\",\"content\":\"你好\"}],\"stream\":true}"
```

Windows PowerShell：

```powershell
curl.exe -N -X POST "http://127.0.0.1:8866/api/v1/chat/completions" `
  -H "Content-Type: application/json" `
  -d '{"model":"got-5.2","messages":[{"role":"user","content":"你好"}],"stream":true}'
```

**注意**：`-N` 会禁用 curl 的缓冲，才能边收边打印。若能看到多行 `data: {...}` 或 `data: [DONE]`，说明服务端流式正常。

## 前端如何消费流式接口？

使用 `EventSource` 仅支持 GET。对 POST + 流式，请用 **fetch + ReadableStream** 或 **axios** 读 `response.body` 流，按行解析 `data: ...`，遇到 `data: [DONE]` 结束。
