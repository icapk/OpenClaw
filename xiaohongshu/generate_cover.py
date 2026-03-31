#!/usr/bin/env python3
"""生成小红书封面图 - 爆款测试 ClaudeCode文章"""
from PIL import Image, ImageDraw, ImageFont
import base64
import os

# 尺寸：小红书3:4竖版推荐 1080x1440
WIDTH = 1080
HEIGHT = 1440

# 配色方案
BG_COLOR = (20, 20, 30)        # 深色背景
ACCENT_COLOR = (255, 100, 60)   # 珊瑚橙强调
TEXT_COLOR = (255, 255, 255)    # 白色文字
SUBTEXT_COLOR = (180, 180, 200) # 浅灰副标题

def load_font(size):
    """加载字体"""
    font_paths = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Arial.ttf",
        None
    ]
    for path in font_paths:
        if path and os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                continue
    return ImageFont.load_default()

def draw_rounded_rect(draw, xy, radius, fill):
    """绘制圆角矩形"""
    x1, y1, x2, y2 = xy
    draw.rectangle([x1+radius, y1, x2-radius, y2], fill=fill)
    draw.rectangle([x1, y1+radius, x2, y2-radius], fill=fill)
    draw.pieslice([x1, y1, x1+2*radius, y1+2*radius], 180, 270, fill=fill)
    draw.pieslice([x2-2*radius, y1, x2, y1+2*radius], 270, 360, fill=fill)
    draw.pieslice([x1, y2-2*radius, x1+2*radius, y2], 90, 180, fill=fill)
    draw.pieslice([x2-2*radius, y2-2*radius, x2, y2], 0, 90, fill=fill)

def create_cover():
    img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    font_title1 = load_font(80)
    font_title2 = load_font(90)
    font_sub = load_font(40)
    font_tag = load_font(35)

    # 顶部装饰线
    draw.rectangle([0, 0, WIDTH, 8], fill=ACCENT_COLOR)

    # 主标题第一行
    title1 = "用了30天Claude Code后"
    bbox1 = draw.textbbox((0, 0), title1, font=font_title1)
    text1_width = bbox1[2] - bbox1[0]
    x1 = (WIDTH - text1_width) // 2
    draw.text((x1, 300), title1, fill=SUBTEXT_COLOR, font=font_title1)

    # 主标题第二行（强调）
    title2 = "我决定把Cursor卸载了"
    bbox2 = draw.textbbox((0, 0), title2, font=font_title2)
    text2_width = bbox2[2] - bbox2[0]
    x2 = (WIDTH - text2_width) // 2
    # 文字背景高亮
    highlight_padding = 20
    draw_rounded_rect(draw, 
                      (x2 - highlight_padding, 500 - highlight_padding, 
                       x2 + text2_width + highlight_padding, 500 + 100 + highlight_padding),
                      15, ACCENT_COLOR)
    draw.text((x2, 500), title2, fill=TEXT_COLOR, font=font_title2)

    # 中间分割装饰
    draw.rectangle([WIDTH//2 - 80, 750, WIDTH//2 + 80, 755], fill=ACCENT_COLOR)

    # 标签文字
    tags = ["#ClaudeCode", "#AI工具", "#产品经理"]
    y_pos = 850
    for tag in tags:
        bbox = draw.textbbox((0, 0), tag, font=font_tag)
        tag_width = bbox[2] - bbox[0]
        x = (WIDTH - tag_width) // 2
        draw.text((x, y_pos), tag, fill=SUBTEXT_COLOR, font=font_tag)
        y_pos += 70

    # 底部信息
    bottom_text = "AI小麦 · 真实体验分享"
    bbox_b = draw.textbbox((0, 0), bottom_text, font=font_sub)
    bottom_width = bbox_b[2] - bbox_b[0]
    draw.text(((WIDTH - bottom_width)//2, 1300), bottom_text, fill=(100, 100, 120), font=font_sub)

    # 底部装饰线
    draw.rectangle([0, HEIGHT-8, WIDTH, HEIGHT], fill=ACCENT_COLOR)

    # 保存
    output_path = "/Users/a1/.openclaw/workspace/xiaohongshu/ready/爆款测试_ClaudeCode_封面_2026-03-29.png"
    img.save(output_path, 'PNG', quality=95)
    print(f"封面图已保存: {output_path}")

    # 输出base64
    with open(output_path, 'rb') as f:
        img_base64 = base64.b64encode(f.read()).decode('utf-8')
    print(f"Base64长度: {len(img_base64)}")
    return output_path, img_base64

if __name__ == "__main__":
    create_cover()
