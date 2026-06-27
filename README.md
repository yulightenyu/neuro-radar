# Neuro Radar · 阿尔茨海默病硬核知识库

静态知识库（病理/诊断/药物/管线/预防，标注证据等级）+ 动态前沿（PubMed 实时文献 + DeepSeek 中文精华）。

## 部署
1. GitHub Pages：Settings → Pages → main 分支根目录
2. DeepSeek key：Settings → Secrets and variables → Actions → New repository secret，名为 DEEPSEEK_API_KEY
3. Actions → update → Run workflow

## 调参
- config.json 的 feeds[].term：四路 PubMed 检索式
- retmax：每路抓几条
- 无 key 也能跑，只是没有中文精华

## 纯净度
fetch.py 仅用标准库 + urllib，无第三方依赖。
