# 安全知识竞赛助手

一个用于安全知识竞赛的 Streamlit 应用，支持自动答题、题库管理、错题收集等功能。
DEMO：https://lgbaqydt.streamlit.app
## 🎯 功能特性

- 🏃‍♂️ **自动答题** - 自动完成竞赛答题
- 📚 **题库管理** - 导入、导出、搜索题目
- 📕 **错题本** - 自动收集错题
- 🎰 **抽奖功能** - 自动抽取奖品
- 🤖 **AI辅助** - 支持调用AI进行答题
- ☁️ **云端同步** - 支持Gitee/GitHub题库同步

## 🚀 快速开始

### 本地运行

```bash
# 克隆仓库
git clone <your-repo-url>
cd <your-repo>

# 安装依赖
pip install -r requirements.txt

# 运行应用
streamlit run app.py
```

### 部署到 Streamlit Cloud

1. 在 GitHub 上创建仓库并推送到代码
2. 在 [streamlit.io](https://streamlit.io/) 登录并选择仓库
3. 在 Secrets 中配置：

```toml
GITHUB_TOKEN = "ghp_your_token"
GITHUB_OWNER = "your-username"
GITHUB_REPO = "your-repo"
GITHUB_BRANCH = "main"
GITHUB_QUESTIONS_PATH = "data/questions.json"
```

## 📁 项目结构

```
.
├── app.py              # Streamlit 主应用
├── api_client.py       # API 客户端
├── answer_engine.py    # 自动答题引擎
├── github_sync.py      # GitHub 同步模块
├── utils.py            # 工具函数
├── requirements.txt    # 依赖列表
└── data/              # 数据目录 (本地)
```

## 📝 使用说明

1. 在「开始答题」页面输入 TOKEN 和 MEMBER_ID
2. （可选）启用 AI 辅助答题
3. 点击「开始自动答题」
4. 在「题库管理」页面管理题库
5. 在「错题本」查看错题

## 🔑 获取 TOKEN 和 MEMBER_ID

1. 打开答题网页
2. 按 F12 打开开发者工具
3. 在网络请求中找到任意 API 请求
4. 在请求头中查看 token 和 memberId 字段

## ⚙️ 配置说明

| 配置项 | 说明 | 必需 |
|--------|------|------|
| TOKEN | 答题平台令牌 | 是 |
| MEMBER_ID | 用户ID | 是 |
| GITHUB_TOKEN | GitHub访问令牌 | 否 |
| AI_API_KEY | AI模型API密钥 | 否 |

## 📄 许可证

MIT License
