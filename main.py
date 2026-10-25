#!/usr/bin/env python3
"""
ikuuu 机场每日签到 - Cookie 版
使用浏览器 Cookie 登录，绕过 Geetest V4 验证码
Cookie 从环境变量 IKUUU_COOKIE 读取，格式：key1=val1; key2=val2
"""
import requests
import json
import os
import re
import sys
import time

# === 强制 UTF-8 输出 ===
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# === 读取 Cookie ===
COOKIE_STR = os.environ.get('IKUUU_COOKIE', '')
if not COOKIE_STR:
    print('[FATAL] 未设置 IKUUU_COOKIE 环境变量')
    sys.exit(1)

def parse_cookie_string(cookie_str):
    """解析 Cookie 字符串为字典"""
    cookies = {}
    for item in cookie_str.split('; '):
        if '=' in item:
            k, v = item.split('=', 1)
            cookies[k.strip()] = v.strip()
    return cookies

def parse_cookie_string_to_header(cookie_str):
    """解析 Cookie 字符串为 Cookie header 格式"""
    return cookie_str.replace('; ', '; ')

# === 通知配置 ===
SCKEY = os.environ.get('SCKEY', '')
PUSHPLUS_TOKEN = os.environ.get('PUSHPLUS_TOKEN', '')

def push(content):
    """推送通知"""
    if SCKEY and SCKEY != '1':
        try:
            url = f"https://sctapi.ftqq.com/{SCKEY}.send?title=ikuuu签到&desp={content}"
            requests.post(url, timeout=10)
            print('Server酱推送完成')
        except Exception as e:
            print(f'推送失败: {e}')
    elif PUSHPLUS_TOKEN and PUSHPLUS_TOKEN != '1':
        try:
            headers = {'Content-Type': 'application/json'}
            data = {"token": PUSHPLUS_TOKEN, 'title': 'ikuuu签到', 'content': content, "template": "json"}
            resp = requests.post('http://www.pushplus.plus/send', json=data, headers=headers, timeout=10)
            print(f'PushPlus 推送: {resp.json().get("code", "?")}')
        except Exception as e:
            print(f'推送失败: {e}')
    else:
        print('未配置消息推送')

# === 主逻辑 ===
def main():
    print('=== ikuuu 机场每日签到 (Cookie 版) ===')
    print(f'Cookie 来源: {"环境变量" if COOKIE_STR else "无"}')
    
    # 解析 Cookie
    cookies = parse_cookie_string(COOKIE_STR)
    print(f'Cookie 字段: {list(cookies.keys())}')
    
    if 'uid' not in cookies or 'key' not in cookies:
        print('[WARN] Cookie 缺少关键字段 (uid/key)，可能已过期')
    
    # 创建 session
    session = requests.session()
    
    # 设置 Cookie
    for k, v in cookies.items():
        session.cookies.set(k, v, domain='.ikuuu.top')
    
    headers = {
        'origin': 'https://ikuuu.top',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'referer': 'https://ikuuu.top/user',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'x-requested-with': 'XMLHttpRequest',
    }
    
    # === 验证登录状态 ===
    print('\n[1/2] 验证登录状态...')
    try:
        resp = session.get('https://ikuuu.top/user/profile', headers=headers, timeout=15, allow_redirects=False)
        if resp.status_code == 302 or 'login' in resp.text.lower()[:500]:
            print('[ERROR] Cookie 已过期或无效，需要重新登录获取 Cookie')
            push('❌ ikuuu 签到失败：Cookie 已过期，请在 Edge 中重新登录 ikuuu.top 并更新 IKUUU_COOKIE Secret')
            return False
        
        if resp.status_code == 200:
            # 尝试提取用户信息
            email = cookies.get('email', 'unknown')
            uid = cookies.get('uid', 'unknown')
            print(f'✅ 登录成功 (uid={uid}, email={email})')
        else:
            print(f'[WARN] 状态码: {resp.status_code}')
    except Exception as e:
        print(f'[ERROR] 验证登录失败: {e}')
        push(f'❌ ikuuu 签到失败: {e}')
        return False
    
    # === 执行签到 ===
    print('\n[2/2] 执行签到...')
    try:
        resp = session.post('https://ikuuu.top/user/checkin', headers=headers, timeout=15)
        
        if resp.status_code != 200:
            print(f'[ERROR] 签到请求失败: HTTP {resp.status_code}')
            push(f'❌ ikuuu 签到请求失败: HTTP {resp.status_code}')
            return False
        
        # 解析响应
        try:
            result = resp.json()
            msg = result.get('msg', str(result))
            ret = result.get('ret', None)
            
            if ret == 1:
                print(f'✅ 签到成功！{msg}')
                content = f'✅ ikuuu 签到成功\n{msg}\nuid: {cookies.get("uid", "?")}'
            elif ret == 0:
                # ret=0 可能是已签到或其他状态
                print(f'⚠️ 签到返回: {msg} (ret={ret})')
                content = f'⚠️ ikuuu 签到: {msg}'
            else:
                print(f'⚠️ 签到返回: {msg}')
                content = f'ikuuu 签到: {msg}'
            
            push(content)
            return True
            
        except json.JSONDecodeError:
            text = resp.text[:200]
            print(f'[WARN] 响应不是 JSON: {text}')
            push(f'ikuuu 签到响应异常: {text}')
            return False
            
    except Exception as e:
        print(f'[ERROR] 签到失败: {e}')
        push(f'❌ ikuuu 签到失败: {e}')
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
