import pymysql

conn = pymysql.connect(host='localhost', user='root', password='123456', database='angel')
cursor = conn.cursor()

# 查询tomato用户最近的5条记录
cursor.execute("SELECT filename, datatime FROM workorder_data WHERE account='tomato' ORDER BY datatime DESC LIMIT 5")
results = cursor.fetchall()

print("Tomato用户最近的记录:")
for r in results:
    print(f"  {r[0]} | {r[1]}")

# 查询QMS用户最近的5条记录  
cursor.execute("SELECT filename, datatime FROM workorder_data WHERE account='QMS' ORDER BY datatime DESC LIMIT 5")
results = cursor.fetchall()

print("\nQMS用户最近的记录:")
for r in results:
    print(f"  {r[0]} | {r[1]}")

cursor.close()
conn.close()
