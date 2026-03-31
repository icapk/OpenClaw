#!/usr/bin/env python3
"""
小红书 & 公众号 浏览器自动化发布脚本
通过 Playwright 控制浏览器完成内容发布
版本：v1.1（修复 Playwright 1.50+ API兼容性）
"""
import sys
import os
import base64
import time
import json
import argparse

# Add scripts dir to path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

def get_image_base64(image_path):
    """读取图片并转为base64"""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

def inject_image_via_datatransfer(page, image_path):
    """
    通过 DataTransfer 将 base64 图片注入到 file input
    这是绕过 file input 限制的核心技巧
    """
    b64 = get_image_base64(image_path)
    # 移除 data URL 前缀，只保留 base64
    b64_data = b64.replace('data:image/png;base64,', '').replace('data:image/jpeg;base64,', '')

    # 使用 JavaScript 注入图片到 file input
    js_code = f"""
    const fileInput = document.querySelector('input[type="file"]');
    if (!fileInput) {{
        console.error('未找到 file input');
    }} else {{
        const bstr = atob('{b64_data}');
        let n = bstr.length;
        const u8arr = new Uint8Array(n);
        while (n--) {{
            u8arr[n] = bstr.charCodeAt(n);
        }}
        const blob = new Blob([u8arr], {{type: 'image/png'}});
        const file = new File([blob], 'cover.png', {{type: 'image/png'}});
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        fileInput.files = dataTransfer.files;
        fileInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
        console.log('图片注入成功');
    }}
    """
    page.evaluate(js_code)
    time.sleep(0.5)

