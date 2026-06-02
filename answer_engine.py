import asyncio
import time
from utils import (
    load_bank, save_bank, load_wrong, save_wrong, 
    load_stats, save_stats, find_in_bank, q_key, init_built_in_bank,
    SCENE_NAME, QMAP
)
from api_client import api_request, cloud_sync, ask_ai


async def answer_one_question(qid, bank, wrong_list, stats, scene_name, level_no):
    result = {
        'success': False,
        'question': '',
        'my_answer': [],
        'correct_answer': [],
        'is_correct': False,
        'source': '',
        'error': ''
    }
    
    qr = api_request(f'/aqy/ques/{qid}/hiddenDangerQues', 'GET')
    if not qr or not isinstance(qr, dict) or not qr.get('data') or not qr['data'].get('ques'):
        result['error'] = '获取题目失败'
        return result, bank, wrong_list, stats
    
    ques = qr['data']['ques']
    opts = ques.get('options', [])
    q_type = 'multiple' if ques.get('quesType') in ['2', 2] else 'single'
    question_text = ques.get('content', '')
    
    result['question'] = question_text
    
    my_answer = None
    source = ''
    
    found = find_in_bank(bank, question_text)
    if found and found.get('answer') and len(found['answer']) > 0:
        mapped = []
        for ans in found['answer']:
            if ans in opts:
                mapped.append(ans)
                continue
            clean_ans = ans.replace(' ', '')
            for opt in opts:
                clean_opt = opt.replace(' ', '')
                if clean_opt == clean_ans or opt in ans or ans in opt:
                    if opt not in mapped:
                        mapped.append(opt)
                    break
        if mapped:
            my_answer = mapped
            source = '题库'
    
    if not my_answer:
        my_answer = await ask_ai(question_text, opts, q_type)
        if my_answer:
            source = 'AI'
            stats['totalAI'] += 1
    
    if not my_answer:
        my_answer = [opts[0]] if opts else []
        source = '随机'
    
    result['my_answer'] = my_answer
    result['source'] = source
    
    ans = api_request('/aqy/ques/answerQues', 'POST', {
        'quesId': ques.get('quesId'),
        'answerOptions': my_answer
    })
    
    if ans and isinstance(ans, dict) and ans.get('data') and ans['data'].get('rightOptions'):
        correct = ans['data']['rightOptions']
        result['correct_answer'] = correct
        
        is_correct = len(my_answer) == len(correct) and sorted(my_answer) == sorted(correct)
        result['is_correct'] = is_correct
        result['success'] = True
        
        key = q_key(question_text)
        new_question_data = {
            'q': question_text,
            'opts': opts,
            'answer': correct,
            'type': ques.get('quesTypeStr') or ('多选' if q_type == 'multiple' else '单选'),
            'scene': scene_name,
            'level': level_no,
            'updated': time.strftime('%Y-%m-%d', time.localtime())
        }
        
        bank[key] = new_question_data
        
        if is_correct:
            stats['totalCorrect'] += 1
        else:
            stats['totalWrong'] += 1
            wrong_list.append({
                'date': time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime()),
                'q': question_text,
                'opts': opts,
                'type': ques.get('quesTypeStr') or q_type,
                'myAnswer': my_answer,
                'correctAnswer': correct,
                'source': source,
                'scene': scene_name,
                'level': level_no
            })
    
    return result, bank, wrong_list, stats


