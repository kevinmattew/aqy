import re
import json
import os
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

BANK_PATH = DATA_DIR / "bank.json"
WRONG_PATH = DATA_DIR / "wrong.json"
STATS_PATH = DATA_DIR / "stats.json"

SCENE_NAME = {"1": "社区", "2": "乡村", "3": "企业", "4": "家庭", "5": "学校"}
SCENE_CODE = {"1": "community", "2": "countryside", "3": "enterprise", "4": "family", "5": "school"}

QMAP = {
    "1": {"1": ["IAwEB9LzlugoIBQc", "ICgEMtLzlugkOBww", "IBgEedLzlugIMCg0", "IDwETNLzlugEKCAY", "IAAELdLzlug0EAAE"],
          "2": ["IDAEZtLzlugYGDQA", "JCwErdLzlug4DBA0", "JAgEmNLzlug0FBgY", "IBQEU9LzlugUADws", "JAQEstLzlugoJAwA"],
          "3": ["JBAEzNLzlugINDAo", "JDgE09LzlugYHCwc", "JBwE5tLzlugUBCQw", "JDQE-dLzlugELDgE", "JCAEh9LzlugkPAQs"],
          "4": ["KBwELdLzlugtKCQk", "KBAEB9LzlugxGDA8", "KDgEGNLzlughMCwI", "KDQEMtLzlug9ADgQ", "KCAETNLzlugdEAQ4"],
          "5": ["KCwEZtLzlugBIBAg", "LDAErdLzlughNDQU", "LBQEmNLzlugtLDw4", "KAQEedLzlugRCAwU", "KAgEU9LzlugNOBgM"],
          "6": ["LCgE-dLzlugdFBwk", "LDwEh9Lzlug9BCAM", "LAwEzNLzlugRDBQI", "LAAE5tLzlugNPAAQ", "LBgEstLzlugxHCgg"]},
    "2": {"1": ["LCQE09LzlugBJAg8", "MBgAHNLzlugKOAAo", "MDwAKdLzlugGIAgE", "MBQANtLzlugWCBQw", "MDAAA9LzlugaEBwc"],
          "2": ["MCgAV9LzlugmMDQs", "MCQAfdLzlug6ACA0", "MAAASNLzlug2GCgY", "MAwAYtLzlugqKDwA", "NDQAnNLzlugGJBAY"],
          "3": ["NCwAyNLzlug6BDgo", "NBwAg9LzlugWDAws", "NDgAttLzlugaFAQA", "NAgA_dLzlug2HDAE", "NBAAqdLzlugKPBg0"],
          "4": ["OAQAHNLzlugTACQI", "NCAA4tLzlugmNCww", "OCAAKdLzlugfGCwk", "OAgANtLzlugPMDAQ", "NAQA19LzlugqLCQc"],
          "5": ["OCwAA9LzlugDKDg8", "OBwASNLzlugvIAw4", "ODgAfdLzlugjOAQU", "OBAAYtLzlugzEBgg", "ODQAV9Lzlug_CBAM"],
          "6": ["PAwAqdLzlugTBDwU", "PCgAnNLzlugfHDQ4", "PCQAttLzlugDLCAg", "PDAAyNLzlugjPBwI", "PAAAg9LzlugPNCgM"]},
    "3": {"1": ["BCAIDdLzluhgLBQU", "PDwA4tLzlug_DAgQ", "PBgA19LzlugzFAA8", "BAQIONLzluhsNBw4", "PBQA_dLzlugvJBQk"],
          "2": ["BDgIWdLzluhcDDwk", "BBwIbNLzluhQFDQI", "BCwIJ9Lzluh8HAAM", "BAgIEtLuhwBAgg", "BBAIRtLzluhMJCAQ"],
          "3": ["ACQIktLzluh8GBgQ", "BDQIc9LzluhAPCg8", "ACgIuNLzluhgKAwI", "AAwIjdLzluhsMAQk", "AAAIp9LzluhwABA8"],
          "4": ["ADAI7NLzluhcCCQ4", "ABQI2dLzluhQECwU", "DBgIONLzluh1DDgY", "ABgI89LzluhMIDgM", "ADwIxtLzluhAODAg"],
          "5": ["DAAIbNLzluhJLBAo", "DBQIEtLzluhpPCwA", "DCQIWdLzluhFNBgE", "DDwIDdLzluh5FDA0", "DDAIJ9LzluhlJCQs"],
          "6": ["DAwIRtLzluhVHAQw", "CDgIktLzluhlIDww", "DCgIc9LzluhZBAwc", "CDQIuNLzluh5ECgo", "CBAIjdLzluh1CCAE"]},
    "4": {"1": ["CBwIp9LzluhpODQc", "CAgI2dLzluhJKAg0", "CCwI7NLzluhFMAAY", "CAQI89LzluhVGBws", "CCAIxtLzluhZABQA"],
          "2": ["FDgMPNLzluheBBQ4", "FBwMCdLzluhSHBwU", "FBAMI9LzluhOLAgM", "FDQMFtLzluhCNAAg", "FCAMaNLzluhiJDwI"],
          "3": ["EDAMidLzluheAAwk", "FAgMd9LzluhyDCA8", "FAQMXdLzluhuPDQk", "EBQMvNLzluhSGAQI", "FCwMQtLzluh-FCgQ"],
          "4": ["EDwMo9LzluhCMBg8", "EBgMltLzluhOKBAQ", "EAAMwtLzluhyCDgg", "ECgM3dLzluhiICQU", "EAwM6NLzluhuOCw4"],
          "5": ["HAwMI9LzluhXFCws", "HCQMPNLzluhHPDAY", "ECQM99Lzluh-EDAM", "HCgMFtLzluhbDCQA", "HAAMCdLzluhLJDg0"],
          "6": ["HDwMaNLzluh7HBgo", "HBgMXdLzluh3BBAE", "HDAMQtLzluhnLAww", "HBQMd9LzluhrNAQc", "GAgMvNLzluhLICAo"]},
    "5": {"1": ["GCwMidLzluhHOCgE", "GAQMltLzluhXEDQw", "GCAMo9LzluhbCDwc", "GBAM6NLzluh3AAgY", "GDQM3dLzluh7GAA0"],
          "2": ["KCQcHNLzluiUMCQM", "KAAcKdLzluiYKCwg", "GBwMwtLzluhrMBwA", "GDgM99LzluhnKBQs", "KCgcNtLzluiIADAU"],
          "3": ["KAwcA9LzluiEGDg4", "KDwcSNLzluioEAw8", "KBgcfdLzluikCAQQ", "KDAcYtLzlui0IBgk", "KBQcV9Lzlui4OBAI"],
          "4": ["LAgcnNLzluiYLDQ8", "LCwcqdLzluiUNDwQ", "LAQcttLzluiEHCAk", "LCAcg9LzluiIBCgI", "LBAcyNLzluikDBwM"],
          "5": ["IDgcHNLzluiNCAAs", "LBwc4tLzlui4PAgU", "LDQc_dLzluioFBQg", "LDgc19Lzlui0JAA4", "IBwcKdLzluiBEAgA"],
          "6": ["ICwcYtLzluitGDwE", "ICAcSNLzluixKCgc", "IDQcNtLzluiROBQ0", "IBAcA9LzluidIBwY", "IAQcfdLzlui9MCAw"]}
}


