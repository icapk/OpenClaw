#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""办公室场景看板集成测试"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:18980"
BOARD_URL = "http://127.0.0.1:18789"

def test_api_server():
    """测试API服务器"""
    print("🧪 测试API服务器...")
    
    # 测试OpenClaw API
    try:
        response = requests.post(
            f"{BASE_URL}/api/openclaw-exec",
            json={"cmd": "openclaw agents list --json"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('ok') and data.get('data'):
                agents = data['data']
                print(f"✅ OpenClaw API正常，返回 {len(agents)} 个agents")
                return True
            else:
                print(f"❌ OpenClaw API返回数据异常: {data}")
                return False
        else:
            print(f"❌ OpenClaw API请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ OpenClaw API请求异常: {e}")
        return False

def test_dashboard_data():
    """测试看板数据"""
    print("🧪 测试看板数据...")
    
    try:
        response = requests.get(f"{BASE_URL}/data/dashboard.json", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'summary' in data and 'agents' in data:
                summary = data['summary']
                agents = data['agents']
                print(f"✅ 看板数据正常，summary: {summary}, agents数量: {len(agents)}")
                return True
            else:
                print(f"❌ 看板数据格式异常: {data}")
                return False
        else:
            print(f"❌ 看板数据请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 看板数据请求异常: {e}")
        return False

def test_office_visual_page():
    """测试办公室可视化页面"""
    print("🧪 测试办公室可视化页面...")
    
    try:
        response = requests.get(f"{BASE_URL}/office-visual.html", timeout=10)
        if response.status_code == 200:
            content = response.text
            if '办公室场景看板' in content or 'OpenClaw' in content:
                print("✅ 办公室可视化页面正常")
                return True
            else:
                print("❌ 办公室可视化页面内容异常")
                return False
        else:
            print(f"❌ 办公室可视化页面请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 办公室可视化页面请求异常: {e}")
        return False

def test_board_routes():
    """测试看板路由"""
    print("🧪 测试看板路由...")
    
    routes = [
        "/board",
        "/board/",
        "/board/office-visual",
        "/board/office-visual/"
    ]
    
    success_count = 0
    for route in routes:
        try:
            response = requests.get(f"{BOARD_URL}{route}", timeout=5)
            if response.status_code == 200:
                success_count += 1
                print(f"✅ 路由 {route} 正常")
            else:
                print(f"❌ 路由 {route} 返回状态码: {response.status_code}")
        except Exception as e:
            print(f"❌ 路由 {route} 请求异常: {e}")
    
    if success_count == len(routes):
        print("✅ 所有看板路由正常")
        return True
    else:
        print(f"❌ {len(routes) - success_count} 个路由异常")
        return False

def main():
    """主测试函数"""
    print("🚀 开始办公室场景看板集成测试")
    print("=" * 50)
    
    tests = [
        ("API服务器", test_api_server),
        ("看板数据", test_dashboard_data),
        ("办公室可视化页面", test_office_visual_page),
        ("看板路由", test_board_routes)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ 测试 {test_name} 异常: {e}")
            results.append((test_name, False))
        
        # 短暂延迟，避免请求过快
        time.sleep(0.5)
    
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 总体结果: {passed}/{len(tests)} 项测试通过")
    
    if passed == len(tests):
        print("🎉 所有测试通过！办公室场景看板集成成功！")
        return True
    else:
        print("⚠️  部分测试失败，请检查相关组件")
        return False

if __name__ == "__main__":
    main()