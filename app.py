from flask import Flask, render_template_string, request, redirect, url_for
import sqlite3
from datetime import datetime
import requests
#import send_custom_robot_group_message
import argparse
import logging
import time
import hmac
import hashlib
import base64
import urllib.parse
import logging
from apscheduler.schedulers.background import BackgroundScheduler

# 初始化Flask应用
app = Flask(__name__)
DATABASE = 'cms.db'

# 钉钉机器人token与加密密钥
#access_token = f"0c3812daf26a236f1e5d4b0c951ff6bfa4ca441cce7873f92811ce8dac6ec48b"
#secret = f"SECc96d8298b4ee6d28f9ae88f469d8fb526e0d897018641bb10dc189d3116340a2"
    
#三人行-测试机器人
access_token = f"9deb6a3a80da03eaf261d22684b85dda2bcfa9ce0bffd740af8613606a0ddb3a"
secret = f"SEC33970c77cd960cfc2d27b52b6018a055e2e0c13afa9128847657a2a6fdb3a5b8"

#消息格式模板
# #markdown格式，可以显示图片（富文本信息待定）
# '''
# {
#      "msgtype": "markdown",
#      "markdown": {
#          "title":"杭州天气",
#          "text": "#### 杭州天气 @150XXXXXXXX \n > 9度，西北风1级，空气良89，相对温度73%\n > ![screenshot](https://img.alicdn.com/tfs/TB1NwmBEL9TBuNjy1zbXXXpepXa-2400-1218.png)\n > ###### 10点20分发布 [天气](https://www.dingtalk.com) \n"
#      },
#       "at": {
#           "atMobiles": [
#               "150XXXXXXXX"
#           ],
#           "atUserIds": [
#               "user123"
#           ],
#           "isAtAll": false
#       }
#  }
# '''


# --------------------------
# 数据库初始化（自动创建）
# --------------------------
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                link TEXT,
                publish_month INTEGER NOT NULL,
                batch TEXT NOT NULL,
                create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                pub_time DATE NOT NULL
            )
        ''')

# --------------------------
# 1. 信息录入表单
# --------------------------
@app.route('/input_msg')
def add_form():
    html = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>信息录入</title>
    <style>
        /* 全局样式重置与基础设置 */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: "Microsoft YaHei", Arial, sans-serif;
        }

        body {
            background-color: #f5f7fa;
            padding: 30px 20px;
            line-height: 1.6;
        }

        /* 页面容器：最大宽度1024px，居中 */
        .container {
            max-width: 1024px;
            width: 100%;
            margin: 0 auto;
            background: #fff;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
        }

        /* 标题 */
        h2 {
            text-align: center;
            color: #333;
            margin-bottom: 25px;
            font-size: 24px;
            border-bottom: 2px solid #409eff;
            padding-bottom: 10px;
        }

        /* 链接样式 */
        a {
            color: #409eff;
            text-decoration: none;
            margin-right: 15px;
        }

        a:hover {
            text-decoration: underline;
        }

        /* 表单样式 */
        form {
            margin: 30px 0;
        }

        /* 表单项布局 */
        .form-item {
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            flex-wrap: wrap;
        }

        /* 标签样式 */
        .form-item label {
            width: 120px;
            font-weight: bold;
            color: #555;
            font-size: 15px;
        }

        /* 输入框、文本域、下拉框统一样式 */
        input[type="text"],
        input[type="url"],
        input[type="date"],
        textarea,
        select {
            flex: 1;
            min-width: 280px;
            padding: 10px 12px;
            border: 1px solid #dcdfe6;
            border-radius: 4px;
            font-size: 14px;
            transition: border 0.3s;
        }

        input:focus,
        textarea:focus,
        select:focus {
            border-color: #409eff;
            outline: none;
        }

        /* 文本域高度 */
        textarea {
            min-height: 100px;
            resize: vertical;
        }

        /* 提交按钮 */
        button[type="submit"] {
            background-color: #409eff;
            color: #fff;
            border: none;
            padding: 12px 30px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 15px;
            margin-left: 120px;
        }

        button[type="submit"]:hover {
            background-color: #338eef;
        }

        /* 底部链接 */
        .bottom-links {
            text-align: center;
            margin-top: 20px;
        }
    </style>
</head>
<body>

<div class="container">
    <h2>信息录入</h2>

    <a href="/">返回信息列表</a>

    <form method="POST" action="/add">
        <div class="form-item">
            <label>标题：</label>
            <input type="text" name="title" required>
        </div>

        <div class="form-item">
            <label>内容概要：</label>
            <textarea name="summary" required></textarea>
        </div>

        <div class="form-item">
            <label>参考链接：</label>
            <input type="url" name="link">
        </div>

        <div class="form-item">
    <label>学习日期：</label>
    <input type="date" name="study_date" id="study_date" required>
</div>

        <div class="form-item">
            <label>发布月份：</label>
            <select name="publish_month" required>
                {% for m in range(1,13) %}
                <option value="{{m}}">{{m}}月</option>
                {% endfor %}
            </select>
        </div>

        <div class="form-item">
            <label>批次：</label>
            <select name="batch" required>
                <option value="第1次">第1次</option>
                <option value="第2次">第2次</option>
            </select>
        </div>

        <button type="submit">提交保存</button>
    </form>

    <div class="bottom-links">
        <a href="/">查看信息列表</a> | <a href="/dingtalk">推送钉钉</a>
    </div>
</div>
<script>
    // 自动设置默认日期为今天
    document.addEventListener('DOMContentLoaded', function(){
        let today = new Date().toISOString().split('T')[0];
        document.getElementById('study_date').value = today;
    });
</script>
</body>
</html>
    '''
    return render_template_string(html)

