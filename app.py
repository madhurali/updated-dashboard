from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Database initialization
def init_db():
    conn = sqlite3.connect('clinic.db')
    c = conn.cursor()
    
    # Create tables if they don't exist
    c.execute('''CREATE TABLE IF NOT EXISTS branches
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT NOT NULL,
                 address TEXT NOT NULL,
                 city TEXT NOT NULL,
                 state TEXT NOT NULL,
                 zip_code TEXT NOT NULL,
                 phone TEXT NOT NULL,
                 email TEXT,
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT NOT NULL,
                 description TEXT,
                 category TEXT NOT NULL,
                 unit_price REAL NOT NULL,
                 reorder_level INTEGER,
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS suppliers
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT NOT NULL,
                 contact_person TEXT,
                 phone TEXT NOT NULL,
                 email TEXT,
                 address TEXT,
                 products_supplied TEXT,
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS inventory
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 product_id INTEGER NOT NULL,
                 branch_id INTEGER NOT NULL,
                 quantity INTEGER NOT NULL,
                 last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                 FOREIGN KEY (product_id) REFERENCES products(id),
                 FOREIGN KEY (branch_id) REFERENCES branches(id))''')
    
    # Insert sample data if tables are empty
    if c.execute('SELECT COUNT(*) FROM branches').fetchone()[0] == 0:
        sample_branches = [
            ('Main Clinic', '123 Medical Ave', 'Boston', 'MA', '02115', '617-555-1000', 'main@clinic.com'),
            ('Downtown Branch', '456 Health St', 'Boston', 'MA', '02108', '617-555-2000', 'downtown@clinic.com'),
            ('Westside Clinic', '789 Wellness Blvd', 'Cambridge', 'MA', '02142', '617-555-3000', 'west@clinic.com')
        ]
        c.executemany('INSERT INTO branches (name, address, city, state, zip_code, phone, email) VALUES (?,?,?,?,?,?,?)', sample_branches)
    
    if c.execute('SELECT COUNT(*) FROM products').fetchone()[0] == 0:
        sample_products = [
            ('Bandages (Box of 100)', 'Sterile adhesive bandages, assorted sizes', 'First Aid', 12.99, 10),
            ('Disposable Gloves (Box of 100)', 'Latex-free examination gloves', 'Protective Equipment', 8.50, 15),
            ('Antiseptic Wipes (Pack of 50)', 'Alcohol-based cleaning wipes', 'First Aid', 5.25, 20),
            ('Face Masks (Box of 50)', 'Surgical-grade disposable masks', 'Protective Equipment', 14.99, 8),
            ('Thermometer (Digital)', 'Fast-reading digital thermometer', 'Diagnostic Equipment', 22.75, 5),
            ('Blood Pressure Monitor', 'Automatic arm blood pressure cuff', 'Diagnostic Equipment', 89.99, 3),
            ('Cotton Swabs (Pack of 200)', 'Sterile cotton swabs', 'Medical Supplies', 3.99, 25),
            ('Gauze Pads (Box of 100)', 'Sterile gauze pads, 4x4 inches', 'Wound Care', 9.95, 12)
        ]
        c.executemany('INSERT INTO products (name, description, category, unit_price, reorder_level) VALUES (?,?,?,?,?)', sample_products)
    
    if c.execute('SELECT COUNT(*) FROM suppliers').fetchone()[0] == 0:
        sample_suppliers = [
            ('MedSupply Co.', 'John Smith', '800-555-1000', 'sales@medsupply.com', '123 Supplier Lane, Boston, MA', 'Bandages, Gloves, Wipes'),
            ('HealthCare Distributors', 'Sarah Johnson', '800-555-2000', 'info@hcdist.com', '456 Medical Drive, Cambridge, MA', 'Masks, Thermometers'),
            ('First Aid Unlimited', 'Mike Brown', '800-555-3000', 'sales@firstaidunltd.com', '789 Emergency Way, Somerville, MA', 'Gauze, Swabs, Bandages'),
            ('Diagnostic Solutions', 'Emily Davis', '800-555-4000', 'support@diagnostics.com', '321 Test Street, Boston, MA', 'BP Monitors, Thermometers')
        ]
        c.executemany('INSERT INTO suppliers (name, contact_person, phone, email, address, products_supplied) VALUES (?,?,?,?,?,?)', sample_suppliers)
    
    if c.execute('SELECT COUNT(*) FROM inventory').fetchone()[0] == 0:
        sample_inventory = [
            (1, 1, 25), (2, 1, 30), (3, 1, 40), (4, 1, 15),
            (5, 1, 8), (6, 1, 4), (7, 1, 50), (8, 1, 30),
            (1, 2, 15), (2, 2, 20), (3, 2, 25), (4, 2, 10),
            (5, 2, 5), (7, 2, 30), (8, 2, 20),
            (1, 3, 20), (2, 3, 25), (3, 3, 30), (4, 3, 12),
            (6, 3, 3), (7, 3, 40), (8, 3, 25)
        ]
        c.executemany('INSERT INTO inventory (product_id, branch_id, quantity) VALUES (?,?,?)', sample_inventory)
    
    conn.commit()
    conn.close()