def publish_xiaohongshu(title, content, image_path, tags=None):
    """
    发布小红书笔记
    需要用户已经登录小红书网页版
    """
    from playwright.sync_api import sync_playwright

    tags = tags or []
    with sync_playwright() as p:
        # 小红书使用 Firefox + 已保存的登录状态
        import os as _os
        auth_state = "/tmp/xhs_firefox_auth.json"
        if _os.path.exists(auth_state):
            # 使用 Firefox + 已保存登录态
            firefox_profile = _os.path.expanduser("~/.mozilla/firefox/publish_profile")
            _os.makedirs(firefox_profile, exist_ok=True)
            context = p.firefox.launch_persistent_context(firefox_profile, headless=False)
            page = context.pages[0] if context.pages else context.new_page()
        else:
            # Fallback: 尝试 Chrome
            import platform
            system = platform.system()
            if system == "Darwin":
                chrome_base = _os.path.expanduser("~/Library/Application Support/Google/Chrome")
            elif system == "Windows":
                chrome_base = _os.path.join(_os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "User Data")
            else:
                chrome_base = _os.path.expanduser("~/.config/google-chrome")
            user_data_path = _os.path.join(chrome_base, "Default")
            context = p.chromium.launch_persistent_context(user_data_path, headless=False)
            page = context.pages[0] if context.pages else context.new_page()

        try:
            # 打开发布页面
            page.goto("https://creator.xiaohongshu.com/publish/publish")
            time.sleep(3)

            # 检查是否需要登录
            if "login" in page.url.lower():
                print("需要登录！请先在浏览器中登录小红书")
                page.screenshot(path="/tmp/xhs_login.png")
                print("登录截图已保存到 /tmp/xhs_login.png")
                return {"status": "need_login", "screenshot": "/tmp/xhs_login.png"}

            # 注入封面图
            inject_image_via_datatransfer(page, image_path)
            time.sleep(1)

            # 填写标题
            title_input = page.query_selector('input[placeholder*="标题"]')
            if title_input:
                title_input.click()
                title_input.fill(title)

            # 填写正文
            content_area = page.query_selector('.editor-textarea, textarea[id*="content"], div[contenteditable="true"]')
            if content_area:
                content_area.click()
                content_area.fill(content)

            # 填写标签
            for tag in tags[:10]:
                tag_input = page.query_selector('input[placeholder*="标签"]')
                if tag_input:
                    tag_input.click()
                    tag_input.fill(tag)
                    time.sleep(0.3)
                    # 按回车确认
                    tag_input.press("Enter")

            # 点击发布按钮（尝试多种选择器）
            publish_btn = None
            for selector in [
                'button:has-text("发布")',
                'button:has-text("发布笔记")',
                '.publish-btn',
                '[class*="publish"] button',
            ]:
                publish_btn = page.query_selector(selector)
                if publish_btn:
                    break

            if publish_btn:
                publish_btn.click()
                time.sleep(2)
                print("发布成功！")
            else:
                print("未找到发布按钮，截图保存...")
                page.screenshot(path="/tmp/xhs_error.png")
                # 保存页面HTML用于调试
                with open("/tmp/xhs_page.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
                print("页面HTML已保存到 /tmp/xhs_page.html")

            return {"status": "published"}

        except Exception as e:
            print(f"发布失败: {e}")
            page.screenshot(path="/tmp/xhs_error.png")
            return {"status": "error", "message": str(e)}

def publish_wechat_gzh(title, content, image_path, account="default"):
    """
    发布公众号文章
    需要用户已经登录微信公众平台
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        # 公众号不维护持久化登录状态，每次重新登录
        browser = p.chromium.launch(headless=False)
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()

        try:
            # 打开发布页面
            page.goto("https://mp.weixin.qq.com/")
            time.sleep(3)

            # 检查是否需要登录
            if "login" in page.url.lower():
                print("需要登录！请先在浏览器中登录微信公众平台")
                page.screenshot(path="/tmp/wx_login.png")
                print("登录截图已保存到 /tmp/wx_login.png")
                return {"status": "need_login", "screenshot": "/tmp/wx_login.png"}

            # 点击新建图文消息
            page.goto("https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit_v2&action=edit&type=10&is_emoji=0&lang=zh_CN&token=")
            time.sleep(2)

            # 填写标题
            title_input = page.query_selector('#title, input[name="title"]')
            if title_input:
                title_input.click()
                title_input.fill(title)

            # 注入封面图
            inject_image_via_datatransfer(page, image_path)
            time.sleep(1)

            # 填写正文 (在富文本编辑器中)
            content_area = page.query_selector('#editor, .edit_area, div[contenteditable="true"]')
            if content_area:
                content_area.click()
                content_area.fill(content)

            # 点击保存
            save_btn = page.query_selector('button:has-text("保存")')
            if save_btn:
                save_btn.click()
                time.sleep(1)
                print("内容已保存")

            # 点击群发 (如果需要)
            send_btn = page.query_selector('button:has-text("群发")')
            if send_btn:
                print("内容已就绪，点击群发即可发布")
                send_btn.screenshot(path="/tmp/wx_ready.png")

            return {"status": "ready_to_publish"}

        except Exception as e:
            print(f"发布失败: {e}")
            page.screenshot(path="/tmp/wx_error.png")
            return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='社交平台发布工具')
    parser.add_argument('--platform', '-p', required=True, choices=['xhs', 'wechat', 'gzh'], help='发布平台: xhs=小红书, wechat/gzh=公众号')
    parser.add_argument('--title', '-t', required=True, help='文章标题')
    parser.add_argument('--content', '-c', required=True, help='文章内容')
    parser.add_argument('--image', '-i', required=True, help='封面图路径')
    parser.add_argument('--tags', '-g', nargs='*', default=[], help='标签 (小红书用)')
    parser.add_argument('--output-json', '-o', default='', help='输出结果JSON路径')

    args = parser.parse_args()

    result = {"platform": args.platform, "title": args.title}

    if args.platform == "xhs":
        result.update(publish_xiaohongshu(args.title, args.content, args.image, args.tags))
    elif args.platform in ["wechat", "gzh"]:
        result.update(publish_wechat_gzh(args.title, args.content, args.image))

    # 保存结果
    if args.output_json:
        with open(args.output_json, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
