import os
import json
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

FILE_NAME = "inventory.json"

# --------------------------
# Load / Save (same as CLI)
# --------------------------
def load_inventory():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_inventory():
    with open(FILE_NAME, "w") as f:
        json.dump(inventory, f, indent=4)

# Load global inventory
inventory = load_inventory()

# --------------------------
# Tkinter App
# --------------------------
class InventoryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Inventory Management System - GUI")
        self.geometry("820x520")
        self.resizable(False, False)
        self.create_widgets()
        self.populate_tree()

    def create_widgets(self):
        # Treeview frame
        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=False, padx=10, pady=8)

        cols = ("Item_ID", "Name", "Quantity", "Price")
        self.tree = ttk.Treeview(frm, columns=cols, show="headings", height=15)
        for c in cols:
            self.tree.heading(c, text=c)
            # set column widths
        self.tree.column("Item_ID", width=100, anchor="w")
        self.tree.column("Name", width=300, anchor="w")
        self.tree.column("Quantity", width=120, anchor="center")
        self.tree.column("Price", width=120, anchor="e")

        vsb = ttk.Scrollbar(frm, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        # Buttons frame
        btn_frm = ttk.Frame(self)
        btn_frm.pack(fill="x", padx=10, pady=6)

        ttk.Button(btn_frm, text="Add Item", command=self.add_item_window).grid(row=0, column=0, padx=6)
        ttk.Button(btn_frm, text="Update Item", command=self.update_item_window).grid(row=0, column=1, padx=6)
        ttk.Button(btn_frm, text="Delete Item", command=self.delete_item).grid(row=0, column=2, padx=6)
        ttk.Button(btn_frm, text="Refresh", command=self.populate_tree).grid(row=0, column=3, padx=6)
        ttk.Button(btn_frm, text="Show Catalog", command=self.show_catalog).grid(row=0, column=4, padx=6)
        ttk.Button(btn_frm, text="Purchase (Ref map)", command=self.purchase_with_ref).grid(row=0, column=5, padx=6)
        ttk.Button(btn_frm, text="Exit", command=self.on_exit).grid(row=0, column=6, padx=6)

        # Search box
        search_frm = ttk.Frame(self)
        search_frm.pack(fill="x", padx=10, pady=(0,8))
        ttk.Label(search_frm, text="Search (ID or name):").pack(side="left")
        self.search_var = tk.StringVar()
        ttk.Entry(search_frm, textvariable=self.search_var, width=30).pack(side="left", padx=6)
        ttk.Button(search_frm, text="Search", command=self.search_items).pack(side="left", padx=6)
        ttk.Button(search_frm, text="Clear Search", command=self.populate_tree).pack(side="left", padx=6)

    # Populate treeview from inventory
    def populate_tree(self, filter_keyword=None):
        for item in self.tree.get_children():
            self.tree.delete(item)
        items = inventory.items()
        if filter_keyword:
            k = filter_keyword.lower()
            items = [it for it in inventory.items() if k == it[0].lower() or k in it[1]['name'].lower()]
        for item_id, details in items:
            self.tree.insert("", "end", iid=item_id, values=(
                item_id,
                details['name'],
                details['quantity'],
                f"{details['price']:.2f}"
            ))

    def get_selected_item(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select item", "Please select an item from the list first.")
            return None
        return sel[0]

    # --------------------------
    # Add Item Window
    # --------------------------
    def add_item_window(self):
        win = tk.Toplevel(self)
        win.title("Add Item")
        win.geometry("360x220")
        ttk.Label(win, text="Item ID (e.g. A101):").pack(anchor="w", padx=10, pady=(10,0))
        id_entry = ttk.Entry(win)
        id_entry.pack(fill="x", padx=10)

        ttk.Label(win, text="Name:").pack(anchor="w", padx=10, pady=(8,0))
        name_entry = ttk.Entry(win)
        name_entry.pack(fill="x", padx=10)

        ttk.Label(win, text="Quantity:").pack(anchor="w", padx=10, pady=(8,0))
        qty_entry = ttk.Entry(win)
        qty_entry.pack(fill="x", padx=10)

        ttk.Label(win, text="Price:").pack(anchor="w", padx=10, pady=(8,0))
        price_entry = ttk.Entry(win)
        price_entry.pack(fill="x", padx=10)

        def on_submit():
            iid = id_entry.get().strip().upper()
            if not iid:
                messagebox.showerror("Error", "Item ID required")
                return
            if iid in inventory:
                messagebox.showerror("Error", "Item ID already exists")
                return
            name = name_entry.get().strip().title()
            try:
                q = int(qty_entry.get().strip())
                p = float(price_entry.get().strip())
            except Exception:
                messagebox.showerror("Error", "Quantity must be integer and price must be number")
                return
            if q < 0 or p < 0:
                messagebox.showerror("Error", "Quantity and price must be non-negative")
                return
            inventory[iid] = {"name": name, "quantity": q, "price": p}
            save_inventory()
            self.populate_tree()
            messagebox.showinfo("Success", f"Item {name} added.")
            win.destroy()

        ttk.Button(win, text="Add", command=on_submit).pack(pady=12)

    # --------------------------
    # Update Item Window
    # --------------------------
    def update_item_window(self):
        sel = self.get_selected_item()
        if not sel:
            return
        item_id = sel
        details = inventory[item_id]

        win = tk.Toplevel(self)
        win.title(f"Update {item_id}")
        win.geometry("380x300")

        ttk.Label(win, text=f"Updating: {item_id}").pack(anchor="w", padx=10, pady=(8,0))

        ttk.Label(win, text="Name (leave blank to keep):").pack(anchor="w", padx=10, pady=(6,0))
        name_entry = ttk.Entry(win)
        name_entry.insert(0, details['name'])
        name_entry.pack(fill="x", padx=10)

        # Quantity
        ttk.Label(win, text="Quantity (leave blank to keep):").pack(anchor="w", padx=10, pady=(6,0))
        qty_entry = ttk.Entry(win)
        qty_entry.pack(fill="x", padx=10)
        qty_mode = tk.StringVar(value="Replace")
        ttk.Label(win, text="Quantity mode:").pack(anchor="w", padx=10, pady=(6,0))
        ttk.OptionMenu(win, qty_mode, "Replace", "Replace", "Add").pack(anchor="w", padx=10)

        # Price
        ttk.Label(win, text="Price (leave blank to keep):").pack(anchor="w", padx=10, pady=(6,0))
        price_entry = ttk.Entry(win)
        price_entry.pack(fill="x", padx=10)
        price_mode = tk.StringVar(value="Replace")
        ttk.Label(win, text="Price mode:").pack(anchor="w", padx=10, pady=(6,0))
        ttk.OptionMenu(win, price_mode, "Replace", "Replace", "Add").pack(anchor="w", padx=10)

        def on_update():
            name_val = name_entry.get().strip()
            if name_val:
                details['name'] = name_val.title()

            qtxt = qty_entry.get().strip()
            if qtxt:
                try:
                    qnum = int(qtxt)
                    if qty_mode.get() == "Add":
                        details['quantity'] += qnum
                    else:
                        details['quantity'] = qnum
                except ValueError:
                    messagebox.showwarning("Warning", "Invalid quantity; skipping quantity update.")

            ptxt = price_entry.get().strip()
            if ptxt:
                try:
                    pnum = float(ptxt)
                    if price_mode.get() == "Add":
                        details['price'] += pnum
                    else:
                        details['price'] = pnum
                except ValueError:
                    messagebox.showwarning("Warning", "Invalid price; skipping price update.")

            inventory[item_id] = details
            save_inventory()
            self.populate_tree()
            messagebox.showinfo("Success", f"Item {item_id} updated.")
            win.destroy()

        ttk.Button(win, text="Update", command=on_update).pack(pady=10)

    # --------------------------
    # Delete Item
    # --------------------------
    def delete_item(self):
        sel = self.get_selected_item()
        if not sel:
            return
        item_id = sel
        details = inventory[item_id]
        # Full delete confirmation
        if messagebox.askyesno("Confirm Delete", f"Do you want to DELETE the entire item {item_id} ({details['name']})?"):
            del inventory[item_id]
            save_inventory()
            self.populate_tree()
            messagebox.showinfo("Deleted", "Item deleted.")
            return

        # Otherwise ask for partial quantity delete
        qty = simpledialog.askinteger("Delete Quantity", f"Enter quantity to remove (1-{details['quantity']}):",
                                      minvalue=1, maxvalue=details['quantity'])
        if qty is None:
            return
        if qty >= details['quantity']:
            if messagebox.askyesno("Confirm", "Requested quantity >= stock. Delete entire item instead?"):
                del inventory[item_id]
                save_inventory()
                self.populate_tree()
                messagebox.showinfo("Deleted", "Entire item deleted.")
                return
            else:
                messagebox.showinfo("Cancelled", "Deletion cancelled.")
                return
        details['quantity'] -= qty
        inventory[item_id] = details
        save_inventory()
        self.populate_tree()
        messagebox.showinfo("Updated", f"{qty} units removed. New qty: {details['quantity']}")

    # --------------------------
    # Show Catalog (no quantity)
    # --------------------------
    def show_catalog(self):
        win = tk.Toplevel(self)
        win.title("Product Catalog")
        win.geometry("480x320")
        cols = ("Item_ID", "Name", "Price")
        tv = ttk.Treeview(win, columns=cols, show="headings", height=15)
        for c in cols:
            tv.heading(c, text=c)
        tv.column("Item_ID", width=100)
        tv.column("Name", width=240)
        tv.column("Price", width=100, anchor="e")
        tv.pack(fill="both", expand=True, padx=8, pady=8)
        for item_id, details in sorted(inventory.items(), key=lambda x: x[1]['name']):
            tv.insert("", "end", values=(item_id, details['name'], f"{details['price']:.2f}"))

    # --------------------------
    # Search
    # --------------------------
    def search_items(self):
        kw = self.search_var.get().strip()
        if not kw:
            self.populate_tree()
            return
        self.populate_tree(filter_keyword=kw)

    # --------------------------
    # Purchase with Ref numbers (simple)
    # --------------------------
    def purchase_with_ref(self):
        # We'll reuse the CLI-style ref map but in a small window.
        win = tk.Toplevel(self)
        win.title("Purchase (Ref Map)")
        win.geometry("620x420")

        # Tree showing refs
        tv = ttk.Treeview(win, columns=("Ref", "Item_ID", "Name", "Price", "Stock"), show="headings")
        for h, w in [("Ref",50), ("Item_ID",100), ("Name",250), ("Price",80), ("Stock",80)]:
            tv.heading(h, text=h)
            tv.column(h, width=w, anchor="w")
        tv.pack(fill="both", expand=False, padx=8, pady=8)

        ref_map = {}
        for idx, (item_id, details) in enumerate(inventory.items(), start=1):
            ref_map[str(idx)] = item_id
            tv.insert("", "end", values=(idx, item_id, details['name'], f"{details['price']:.2f}", details['quantity']))

        cart = {}

        # Controls
        ctrl_frm = ttk.Frame(win)
        ctrl_frm.pack(fill="x", padx=8, pady=6)
        ttk.Label(ctrl_frm, text="Enter Ref number:").grid(row=0, column=0, padx=4, pady=4)
        ref_ent = ttk.Entry(ctrl_frm, width=8)
        ref_ent.grid(row=0, column=1, padx=4, pady=4)
        ttk.Label(ctrl_frm, text="Qty:").grid(row=0, column=2, padx=4)
        qty_ent = ttk.Entry(ctrl_frm, width=8)
        qty_ent.grid(row=0, column=3, padx=4)

        cart_listbox = tk.Listbox(win, height=6)
        cart_listbox.pack(fill="both", expand=False, padx=8, pady=(0,8))

        def add_to_cart():
            r = ref_ent.get().strip()
            if r not in ref_map:
                messagebox.showerror("Error", "Invalid ref number.")
                return
            iid = ref_map[r]
            try:
                q = int(qty_ent.get().strip())
            except Exception:
                messagebox.showerror("Error", "Invalid qty.")
                return
            if q <= 0 or q > inventory[iid]['quantity']:
                messagebox.showerror("Error", f"Qty must be 1 - {inventory[iid]['quantity']}")
                return
            if iid in cart:
                cart[iid]['quantity'] += q
            else:
                cart[iid] = {"name": inventory[iid]['name'], "price": inventory[iid]['price'], "quantity": q}
            inventory[iid]['quantity'] -= q
            save_inventory()
            self.populate_tree()
            cart_listbox.insert("end", f"{iid} | {cart[iid]['name']} x {cart[iid]['quantity']}")
            messagebox.showinfo("Added", f"Added {q} x {inventory[iid]['name']} to cart.")

        def checkout():
            if not cart:
                messagebox.showinfo("Cart empty", "No items in cart.")
                return
            # print simple bill window
            bill_win = tk.Toplevel(win)
            bill_win.title("Final Bill")
            bill_win.geometry("480x320")
            txt = tk.Text(bill_win)
            txt.pack(fill="both", expand=True)
            total = 0
            txt.insert("end", "FINAL BILL\n\n")
            txt.insert("end", f"{'Item':<20}{'Qty':<8}{'Price':<10}{'Subtotal':<10}\n")
            txt.insert("end", "-"*48 + "\n")
            for iid, d in cart.items():
                subtotal = d['quantity'] * d['price']
                total += subtotal
                txt.insert("end", f"{d['name']:<20}{d['quantity']:<8}{d['price']:<10}{subtotal:<10}\n")
            txt.insert("end", "-"*48 + "\n")
            txt.insert("end", f"TOTAL: {total}\n")
            # clear cart after checkout
            cart.clear()
            cart_listbox.delete(0, "end")
            messagebox.showinfo("Checkout", "Purchase completed. Inventory updated.")

        ttk.Button(ctrl_frm, text="Add to cart", command=add_to_cart).grid(row=0, column=4, padx=6)
        ttk.Button(ctrl_frm, text="Checkout", command=checkout).grid(row=0, column=5, padx=6)

    def on_exit(self):
        save_inventory()
        self.destroy()


if __name__ == "__main__":
    app = InventoryApp()
    app.mainloop()
