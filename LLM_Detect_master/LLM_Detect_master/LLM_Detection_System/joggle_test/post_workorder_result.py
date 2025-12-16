import requests
import pymysql

# 配置
BASE_URL = "http://qmstest.angelgroup.com.cn:8080"
SUBMIT_URL = f"{BASE_URL}/qualityDataAnalysis/baseData/crmMaintenanceData/aiSubmitJudgment"

# 直接填入你已获取的token
ACCESS_TOKEN = "Bearer cXVhbGl0eURhdGE6JDJhJDEwJGZDOU40WUxOWUlCLzgyM3ZQcjd2b2U3dWtndUtHSkRNYzdya210UmkxeHVCQ0lZZUcwMkJX"  # 替换为你实际的token

# 数据库连接信息
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "123456",
    "database": "angel",
    "charset": "utf8mb4"
}

# 从数据库读取待回写的工单
def fetch_workorders():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    sql = """
        SELECT workAlone, workOrderNature, judgmentBasis
        FROM workorder_data
        WHERE workAlone IS NOT NULL
          AND workOrderNature IS NOT NULL
          AND judgmentBasis IS NOT NULL
    """
    cursor.execute(sql)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

# 回写判定结果
def submit_judgment(auth_token, workorder):
    headers = {
        "Authorization": auth_token,
        "Content-Type": "application/json"
    }
    payload = {
        "workAlone": workorder["workAlone"],
        "workOrderNature": workorder["workOrderNature"],
        "judgmentBasis": workorder["judgmentBasis"]
    }
    response = requests.post(SUBMIT_URL, json=payload, headers=headers)
    return response.status_code, response.json()

# 主函数
def main():
    try:
        workorders = fetch_workorders()
        print(f"从数据库读取到 {len(workorders)} 条工单")

        for wo in workorders:
            status, result = submit_judgment(ACCESS_TOKEN, wo)
            if status == 200:
                print(f"工单 {wo['workAlone']} 回写成功")
            else:
                print(f"工单 {wo['workAlone']} 回写失败，响应：{result}")

    except Exception as e:
        print("执行出错：", e)

if __name__ == "__main__":
    main()