---
title: "Embarking on Games"
date: 2026-10-17T17:49:44+08:00
weight: 1
draft: false
---

要叠满500层，f12阅读一下html，大概率在game.min.js里，发现全部是16进制，找0x1f2(500)，找到
```js
fetch(_0xd8d602(0x1f9), {
            'method': _0xd8d602(0x1c1),
            'headers': {
                'Secret-Code': encodeURIComponent('海月の虚空に秋涼し時鳥')
            }
        })[_0xd8d602(0x1d0)](_0x592092 => {
            const _0x9d02a5 = _0xd8d602;
            if (_0x592092[_0x9d02a5(0x1c6)] === 0xc8)
                return _0x592092[_0x9d02a5(0x1db)]();
        }
        )['then'](_0x311d7c => {
            const _0x4ebf11 = _0xd8d602;
            instructions[_0x4ebf11(0x1f8)] = _0x311d7c?.['flag'];
        }
```
搜索```_0xd8d60```锁定到全局定义域下叫```_0x564a```,经过简单代码阅读发现这是一个函数，在console中解码出url，method，'innerHTML'。学习一些[js语法](/notes/web/前端基础/js语法/)后发现上述可以被翻译为
```js
fetch('/0n_th3_t0p_of_toweR,st4nds_th3_fl4g', {
    method: 'GET',
    headers: {
        'Secret-Code': encodeURIComponent('海月の虚空に秋涼し時鳥')
    }
})

.then(response => {
    if (response.status === 200)
        return response.json();
})
.then(data => {
    instructions.innerHTML = data?.flag;
});

```
在console中写入
```js
fetch('/0n_th3_t0p_of_toweR,st4nds_th3_fl4g', {
    method: 'GET',
    headers: {
        'Secret-Code': encodeURIComponent('海月の虚空に秋涼し時鳥')
    }
})
.then(response => response.json())
.then(data => console.log(data.flag))
```
拿到flag。

第一题做得我好辛苦我什么也不会。T T
