#!/usr/bin/python
# coding: UTF-8
import pandas as pd
from ipaddress import ip_address
import time
from config import *

# ------------------------- 定级备案excel文件处理模块 -------------------------
def fenxi_AnZi(step,total,current_time):
    print_progress(step, total, "开始处理安资平台数据...") 
    """处理安资平台数据生成安资自用.xlsx"""
    filename = FILE_PATHS['input']['安资平台']
    df_asset = pd.read_excel(filename, sheet_name='资产填报')
    # 准备安资数据
    result = df_asset.iloc[:, [1, 6, 16, 17, 18]]
	# 重新指定列名
    new_column_names = ['资产IP', '资产小类型', '定级对象名称', '资产所属系统的定级备案等级', '网络单元类型名称']
    result.columns = new_column_names

    # 定义替换映射
    mapping = {
    '10000701': 'IP承载网城域网',
    '10001401': '互联网数据中心',
    '10001601': '互联网公有云服务平台',
    '10000601': '光传送网本地传送网',
    '10001012': '管理支撑系统',
    '10002402': 'IPTV省级平台',
    '10002002': '公众号接口服务系统'
    }

    # 假设 temp 是 result 的一个切片
    temp = result.copy()
    # 将网络单元类型名称列的数据类型转换为字符串
    temp['网络单元类型名称'] = temp['网络单元类型名称'].astype(str)    
    # 使用 .loc 方法进行替换
    temp.loc[:, '网络单元类型名称'] = temp['网络单元类型名称'].replace(mapping)
    # print(temp)
    print_progress(step, total, "安资平台数据处理完成！")
    return temp
    # 在返回安资平台数据时，需要考虑区分 公网IP 和 非公网IP

def read_from_file():
    current_time = time.strftime("%Y%m%d%H%M%S", time.localtime())  # 获取当前时间戳       
    result = (fenxi_AnZi(2,3,current_time))
    # 保存结果
    original_result_path = FILE_PATHS['output']['安资自用']
    timestamp_result_path = original_result_path.replace(".xlsx", f"_{current_time}.xlsx")  
    result.to_excel(timestamp_result_path, index=False)    

if __name__ == "__main__":
	read_from_file()