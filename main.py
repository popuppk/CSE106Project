from flask import flash, Flask, jsonify, render_template, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
import os
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash



app = Flask(__name__, template_folder='templates')
login_manager = LoginManager(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///storage.db'
app.config['SECRET_KEY'] = 'adminkey'

login_manager.login_view = 'login'

db = SQLAlchemy(app)
admin = Admin(app, name='Admin Interface', template_mode='bootstrap3')


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    passwordhash = db.Column(db.String(100), nullable=False)

    def set_password(self, password):
        self.passwordhash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.passwordhash, password)
    def is_active(self):
        return (current_user.username == self.username)
    def get_id(self):
        return str(self.id)
    def is_authenticated(self):
        return True

class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userID = db.Column(db.Integer,db.ForeignKey('users.id'), nullable=False)
    itemName = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    restockmin = db.Column(db.Integer)
    description = db.Column(db.Text)
    def get_id(self):
        return str(self.id)

class SharedInventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ownersID = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sharedID = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    permissionLevel = db.Column(db.String(20), nullable=False)

class RestockInventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    itemID = db.Column(db.Integer, db.ForeignKey('inventory.id'), nullable=False)
    quantityNeeded = db.Column(db.Integer, nullable=False)
    dateAdded = db.Column(db.Date, nullable=False)
    Status = db.Column(db.String(20), nullable=False)



class UsersAdminView(ModelView):
    column_list = ['id', 'name', 'username', 'email']  
    can_create = True
    can_edit = True
    can_delete = True
    column_searchable_list = ['username', 'email'] 

class InventoryAdminView(ModelView):
    column_list = ['id', 'userID', 'itemName', 'quantity'] 
    can_create = True
    can_edit = True
    can_delete = True
    column_searchable_list = ['itemName']  

class SharedInventoryAdminView(ModelView):
    column_list = ['id', 'sharedUserID', 'itemID', 'permissionLevel']  
    can_create = True
    can_edit = True
    can_delete = True
    column_searchable_list = ['permissionLevel'] 

class RestockInventoryAdminView(ModelView):
    column_list = ['id', 'itemID', 'quantityNeeded', 'dateAdded', 'Status']  
    can_create = True
    can_edit = True
    can_delete = True
    column_searchable_list = ['Status'] 


admin.add_view(UsersAdminView(Users, db.session))
admin.add_view(InventoryAdminView(Inventory, db.session))
admin.add_view(SharedInventoryAdminView(SharedInventory, db.session))
admin.add_view(RestockInventoryAdminView(RestockInventory, db.session))


with app.app_context():
    db.create_all();


#login stuff:
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = Users.query.filter_by(username=username).first()

        if(username == "admin"):
            return redirect("/admin")
        

        if user and (user.check_password(password)):
            login_user(user)
            return render_template('index.html', username=current_user.username)
            
    return render_template('login.html')

@app.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        existing_user = Users.query.filter_by(username=username).first()

        if existing_user:
            flash('Username already exists')
        else:
            new_user = Users(username=username,email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('You have successfully registered')
            return redirect(url_for('login')) 
    return render_template('registration.html')


#Navigation stuff
@app.route('/')
def home():
    return render_template('login.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/inventory', methods=['GET', 'POST'])
def inventory():
    if request.method == 'POST':
        # Handle filtering and search logic
        item_name_filter = request.form.get('itemName')
        min_quantity_filter = request.form.get('minQuantity')

        # Query the inventory based on filters
        inventory_items = Inventory.query.filter(
            Inventory.itemName.ilike(f"%{item_name_filter}%"),
            Inventory.quantity >= min_quantity_filter if min_quantity_filter else True
        ).all()

        return render_template('inventory.html', inventory_items=inventory_items)

    # If it's a GET request, just render the inventory template
    return render_template('inventory.html')

@app.route('/sharedinv')
def shared_inventory():
    return render_template('index.html')

@app.route('/restock')
def restock():
    return render_template('index.html')

@app.route('/registration', methods=['Get'])
def registration():
    return render_template('registration.html')



#Data Getting:
@app.route('/getUserInventory', methods=['GET'])
def get_user_inventory():
    user_inventory = Inventory.query.filter_by(userID=current_user.id).all()

    if not user_inventory:
        return jsonify({'message': 'No inventory found for this user'}), 404

    inventory_list = []
    for item in user_inventory:
        inventory_list.append({
            'id': item.id,
            'itemName': item.itemName,
            'quantity': item.quantity,
            'restock': item.restockmin,
            'description': item.description
        })

    return jsonify({'user_inventory': inventory_list}), 200

#Data Setting:

@app.route('/add_row', methods=['POST'])
def add_row():
    print('data received')
    data = request.json
    newitem = Inventory(userID=current_user.id, itemName=data[2], quantity=int(data[3]), restockmin=int(data[4]), description=data[5])
    db.session.add(newitem)
    db.session.commit()
    print('data received')
    return 'Data received'

@app.route('/edit_row', methods=['PUT'])
def edit_row():
    data = request.json
    entry = Inventory.query.get(int(data[0]))

    entry.itemName = data[2]
    entry.quantity = int(data[3])
    entry.restockmin = int(data[4])
    entry.description = data[5]

    db.session.commit()

    return "Edit Complete"


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))



