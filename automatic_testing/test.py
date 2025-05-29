from datetime import datetime
import json
import mysql.connector

import requests


data= {
      "Department": "AE2",
      "ProjectNo": "P07784",
      "Carline": "P611Z",
      "ProductVariant": "SCM",
      "SamplePhase": "C03",
      "SYS_Testable": "Unknown",
      "SYS_Passed": "Unknown",
      "VerifyPassRate": "Unknown",
      "TotalRelease": "Unknown",
      "SuccessRelease": "Unknown",
      "RelSuccessRate": "Unknown",
      "Issue_TotalNum": "Unknown",
      "Issue_OpenNum": "Unknown",
      "Issue_CloseRate": "Unknown",
      "Customer_Issue_TotalNum": "Unknown",
      "Customer_Issue_OpenNum": "Unknown",
      "Customer_Issue_CloseRate": "Unknown",
      "Date": "2025-04-08 15:27:06",
      "CalendarWeek": "2025-W15"
    }

if __name__ == '__main__':
    # config = {
    #     user: 'system',
    #     password': 'Kostal8888',
    #     'host': 'cnsfjenl004.cn.kostal.int',
    #     'database': 'ai_related',
    #     auth_plugin='mysql_native_password'
    # }
    conn = mysql.connector.connect(user='system', password='Kostal8888', host='cnsfjenl004.cn.kostal.int', database='ai_related', auth_plugin='mysql_native_password')
    cursor = conn.cursor()
    department = data['Department']
    project_no = data['ProjectNo']
    carline = data['Carline']
    product_variant = data['ProductVariant']
    sample_phase = data['SamplePhase']
    select_query = "select id from Project_List where Department = %s and ProjectNo = %s and Carline = %s and ProductVariant = %s and SamplePhase = %s"
    cursor.execute(select_query, (department, project_no, carline, product_variant, sample_phase))
    result = cursor.fetchone()
    if result:
        # 如果找到了匹配的记录，则更新数据
        update_query = "update Project_List set SYS_Testable = %s, SYS_Passed = %s, VerifyPassRate = %s, TotalRelease = %s, SuccessRelease = %s, RelSuccessRate = %s, Issue_TotalNum = %s, Issue_OpenNum = %s, Issue_CloseRate = %s, Customer_Issue_TotalNum = %s, Customer_Issue_OpenNum = %s, Customer_Issue_CloseRate = %s, Date = %s, CalendarWeek = %s where id = %s"
        cursor.execute(update_query, (
            data['SYS_Testable'],
            data['SYS_Passed'],
            data['VerifyPassRate'],
            data['TotalRelease'],
            data['SuccessRelease'],
            data['RelSuccessRate'],
            data['Issue_TotalNum'],
            data['Issue_OpenNum'],
            data['Issue_CloseRate'],
            data['Customer_Issue_TotalNum'],
            data['Customer_Issue_OpenNum'],
            data['Customer_Issue_CloseRate'],
            datetime.strptime(data["Date"], "%Y-%m-%d %H:%M:%S"),
            data["CalendarWeek"],
            result[0]
        ))
    else:
        # 插入数据
        insert_query = "insert into Project_List (Department, ProjectNo, Carline, ProductVariant, SamplePhase, SYS_Testable, SYS_Passed, VerifyPassRate, TotalRelease, SuccessRelease, RelSuccessRate, Issue_TotalNum, Issue_OpenNum, Issue_CloseRate, Customer_Issue_TotalNum, Customer_Issue_OpenNum, Customer_Issue_CloseRate, Date, CalendarWeek) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) on duplicate key update SYS_Testable=values(SYS_Testable), SYS_Passed=values(SYS_Passed), VerifyPassRate=values(VerifyPassRate), TotalRelease=values(TotalRelease), SuccessRelease=values(SuccessRelease), RelSuccessRate=values(RelSuccessRate), Issue_TotalNum=values(Issue_TotalNum), Issue_OpenNum=values(Issue_OpenNum), Issue_CloseRate=values(Issue_CloseRate), Customer_Issue_TotalNum=values(Customer_Issue_TotalNum), Customer_Issue_OpenNum=values(Customer_Issue_OpenNum), Customer_Issue_CloseRate=values(Customer_Issue_CloseRate), Date=values(Date), CalendarWeek=values(CalendarWeek)"
        data_tuple = (
            data['Department'],
            data['ProjectNo'],
            data['Carline'],
            data['ProductVariant'],
            data['SamplePhase'],
            data['SYS_Testable'],
            data['SYS_Passed'],
            data['VerifyPassRate'],
            data['TotalRelease'],
            data['SuccessRelease'],
            data['RelSuccessRate'],
            data['Issue_TotalNum'],
            data['Issue_OpenNum'],
            data['Issue_CloseRate'],
            data['Customer_Issue_TotalNum'],
            data['Customer_Issue_OpenNum'],
            data['Customer_Issue_CloseRate'],
            datetime.strptime(data["Date"], "%Y-%m-%d %H:%M:%S"),
            data["CalendarWeek"]
        )
        cursor.execute(insert_query, data_tuple)
    conn.commit()
    cursor.close()
    conn.close()