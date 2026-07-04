with open('index.html', 'r', encoding='utf-8') as f:
    s = f.read()

# 修1: 英文标题 annotate(it.title) 前先 unent()
old1 = 'annotate(it.title)'
new1 = 'annotate(unent(it.title))'
assert old1 in s, "未找到 annotate(it.title)"
s = s.replace(old1, new1)

# 修2: 中文标题 esc(it.zh) 前先 unent()
old2 = '${esc(it.zh)}'
new2 = '${esc(unent(it.zh))}'
assert old2 in s, "未找到 esc(it.zh)"
s = s.replace(old2, new2)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(s)
print("补丁成功")
