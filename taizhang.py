#!/usr/bin/python
# coding: UTF-8
import pandas as pd
from ipaddress import ip_address
import time
from config import *

# ------------------------- 本地台账excel文件处理模块 -------------------------
def fenxi_taizhang(step,total,current_time):
    print_progress(step, total, "开始处理本地台账数据...") 
    """处理本地台账数据生成台账自用.xlsx"""
    filename = FILE_PATHS['input']['本地台账']
    result = pd.read_excel(filename,sheet_name='总表')

    print_progress(step, total, "本地台账数据处理完成！")

    return result[['IP','系统全名']]

def read_from_taizhangfile():
    current_time = time.strftime("%Y%m%d%H%M%S", time.localtime())  # 获取当前时间戳       
    result = (fenxi_taizhang(2,3,current_time))
    print(result)
    return result
    # 保存结果
    original_result_path = FILE_PATHS['output']['台账自用']
    timestamp_result_path = original_result_path.replace(".xlsx", f"_{current_time}.xlsx")  
    result.to_excel(timestamp_result_path, index=False)    

# ------------------------- 测试main函数 -------------------------
if __name__ == "__main__":
    read_from_taizhangfile()