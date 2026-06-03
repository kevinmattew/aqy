import streamlit as st
import asyncio
import json
from datetime import datetime
from utils import (
    load_bank, save_bank, load_wrong, save_wrong,
    load_stats, save_stats, init_built_in_bank, q_key, find_in_bank, BUILT_IN_BANK
)
from api_client import api_request, cloud_sync, GITEE_CONFIG, TOKEN, MEMBER_ID, AI_CONFIG
from answer_engine import run_auto_answer
from github_sync import GitHubSync

st.set_page_config(
    page_title="安全知识竞赛助手",
    page_icon="🎯",
    layout="wide"
)

if 'logs' not in st.session_state:
    st.session_state.logs = []

if 'stats' not in st.session_state:
    st.session_state.stats = load_stats()

if 'bank' not in st.session_state:
    st.session_state.bank = init_built_in_bank()

if 'wrong_list' not in st.session_state:
    st.session_state.wrong_list = load_wrong()


def add_log(msg):
    st.session_state.logs.append({
        'time': datetime.now().strftime('%H:%M:%S'),
        'msg': msg
    })
    if len(st.session_state.logs) > 200:
        st.session_state.logs = st.session_state.logs[-200:]


def render_logs():
    log_container = st.container()
    with log_container:
        for log_entry in st.session_state.logs:
            time = log_entry['time']
            msg = log_entry['msg']
            prefix = f"[{time}] "
            
            if '✅' in msg:
                st.success(prefix + msg)
            elif '❌' in msg:
                st.error(prefix + msg)
            elif '⚠️' in msg:
                st.warning(prefix + msg)
            else:
                st.info(prefix + msg)


def check_account_status(token, member_id):
    if not token or not member_id:
        return {'status': 'error', 'msg': '请填写账号信息'}
    
    import api_client
    old_token = api_client.TOKEN
    old_member_id = api_client.MEMBER_ID
    
    api_client.TOKEN = token
    api_client.MEMBER_ID = member_id
    
    try:
        result = api_client.api_request('/aqy/regist/competition')
        if isinstance(result, dict):
            if result.get('data'):
                return {
                    'status': 'success',
                    'msg': '账号已登录',
                    'data': {
                        'companyName': result['data'].get('companyName'),
                        'userCode': result['data'].get('userCode'),
                        'points': result['data'].get('points')
                    }
                }
            elif result.get('result', {}).get('code') == 100:
                return {'status': 'error', 'msg': '请先登录！Token可能已过期'}
            else:
                return {'status': 'error', 'msg': result.get('result', {}).get('msg', '未知错误')}
        else:
            return {'status': 'error', 'msg': '网络请求异常'}
    finally:
        api_client.TOKEN = old_token
        api_client.MEMBER_ID = old_member_id


