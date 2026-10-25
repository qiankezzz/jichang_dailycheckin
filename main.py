import requests, json, re, os, time

session = requests.session()

emails = os.environ.get('EMAIL', '').split(',')
passwords = os.environ.get('PASSWD', '').split(',')

SCKEY = os.environ.get('SCKEY')
Token = os.environ.get('TOKEN')

def push(content):
    if SCKEY != '1':
        url = "https://sctapi.ftqq.com/{}.send?title={}&desp={}".format(SCKEY, 'ikuuu签到', content)
        requests.post(url)
        print('推送完成')
    elif Token != '1':
        headers = {'Content-Type': 'application/json'}
        json = {"token": Token, 'title': 'ikuuu签到', 'content': content, "template": "json"}
        resp = requests.post(f'https://www.pushplus.plus/send', json=json, headers=headers).json()
        print('push+推送成功' if resp['code'] == 200 else 'push+推送失败')
    else:
        print('未使用消息推送推送！')

login_url = 'https://ikuuu.top/auth/login'
check_url = 'https://ikuuu.top/user/checkin'
info_url = 'https://ikuuu.top/user/profile'

headers = {
    'origin': 'https://ikuuu.top',
    'referer': 'https://ikuuu.top/auth/login',
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

for email, passwd in zip(emails, passwords):
    session = requests.session()
    session.headers.update(headers)
    data = {'email': email, 'passwd': passwd}
    try:
        print(f'[{email}] 获取登录页...')
        # 先访问登录页获取 cookies / 反爬 token
        pre = session.get('https://ikuuu.top/auth/login', timeout=15)
        print(f'登录页状态: {pre.status_code}, 长度: {len(pre.text)}')
        time.sleep(1)
        print(f'[{email}] 进行登录...')
        response = session.post(url=login_url, json=data, timeout=15)
        print(f'登录响应状态: {response.status_code}')
        login_resp = json.loads(response.text)
        print(login_resp.get('msg', str(login_resp)))
        if login_resp.get('ret') != 0 and login_resp.get('status') != 'success' and '成功' not in login_resp.get('msg', ''):
            content = f'登录失败: {login_resp.get("msg", str(login_resp))}'
            print(content)
            push(content)
            continue
        time.sleep(1)
        result = session.post(url=check_url, timeout=15)
        print(f'签到响应状态: {result.status_code}')
        result_json = json.loads(result.text)
        print(result_json.get('msg', str(result_json)))
        content = result_json.get('msg', '签到完成')
        push(content)
    except Exception as e:
        content = f'签到失败: {repr(e)}'
        print(content)
        push(content)
