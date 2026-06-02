import requests
import time
import base64
import json
from utils import q_key, load_bank, save_bank, load_wrong, save_wrong
from dotenv import load_dotenv
import os

load_dotenv()

BASE_URL = os.getenv('BASE_URL', 'https://aqy-app.lgb360.com')
TOKEN = os.getenv('TOKEN', '')
MEMBER_ID = os.getenv('MEMBER_ID', '')
UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.59(0x18003b2c) NetType/WIFI Language/zh_CN'

GITEE_CONFIG = {
    'enabled': os.getenv('GITEE_ENABLED', 'true').lower() == 'true',
    'owner': os.getenv('GITEE_OWNER', 'sanchuan503'),
    'repo': os.getenv('GITEE_REPO', 'safe-quiz-bank'),
    'token': os.getenv('GITEE_TOKEN', ''),
    'branch': os.getenv('GITEE_BRANCH', 'master'),
    'question_path': os.getenv('GITEE_QUESTION_PATH', 'questions.json'),
    'wrong_path': os.getenv('GITEE_WRONG_PATH', 'wrong.json')
}

AI_CONFIG = {
    'api_key': os.getenv('AI_API_KEY', ''),
    'api_url': os.getenv('AI_API_URL', 'https://api.deepseek.com/v1/chat/completions'),
    'model': os.getenv('AI_MODEL', 'deepseek-v4-flash')
}