def main():
    st.title("🎯 全民全域安全知识竞赛 · 自动答题助手")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🏃 开始答题", "📚 题库管理", "📕 错题本", "📊 统计"])
    
    with tab1:
        st.header("自动答题")
        
        col1, col2 = st.columns(2)
        with col1:
            token_input = st.text_input("🔑 TOKEN", value="", placeholder="请输入您的TOKEN", type="password")
        with col2:
            member_id_input = st.text_input("🆔 MEMBER_ID", value="", placeholder="请输入您的MEMBER_ID", type="password")
        
        st.subheader("📊 账号状态")
        status_placeholder = st.empty()
        
        if token_input and member_id_input:
            with status_placeholder:
                with st.spinner("检查账号状态..."):
                    status = check_account_status(token_input, member_id_input)
                
            status_placeholder.empty()
            
            if status['status'] == 'success':
                with st.container():
                    st.success(f"✅ {status['msg']}")
                    data = status['data']
                    if data.get('companyName'):
                        st.write(f"🏢 单位: {data['companyName']}")
                    if data.get('userCode'):
                        st.write(f"🆔 用户编号: {data['userCode']}")
                    if data.get('points'):
                        st.write(f"⭐ 当前积分: {data['points']}")
            else:
                st.error(f"❌ {status['msg']}")
        else:
            st.info("ℹ️ 请填写 TOKEN 和 MEMBER_ID 以检查账号状态")
        
        st.subheader("☁️ 题库同步配置（可选）")
        sync_source = st.radio(
            "同步源选择",
            ["GitHub (推荐)", "Gitee", "不同步"],
            index=0
        )
        
        st.subheader("🤖 AI 答题配置")
        # 默认用 Secrets 里的 AI 配置，默认启用
        ai_enabled = st.checkbox("启用 AI 辅助答题", value=bool(AI_CONFIG.get('api_key')), disabled=not bool(AI_CONFIG.get('api_key')))
        
        # 高级选项（展开显示 AI 配置
        with st.expander("⚙️ 高级：修改 AI 配置", expanded=False):
            ai_col1, ai_col2, ai_col3 = st.columns(3)
            with ai_col1:
                ai_api_key = st.text_input("AI API Key", value=AI_CONFIG.get('api_key', ''), placeholder="sk-xxx", type="password")
            with ai_col2:
                ai_api_url = st.text_input("API URL", value=AI_CONFIG.get('api_url', 'https://api.deepseek.com/v1/chat/completions'))
            with ai_col3:
                ai_model = st.text_input("模型名称", value=AI_CONFIG.get('model', 'deepseek-v4-flash'))
        
        if st.button("▶️ 开始自动答题", type="primary"):
            if not token_input or not member_id_input:
                st.error("请先填写 TOKEN 和 MEMBER_ID")
                return
            
            st.session_state.logs = []
            progress_bar = st.progress(0)
            
            async def run():
                import api_client
                api_client.TOKEN = token_input
                api_client.MEMBER_ID = member_id_input
                
                if ai_enabled:
                    api_client.AI_CONFIG['api_key'] = ai_api_key
                    api_client.AI_CONFIG['api_url'] = ai_api_url
                    api_client.AI_CONFIG['model'] = ai_model
                
                def progress_callback(msg):
                    add_log(msg)
                    progress_bar.progress(min(95, len(st.session_state.logs) * 2))
                
                result = await run_auto_answer(progress_callback, sync_source)
                progress_bar.progress(100)
                
                if result['success']:
                    add_log("🎉 答题完成！")
                    if result['prizes']:
                        add_log("🎁 获得奖品: " + ", ".join(result['prizes']))
                else:
                    add_log(f"❌ {result.get('error', '未知错误')}")
            
            asyncio.run(run())
        
        st.subheader("🎰 抽奖功能")
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("🎲 检查抽奖机会"):
                if not token_input or not member_id_input:
                    st.error("请先填写 TOKEN 和 MEMBER_ID")
                else:
                    import api_client
                    old_token, old_member_id = api_client.TOKEN, api_client.MEMBER_ID
                    api_client.TOKEN, api_client.MEMBER_ID = token_input, member_id_input
                    
                    try:
                        draw_info = api_client.api_request('/aqy/prize/getDrawSurplusNum', 'GET')
                        if isinstance(draw_info, dict) and draw_info.get('data'):
                            surplus = draw_info['data'].get('surplusNum', 0)
                            st.success(f"🎉 剩余抽奖次数: {surplus} 次")
                        else:
                            st.error("无法获取抽奖信息")
                    finally:
                        api_client.TOKEN, api_client.MEMBER_ID = old_token, old_member_id
            
            if st.button("🎁 立即抽奖"):
                if not token_input or not member_id_input:
                    st.error("请先填写 TOKEN 和 MEMBER_ID")
                    return
                
                import api_client
                old_token, old_member_id = api_client.TOKEN, api_client.MEMBER_ID
                api_client.TOKEN, api_client.MEMBER_ID = token_input, member_id_input
                
                try:
                    draw_info = api_client.api_request('/aqy/prize/getDrawSurplusNum', 'GET')
                    if not isinstance(draw_info, dict) or not draw_info.get('data'):
                        st.error("无法获取抽奖次数")
                        return
                    
                    draws = draw_info['data'].get('surplusNum', 0)
                    try:
                        draws = int(draws)
                    except:
                        draws = 0
                    
                    if draws <= 0:
                        st.warning("暂无抽奖机会")
                        return
                    
                    with st.spinner(f"正在抽取 {draws} 次..."):
                        prizes = []
                        for i in range(draws):
                            import time
                            time.sleep(0.8)
                            pr = api_client.api_request('/aqy/prize/drawPrize', 'POST')
                            name = '未知'
                            if isinstance(pr, dict):
                                name = pr.get('data', {}).get('prizeName', '未知')
                            prizes.append(name)
                        
                        st.success("🎉 抽奖完成！")
                        st.subheader("🎁 获得奖品")
                        for i, prize in enumerate(prizes, 1):
                            st.write(f"{i}. {prize}")
                finally:
                    api_client.TOKEN, api_client.MEMBER_ID = old_token, old_member_id
        
        st.subheader("📝 答题日志")
        log_expander = st.expander("查看日志", expanded=True)
        with log_expander:
            render_logs()
    
    with tab2:
        st.header("题库管理")
        
        bank = load_bank()
        bank_size = len(bank)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("题库总量", bank_size)
        col2.metric("内置题库", len(BUILT_IN_BANK))
        col3.metric("错题数量", len(st.session_state.wrong_list))
        
        by_scene = {}
        for v in bank.values():
            scene = v.get('scene', '未分类')
            by_scene[scene] = by_scene.get(scene, 0) + 1
        
        st.subheader("📊 题库分布")
        for scene, count in by_scene.items():
            st.write(f"- {scene}: {count} 题")
        
        st.subheader("🔍 搜索题目")
        search_query = st.text_input("输入关键词搜索题目", "")
        if search_query:
            found = []
            for v in bank.values():
                if search_query.lower() in v.get('q', '').lower():
                    found.append(v)
            
            if found:
                st.success(f"找到 {len(found)} 条匹配题目")
                for i, item in enumerate(found[:10], 1):
                    with st.expander(f"题目 {i}: {item['q'][:50]}..."):
                        st.write(f"**题目:** {item['q']}")
                        st.write(f"**选项:** {', '.join(item.get('opts', []))}")
                        st.write(f"**答案:** {', '.join(item.get('answer', item.get('ans', [])))}")
                        st.write(f"**类型:** {item.get('type', '单选')}")
            else:
                st.info("未找到匹配题目")
        
        st.subheader("➕ 添加新题目")
        with st.form("add_question_form"):
            q_text = st.text_input("题目内容")
            q_type = st.selectbox("题目类型", ["单选", "多选", "判断"])
            opts_input = st.text_area("选项（每行一个）")
            ans_input = st.text_input("正确答案（多个用逗号分隔）")
            
            if st.form_submit_button("添加题目"):
                if not q_text or not opts_input or not ans_input:
                    st.error("请填写完整信息")
                else:
                    opts = [line.strip() for line in opts_input.strip().split('\n') if line.strip()]
                    ans = [a.strip() for a in ans_input.strip().split(',') if a.strip()]
                    
                    new_q = {
                        'q': q_text.strip(),
                        'opts': opts,
                        'answer': ans,
                        'type': q_type,
                        'scene': '手动添加',
                        'updated': datetime.now().isoformat()
                    }
                    
                    bank[q_key(q_text)] = new_q
                    save_bank(bank)
                    st.session_state.bank = bank
                    st.success("✅ 题目添加成功！")
        
        st.subheader("📥 批量导入题库")
        upload_type = st.radio("导入方式", ["从剪贴板粘贴JSON", "上传JSON文件", "导入内置题库"])
        
        if upload_type == "从剪贴板粘贴JSON":
            raw_text = st.text_area("粘贴JSON格式题库", height=200)
            if st.button("解析导入"):
                if not raw_text:
                    st.error("请先粘贴内容")
                    return
                
                try:
                    items = []
                    trimmed = raw_text.strip()
                    
                    if trimmed.startswith('[') or trimmed.startswith('{'):
                        parsed = json.loads(trimmed)
                        if isinstance(parsed, list):
                            items = [
                                {
                                    'q': item.get('q', item.get('question', item.get('content', '')).strip()),
                                    'opts': item.get('opts', item.get('options', [])),
                                    'ans': item.get('ans', item.get('answer', item.get('correctAnswer', []))),
                                    'type': item.get('type', '单选')
                                }
                                for item in parsed if item.get('q') or item.get('question')
                            ]
                        else:
                            for v in parsed.values():
                                if v.get('q'):
                                    items.append({
                                        'q': v['q'],
                                        'opts': v.get('opts', []),
                                        'ans': v.get('answer', v.get('ans', [])),
                                        'type': v.get('type', '单选')
                                    })
                    
                    if items:
                        added = 0
                        for item in items:
                            key = q_key(item['q'])
                            if key not in bank:
                                bank[key] = {
                                    'q': item['q'],
                                    'opts': item['opts'],
                                    'answer': item['ans'] if isinstance(item['ans'], list) else [item['ans']],
                                    'type': item['type'],
                                    'scene': '导入',
                                    'level': '',
                                    'updated': datetime.now().strftime('%Y-%m-%d')
                                }
                                added += 1
                        save_bank(bank)
                        st.session_state.bank = bank
                        st.success(f"✅ 导入成功！新增 {added} 题，总计 {len(bank)} 题")
                    else:
                        st.error("❌ 未解析到任何题目")
                except Exception as e:
                    st.error(f"❌ 解析失败: {str(e)}")
        
        elif upload_type == "上传JSON文件":
            uploaded_file = st.file_uploader("选择JSON文件", type=['json'])
            if uploaded_file:
                try:
                    raw_text = uploaded_file.read().decode('utf-8')
                    st.text_area("文件内容预览", raw_text, height=150)
                    
                    if st.button("解析并导入"):
                        items = []
                        trimmed = raw_text.strip()
                        
                        if trimmed.startswith('[') or trimmed.startswith('{'):
                            parsed = json.loads(trimmed)
                            if isinstance(parsed, list):
                                items = [
                                    {
                                        'q': item.get('q', item.get('question', '')),
                                        'opts': item.get('opts', item.get('options', [])),
                                        'ans': item.get('ans', item.get('answer', [])),
                                        'type': item.get('type', '单选')
                                    }
                                    for item in parsed if item.get('q')
                                ]
                        
                        if items:
                            added = 0
                            for item in items:
                                key = q_key(item['q'])
                                if key not in bank:
                                    bank[key] = {
                                        'q': item['q'],
                                        'opts': item['opts'],
                                        'answer': item['ans'] if isinstance(item['ans'], list) else [item['ans']],
                                        'type': item['type'],
                                        'scene': '导入',
                                        'level': '',
                                        'updated': datetime.now().strftime('%Y-%m-%d')
                                    }
                                    added += 1
                            save_bank(bank)
                            st.session_state.bank = bank
                            st.success(f"✅ 导入成功！新增 {added} 题")
                except Exception as e:
                    st.error(f"❌ 读取文件失败: {str(e)}")
        
        elif upload_type == "导入内置题库":
            st.info(f"📚 内置题库包含 {len(BUILT_IN_BANK)} 道题目")
            if st.button("📥 导入内置题库"):
                added = 0
                for q in BUILT_IN_BANK:
                    key = q_key(q['q'])
                    if key not in bank:
                        bank[key] = {
                            'q': q['q'],
                            'opts': q.get('opts', []),
                            'answer': q.get('answer', q.get('ans', [])),
                            'type': q.get('type', '单选'),
                            'scene': '内置',
                            'level': '',
                            'updated': datetime.now().strftime('%Y-%m-%d')
                        }
                        added += 1
                save_bank(bank)
                st.session_state.bank = bank
                st.success(f"✅ 导入成功！新增 {added} 题，总计 {len(bank)} 题")
        
        st.subheader("📤 导出题库")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📋 导出到剪贴板"):
                arr = [{
                    'q': v['q'],
                    'type': v['type'],
                    'options': v['opts'],
                    'answer': v['answer'],
                    'scene': v.get('scene', '')
                } for v in bank.values()]
                st.code(json.dumps(arr, ensure_ascii=False, indent=2), language='json')
        
        with col2:
            if st.button("💾 导出到文件"):
                arr = [{
                    'q': v['q'],
                    'type': v['type'],
                    'options': v['opts'],
                    'answer': v['answer'],
                    'scene': v.get('scene', '')
                } for v in bank.values()]
                json_content = json.dumps(arr, ensure_ascii=False, indent=2)
                st.download_button(
                    label="📥 下载题库.json",
                    data=json_content,
                    file_name=f"questions_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )
        
        st.subheader("🔄 云端同步")
        
        sync_source = st.radio("选择同步源", ["Gitee", "GitHub"])
        
        if sync_source == "Gitee":
            if not GITEE_CONFIG['enabled']:
                st.info("☁️ Gitee云同步已禁用")
            else:
                if st.button("☁️ 从Gitee同步题库"):
                    with st.spinner("正在同步..."):
                        result = asyncio.run(cloud_sync())
                        if result['success']:
                            st.success(f"✅ 同步完成！\n- 题库新增: {result['bank_added']} 题\n- 错题新增: {result['wrong_added']} 条")
                            st.session_state.bank = load_bank()
                            st.session_state.wrong_list = load_wrong()
                        else:
                            st.error(f"❌ 同步失败: {result['reason']}")
        
        else:
            gh_sync = GitHubSync()
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⬇️ 从GitHub拉取题库"):
                    with st.spinner("正在从GitHub拉取..."):
                        result = gh_sync.sync_from_github()
                        if result['success']:
                            questions = result['data']
                            if isinstance(questions, dict):
                                for k, v in questions.items():
                                    if v.get('q'):
                                        bank[q_key(v['q'])] = v
                            elif isinstance(questions, list):
                                for q in questions:
                                    if q.get('q'):
                                        bank[q_key(q['q'])] = {
                                            'q': q['q'],
                                            'opts': q.get('opts', q.get('options', [])),
                                            'answer': q.get('answer', q.get('ans', [])),
                                            'type': q.get('type', '单选'),
                                            'scene': 'GitHub',
                                            'level': '',
                                            'updated': datetime.now().strftime('%Y-%m-%d')
                                        }
                            save_bank(bank)
                            st.session_state.bank = bank
                            st.success(f"✅ 拉取成功！当前题库共 {len(bank)} 题")
                        else:
                            st.error(f"❌ 拉取失败: {result.get('reason', '未知错误')}")
            
            with col2:
                if st.button("⬆️ 上传题库到GitHub"):
                    with st.spinner("正在上传到GitHub..."):
                        result = gh_sync.sync_to_github(bank)
                        if result['success']:
                            st.success(f"✅ 上传成功！Commit: {result['commit'][:7]}")
                        else:
                            st.error(f"❌ 上传失败: {result.get('reason', '未知错误')}")
        
        st.subheader("🗑️ 管理操作")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("清空全部题库", type="secondary"):
                if st.checkbox("确认清空"):
                    save_bank({})
                    st.session_state.bank = {}
                    st.success("✅ 已清空题库")
        
        with col2:
            if st.button("刷新题库"):
                st.session_state.bank = load_bank()
                st.success("✅ 题库已刷新")
    
    with tab3:
        st.header("错题本")
        
        wrong_list = load_wrong()
        
        if not wrong_list:
            st.info("🎉 暂无错题")
            return
        
        st.metric("错题数量", len(wrong_list))
        
        by_date = {}
        for w in wrong_list:
            date = w.get('date', '').split('T')[0] if w.get('date') else datetime.now().strftime('%Y-%m-%d')
            if date not in by_date:
                by_date[date] = []
            by_date[date].append(w)
        
        dates = sorted(by_date.keys(), reverse=True)
        selected_date = st.selectbox("选择日期", dates)
        
        if selected_date:
            st.subheader(f"📅 {selected_date}")
            for i, w in enumerate(by_date[selected_date]):
                with st.expander(f"[{w.get('type', '单选')}] {w['q'][:50]}..."):
                    st.write(f"**题目**: {w['q']}")
                    st.write("**选项**:")
                    for j, opt in enumerate(w.get('opts', [])):
                        prefix = '✅ ' if opt in (w.get('correctAnswer', [])) else ''
                        prefix += '❌ ' if opt in (w.get('myAnswer', [])) else ''
                        st.write(f"  {chr(65+j)}. {prefix}{opt}")
                    st.write(f"**我的答案**: {', '.join(w.get('myAnswer', []))}")
                    st.write(f"**正确答案**: {', '.join(w.get('correctAnswer', []))}")
                    st.write(f"**来源**: {w.get('source', '')}")
                    st.write(f"**场景**: {w.get('scene', '')} · 关卡{w.get('level', '')}")
        
        if st.button("清空错题本"):
            if st.confirm("确定要清空所有错题吗？"):
                save_wrong([])
                st.success("已清空")
    
    with tab4:
        st.header("统计信息")
        
        stats = load_stats()
        bank = load_bank()
        wrong_list = load_wrong()
        
        total_answered = stats.get('totalCorrect', 0) + stats.get('totalWrong', 0)
        accuracy = round(stats.get('totalCorrect', 0) / total_answered * 100, 1) if total_answered > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("运行次数", stats.get('totalRuns', 0))
        col2.metric("答题总数", total_answered)
        col3.metric("正确率", f"{accuracy}%")
        col4.metric("题库总量", len(bank))
        
        st.subheader("📈 答题详情")
        st.write(f"- ✅ 答对: {stats.get('totalCorrect', 0)}")
        st.write(f"- ❌ 答错: {stats.get('totalWrong', 0)}")
        st.write(f"- 🤖 AI答题: {stats.get('totalAI', 0)}")
        st.write(f"- ✋ 手动答题: {stats.get('totalManual', 0)}")
        
        st.subheader("📕 错题统计")
        st.write(f"- 累计错题: {len(wrong_list)} 条")
        
        today = datetime.now().strftime('%Y-%m-%d')
        today_wrong = sum(1 for w in wrong_list if w.get('date', '').startswith(today))
        st.write(f"- 今日错题: {today_wrong} 条")
        
        try:
            reg = api_request('/aqy/regist/competition', 'GET')
            if reg and reg.get('data'):
                st.subheader("🏆 当前积分")
                st.write(f"- 积分: {reg['data'].get('points', '??')}")
                st.write(f"- 剩余抽奖: {reg['data'].get('drawNum', '??')}")
                st.write(f"- 今日已答: {'是' if reg['data'].get('isAnswered') in [True, 'true'] else '否'}")
        except:
            pass


if __name__ == "__main__":
    main()