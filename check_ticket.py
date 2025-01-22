import json

import requests


def fetch_ticket_data(train_date, from_station, to_station):
    try:
        query_url = "https://kyfw.12306.cn/otn/leftTicket/queryG"
        params = {
            "leftTicketDTO.train_date": train_date,
            "leftTicketDTO.from_station": from_station,
            "leftTicketDTO.to_station": to_station,
            "purpose_codes": "ADULT"
        }

        headers = {
            "Cookie": "JSESSIONID=0"
        }
        response = requests.get(query_url, params=params, headers=headers, timeout=10)
        # 检查是否返回了错误页面
        if "error.html" in response.url:
            print("返回了错误页面，可能是请求被拦截或参数错误。")
            return False

        if response.status_code == 200 and response.text.strip():
            data = response.json()
            if data["status"] and data["data"]["result"]:
                train_list = data["data"]["result"]
                for train in train_list:
                    train_info = train.split("|")
                    train_no = train_info[3]
                    start_time = train_info[8]
                    end_time = train_info[9]
                    duration = train_info[10]
                    seat_info = {
                        "商务座": train_info[32] or train_info[25],
                        "一等座": train_info[31],
                        "二等座": train_info[30],
                        "软卧": train_info[23],
                        "硬卧": train_info[28],
                        "硬座": train_info[29],
                        "无座": train_info[26]
                    }
                    print(f"车次：{train_no}")
                    print(f"出发时间：{start_time}，到达时间：{end_time}，历时：{duration}")
                    print("余票情况：")
                    for seat_type, ticket_num in seat_info.items():
                        print(f"  {seat_type}: {ticket_num}")
                    print("-" * 40)
                return True
            else:
                print("未找到符合条件的车次。")
        else:
            print("返回内容为空或状态码异常。")
            return False
    except requests.exceptions.RequestException as e:
        print("请求异常：", e)
        return False
    except json.JSONDecodeError:
        print("返回内容不是 JSON 格式，可能是 HTML 页面。")
        return False


# 读取 station.json 文件
def read_stations():
    file_path = "station.json"
    with open(file_path, "r", encoding="utf-8") as file:
        all_stations = json.load(file)
    return all_stations

if __name__ == '__main__':
    # query_url = "https://kyfw.12306.cn/otn/leftTicket/queryG"
    # params = {
    #     "leftTicketDTO.train_date": "2025-01-23",
    #     "leftTicketDTO.from_station": "BJP",
    #     "leftTicketDTO.to_station": "HBB",
    #     "purpose_codes": "ADULT"
    # }
    #
    # headers = {
    #     "Cookie": "JSESSIONID=0"
    # }
    # response = requests.get(query_url, params=params, headers=headers, timeout=10)
    # print(response.status_code)
    # print(response.text)
    stations = read_stations()
    # print(stations)
    # fetch_ticket_data("2025-01-23", stations['北京'], 'HBB')
    for key,value in stations.items():
        # print(value)
        fetch_ticket_data("2025-01-23", value, 'HBB')