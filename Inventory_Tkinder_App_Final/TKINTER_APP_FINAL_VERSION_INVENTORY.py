import os
import json
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# -------------------------
# Config
# -------------------------
FILE_NAME = "inventory.json"
LOW_STOCK_THRESHOLD = 5
APP_BG = "#2b2b2b"
HEADER_BG = "#1f1f1f"
CARD_BG = "#333333"
TEXT_COLOR = "#FFFFFF"
SECONDARY_TEXT = "#CCCCCC"

# -------------------------
# Persistence helpers
# -------------------------
def load_inventory():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                return {}
        # normalize older key names: 'quantity' -> 'qty'
        for k, v in data.items():
            if "quantity" in v and "qty" not in v:
                v["qty"] = v.pop("quantity")
        return data
    return {}

def save_inventory(inv):
    with open(FILE_NAME, "w") as f:
        json.dump(inv, f, indent=4)

# -------------------------
# App
# -------------------------
class InventoryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Inventory Management System")
        self.configure(bg=APP_BG)
        # We don't need a specific self.geometry() now, 
        # as the internal content will determine the scroll size.
        # self.geometry("1000x650") 
        self.minsize(400, 300) # Set a sensible minimum size for the scrollable window

        # Load inventory (dict keyed by item_id)
        self.inventory = load_inventory()

        # ----------------------------------------------------
        # 🔥 START OF VISUALIZATION CHANGES 🔥
        # 1. Setup Canvas and Scrollbars
        # ----------------------------------------------------
        
        # Frame to hold the Canvas and Vertical Scrollbar (fills the root window)
        self.scroll_container = tk.Frame(self, bg=APP_BG)
        self.scroll_container.pack(fill='both', expand=True)

        # Create the Canvas
        self.canvas = tk.Canvas(self.scroll_container, bg=APP_BG, highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        # Create Scrollbars
        self.v_scrollbar = ttk.Scrollbar(self.scroll_container, orient="vertical", command=self.canvas.yview)
        self.v_scrollbar.pack(side="right", fill="y")
        
        # Horizontal scrollbar (if needed, place it in the root window below the main scroll_container)
        self.h_scrollbar = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.h_scrollbar.pack(side="bottom", fill="x")

        # Configure the Canvas to use the Scrollbars
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)
        
        # 2. Create the INNER FRAME (content_frame) to hold ALL your existing widgets
        self.content_frame = tk.Frame(self.canvas, bg=APP_BG)
        
        # Place the content_frame inside the canvas
        self.canvas_window = self.canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        
        # Bind the frame configuration to update the scroll region
        self.content_frame.bind("<Configure>", self._on_frame_configure)
        
        # Bind the canvas size change to make the inner frame the same width as the canvas
        self.canvas.bind("<Configure>", self._on_canvas_resize)

        # ----------------------------------------------------
        # 🔥 END OF VISUALIZATION CHANGES 🔥
        # ----------------------------------------------------

        # 3. Modify all UI builders to use 'self.content_frame' as parent
        self._build_header()
        self._build_tree()
        self._build_controls()
        self._build_footer()

        # Populate initial data
        self.populate_tree()

        # Style: zebra rows
        self._style_treeview()

    # ----------------------------------------------------
    # 🔥 NEW SCROLLING HELPER METHODS 🔥
    # ----------------------------------------------------
    def _on_frame_configure(self, event):
        """Update the scroll region to encompass the inner frame's total size."""
        # Calculate the required scroll region based on the inner frame's size
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_resize(self, event):
        """Update the inner frame's width to match the canvas's width."""
        # This ensures the internal widgets stretch horizontally with the window 
        # (if they were set to fill='x' or use grid/pack expand options)
        # without affecting the content's calculated height.
        self.canvas.itemconfig(self.canvas_window, width=self.canvas.winfo_width())

    # -------------------------
    # UI builders (Modified to use self.content_frame as parent)
    # -------------------------
    def _build_header(self):
        # NOTE: Using self.content_frame as parent
        header = tk.Frame(self.content_frame, bg=HEADER_BG, height=70)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        title = tk.Label(header, text="🛒 Inventory Management System",
                          bg=HEADER_BG, fg=TEXT_COLOR, font=("Helvetica", 18, "bold"))
        title.pack(side="left", padx=20)

    def _build_tree(self):
        # NOTE: Using self.content_frame as parent
        frame = tk.Frame(self.content_frame, bg=APP_BG)
        frame.pack(fill="x", padx=16, pady=(12,6)) # Changed fill="both", expand=True to fill="x"

        cols = ("ID", "Name", "Qty", "Price")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", height=18)
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=180 if c == "Name" else 110, anchor="center")
        self.tree.pack(side="left", fill="x", expand=True) # Changed fill="both" to fill="x"

        vs = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vs.set)
        vs.pack(side="left", fill="y")
        # NOTE: The Treeview already has its own scrollbar. This is fine.

    def _build_controls(self):
        # NOTE: Using self.content_frame as parent
        ctrl = tk.Frame(self.content_frame, bg=APP_BG)
        ctrl.pack(fill="x", padx=16, pady=(6,12))

        btn_cfg = {"padx":10, "pady":8, "bd":0, "relief":"flat", "width":14, "font":("Helvetica", 10, "bold")}
        # ... (rest of the controls remain the same, packed/gridded into 'ctrl')
        tk.Button(ctrl, text="Add Item", bg="#4CAF50", fg="white", command=self.add_item_window, **btn_cfg).grid(row=0, column=0, padx=6)
        tk.Button(ctrl, text="Update Item", bg="#2196F3", fg="white", command=self.update_item_window, **btn_cfg).grid(row=0, column=1, padx=6)
        tk.Button(ctrl, text="Delete Item", bg="#F44336", fg="white", command=self.delete_item, **btn_cfg).grid(row=0, column=2, padx=6)
        tk.Button(ctrl, text="Purchase", bg="#FF9800", fg="white", command=self.purchase_with_ref, **btn_cfg).grid(row=0, column=3, padx=6)
        tk.Button(ctrl, text="Show Catalog", bg="#9C27B0", fg="white", command=self.show_catalog, **btn_cfg).grid(row=0, column=4, padx=6)
        tk.Button(ctrl, text="Low Stock", bg="#FFEB3B", fg="#111111", command=self.low_stock_items, **btn_cfg).grid(row=0, column=5, padx=6)
        tk.Button(ctrl, text="Refresh", bg="#B0BEC5", fg="#111111", command=self.populate_tree, **btn_cfg).grid(row=0, column=6, padx=6)

        # Search area
        search_frm = tk.Frame(ctrl, bg=APP_BG)
        search_frm.grid(row=0, column=7, padx=(20,0))
        tk.Label(search_frm, text="Search:", bg=APP_BG, fg=SECONDARY_TEXT).pack(side="left", padx=(0,6))
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frm, textvariable=self.search_var, width=25, font=("Helvetica", 10))
        search_entry.pack(side="left")
        tk.Button(search_frm, text="Go", bg="#607D8B", fg="white", command=self._search_and_show, **{"padx":8,"pady":6,"bd":0}).pack(side="left", padx=6)
        tk.Button(search_frm, text="Clear", bg="#455A64", fg="white", command=self._clear_search, **{"padx":8,"pady":6,"bd":0}).pack(side="left")

    def _build_footer(self):
        # NOTE: Using self.content_frame as parent
        footer = tk.Frame(self.content_frame, bg=APP_BG, height=28)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)
        lbl = tk.Label(footer, text="Powered by Bala | Tkinter", bg=APP_BG, fg="#9E9E9E", font=("Helvetica", 9, "italic"))
        lbl.pack(side="right", padx=12, pady=4)

    # -------------------------
    # Tree helpers (no change needed here)
    # -------------------------
    def _style_treeview(self):
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("Treeview",
                         background=CARD_BG,
                         foreground=TEXT_COLOR,
                         fieldbackground=CARD_BG,
                         rowheight=26,
                         font=("Helvetica", 10))
        style.configure("Treeview.Heading", font=("Helvetica", 11, "bold"), background="#3a3a3a", foreground=TEXT_COLOR)
        style.map('Treeview', background=[('selected', '#5a95ff')], foreground=[('selected', 'white')])

    def populate_tree(self, filter_keyword=None, reserved=None):
        """
        Populate the main tree. If `reserved` is provided (dict iid->reserved_qty),
        displayed qty will be inventory_qty - reserved_qty (but underlying self.inventory unchanged).
        """
        if reserved is None:
            reserved = {}
        for r in self.tree.get_children():
            self.tree.delete(r)
        items = list(self.inventory.items())
        if filter_keyword:
            k = filter_keyword.lower()
            items = [it for it in items if k == it[0].lower() or k in it[1].get('name','').lower()]
        for idx, (iid, info) in enumerate(items):
            bg = "#333333" if idx % 2 == 0 else "#3b3b3b"
            base_qty = info.get("qty", info.get("quantity",0))
            display_qty = max(0, base_qty - reserved.get(iid, 0))
            self.tree.insert("", "end", iid=iid, values=(iid, info.get("name",""), display_qty, f"{info.get('price',0):.2f}"), tags=(bg,))
            self.tree.tag_configure(bg, background=bg, foreground=TEXT_COLOR)

    # -------------------------
    # Utilities (no change needed here)
    # -------------------------
    def center_window(self, win, w=420, h=300):
        win.update_idletasks()
        ws = win.winfo_screenwidth(); hs = win.winfo_screenheight()
        x = (ws // 2) - (w // 2); y = (hs // 2) - (h // 2)
        win.geometry(f"{w}x{h}+{x}+{y}")

    def _selected_item_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select item", "Please select an item first.", parent=self)
            return None
        return sel[0]

    # -------------------------
    # Search helpers (no change needed here)
    # -------------------------
    def _search_and_show(self):
        kw = self.search_var.get().strip()
        if not kw:
            self.populate_tree()
            return
        self.populate_tree(filter_keyword=kw)

    def _clear_search(self):
        self.search_var.set("")
        self.populate_tree()

    # -------------------------
    # Add Item (no change needed here)
    # -------------------------
    def add_item_window(self):
        win = tk.Toplevel(self)
        win.title("Add Item")
        win.configure(bg=APP_BG)
        win.transient(self); win.grab_set(); win.lift(); win.focus_force()
        self.center_window(win, 420, 320)

        frm = tk.Frame(win, bg=APP_BG); frm.pack(fill="both", expand=True, padx=14, pady=12)

        tk.Label(frm, text="Item ID (e.g. A101):", bg=APP_BG, fg=SECONDARY_TEXT).pack(anchor="w", pady=(2,2))
        id_entry = tk.Entry(frm, font=("Helvetica", 11))
        id_entry.pack(fill="x", pady=(0,8))

        tk.Label(frm, text="Name:", bg=APP_BG, fg=SECONDARY_TEXT).pack(anchor="w", pady=(2,2))
        name_entry = tk.Entry(frm, font=("Helvetica", 11))
        name_entry.pack(fill="x", pady=(0,8))

        tk.Label(frm, text="Quantity:", bg=APP_BG, fg=SECONDARY_TEXT).pack(anchor="w", pady=(2,2))
        qty_entry = tk.Entry(frm, font=("Helvetica", 11))
        qty_entry.pack(fill="x", pady=(0,8))

        tk.Label(frm, text="Price:", bg=APP_BG, fg=SECONDARY_TEXT).pack(anchor="w", pady=(2,2))
        price_entry = tk.Entry(frm, font=("Helvetica", 11))
        price_entry.pack(fill="x", pady=(0,12))

        def on_submit():
            win.lift(); win.focus_force()
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
            if q < 0 or p < 0:
                messagebox.showerror("Error", "Quantity and price must be non-negative", parent=win)
                return
            if iid in self.inventory:
                messagebox.showerror("Error", "Item ID already exists", parent=win)
                return
            self.inventory[iid] = {"name": name, "qty": q, "price": p}
            save_inventory(self.inventory)
            self.populate_tree()
            messagebox.showinfo("Success", f"Item '{name}' added.", parent=win)
            win.destroy()

        btn = tk.Button(frm, text="Add Item", bg="#4CAF50", fg="white", font=("Helvetica", 11, "bold"), bd=0, relief="raised", padx=8, pady=6, command=on_submit)
        btn.pack()

    # -------------------------
    # Update item (no change needed here)
    # -------------------------
    def update_item_window(self):
        iid = self._selected_item_id()
        if not iid: return
        details = self.inventory[iid]

        win = tk.Toplevel(self)
        win.title(f"Update {iid}")
        win.configure(bg=APP_BG)
        win.transient(self); win.grab_set(); win.lift(); win.focus_force()
        self.center_window(win, 460, 420)

        frm = tk.Frame(win, bg=APP_BG); frm.pack(fill="both", expand=True, padx=14, pady=12)

        tk.Label(frm, text=f"Updating: {iid}", bg=APP_BG, fg=TEXT_COLOR, font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(0,6))

        tk.Label(frm, text="Name (leave blank to keep):", bg=APP_BG, fg=SECONDARY_TEXT).pack(anchor="w", pady=(4,2))
        name_entry = tk.Entry(frm, font=("Helvetica", 11)); name_entry.insert(0, details.get("name","")); name_entry.pack(fill="x")

        tk.Label(frm, text="Quantity (leave blank to keep):", bg=APP_BG, fg=SECONDARY_TEXT).pack(anchor="w", pady=(8,2))
        qty_entry = tk.Entry(frm, font=("Helvetica", 11)); qty_entry.pack(fill="x")
        qty_mode = tk.StringVar(value="Replace")
        mode_frm = tk.Frame(frm, bg=APP_BG); mode_frm.pack(anchor="w", pady=(6,2))
        tk.Radiobutton(mode_frm, text="Replace", variable=qty_mode, value="Replace", bg=APP_BG, fg=SECONDARY_TEXT, selectcolor="#444444").pack(side="left")
        tk.Radiobutton(mode_frm, text="Add", variable=qty_mode, value="Add", bg=APP_BG, fg=SECONDARY_TEXT, selectcolor="#444444").pack(side="left")

        tk.Label(frm, text="Price (leave blank to keep):", bg=APP_BG, fg=SECONDARY_TEXT).pack(anchor="w", pady=(8,2))
        price_entry = tk.Entry(frm, font=("Helvetica", 11)); price_entry.pack(fill="x")
        price_mode = tk.StringVar(value="Replace")
        pm_frm = tk.Frame(frm, bg=APP_BG); pm_frm.pack(anchor="w", pady=(6,2))
        tk.Radiobutton(pm_frm, text="Replace", variable=price_mode, value="Replace", bg=APP_BG, fg=SECONDARY_TEXT, selectcolor="#444444").pack(side="left")
        tk.Radiobutton(pm_frm, text="Add", variable=price_mode, value="Add", bg=APP_BG, fg=SECONDARY_TEXT, selectcolor="#444444").pack(side="left")

        def on_update():
            win.lift(); win.focus_force()
            name_val = name_entry.get().strip()
            if name_val:
                details['name'] = name_val.title()
            ptxt = price_entry.get().strip()
            qtxt = qty_entry.get().strip()
            if qtxt:
                try:
                    qnum = int(qtxt)
                    if qty_mode.get() == "Add":
                        details['qty'] = details.get('qty',0) + qnum
                    else:
                        details['qty'] = qnum
                except ValueError:
                    messagebox.showwarning("Warning", "Invalid quantity; skipping qty update.", parent=win)
            
            if ptxt:
                try:
                    pnum = float(ptxt)
                    if price_mode.get() == "Add":
                        details['price'] = details.get('price',0.0) + pnum
                    else:
                        details['price'] = pnum
                except ValueError:
                    messagebox.showwarning("Warning", "Invalid price; skipping price update.", parent=win)

            self.inventory[iid] = details
            save_inventory(self.inventory)
            self.populate_tree()
            messagebox.showinfo("Success", f"Item '{details['name']}' updated.", parent=win)
            win.destroy()

        tk.Button(frm, text="Update Item", bg="#2196F3", fg="white", font=("Helvetica",11,"bold"), bd=0, padx=8, pady=6, command=on_update).pack(pady=10)

    # -------------------------
    # Delete item (full or partial) (no change needed here)
    # -------------------------
    def delete_item(self):
        iid = self._selected_item_id()
        if not iid: return
        details = self.inventory[iid]
        if messagebox.askyesno("Confirm Delete", f"Do you want to DELETE the entire item '{details['name']}'?", parent=self):
            del self.inventory[iid]
            save_inventory(self.inventory)
            self.populate_tree()
            messagebox.showinfo("Deleted", f"Item '{details['name']}' deleted.", parent=self)
            return
        qty = simpledialog.askinteger("Delete Quantity", f"Enter quantity to remove (1 - {details.get('qty',0)}):",
                                     minvalue=1, maxvalue=details.get('qty',0), parent=self)
        if qty is None:
            return
        if qty >= details.get('qty',0):
            if messagebox.askyesno("Confirm", "Requested qty >= stock. Delete entire item instead?", parent=self):
                del self.inventory[iid]
                save_inventory(self.inventory)
                self.populate_tree()
                messagebox.showinfo("Deleted", f"Item '{details['name']}' deleted.", parent=self)
                return
            else:
                messagebox.showinfo("Cancelled", "Deletion cancelled.", parent=self)
                return
        details['qty'] = details.get('qty',0) - qty
        self.inventory[iid] = details
        save_inventory(self.inventory)
        self.populate_tree()
        messagebox.showinfo("Updated", f"{qty} units removed from '{details['name']}'. New qty: {details['qty']}", parent=self)

    # -------------------------
    # Show Catalog (no change needed here)
    # -------------------------
    def show_catalog(self):
        win = tk.Toplevel(self)
        # ... (rest of function remains the same)
        win.title("Product Catalog")
        win.configure(bg=APP_BG)
        win.transient(self); win.grab_set(); win.lift(); win.focus_force()
        self.center_window(win, 600, 420)

        cols = ("ID", "Name", "Price")
        tv = ttk.Treeview(win, columns=cols, show="headings", height=16)
        for c in cols:
            tv.heading(c, text=c)
            tv.column(c, width=200 if c=="Name" else 120, anchor="center")
        tv.pack(fill="both", expand=True, padx=10, pady=10)
        vs = ttk.Scrollbar(win, orient="vertical", command=tv.yview)
        tv.configure(yscroll=vs.set)
        vs.pack(side="right", fill="y")

        for iid, d in sorted(self.inventory.items(), key=lambda x: x[1].get('name','').lower()):
            tv.insert("", "end", values=(iid, d.get('name',''), f"{d.get('price',0):.2f}"))

    # -------------------------
    # Low stock items (button) (no change needed here)
    # -------------------------
    def low_stock_items(self):
        win = tk.Toplevel(self)
        # ... (rest of function remains the same)
        win.title("Low Stock Items")
        win.configure(bg=APP_BG)
        win.transient(self); win.grab_set(); win.lift(); win.focus_force()
        self.center_window(win, 520, 360)

        cols = ("ID", "Name", "Qty")
        tv = ttk.Treeview(win, columns=cols, show="headings", height=14)
        for c in cols:
            tv.heading(c, text=c)
            tv.column(c, width=180 if c=="Name" else 120, anchor="center")
        tv.pack(fill="both", expand=True, padx=12, pady=12)

        for iid, d in self.inventory.items():
            if d.get('qty',0) < LOW_STOCK_THRESHOLD:
                tv.insert("", "end", values=(iid, d.get('name',''), d.get('qty',0)))

    # -------------------------
    # Purchase window with ref map and cart visible (no change needed here)
    # -------------------------
    def purchase_with_ref(self):
        if not self.inventory:
            messagebox.showerror("Error", "Inventory is empty!", parent=self); return

        win = tk.Toplevel(self)
        # ... (rest of function remains the same)
        win.title("Purchase (Ref Map)")
        win.configure(bg=APP_BG)
        win.transient(self); win.grab_set(); win.lift(); win.focus_force()
        self.center_window(win, 760, 520)

        # This dict holds temporary reserved quantities while purchase window is open
        reserved = {}  # iid -> reserved_qty

        top_frm = tk.Frame(win, bg=APP_BG)
        top_frm.pack(fill="x", padx=12, pady=(8,4))

        # Reference map (treeview neatly)
        ref_cols = ("Ref", "ID", "Name", "Price", "Stock")
        ref_tv = ttk.Treeview(win, columns=ref_cols, show="headings", height=8)
        for c,w in zip(ref_cols, [60,110,300,100,100]):
            ref_tv.heading(c, text=c); ref_tv.column(c, width=w, anchor="center")
        ref_tv.pack(fill="x", padx=12, pady=(4,6))

        # build ref_map
        ref_map = {}
        for idx, (iid, d) in enumerate(self.inventory.items(), 1):
            ref_map[str(idx)] = iid
            ref_tv.insert("", "end", values=(idx, iid, d.get('name',''), f"{d.get('price',0):.2f}", d.get('qty',0)))

        # Cart list area
        cart_frame = tk.LabelFrame(win, text="Cart", bg=APP_BG, fg=TEXT_COLOR)
        cart_frame.pack(fill="both", expand=True, padx=12, pady=(4,10))
        cart_listbox = tk.Listbox(cart_frame, height=6, font=("Helvetica", 10))
        cart_listbox.pack(side="left", fill="both", expand=True, padx=(6,0), pady=6)
        cart_scroll = ttk.Scrollbar(cart_frame, orient="vertical", command=cart_listbox.yview)
        cart_listbox.configure(yscrollcommand=cart_scroll.set)
        cart_scroll.pack(side="left", fill="y", padx=(0,6))

        # Controls
        ctrl = tk.Frame(win, bg=APP_BG)
        ctrl.pack(fill="x", padx=12, pady=(2,8))
        tk.Label(ctrl, text="Ref No:", bg=APP_BG, fg=SECONDARY_TEXT).grid(row=0, column=0, padx=6, pady=6)
        ref_ent = tk.Entry(ctrl, width=8); ref_ent.grid(row=0, column=1, padx=6)
        tk.Label(ctrl, text="Qty:", bg=APP_BG, fg=SECONDARY_TEXT).grid(row=0, column=2, padx=6)
        qty_ent = tk.Entry(ctrl, width=8); qty_ent.grid(row=0, column=3, padx=6)

        cart = []

        def refresh_ref_view():
            """Refresh the ref_tv display's stock column using reserved map."""
            # clear and re-insert with updated stock (inventory_qty - reserved)
            for r in ref_tv.get_children():
                ref_tv.delete(r)
            for idx, (iid, d) in enumerate(self.inventory.items(), 1):
                base_qty = d.get('qty',0)
                display_qty = max(0, base_qty - reserved.get(iid, 0))
                ref_tv.insert("", "end", values=(idx, iid, d.get('name',''), f"{d.get('price',0):.2f}", display_qty))

        def refresh_main_tree():
            """Refresh main tree to show display_qty = inventory_qty - reserved_qty (visual only)."""
            self.populate_tree(reserved=reserved)

        def add_to_cart():
            win.lift(); win.focus_force()
            r = ref_ent.get().strip()
            if r not in ref_map:
                messagebox.showerror("Error", "Invalid Ref No.", parent=win); return
            try:
                q = int(qty_ent.get().strip())
            except:
                messagebox.showerror("Error", "Invalid quantity.", parent=win); return
            iid = ref_map[r]; item = self.inventory[iid]
            available = item.get('qty',0) - reserved.get(iid, 0)
            if q <= 0 or q > available:
                messagebox.showerror("Error", f"Qty must be 1 - {available}", parent=win); return
            # update cart and reserved (temporary)
            found = False
            for c in cart:
                if c['id'] == iid:
                    c['qty'] += q; found = True; break
            if not found:
                cart.append({"id": iid, "name": item.get('name',''), "qty": q, "price": item.get('price',0)})
            # increase reserved
            reserved[iid] = reserved.get(iid, 0) + q

            # refresh both views (visual only)
            refresh_ref_view()
            refresh_main_tree()

            # refresh cart display
            cart_listbox.delete(0, "end")
            for c in cart:
                cart_listbox.insert("end", f"{c['id']} | {c['name']} x {c['qty']} @ {c['price']:.2f}")
            # clear inputs
            ref_ent.delete(0, "end"); qty_ent.delete(0, "end")
            messagebox.showinfo("Added", f"Added {q} x {item.get('name','')} to cart.", parent=win)

        def checkout():
            if not cart:
                messagebox.showinfo("Cart empty", "No items in cart", parent=win); return
            # prepare bill lines
            lines = []
            lines.append("-" * 44)
            lines.append("{:^44}".format("BILL SUMMARY"))
            lines.append("-" * 44)
            lines.append("{:<20}{:>5}{:>9}{:>10}".format("Item", "Qty", "Price", "Subtotal"))
            lines.append("-" * 44)
            total = 0.0
            for c in cart:
                subtotal = c['qty'] * c['price']
                total += subtotal
                lines.append("{:<20}{:>5}{:>9.2f}{:>10.2f}".format(c['name'][:20], c['qty'], c['price'], subtotal))
            lines.append("-" * 44)
            lines.append("{:^44}".format(""))
            lines.append("{:>34}{:>10.2f}".format("TOTAL: ", total))
            lines.append("-" * 44)
            lines.append("\n{:^44}".format("Thank you for your purchase!"))

            # Apply reserved to actual inventory (permanent)
            for iid, rqty in reserved.items():
                if iid in self.inventory:
                    self.inventory[iid]['qty'] = max(0, self.inventory[iid].get('qty',0) - rqty)
            save_inventory(self.inventory)
            # refresh main view (now permanent)
            self.populate_tree()

            # Bill window
            bill = tk.Toplevel(win)
            bill.title("Bill Summary")
            bill.configure(bg=APP_BG)
            bill.transient(win); bill.grab_set(); bill.lift(); bill.focus_force()
            self.center_window(bill, 450, 500)

            lbl = tk.Label(bill, text="BILL SUMMARY", bg=APP_BG, fg=TEXT_COLOR, font=("Courier New", 14, "bold"))
            lbl.pack(pady=(10,6))

            text = tk.Text(bill, bg="#1e1e1e", fg=TEXT_COLOR, font=("Courier New", 11), bd=0, relief="flat")
            text.pack(fill="both", expand=True, padx=12, pady=(0,6))
            text.insert("1.0", "\n".join(lines))
            text.configure(state="disabled")

            tk.Button(bill, text="Close", bg="#607D8B", fg="white", command=bill.destroy, font=("Helvetica", 11, "bold"), bd=0, padx=8, pady=6).pack(pady=(6,12))

            # clear cart and reserved (since permanent now)
            cart.clear()
            reserved.clear()
            cart_listbox.delete(0, "end")
            refresh_ref_view()
            messagebox.showinfo("Checkout", "Purchase completed. Inventory updated.", parent=bill)

        def on_purchase_window_close():
            # discard temporary reservations and refresh main tree to original inventory
            if reserved:
                # confirm if they want to cancel changes
                if not messagebox.askyesno("Cancel Purchase", "Closing will cancel the current cart and release reserved stock. Continue?", parent=win):
                    return
            # simply clear and refresh displays
            reserved.clear()
            self.populate_tree()  # no reserved => show actual inventory
            win.destroy()

        # Buttons
        tk.Button(ctrl, text="Add to Cart", bg="#F1C40F", fg="#111111", font=("Helvetica", 10, "bold"), bd=0, padx=8, pady=6, command=add_to_cart).grid(row=0, column=4, padx=10)
        tk.Button(ctrl, text="Checkout", bg="#16A085", fg="white", font=("Helvetica", 10, "bold"), bd=0, padx=8, pady=6, command=checkout).grid(row=0, column=5, padx=10)

        # Ensure closing the purchase window reverts the temporary reservation
        win.protocol("WM_DELETE_WINDOW", on_purchase_window_close)

    # -------------------------
    # Exit / Save (no change needed here)
    # -------------------------
    def on_exit(self):
        save_inventory(self.inventory)
        self.destroy()

# -------------------------
# Run
# -------------------------
if __name__ == "__main__":
    app = InventoryApp()
    app.protocol("WM_DELETE_WINDOW", app.on_exit)
    app.mainloop()