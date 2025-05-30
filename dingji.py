#!/usr/bin/python
# coding: UTF-8
import pandas as pd
from ipaddress import ip_address
import time
from config import *
import datetime
import requests
import json
from collections import defaultdict
import os


# 设置代理服务器（HTTP 和 HTTPS 可分别设置）
proxies = {
    'http': 'http://127.0.0.1:8080',
    'https': 'http://127.0.0.1:8080'  # 或 'https://...'
}

PROXY_DEBUG = False
GET_DETAIL_INFO = False

# ================== 第一部分：定级备案网站数据导出 ==================

def expand_ip_range(ip_str):
    """处理IP地址或网段，返回单个IP列表"""
    if not ip_str or pd.isna(ip_str):
        return []

    ip_str = str(ip_str).strip()
    if '-' in ip_str:
        base_ip, range_part = ip_str.split('-')
        base_parts = base_ip.split('.')
        start = int(base_parts[3])
        end = int(range_part)

        ips = []
        for i in range(start, end + 1):
            ips.append(f"{base_parts[0]}.{base_parts[1]}.{base_parts[2]}.{i}")
        return ips
    else:
        return [ip_str]

def process_ip_input(ip_input):
    """处理IP输入，支持字符串或列表形式，处理逗号分隔和网段"""
    if ip_input is None:
        return []

    if hasattr(ip_input, '__iter__') and not isinstance(ip_input, (str, bytes)):
        ip_input = list(ip_input)

    if isinstance(ip_input, list):
        ip_str = ','.join(
            str(ip) for ip in ip_input if ip is not None and not (hasattr(ip, '__float__') and pd.isna(ip)))
    else:
        if pd.isna(ip_input):
            return []
        ip_str = str(ip_input)

    ip_list = []
    for part in ip_str.split(','):
        part = part.strip()
        if part:
            ip_list.extend(expand_ip_range(part))

    return ip_list

def get_jwt_from_user():
    """从用户输入获取JWT"""
    print("请从浏览器开发者工具中获取最新的JWT值：")
    print("1. 打开Chrome开发者工具(F12)")
    print("2. 切换到Network(网络)标签")
    print("3. 刷新页面并找到任意api请求")
    print("4. 在请求头中找到Authorization字段的值")
    print("5. 复制该值并粘贴到此处")
    # for test
    if PROXY_DEBUG:
        return "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiY2MzNDc1MWZlNWY0NWYxZWJlNDc4ZTYyOTk4YTA1MTAyN2ZiNjQ1NjllNzFmOWY3Njg0ZmNiMDM0Y2MzYWY4OGM1NmEyODhjMmFmYmUyODkiLCJpYXQiOjE3NDcyNzIwNTYuODkyOTU2LCJuYmYiOjE3NDcyNzIwNTYuODkyOTY0LCJleHAiOjE3NDczNTg0NTYuNzc1ODYzLCJzdWIiOiIzODA1MSIsInNjb3BlcyI6W119.RvxPOUZGuo4LhcPpvjwMdALWdoNXuEQFUFCiGZicHIoGgPJaIRap9JcLhfy3uSMBsr3fCbAMa9clK8gwxT9kW9heXA3W0t7DPf_lTbXzEF8jTLQlndhPbHDExmf6ZgVwhXivG1wve6tgoUmuWvprl8Kttqn1Glqt2mhWkmzpPJvzNcC_ZtCoiYJ8zwbX8Bk2oFE25ZNuc2XTUtVQhPyHe_Y7OVWJypYmYKjemcrLWzn5f2b0x0HYXcahUtSirKf-vMvhMv4Jzsz6rCvwzcWSaGlz_SKi30MRQbAXy2ilIo5IED0mkRADfXAUrExcloh0Zt3EzlRdbWLut3DV2zrS5mv_UdARydnwQvcVOwDYw5k59jGP66FE4lIRGhV70HRysFf07yeY4kA5epxQ_XzRHWwcTVPXUWxp7bbaw2q97zU5MmJUsOt1wx6STt7vR6GfiLga0pJC1jkpyaIBuPpHa56TcRw0sQxk1Z5GNd6PnrlMDKDSfV0P-jkcukG0lXG9T5RyYuMytC0PwOmfcim1meflyXeqWsshGfcXCWfDiSuTWIeVtoBa6L8rO8c1s-KrksmyZeD9w8xvyjrKSWpdB4y-yVSiGT7Ma_bTlvJ-vjcejf56hPGZddKr_og4K7I0UZXSQNN7Kr2aLO6eO332KUvLihzSAUDTkIERrYBHWM4"
    # for test
    jwt = input("请输入JWT值: ").strip()
    if not jwt:
        print("错误：JWT值不能为空！")
        exit(1)
    return jwt