# --------------------------
# 2. 提交保存数据
# --------------------------
@app.route('/add', methods=['POST'])
def add_article():
    title = request.form['title']
    summary = request.form['summary']
    link = request.form['link']
    study_date = request.form['study_date']  # 新增
    publish_month = request.form['publish_month']
    batch = request.form['batch']

    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute(
            'INSERT INTO articles (title, summary, link, pub_time, publish_month, batch) VALUES (?,?,?,?,?,?)',
            (title, summary, link, study_date, publish_month, batch)
        )
    return redirect('/')

# --------------------------
# 3.首页， 信息列表（倒序）
# --------------------------
@app.route('/')
def article_list():
    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM articles ORDER BY create_time DESC')
        rows = c.fetchall()

   # 表格化 HTML 模板，带删除、修改按钮
    html = '''
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>信息列表</title>
        <style>
            * {
                margin: 0; padding: 0; box-sizing: border-box;
                font-family: "Microsoft YaHei", Arial, sans-serif;
            }
            body {
                background: #f5f7fa; padding: 30px;
            }
            .container {
                max-width: 1200px; margin: 0 auto;
                background: white; padding: 30px; border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            }
            h2 {
                color: #333; margin-bottom: 20px; text-align: center;
                border-bottom: 2px solid #409eff; padding-bottom: 10px;
            }
            table {
                width: 100%; border-collapse: collapse; margin: 20px 0;
                background: #fff;
            }
            th, td {
                padding: 12px 10px; text-align: center;
                border: 1px solid #eee;
            }
            th {
                background-color: #409eff; color: white;
            }
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            .btn {
                padding: 6px 12px; border-radius: 4px;
                text-decoration: none; color: white;
                font-size: 14px;
            }
            .btn-edit {
                background-color: #67c23a;
            }
            .btn-delete {
                background-color: #f56c6c;
                border: none; cursor: pointer;
            }
            .btn-edit:hover { background: #56b028; }
            .btn-delete:hover { background: #e45656; }
            .bottom-link {
                margin-top: 20px;
                text-align: center;
            }
            .bottom-link a {
                color: #409eff;
                text-decoration: none;
                margin: 0 10px;
            }
            .bottom-link a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
    <div class="container">
        <h2>信息列表</h2>

        <table>
            <tr>
                <th>ID</th>
                <th>标题</th>
                <th>内容概要</th>
                <th>参考链接</th>
                <th>学习日期</th>
                <th>发布月份</th>
                <th>批次</th>
                <th>录入时间</th>
                <th>操作</th>
            </tr>
            {% for row in rows %}
            <tr>
                <td>{{ row.id }}</td>
                <td style="text-align:left; max-width:180px;">{{ row.title }}</td>
                <td style="text-align:left; max-width:280px;">{{ row.summary[:30]+'...' if row.summary else '无内容' }}</td>
                <td><a href="{{ row.link }}" target="_blank" style="color:#409eff;">查看</a></td>
                <td>{{ row.pub_time }}</td>
                <td>{{ row.publish_month }}月</td>
                <td>{{ row.batch }}</td>
                <td style="text-align:left; max-width:120px;">{{ row.create_time }}</td>
                <td>
                    <!-- 修改按钮 -->
                    <a href="/edit/{{ row.id }}" class="btn btn-edit">修改</a>
                    <!-- 删除按钮（带确认） -->
                    <form action="/delete/{{ row.id }}" method="POST" style="display:inline;" onsubmit="return confirm('确定要删除这条信息吗？');">
                        <button type="submit" class="btn btn-delete">删除</button>
                    </form>
                </td>
            </tr>
            {% endfor %}
        </table>

        <div class="bottom-link">
            <a href="/input_msg">第一议题信息录入</a> | <a href="/dingtalk">推送钉钉</a>
        </div>
    </div>
    </body>
    </html>
    '''
    return render_template_string(html, rows=rows)

