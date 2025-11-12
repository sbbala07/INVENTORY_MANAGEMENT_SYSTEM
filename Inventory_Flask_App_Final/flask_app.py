import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime


APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(APP_DIR, "inventory.json")

app = Flask(__name__)
app.secret_key = "replace_with_secure_secret"  # keep as-is for local dev
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

LOW_STOCK_THRESHOLD = 5

# ----------------- persistence helpers -----------------
def load_inventory():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}
    # normalize older schemas if any
    for k, v in list(data.items()):
        if "quantity" not in v and "qty" in v:
            v["quantity"] = v.pop("qty")
    return data

def save_inventory(inv):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(inv, f, indent=4)

# ----------------- utility -----------------
def build_ref_map(inv):
    # returns dict mapping ref_str -> item_id (enumeration)
    return {str(i): item_id for i, item_id in enumerate(inv.keys(), start=1)}

# ----------------- routes -----------------
@app.route("/")
def index():
    inv = load_inventory()
    q = request.args.get("q", "").strip()
    filtered = inv
    if q:
        k = q.lower()
        filtered = {iid: d for iid, d in inv.items() 
                    if k in iid.lower() or k in d["name"].lower()}
    return render_template("index.html", inventory=filtered, q=q, low_threshold=LOW_STOCK_THRESHOLD)

# Add
@app.route("/add", methods=["GET", "POST"])
def add_item():
    inv = load_inventory()
    if request.method == "POST":
        iid = request.form.get("item_id","").strip().upper()
        name = request.form.get("name","").strip().title()
        qty = request.form.get("quantity","").strip()
        price = request.form.get("price","").strip()
        # validation
        if not iid or not name or qty == "" or price == "":
            flash("Item ID, Name, Quantity and Price are required.", "danger")
            return redirect(url_for("add_item"))
        try:
            qty = int(qty)
            price = float(price)
        except ValueError:
            flash("Quantity must be integer and Price must be numeric.", "danger")
            return redirect(url_for("add_item"))
        if qty < 0 or price < 0:
            flash("Quantity and Price must be non-negative.", "danger")
            return redirect(url_for("add_item"))
        if iid in inv:
            flash("Item ID already exists.", "warning")
            return redirect(url_for("add_item"))
        inv[iid] = {"name": name, "quantity": qty, "price": price}
        save_inventory(inv)
        flash(f"Item '{name}' added.", "success")
        return redirect(url_for("index"))
    return render_template("add.html")

# Update (select item by id in form or go to /update/<item_id> for prefilled)
@app.route("/update", methods=["GET","POST"])
def update_item():
    inv = load_inventory()
    if request.method == "POST":
        iid = request.form.get("item_id_select","").strip().upper()
        if iid not in inv:
            flash("Item ID not found.", "danger")
            return redirect(url_for("update_item"))
        details = inv[iid]
        # values
        new_name = request.form.get("name","").strip()
        qty_txt = request.form.get("quantity","").strip()
        qty_mode = request.form.get("qty_mode","Replace")
        price_txt = request.form.get("price","").strip()
        price_mode = request.form.get("price_mode","Replace")
        if new_name:
            details["name"] = new_name.title()
        if qty_txt:
            try:
                qnum = int(qty_txt)
                if qty_mode == "Add":
                    details["quantity"] = details.get("quantity",0) + qnum
                else:
                    details["quantity"] = qnum
            except ValueError:
                flash("Invalid quantity; skipping quantity update.", "warning")
        if price_txt:
            try:
                pnum = float(price_txt)
                if price_mode == "Add":
                    details["price"] = details.get("price",0.0) + pnum
                else:
                    details["price"] = pnum
            except ValueError:
                flash("Invalid price; skipping price update.", "warning")
        inv[iid] = details
        save_inventory(inv)
        flash(f"Item '{iid} - {details['name']}' updated.", "success")
        return redirect(url_for("index"))
    # GET
    return render_template("update.html", inventory=inv)

# Delete (full or partial)
@app.route("/delete", methods=["GET","POST"])
def delete_item():
    inv = load_inventory()
    if request.method == "POST":
        iid = request.form.get("item_id_select","").strip().upper()
        if iid not in inv:
            flash("Item ID not found.", "danger")
            return redirect(url_for("delete_item"))
        details = inv[iid]
        mode = request.form.get("delete_mode","full")
        if mode == "full":
            del inv[iid]
            save_inventory(inv)
            flash(f"Item '{details['name']}' deleted.", "success")
            return redirect(url_for("index"))
        else:
            # partial
            qty_txt = request.form.get("partial_qty","").strip()
            if not qty_txt:
                flash("Please enter quantity to remove.", "warning")
                return redirect(url_for("delete_item"))
            try:
                q = int(qty_txt)
            except ValueError:
                flash("Invalid quantity.", "danger")
                return redirect(url_for("delete_item"))
            if q >= details.get("quantity",0):
                # confirm full delete fallback
                del inv[iid]
                save_inventory(inv)
                flash(f"Quantity removed >= stock. Entire item '{details['name']}' deleted.", "info")
                return redirect(url_for("index"))
            details["quantity"] = details.get("quantity",0) - q
            inv[iid] = details
            save_inventory(inv)
            flash(f"Removed {q} units from '{details['name']}'. New qty: {details['quantity']}.", "success")
            return redirect(url_for("index"))
    return render_template("delete.html", inventory=inv)

# Catalogue
@app.route("/catalogue")
def catalogue():
    inv = load_inventory()
    # sorted by name
    items = sorted(inv.items(), key=lambda x: x[1]["name"].lower())
    return render_template("catalogue.html", items=items)