def export_djba_data_summary(jwt):
    """导出定级备案数据"""

    url = "https://www.mii-aqfh.cn/"
    headers = {
        "Authorization": jwt,
        "Origin": "https://www.mii-aqfh.cn",
        "Referer": "https://www.mii-aqfh.cn/gradingFiling?company_type=3",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0",
        "Content-Type": "application/json;charset=utf-8",
        "Te": "trailers"
    }

    # 获取网络类型映射
    neteid_proj = {}
    route = "/api/api/common/getNetType"
    try:
        if PROXY_DEBUG:
            response = requests.get(url=url + route, headers=headers, timeout=10, proxies=proxies, verify=False)
        else:
            response = requests.get(url=url + route, headers=headers, timeout=10)
        response.raise_for_status()
        res = json.loads(response.text)["data"]
        for r in res:
            neteid_proj[r["id"]] = r["name"]
            if "list" in r:
                for rr in r["list"]:
                    neteid_proj[rr["id"]] = rr["name"]
    except Exception as e:
        print(f"获取网络类型时出错: {str(e)}")
        exit(0)

    # 获取对象列表数据
    result_data = {}
    route = "api/api/getObjectList"
    for i in range(2):
        try:
            body = {
                "name": "", "neteid": "", "rank": [], "status": [], "time": "",
                "reviewer_name": "", "review_status": [], "expire_status": "",
                "apply_back_status": "", "creator_name": "", "company_name": "",
                "updated_at": "", "comment_time_start": "", "comment_time_end": "",
                "page": i + 1, "public_ip": "", "software_ip": "", "companytype": "3"
            }
            if PROXY_DEBUG:
                response = requests.post(url=url + route, headers=headers, json=body, timeout=10, proxies=proxies, verify=False)
            else:
                response = requests.post(url=url + route, headers=headers, json=body, timeout=10)
            response.raise_for_status()
            res = json.loads(response.text)["data"]["data"]
            for item in res:
                
                result_data[item["name"]] = {
                    "id": item.get("id"),
                    "software_ip": item.get("software_ip"),
                    "public_ip": item.get("public_ip"),
                    "rankNo": item.get("rankNo"),
                    "net_type": neteid_proj.get(item["nete_id"], "未知网络类型")
                }
                # print(result_data[item["name"]])
        except Exception as e:
            print(f"获取第{i + 1}页数据时出错: {str(e)}")
            continue
    return   result_data  

def export_djba_operatersystem_detail_by_id(name,id,jwt):
    """导出定级备案数据"""
    url = "https://www.mii-aqfh.cn"
    headers = {
        "Authorization": jwt,
        "Origin": "https://www.mii-aqfh.cn",
        "Referer": "https://www.mii-aqfh.cn/gradingFiling?company_type=3",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0",
        "Content-Type": "application/json;charset=utf-8",
        "Te": "trailers"
    }
    # 获取某定级备案详细信息
    neteid_proj = {}
    route = "/api/api/getAssets"
    try:
        body = {
            "id": str(id), "companytype": "3","getType":3,"page":1
        }
        if PROXY_DEBUG:
            response = requests.post(url=url + route, headers=headers, json=body, timeout=10, proxies=proxies, verify=False)
        else:
            response = requests.post(url=url + route, headers=headers, json=body, timeout=10)
        response.raise_for_status()
        res = json.loads(response.text)
        data = res['data']['basesoft']
        df = pd.json_normalize(data)
        df.to_excel(f'{name}.xlsx', index=False)  # 搞到这里了，先看看导出结果什么样子，如何结合4单一致
    except Exception as e:
        print(f"获取{name}详细信息时出错: {str(e)}")
        exit(0)
    
def export_djba_data_detail(result_data,jwt):
    # 遍历列表中的每个字典
    dingjibeian_systems={}
    for name, details in result_data.items():
        dingjibeian_systems[name]=details['id']
        export_djba_data_detail_by_id(name,details['id'],jwt)
    
