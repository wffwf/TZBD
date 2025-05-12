#!/usr/bin/python
# coding: UTF-8
import pandas as pd
from ipaddress import ip_address
import time
from config import *
def expand_ip_range(start_ip, end_ip):
    """Expand a range of IPs into individual IPs in dotted-decimal notation."""
    start = ip_address(start_ip)
    end = ip_address(end_ip)
    return [str(ip_address(ip)) for ip in range(int(start), int(end) + 1)]

def fenxi_ICPIP_beian(step,total,current_time):
    """处理备案数据生成备案自用.xlsx"""
    print_progress(step, total, "开始处理ICPIP备案数据...")

    # 原始beian.py逻辑
    iris = pd.read_excel(FILE_PATHS['input']['ICPIP备案'], None)
    keys = list(iris.keys())
    iris_concat = pd.DataFrame()

    for i in keys:
        iris1 = iris[i]
        iris_concat = pd.concat([iris_concat, iris1])

    # 数据过滤处理
    iris_concat = iris_concat[iris_concat["使用方式"] != "动态"]
    iris_concat.loc[iris_concat["使用方式"] == "未知", "分配方式"] = "空闲"
    temp = (iris_concat["使用方式"] == "静态") & (iris_concat["分配方式"] == "自用")
    iris_concat.loc[temp, "分配方式"] = "自用静态"

    # 生成备案数据
    iris_concat.loc[iris_concat["分配方式"] == "再分配", "使用单位名称"] = iris_concat.loc[
        iris_concat["分配方式"] == "再分配", "分配对象"]
    df = iris_concat[["起始IP", "终止IP", "分配方式", "使用单位名称"]].copy()
    df.rename(columns={'分配方式': "分配方式（备案）", '使用单位名称': "集团客户名称（备案）"}, inplace=True)

    # IP展开逻辑
    def expand_ip_range(start_ip, end_ip):
        start = ip_address(start_ip)
        end = ip_address(end_ip)
        return [str(ip_address(ip)) for ip in range(int(start), int(end) + 1)]

    static_self_use = df[df["分配方式（备案）"] == "自用静态"]
    individual_ips = []

    for _, row in static_self_use.iterrows():
        individual_ips.extend([
            (ip, row["分配方式（备案）"], row["集团客户名称（备案）"])
            for ip in expand_ip_range(row["起始IP"], row["终止IP"])
        ])

    ips_df = pd.DataFrame(individual_ips, columns=["IP地址", "分配方式（备案）", "集团客户名称（备案）"])  

    # 筛选出第三列非空的数据
    non_empty_df = ips_df[ips_df['集团客户名称（备案）'].notnull() & (ips_df['集团客户名称（备案）'] != "")]
    if(non_empty_df.shape[0]):
        # 输出需要告警的数据
        print("WARNING:")
        print(non_empty_df)
    print_progress(step, total, "ICPIP备案数据处理完成!")
    return ips_df


if __name__ == "__main__":
    current_time = time.strftime("%Y%m%d%H%M%S", time.localtime())  # 获取当前时间戳   
    ips_df = (fenxi_ICPIP_beian(1,3,current_time))
    # 保存结果
    original_result_path = FILE_PATHS['output']['备案自用']
    timestamp_result_path = original_result_path.replace(".xlsx", f"_{current_time}.xlsx")  
    ips_df.to_excel(timestamp_result_path, index=False)