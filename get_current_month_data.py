import sqlite3
from datetime import datetime

DATABASE = 'cms.db'

def get_current_month_articles():
    current_month = datetime.now().month
    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT title, summary, link, publish_month, batch FROM articles WHERE publish_month = ?', (current_month,))
        return c.fetchall()

if __name__ == '__main__':
    data = get_current_month_articles()
    print(f"{datetime.now().month} 月发布的信息：\n")
    for item in data:
        print("标题：", item['title'])
        print("摘要：", item['summary'])
        print("链接：", item['link'])
        print("批次：", item['batch'])
        print("-" * 40)