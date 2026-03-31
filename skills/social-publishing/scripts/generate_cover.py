#!/usr/bin/env python3
"""
小红书/公众号封面图生成器
生成 3:4 竖版封面图 (1080x1440)
"""
from PIL import Image, ImageDraw, ImageFont
import base64
import os
import sys
import json

WIDTH = 1080
HEIGHT = 1440

BG_COLORS = {
    "dark": (20, 20, 30),
    "blue": (30, 40, 80),
    "purple": (50, 30, 70),
    "orange": (80, 40, 20),
}

ACCENT_COLORS = {
    "coral": (255, 100, 60),
    "gold": (255, 200, 100),
    "cyan": (100, 200, 255),
    "green": (100, 255, 150),
}

def load_font(size):
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
    x1, y1, x2, y2 = xy
    draw.rectangle([x1+radius, y1, x2-radius, y2], fill=fill)
    draw.rectangle([x1, y1+radius, x2, y2-radius], fill=fill)
    draw.pieslice([x1, y1, x1+2*radius, y1+2*radius], 180, 270, fill=fill)
    draw.pieslice([x2-2*radius, y1, x2, y1+2*radius], 270, 360, fill=fill)
    draw.pieslice([x1, y2-2*radius, x1+2*radius, y2], 90, 180, fill=fill)
    draw.pieslice([x2-2*radius, y2-2*radius, x2, y2], 0, 90, fill=fill)

def create_cover(title1, title2, subtitle="", bg_color="dark", accent_color="coral", tags=None, output_path=None):
    """生成小红书封面图"""
    img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLORS.get(bg_color, BG_COLORS["dark"]))
    draw = ImageDraw.Draw(img)

    font_title1 = load_font(70)
    font_title2 = load_font(85)
    font_sub = load_font(40)
    font_tag = load_font(35)

    accent = ACCENT_COLORS.get(accent_color, ACCENT_COLORS["coral"])

    # 顶部装饰线
    draw.rectangle([0, 0, WIDTH, 8], fill=accent)

    # 主标题第一行
    if title1:
        bbox1 = draw.textbbox((0, 0), title1, font=font_title1)
        text1_width = bbox1[2] - bbox1[0]
        x1 = (WIDTH - text1_width) // 2
        draw.text((x1, 280), title1, fill=(180, 180, 200), font=font_title1)

    # 主标题第二行（强调）
    if title2:
        bbox2 = draw.textbbox((0, 0), title2, font=font_title2)
        text2_width = bbox2[2] - bbox2[0]
        x2 = (WIDTH - text2_width) // 2
        highlight_padding = 20
        draw_rounded_rect(draw,
                          (x2 - highlight_padding, 480 - highlight_padding,
                           x2 + text2_width + highlight_padding, 480 + 100 + highlight_padding),
                          15, accent)
        draw.text((x2, 480), title2, fill=(255, 255, 255), font=font_title2)

    # 副标题
    if subtitle:
        bbox_sub = draw.textbbox((0, 0), subtitle, font=font_sub)
        sub_width = bbox_sub[2] - bbox_sub[0]
        x_sub = (WIDTH - sub_width) // 2
        draw.text((x_sub, 750), subtitle, fill=(150, 150, 170), font=font_sub)

    # 标签
    if tags:
        y_pos = 900
        for tag in tags[:3]:
            bbox = draw.textbbox((0, 0), tag, font=font_tag)
            tag_width = bbox[2] - bbox[0]
            x = (WIDTH - tag_width) // 2
            draw.text((x, y_pos), tag, fill=(130, 130, 150), font=font_tag)
            y_pos += 60

    # 底部装饰线
    draw.rectangle([0, HEIGHT-8, WIDTH, HEIGHT], fill=accent)

    if not output_path:
        output_path = "/Users/a1/.openclaw/workspace/xiaohongshu/ready/cover.png"

    img.save(output_path, 'PNG', quality=95)
    print(f"封面图已保存: {output_path}")

    # 输出base64
    with open(output_path, 'rb') as f:
        img_base64 = base64.b64encode(f.read()).decode('utf-8')
    return output_path, img_base64

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='生成小红书封面图')
    parser.add_argument('--title1', '-t1', default='', help='第一行标题')
    parser.add_argument('--title2', '-t2', required=True, help='第二行标题（主标题）')
    parser.add_argument('--subtitle', '-s', default='', help='副标题')
    parser.add_argument('--bg', default='dark', choices=['dark', 'blue', 'purple', 'orange'], help='背景色')
    parser.add_argument('--accent', default='coral', choices=['coral', 'gold', 'cyan', 'green'], help='强调色')
    parser.add_argument('--tags', '-g', nargs='*', default=[], help='标签')
    parser.add_argument('--output', '-o', default='', help='输出路径')
    args = parser.parse_args()

    output_path = args.output if args.output else None
    path, b64 = create_cover(
        args.title1, args.title2, args.subtitle,
        args.bg, args.accent, args.tags, output_path
    )
    print(f"Base64长度: {len(b64)}")