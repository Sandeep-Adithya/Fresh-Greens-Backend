from flask import current_app as app, jsonify, request, render_template
from flask_security import auth_required, roles_required
from werkzeug.security import check_password_hash, generate_password_hash
from flask_restful import marshal, fields
from models import User, db, datastore

@app.get('/')
def api():
    return jsonify({'message' : 'Hello, World'})

@app.post('/authenticate')
def ulogin():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({"message": "email not provided"}), 400

    user = datastore.find_user(email=email)

    if not user:
        return jsonify({"message": "User Not Found"}), 404

    if check_password_hash(user.password, data.get("password")):
        if user.active==True:
            return jsonify({"token": user.get_auth_token(), "name": user.name, "email": user.email, "phone": user.phone, "address": user.address, "role": user.roles[0].name})
        else:
            return jsonify({"message": "User Not Active"}), 400
    else:
        return jsonify({"message": "Wrong Password"}), 400
    
@app.post('/register/<string:role>')
def signup(role):
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    phone = data.get('phone')
    address = data.get('address')
    active=False
    if not email:
        return jsonify({"message": "email not provided"}), 400
    if not password:
        return jsonify({"message": "password not provided"}), 400
    if not name:
        return jsonify({"message": "name not provided"}), 400
    if not phone:
        return jsonify({"message": "phone not provided"}), 400
    if not address:
        return jsonify({"message": "address not provided"}), 400
    user = datastore.find_user(email=email)
    if user:
        return jsonify({"message": "User Already Exists"}), 400
    else:
        if role=="user":
            active=True
        datastore.create_user(email=email, password=generate_password_hash(password), roles=[role], name=name, address=address, phone=phone, active=active)
        datastore.commit()
        return jsonify({"message": "User Created"}), 201
    
@app.post('/activate')
def activate():
    data = request.get_json()
    id = data.get('id')
    user = datastore.find_user(id=id)
    if not user:
        return jsonify({"message": "User Not Found"}), 404
    else:
        if data.get('active') == True:
            user.active=False
        else:
            user.active=True
        db.session.commit()
        return jsonify({"message": "User Activated"}), 200
    
user_fields={
    'id': fields.Integer,
    'name': fields.String,
    'email': fields.String,
    'phone': fields.Integer,
    'address': fields.String,
    'active': fields.Boolean,
    'roles': fields.List(fields.String)
}

@app.get('/users')
@auth_required()
@roles_required('admin')
def get_users():
    users = User.query.all()
    return jsonify([marshal(user, user_fields) for user in users])

@app.get('/users/<int:id>')
@auth_required()
@roles_required('admin')
def get_user(id):
    user = User.query.get(id)
    return jsonify(marshal(user, user_fields))

