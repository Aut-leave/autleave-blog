---
title: "curl"
date: 2026-10-18T11:54:06+08:00
draft: false
---

# curl 常用命令速查表

> 基本语法：`curl [选项] <URL>`  
> 短选项与长选项等价，如 `-H` 与 `--header`。

---

## 一、请求方法与数据

| 选项                          | 说明                                                 | 示例                                                         |
| --------------------------- | -------------------------------------------------- | ---------------------------------------------------------- |
| `-X, --request <method>`    | 指定 HTTP 方法（含自定义方法）                                 | `curl -X POST https://api.example.com`                     |
| `-d, --data <data>`         | 发送请求体（默认 POST，`application/x-www-form-urlencoded`） | `curl -d "name=alice&age=20" https://api.example.com`      |
| `--data-raw <data>`         | 同 `-d`，但不处理 `@` 符号                                 | `curl --data-raw '{"a":1}' https://api.example.com`        |
| `--data-binary <data>`      | 原样发送二进制数据                                          | `curl --data-binary @file.bin https://api.example.com`     |
| `-F, --form <name=content>` | 发送 multipart/form-data（文件上传）                       | `curl -F "file=@photo.jpg" https://api.example.com/upload` |
| `-G, --get`                 | 把 `-d` 数据拼到 URL 查询串，改用 GET                         | `curl -G -d "q=curl" https://api.example.com/search`       |

**常用组合**

```bash

# JSON POST
curl -X POST https://api.example.com/users \
  -H "Content-Type: application/json" \
  -d '{"name":"alice","age":20}'
# 表单 POST
curl -X POST https://api.example.com/login \
  -d "username=admin&password=123456"
# 文件上传
curl -F "file=@./test.zip" -F "name=demo" https://api.example.com/upload
# 自定义方法
curl -X GRAB https://api.example.com/entrance
```

---

## 二、请求头（Headers）

|选项|说明|示例|
|---|---|---|
|`-H, --header <header>`|添加/修改请求头|`curl -H "Content-Type: application/json" https://api.example.com`|
|`-A, --user-agent <ua>`|设置 `User-Agent`|`curl -A "Mozilla/5.0" https://example.com`|
|`-e, --referer <url>`|设置 `Referer`|`curl -e "https://google.com" https://example.com`|
|`-H "Header:"`|删除某个请求头（冒号后留空）|`curl -H "Accept:" https://example.com`|

**常见伪造头**

~~~bash

# 伪造来源
curl -e "https://lemu.de/" http://target/api
# 伪造客户端 IP
curl -H "X-Forwarded-For: 127.0.0.1" http://target/admin
curl -H "X-Real-IP: 127.0.0.1" http://target/admin
# 伪造 UA
curl -A "LeMMIH/0.1" http://target/api
~~~
---

## 三、响应处理与输出

|选项|说明|示例|
|---|---|---|
|`-i, --include`|输出中包含响应头|`curl -i https://example.com`|
|`-I, --head`|只请求响应头（HEAD 方法）|`curl -I https://example.com`|
|`-o, --output <file>`|保存响应到指定文件|`curl -o page.html https://example.com`|
|`-O, --remote-name`|用 URL 中的文件名保存|`curl -O https://example.com/file.zip`|
|`-s, --silent`|静默模式，不显示进度/错误|`curl -s https://api.example.com`|
|`-S, --show-error`|与 `-s` 搭配，静默但显示错误|`curl -sS https://api.example.com`|
|`-w, --write-out <format>`|请求后输出指定信息|`curl -s -o /dev/null -w "%{http_code}" https://example.com`|

**常用状态码检测**

~~~bash

# 只看 HTTP 状态码
curl -s -o /dev/null -w "%{http_code}\n" https://example.com
# 输出耗时、状态码、大小
curl -s -o /dev/null -w "code=%{http_code} time=%{time_total}s size=%{size_download}\n" https://example.com
~~~
---

## 四、重定向与连接控制

|选项|说明|示例|
|---|---|---|
|`-L, --location`|自动跟随 3xx 重定向|`curl -L https://example.com`|
|`--max-redirs <n>`|限制最大重定向次数|`curl -L --max-redirs 3 https://example.com`|
|`--connect-timeout <sec>`|连接超时时间|`curl --connect-timeout 5 https://example.com`|
|`-m, --max-time <sec>`|整个请求最大耗时|`curl -m 10 https://example.com`|
|`--retry <n>`|失败重试次数|`curl --retry 3 https://example.com`|
|`-k, --insecure`|跳过 SSL 证书校验|`curl -k https://self-signed.example.com`|
|`--http1.1` / `--http2`|指定 HTTP 协议版本|`curl --http2 https://example.com`|

---

## 五、认证

| 选项                                   | 说明           | 示例                                                               |
| ------------------------------------ | ------------ | ---------------------------------------------------------------- |
| `-u, --user <user:pass>`             | Basic 认证     | `curl -u admin:123456 https://api.example.com`                   |
| `--digest`                           | Digest 认证    | `curl --digest -u admin:123456 https://api.example.com`          |
| `-H "Authorization: Bearer <token>"` | Bearer Token | `curl -H "Authorization: Bearer abc123" https://api.example.com` |
| `-E, --cert <cert>`                  | 客户端证书        | `curl -E client.pem https://api.example.com`                     |

~~~bash

# Basic 认证（等价于 -u）
curl -H "Authorization: Basic $(echo -n 'admin:123456' | base64)" https://api.example.com
# 从文件读取 token 变量
curl -H "Authorization: Bearer $(cat token.txt)" https://api.example.com
~~~
---

## 六、Cookie 处理

