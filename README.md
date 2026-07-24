# 情感日报 · 昨日情感热点

一个**无需云服务器**的静态网站：聚合微博 / 知乎 / 抖音等平台中「夫妻感情 / 婚姻 / 育儿 / 两性生活」相关热点，每天多次自动更新。

- 站点托管：**GitHub Pages**（免费，纯静态）
- 自动更新：**GitHub Actions**（定时抓取 → 生成 `data/news.json` → 自动提交发布）
- 技术栈：纯 HTML/CSS/JS + 一个 Python 抓取脚本（零第三方依赖）

> 数据由 GitHub 的服务器抓取，不受你本机网络限制影响。

---

## 文件结构

```
.
├── index.html              # 站点页面（也就是视觉稿，可直接上线）
├── fetch_news.py           # 抓取 + 生成数据脚本（标准库，无需 pip）
├── data/news.json          # 页面读取的数据（由 Actions 自动更新）
├── .github/workflows/
│   └── update.yml          # 每 4 小时自动运行的定时任务
└── .nojekyll               # 关闭 Jekyll，保证静态资源原样发布
```

---

## 一、部署到 GitHub（新建仓库，具体步骤）

### 第 1 步：在 GitHub 新建仓库
1. 打开 https://github.com/new （需登录 GitHub 账号）。
2. **Repository name** 填一个名字，例如 `emotion-daily`。
3. 可见性选 **Public**（GitHub Pages 免费版要求公开仓库）。
4. 不要勾选 "Add a README file"（我们已有自己的文件），也不要加 .gitignore。
5. 点击 **Create repository**。

### 第 2 步：把本地文件推上去
在你这台电脑上，打开终端 / Git Bash，进入本项目目录（即 `index.html` 所在的文件夹），依次执行：

```bash
git init
git add .
git commit -m "init: 情感日报站点"
git branch -M main
git remote add origin https://github.com/你的用户名/emotion-daily.git
git push -u origin main
```

> ⚠️ 若 `git push` 因网络无法直连 GitHub 而失败：
> - 方案 A：用 **GitHub Desktop**（官网下载）登录后「拖入仓库 → Publish》推送」，它对网络更友好；
> - 方案 B：在 GitHub 网页端新建空仓库后，直接用网页的 **Add file → Upload files** 把这几个文件传上去。
> 两种方式都不影响后续的自动更新。

### 第 3 步：开启 GitHub Pages
1. 进入仓库 → 顶部 **Settings**（设置）。
2. 左侧找到 **Pages**。
3. **Build and deployment** 的 Source 选 **Deploy from a branch**。
4. Branch 选 **main**，目录选 **/ (root)**，点 **Save**。
5. 约 1–2 分钟后，访问 `https://你的用户名.github.io/emotion-daily` 即可看到站点。

### 第 4 步：确认自动更新已生效
1. 仓库顶部切到 **Actions** 标签，能看到名为「更新情感热点数据」的工作流。
2. 首次推送后它会自动跑一次；之后每 4 小时跑一次。
3. 每次运行成功，都会把新的 `data/news.json` 提交回仓库，站点随之刷新。

---

## 二、自定义

| 想改什么 | 改哪里 |
| --- | --- |
| 更新频率 | `.github/workflows/update.yml` 里的 `cron: "17 */4 * * *"`（每 4 小时）。例如每 6 小时：`17 */6 * * *` |
| 站点标题 / 品牌 / 分类标签 | `index.html` 顶部的导航、Hero 文案、`<nav class="tabs">` 分类 |
| 配色 | `index.html` 里 `:root` 的 CSS 变量（`--accent` 砖红等） |
| 情感关键词 / 分类规则 | `fetch_news.py` 的 `EMOTION_KEYWORDS`、`CATEGORY_MAP` |
| 换 / 加数据源 | `fetch_news.py` 的 `SOURCES` 列表，照葫芦画瓢加一条 + 写 `parse_*` 解析函数 |

### 接入你自己的数据源（示例）
在 `fetch_news.py` 里新增一个解析函数并加入 `SOURCES` 即可，例如接某个返回 JSON 的热点接口：

```python
def parse_myapi(obj):
    out = []
    for it in obj.get("list", []):
        out.append((it["title"], _to_wan(it.get("hot", 0)), ""))
    return out

SOURCES.append({"name": "我的源", "url": "https://你的接口", "parse": parse_myapi})
```

---

## 三、常见问题

- **站点打开是空的 / 一直是示例数据？** 先看 `Actions` 是否运行成功；失败多半是某个接口临时不可用，脚本会自动跳过并尝试下一个，全部失败才用内置语料兜底（此时会显示示例内容，但站点不会崩）。
- **想立刻看一次更新效果？** 在 `Actions` 页面点「更新情感热点数据」→ **Run workflow** 手动触发一次。
- **本地预览？** 直接双击 `index.html` 即可（会显示内置示例数据）；想看真实数据，本地装好 Python 后运行 `python fetch_news.py` 再刷新。
