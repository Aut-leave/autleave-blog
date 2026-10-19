---
title: "Rushing into Courses"
date: 2026-10-17T17:50:37+08:00
weight: 2
draft: false
---

我几把不知道啊总之这样就是可以过了
等我过一段时间再来看吧我好崩溃啊。

```js
(async () => {
    const courses = [
        ...document.querySelectorAll('li[onclick^="doCourseSelect"]')
    ].filter(el => /状态[：:]\s*未选/.test(el.innerText));

    console.log(`找到 ${courses.length} 门未选课程，开始提交……`);

    const results = await Promise.all(
        courses.map(async el => {
            const name = el.innerText.trim();
            const match = (el.getAttribute('onclick') || '')
                .match(/doCourseSelect\('([^']+)'\)/);

            if (!match) {
                return {
                    课程: name,
                    结果: '无法提取课程 ID'
                };
            }

            try {
                const res = await fetch('/api/course/select', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        uuid: match[1]
                    })
                });

                const ret = await res.json();

                const success =
                    res.ok &&
                    (ret.code === 0 || ret.code === 200);

                return {
                    课程: name,
                    结果: success ? '服务器返回成功' : '选课失败',
                    消息: ret.message || '',
                    业务码: ret.code,
                    HTTP状态: res.status,
                    原始响应: JSON.stringify(ret)
                };
            } catch (err) {
                return {
                    课程: name,
                    结果: '请求异常',
                    消息: String(err)
                };
            }
        })
    );

    console.table(results);
    console.log('所有请求已结束，请刷新页面确认实际选课状态。');
})();
```