# --------------------------
# 4. 钉钉推送页面（访问即推送）
# --------------------------
@app.route('/dingtalk')
def send_dingtalk():

    timestamp = str(round(time.time() * 1000))
    string_to_sign = f'{timestamp}\n{secret}'
    hmac_code = hmac.new(secret.encode('utf-8'), string_to_sign.encode('utf-8'), digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))

    url = f'https://oapi.dingtalk.com/robot/send?access_token={access_token}&timestamp={timestamp}&sign={sign}'

    is_at_all = True
    at_user_ids=[]
    at_mobiles=[]
    msg=''



    # 获取当前月份
    current_month = datetime.now().month
    current_day=datetime.now().day
    if current_day>15:
        batch="第2次"
    else:
        batch="第1次"
    

    # 查询当月当次数据
    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM articles WHERE publish_month = ? and batch= ? ', (current_month,batch,))
        #c.execute('SELECT * FROM articles WHERE publish_month = 3 and batch= "第2次" ')
        data = c.fetchall()

    if not data:
        return f'''{current_month}月份{batch}批次未录入第一议题学习信息，请点击：<a href="/input_msg">第一议题信息录入</a>'''

    # 组装推送消息
    msg = f"{current_month}月 {batch} 第一议题学习内容：\n\n"
    for item in data:
        msg += f"标题：{item['title']}\n"
        msg += f"摘要：{item['summary']}\n"
        msg += f"链接：{item['link']}\n"
        msg += f"-"*24+"\n\n"
        

    # 发送钉钉
    #/发送消息的JSON格式构造
    body = {
        "at": {
            "isAtAll": str(is_at_all).lower(),
            "atUserIds": at_user_ids or [],
            "atMobiles": at_mobiles or []
        },
        "text": {
            "content": msg
        },
        "msgtype": "text"
    }

    headers = {'Content-Type': 'application/json'}
    #resp = requests.post(url, json=body, headers=headers)
    #logging.info("钉钉自定义机器人群消息响应：%s", resp.text)
    #return resp.json()
    #print(body)s
    try:
        resp=requests.post(url, json=body, headers=headers)
        logging.info("钉钉自定义机器人群消息响应：%s", resp.text)
        #print(f"✅ 推送成功！共推送 {len(data)} 条第一议题学习内容。{resp.json()}")
        return f'''✅ 推送成功！共推送 {len(data)} 条第一议题学习内容。{resp.json()} <br><br>&nbsp;&nbsp;&nbsp;&nbsp; <a href="/">返回信息列表</a>'''
    
    except:
        return "❌ 推送失败"
    



# ======================
# 删除信息
# ======================
@app.route('/delete/<int:id>', methods=['POST'])
def delete_article(id):
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('DELETE FROM articles WHERE id = ?', (id,))
    return redirect('/')


# ======================
# 修改页面（加载原有数据）
# ======================
@app.route('/edit/<int:id>')
def edit_article(id):
    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM articles WHERE id = ?', (id,))
        row = c.fetchone()

    html = '''
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>修改信息</title>
        <style>
            * {
                margin: 0; padding: 0; box-sizing: border-box;
                font-family: "Microsoft YaHei", Arial, sans-serif;
            }
            body {
                background: #f5f7fa; padding: 30px;
            }
            .container {
                max-width: 1024px; margin: 0 auto;
                background: white; padding: 30px; border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            }
            h2 {
                color: #333; margin-bottom: 25px; text-align: center;
                border-bottom: 2px solid #409eff; padding-bottom: 10px;
            }
            a {
                color: #409eff; text-decoration: none;
            }
            a:hover { text-decoration: underline; }
            .form-item {
                margin-bottom: 20px;
                display: flex; align-items: center; flex-wrap: wrap;
            }
            .form-item label {
                width: 120px; font-weight: bold; color: #555;
            }
            input, textarea, select {
                flex: 1; min-width: 280px; padding: 10px;
                border: 1px solid #ddd; border-radius: 4px;
            }
            textarea { min-height: 100px; resize: vertical; }
            button {
                background: #409eff; color: white; border: none;
                padding: 12px 30px; border-radius: 4px; cursor: pointer;
                margin-left: 120px;
            }
            button:hover { background: #338eef; }
        </style>
    </head>
    <body>
    <div class="container">
        <h2>修改信息</h2>
        <a href="/">返回列表</a>
        <br><br>

        <form method="POST" action="/update/{{ row.id }}">
            <div class="form-item">
                <label>标题：</label>
                <input type="text" name="title" value="{{ row.title }}" required>
            </div>

            <div class="form-item">
                <label>内容概要：</label>
                <textarea name="summary" required>{{ row.summary }}</textarea>
            </div>

            <div class="form-item">
                <label>参考链接：</label>
                <input type="url" name="link" value="{{ row.link }}">
            </div>

            <!-- 适配学习日期 -->
            <div class="form-item">
                <label>学习日期：</label>
                <input type="date" name="study_date" value="{{ row.pub_time }}" required>
            </div>

            <div class="form-item">
                <label>发布月份：</label>
                <select name="publish_month" required>
                    {% for m in range(1,13) %}
                    <option value="{{m}}" {% if m == row.publish_month %}selected{% endif %}>{{m}}月</option>
                    {% endfor %}
                </select>
            </div>

            <div class="form-item">
                <label>批次：</label>
                <select name="batch" required>
                    <option value="第1次" {% if row.batch == '第1次' %}selected{% endif %}>第1次</option>
                    <option value="第2次" {% if row.batch == '第2次' %}selected{% endif %}>第2次</option>
                </select>
            </div>

            <button type="submit">保存修改</button>
        </form>
    </div>
    </body>
    </html>
    '''
    return render_template_string(html, row=row)



