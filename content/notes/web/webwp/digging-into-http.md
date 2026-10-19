---
title: "Digging into HTTP"
date: 2026-10-17T18:23:01+08:00
weight: 6
draft: false
---

f12找到```<!--API Endpoint /api/entrance-->```，访问`http://202.120.222.171:31876/api/entrance`，显示要以LeMMIH/0.1 or higher version访问，问gpt一些基础[curl](/notes/web/http/curl/)，运行
```powershell
curl.exe -A "LeMMIH/0.1" "http://202.120.222.171:31876/api/entrance"
```
一直502，加上`--noproxy "*"`。

显示Unauthorized access, please access this endpoint from lemu.de。加上```-e "https://lemu.de/"```。

显示Please GRAB instead of GET，加上`-X GRAB`。

得到flag。

后续在做[Flag免费送](/notes/web/webwp/flag免费送/)时学到，也可以用以下代码实现：
```python
import requests

url = "http://202.120.222.171:31876/api/entrance"
headers = {
    "User-Agent": "LeMMIH/0.1",
    "Referer": "https://lemu.de/",
}
s = requests.Session()
s.trust_env = False  #等价 --noproxy "*"
r = s.request("GRAB", url, headers=headers, timeout=10)
print(r.status_code)
print(r.text)
```
