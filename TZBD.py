"""
合并版IP管理系统脚本
功能：备案数据处理 -> 资管数据处理 -> IP比对分析 -> 邮件通知
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from beian import *
from dingji import *
from config import *
from anzi import *
from si_4a import *
from taizhang import *

# ------------------------- 根据col_name指定列分离内网和外网DataFrame -------------------------
def split_to_public_private(pd,col_name):
    # 定义内网IP的正则模式
    private_ip_pattern = r'^(10\.)|(172\.1[6-9]\.)|(172\.2[0-9]\.)|(172\.3[0-1]\.)|(192\.168\.)'

    # 创建新列标记内外网
    pd['is_private'] = pd[col_name].str.match(private_ip_pattern)

    # 分离内网和外网DataFrame
    pd_private = pd[pd['is_private']].copy()  # 内网
    pd_public = pd[~pd['is_private']].copy()  # 外网
    return  pd_private, pd_public

# ------------------------- 对比分析模块 -------------------------
def process_compare_new(pd_taizhang,pd_4a,pd_4a_host_data,pd_dingji,pd_beian,pd_anzi,current_time):
# def process_compare_new(pd_ziguan,pd_dingji,pd_beian,pd_anzi):  # 综合资管安全无需比对  
    # 定义IP检查函数
    def is_excluded(ip_str):
        try:
            ip = ipaddress.ip_address(ip_str)
            return any(ip in net if isinstance(net, ipaddress.IPv4Network) else ip == net for net in EXCLUDE_IPS)
        except ValueError:
            return True  
    # 准备输出文件
    outputfilename = FILE_PATHS['output']['对比结果'].replace(".xlsx", f"_{current_time}.xlsx")
    writer = pd.ExcelWriter(outputfilename, engine='openpyxl')

    # 原始数据写入各sheet  
    pd_dingji.to_excel(writer, sheet_name='定级备案网站数据', index=False)    
    # pd_ziguan.to_excel(writer, sheet_name='综合资管平台数据', index=False)     # 综合资管安全无需比对 
    pd_4a.to_excel(writer, sheet_name='4A全量资产IP去重', index=False) 
    pd_4a_host_data.to_excel(writer, sheet_name='4A4A资产类型操作系统信息去重', index=False) 
    pd_beian.to_excel(writer, sheet_name='ICPIP备案自用', index=False)  
    pd_anzi.to_excel(writer, sheet_name='安资自用', index=False)  
    pd_taizhang.to_excel(writer, sheet_name='本地台账', index=False) 
    # 准备比对
    ips = {}  # 用于IP比对
    ip_dingjibeianming_dingjibeiandengji= {}  # 用于定级备案名称、等级的比对
    sidan_yizhi = {} # 用于4单一致比对，特别说明，地市四单一致目前仅涉及安资和4A@20250515
    # 综合资管安全无需比对
    # ip_ziguan = set(pd_ziguan['IP地址'].dropna().apply(str).apply(lambda x: x.strip()).loc[
    #                    lambda x: ~x.apply(is_excluded)])
    # ips['资管自用'] = ip_ziguan
    # 综合资管安全无需比对

    ###################################################    
    # 开始对4A系统中的数据准备  
    # 4A地址需要区分内外网
    pd_4a_private, pd_4a_public = split_to_public_private(pd_4a,'资源IP')
    ip_4a_public = set(pd_4a_public['资源IP'].dropna().apply(str).apply(lambda x: x.strip()).loc[
                       lambda x: ~x.apply(is_excluded)])
    ips['4A全量公网']=ip_4a_public    
    # 获取4A中主机类型为host的IP信息，用于四单一致比较
    sidan_4a_host = set(pd_4a_host_data['资源IP'].dropna().apply(str).apply(lambda x: x.strip()).loc[
                       lambda x: ~x.apply(is_excluded)])    
    sidan_yizhi['四单一致4A资产类型操作系统']= sidan_4a_host
    # 结束对4A系统中的数据准备
    ###################################################


    ###################################################    
    # 开始对定级备案系统中的数据准备  
    ip_dingji = set(pd_dingji['ip_seg'].dropna().apply(str).apply(lambda x: x.strip()).loc[
                       lambda x: ~x.apply(is_excluded)])
    combined_dingji = set(pd_dingji[['ip_seg', '系统名称', 'rankNo']]
                          .dropna()  # 移除包含缺失值的行
                          .apply(lambda row: '_'.join(row.astype(str).str.strip()), axis=1))
    ips['定级备案全量']=ip_dingji
    ip_dingjibeianming_dingjibeiandengji['定级备案名称等级全量']=combined_dingji

    # 定级备案需要区分内外网
    pd_dingji_private, pd_dingji_public = split_to_public_private(pd_dingji,'ip_seg')
    ip_dingji_public = set(pd_dingji_public['ip_seg'].dropna().apply(str).apply(lambda x: x.strip()).loc[
                       lambda x: ~x.apply(is_excluded)])
    combined_dingji_public = set(pd_dingji_public[['ip_seg', '系统名称', 'rankNo']]
                          .dropna()  # 移除包含缺失值的行
                          .apply(lambda row: '_'.join(row.astype(str).str.strip()), axis=1))    
    ips['定级备案公网']=ip_dingji_public    
    ip_dingjibeianming_dingjibeiandengji['定级备案名称等级公网']=combined_dingji_public
    # 结束对定级备案系统中的数据准备  
    ###################################################

    ###################################################
    # 开始对ICPIP备案系统中的数据准备  
    ip_beian = set(pd_beian['IP地址'].dropna().apply(str).apply(lambda x: x.strip()).loc[
                       lambda x: ~x.apply(is_excluded)])
    ips['ICPIP备案自用'] = ip_beian
    # 结束对ICPIP备案系统中的数据准备  
    ###################################################

    ###################################################
    # 开始对安资系统中的数据准备  
    ip_anzi = set(pd_anzi['资产IP'].dropna().apply(str).apply(lambda x: x.strip()).loc[
                       lambda x: ~x.apply(is_excluded)])
    ips['安资自用'] = ip_anzi
    combined_anzi = set(pd_anzi[['资产IP', '定级对象名称', '资产所属系统的定级备案等级']]
                          .dropna()  # 移除包含缺失值的行
                          .apply(lambda row: '_'.join(row.astype(str).str.strip()), axis=1))
    ip_dingjibeianming_dingjibeiandengji['安资平台定级备案名称等级全量']=combined_anzi
    sidan_anzi = set(pd_anzi.loc[pd_anzi['资产小类型'] == '操作系统', '资产IP'].dropna().apply(str).apply(lambda x: x.strip()).loc[
                       lambda x: ~x.apply(is_excluded)])
    sidan_yizhi['四单一致安资平台资产类型操作系统']= sidan_anzi
    # 结束对安资系统中的数据准备  
    ###################################################

    ###################################################
    # 开始对本地台账中的数据准备  
    ip_taizhang = set(pd_taizhang['IP'].dropna().apply(str).apply(lambda x: x.strip()).loc[
                       lambda x: ~x.apply(is_excluded)])
    ips['本地台账'] = ip_taizhang
    # 本地台账中仅包含了定级备案名称，没有关联定级备案等级，暂时未实现，如果要实现，可以添加一列。但是似乎没有必要
    # 结束对本地台账中的数据准备  
    ###################################################
  
    # 执行对比
    all_results = []

    # 定义双向比较方法，name1相关数据 === name2相关数据
    def save_comparison_full(name1, name2, desc1, desc2):
        unique1 = ips[name1] - ips[name2]
        unique2 = ips[name2] - ips[name1]

        result_df = pd.DataFrame(
            [[ip, desc2, name1] for ip in unique1] +
            [[ip, desc1, name2] for ip in unique2],
            columns=['比对内容', '缺失类型', '来源文件']
        )
        all_results.append(result_df)
        result_df.to_excel(writer, sheet_name=f'{name1}vs{name2}', index=False)

    # 定义单项比较方法，只要name1对应数据全量存在name2即可
    def save_comparison_half(name1, name2, desc1, desc2): # desc1其实没用了，为了好看而已
        unique1 = ips[name1] - ips[name2]
        # unique2 = ips[name2] - ips[name1]

        result_df = pd.DataFrame(
            [[ip, desc2, name1] for ip in unique1],
            columns=['比对内容', '缺失类型', '来源文件']
        )
        all_results.append(result_df)
        result_df.to_excel(writer, sheet_name=f'{name1}vs{name2}', index=False)

    # 双向比较        
    # save_comparison_full('资管自用', '定级备案公网', '资管缺失', '定级缺失') # 综合资管安全无需比对
    save_comparison_full('ICPIP备案自用', '定级备案公网', 'ICPIP备案缺失', '定级备案缺失')
    save_comparison_full('本地台账', '定级备案公网', '本地台账缺失', '定级备案缺失')
    # save_comparison_full('资管自用', '备案自用', '资管缺失', '备案缺失') # 综合资管安全无需比对
    save_comparison_full('安资自用', '定级备案全量', '安资缺失', '定级备案缺失')

    # 单项比较
    save_comparison_half('4A全量公网', 'ICPIP备案自用', '4A缺失', 'ICPIP备案缺失')  # '4A全量公网' ∈ 'ICPIP备案自用'
    # save_comparison_half('4A全量主机', '安资自用', '4A主机缺失', '安资备案缺失')

    # 定义用于四单一致的单向比较方法
    def save_sidanyizhi_comparison_half(name1, name2, desc1, desc2): # desc1其实没用了，为了好看而已
        unique1 = sidan_yizhi[name1] - sidan_yizhi[name2]
        # unique2 = ips[name2] - ips[name1]

        result_df = pd.DataFrame(
            [[ip, desc2, name1] for ip in unique1],
            columns=['比对内容', '缺失类型', '来源文件']
        )
        all_results.append(result_df)
        result_df.to_excel(writer, sheet_name=f'{name1}vs{name2}', index=False)
    save_sidanyizhi_comparison_half('四单一致安资平台资产类型操作系统', '四单一致4A资产类型操作系统', '安资平台四单不一致', '4A资产四单不一致')  # '四单一致安资平台资产类型操作系统' ∈  '四单一致4A资产类型操作系统' 
    # 四单一致当前的计算方式特点，就是分子大于分母，分母是分子的子集，这样可以保证一致率大于等于100% 

    # 定义用于定级备案名称的双向比较方法
    def save_dingjibeian_comparison_full(name1, name2, desc1, desc2):
        unique1 = ip_dingjibeianming_dingjibeiandengji[name1] - ip_dingjibeianming_dingjibeiandengji[name2]
        unique2 = ip_dingjibeianming_dingjibeiandengji[name2] - ip_dingjibeianming_dingjibeiandengji[name1]

        result_df = pd.DataFrame(
            [[dingjibeian, desc2, name1] for dingjibeian in unique1] +
            [[dingjibeian, desc1, name2] for dingjibeian in unique2],
            columns=['比对内容', '缺失类型', '来源文件']
        )
        all_results.append(result_df)
        result_df.to_excel(writer, sheet_name=f'{name1}vs{name2}', index=False)
    save_dingjibeian_comparison_full('定级备案名称等级全量', '安资平台定级备案名称等级全量', '定级备案不准确', '安资不准确')

    writer.close()
    print(f"对比分析完成，结果保存至：{outputfilename}")
    return all_results

# ========================= 主执行流程 =========================
def TZBD():
    start_time = time.time()
    current_time = time.strftime("%Y%m%d%H%M%S", time.localtime())  # 获取当前时间戳

    try:
        # 前置检查
        for f in [FILE_PATHS['input']['ICPIP备案'], FILE_PATHS['input']['安资平台'], FILE_PATHS['input']['4A平台'], FILE_PATHS['input']['本地台账']]:
            if not os.path.exists(f):
                raise FileNotFoundError(f"必要文件缺失：{f}")
        TOTAL = 5
        # 执行流程
        # pd_dingji= fenxi_DingJi(1,TOTAL,current_time)
        pd_dingji= get_DingJi(1,TOTAL,current_time)

        pd_4a,pd_4a_host_data = fenxi_4A(2,TOTAL,current_time)
        # pd_ziguan = fenxi_ZiGuan(2,TOTAL,current_time) # 综合资管安全无需比对

        pd_beian = fenxi_ICPIP_beian(3,TOTAL,current_time)

        pd_anzi = fenxi_AnZi(4,TOTAL,current_time)

        pd_taizhang = fenxi_taizhang(5,TOTAL,current_time)

        all_results = process_compare_new(pd_taizhang,pd_4a,pd_4a_host_data,pd_dingji,pd_beian,pd_anzi,current_time)
        # all_results = process_compare_new(pd_ziguan,pd_dingji,pd_beian,pd_anzi)# 综合资管安全无需比对

        # print(all_results)

        # 准备邮件
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['SENDER']
        msg['To'] = EMAIL_CONFIG['RECEIVER']
        # 准备第二个邮件
        msg_2 = MIMEMultipart()
        msg_2['From'] = EMAIL_CONFIG_OTHER['SENDER']
        msg_2['To'] = EMAIL_CONFIG_OTHER['RECEIVER']  

        combined_df = pd.concat(all_results) if 'all_results' else pd.DataFrame()
        
        if not combined_df.empty:
            msg['Subject'] = 'IP地址比对异常报告'
            msg_2['Subject'] = 'IP地址比对异常报告'

            html = f"""
            <html>
              <body>
                <h3>⏰ 比对时间：{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}</h3>
                <h3>🔍 比对结果：发现 {len(combined_df)} 条异常</h3>
                {combined_df.to_html(index=False, border=1)}
                <p style='color:#666;margin-top:20px'>自动发送，请勿直接回复</p>
              </body>
            </html>
            """
        else:
            msg['Subject'] = 'IP地址比对结果'
            msg_2['Subject'] = 'IP地址比对结果'

            html = f"""
            <html>
              <body>
                <h3>⏰ 比对时间：{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}</h3>
                <h3 style="color:green">✅ 比对结果：无异常</h3>
                <p>安资数据与定级备案数据完全匹配，没有发现差异项。</p>
                <p style='color:#666;margin-top:20px'>自动发送，请勿直接回复</p>
              </body>
            </html>
            """
        
        # 添加附件
        timestamp_result_path = FILE_PATHS['output']['对比结果'].replace(".xlsx", f"_{current_time}.xlsx")
        with open(timestamp_result_path, "rb") as f:
            part = MIMEText(f.read(), "base64", "utf-8")
            part["Content-Type"] = "application/octet-stream"
            part["Content-Disposition"] = f'attachment; filename="{os.path.basename(timestamp_result_path)}"'
            msg.attach(part)
            msg_2.attach(part)            
        
        msg.attach(MIMEText(html, 'html'))
        msg_2.attach(MIMEText(html, 'html'))

        # 发送邮件
        if EMAIL_SEND:
            try:
                with smtplib.SMTP_SSL(EMAIL_CONFIG['SMTP_SERVER'], EMAIL_CONFIG['SMTP_PORT']) as server:
                    server.login(EMAIL_CONFIG['SENDER'], EMAIL_CONFIG['PASSWORD'])
                    server.sendmail(EMAIL_CONFIG['SENDER'], EMAIL_CONFIG['RECEIVER'], msg.as_string())
                print("邮件发送成功")
            except Exception as e:
                print(f"邮件发送失败: {str(e)}")
            # 发送第二个邮件
            try:
                with smtplib.SMTP_SSL(EMAIL_CONFIG_OTHER['SMTP_SERVER'], EMAIL_CONFIG_OTHER['SMTP_PORT']) as server:
                    server.login(EMAIL_CONFIG_OTHER['SENDER'], EMAIL_CONFIG_OTHER['PASSWORD'])
                    server.sendmail(EMAIL_CONFIG_OTHER['SENDER'], EMAIL_CONFIG_OTHER['RECEIVER'], msg.as_string())
                print("第二个邮件发送成功")
            except Exception as e:
                print(f"邮件发送失败: {str(e)}")            
        # 结束发送邮件

        print(f"\n所有操作已完成，总耗时：{time.time() - start_time:.2f}秒")
    except Exception as e:
        print(f"\n程序执行出错: {str(e)}")


if __name__ == "__main__":
    TZBD()
    # 测试：
    # 定级备案网站有，icpip备案无：在定级备案网站数据中增加8.8.8.8，测试成功
    # 定级备案网站无，icpip备案有：在icpip备案系统数据中增加8.8.8.8-8.8.8.9，测试成功
    # 另外，我不关注综合资管的准确性，取消了所有的综资比对
    # 定级备案网站有数据，安资平台无，测试成功
    # 定级备案网站无数据，安资平台有，测试成功
    # 在不区分内外网地址的情况下，定级备案网站和安资平台数据一致！
    # 4A中的公网地址，和ICPIP备案进行了单项比较，发现4台bas管理地址备案非自用
    # 4A中类型为主机的IP地址，不区分内外网，和安资平台比对，发现了一些内网地址安资没有
    # 定级备案和ICPIP备案比较，需要挑选定级备案中的外网地址比对
    # 定级备案和本地台账，修改了台账一条数据，测试成功
    # 定级备案名称和等级，对比了定级备案数据和安资数据，修改了安资平台数据，测试成功，名称和等级的比对没有涉及台账，因为没有等级这列
    # 四单一致，目前的比较策略：安资平台中资产小类为操作系统的，必须在4A中对应一条host主机信息