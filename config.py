#!/usr/bin/python
# coding: UTF-8
import ipaddress

# ========================= 功能模块 =========================
def print_progress(step, total, message):
    """打印带进度标识的状态信息"""
    print(f"[{step}/{total}] {message}")

# ========================= 全局配置 =========================
# 文件路径配置
FILE_PATHS = {
    'input': {
        'ICPIP备案': "./fpxxList.xls",
        # 'IDC业务': "./IDC业务地址.xlsx",
        # 'IDC自用': "./IDC自用地址.xlsx",
        # '专线地址': "./专线地址.xlsx",
        # '自用地址': "./自用地址.xlsx",
        '安资平台': "./安资平台.xlsx",        
        '4A平台': "./20250428全量资源.xlsx",  
        '本地台账': "./附件1：暴露面资产IP和端口开通依据确认表【2022年新模板】-20250506.xlsx",              
        '定级备案': "./定级备案.xlsx"
    },
    'output': {
        '备案自用': "./ICPIP备案自用.xlsx",
        # '资管自用': "./资管自用.xlsx",
        '安资自用': "./安资自用.xlsx",                 
        '4A自用':   "./4A自用.xlsx",                 
        '定级自用': "./定级备案.xlsx",
        '台账自用': "./本地台账.xlsx",       
        '对比结果': "./ip_comparison_results.xlsx"
    }
}

# 邮件配置
EMAIL_CONFIG = {
    'SMTP_SERVER': 'smtp.xxx.com',
    'SMTP_PORT': 465,
    'SENDER': 'xxx@xxx.com',
    'PASSWORD': 'xxxxxxxxxx',
    'RECEIVER': 'xxxx@xx.com',
    'CC': 'xxxxxx@xxxxxx.com'
}

# 邮件配置
EMAIL_CONFIG_OTHER = {
    'SMTP_SERVER': 'smtp.xxx.com',
    'SMTP_PORT': 465,
    'SENDER': 'xxx@xxx.com',
    'PASSWORD': 'xxxxxxxxxx',
    'RECEIVER': 'xxxx@xx.com',
}

# 排除IP配置
EXCLUDE_IPS = {
    ipaddress.ip_network('x.x.x.0/24', strict=False), 
    ipaddress.ip_address('x.x.x.x'), 
    ipaddress.ip_address('x.x.x.x'), 
    ipaddress.ip_address('x.x.x.x'),
    ipaddress.ip_address('x.x.x.x'),
    ipaddress.ip_address('x.x.x.x')
}