def export_djba_data():
    jwt = get_jwt_from_user()    
    result_data = export_djba_data_summary(jwt)

    # 准备合并后的数据
    ip_info = defaultdict(lambda: {
        'ip_types': set(),
        'systems': set(),
        'net_types': set(),
        'rankNos': set()
    })

    for name, details in result_data.items():
        # 处理public_ip数据
        public_ips = process_ip_input(details["public_ip"])
        for ip in public_ips:
            ip_info[ip]['ip_types'].add('public_ip')
            ip_info[ip]['systems'].add(name)
            ip_info[ip]['net_types'].add(details["net_type"])
            ip_info[ip]['rankNos'].add(details["rankNo"])

        # 处理software_ip数据
        software_ips = process_ip_input(details["software_ip"])
        for ip in software_ips:
            ip_info[ip]['ip_types'].add('software_ip')
            ip_info[ip]['systems'].add(name)
            ip_info[ip]['net_types'].add(details["net_type"])
            ip_info[ip]['rankNos'].add(details["rankNo"])

    # 构建概要信息DataFrame
    merged_data = []
    for ip, info in ip_info.items():
        merged_data.append({
            'ip_seg': ip,
            'ip_type': ','.join(sorted(info['ip_types'])),
            '系统名称': ','.join(sorted(info['systems'])),
            'net_type': ','.join(sorted(info['net_types'])),
            'rankNo': ','.join(str(r) for r in sorted(info['rankNos']))
        })

    # 创建DataFrame并按IP排序
    merged_df = pd.DataFrame(merged_data).sort_values('ip_seg')

    # 准备获取详细信息，输入result_data和jwt，从result_data中提取id和name进一步获取详细信息
    if GET_DETAIL_INFO:
        for name, details in result_data.items():
            export_djba_operatersystem_detail_by_id(name,details['id'],jwt)

    return merged_df


# ------------------------- 定级备案excel文件处理模块 -------------------------
def get_DingJi_from_file(step,total,current_time):
    print_progress(step, total, "开始处理定级备案数据...") 
    """处理定级备案数据生成定级自用.xlsx"""
    filename = FILE_PATHS['input']['定级备案']
    result = pd.read_excel(filename)

    print_progress(step, total, "ICPIP备案数据处理完成！")
    return result

def read_from_file():
    current_time = time.strftime("%Y%m%d%H%M%S", time.localtime())  # 获取当前时间戳       
    result = (fenxi_DingJi(2,3,current_time))
    # 保存结果
    original_result_path = FILE_PATHS['output']['定级自用']
    timestamp_result_path = original_result_path.replace(".xlsx", f"_{current_time}.xlsx")  
    result.to_excel(timestamp_result_path, index=False)    

def get_DingJi_from_web(step,total,current_time):
    try:
        # 第一步：导出定级备案数据
        print_progress(step,total, "正在准备爬取定级备案数据...")
        merged_df = export_djba_data()
        if merged_df is None or merged_df.empty:
            raise Exception("定级备案数据导出失败")
        print_progress(step, total, "定级备案网站数据爬取完成！")            
    except Exception as e:
        print(f"\n处理过程中发生错误: {str(e)}")
        exit(0)

    return merged_df # 注意这里返回的定级备案ip地址涉及公网地址和内网地址

def read_from_web(step,total,current_time):
    merged_df = get_DingJi_from_web(step,total,current_time)
    return(merged_df)
    


def get_DingJi(step,total,current_time):
    return get_DingJi_from_web(step,total,current_time)

# ------------------------- 测试main函数 -------------------------
if __name__ == "__main__":
    current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")    
    merged_df = read_from_web(2,4,current_time)
    # read_from_file()
    print(merged_df) 
    exit(0)
    # 保存到Excel文件
    output_file = f"定级备案网站数据_{current_time}.xlsx"    
    try:
        with pd.ExcelWriter(output_file) as writer:
            merged_df.to_excel(writer, sheet_name="ip_list", index=False)
            # 确保至少有一个可见的工作表
            if len(merged_df) == 0:
                pd.DataFrame({'提示': ['没有找到定级备案数据']}).to_excel(writer, sheet_name="无数据", index=False)
        print(f"定级备案数据已成功保存到 {output_file}")
    except Exception as e:
        print(f"保存Excel文件时出错: {str(e)}")
