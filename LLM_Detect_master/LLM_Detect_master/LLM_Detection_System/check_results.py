import pymysql

conn = pymysql.connect(host='localhost', user='root', password='123456', database='angel')
cursor = conn.cursor()

# 查询QMS的记录
cursor.execute("SELECT workAlone, workOrderNature, judgmentBasis FROM workorder_data WHERE filename='batch_001_20251219_104156_062246_3229' LIMIT 5")
results = cursor.fetchall()

print("QMS记录的检测结果:")
for r in results:
    judgment = r[2][:80] + '...' if r[2] and len(r[2]) > 80 else r[2]
    print(f"  工单号={r[0]}")
    print(f"  工单性质={r[1]}")
    print(f"  判定依据={judgment}")
    print()

# 查询tomato的记录
cursor.execute("SELECT workAlone, workOrderNature, judgmentBasis FROM workorder_data WHERE filename='20251218_194158_工作簿1.xlsx' LIMIT 3")
results = cursor.fetchall()

print("\nTomato记录的检测结果:")
for r in results:
    judgment = r[2][:80] + '...' if r[2] and len(r[2]) > 80 else r[2]
    print(f"  工单号={r[0]}")
    print(f"  工单性质={r[1]}")
    print(f"  判定依据={judgment}")
    print()

cursor.close()
conn.close()
