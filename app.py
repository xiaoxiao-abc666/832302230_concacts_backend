import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

# 1. 初始化
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}}, supports_credentials=True)

# 2. 配置数据库
# __file__ 指的是当前 app.py 文件的路径
# os.path.abspath(__file__) 是 app.py 的绝对路径
# os.path.dirname(...) 是 app.py 所在的文件夹 (也就是你的项目根目录)
# os.path.join(...) 把文件夹路径和 'contacts.db' 拼接起来
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'contacts.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # 关闭一个不必要的警告

# 3. 初始化数据库 ORM (对象关系映射)
db = SQLAlchemy(app)

# 4. 【关键】定义你的通讯录模型 (数据表结构)
class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True) # 主键 ID
    name = db.Column(db.String(100), nullable=False) # 姓名
    phone = db.Column(db.String(100), nullable=False) # 电话

    # 这个函数是可选的，但很有用，它能帮你调试
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone
        }

# 5. 创建一个 "Hello World" 的 API
@app.route('/api/test', methods=['GET'])
def test_api():
    return jsonify({"message": "后端 API 运行正常!"})
# 6. 【新功能】创建 "添加联系人" 的 API
#    methods=['POST'] 表示这个接口只接受 POST 请求（用于“创建”新数据）
#
@app.route('/api/contacts', methods=['POST'])
def add_contact():
    # 1. 从前端发送的 JSON 数据中获取 'name' 和 'phone'
    data = request.json
    name = data.get('name')
    phone = data.get('phone')

    # 2. 简单的验证：确保 name 和 phone 都不为空
    if not name or not phone:
        # 400 Bad Request: 告诉前端 "请求无效，因为数据不完整"
        return jsonify({'error': 'Name and phone are required.'}), 400

    # 3. 创建一个新的 Contact 对象（使用我们之前定义的 Contact 类）
    new_contact = Contact(name=name, phone=phone)

    # 4. 把这个新对象添加到数据库 "会话" (session) 中
    db.session.add(new_contact)

    # 5. 提交 "会话"，将更改真正写入数据库文件
    db.session.commit()

    # 6. 成功后，返回一个 JSON 告诉前端“创建成功”，并附上新联系人的数据
    #    new_contact.to_dict() 是我们之前在 Contact 类里定义的辅助函数
    return jsonify(new_contact.to_dict()), 201 # 201 Created: "创建成功"
    # 7. 【新功能】创建 "获取所有联系人" 的 API
#    methods=['GET'] 表示这个接口只接受 GET 请求（用于“读取”数据）
#
@app.route('/api/contacts', methods=['GET'])
def get_contacts():
    # 1. 查询数据库：获取 Contact 表中的“所有”记录
    all_contacts = Contact.query.all()

    # 2. 转换数据
    #    all_contacts 是一个 Python 对象列表，我们需要把它转换成
    #    一个 JSON (字典) 列表，前端才能看懂。
    #    (我们使用了 Contact 类里的 to_dict() 辅助函数)
    contacts_list = []
    for contact in all_contacts:
        contacts_list.append(contact.to_dict())

    # 3. 成功后，返回这个列表
    return jsonify(contacts_list), 200
    # 8. 【新功能】创建 "删除联系人" 的 API
#    methods=['DELETE'] 表示这个接口只接受 DELETE 请求
#    <int:contact_id> 是一个“动态路由”，它会捕获 URL 中的数字
#    例如：DELETE /api/contacts/1 就会删除 ID=1 的联系人
#
@app.route('/api/contacts/<int:contact_id>', methods=['DELETE'])
def delete_contact(contact_id):
    # 1. 根据 URL 传来的 ID，在数据库中查找这个联系人
    contact_to_delete = Contact.query.get(contact_id)

    # 2. 检查：如果这个 ID 不存在 (比如已经被删了)
    if not contact_to_delete:
        # 404 Not Found: 告诉前端 "找不到"
        return jsonify({'error': 'Contact not found.'}), 404

    # 3. 如果找到了，就从数据库 "会话" (session) 中删除它
    db.session.delete(contact_to_delete)

    # 4. 提交 "会话"，将更改真正写入数据库文件
    db.session.commit()

    # 5. 成功后，返回一个空消息和 204 "No Content" (无内容) 状态码
    #    这是 DELETE 操作的标准做法
    return '', 204
# 9. 【新功能】创建 "修改/更新联系人" 的 API
#    methods=['PUT'] 表示这个接口只接受 PUT 请求 (用于“更新”数据)
#
@app.route('/api/contacts/<int:contact_id>', methods=['PUT'])
def update_contact(contact_id):
    # 1. 根据 URL 传来的 ID，在数据库中查找这个联系人
    contact_to_update = Contact.query.get(contact_id)

    # 2. 检查：如果这个 ID 不存在
    if not contact_to_update:
        return jsonify({'error': 'Contact not found.'}), 404

    # 3. 从前端发送的 JSON 数据中获取 'name' 和 'phone'
    data = request.json
    name = data.get('name')
    phone = data.get('phone')

    # 4. 验证：确保 name 和 phone 都不为空
    if not name or not phone:
        return jsonify({'error': 'Name and phone are required.'}), 400

    # 5. 更新这个联系人对象的信息
    contact_to_update.name = name
    contact_to_update.phone = phone

    # 6. 提交 "会话"，将更改真正写入数据库文件
    db.session.commit()

    # 7. 成功后，返回更新后的联系人数据
    return jsonify(contact_to_update.to_dict()), 200
# 6. 运行服务器
if __name__ == '__main__':
    # 在第一次运行前，自动创建数据库和表
    with app.app_context():
        db.create_all()
    
    # 启动服务器，使用 5000 端口，并开启调试模式
    app.run(debug=True, port=5000)