# Low stock
@app.route("/low_stock")
def low_stock():
    inv = load_inventory()
    low = {iid: d for iid, d in inv.items() if d.get("quantity",0) < LOW_STOCK_THRESHOLD}
    return render_template("low_stock.html", inventory=low, threshold=LOW_STOCK_THRESHOLD)

# Search handled via index GET param; provide explicit page too
@app.route("/search", methods=["GET","POST"])
def search():
    inv = load_inventory()
    results = {}
    if request.method == "POST":
        term = request.form.get("term","").strip().lower()
        if term:
            results = {iid: d for iid, d in inv.items() if term == iid.lower() or term in d["name"].lower()}
        if not results:
            flash("No matching items found.", "warning")
    return render_template("search.html", results=results)

# Purchase flow: ref map + cart in session
@app.route("/purchase", methods=["GET"])
def purchase():
    inv = load_inventory()
    # Apply temporary 'reservation' to inventory displayed in the purchase view
    temp_inv = inv.copy()
    cart = session.get("cart", {})
    
    # Apply cart quantities to 'temp_inv' for display 
    # The 'actual' inventory (inv) is NOT modified here.
    for iid, d in cart.items():
        if iid in temp_inv:
            # Subtract the cart quantity from the temporary inventory copy
            temp_inv[iid]["quantity"] = temp_inv[iid].get("quantity", 0) - d.get("quantity", 0)

    ref_map = build_ref_map(temp_inv) # Build map using temporary inventory
    
    return render_template("purchase.html", inv=temp_inv, ref_map=ref_map, cart=cart)
    # The purchase view now shows quantities *as if* the cart items are reserved.
    # The main 'inv' object is untouched until checkout.

@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    inv = load_inventory()
    ref = request.form.get("ref","").strip()
    qty_txt = request.form.get("qty","").strip()
    ref_map = build_ref_map(inv) # Use main inventory for initial lookup
    
    if ref not in ref_map:
        flash("Invalid ref number.", "danger")
        return redirect(url_for("purchase"))
    
    iid = ref_map[ref]
    
    try:
        qty = int(qty_txt)
    except ValueError:
        flash("Invalid quantity.", "danger")
        return redirect(url_for("purchase"))
    
    # Check current inventory + existing cart quantity to prevent over-selling
    current_stock = inv[iid].get("quantity", 0)
    cart = session.get("cart", {})
    in_cart = cart.get(iid, {}).get("quantity", 0)
    available_stock = current_stock - in_cart

    if qty <= 0 or qty > available_stock:
        flash(f"Qty must be 1 - {available_stock}. Current stock is {current_stock}, {in_cart} in cart.", "danger")
        return redirect(url_for("purchase"))
    
    # DO NOT touch inventory here (No save_inventory(inv)) 
    # Removed: item["quantity"] -= qty
    # Removed: inv[iid] = item
    # Removed: save_inventory(inv)
    
    # Add to session cart (dict keyed by iid)
    item_details = inv[iid]
    if iid in cart:
        cart[iid]["quantity"] += qty
    else:
        cart[iid] = {"name": item_details["name"], "price": item_details["price"], "quantity": qty}
        
    session["cart"] = cart
    flash(f"Added {qty} x {item_details['name']} to cart. Stock reserved in purchase view.", "success")
    return redirect(url_for("purchase"))

@app.route("/clear_cart", methods=["POST"])
def clear_cart():
    # Inventory restoration is no longer needed
    # The actual inventory was never modified!
    session.pop("cart", {})
    # Removed: inventory restoration logic
    # Removed: save_inventory(inv)
    
    flash("Cart cleared.", "info")
    return redirect(url_for("purchase"))

@app.route("/cancel_purchase")
def cancel_purchase():
    """Clears the session cart and redirects to the main inventory view."""
    if session.get("cart"):
        session.pop("cart", None)
        flash("Purchase cancelled and cart cleared.", "info")
    return redirect(url_for("index"))

@app.route("/checkout", methods=["POST"])
def checkout():
    inv = load_inventory() # Load inventory just before final deduction
    cart = session.get("cart", {})
    
    if not cart:
        flash("Cart is empty.", "warning")
        return redirect(url_for("purchase"))

    # DEDUCT inventory ONLY at checkout
    for iid, d in cart.items():
        qty_to_deduct = d.get("quantity", 0)
        
        # Double-check stock just in case
        if iid in inv and inv[iid].get("quantity", 0) >= qty_to_deduct:
            inv[iid]["quantity"] -= qty_to_deduct
        else:
            # This should ideally not happen if add_to_cart check works
            flash(f"Error: Not enough stock for {d['name']} at checkout. Purchase cancelled.", "danger")
            # Clear cart anyway, but don't save inventory changes
            session.pop("cart", None)
            return redirect(url_for("purchase"))
            
    # Save the DEDUCTED inventory
    save_inventory(inv)
    

    total = 0.0
    lines = []
    for iid, d in cart.items():
        subtotal = d["quantity"] * d["price"]
        total += subtotal
        lines.append({
            "id": iid,
            "name": d["name"],
            "qty": d["quantity"],
            "price": d["price"],
            "subtotal": subtotal
        })

    # Generate current timestamp
    current_time = datetime.now().strftime("%d-%b-%Y %I:%M %p")

    # Clear cart after data is passed
    session.pop("cart", None)

    return render_template(
        "bill.html",
        cart=lines,
        total=total,
        date=current_time
    )

# ----------------- run -----------------
if __name__ == "__main__":
    # create inventory file if not present
    if not os.path.exists(DATA_FILE):
        save_inventory({})
    app.run(debug=True)