# ======================
# 保存修改
# ======================
@app.route('/update/<int:id>', methods=['POST'])
def update_article(id):
    title = request.form['title']
    summary = request.form['summary']
    link = request.form['link']
    study_date = request.form['study_date']  # 新增
    publish_month = request.form['publish_month']
    batch = request.form['batch']

    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('''
            UPDATE articles 
            SET title=?, summary=?, link=?, pub_time=?, publish_month=?, batch=?
            WHERE id=?
        ''', (title, summary, link, study_date, publish_month, batch, id))
    return redirect('/')


#=================================
# 定时发送钉钉消息任务函数
#=================================
def send_dingding_msg():
    timestamp = str(round(time.time() * 1000))
    string_to_sign = f'{timestamp}\n{secret}'
    hmac_code = hmac.new(secret.encode('utf-8'), string_to_sign.encode('utf-8'), digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))

    url = f'https://oapi.dingtalk.com/robot/send?access_token={access_token}&timestamp={timestamp}&sign={sign}'

    is_at_all = True
    at_user_ids=[]
    at_mobiles=[]
    msg=''

    # 获取当前月份
    current_month = datetime.now().month
    current_day=datetime.now().day
    if current_day>15:
        batch="第2次"
    else:
        batch="第1次"
    

    # 查询当月当次数据
    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM articles WHERE publish_month = ? and batch= ? ', (current_month,batch,))
        data = c.fetchall()

    if not data:
        return f'''{current_month}月份{batch}批次未录入第一议题学习信息，请点击：<a href="/input_msg">第一议题信息录入</a>'''

    # 组装推送消息
    msg = f"{current_month}月 {batch} 第一议题学习内容：\n\n"
    for item in data:
        msg += f"标题：{item['title']}\n"
        msg += f"摘要：{item['summary']}\n"
        msg += f"链接：{item['link']}\n"
        msg += f"-"*24+"\n\n"
        

    # 发送钉钉
    #/发送消息的JSON格式构造
    body = {
        "at": {
            "isAtAll": str(is_at_all).lower(),
            "atUserIds": at_user_ids or [],
            "atMobiles": at_mobiles or []
        },
        "text": {
            "content": msg
        },
        "msgtype": "text"
    }

    headers = {'Content-Type': 'application/json'}
    #resp = requests.post(url, json=body, headers=headers)
    #logging.info("钉钉自定义机器人群消息响应：%s", resp.text)
    #return resp.json()
    #print(body)s
    try:
        resp=requests.post(url, json=body, headers=headers)
        logging.info("钉钉自定义机器人群消息响应：%s", resp.text)
        #print(f"✅ 推送成功！共推送 {len(data)} 条第一议题学习内容。{resp.json()}")
        return f'''✅ 推送成功！共推送 {len(data)} 条第一议题学习内容。{resp.json()} <br><br>&nbsp;&nbsp;&nbsp;&nbsp; <a href="/">返回信息列表</a>'''
    
    except:
        return "❌ 推送失败"
    

#================================
# 定时任务  使用调度器
#=================================
scheduler = BackgroundScheduler()
#每月第一个周五，第三个周五早8:30触发
scheduler.add_job(func=send_dingding_msg,id="send_msg",trigger="cron", month="*",day="1st fri,4th mon",hour=8, minute=30,timezone="Asia/Shanghai")
#scheduler.add_job(func=job1, args=("1","2"),id="job_1", trigger="interval", seconds=5, replace_existing=False)


# --------------------------
# 启动程序
# --------------------------
if __name__ == '__main__':
    init_db()
    # 配置日志记录器，将日志记录到文件中
    logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S',filename='dingding_msg.log', level=logging.DEBUG,encoding='utf-8')
    # 启动任务列表
    scheduler.start()
    app.run(debug=True, host='0.0.0.0', port=5000)