import gzip
def api_request(path, method='GET', body=None, retries=2):
    url = BASE_URL + path
    
    global TOKEN, MEMBER_ID
    
    headers = {
        'Content-Language': 'zh_CN',
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Referer': 'https://aqy-app.lgb360.com/',
        'User-Agent': UA,
        'memberId': MEMBER_ID,
        'token': TOKEN
    }
    
    if method in ['POST', 'PUT']:
        headers['Content-Type'] = 'application/json;charset=utf-8'
    
    for i in range(retries):
        try:
            if method == 'GET':
                if body:
                    url += '?' + '&'.join(f'{k}={v}' for k, v in body.items())
                response = requests.get(url, headers=headers, timeout=30)
            else:
                response = requests.request(method, url, headers=headers, json=body, timeout=30)
            
            print(f"API Response [{path}]: status={response.status_code}")
            print(f"  Content-Encoding: {response.headers.get('Content-Encoding', 'none')}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"  JSON response: {str(data)[:200]}...")
                    return data
                except Exception as e:
                    print(f"  JSON parse error: {e}")
                    try:
                        encoding = response.headers.get('Content-Encoding', '').lower()
                        if encoding == 'gzip':
                            decompressed = gzip.decompress(response.content)
                            text = decompressed.decode('utf-8')
                            print(f"  gzip decompressed: {text[:500]}...")
                        else:
                            text = response.text[:500]
                            print(f"  Text response: {text}...")
                            return text
                            
                        try:
                            return json.loads(text)
                        except:
                            return text
                    except Exception as e2:
                        print(f"  Decompress error: {e2}")
                        return response.text[:500]
            else:
                print(f"  Error: status={response.status_code}")
                if i == retries - 1:
                    return None
        except Exception as e:
            print(f"  Exception: {e}")
            if i == retries - 1:
                return None
            time.sleep(1)
    return None


async def async_api_request(path, method='GET', body=None, retries=2):
    return api_request(path, method, body, retries)


async def cloud_sync():
    if not GITEE_CONFIG['enabled']:
        return {'success': False, 'reason': '云同步已禁用'}
    
    owner = GITEE_CONFIG['owner']
    repo = GITEE_CONFIG['repo']
    token = GITEE_CONFIG['token']
    branch = GITEE_CONFIG['branch']
    question_path = GITEE_CONFIG['question_path']
    wrong_path = GITEE_CONFIG['wrong_path']
    
    base_url = 'https://gitee.com/api/v5/repos'
    headers = {'Accept': 'application/json'}
    if token:
        headers['Authorization'] = f'token {token}'
    
    def gitee_api(path, method='GET', body=None):
        url = f'{base_url}{path}'
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=20)
            else:
                response = requests.request(method, url, headers=headers, json=body, timeout=20)
            return response.json()
        except Exception as e:
            return {'error': str(e)}
    
    def get_file(file_path):
        resp = gitee_api(f'/{owner}/{repo}/contents/{file_path}?ref={branch}')
        if 'content' in resp:
            decoded = base64.b64decode(resp['content']).decode('utf-8')
            return json.loads(decoded)
        return None
    
    def get_sha(file_path):
        resp = gitee_api(f'/{owner}/{repo}/contents/{file_path}?ref={branch}')
        return resp.get('sha')
    
    def set_file(file_path, content, sha=None):
        encoded = base64.b64encode(json.dumps(content, ensure_ascii=False).encode('utf-8')).decode('utf-8')
        data = {
            'access_token': token,
            'owner': owner,
            'repo': repo,
            'branch': branch,
            'path': file_path,
            'content': encoded,
            'message': f'Sync: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}'
        }
        if sha:
            data['sha'] = sha
        return gitee_api(f'/{owner}/{repo}/contents/{file_path}', method='POST', body=data)
    
    def merge_bank(local, remote):
        merged = dict(local)
        added = 0
        for k, v in remote.items():
            if k not in merged:
                merged[k] = v
                added += 1
        return merged, added
    
    def merge_wrong(local, remote):
        local_keys = set()
        for w in local:
            key = q_key(w.get('q', '')) + '_' + (w.get('date', '').split('T')[0] if w.get('date') else '')
            local_keys.add(key)
        
        new_wrong = []
        for w in remote:
            key = q_key(w.get('q', '')) + '_' + (w.get('date', '').split('T')[0] if w.get('date') else '')
            if key not in local_keys:
                new_wrong.append(w)
        
        return local + new_wrong
    
    try:
        remote_bank = get_file(question_path)
        remote_wrong = get_file(wrong_path)
        
        local_bank = load_bank()
        local_wrong = load_wrong()
        
        bank_added = 0
        wrong_added = 0
        
        if remote_bank and isinstance(remote_bank, dict):
            remote_questions = remote_bank
            if isinstance(remote_bank.get('questions'), list):
                remote_questions = {}
                for q in remote_bank['questions']:
                    if q.get('q'):
                        key = q_key(q['q'])
                        remote_questions[key] = {
                            'q': q['q'],
                            'opts': q.get('opts', q.get('options', [])),
                            'answer': q.get('answer', q.get('ans', [])),
                            'type': q.get('type', '单选'),
                            'scene': q.get('scene', '云端'),
                            'level': q.get('level', ''),
                            'updated': q.get('updated', '')
                        }
            
            if remote_questions and not 'q_xxx' in remote_questions:
                temp = {}
                for k, q in remote_questions.items():
                    if q and q.get('q'):
                        temp[q_key(q['q'])] = q
                remote_questions = temp
            
            merged_bank, added = merge_bank(local_bank, remote_questions)
            bank_added = added
            
            if bank_added > 0 or len(merged_bank) > len(local_bank):
                save_bank(merged_bank)
        
        if remote_wrong and isinstance(remote_wrong, list):
            merged_wrong = merge_wrong(local_wrong, remote_wrong)
            wrong_added = len(merged_wrong) - len(local_wrong)
            
            if wrong_added > 0:
                save_wrong(merged_wrong)
        
        local_bank_updated = load_bank()
        local_wrong_updated = load_wrong()
        
        bank_sha = get_sha(question_path)
        wrong_sha = get_sha(wrong_path)
        
        set_file(question_path, local_bank_updated, bank_sha)
        set_file(wrong_path, local_wrong_updated, wrong_sha)
        
        return {'success': True, 'bank_added': bank_added, 'wrong_added': wrong_added}
    
    except Exception as e:
        return {'success': False, 'reason': str(e)}


async def ask_ai(question, options, ques_type):
    if not AI_CONFIG['api_key']:
        return None
    
    type_hint = '多选题' if ques_type == 'multiple' else '单选题'
    opt_text = '\n'.join(f'{chr(65 + i)}. {o}' for i, o in enumerate(options))
    prompt = f'安全知识竞赛。请选择正确答案。\n\n类型: {type_hint}\n题目: {question}\n{opt_text}\n\n直接返回正确选项的完整文本，多个用|分隔。不要字母，不要解释。'
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {AI_CONFIG["api_key"]}'
    }
    
    body = {
        'model': AI_CONFIG['model'],
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0.1,
        'max_tokens': 200
    }
    
    try:
        response = requests.post(AI_CONFIG['api_url'], headers=headers, json=body, timeout=20)
        if response.status_code == 200:
            data = response.json()
            text = data.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
            if not text:
                return None
            
            matched = []
            parts = [p.strip() for p in text.split('|')]
            for p in parts:
                for opt in options:
                    if (opt in p or p in opt) and opt not in matched:
                        matched.append(opt)
            
            if not matched:
                for opt in options:
                    if opt in text and opt not in matched:
                        matched.append(opt)
            
            return matched if matched else None
    except Exception as e:
        pass
    
    return None