|选项|说明|示例|
|---|---|---|
|`-b, --cookie <data\|file>`|发送 Cookie|`curl -b "session=abc123" https://example.com`|
|`-c, --cookie-jar <file>`|保存响应中的 Cookie 到文件|`curl -c cookies.txt https://example.com`|
|`-b cookies.txt`|读取之前保存的 Cookie|`curl -b cookies.txt https://example.com`|

~~~bash

# 登录并保存 Cookie，再用 Cookie 访问
curl -c cookies.txt -d "user=admin&pass=123" https://example.com/login
curl -b cookies.txt https://example.com/profile
~~~
---

## 七、代理

|选项|说明|示例|
|---|---|---|
|`-x, --proxy <[protocol://]host:port>`|指定代理|`curl -x http://127.0.0.1:8080 https://example.com`|
|`--noproxy <list>`|指定不走代理的主机，`"*"` 表示全部|`curl --noproxy "*" https://example.com`|
|`-U, --proxy-user <user:pass>`|代理认证|`curl -x http://proxy:8080 -U user:pass https://example.com`|

~~~bash

# 强制直连，绕过系统代理（你原命令中的用法）
curl --noproxy "*" http://202.120.222.171:31876/api/entrance
~~~
---

## 八、调试与详细输出

| 选项                     | 说明                | 示例                                                 |
| ---------------------- | ----------------- | -------------------------------------------------- |
| `-v, --verbose`        | 显示详细请求/响应过程（首选调试） | `curl -v https://example.com`                      |
| `--trace <file>`       | 输出完整通信数据到文件       | `curl --trace trace.txt https://example.com`       |
| `--trace-ascii <file>` | 以 ASCII 输出通信数据    | `curl --trace-ascii trace.txt https://example.com` |
| `-s -v`                | 静默+详细，去掉进度条只留详情   | `curl -s -v https://example.com`                   |

~~~bash

# 常用调试：看请求头、响应头、状态码
curl -v https://example.com
# 只保留响应头（不发请求体）
curl -s -D - -o /dev/null https://example.com
~~~
---

## 九、文件传输与断点续传

|选项|说明|示例|
|---|---|---|
|`-O`|下载并保留远程文件名|`curl -O https://example.com/file.zip`|
|`-C, --continue-at <offset>`|断点续传，`-` 表示自动续传|`curl -C - -O https://example.com/file.zip`|
|`-T, --upload-file <file>`|上传文件（PUT）|`curl -T file.txt https://example.com/upload`|
|`--limit-rate <rate>`|限速|`curl --limit-rate 200K -O https://example.com/file.zip`|

~~~bash

# 断点续传
curl -C - -O https://example.com/bigfile.iso
# PUT 上传
curl -X PUT -T local.txt https://api.example.com/files/local.txt
~~~
---

## 十、其他实用选项

|选项|说明|示例|
|---|---|---|
|`--resolve <host:port:addr>`|强制域名解析到指定 IP|`curl --resolve example.com:443:1.2.3.4 https://example.com`|
|`--interface <iface>`|指定网卡/源 IP|`curl --interface 127.0.0.1 https://example.com`|
|`--path-as-is`|保留 URL 中的 `..` 不规范化|`curl --path-as-is https://example.com/a/../b`|
|`--url <url>`|指定 URL（可多个）|`curl --url https://a.com --url https://b.com`|
|`-g, --globoff`|关闭 `{}` `[]` 的通配展开|`curl -g "https://example.com/?q=[1]"`|
|`-4` / `-6`|强制 IPv4 / IPv6|`curl -4 https://example.com`|

---

## 十一、CTF / 安全题高频组合

~~~bash

# 1. 自定义方法 + 伪造来源 + 伪造 UA + 禁代理
curl.exe --noproxy "*" -X GRAB -A "LeMMIH/0.1" -e "https://lemu.de/" \
  "http://202.120.222.171:31876/api/entrance"
# 2. 伪造本地 IP 访问管理员页
curl -H "X-Forwarded-For: 127.0.0.1" http://target/admin.php
# 3. 修改 Cookie 越权
curl -b "admin=1" http://target/index.php
# 4. Basic 认证爆破（配合字典循环）
for p in $(cat pass.txt); do
  code=$(curl -s -o /dev/null -w "%{http_code}" -u "admin:$p" http://target/)
  [ "$code" = "200" ] && echo "FOUND: $p"
done
# 5. 只取响应头看重定向
curl -I http://target/
# 6. 保留路径穿越，不规范化
curl --path-as-is "http://target/static/../../etc/passwd"
# 7. 发送 JSON 并看状态码
curl -s -o /dev/null -w "%{http_code}\n" -X POST \
  -H "Content-Type: application/json" -d '{"id":1}' http://target/api
~~~
---

## 十二、速记口诀

- **改方法** → `-X`
    
- **加头** → `-H`；UA → `-A`；来源 → `-e`
    
- **发数据** → `-d`（表单/JSON）；上传文件 → `-F`
    
- **跟随跳转** → `-L`
    
- **看响应头** → `-i` / `-I`
    
- **存文件** → `-o` / `-O`
    
- **静默** → `-s`；调试 → `-v`
    
- **认证** → `-u`
    
- **Cookie** → `-b` 发送 / `-c` 保存
    
- **代理** → `-x` 用代理 / `--noproxy "*"` 禁代理
    
- **状态码** → `-w "%{http_code}"`
    

> 核心原则：curl 的选项都是“拼装 HTTP 请求”的零件——方法、URL、头、体、认证、代理、重定向，按题目要求组合即可。

本回答由 AI 生成，内容仅供参考，请仔细甄别

# 题目

- [Digging into HTTP](/notes/web/webwp/digging-into-http/)