init_db()

# Helper function to get database connection
def get_db():
    conn = sqlite3.connect('clinic.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def dashboard():
    conn = get_db()
    
    # Get counts for dashboard
    branch_count = conn.execute('SELECT COUNT(*) FROM branches').fetchone()[0]
    product_count = conn.execute('SELECT COUNT(*) FROM products').fetchone()[0]
    supplier_count = conn.execute('SELECT COUNT(*) FROM suppliers').fetchone()[0]
    
    # Get low inventory items
    low_inventory = conn.execute('''
        SELECT p.name, i.quantity, p.reorder_level, b.name as branch_name
        FROM inventory i
        JOIN products p ON i.product_id = p.id
        JOIN branches b ON i.branch_id = b.id
        WHERE i.quantity <= p.reorder_level
        ORDER BY i.quantity ASC
        LIMIT 5
    ''').fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', 
                         branch_count=branch_count,
                         product_count=product_count,
                         supplier_count=supplier_count,
                         low_inventory=low_inventory)

# Branches routes
@app.route('/branches')
def branches():
    conn = get_db()
    branches = conn.execute('SELECT * FROM branches ORDER BY name').fetchall()
    conn.close()
    return render_template('branches.html', branches=branches)

@app.route('/branches/add', methods=['POST'])
def add_branch():
    name = request.form['name']
    address = request.form['address']
    city = request.form['city']
    state = request.form['state']
    zip_code = request.form['zip_code']
    phone = request.form['phone']
    email = request.form['email']
    
    conn = get_db()
    conn.execute('''
        INSERT INTO branches (name, address, city, state, zip_code, phone, email)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (name, address, city, state, zip_code, phone, email))
    conn.commit()
    conn.close()
    
    return redirect(url_for('branches'))

@app.route('/branches/delete/<int:id>')
def delete_branch(id):
    conn = get_db()
    conn.execute('DELETE FROM branches WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('branches'))

# Products routes
@app.route('/products')
def products():
    conn = get_db()
    products = conn.execute('SELECT * FROM products ORDER BY name').fetchall()
    conn.close()
    return render_template('products.html', products=products)

@app.route('/products/add', methods=['POST'])
def add_product():
    name = request.form['name']
    description = request.form['description']
    category = request.form['category']
    unit_price = float(request.form['unit_price'])
    reorder_level = int(request.form['reorder_level'])
    
    conn = get_db()
    conn.execute('''
        INSERT INTO products (name, description, category, unit_price, reorder_level)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, description, category, unit_price, reorder_level))
    conn.commit()
    conn.close()
    
    return redirect(url_for('products'))