def q_key(content):
    clean = re.sub(r'[\s（）()，。、？！""《》\u3000]', '', str(content)).strip()
    h = 0
    for i in range(len(clean)):
        h = ((h << 5) - h + ord(clean[i])) & 0xFFFFFFFF
    return "q_" + str(abs(h))


def load_json(path):
    if not path.exists():
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_bank():
    return load_json(BANK_PATH) or {}


def save_bank(bank):
    save_json(BANK_PATH, bank)


def load_wrong():
    return load_json(WRONG_PATH) or []


def save_wrong(wrong):
    save_json(WRONG_PATH, wrong)


def load_stats():
    return load_json(STATS_PATH) or {
        'totalRuns': 0, 'totalCorrect': 0, 'totalWrong': 0,
        'totalAI': 0, 'totalManual': 0, 'bankSize': 0
    }


def save_stats(stats):
    save_json(STATS_PATH, stats)


def find_in_bank(bank, question_text):
    key = q_key(question_text)
    if key in bank:
        return bank[key]

    clean_q = re.sub(r'[\s（）()，。、？！""《》\u3000]', '', str(question_text))
    best_match = None
    highest_score = 0

    for k, v in bank.items():
        clean_b = re.sub(r'[\s（）()，。、？！""《》\u3000]', '', str(v.get('q', '')))

        if abs(len(clean_q) - len(clean_b)) > 5:
            continue

        match_count = sum(1 for c in clean_q if c in clean_b)
        score = match_count / max(len(clean_q), len(clean_b))

        if score > highest_score:
            highest_score = score
            best_match = v

    if highest_score > 0.85:
        return best_match
    return None


