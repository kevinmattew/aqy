import requests
import base64
import json
import os
from datetime import datetime

class GitHubSync:
    def __init__(self):
        self.token = os.getenv('GITHUB_TOKEN', '')
        self.owner = os.getenv('GITHUB_OWNER', 'your-username')
        self.repo = os.getenv('GITHUB_REPO', 'your-repo')
        self.branch = os.getenv('GITHUB_BRANCH', 'main')
        self.questions_path = os.getenv('GITHUB_QUESTIONS_PATH', 'data/questions.json')
        
    def _get_headers(self):
        headers = {'Accept': 'application/vnd.github.v3+json'}
        if self.token:
            headers['Authorization'] = f'token {self.token}'
        return headers
    
    def _api_request(self, path, method='GET', body=None):
        url = f'https://api.github.com{path}'
        try:
            if method == 'GET':
                response = requests.get(url, headers=self._get_headers(), timeout=20)
            else:
                response = requests.request(method, url, headers=self._get_headers(), json=body, timeout=20)
            return response.json()
        except Exception as e:
            return {'error': str(e)}
    
    def get_questions(self):
        """从GitHub获取题库"""
        if not self.token:
            return {'success': False, 'reason': '未配置GitHub令牌'}
        
        resp = self._api_request(f'/repos/{self.owner}/{self.repo}/contents/{self.questions_path}')
        if 'content' in resp:
            decoded = base64.b64decode(resp['content']).decode('utf-8')
            return {'success': True, 'data': json.loads(decoded), 'sha': resp.get('sha')}
        return {'success': False, 'reason': resp.get('message', '获取失败')}
    
    def update_questions(self, content, sha=None):
        """更新GitHub上的题库"""
        if not self.token:
            return {'success': False, 'reason': '未配置GitHub令牌'}
        
        encoded = base64.b64encode(json.dumps(content, ensure_ascii=False).encode('utf-8')).decode('utf-8')
        data = {
            'message': f'更新题库 - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            'content': encoded,
            'branch': self.branch
        }
        if sha:
            data['sha'] = sha
        
        resp = self._api_request(f'/repos/{self.owner}/{self.repo}/contents/{self.questions_path}', method='PUT', body=data)
        if 'commit' in resp:
            return {'success': True, 'commit': resp['commit']['sha']}
        return {'success': False, 'reason': resp.get('message', '更新失败')}
    
    def sync_from_github(self):
        """从GitHub同步题库"""
        result = self.get_questions()
        if result['success']:
            return {'success': True, 'data': result['data'], 'sha': result['sha']}
        return result
    
    def sync_to_github(self, questions):
        """同步题库到GitHub"""
        current = self.get_questions()
        if not current['success']:
            return current
        
        sha = current.get('sha')
        return self.update_questions(questions, sha)
    
    def get_repo_info(self):
        """获取仓库信息"""
        resp = self._api_request(f'/repos/{self.owner}/{self.repo}')
        if 'name' in resp:
            return {
                'success': True,
                'name': resp['name'],
                'full_name': resp['full_name'],
                'description': resp.get('description', '')
            }
        return {'success': False, 'reason': resp.get('message', '获取失败')}

# 使用示例
if __name__ == '__main__':
    sync = GitHubSync()
    
    # 获取仓库信息
    info = sync.get_repo_info()
    print("仓库信息:", info)
    
    # 从GitHub获取题库
    questions = sync.sync_from_github()
    print("题库同步结果:", questions)
