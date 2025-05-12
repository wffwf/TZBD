#!/usr/bin/python
# coding: UTF-8
import pandas as pd
from ipaddress import ip_address
import time
from config import *

# ------------------------- 4a全量资产excel文件处理模块 -------------------------
def fenxi_4A_byIP(iris):
    return iris['资源IP'].to_frame().drop_duplicates()
def fenxi_4A_byIPandHost(iris):
    # 筛选资源类别为'主机'的记录
    host_data = iris[iris['资源类别'] == '主机']
    # 返回资源IP和资源类别两列
    return host_data[['资源IP', '资源类别']].drop_duplicates()

def fenxi_4A(step,total,current_time):
    print_progress(step, total, "开始处理4a全量资产数据...") 
    """处理4a全量资产数据生成4A资产.xlsx"""
    filename = FILE_PATHS['input']['4A平台']
    iris = pd.read_excel(filename)
    # 硬编码剔除4A中4个IP报备不合规的资产
    # 希望能够在2026年1月份各项通报工作尚未正式开展时完成修改
    # 定义需要过滤的IP地址列表
    filtered_ips = ['221.178.219.219', '221.178.219.218', '221.178.219.175', '221.178.219.176']
    # 将字符串转换为 pandas 时间戳
    current_timestamp = pd.to_datetime(current_time, format="%Y%m%d%H%M%S")
    # 比较时间
    if current_timestamp < pd.Timestamp('2026-01-01'):
        # 从iris中过滤掉'资源IP'列中包含特定IP的行
        iris = iris[~iris['资源IP'].isin(filtered_ips)]    
    # 硬编码结束
    result = fenxi_4A_byIP(iris)
    host_data = fenxi_4A_byIPandHost(iris)

    print_progress(step, total, "4a全量资产数据处理完成！")

    return result,host_data

def read_from_4afile():
    current_time = time.strftime("%Y%m%d%H%M%S", time.localtime())  # 获取当前时间戳       
    result,host_data = (fenxi_4A(2,3,current_time))
    # print(host_data)
    return result

# ------------------------- 测试main函数 -------------------------
if __name__ == "__main__":
    result = read_from_4afile()
    # 保存结果
    current_time = time.strftime("%Y%m%d%H%M%S", time.localtime())  # 获取当前时间戳     
    original_result_path = FILE_PATHS['output']['4A自用']
    timestamp_result_path = original_result_path.replace(".xlsx", f"_{current_time}.xlsx")  
    result.to_excel(timestamp_result_path, index=False)     