@app.route('/products/delete/<int:id>')
def delete_product(id):
    conn = get_db()
    conn.execute('DELETE FROM products WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('products'))

# Suppliers routes
@app.route('/suppliers')
def suppliers():
    conn = get_db()
    suppliers = conn.execute('SELECT * FROM suppliers ORDER BY name').fetchall()
    conn.close()
    return render_template('suppliers.html', suppliers=suppliers)

@app.route('/suppliers/add', methods=['POST'])
def add_supplier():
    name = request.form['name']
    contact_person = request.form['contact_person']
    phone = request.form['phone']
    email = request.form['email']
    address = request.form['address']
    products_supplied = request.form['products_supplied']
    
    conn = get_db()
    conn.execute('''
        INSERT INTO suppliers (name, contact_person, phone, email, address, products_supplied)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (name, contact_person, phone, email, address, products_supplied))
    conn.commit()
    conn.close()
    
    return redirect(url_for('suppliers'))

@app.route('/suppliers/delete/<int:id>')
def delete_supplier(id):
    conn = get_db()
    conn.execute('DELETE FROM suppliers WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('suppliers'))

# Inventory routes
@app.route('/inventory')
def inventory():
    conn = get_db()
    
    # Get inventory with product and branch details
    inventory = conn.execute('''
        SELECT i.id, p.name as product_name, b.name as branch_name, 
               i.quantity, p.reorder_level, p.unit_price,
               (i.quantity * p.unit_price) as total_value
        FROM inventory i
        JOIN products p ON i.product_id = p.id
        JOIN branches b ON i.branch_id = b.id
        ORDER BY b.name, p.name
    ''').fetchall()
    
    products = conn.execute('SELECT id, name FROM products ORDER BY name').fetchall()
    branches = conn.execute('SELECT id, name FROM branches ORDER BY name').fetchall()
    
    conn.close()
    
    return render_template('inventory.html', 
                         inventory=inventory,
                         products=products,
                         branches=branches)

@app.route('/inventory/add', methods=['POST'])
def add_inventory():
    product_id = int(request.form['product_id'])
    branch_id = int(request.form['branch_id'])
    quantity = int(request.form['quantity'])
    
    conn = get_db()
    
    # Check if inventory item already exists
    existing = conn.execute('''
        SELECT id FROM inventory 
        WHERE product_id = ? AND branch_id = ?
    ''', (product_id, branch_id)).fetchone()
    
    if existing:
        # Update existing inventory
        conn.execute('''
            UPDATE inventory 
            SET quantity = quantity + ?
            WHERE id = ?
        ''', (quantity, existing['id']))
    else:
        # Add new inventory item
        conn.execute('''
            INSERT INTO inventory (product_id, branch_id, quantity)
            VALUES (?, ?, ?)
        ''', (product_id, branch_id, quantity))
    
    conn.commit()
    conn.close()
    
    return redirect(url_for('inventory'))

@app.route('/inventory/update/<int:id>', methods=['POST'])
def update_inventory(id):
    quantity = int(request.form['quantity'])
    
    conn = get_db()
    conn.execute('UPDATE inventory SET quantity = ? WHERE id = ?', (quantity, id))
    conn.commit()
    conn.close()
    
    return redirect(url_for('inventory'))

@app.route('/inventory/delete/<int:id>')
def delete_inventory(id):
    conn = get_db()
    conn.execute('DELETE FROM inventory WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('inventory'))

# API routes for AJAX calls
@app.route('/api/inventory/<int:branch_id>/<int:product_id>')
def get_inventory(branch_id, product_id):
    conn = get_db()
    item = conn.execute('''
        SELECT i.quantity 
        FROM inventory i
        WHERE i.branch_id = ? AND i.product_id = ?
    ''', (branch_id, product_id)).fetchone()
    
    quantity = item['quantity'] if item else 0
    conn.close()
    
    return jsonify({'quantity': quantity})

if __name__ == '__main__':
    app.run(debug=True)