BUILT_IN_BANK = [
    {"q": "《中华人民共和国突发事件应对法》适用于地质灾害的预防与应急准备、监测与预警、应急处置与救援、事后恢复与重建等应对活动。", "opts": ["正确", "错误"], "ans": ["正确"], "type": "判断"},
    {"q": "根据《危险化学品安全管理条例》，生产、储存危险化学品的单位，应当在其作业场所和安全设施、设备上设置明显的安全警示标志。", "opts": ["正确", "错误"], "ans": ["正确"], "type": "判断"},
    {"q": "生产经营单位重大事故隐患排查治理情况应当及时向负有安全生产监督管理职责的部门和职工大会或者职工代表大会报告。", "opts": ["正确", "错误"], "ans": ["正确"], "type": "判断"},
    {"q": "根据《中华人民共和国安全生产法》，生产经营单位的（ ）是本单位安全生产第一责任人，对本单位的安全生产工作全面负责。", "opts": ["技术负责人", "主要负责人", "安全总监"], "ans": ["主要负责人"], "type": "单选"},
    {"q": "根据《中华人民共和国突发事件应对法》，按照社会危害程度、影响范围等因素，突发自然灾害分为特别重大、重大、一般重大和较大四级。", "opts": ["正确", "错误"], "ans": ["错误"], "type": "判断"},
    {"q": "飞线充电时，私拉的电线暴露在外，易受风吹日晒及雨淋，导致绝缘体磨损和老化，引发漏电和短路。", "opts": ["对", "错"], "ans": ["对"], "type": "判断"},
    {"q": "阳台的窗台上放置花盆若未固定稳固或无护栏等防护措施，可能因风力、震动或碰撞而坠落，砸伤行人或车辆。", "opts": ["对", "错"], "ans": ["对"], "type": "判断"},
    {"q": "关于儿童居家安全，下列说法正确的是（  ）。", "opts": ["家长应教育孩子不要在家中攀爬阳台上的防护栏杆", "家长应对家中窗户、阳台等存在安全隐患的部位加强防护", "家长可以单独将孩子留在房中", "家中床和桌子不要紧挨窗户，以免孩子攀爬上去"], "ans": ["家长应教育孩子不要在家中攀爬阳台上的防护栏杆", "家长应对家中窗户、阳台等存在安全隐患的部位加强防护", "家中床和桌子不要紧挨窗户，以免孩子攀爬上去"], "type": "多选"},
    {"q": "《食品安全法》中规定，食品生产经营应当符合食品安全标准，具有与生产经营的食品品种、数量相适应的生产经营设备或者设施，有相应的消毒、更衣、盥洗、采光、照明、通风、防腐、（  ）、洗涤以及处理废水、存放垃圾和废弃物的设备或者设施。", "opts": ["防尘", "防蝇", "防鼠", "防虫"], "ans": ["防尘", "防蝇", "防鼠", "防虫"], "type": "多选"},
    {"q": "电线穿墙敷设但未穿管保护时，未穿管保护的电线易受墙体挤压、摩擦，导致电线绝缘层破损，进而引发短路、漏电甚至火灾。", "opts": ["对", "错"], "ans": ["对"], "type": "判断"},
    {"q": "摩托车驾驶人必须佩戴头盔的主要目的是（  ）。", "opts": ["防止头发被风吹乱", "避免被交警处罚", "降低头部受伤风险"], "ans": ["降低头部受伤风险"], "type": "单选"},
    {"q": "灭火器是扑灭初期火灾的关键工具。", "opts": ["对", "错"], "ans": ["对"], "type": "判断"},
    {"q": "任何单位、个人不得损坏、挪用或者擅自拆除、停用消防设施、器材，不得埋压、圈占、遮挡消火栓或者占用防火间距，不得（  ）疏散通道、安全出口、消防车通道。", "opts": ["占用", "堵塞", "封闭", "使用"], "ans": ["占用", "堵塞", "封闭"], "type": "多选"},
    {"q": "电动车在室内充电可能会引发火灾。", "opts": ["对", "错"], "ans": ["对"], "type": "判断"},
    {"q": "《高等学校消防安全管理规定》中要求，学生宿舍、教室和礼堂等人员密集场所，禁止违规使用大功率电器。", "opts": ["对", "错"], "ans": ["对"], "type": "判断"},
    {"q": "在客厅内吸完烟后，应将烟头熄灭后，放进烟灰缸内。", "opts": ["对", "错"], "ans": ["对"], "type": "判断"},
    {"q": "烟花爆竹若存放不当，极易因摩擦、明火或自燃引发火灾及爆炸事故。", "opts": ["对", "错"], "ans": ["对"], "type": "判断"},
    {"q": "农田垃圾中的塑料薄膜长期滞留土壤中，会导致（  ）。", "opts": ["土壤透气性增加", "土壤板结和微生物减少", "农作物产量提升"], "ans": ["土壤板结和微生物减少"], "type": "单选"},
    {"q": "作业人员在存在可燃性粉尘的车间内吸烟，吸烟产生的火星或高温可能引发粉尘爆炸，导致群死群伤。", "opts": ["对", "错"], "ans": ["对"], "type": "判断"},
    {"q": "使用燃气灶做饭时，可以中途离开现场。", "opts": ["对", "错"], "ans": ["错"], "type": "判断"},
    {"q": "下列选项中，不能用微波炉加热的有（  ）。", "opts": ["完整带壳的生鸡蛋", "未开封的罐头", "铝箔纸包裹的食物", "带壳且未开口的板栗"], "ans": ["完整带壳的生鸡蛋", "未开封的罐头", "铝箔纸包裹的食物", "带壳且未开口的板栗"], "type": "多选"},
    {"q": "《学生伤害事故处理办法》中规定，因学校的校舍、场地、其他公共设施，以及学校提供给学生使用的学具、教育教学和生活设施、设备不符合国家规定的标准，或者有明显不安全因素造成学生伤害的，学校应当依法承担相应的责任。", "opts": ["对", "错"], "ans": ["对"], "type": "判断"},
    {"q": "校园欺凌只发生在男生之间，女生之间不会出现。", "opts": ["对", "错"], "ans": ["错"], "type": "判断"},
    {"q": "气瓶使用时，氧气瓶与乙炔瓶的工作间距不应小于（  ）m，气瓶与明火作业点的距离不应小于10m。", "opts": ["5.0", "7.0", "10.0"], "ans": ["5.0"], "type": "单选"},
    {"q": "乙炔气瓶在任何情况下均可横躺卧放，不会存在安全隐患。", "opts": ["对", "错"], "ans": ["错"], "type": "判断"},
    {"q": "焊接作业时，工器具随意放置在地面或通道上，作业人员或巡检人员可能被绊倒，导致摔伤等意外事故。", "opts": ["对", "错"], "ans": ["对"], "type": "判断"},
    {"q": "以人体作为叉车配重可能导致的不良后果有（  ）。", "opts": ["人员挤压伤亡", "叉车失稳倾覆", "货物损毁", "货物堆放不整齐"], "ans": ["人员挤压伤亡", "叉车失稳倾覆", "货物损毁"], "type": "多选"},
    {"q": "发现配电箱严重锈蚀，首先应（  ）。", "opts": ["刷油漆遮盖锈迹", "切断电源并联系电工更换", "继续使用至彻底损坏"], "ans": ["切断电源并联系电工更换"], "type": "单选"},
    {"q": "书籍堆放过高容易导致（  ）。", "opts": ["书籍倾倒掉落伤人", "书籍褪色", "书籍受潮"], "ans": ["书籍倾倒掉落伤人"], "type": "单选"},
    {"q": "点燃蚊香后，蚊香应远离（  ）。", "opts": ["窗帘", "纸张", "衣物", "床单"], "ans": ["窗帘", "纸张", "衣物", "床单"], "type": "多选"},
    {"q": "只要不转账，点击诈骗链接看看没关系。", "opts": ["对", "错"], "ans": ["错"], "type": "判断"},
    {"q": "化学实验中会接触到各种具有腐蚀性的化学试剂，如强酸、强碱等，实验人员若穿着短裤、短袖，无法阻挡这些化学试剂与皮肤的接触，一旦试剂溅到身上，就会对皮肤造成严重的腐蚀伤害。", "opts": ["对", "错"], "ans": ["对"], "type": "判断"},
    {"q": "实验室的门应有可视窗并可锁闭，门锁及门的开启方向应不妨碍室内人员逃生。", "opts": ["对", "错"], "ans": ["对"], "type": "判断"},
    {"q": "动火作业时，动火点周围的可燃物如果未及时清除，动火作业中的明火、高温或火花易引燃周围可燃物。", "opts": ["对", "错"], "ans": ["对"], "type": "判断"},
    {"q": "作为企业安全管理人员，发现高处作业人员未佩戴安全带，应（  ）。", "opts": ["立即要求其停止作业并责令整改", "允许高处作业人员完成当前操作后再佩戴安全带", "作口头警告后允许其继续作业"], "ans": ["立即要求其停止作业并责令整改"], "type": "单选"},
    {"q": "在屋顶作业时间短，高度低，自己注意就可以，不用系安全带。", "opts": ["对", "错"], "ans": ["错"], "type": "判断"},
    {"q": "日常生活中，人们如果有临时用电需求可自行拉接电线，无需专业人员操作。", "opts": ["对", "错"], "ans": ["错"], "type": "判断"},
    {"q": "发现浴室玻璃门有裂缝时，以下做法正确的是（  ）。", "opts": ["忽视不管", "自行用胶水修补", "咨询专业人员更换浴室玻璃门"], "ans": ["咨询专业人员更换浴室玻璃门"], "type": "单选"},
    {"q": "用湿手触碰电器开关，易导致的危险后果是（  ）。", "opts": ["触电", "开关按键褪色", "开关破损"], "ans": ["触电"], "type": "单选"},
    {"q": "车辆违规停放占用消防通道，如果发生火灾，会阻碍消防车通行及人员疏散，延误灭火救援，加剧火灾人员伤亡与财产损失。", "opts": ["对", "错"], "ans": ["对"], "type": "判断"},
    {"q": "《起重机械安全规程 第1部分：总则》（GB/T 6067.1）中规定，（  ）在悬停载荷的下方停留或通过。", "opts": ["任何人不得", "起重机司机可以", "吊装工可以"], "ans": ["任何人不得"], "type": "单选"},
    {"q": "野外烧烤时，要选择远离有枯叶、干树枝等易燃物的烧烤场地。", "opts": ["对", "错"], "ans": ["对"], "type": "判断"},
    {"q": "从人身安全的角度出发，下列场所中最适合游泳的是（  ）。", "opts": ["无人管理的野外湖泊", "有救生员值守的正规泳池", "海边礁石区"], "ans": ["有救生员值守的正规泳池"], "type": "单选"},
    {"q": "下列选项中，能有效预防手机充电器起火的做法是（  ）。", "opts": ["使用后立即拔下充电器", "每周用酒精擦拭充电头", "在充电器旁放置水杯降温"], "ans": ["使用后立即拔下充电器"], "type": "单选"},
    {"q": "《高层民用建筑消防安全管理规定》中要求，禁止在高层民用建筑（  ）停放电动自行车或者为电动自行车充电。", "opts": ["公共门厅", "疏散走道", "楼梯间", "安全出口"], "ans": ["公共门厅", "疏散走道", "楼梯间", "安全出口"], "type": "多选"},
    {"q": "《消防法》中规定，住宅区的物业服务企业应当对管理区域内的共用消防设施进行维护管理，提供消防安全防范服务。", "opts": ["对", "错"], "ans": ["对"], "type": "判断"},
    {"q": "《消防法》中规定，对（  ）疏散通道、安全出口或者有其他妨碍安全疏散行为的单位，责令改正，处五千元以上五万元以下罚款。", "opts": ["占用", "堵塞", "封闭", "使用"], "ans": ["占用", "堵塞", "封闭"], "type": "多选"}
]


def init_built_in_bank():
    bank = load_bank()
    added = 0
    for item in BUILT_IN_BANK:
        key = q_key(item['q'])
        if key not in bank:
            bank[key] = {
                'q': item['q'],
                'opts': item['opts'],
                'answer': item['ans'],
                'type': item['type'],
                'scene': '内置',
                'level': '',
                'updated': '内置'
            }
            added += 1
    if added > 0:
        save_bank(bank)
    return bank