from flask_restful import Resource, Api, reqparse, fields, marshal
from flask_security import auth_required, roles_required, current_user, roles_accepted
from flask import jsonify
from sqlalchemy import or_
from models import db, Category, User, Cart, Products, Orders, Role, Unit
import datetime
from instances import cache

api = Api(prefix="/api")

product_parser = reqparse.RequestParser()
product_parser.add_argument('name', type=str, required=True, help="Name cannot be blank!")
product_parser.add_argument('price', type=int, required=True, help="Price cannot be blank!")
product_parser.add_argument('quantity', type=int, required=True, help="Quantity cannot be blank!")
product_parser.add_argument('description', type=str, required=True, help="Description cannot be blank!")
product_parser.add_argument('category', type=int, required=True, help="Category cannot be blank!")
product_parser.add_argument('unit', type=int, required=True, help="Unit cannot be blank!")
product_parser.add_argument('expiry', type=str, required=True, help="Expiry cannot be blank!")

cart_parser = reqparse.RequestParser()
cart_parser.add_argument('cart', type=list, required=True, help="Cart cannot be blank!")

category_parser = reqparse.RequestParser()
category_parser.add_argument('name', type=str, required=True, help="Name cannot be blank!")
category_parser.add_argument('active', type=int, required=False, help="")
category_parser.add_argument('request_action', type=int, required=False, help="")

user_parser = reqparse.RequestParser()
user_parser.add_argument('name', type=str, required=True, help="Name cannot be blank!")
user_parser.add_argument('email', type=str, required=True, help="Email cannot be blank!")
user_parser.add_argument('password', type=str, required=True, help="Password cannot be blank!")
user_parser.add_argument('phone', type=int, required=True, help="Phone cannot be blank!")
user_parser.add_argument('address', type=str, required=True, help="Address cannot be blank!")

unit_parser = reqparse.RequestParser()
unit_parser.add_argument('name', type=str, required=True, help="Name cannot be blank!")

product_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'price': fields.Integer,
    'quantity': fields.Integer,
    'description': fields.String,
    'category': fields.String,
    'unit': fields.String,
    'expiry': fields.DateTime,
    'created_at': fields.DateTime,
    'updated_at': fields.DateTime
}

cart_fields = {
    'id': fields.Integer,
    'user_id': fields.Integer,
    'value': fields.String
}

category_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'active': fields.Boolean,
    'request_action': fields.Integer,
}

unit_fields = {
    'id': fields.Integer,
    'name': fields.String
}

user_fields={
    'id': fields.Integer,
    'name': fields.String,
    'email': fields.String,
    'phone': fields.Integer,
    'address': fields.String,
    'active': fields.Boolean
}

class Category_API(Resource):
    @cache.cached(9999, key_prefix="categories")
    def get(self):
        category = Category.query.all()
        print(category)
        return [marshal(category, category_fields) for category in category], 200
    
    @auth_required("token")
    @roles_accepted("manager", "admin")
    def post(self):
        args = category_parser.parse_args()
        category = Category.query.filter_by(name=args.get('name')).first()
        if category != None:
            return {"message": "Category already exists"}, 400
        category = Category(name=args['name'])
        db.session.add(category)
        db.session.commit()
        cache.delete("categories")
        return {"message": "Category added"}, 201
    
    @auth_required("token")
    @roles_accepted("manager", "admin")
    def delete(self, id):
        print(id)
        category = Category.query.filter_by(id=id).first()
        print(category)
        if not category:
            return {"message": "Category not found"}, 404
        db.session.delete(category)
        db.session.commit()
        cache.delete("categories")
        return {"message": "Category deleted"}, 200
    
    @auth_required("token")
    @roles_accepted("manager", "admin")
    def put(self, id):
        args = category_parser.parse_args()
        category = Category.query.filter_by(id=id).first()
        if not category:
            return {"message": "Category not found"}, 404
        category.name = args.get('name')
        category.active = args.get('active')
        category.request_action = args.get('request_action')
        db.session.commit()
        cache.delete("categories")
        return {"message": "Category updated"}, 200

class User_API(Resource):
    @auth_required("token")
    @roles_accepted("admin")
    def get(self, role):
        user = User.query.all()
        user = [user for user in user if user.has_role(role)]
        return [marshal(user, user_fields) for user in user], 200
    
    @auth_required("token")
    @roles_accepted("admin")
    def delete(self, id):
        user = User.query.filter_by(id=id).first()
        if not user:
            return {"message": "User not found"}, 404
        db.session.delete(user)
        db.session.commit()
        return {"message": "User deleted"}, 200

