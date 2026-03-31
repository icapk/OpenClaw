#!/usr/bin/env python3
"""
GCD - 最大公约数计算器
使用欧几里得算法计算两个数的最大公约数

测试用例：
  gcd(48, 18) = 6
  gcd(17, 13) = 1
  gcd(100, 25) = 25
  gcd(7, 14) = 7
"""

def gcd(a: int, b: int) -> int:
    """欧几里得算法：计算 a 和 b 的最大公约数"""
    while b:
        a, b = b, a % b
    return a

def test_gcd():
    """运行测试用例"""
    test_cases = [
        (48, 18, 6),
        (17, 13, 1),
        (100, 25, 25),
        (7, 14, 7),
        (0, 5, 5),   # 0 和任何数的 GCD 是那个数本身
        (1, 1, 1),
        (54, 24, 6),
        (17, 0, 17), # 任何数和 0 的 GCD 是那个数本身
    ]
    
    all_passed = True
    for a, b, expected in test_cases:
        result = gcd(a, b)
        status = "✅" if result == expected else "❌"
        if result != expected:
            all_passed = False
        print(f"{status} gcd({a}, {b}) = {result} (expected: {expected})")
    
    print()
    if all_passed:
        print("所有测试用例通过！🎉")
    else:
        print("部分测试用例失败 ❌")
    
    return all_passed

if __name__ == "__main__":
    test_gcd()
