import os
import json
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

FILE_NAME = "inventory.json"

# --------------------------
# Load / Save
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

# Global inventory
inventory = load_inventory()

# --------------------------
# Tkinter App
# --------------------------
class InventoryApp(tk.Tk):
    LOW_STOCK_THRESHOLD = 5  # for low stock alert

    def __init__(self):
        super().__init__()
        self.title("Inventory Management System - GUI")
        self.geometry("900x550")
        self.resizable(False, False)
        self.create_widgets()
        self.populate_tree()

    # --------------------------
    # Widgets
    # --------------------------
    def create_widgets(self):
        # Treeview frame
        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=False, padx=10, pady=8)

        cols = ("Item_ID", "Name", "Quantity", "Price")
        self.tree = ttk.Treeview(frm, columns=cols, show="headings", height=15)
        for c in cols:
            self.tree.heading(c, text=c)
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
        ttk.Button(btn_frm, text="Low Stock Items", command=self.low_stock_items).grid(row=0, column=5, padx=6)
        ttk.Button(btn_frm, text="Purchase (Ref map)", command=self.purchase_with_ref).grid(row=0, column=6, padx=6)
        ttk.Button(btn_frm, text="Exit", command=self.on_exit).grid(row=0, column=7, padx=6)

        # Search box
        search_frm = ttk.Frame(self)
        search_frm.pack(fill="x", padx=10, pady=(0,8))
        ttk.Label(search_frm, text="Search (ID or name):").pack(side="left")
        self.search_var = tk.StringVar()
        ttk.Entry(search_frm, textvariable=self.search_var, width=30).pack(side="left", padx=6)
        ttk.Button(search_frm, text="Search", command=self.search_items).pack(side="left", padx=6)
        ttk.Button(search_frm, text="Refresh", command=self.populate_tree).pack(side="left", padx=6)

    # --------------------------
    # Treeview populate
    # --------------------------
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
    # Add Item
    # --------------------------
    def add_item_window(self):
        win = tk.Toplevel(self)
        win.title("Add Item")
        win.geometry("360x250")
        win.transient(self)
        win.grab_set()
        win.focus_force()
        self.center_window(win, 360, 250)

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
            name = name_entry.get().strip().title()
            try:
                q = int(qty_entry.get().strip())
                p = float(price_entry.get().strip())
            except Exception:
                messagebox.showerror("Error", "Quantity must be integer and price must be number", parent=win)
                return
            if not iid or not name:
                messagebox.showerror("Error", "Item ID and Name are required!", parent=win)
                return
            if iid in inventory:
                messagebox.showerror("Error", "Item ID already exists", parent=win)
                return
            if q < 0 or p < 0:
                messagebox.showerror("Error", "Quantity and price must be non-negative", parent=win)
                return
            inventory[iid] = {"name": name, "quantity": q, "price": p}
            save_inventory()
            self.populate_tree()
            messagebox.showinfo("Success", f"Item '{name}' added.", parent=win)
            win.destroy()

        ttk.Button(win, text="Add Item", command=on_submit).pack(pady=12)

    # --------------------------
    # Update Item
    # --------------------------
    def update_item_window(self):
        sel = self.get_selected_item()
        if not sel: return
        item_id = sel
        details = inventory[item_id]

        win = tk.Toplevel(self)
        win.title(f"Update {item_id}")
        win.geometry("380x320")
        win.transient(self)
        win.grab_set()
        win.focus_force()
        self.center_window(win, 380, 320)

        ttk.Label(win, text=f"Updating: {item_id} ({details['name']})").pack(anchor="w", padx=10, pady=(8,0))

        ttk.Label(win, text="Name (leave blank to keep):").pack(anchor="w", padx=10, pady=(6,0))
        name_entry = ttk.Entry(win)
        name_entry.insert(0, details['name'])
        name_entry.pack(fill="x", padx=10)

        ttk.Label(win, text="Quantity (leave blank to keep):").pack(anchor="w", padx=10, pady=(6,0))
        qty_entry = ttk.Entry(win)
        qty_entry.pack(fill="x", padx=10)
        qty_mode = tk.StringVar(value="Replace")
        ttk.Label(win, text="Quantity mode:").pack(anchor="w", padx=10, pady=(6,0))
        ttk.OptionMenu(win, qty_mode, "Replace", "Replace", "Add").pack(anchor="w", padx=10)

        ttk.Label(win, text="Price (leave blank to keep):").pack(anchor="w", padx=10, pady=(6,0))
        price_entry = ttk.Entry(win)
        price_entry.pack(fill="x", padx=10)
        price_mode = tk.StringVar(value="Replace")
        ttk.Label(win, text="Price mode:").pack(anchor="w", padx=10, pady=(6,0))
        ttk.OptionMenu(win, price_mode, "Replace", "Replace", "Add").pack(anchor="w", padx=10)

        def on_update():
            name_val = name_entry.get().strip()
            if name_val: details['name'] = name_val.title()

            qtxt = qty_entry.get().strip()
            if qtxt:
                try:
                    qnum = int(qtxt)
                    if qty_mode.get() == "Add":
                        details['quantity'] += qnum
                    else:
                        details['quantity'] = qnum
                except ValueError:
                    messagebox.showwarning("Warning", "Invalid quantity; skipping update.", parent=win)

            ptxt = price_entry.get().strip()
            if ptxt:
                try:
                    pnum = float(ptxt)
                    if price_mode.get() == "Add":
                        details['price'] += pnum
                    else:
                        details['price'] = pnum
                except ValueError:
                    messagebox.showwarning("Warning", "Invalid price; skipping update.", parent=win)

            inventory[item_id] = details
            save_inventory()
            self.populate_tree()
            messagebox.showinfo("Success", f"Item '{details['name']}' updated.", parent=win)
            win.destroy()

        ttk.Button(win, text="Update Item", command=on_update).pack(pady=10)

    # --------------------------
    # Delete Item
    # --------------------------
    def delete_item(self):
        sel = self.get_selected_item()
        if not sel: return
        item_id = sel
        details = inventory[item_id]

        if messagebox.askyesno("Confirm Delete", f"Do you want to DELETE the entire item '{details['name']}'?"):
            del inventory[item_id]
            save_inventory()
            self.populate_tree()
            messagebox.showinfo("Deleted", f"Item '{details['name']}' deleted.")
            return

        qty = simpledialog.askinteger("Delete Quantity", f"Enter quantity to remove (1-{details['quantity']}):",
                                      minvalue=1, maxvalue=details['quantity'], parent=self)
        if qty is None: return
        if qty >= details['quantity']:
            if messagebox.askyesno("Confirm", "Requested quantity >= stock. Delete entire item instead?"):
                del inventory[item_id]
                save_inventory()
                self.populate_tree()
                messagebox.showinfo("Deleted", f"Item '{details['name']}' deleted.")
                return
            else:
                messagebox.showinfo("Cancelled", "Deletion cancelled.")
                return
        details['quantity'] -= qty
        inventory[item_id] = details
        save_inventory()
        self.populate_tree()
        messagebox.showinfo("Updated", f"{qty} units removed from '{details['name']}'. New qty: {details['quantity']}")

    # --------------------------
    # Show Catalog
    # --------------------------
    def show_catalog(self):
        win = tk.Toplevel(self)
        win.title("Product Catalog")
        win.geometry("500x350")
        win.transient(self)
        win.grab_set()
        win.focus_force()
        self.center_window(win, 500, 350)

        cols = ("Item_ID", "Name", "Price")
        tv = ttk.Treeview(win, columns=cols, show="headings", height=15)
        for c in cols:
            tv.heading(c, text=c)
        tv.column("Item_ID", width=100)
        tv.column("Name", width=250)
        tv.column("Price", width=100, anchor="e")
        tv.pack(fill="both", expand=True, padx=8, pady=8)

        for item_id, details in sorted(inventory.items(), key=lambda x: x[1]['name']):
            tv.insert("", "end", values=(item_id, details['name'], f"{details['price']:.2f}"))

    # --------------------------
    # Low Stock Items
    # --------------------------
    def low_stock_items(self):
        win = tk.Toplevel(self)
        win.title("Low Stock Items")
        win.geometry("480x320")
        win.transient(self)
        win.grab_set()
        win.focus_force()
        self.center_window(win, 480, 320)

        cols = ("Item_ID", "Name", "Quantity")
        tv = ttk.Treeview(win, columns=cols, show="headings", height=15)
        for c in cols:
            tv.heading(c, text=c)
        tv.column("Item_ID", width=100)
        tv.column("Name", width=250)
        tv.column("Quantity", width=100, anchor="center")
        tv.pack(fill="both", expand=True, padx=8, pady=8)

        low_items = [(iid,d) for iid,d in inventory.items() if d['quantity'] < self.LOW_STOCK_THRESHOLD]
        for iid, d in low_items:
            tv.insert("", "end", values=(iid,d['name'],d['quantity']))

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
    # Purchase with Ref numbers
    # --------------------------
    def purchase_with_ref(self):
        win = tk.Toplevel(self)
        win.title("Purchase (Ref Map)")
        win.geometry("650x450")
        win.transient(self)
        win.grab_set()
        win.focus_force()
        self.center_window(win, 650, 450)

        # Treeview for ref map
        cols = ("Ref", "Item_ID", "Name", "Price", "Stock")
        tv = ttk.Treeview(win, columns=cols, show="headings", height=10)
        for c,w in zip(cols,[50,100,250,80,80]):
            tv.heading(c, text=c)
            tv.column(c, width=w)
        tv.pack(fill="x", padx=8, pady=8)

        ref_map = {}
        for idx, (item_id, details) in enumerate(inventory.items(), start=1):
            ref_map[str(idx)] = item_id
            tv.insert("", "end", values=(idx, item_id, details['name'], f"{details['price']:.2f}", details['quantity']))

        cart = {}
        # Cart listbox
        cart_listbox = tk.Listbox(win, height=6)
        cart_listbox.pack(fill="both", expand=False, padx=8, pady=(0,8))

        # Controls
        ctrl_frm = ttk.Frame(win)
        ctrl_frm.pack(fill="x", padx=8, pady=6)
        ttk.Label(ctrl_frm, text="Ref No:").grid(row=0, column=0, padx=4)
        ref_ent = ttk.Entry(ctrl_frm, width=8)
        ref_ent.grid(row=0, column=1, padx=4)
        ttk.Label(ctrl_frm, text="Qty:").grid(row=0, column=2, padx=4)
        qty_ent = ttk.Entry(ctrl_frm, width=8)
        qty_ent.grid(row=0, column=3, padx=4)

        def add_to_cart():
            r = ref_ent.get().strip()
            if r not in ref_map:
                messagebox.showerror("Error", "Invalid Ref No.", parent=win)
                return
            iid = ref_map[r]
            try: q = int(qty_ent.get().strip())
            except: messagebox.showerror("Error", "Invalid Qty.", parent=win); return
            if q <=0 or q>inventory[iid]['quantity']:
                messagebox.showerror("Error", f"Qty must be 1-{inventory[iid]['quantity']}", parent=win)
                return
            if iid in cart:
                cart[iid]['quantity'] += q
            else:
                cart[iid] = {"name":inventory[iid]['name'], "price":inventory[iid]['price'], "quantity":q}
            inventory[iid]['quantity'] -= q
            save_inventory()
            self.populate_tree()
            # Update cart listbox
            cart_listbox.delete(0,"end")
            for k,d in cart.items():
                cart_listbox.insert("end", f"{k} | {d['name']} x {d['quantity']}")
            # clear entry fields
            ref_ent.delete(0,"end"); qty_ent.delete(0,"end")
            messagebox.showinfo("Added", f"Added {q} x {inventory[iid]['name']} to cart", parent=win)

        def checkout():
            if not cart:
                messagebox.showinfo("Cart empty","No items in cart", parent=win)
                return
            bill_win = tk.Toplevel(win)
            bill_win.title("Bill Summary")
            bill_win.geometry("480x320")
            bill_win.transient(win)
            bill_win.grab_set()
            bill_win.focus_force()
            self.center_window(bill_win,480,320)
            txt = tk.Text(bill_win)
            txt.pack(fill="both", expand=True)
            total = 0
            txt.insert("end", f"{'Item':<20}{'Qty':<8}{'Price':<10}{'Subtotal':<10}\n")
            txt.insert("end", "-"*50 + "\n")
            for iid,d in cart.items():
                subtotal = d['quantity']*d['price']
                total += subtotal
                txt.insert("end", f"{d['name']:<20}{d['quantity']:<8}{d['price']:<10.2f}{subtotal:<10.2f}\n")
            txt.insert("end", "-"*50 + "\n")
            txt.insert("end", f"{'TOTAL:':<38}{total:<10.2f}\n")
            cart.clear()
            cart_listbox.delete(0,"end")
            messagebox.showinfo("Checkout", "Purchase completed. Inventory updated.", parent=bill_win)

        ttk.Button(ctrl_frm, text="Add to Cart", command=add_to_cart).grid(row=0,column=4,padx=6)
        ttk.Button(ctrl_frm, text="Checkout", command=checkout).grid(row=0,column=5,padx=6)

    # --------------------------
    # Center window utility
    # --------------------------
    def center_window(self, win, w, h):
        ws = win.winfo_screenwidth(); hs = win.winfo_screenheight()
        x = (ws//2)-(w//2); y=(hs//2)-(h//2)
        win.geometry(f"{w}x{h}+{x}+{y}")

    # --------------------------
    # Exit
    # --------------------------
    def on_exit(self):
        save_inventory()
        self.destroy()


if __name__ == "__main__":
    app = InventoryApp()
    app.mainloop()
