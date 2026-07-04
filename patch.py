with open('fetch.py', 'r', encoding='utf-8') as f:
    s = f.read()

# 顶部加 import html
old1 = 'import json'
new1 = 'import json, html as _html'
assert old1 in s, "未找到 import json"
s = s.replace(old1, new1, 1)

# title 赋值时解码实体
old2 = 'title = " ".join(tag("ArticleTitle").split())'
new2 = 'title = _html.unescape(" ".join(tag("ArticleTitle").split()))'
assert old2 in s, "未找到 title 赋值"
s = s.replace(old2, new2)

with open('fetch.py', 'w', encoding='utf-8') as f:
    f.write(s)
print("补丁成功")