class Product_API(Resource):
    @cache.cached(9999, key_prefix="products")
    def get(self):
        from models import Products
        products = Products.query.all()
        product_list = []
        for product in products:
            product_data = {
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'quantity': product.quantity,
                'description': product.description,
                'category': product.category,
                'unit': product.unit,
                'expiry': product.expiry.date().strftime("%Y-%m-%d"),
                'created_at': product.created_at.date().strftime("%Y-%m-%d"),
                'updated_at': product.updated_at.date().strftime("%Y-%m-%d")
            }
            product_list.append(product_data)
        return product_list, 200
    
    @auth_required("token")
    @roles_accepted('manager', 'admin')
    def delete(self, id):
        product = Products.query.filter_by(id=id).first()
        if not product:
            return {"message": "Product not found"}, 404
        db.session.delete(product)
        db.session.commit()
        cache.delete("products")
        return {"message": "Product deleted"}, 200
    
    @auth_required("token")
    @roles_accepted('manager', 'admin')
    def put(self, id):
        args = product_parser.parse_args()
        product = Products.query.filter_by(id=id).first()
        if not product:
            return {"message": "Product not found"}, 404
        product.name = args['name']
        product.price = args['price']
        product.quantity = args['quantity']
        product.description = args['description']
        product.category = args['category']
        product.unit = args['unit']
        product.expiry = datetime.datetime.strptime(args['expiry'], "%Y-%m-%d")
        product.updated_at = datetime.datetime.strptime(datetime.datetime.now().strftime("%Y-%m-%d"),"%Y-%m-%d")
        db.session.commit()
        cache.delete("products")
        return {"message": "Product updated"}, 200
    
    @auth_required("token")
    @roles_accepted('manager', 'admin')
    def post(self):
        args = product_parser.parse_args()
        product = Products.query.filter_by(name = args.get('name')).first()
        if product:
            return {"message": "Product already exists"}, 400
        product = Products(name=args['name'], price=args['price'], quantity=args['quantity'], description=args['description'], category=args['category'], unit=args['unit'], expiry=datetime.datetime.strptime(args['expiry'], '%Y-%m-%d'), created_at=datetime.datetime.strptime(datetime.datetime.now().strftime("%Y-%m-%d"), "%Y-%m-%d"), updated_at=datetime.datetime.strptime(datetime.datetime.now().strftime("%Y-%m-%d"),"%Y-%m-%d"))
        db.session.add(product)
        db.session.commit()
        cache.delete("products")
        return {"message": "Product added"}, 201
    
class Cart_API(Resource):
    @auth_required("token")
    def get(self):
        cart = Cart.query.filter_by(user_id=current_user.id).first()
        return {"cart": (eval(cart.value))}, 200
    
    @auth_required("token")
    def post(self):
        args = cart_parser.parse_args()
        cart = Cart.query.filter_by(user_id=current_user.id).first()
        if cart:
            cart.value = str(args.get('cart'))
            db.session.commit()
            return {"message": "Cart updated"}, 200
        else:
            cart = Cart(user_id=current_user.id, value=str(args.get('cart')))
            db.session.add(cart)
            db.session.commit()
            return {"message": "Cart added"}, 201

class Units_API(Resource):
    @cache.cached(9999, key_prefix="units")
    def get(self):
        units = Unit.query.all()
        return [marshal(unit, unit_fields) for unit in units], 200
    
    @auth_required("token")
    @roles_accepted('manager', 'admin')
    def post(self):
        args = unit_parser.parse_args()
        unit = Unit.query.filter_by(name=args.get('name')).first()
        if unit:
            return {"message": "Unit already exists"}, 400
        unit = Unit(name=args['name'])
        db.session.add(unit)
        db.session.commit()
        cache.delete("units")
        return {"message": "Unit added"}, 201
    
    @auth_required("token")
    @roles_accepted('manager', 'admin')
    def delete(self, id):
        unit = Unit.query.filter_by(id=id).first()
        if not unit:
            return {"message": "Unit not found"}, 404
        db.session.delete(unit)
        db.session.commit()
        cache.delete("units")
        return {"message": "Unit deleted"}, 200
    
    @auth_required("token")
    @roles_accepted('manager', 'admin')
    def put(self, id):
        unit = Unit.query.filter_by(id=id).first()
        if not unit:
            return {"message": "Unit not found"}, 404
        args = unit_parser.parse_args()
        unit.name = args.get('name')
        db.session.commit()
        cache.delete("units")
        return {"message": "Unit updated"}, 200

class Order_API(Resource):
    @auth_required("token")
    def get(self):
        orders = Orders.query.filter_by(user_id=current_user.id).first()
        return {"order" : (eval(orders.value))}
    
    @auth_required("token")
    def post(self):
        args = cart_parser.parse_args()
        order = Orders(user_id=current_user.id, value=str(args.get('cart')), date=datetime.datetime.now())
        db.session.add(order)
        db.session.commit()
        cart = args.get('cart')
        for item in cart:
            product = Products.query.filter_by(id=item['id']).first()
            product.quantity -= item['qty']
            db.session.commit()
        return {"message": "Order has been placed."}, 201

api.add_resource(Category_API,"/category", "/category/<int:id>")
api.add_resource(User_API,"/user/<string:role>", "/user/<int:id>")
api.add_resource(Product_API,"/product", "/product/<int:id>")
api.add_resource(Cart_API,"/cart")
api.add_resource(Units_API,"/unit", "/unit/<int:id>")
api.add_resource(Order_API,"/order")