async def run_auto_answer(progress_callback=None):
    logs = []
    
    def log(msg):
        logs.append(msg)
        if progress_callback:
            progress_callback(msg)
    
    if not api_request.__globals__.get('TOKEN') or not api_request.__globals__.get('MEMBER_ID'):
        return {'success': False, 'error': '未配置 TOKEN 或 MEMBER_ID', 'logs': logs}
    
    bank = init_built_in_bank()
    wrong_list = load_wrong()
    stats = load_stats()
    stats['totalRuns'] += 1
    
    log('🚀 开始自动答题')
    log(f'⏰ {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
    log(f'📚 题库 {len(bank)} 题 | 📕 错题 {len(wrong_list)} 条')
    
    log('📝 [1/4] 注册竞赛...')
    api_request('/aqy/regist/activity', 'GET')
    reg = api_request('/aqy/regist/competition', 'GET')
    
    if not reg or not isinstance(reg, dict):
        log('❌ 注册失败 - 网络请求异常')
        save_stats(stats)
        return {'success': False, 'error': '注册失败 - 网络请求异常', 'logs': logs}
    
    if reg.get('result', {}).get('code') == 100:
        log('❌ 注册失败 - ' + reg.get('result', {}).get('msg', '请先登录'))
        save_stats(stats)
        return {'success': False, 'error': '注册失败 - ' + reg.get('result', {}).get('msg', '请检查TOKEN和MEMBER_ID是否正确'), 'logs': logs}
    
    if not reg.get('data'):
        log('❌ 注册失败 - 无返回数据')
        save_stats(stats)
        return {'success': False, 'error': '注册失败 - 无返回数据', 'logs': logs}
    
    log(f'   ✅ {reg["data"].get("companyName", "")} | {reg["data"].get("userCode", "")} | 积分:{reg["data"].get("points", 0)} | 剩余抽奖:{reg["data"].get("drawNum", 0)} | 已答:{reg["data"].get("isAnswered", False) and "是" or "否"}')
    
    if reg['data'].get('isAnswered') in [True, 'true']:
        log('⛔ 今日已完成挑战，明天再来！')
        save_stats(stats)
        return {'success': False, 'error': '今日已完成', 'logs': logs}
    
    log('📊 [2/4] 获取场景...')
    info = api_request('/aqy/user/level/getUserSceneAndLevel', 'GET')
    
    if not info or not isinstance(info, dict) or not info.get('data') or not info['data'].get('list'):
        log('❌ 获取场景失败')
        save_stats(stats)
        return {'success': False, 'error': '获取场景失败', 'logs': logs}
    
    for s in info['data']['list']:
        no = s.get('sceneNo')
        log(f'   {SCENE_NAME.get(str(no), no)}: {s.get("finishLevelNo", 0)}/6 关')
    
    log('📖 [3/4] 答题...')
    round_count = 0
    all_results = []
    
    for scene in info['data']['list']:
        s_no = str(scene.get('currentSceneNo') or scene.get('sceneNo'))
        finished = scene.get('finishLevelNo', 0)
        s_name = SCENE_NAME.get(s_no, '场景' + s_no)
        
        if s_no not in QMAP:
            continue
        
        for lv in range(1, 7):
            if lv <= finished:
                continue
            if lv > finished + 1:
                break
            
            ids = QMAP[s_no].get(str(lv))
            if not ids:
                continue
            
            log(f'\n── {s_name} · 关卡{lv} ──')
            round_count += 1
            
            init = api_request('/aqy/user/level/getUserLevelAndInit', 'GET', {'sceneNo': int(s_no)})
            if not init or not isinstance(init, dict) or not init.get('data'):
                log('   ⚠️ 初始化场景失败')
                continue
            
            start = api_request('/aqy/ques/startLevel', 'GET', {'scene': s_no, 'level': str(lv)})
            if not start or not isinstance(start, dict) or not start.get('data'):
                log('   ⚠️ startLevel 失败')
                continue
            
            qids = ids
            for i, qid in enumerate(qids):
                log(f'   [{i+1}/{len(qids)}]')
                result, bank, wrong_list, stats = await answer_one_question(
                    qid, bank, wrong_list, stats, s_name, lv
                )
                all_results.append(result)
                
                status = '✅' if result['is_correct'] else '❌'
                title = result['question'][:35] + '…' if len(result['question']) > 35 else result['question']
                log(f'   {status} [{result["source"]}] {title}')
                
                if not result['is_correct']:
                    log(f'      我选: {", ".join(result["my_answer"])}')
                    log(f'      正确: {", ".join(result["correct_answer"])}')
                
                await asyncio.sleep(0.8)
            
            log('   📤 交卷...')
            sub = api_request('/aqy/ques/submitCompetition', 'POST')
            if sub and isinstance(sub, dict) and sub.get('data'):
                log(f'   🏆 得分{sub["data"].get("score", 0)} | 对{sub["data"].get("correctNum", 0)} 错{sub["data"].get("errorNum", 0)} | {sub["data"].get("correctRate", 0)}%')
            
            await asyncio.sleep(1.5)
    
    if round_count == 0:
        log('\n💤 所有关卡已完成')
    
    log('\n🎰 [4/4] 抽奖阶段')
    draw_info = api_request('/aqy/prize/getDrawSurplusNum', 'GET')
    draws = 0
    if draw_info and isinstance(draw_info, dict):
        draws = draw_info.get('data', {}).get('surplusNum', 0)
    try:
        draws = int(draws)
    except:
        draws = 0
    log(f'   可抽 {draws} 次')
    
    prizes = []
    for i in range(draws):
        await asyncio.sleep(1.2)
        pr = api_request('/aqy/prize/drawPrize', 'POST')
        name = '未知'
        if pr and isinstance(pr, dict):
            name = pr.get('data', {}).get('prizeName', '未知')
        prizes.append(name)
        log(f'   🎁 {i+1}: {name}')
    
    await cloud_sync()
    
    stats['bankSize'] = len(bank)
    save_bank(bank)
    save_wrong(wrong_list)
    save_stats(stats)
    
    log(f'\n✅ 完成! 题库 {stats["bankSize"]} 题')
    if prizes:
        log(f'🎁 {", ".join(prizes)}')
    
    return {
        'success': True,
        'logs': logs,
        'stats': stats,
        'prizes': prizes,
        'results': all_results
    }