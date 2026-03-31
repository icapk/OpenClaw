---
name: social-publishing
description: 小红书和公众号自动化发布技能。核心功能：(1) 生成封面图（3:4竖版1080x1440）；(2) 浏览器自动化发布小红书笔记；(3) 浏览器自动化发布公众号文章。触发场景："帮我发布小红书"、"发布公众号文章"、"生成封面图"、"把内容发布到社交平台"。包含Python脚本支持图片生成、DataTransfer图片注入、Playwright浏览器自动化。
---

# 社交平台发布 Skill

> 版本：v1.0 | 创建日期：2026-03-30
> 功能：封面图生成 + 小红书发布 + 公众号发布
> 依赖：Python3, playwright, PIL

---

## 核心流程

```
内容准备 → 封面图生成 → 浏览器自动化发布
```

---

## 一、封面图生成

### 使用方式

```bash
python3 scripts/generate_cover.py \
    --title1 "第一行标题" \
    --title2 "第二行标题（主标题）" \
    --subtitle "副标题" \
    --bg dark \
    --accent coral \
    --tags "#标签1" "#标签2" "#标签3" \
    --output /path/to/output.png
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| --title1 | 第一行标题（可选） | 空 |
| --title2 | 第二行标题（必填，主标题） | - |
| --subtitle | 副标题 | 空 |
| --bg | 背景色：dark/blue/purple/orange | dark |
| --accent | 强调色：coral/gold/cyan/green | coral |
| --tags | 标签列表（最多3个） | [] |
| --output | 输出路径 | xiaohongshu/ready/cover.png |

### 示例

```bash
# 生成小红书封面图
python3 scripts/generate_cover.py \
    --title2 "AI Agent时代，PM最核心的能力只有一个字 🔥" \
    --bg blue \
    --accent gold \
    --output ~/xiaohongshu/ready/封面1.png
```

---

## 二、小红书发布

### 发布脚本

```bash
python3 scripts/publish.py \
    --platform xhs \
    --title "文章标题" \
    --content "文章正文内容" \
    --image /path/to/cover.png \
    --tags "#标签1" "#标签2" \
    --output-json result.json
```

### 发布流程

1. 启动 Chromium 浏览器（非无头模式）
2. 打开小红书创作者中心
3. 通过 DataTransfer 注入封面图到 file input
4. 自动填写标题、正文、标签
5. 点击发布按钮

### 登录状态维护

**重要**：首次使用需要登录小红书，之后浏览器会保存登录状态（user_data_dir）。

如果提示需要登录：
1. 手动在浏览器中登录一次
2. 登录状态会被保存

### 标签要求

- 小红书最多添加10个标签
- 建议5-8个精准tag
- 自动添加到内容末尾

---

## 三、公众号发布

### 发布脚本

```bash
python3 scripts/publish.py \
    --platform gzh \
    --title "文章标题" \
    --content "文章正文内容" \
    --image /path/to/cover.png \
    --output-json result.json
```

### 发布流程

1. 启动 Chromium 浏览器
2. 打开微信公众平台
3. 通过 DataTransfer 注入封面图
4. 自动填写标题和正文
5. 保存后需人工确认群发

### 注意事项

- 公众号发布后需要人工点击"群发"才能正式发布
- 保存为草稿后可随时编辑

---

## 四、DataTransfer 注入原理

这是发布功能的核心技术，绕过了 file input 无法直接接受路径的限制：

```python
# 1. 读取图片为 base64
with open(image_path, 'rb') as f:
    img_base64 = base64.b64encode(f.read()).decode('utf-8')

# 2. 转换为 Uint8Array
js_code = f"""
const bstr = atob('{img_base64}');
const n = bstr.length;
const u8arr = new Uint8Array(n);
while (n--) {{ u8arr[n] = bstr.charCodeAt(n); }}

# 3. 创建 Blob 和 File
const blob = new Blob([u8arr], {{type: 'image/png'}});
const file = new File([blob], 'cover.png', {{type: 'image/png'}});

# 4. 通过 DataTransfer 注入到 file input
const dataTransfer = new DataTransfer();
dataTransfer.items.add(file);
fileInput.files = dataTransfer.files;
fileInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
"""
```

---

## 五、环境要求

### 依赖安装

```bash
pip3 install playwright
playwright install chromium
```

### Python 库

- `playwright` - 浏览器自动化
- `PIL` (Pillow) - 图片生成
- `base64` - 图片编码（内置）

---

## 六、输出文件

发布结果会保存到 `output_json` 指定路径，包含：

```json
{
  "platform": "xhs",
  "title": "文章标题",
  "status": "published",
  "message": "发布成功"
}
```

状态值：
- `published` - 发布成功
- `need_login` - 需要登录
- `error` - 发布失败

---

## 七、使用示例

### 完整发布流程

```python
# 1. 生成封面图
from generate_cover import create_cover
cover_path, _ = create_cover(
    title1="用了30天Claude Code后",
    title2="我决定把Cursor卸载了",
    subtitle="#ClaudeCode #AI工具 #产品经理",
    bg_color="dark",
    accent_color="coral",
    output_path="/tmp/cover.png"
)

# 2. 发布小红书
import subprocess
result = subprocess.run([
    "python3", "scripts/publish.py",
    "--platform", "xhs",
    "--title", "用了30天Claude Code后，我决定把Cursor卸载了",
    "--content", "姐妹们！...",
    "--image", cover_path,
    "--tags", "#ClaudeCode", "#AI工具",
    "--output-json", "/tmp/publish_result.json"
], capture_output=True, text=True)

print(result.stdout)
```

---

## 八、故障排除

### 浏览器无法启动

```bash
# 重新安装 chromium
playwright install chromium
```

### 图片注入失败

- 检查 file input 是否存在
- 可能是小红书页面结构更新，需要重新定位元素
- 可以手动上传图片作为备选方案

### 登录状态失效

- 清除 user_data_dir 目录
- 重新手动登录一次

---

*Skill 创建时间：2026-03-30*
*维护人：运营部*
