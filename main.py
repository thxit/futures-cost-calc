#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
期货品种生产成本计算器 v3.0
- 生产成本计算 & 盈亏对比
- 季节性规律 & 产销淡旺季（月度评分 + 供需详解）
"""

import tkinter as tk
from tkinter import ttk, messagebox

# ═══════════════════════════════════════════════════════════
#  品种数据
# ═══════════════════════════════════════════════════════════

class Variety:
    def __init__(self, name, code, category, inputs, formula,
                 description="", seasonal=None):
        self.name = name
        self.code = code
        self.category = category
        self.inputs = inputs
        self.formula = formula
        self.description = description
        self.seasonal = seasonal or {}

    def calculate(self, input_values):
        return self.formula(input_values)

# ═══════════════════════════════════════════════════════════
#  季节性构建工具
# ═══════════════════════════════════════════════════════════

MN = ["1月","2月","3月","4月","5月","6月","7月","8月","9月","10月","11月","12月"]

def _rng(a,b): return f"{MN[a-1]}-{MN[b-1]}"

# 月度评分: 2=强劲旺季  1=偏强  0=中性  -1=偏弱  -2=深度淡季
def _build_monthly(peak_ranges, offpeak_ranges, overrides=None):
    r = [0]*12
    for s,e,_ in peak_ranges:
        for i in range(s-1,e): r[i]=max(r[i],2)
    for s,e,_ in offpeak_ranges:
        for i in range(s-1,e):
            if r[i]==0: r[i]=-2
    if overrides:
        for m,v in overrides.items():
            if 1<=m<=12: r[m-1]=v
    return r

def _sea(peak=None, offpeak=None, monthly=None, produce="",
         supply="", demand="", key_periods=None, note=""):
    m = monthly or _build_monthly(peak or [], offpeak or [])
    return {
        "peak": peak or [], "offpeak": offpeak or [], "monthly": m,
        "produce": produce, "supply": supply, "demand": demand,
        "key_periods": key_periods or [], "note": note,
    }

# ═══════════════════════════════════════════════════════════
#  成本计算公式
# ═══════════════════════════════════════════════════════════

def _rebar(v):
    i=float(v.get("铁矿石",0)); c=float(v.get("焦炭",0))
    r=(1.6*i+0.5*c)*1.13; return {"生铁成本":round(r,0),"轧制费用":350,"生产成本":round(r+350,0)}
def _hrc(v):
    i=float(v.get("铁矿石",0)); c=float(v.get("焦炭",0))
    rb=(1.6*i+0.5*c)*1.13+350; return {"螺纹钢成本":round(rb,0),"热卷溢价":150,"生产成本":round(rb+150,0)}
def _coke(v):
    co=float(v.get("焦煤",0)); return {"焦煤成本":round(1.33*co,0),"加工费用":200,"生产成本":round(1.33*co+200,0)}
def _iron(v):
    i=float(v.get("普氏62%指数",0)); r=float(v.get("美元兑人民币",0))
    return {"到岸成本":round(i*r*0.1,0),"港杂费":130,"生产成本":round(i*r*0.1+130,0)}
def _meal(v):
    b=float(v.get("大豆",0)); o=float(v.get("豆油",0))
    return {"大豆成本":round(b,0),"豆油副产抵扣":round(0.185*o,0),"需大豆/吨":1.274,"生产成本":round((b-0.185*o)/0.785,0)}
def _oil(v):
    b=float(v.get("大豆",0)); m=float(v.get("豆粕",0))
    return {"大豆成本":round(b,0),"豆粕副产抵扣":round(0.785*m,0),"需大豆/吨":5.405,"生产成本":round((b-0.785*m)/0.185,0)}
def _bean(v):
    c=float(v.get("CBOT大豆",0)); p=float(v.get("升贴水",0)); r=float(v.get("美元兑人民币",0))
    return {"CBOT折算":round((c+p)*r*0.36744,0),"到岸费用":150,"生产成本":round((c+p)*r*0.36744+150,0)}
def _sugar(v):
    r=float(v.get("原糖期货",0)); e=float(v.get("美元兑人民币",0))
    return {"原糖到岸":round(r*1.03*e*0.022046,0),"加工费用":100,"生产成本":round(r*1.03*e*0.022046+100,0)}
def _pig(v):
    cn=float(v.get("玉米",0)); m=float(v.get("豆粕",0)); p=float(v.get("仔猪成本",0))
    f=(0.65*cn+0.2*m)*2.8; return {"仔猪成本":round(p,0),"饲料成本":round(f,0),"其他费用":350,"生产成本":round(p+f+350,0)}
def _egg(v):
    cn=float(v.get("玉米",0)); m=float(v.get("豆粕",0))
    f=(0.65*cn+0.22*m)*2.2; return {"饲料成本":round(f,0),"其他费用":200,"生产成本":round(f+200,0)}
def _corn(v):
    b=float(v.get("产地收购价",0)); t=float(v.get("运费",0))
    return {"产地成本":round(b,0),"运费":round(t,0),"到港成本":round(b+t,0)}
def _cotton(v):
    ic=float(v.get("ICE棉花",0)); p=float(v.get("升贴水",0)); r=float(v.get("美元兑人民币",0))
    c=(ic*0.4536+p)*r*1.01; return {"ICE到岸":round(c,0),"港杂费":300,"生产成本":round(c+300,0)}
def _pta(v):
    p=float(v.get("PX价格",0)); return {"PX原料":round(0.655*p,0),"加工费用":550,"生产成本":round(0.655*p+550,0)}
def _meth(v):
    c=float(v.get("煤炭",0)); return {"煤炭原料":round(1.8*c,0),"制造费用":800,"生产成本":round(1.8*c+800,0)}
def _pp(v):
    p=float(v.get("丙烯",0)); return {"丙烯原料":round(1.01*p,0),"加工费用":800,"生产成本":round(1.01*p+800,0)}
def _pvc(v):
    c=float(v.get("电石",0)); return {"电石原料":round(1.5*c,0),"加工费用":800,"生产成本":round(1.5*c+800,0)}
def _soda(v):
    s=float(v.get("原盐",0)); l=float(v.get("石灰石",0))
    return {"原盐成本":round(1.5*s,0),"石灰石成本":round(0.3*l,0),"加工费用":500,"生产成本":round(1.5*s+0.3*l+500,0)}
def _glass(v):
    s=float(v.get("纯碱",0)); q=float(v.get("石英砂",0))
    return {"纯碱成本":round(0.2*s,0),"石英砂成本":round(0.7*q,0),"加工费用":400,"生产成本":round(0.2*s+0.7*q+400,0)}
def _urea(v):
    c=float(v.get("煤炭",0)); return {"煤炭原料":round(1.5*c,0),"加工费用":600,"生产成本":round(1.5*c+600,0)}
def _alu(v):
    a=float(v.get("氧化铝",0)); p=float(v.get("电价(元/度)",0)); ec=0.14*10000*p
    return {"氧化铝成本":round(1.93*a,0),"电费成本":round(ec,0),"其他费用":3000,"生产成本":round(1.93*a+ec+3000,0)}
def _copper(v):
    l=float(v.get("LME铜",0)); r=float(v.get("美元兑人民币",0))
    return {"LME到岸":round(l*r*1.13,0),"港杂费":200,"生产成本":round(l*r*1.13+200,0)}
def _foil(v):
    o=float(v.get("原油",0)); return {"原油原料":round(o*0.85,0),"加工费用":200,"生产成本":round(o*0.85+200,0)}
def _ash(v):
    o=float(v.get("原油",0)); return {"原油原料":round(o*0.8,0),"加工费用":300,"生产成本":round(o*0.8+300,0)}
def _lpg(v):
    o=float(v.get("原油",0)); return {"原油原料":round(o*0.6,0),"加工费用":500,"生产成本":round(o*0.6+500,0)}

FORMULAS = {
    "螺纹钢":_rebar,"热轧卷板":_hrc,"焦炭":_coke,"铁矿石":_iron,
    "豆粕":_meal,"豆油":_oil,"进口大豆":_bean,"白糖":_sugar,
    "生猪":_pig,"鸡蛋":_egg,"玉米":_corn,"棉花":_cotton,
    "PTA":_pta,"甲醇":_meth,"聚丙烯":_pp,"PVC":_pvc,
    "纯碱":_soda,"玻璃":_glass,"尿素":_urea,
    "沪铝":_alu,"沪铜":_copper,
    "燃料油":_foil,"沥青":_ash,"液化石油气":_lpg,
}

# ═══════════════════════════════════════════════════════════
#  季节性数据（完整版）
# ═══════════════════════════════════════════════════════════

S = {}

S["螺纹钢"] = _sea(
    peak=[(3,5,"春季开工旺季，需求集中释放"),(9,11,"金九银十赶工期")],
    offpeak=[(1,2,"春节停工，需求冰点"),(6,8,"高温多雨，施工受限")],
    produce="高炉全年生产，限产集中在10月-次年3月（秋冬季）",
    supply="国内粗钢产量受环保限产影响大，秋冬季限产导致供应收缩；电炉钢受废钢价格和峰谷电价影响调节产量。",
    demand="房地产（约40%）+ 基建（约30%）+ 制造业（约30%）。春节后复工和雨季结束赶工是两个需求高峰。",
    key_periods=["正月十五后复工情况","两会后基建政策落地","雨季结束赶工期（9-10月）","秋冬采暖季限产（10月-次年3月）"],
    note="政策敏感型品种，房地产和基建的晴雨表。冬储行情（12-1月）和节后复工行情是两大交易主题。",
)
S["热轧卷板"] = _sea(
    peak=[(3,5,"制造业复工，旺季启动"),(9,11,"金九银十，汽车家电产销旺")],
    offpeak=[(1,2,"春节淡季"),(7,8,"汽车厂高温检修期")],
    produce="同螺纹钢，高炉全年生产",
    supply="与螺纹钢共用高炉产能，铁水流向可调节（螺纹利润高时减少热卷产量）。",
    demand="汽车（约25%）+ 家电（约15%）+ 机械（约20%）+ 出口（约20%）。季节性弱于螺纹钢，受出口订单影响大。",
    key_periods=["汽车产销数据（每月中旬）","出口退税政策","家电补贴政策"],
    note="工业板材，季节性弱于螺纹钢。关注汽车行业周期和出口订单变化，热卷-螺纹价差是重要指标。",
)
S["焦炭"] = _sea(
    peak=[(3,5,"钢厂复产补库"),(9,11,"秋冬限产预期+补库")],
    offpeak=[(1,2,"春节钢厂减产"),(7,8,"钢厂限产+焦化累库")],
    produce="焦化全年连续生产，环保限产为变量",
    supply="独立焦化厂为主，受环保限产影响极大（尤其山西、河北）。焦化利润长期偏低时自动减产。",
    demand="下游100%为钢厂，1吨铁水约需0.5吨焦炭。跟随钢铁产量波动。",
    key_periods=["环保限产政策（2+26城市）","焦化去产能","钢厂开工率"],
    note="产业链中间品，上下受挤，利润常被钢厂和煤矿两头压缩。环保限产是主要供给变量。",
)
S["铁矿石"] = _sea(
    peak=[(3,5,"钢厂复产补库"),(9,11,"节前补库+限产前抢运")],
    offpeak=[(1,2,"澳洲飓风季发货减量但需求也弱"),(6,8,"海外发运高峰+国内需求走弱")],
    monthly=_build_monthly([(3,5,"补库"),(9,11,"补库")],[(1,2,"双弱"),(6,8,"发运高峰")],{12:1}),
    produce="澳洲: 全年, 巴西: 11月-次年4月雨季影响发运",
    supply="澳洲（力拓/必和必拓/FMG）占60%进口，巴西（淡水河谷）占20%。澳洲飓风（1-3月）和巴西雨季（11-4月）影响发运。",
    demand="100%用于钢铁冶炼。1吨生铁约需1.6吨铁矿（62%品位）。需求完全跟随钢厂开工。",
    key_periods=["澳洲巴西发运量（每周一）","钢厂开工率","港口库存变化","钢铁限产政策"],
    note="四大矿山高度寡头垄断，供应端有较强的控制力。但需求端跟随国内钢铁产量，是典型的供需双强格局。",
)

S["豆粕"] = _sea(
    peak=[(4,6,"南美大豆到港高峰+养殖补栏"),(9,12,"生猪补栏+水产旺季")],
    offpeak=[(1,3,"南美上市前供应偏紧"),(7,8,"高温影响养殖增速")],
    produce="跟随进口大豆到港节奏：巴西大豆3-7月集中到港，美豆10-12月到港",
    supply="压榨厂开机率决定供应，利润好时高开机。大豆到港量是领先指标。",
    demand="饲料（约95%）：猪料50%+禽料32%+水产8%。猪周期是核心驱动。",
    key_periods=["USDA月度供需报告（每月9-12日）","季度库存报告","生猪存栏数据","大豆到港量"],
    note="跟随大豆进口成本，压榨利润波动大。猪周期是长期核心驱动，USDA报告是短期爆发点。",
)
S["豆油"] = _sea(
    peak=[(9,12,"双节备货+冬季消费旺季")],
    offpeak=[(1,3,"节后消费回落"),(6,8,"夏季消费淡季")],
    monthly=_build_monthly([(9,12,"备货旺季")],[(1,3,"节后淡季"),(6,8,"淡季")],{11:2,12:2}),
    produce="随大豆压榨，全年生产",
    supply="大豆压榨的副产品，与豆粕联产（1吨大豆产0.185吨豆油+0.785吨豆粕）。豆粕需求旺盛时豆油供应被动增加。",
    demand="食用（约70%）+ 工业（约15%）+ 饲料（约10%）。节前备货效应明显。",
    key_periods=["双节前1-2个月备货","棕榈油价格联动","生物柴油政策"],
    note="与豆粕存在跷跷板效应：豆粕需求好→开机高→豆油被动增产→豆油承压。",
)
S["进口大豆"] = _sea(
    peak=[(5,7,"巴西大豆到港高峰"),(10,12,"美豆到港高峰")],
    offpeak=[(2,4,"南美尚未大量上市，国内库存偏低")],
    produce="巴西: 2-5月收获, 美国: 9-12月收获, 阿根廷: 4-6月收获",
    supply="全球大豆看南美（巴西+阿根廷≈50%）和美国（≈30%）。巴西大豆出口季为2-7月，美豆为10-次年1月。",
    demand="中国进口占全球60%以上，主要用于压榨（85%为豆粕）和食用（15%）。",
    key_periods=["USDA月度供需报告","巴西/阿根廷天气（10月-次年3月种植期）","美豆种植面积（6月）","中美贸易关系"],
    note="国际定价品种，受CBOT、汇率、海运费三重影响。天气升水是常见的交易题材。",
)
S["白糖"] = _sea(
    peak=[(4,6,"夏季冷饮消费启动"),(9,12,"中秋+国庆+春节三重备货")],
    offpeak=[(1,3,"压榨高峰供应充足"),(7,8,"纯消费但无节日驱动")],
    produce="国内: 11月-次年4月（南方甘蔗压榨季）",
    supply="国内产量约1000万吨/年（广西占60%），进口约500万吨/年。甘蔗宿根三年，种植面积相对稳定。",
    demand="食用（约60%）+ 饮料（约20%）+ 食品加工（约15%）。春节前为年度消费最旺季。",
    key_periods=["开榨进度（11月起）","国储糖拍卖/收储","印度/巴西产量","进口关税政策"],
    note="政策市特征明显（进口关税+国储调控）。压榨季供应充裕价格承压，节前备货推升价格。",
)
S["生猪"] = _sea(
    peak=[(8,9,"开学+贴秋膘+中秋备货"),(12,1,"腌腊+春节旺季")],
    offpeak=[(3,5,"节后消费回落，年度价格低点")],
    monthly=_build_monthly([(8,9,"开学备货"),(12,1,"春节")],[(3,5,"节后淡季")],{6:-1,7:-1,10:1,11:1}),
    produce="全年生产，但季节性出栏有差异",
    supply="能繁母猪存栏决定了10个月后的出栏量。北方冬季仔猪成活率低导致8-9月出栏偏少。",
    demand="鲜肉消费为主（约85%），冻品库存调节。冬季消费旺季（腌腊+火锅+春节）。",
    key_periods=["能繁母猪存栏（每月）","仔猪价格（领先6个月指标）","冻品库存","非瘟/疫病"],
    note="产能周期（3-4年）远大于季节性影响，季节性节奏可靠但幅度受周期位置制约。",
)
S["鸡蛋"] = _sea(
    peak=[(8,9,"开学+中秋备货，年度高点"),(12,1,"春节备货")],
    offpeak=[(2,4,"节后需求淡季"),(6,7,"梅雨季不易储存")],
    produce="全年生产，春季补栏决定8个月后在产蛋鸡存栏",
    supply="在产蛋鸡存栏是核心供应指标。春季（3-5月）补栏高峰期，8个月后开产。夏季高温产蛋率下降5-10%。",
    demand="家庭消费+食品加工。中秋月饼和国庆宴席是年度最强驱动。",
    key_periods=["在产蛋鸡存栏（每月）","淘汰鸡价格","饲料成本","中秋节前1-2个月见顶"],
    note="中秋节前为传统年度高点的确定性较强。梅雨季和春节后为两波低点。",
)
S["玉米"] = _sea(
    peak=[(12,2,"新粮上市后贸易商屯粮"),(5,7,"余粮减少，青黄不接")],
    offpeak=[(10,11,"新粮集中上市，供应压力最大")],
    produce="华北: 9-10月收获, 东北: 10-11月收获",
    supply="国内产量约2.7亿吨/年（东北占40%+，华北占30%+）。种植面积受政策调控。",
    demand="饲料（约65%）+ 深加工（约25%）+ 食用（约10%）。生猪存栏量是主要需求驱动。",
    key_periods=["临储/国储拍卖","新作种植面积","产区天气（6-8月关键生长期）","进口替代（高粱/大麦）"],
    note="收获期价格承压，次年5月后余粮减少价格偏强。国家调控力度大（进口配额+储备）。",
)
S["棉花"] = _sea(
    peak=[(3,5,"纺织旺季+春播天气炒作"),(9,12,"秋冬订单+收储")],
    offpeak=[(1,2,"春节前后停工"),(7,8,"纺织淡季+高温")],
    produce="新疆: 9-11月采摘, 内地: 8-10月",
    supply="新疆占国内产量约90%。目标价格补贴政策保障种植面积。进口配额（89.4万吨关税内+滑准税）。",
    demand="纺织服装出口+内需消费。秋冬订单（9-12月）为传统旺季，春夏订单（3-5月）次之。",
    key_periods=["USDA供需报告","新疆目标价格","纺企开工率","出口订单（领先指标）"],
    note="新棉上市前供应偏紧（8-9月青黄不接），收割期（10-12月）供应压力大。",
)

S["PTA"] = _sea(
    peak=[(3,5,"金三银四聚酯旺季"),(9,12,"秋冬纺织旺季")],
    offpeak=[(1,2,"春节下游放假"),(6,8,"聚酯淡季+高温限电")],
    produce="全年生产，4-5月为集中检修季",
    supply="国内产能约7000万吨/年，集中检修期（4-5月）供应明显收缩。开工率视加工费而定。",
    demand="100%用于聚酯生产，聚酯再用于纺织。终端纺织服装消费驱动。",
    key_periods=["PX检修季（4-5月）","聚酯开工率","纺织终端订单","PTA加工费"],
    note="产业链利润分配不均，PX拿走大头，PTA加工费长期偏低。检修季是唯一主动减产的窗口。",
)
S["甲醇"] = _sea(
    peak=[(3,4,"春季检修供应减少"),(9,10,"冬季限气预期")],
    offpeak=[(1,2,"需求淡季"),(6,8,"MTO检修需求回落")],
    produce="煤制（约75%）+ 天然气制（约15%）+ 焦炉气（约10%）",
    supply="国内产能约1亿吨/年，煤制为主。冬季天然气限气影响西南天然气制甲醇。进口（伊朗为主）占约15%。",
    demand="MTO/CTO（约50%）+ 传统下游（甲醛/醋酸等约35%）+ 燃料（约15%）。MTO开工率是核心变量。",
    key_periods=["天然气限气政策（冬）","MTO开工率","进口到港量","煤炭价格"],
    note="冬季天然气限气导致供应收缩为多头题材，夏季MTO检修需求回落为空头题材。",
)
S["聚丙烯"] = _sea(
    peak=[(3,5,"春季检修+金三银四"),(9,11,"金九银十")],
    offpeak=[(1,2,"春节下游停工"),(6,8,"塑编淡季+高温")],
    produce="全年生产，3-5月集中检修",
    supply="油制（约50%）+ 煤制（约25%）+ PDH（约25%）。产能持续扩张，供需格局偏宽松。",
    demand="塑编/包装（约40%）+ 汽车家电（约20%）+ 管材（约15%）+ 其他。",
    key_periods=["检修季（3-5月供应收缩）","新装置投产","原油/丙烷价格"],
    note="产能扩张周期中，检修季是仅有阶段性供需改善窗口。长期价格重心受原油影响。",
)
S["PVC"] = _sea(
    peak=[(3,5,"春季开工+房地产施工"),(9,11,"金九银十赶工期")],
    offpeak=[(1,2,"春节停工"),(6,8,"高温+雨季施工减少")],
    produce="全年生产，秋季检修",
    supply="电石法（约80%）+ 乙烯法（约20%）。电石法高耗能，环保限电影响大。",
    demand="管材型材（约60%）+ 软制品（约25%）+ 其他（约15%）。房地产施工为核心驱动。",
    key_periods=["房地产开工/竣工数据","环保限电（夏/冬）","出口窗口（印度/东南亚）"],
    note="电石法成本高且高耗能，环保政策影响供应端。房地产竣工回暖是长期需求驱动。",
)
S["纯碱"] = _sea(
    peak=[(3,5,"浮法玻璃复产+光伏投产"),(9,11,"玻璃旺季拉动")],
    offpeak=[(1,2,"春节淡季"),(7,8,"玻璃冷修增加需求减少")],
    produce="全年生产，6-8月为检修季",
    supply="氨碱法（约50%）+ 联碱法（约45%）+ 天然碱（约5%）。新增产能集中释放（远兴能源等）。",
    demand="浮法玻璃（约45%）+ 光伏玻璃（约25%）+ 其他（洗涤/食品等）。光伏玻璃是新增量。",
    key_periods=["光伏玻璃投产进度","浮法玻璃冷修/复产","房地产竣工","新增产能投放"],
    note="双轮驱动：传统浮法玻璃看房地产竣工，光伏玻璃看碳中和政策下的产能扩张。",
)
S["玻璃"] = _sea(
    peak=[(3,5,"春季开工"),(9,11,"赶工期+房地产竣工")],
    offpeak=[(1,2,"春节停工"),(6,8,"高温多雨施工淡季")],
    produce="全年连续生产，停产冷修成本极高",
    supply="熔窑连续生产（8-10年寿命），冷修/复产成本极高。一旦点火不能轻易停产。",
    demand="房地产竣工（约75%）+ 汽车（约10%）+ 出口（约5%）。房地产竣工周期是核心驱动。",
    key_periods=["房地产竣工数据","纯碱价格","生产线冷修/点火"],
    note="供应刚性（连续生产），需求跟随房地产竣工。冷修周期和竣工周期共振时波动最大。",
)
S["尿素"] = _sea(
    peak=[(3,5,"春耕用肥旺季"),(9,10,"秋播备肥旺季")],
    offpeak=[(1,2,"春节"),(6,8,"农业间歇期"),(11,12,"淡季")],
    produce="全年生产，气头限气冬季减产",
    supply="煤制（约75%）+ 天然气制（约25%）。冬季天然气限气影响气头产量。",
    demand="农业直接施用（约60%）+ 复合肥（约20%）+ 工业（约15%）。春耕和秋播为刚性需求。",
    key_periods=["春耕备肥（2-4月）","印度招标（影响出口预期）","煤炭价格","气头限气"],
    note="农业季节性最强品种之一。春耕（3-5月）和秋播（9-10月）为需求高峰，时间确定性高。",
)

S["沪铝"] = _sea(
    peak=[(3,5,"金三银四消费旺季"),(9,11,"金九银十消费旺季")],
    offpeak=[(1,2,"春节下游停工"),(6,8,"消费淡季+夏季限电")],
    produce="全年生产，云南11月-次年5月枯水期限产",
    supply="云南水电铝占全国约30%，枯水期（11-5月）限产成为常态。其余地区相对稳定。",
    demand="建筑（约30%）+ 交通（约20%）+ 电力电子（约15%）+ 包装（约10%）。",
    key_periods=["云南枯水期限产（冬春）","社会库存变化（每周四）","加工企业开工率"],
    note="供应端受云南水电影响大（限产-复产的周期性），消费端跟随加工企业开工率。",
)
S["沪铜"] = _sea(
    peak=[(3,5,"金三银四旺季"),(9,11,"金九银十旺季")],
    offpeak=[(1,2,"春节淡季"),(6,8,"消费淡季")],
    monthly=_build_monthly([(3,5,"旺季"),(9,11,"旺季")],[(1,2,"淡季")],{6:-1,7:-1,8:-1,12:0}),
    produce="全年生产，铜精矿供应偏紧",
    supply="全球铜精矿供应偏紧，中国冶炼产能占全球40%以上。TC/RC加工费反映矿端松紧。",
    demand="电力（约45%）+ 家电（约15%）+ 交通（约10%）+ 建筑（约10%）。新能源（电动车+光伏）是增量。",
    key_periods=["LME库存变化","中国进口数据","美元指数","新能源政策"],
    note="'铜博士'，对宏观经济高度敏感。新能源转型为长期需求故事，季节性相对其他品种偏弱。",
)

S["燃料油"] = _sea(
    peak=[(6,9,"夏季发电需求+北半球航运旺季")],
    offpeak=[(1,3,"航运淡季")],
    monthly=_build_monthly([(6,9,"旺季")],[(1,3,"淡季")],{10:1,11:0,12:0,4:0,5:1}),
    produce="原油常减压蒸馏的副产品",
    supply="炼厂副产物，产量取决于炼厂开工率和原油加工量。高低硫价差受IMO法规影响。",
    demand="船燃（约50%）+ 发电（约20%）+ 炼厂原料（约15%）。航运BDI指数是领先指标。",
    key_periods=["IMO限硫令执行","BDI航运指数","东西方套利窗口"],
    note="高低硫价差是核心交易指标，夏季发电和航运旺季为季节性支撑。",
)
S["沥青"] = _sea(
    peak=[(4,6,"春季道路施工+冬储后补库"),(9,11,"赶工期")],
    offpeak=[(1,2,"低温无法施工"),(7,8,"高温+雨季（南方）")],
    produce="原油减压蒸馏的副产物，稀释沥青进口补充",
    supply="炼厂副产物，产量与原油加工量相关。稀释沥青进口是重要补充（委内瑞拉/马来西亚）。",
    demand="道路建设（约80%）+ 防水材料（约10%）+ 其他。道路施工受气温和降水制约极大。",
    key_periods=["冬储（12-1月）","道路施工项目进度","原油价格","稀释沥青进口政策"],
    note="道路施工季节性极强：一年两波行情（春季开工+秋季赶工），且受天气影响确定性高。",
)
S["液化石油气"] = _sea(
    peak=[(10,12,"冬季取暖需求旺盛"),(1,2,"春节前备货")],
    offpeak=[(4,6,"气温回升，民用需求大减")],
    produce="炼厂副产+伴生气，夏季为供应高峰（炼厂检修完毕）",
    supply="炼厂副产（约60%）+ 伴生气（约40%）。PDH装置投产增加化工需求。",
    demand="民用燃料（约50%）+ 化工（约30%，PDH制丙烯）+ 工业燃料（约15%）。冬季取暖为刚需。",
    key_periods=["CP价格（沙特月度报价）","PDH装置开工率","进口到港量","气温变化"],
    note="季节性最明显的品种之一：冬季取暖刚需 vs 夏季需求低谷，价差波动大。",
)

# ═══════════════════════════════════════════════════════════
#  品种注册表（紧凑格式）
# ═══════════════════════════════════════════════════════════

CATEGORIES = ["黑色系 (Ferrous)","农产品 (Agriculture)","化工品 (Chemicals)","有色金属 (Metals)","能源化工 (Energy)"]

def V(name, code, cat, inputs, desc):
    return Variety(name, code, cat, inputs, FORMULAS[name], desc, seasonal=S.get(name))

VARIETY_DATA = [
    V("螺纹钢","RB","黑色系 (Ferrous)",[("铁矿石","800","元/吨","62%"),("焦炭","2200","元/吨","准一级")],
      "成本 = (1.6×铁矿+0.5×焦炭)×1.13+350"),
    V("热轧卷板","HC","黑色系 (Ferrous)",[("铁矿石","800","元/吨","62%"),("焦炭","2200","元/吨","准一级")],
      "成本 = 螺纹钢成本+150"),
    V("焦炭","J","黑色系 (Ferrous)",[("焦煤","1600","元/吨","主焦煤")],"成本 = 1.33×焦煤+200"),
    V("铁矿石","I","黑色系 (Ferrous)",[("普氏62%指数","108","美元/吨",""),("美元兑人民币","7.25","","")],
      "进口成本 = 普氏指数×汇率×0.1+130"),

    V("豆粕","M","农产品 (Agriculture)",[("大豆","4200","元/吨","到港价"),("豆油","7800","元/吨","")],
      "成本 = (大豆-0.185×豆油)/0.785"),
    V("豆油","Y","农产品 (Agriculture)",[("大豆","4200","元/吨","到港价"),("豆粕","3200","元/吨","")],
      "成本 = (大豆-0.785×豆粕)/0.185"),
    V("进口大豆","A","农产品 (Agriculture)",[("CBOT大豆","1150","美分/蒲",""),("升贴水","100","美分/蒲",""),("美元兑人民币","7.25","","")],
      "到港成本 = (CBOT+升贴水)×汇率×0.36744+150"),
    V("白糖","SR","农产品 (Agriculture)",[("原糖期货","19","美分/磅",""),("美元兑人民币","7.25","","")],
      "进口成本 = 原糖×1.03×汇率×0.022046+100"),
    V("生猪","LH","农产品 (Agriculture)",[("玉米","2400","元/吨",""),("豆粕","3200","元/吨",""),("仔猪成本","700","元/头","15kg")],
      "成本 = 仔猪+(0.65×玉米+0.2×豆粕)×2.8+350"),
    V("鸡蛋","JD","农产品 (Agriculture)",[("玉米","2400","元/吨",""),("豆粕","3200","元/吨","")],
      "成本 = (0.65×玉米+0.22×豆粕)×2.2+200"),
    V("玉米","C","农产品 (Agriculture)",[("产地收购价","2200","元/吨",""),("运费","150","元/吨","到港")],
      "到港成本 = 产地收购价+运费"),
    V("棉花","CF","农产品 (Agriculture)",[("ICE棉花","75","美分/磅",""),("升贴水","5","美分/磅",""),("美元兑人民币","7.25","","")],
      "进口成本 = (ICE×0.4536+升贴水)×汇率×1.01+300"),

    V("PTA","TA","化工品 (Chemicals)",[("PX价格","900","美元/吨","CFR中国")],"成本 = 0.655×PX+550"),
    V("甲醇","MA","化工品 (Chemicals)",[("煤炭","700","元/吨","动力煤")],"煤制成本 = 1.8×煤炭+800"),
    V("聚丙烯","PP","化工品 (Chemicals)",[("丙烯","7000","元/吨","")],"油制成本 = 1.01×丙烯+800"),
    V("PVC","V","化工品 (Chemicals)",[("电石","3000","元/吨","")],"电石法成本 = 1.5×电石+800"),
    V("纯碱","SA","化工品 (Chemicals)",[("原盐","350","元/吨",""),("石灰石","100","元/吨","")],"成本 = 1.5×原盐+0.3×石灰石+500"),
    V("玻璃","FG","化工品 (Chemicals)",[("纯碱","2000","元/吨",""),("石英砂","300","元/吨","")],"成本 = 0.2×纯碱+0.7×石英砂+400"),
    V("尿素","UR","化工品 (Chemicals)",[("煤炭","700","元/吨","动力煤")],"煤制成本 = 1.5×煤炭+600"),

    V("沪铝","AL","有色金属 (Metals)",[("氧化铝","3200","元/吨",""),("电价(元/度)","0.45","元/度","工业用电")],
      "成本 = 1.93×氧化铝+14000度×电价+3000"),
    V("沪铜","CU","有色金属 (Metals)",[("LME铜","9500","美元/吨",""),("美元兑人民币","7.25","","")],
      "进口成本 = LME铜×汇率×1.13+200"),

    V("燃料油","FU","能源化工 (Energy)",[("原油","5500","元/吨","SC期货")],"成本 = 原油×0.85+200"),
    V("沥青","BU","能源化工 (Energy)",[("原油","5500","元/吨","SC期货")],"成本 = 原油×0.8+300"),
    V("液化石油气","PG","能源化工 (Energy)",[("原油","5500","元/吨","SC期货")],"成本 = 原油×0.6+500"),
]

# ═══════════════════════════════════════════════════════════
#  GUI
# ═══════════════════════════════════════════════════════════

COLORS = {
    "bg":"#f0f2f5","card":"#ffffff","accent":"#2563eb",
    "profit":"#16a34a","loss":"#dc2626","border":"#d1d5db",
    "text":"#1f2937","secondary":"#6b7280","sidebar":"#f8fafc",
    "sel_bg":"#dbeafe","sel_fg":"#1e40af","hover":"#eff6ff",
    "bar_bg":"#374151",
    # 月度颜色
    "m2":"#22c55e","m1":"#86efac","m0":"#d1d5db","_m1":"#fca5a5","_m2":"#ef4444",
}

MONTH_LABELS = ["1月","2月","3月","4月","5月","6月","7月","8月","9月","10月","11月","12月"]

def _month_rating_color(r):
    if r>=2: return COLORS["m2"]
    if r==1: return COLORS["m1"]
    if r==0: return COLORS["m0"]
    if r==-1: return COLORS["_m1"]
    return COLORS["_m2"]

def _month_label_short(r):
    if r>=1: return "旺"
    if r==0: return "中"
    return "淡"

class FuturesCostApp:
    def __init__(self, root):
        self.root = root
        self.root.title("期货品种生产成本计算器 v3.0")
        self.root.geometry("1150x780")
        self.root.minsize(1000, 680)
        self.root.configure(bg=COLORS["bg"])

        self.varieties_by_cat = {}
        for v in VARIETY_DATA:
            self.varieties_by_cat.setdefault(v.category, []).append(v)
        self.current_variety = None
        self.input_widgets = {}
        self._build_ui()

    def _build_ui(self):
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_main()
        self._build_statusbar()

    def _build_sidebar(self):
        sb = tk.Frame(self.root, bg=COLORS["sidebar"], width=200,
                      highlightbackground=COLORS["border"], highlightthickness=1)
        sb.grid(row=0, column=0, sticky="ns", padx=(0,1))
        sb.grid_propagate(False)

        tk.Label(sb, text="品种列表", font=("Microsoft YaHei", 13, "bold"),
                 bg=COLORS["sidebar"], fg=COLORS["text"], pady=14).pack(fill="x")

        self._cat_btns = []
        for cat in CATEGORIES:
            tk.Label(sb, text=cat, font=("Microsoft YaHei", 9, "bold"),
                     bg="#e5e7eb", fg=COLORS["text"], anchor="w",
                     padx=12, pady=3).pack(fill="x")
            for v in self.varieties_by_cat.get(cat, []):
                btn = tk.Label(sb, text=f"  {v.name} ({v.code})",
                               font=("Microsoft YaHei", 10),
                               bg=COLORS["sidebar"], fg=COLORS["text"],
                               anchor="w", padx=22, pady=2, cursor="hand2")
                btn.pack(fill="x")
                btn.bind("<Button-1>", lambda e, var=v: self._select(var))
                btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=COLORS["hover"]))
                btn.bind("<Leave>", lambda e, b=btn: b.configure(
                    bg=COLORS["sel_bg"] if self.current_variety and b.cget("text")==f"  {self.current_variety.name} ({self.current_variety.code})" else COLORS["sidebar"]))
                self._cat_btns.append((btn, v))

    def _build_main(self):
        main = tk.Frame(self.root, bg=COLORS["bg"])
        main.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(1, weight=1)

        # 顶栏
        hf = tk.Frame(main, bg=COLORS["bg"])
        hf.grid(row=0, column=0, sticky="ew", pady=(0,6))
        self.title_lbl = tk.Label(hf, text="请从左侧选择一个品种",
                                   font=("Microsoft YaHei", 16, "bold"),
                                   bg=COLORS["bg"], fg=COLORS["text"])
        self.title_lbl.pack(anchor="w")
        self.desc_lbl = tk.Label(hf, text="", font=("Microsoft YaHei", 9),
                                  bg=COLORS["bg"], fg=COLORS["secondary"],
                                  wraplength=850, justify="left")
        self.desc_lbl.pack(anchor="w")

        # 笔记簿
        self.nb = ttk.Notebook(main)
        self.nb.grid(row=1, column=0, sticky="nsew")

        # Tab 1: 成本分析
        ct = tk.Frame(self.nb, bg=COLORS["bg"])
        self.nb.add(ct, text="  成本分析  ")
        ct.columnconfigure(0, weight=1); ct.columnconfigure(1, weight=1)
        ct.rowconfigure(0, weight=1)

        ic = tk.Frame(ct, bg=COLORS["card"],
                      highlightbackground=COLORS["border"], highlightthickness=1,
                      padx=14, pady=10)
        ic.grid(row=0, column=0, sticky="nsew", padx=(0,6))
        tk.Label(ic, text="原料价格输入", font=("Microsoft YaHei", 12, "bold"),
                 bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w")
        self.input_c = tk.Frame(ic, bg=COLORS["card"])
        self.input_c.pack(fill="both", expand=True, pady=(6,0))
        self.calc_btn = ttk.Button(ic, text="📊 计算", command=self._calc, state="disabled")
        self.calc_btn.pack(pady=8)

        rc = tk.Frame(ct, bg=COLORS["card"],
                      highlightbackground=COLORS["border"], highlightthickness=1,
                      padx=14, pady=10)
        rc.grid(row=0, column=1, sticky="nsew", padx=(6,0))
        tk.Label(rc, text="成本分析结果", font=("Microsoft YaHei", 12, "bold"),
                 bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w")
        self.res_c = tk.Frame(rc, bg=COLORS["card"])
        self.res_c.pack(fill="both", expand=True, pady=(6,0))
        self._show_res_placeholder()

        # Tab 2: 季节性
        self.st = tk.Frame(self.nb, bg=COLORS["bg"])
        self.nb.add(self.st, text="  季节性规律  ")
        self._show_sea_placeholder()

    def _build_statusbar(self):
        bar = tk.Frame(self.root, bg=COLORS["bar_bg"])
        bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.sv = tk.StringVar(value="就绪  |  选择品种 → 输入原料价格 → 计算成本  |  查看季节性规律")
        tk.Label(bar, textvariable=self.sv, font=("Microsoft YaHei", 9),
                 bg=COLORS["bar_bg"], fg="#d1d5db", anchor="w",
                 padx=10, pady=3).pack(side="left")
        tk.Label(bar, text="v3.0", font=("Microsoft YaHei", 8),
                 bg=COLORS["bar_bg"], fg="#9ca3af", padx=10).pack(side="right")

    # ─── 占位 ─────────────────────────────────────

    def _show_res_placeholder(self):
        for w in self.res_c.winfo_children(): w.destroy()
        tk.Label(self.res_c, text="← 输入原料价格后\n点击「计算」按钮",
                 font=("Microsoft YaHei",11), bg=COLORS["card"],
                 fg=COLORS["secondary"], justify="center").pack(expand=True)

    def _show_sea_placeholder(self):
        for w in self.st.winfo_children(): w.destroy()
        tk.Label(self.st, text="← 从左侧选择品种查看季节性规律",
                 font=("Microsoft YaHei",11), bg=COLORS["bg"],
                 fg=COLORS["secondary"], justify="center").pack(expand=True)

    # ─── 品种选择 ─────────────────────────────────

    def _select(self, variety):
        self.current_variety = variety
        for btn, v in self._cat_btns:
            btn.configure(bg=COLORS["sel_bg"] if v is variety else COLORS["sidebar"],
                          fg=COLORS["sel_fg"] if v is variety else COLORS["text"])
        self.title_lbl.configure(text=f"{variety.name} ({variety.code})")
        self.desc_lbl.configure(text=variety.description)
        self._rebuild_inputs(variety)
        self.calc_btn.configure(state="normal")
        self._show_res_placeholder()
        self._build_seasonal(variety)
        self.nb.select(0)
        self.sv.set(f"当前: {variety.name} ({variety.code})")

    def _rebuild_inputs(self, variety):
        for w in self.input_c.winfo_children(): w.destroy()
        self.input_widgets.clear()
        for name, default, unit, hint in variety.inputs:
            row = tk.Frame(self.input_c, bg=COLORS["card"])
            row.pack(fill="x", pady=3)
            txt = f"{name} ({unit})" if unit else name
            tk.Label(row, text=txt, font=("Microsoft YaHei", 10),
                     bg=COLORS["card"], fg=COLORS["text"],
                     width=20, anchor="w").pack(side="left")
            e = ttk.Entry(row, font=("Consolas", 11), width=14)
            e.insert(0, str(default))
            e.pack(side="left", padx=4)
            self.input_widgets[name] = e
            if hint:
                tk.Label(row, text=hint, font=("Microsoft YaHei", 8),
                         bg=COLORS["card"], fg=COLORS["secondary"]).pack(side="left",padx=2)

    # ─── 季节性 Tab ─────────────────────────────

    def _build_seasonal(self, variety):
        """构建季节性规律标签页的全部内容"""
        for w in self.st.winfo_children(): w.destroy()
        sea = variety.seasonal
        if not sea:
            tk.Label(self.st, text="暂无季节性数据", font=("Microsoft YaHei",11),
                     bg=COLORS["bg"], fg=COLORS["secondary"]).pack(expand=True)
            return

        canvas = tk.Canvas(self.st, bg=COLORS["bg"], highlightthickness=0)
        sb = ttk.Scrollbar(self.st, orient="vertical", command=canvas.yview)
        sf = tk.Frame(canvas, bg=COLORS["bg"])
        sf.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0), window=sf, anchor="nw", width=canvas.winfo_width())
        canvas.configure(yscrollcommand=sb.set)

        def _resize(e):
            canvas.itemconfig(1, width=e.width-20)
        canvas.bind("<Configure>", _resize)

        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        def _mw(e):
            canvas.yview_scroll(-1*(e.delta//120), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _mw))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # ═══════════════ 年度周期条 ═══════════════
        bar_frame = tk.Frame(sf, bg=COLORS["card"],
                             highlightbackground=COLORS["border"], highlightthickness=1,
                             padx=12, pady=8)
        bar_frame.pack(fill="x", pady=(0,6), padx=2)

        tk.Label(bar_frame, text="📅 年度季节性周期", font=("Microsoft YaHei", 11, "bold"),
                 bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w", pady=(0,6))

        # 12个月彩色条
        months = sea.get("monthly", [0]*12)
        bar_row = tk.Frame(bar_frame, bg=COLORS["card"])
        bar_row.pack(fill="x")

        for i, rating in enumerate(months):
            color = _month_rating_color(rating)
            short = _month_label_short(rating)
            cell = tk.Frame(bar_row, bg=color, width=62, height=48,
                            highlightbackground="white", highlightthickness=1)
            cell.pack(side="left", fill="x", expand=True)
            cell.pack_propagate(False)
            tk.Label(cell, text=MONTH_LABELS[i], font=("Microsoft YaHei", 8),
                     bg=color, fg="white" if abs(rating)>=2 else COLORS["text"]).pack(anchor="center")
            tk.Label(cell, text={2:"🔥旺季",1:"📈偏强",0:"➖中性",-1:"📉偏弱",-2:"💧淡季"}.get(rating,""),
                     font=("Microsoft YaHei", 7),
                     bg=color, fg="white" if abs(rating)>=2 else COLORS["text"]).pack(anchor="center")

        # 图例
        leg = tk.Frame(bar_row, bg=COLORS["card"])
        leg.pack(side="left", padx=8)
        for r, lbl in [(2,"🔥旺季"),(1,"偏强"),(0,"中性"),(-1,"偏弱"),(-2,"💧淡季")]:
            f = tk.Frame(leg, bg=COLORS["card"])
            f.pack(anchor="w", pady=1)
            c = _month_rating_color(r)
            tk.Canvas(f, bg=c, width=10, height=10, highlightthickness=0).pack(side="left",padx=2)
            tk.Label(f, text=lbl, font=("Microsoft YaHei", 8),
                     bg=COLORS["card"], fg=COLORS["secondary"]).pack(side="left")

        # ═══════════════ 供应 & 需求 ═══════════════
        sd_frame = tk.Frame(sf, bg=COLORS["bg"])
        sd_frame.pack(fill="x", pady=4, padx=2)

        # 供应
        if sea.get("supply"):
            sc = tk.Frame(sd_frame, bg="#fffbeb",
                          highlightbackground=COLORS["border"], highlightthickness=1,
                          padx=12, pady=8)
            sc.pack(side="left", fill="x", expand=True, padx=(0,3))
            tk.Label(sc, text="🏭 供应端季节性", font=("Microsoft YaHei", 10, "bold"),
                     bg="#fffbeb", fg="#92400e").pack(anchor="w")
            tk.Label(sc, text=sea["supply"], font=("Microsoft YaHei", 9), wraplength=480,
                     bg="#fffbeb", fg=COLORS["text"], justify="left").pack(anchor="w", pady=2)

        # 需求
        if sea.get("demand"):
            dc = tk.Frame(sd_frame, bg="#eff6ff",
                          highlightbackground=COLORS["border"], highlightthickness=1,
                          padx=12, pady=8)
            dc.pack(side="left", fill="x", expand=True, padx=(3,0))
            tk.Label(dc, text="🛒 需求端季节性", font=("Microsoft YaHei", 10, "bold"),
                     bg="#eff6ff", fg="#1e40af").pack(anchor="w")
            tk.Label(dc, text=sea["demand"], font=("Microsoft YaHei", 9), wraplength=480,
                     bg="#eff6ff", fg=COLORS["text"], justify="left").pack(anchor="w", pady=2)

        # ═══════════════ 旺季 & 淡季 ═══════════════
        po_frame = tk.Frame(sf, bg=COLORS["bg"])
        po_frame.pack(fill="x", pady=4, padx=2)

        if sea.get("peak"):
            pc = tk.Frame(po_frame, bg="#f0fdf4",
                          highlightbackground=COLORS["border"], highlightthickness=1,
                          padx=12, pady=8)
            pc.pack(side="left", fill="x", expand=True, padx=(0,3))
            tk.Label(pc, text="📈 需求旺季（价格上涨概率大）", font=("Microsoft YaHei", 10, "bold"),
                     bg="#f0fdf4", fg="#166534").pack(anchor="w")
            for sm, em, note in sea["peak"]:
                r = tk.Frame(pc, bg="#dcfce7", padx=8, pady=3)
                r.pack(fill="x", pady=2)
                tk.Label(r, text=_rng(sm,em), font=("Consolas", 11, "bold"),
                         bg="#dcfce7", fg="#166534", width=12).pack(side="left")
                tk.Label(r, text=note, font=("Microsoft YaHei", 9), wraplength=400,
                         bg="#dcfce7", fg="#166534", justify="left").pack(side="left", padx=6)

        if sea.get("offpeak"):
            oc = tk.Frame(po_frame, bg="#fef2f2",
                          highlightbackground=COLORS["border"], highlightthickness=1,
                          padx=12, pady=8)
            oc.pack(side="left", fill="x", expand=True, padx=(3,0))
            tk.Label(oc, text="📉 需求淡季（价格承压概率大）", font=("Microsoft YaHei", 10, "bold"),
                     bg="#fef2f2", fg="#991b1b").pack(anchor="w")
            for sm, em, note in sea["offpeak"]:
                r = tk.Frame(oc, bg="#fee2e2", padx=8, pady=3)
                r.pack(fill="x", pady=2)
                tk.Label(r, text=_rng(sm,em), font=("Consolas", 11, "bold"),
                         bg="#fee2e2", fg="#991b1b", width=12).pack(side="left")
                tk.Label(r, text=note, font=("Microsoft YaHei", 9), wraplength=400,
                         bg="#fee2e2", fg="#991b1b", justify="left").pack(side="left", padx=6)

        # ═══════════════ 生产/收获季 ═══════════════
        if sea.get("produce"):
            pr = tk.Frame(sf, bg="#fefce8",
                          highlightbackground=COLORS["border"], highlightthickness=1,
                          padx=12, pady=8)
            pr.pack(fill="x", pady=4, padx=2)
            tk.Label(pr, text="🌾 集中生产 / 收获季", font=("Microsoft YaHei", 10, "bold"),
                     bg="#fefce8", fg="#a16207").pack(anchor="w")
            tk.Label(pr, text=sea["produce"], font=("Microsoft YaHei", 9), wraplength=800,
                     bg="#fefce8", fg=COLORS["text"], justify="left").pack(anchor="w", pady=2)
            tk.Label(pr, text="💡 此阶段供应集中释放，价格通常承压",
                     font=("Microsoft YaHei", 8), bg="#fefce8",
                     fg=COLORS["secondary"]).pack(anchor="w")

        # ═══════════════ 关键时间节点 ═══════════════
        if sea.get("key_periods"):
            kf = tk.Frame(sf, bg=COLORS["card"],
                          highlightbackground=COLORS["border"], highlightthickness=1,
                          padx=12, pady=8)
            kf.pack(fill="x", pady=4, padx=2)
            tk.Label(kf, text="📅 关键时间节点", font=("Microsoft YaHei", 10, "bold"),
                     bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w")
            for kp in sea["key_periods"]:
                r = tk.Frame(kf, bg=COLORS["card"])
                r.pack(fill="x", anchor="w", pady=1)
                tk.Label(r, text="▸", font=("Consolas", 9),
                         bg=COLORS["card"], fg=COLORS["accent"]).pack(side="left")
                tk.Label(r, text=kp, font=("Microsoft YaHei", 9),
                         bg=COLORS["card"], fg=COLORS["text"]).pack(side="left", padx=4)

        # ═══════════════ 交易提示 ═══════════════
        if sea.get("note"):
            nf = tk.Frame(sf, bg="#f0f9ff",
                          highlightbackground=COLORS["border"], highlightthickness=1,
                          padx=12, pady=8)
            nf.pack(fill="x", pady=4, padx=2)
            tk.Label(nf, text="💡 交易提示", font=("Microsoft YaHei", 10, "bold"),
                     bg="#f0f9ff", fg=COLORS["accent"]).pack(anchor="w")
            tk.Label(nf, text=sea["note"], font=("Microsoft YaHei", 9), wraplength=800,
                     bg="#f0f9ff", fg=COLORS["text"], justify="left").pack(anchor="w", pady=2)

    # ─── 计算 ─────────────────────────────────────

    def _calc(self):
        v = self.current_variety
        if not v: return
        vals = {}
        for name, e in self.input_widgets.items():
            t = e.get().strip()
            if not t:
                messagebox.showwarning("输入错误", f"请输入 {name}")
                return
            try: float(t)
            except ValueError:
                messagebox.showwarning("输入错误", f"{name} 不是有效数字")
                return
            vals[name] = t
        res = v.calculate(vals)
        if res is None:
            messagebox.showerror("计算失败", "请检查输入值")
            return
        self._show_result(v, res)
        self.sv.set(f"{v.name} 成本: {res.get('生产成本',0):,.0f} 元/吨")

    def _show_result(self, variety, result):
        for w in self.res_c.winfo_children(): w.destroy()
        total = result.get("生产成本", 0)

        tk.Label(self.res_c, text="📋 成本构成", font=("Microsoft YaHei", 11, "bold"),
                 bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w")
        for name, val in result.items():
            if name=="生产成本": continue
            r = tk.Frame(self.res_c, bg=COLORS["card"])
            r.pack(fill="x", pady=1)
            tk.Label(r, text=f"  {name}:", font=("Microsoft YaHei",10),
                     bg=COLORS["card"], fg=COLORS["secondary"]).pack(side="left")
            vs = f"{val:,.0f}" if isinstance(val,(int,float)) else str(val)
            suf = " 元/吨" if isinstance(val,(int,float)) else ""
            tk.Label(r, text=f"{vs}{suf}", font=("Consolas",10),
                     bg=COLORS["card"], fg=COLORS["text"]).pack(side="right")

        ttk.Separator(self.res_c, orient="horizontal").pack(fill="x", pady=6)

        tf = tk.Frame(self.res_c, bg=COLORS["card"])
        tf.pack(fill="x")
        tk.Label(tf, text="🏭 生产成本", font=("Microsoft YaHei",12,"bold"),
                 bg=COLORS["card"], fg=COLORS["text"]).pack(side="left")
        tk.Label(tf, text=f"{total:,.0f} 元/吨", font=("Consolas",16,"bold"),
                 bg=COLORS["card"], fg=COLORS["accent"]).pack(side="right")

        ttk.Separator(self.res_c, orient="horizontal").pack(fill="x", pady=6)

        tk.Label(self.res_c, text="📈 与市场价对比", font=("Microsoft YaHei",11,"bold"),
                 bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w")

        mf = tk.Frame(self.res_c, bg=COLORS["card"])
        mf.pack(fill="x", pady=4)
        tk.Label(mf, text="  期货价格:", font=("Microsoft YaHei",10),
                 bg=COLORS["card"], fg=COLORS["secondary"]).pack(side="left")
        self.mkt_e = ttk.Entry(mf, font=("Consolas",11), width=14)
        self.mkt_e.pack(side="left", padx=4)
        self.mkt_e.bind("<Return>", lambda e: self._cmp(total))
        tk.Label(mf, text="元/吨", font=("Microsoft YaHei",9),
                 bg=COLORS["card"], fg=COLORS["secondary"]).pack(side="left")
        ttk.Button(mf, text="对比", command=lambda: self._cmp(total)).pack(side="left",padx=4)

        self.cmp_lbl = tk.Label(self.res_c, text="", font=("Microsoft YaHei",12,"bold"),
                                 bg=COLORS["card"])
        self.cmp_lbl.pack(fill="x", pady=6)
        self.nb.select(0)

    def _cmp(self, cost):
        t = self.mkt_e.get().strip()
        if not t: return
        try: m = float(t)
        except: return
        d=m-cost; p=d/cost*100 if cost else 0
        if d>0: c=COLORS["profit"]; s="+"; st="盈利 🟢"
        else: c=COLORS["loss"]; s=""; st="亏损 🔴"
        self.cmp_lbl.configure(text=f"  {s}{d:,.0f} 元/吨 ({s}{p:.1f}%)  {st}", fg=c)
        self.sv.set(f"对比: {'盈利' if d>0 else '亏损'} {abs(p):.1f}%")


def main():
    root = tk.Tk()
    app = FuturesCostApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
