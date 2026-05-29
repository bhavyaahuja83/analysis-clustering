import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import threading
import pyperclip
import os
import math

EXCEL_FILE = 'output_clusters.xlsx'

# ---------------------- Data loading (background-friendly) ----------------------

def safe_float(v, default=None):
    try:
        if pd.isna(v):
            return default
        return float(v)
    except Exception:
        return default

# Load and structure data per cluster
def load_data_from_excel(path):
    grouped = {}
    df = pd.read_excel(path)
    for _, row in df.iterrows():
        cid = row.get('ClusterIndex')
        if pd.isna(cid):
            continue
        cid = int(cid)
        if cid not in grouped:
            grouped[cid] = {
                'meta': {
                    'AgeGroup': row.get('AgeGroup', ''),
                    'Gender': row.get('Gender', ''),
                    'IncomeGroup': row.get('IncomeGroup', ''),
                    'Profession': row.get('Profession', ''),
                    'City': row.get('City', ''),
                    'Brand': row.get('Brand', ''),
                    'LeadCount': int(row.get('LeadCount', 0) if not pd.isna(row.get('LeadCount')) else 0)
                },
                'slots': []
            }
        grouped[cid]['slots'].append({
            'Day': row.get('Day', ''),
            'Time': row.get('Time', ''),
            'PickupRate': safe_float(row.get('PickupRate')),
            'AvgDuration': safe_float(row.get('AvgDuration')),
            'BestTime': row.get('BestTime', '')
        })
    return grouped

# ---------------------- Clipboard helpers ----------------------

def copy_row_to_clipboard(cluster_meta):
    formatted = " | ".join(f"{k}: {v}" for k, v in cluster_meta.items())
    pyperclip.copy(formatted)
    messagebox.showinfo("Copied", "Cluster details copied to clipboard!")

def copy_slot_to_clipboard(slot_data):
    pickup = f"{slot_data['PickupRate']:.2f}%" if isinstance(slot_data['PickupRate'], (int, float)) else str(slot_data['PickupRate'])
    duration = f"{slot_data['AvgDuration']:.1f} s" if isinstance(slot_data['AvgDuration'], (int, float)) else str(slot_data['AvgDuration'])
    formatted = f"Day: {slot_data['Day']} | Time: {slot_data['Time']} | Pickup Rate: {pickup} | Avg Duration: {duration} | Best Time: {slot_data['BestTime']}"
    pyperclip.copy(formatted)
    messagebox.showinfo("Copied", "Time slot details copied to clipboard!")

# ---------------------- Export functions ----------------------

def _data_to_dataframe(data):
    export_df = []
    for cid, info in data.items():
        for slot in info['slots']:
            export_df.append({**{'ClusterIndex': cid}, **info['meta'], **slot})
    return pd.DataFrame(export_df)


def export_to_csv(data):
    df = _data_to_dataframe(data)
    file = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if file:
        df.to_csv(file, index=False)
        messagebox.showinfo("Exported", "Data exported as CSV.")


def export_to_excel(data):
    df = _data_to_dataframe(data)
    file = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
    if file:
        df.to_excel(file, index=False)
        messagebox.showinfo("Exported", "Data exported as Excel.")


def export_to_json(data):
    df = _data_to_dataframe(data)
    file = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
    if file:
        df.to_json(file, orient='records', indent=2)
        messagebox.showinfo("Exported", "Data exported as JSON.")

# ---------------------- Main GUI ----------------------
class ClusterViewerGUI:
    def __init__(self):
        self.data = {}
        self.filtered_data = {}
        self.root = tk.Tk()
        self.root.title("Cluster Viewer")
        self.root.geometry("1400x800")

        self.setup_styles()
        self.create_context_menu()
        self.create_widgets()

        # Load data in background to avoid freezing UI
        self.status_bar = ttk.Label(self.root, text="Loading...", anchor='w')
        self.status_bar.pack(side='bottom', fill='x', padx=8, pady=4)
        threading.Thread(target=self._load_data_background, daemon=True).start()

    def setup_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("Treeview", rowheight=28, font=('Segoe UI', 10))
        style.configure("Treeview.Heading", font=('Segoe UI', 10, 'bold'))
        style.configure("TLabel", font=('Segoe UI', 10))
        style.configure("TButton", font=('Segoe UI', 10))
        style.configure("TCombobox", font=('Segoe UI', 10))
        style.configure("TEntry", font=('Segoe UI', 10))
        style.configure("TLabelframe.Label", font=('Segoe UI', 10, 'bold'))

    def create_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Copy Cluster Info", command=self.copy_cluster_info)
        self.context_menu.add_command(label="Copy Slot Info", command=self.copy_slot_info)

        # We need to keep track of what was clicked
        self.clicked_item_id = None
        self.clicked_widget = None

    def create_widgets(self):
        # Main layout with a PanedWindow
        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Left side: Filters and Cluster list
        left_frame = ttk.Frame(main_pane, padding=8)

        # Filters
        filter_frame = ttk.LabelFrame(left_frame, text="Filters")
        filter_frame.pack(fill='x', pady=(0, 8), expand=False)

        # -- Filter controls
        filter_controls = ttk.Frame(filter_frame, padding=5)
        filter_controls.pack(fill='x')

        ttk.Label(filter_controls, text="Age:").grid(row=0, column=0, padx=(0, 5), pady=5, sticky='w')
        self.age_var = tk.StringVar()
        self.age_combo = ttk.Combobox(filter_controls, textvariable=self.age_var, width=12)
        self.age_combo.grid(row=0, column=1, padx=(0, 10), pady=5, sticky='ew')

        ttk.Label(filter_controls, text="Gender:").grid(row=0, column=2, padx=(0, 5), pady=5, sticky='w')
        self.gender_var = tk.StringVar()
        self.gender_combo = ttk.Combobox(filter_controls, textvariable=self.gender_var, width=12)
        self.gender_combo.grid(row=0, column=3, padx=(0, 10), pady=5, sticky='ew')

        ttk.Label(filter_controls, text="City:").grid(row=1, column=0, padx=(0, 5), pady=5, sticky='w')
        self.city_var = tk.StringVar()
        self.city_combo = ttk.Combobox(filter_controls, textvariable=self.city_var, width=12)
        self.city_combo.grid(row=1, column=1, padx=(0, 10), pady=5, sticky='ew')

        filter_controls.columnconfigure(1, weight=1)
        filter_controls.columnconfigure(3, weight=1)

        # -- Search and Clear
        search_frame = ttk.Frame(filter_frame, padding=5)
        search_frame.pack(fill='x', pady=(5, 0))
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill='x', expand=True, padx=(0, 10))
        self.search_entry.bind('<KeyRelease>', self.on_search)
        ttk.Button(search_frame, text="Clear", command=self.clear_filters).pack(side=tk.RIGHT)

        # Cluster Treeview
        tree_frame = ttk.Frame(left_frame)
        tree_frame.pack(fill='both', expand=True)

        self.cluster_tree = ttk.Treeview(tree_frame, show='headings')
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.cluster_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.cluster_tree.xview)
        self.cluster_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.cluster_tree.bind('<<TreeviewSelect>>', self.on_cluster_select)
        self.cluster_tree.bind('<Button-3>', self.show_context_menu)

        self.cluster_tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')

        # Export buttons
        export_frame = ttk.LabelFrame(left_frame, text="Export Filtered Data")
        export_frame.pack(fill='x', pady=(8, 0), expand=False)

        btn_frame = ttk.Frame(export_frame, padding=5)
        btn_frame.pack(fill='x')

        ttk.Button(btn_frame, text="Export CSV", command=lambda: export_to_csv(self.filtered_data)).pack(side=tk.LEFT, expand=True, fill='x', padx=2)
        ttk.Button(btn_frame, text="Export Excel", command=lambda: export_to_excel(self.filtered_data)).pack(side=tk.LEFT, expand=True, fill='x', padx=2)
        ttk.Button(btn_frame, text="Export JSON", command=lambda: export_to_json(self.filtered_data)).pack(side=tk.LEFT, expand=True, fill='x', padx=2)

        main_pane.add(left_frame, weight=1)

        # Right side: Details of selected cluster
        self.details_frame = ttk.Frame(main_pane, padding=12)
        main_pane.add(self.details_frame, weight=3)
        self.show_placeholder_details()

    def show_placeholder_details(self):
        for widget in self.details_frame.winfo_children():
            widget.destroy()
        placeholder = ttk.Label(self.details_frame, text="Select a cluster to see details", font=('Segoe UI', 12, 'italic'), foreground='grey')
        placeholder.pack(expand=True)

    def _load_data_background(self):
        try:
            if not os.path.exists(EXCEL_FILE):
                raise FileNotFoundError(f"'{EXCEL_FILE}' not found. Please place it in the correct directory.")
            data = load_data_from_excel(EXCEL_FILE)
            self.root.after(0, lambda: self._on_data_loaded(data))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Could not load data: {e}"))
            self.root.after(0, lambda: self.status_bar.config(text=f"Failed to load: {e}"))

    def _on_data_loaded(self, data):
        self.data = data
        self.filtered_data = dict(self.data)
        self.populate_filter_options()
        self.populate_cluster_tree()
        self.status_bar.config(text=f"Loaded {len(data)} clusters successfully.")

    def populate_filter_options(self):
        age_groups = sorted(list(set(str(info['meta']['AgeGroup']) for info in self.data.values())))
        genders = sorted(list(set(str(info['meta']['Gender']) for info in self.data.values())))
        cities = sorted(list(set(str(info['meta']['City']) for info in self.data.values())))
        self.age_combo['values'] = ['All'] + age_groups
        self.gender_combo['values'] = ['All'] + genders
        self.city_combo['values'] = ['All'] + cities
        self.clear_filters()
        self.age_var.trace_add('write', self.apply_filters)
        self.gender_var.trace_add('write', self.apply_filters)
        self.city_var.trace_add('write', self.apply_filters)

    def apply_filters(self, *args):
        search_term = self.search_var.get().lower().strip()
        self.filtered_data = {}
        for cid, info in self.data.items():
            meta = info['meta']
            # Combo box filters
            if self.age_var.get() != 'All' and str(meta['AgeGroup']) != self.age_var.get(): continue
            if self.gender_var.get() != 'All' and str(meta['Gender']) != self.gender_var.get(): continue
            if self.city_var.get() != 'All' and str(meta['City']) != self.city_var.get(): continue
            # Search term filter
            if search_term:
                searchable_text = f"{meta['AgeGroup']} {meta['Gender']} {meta['IncomeGroup']} {meta['Profession']} {meta['City']} {meta['Brand']}"
                if search_term not in searchable_text.lower():
                    continue
            self.filtered_data[cid] = info
        self.populate_cluster_tree()
        self.show_placeholder_details()

    def on_search(self, event=None):
        self.apply_filters()

    def clear_filters(self):
        self.age_var.set('All')
        self.gender_var.set('All')
        self.city_var.set('All')
        self.search_var.set('')
        # self.apply_filters() # This is called by the variable traces

    def populate_cluster_tree(self):
        for item in self.cluster_tree.get_children():
            self.cluster_tree.delete(item)

        cols = ("AgeGroup", "Gender", "IncomeGroup", "Profession", "City", "Brand", "LeadCount")
        self.cluster_tree['columns'] = cols
        self.cluster_tree.heading('#0', text='Cluster ID')
        self.cluster_tree.column('#0', width=80, anchor='center')
        for col in cols:
            self.cluster_tree.heading(col, text=col, command=lambda _col=col: self.sort_by_column(_col, False))
            self.cluster_tree.column(col, anchor='w', width=100)

        for cid, info in sorted(self.filtered_data.items()):
            cluster_meta = info['meta']
            self.cluster_tree.insert('', 'end', iid=str(cid), text=str(cid), values=[
                cluster_meta['AgeGroup'], cluster_meta['Gender'], cluster_meta['IncomeGroup'],
                cluster_meta['Profession'], cluster_meta['City'], cluster_meta['Brand'], cluster_meta['LeadCount']
            ])

    def on_cluster_select(self, event):
        selected_items = self.cluster_tree.selection()
        if not selected_items:
            return

        cluster_id = int(selected_items[0])
        self.update_details_view(cluster_id)

    def update_details_view(self, cid):
        for widget in self.details_frame.winfo_children():
            widget.destroy()

        cluster_info = self.data.get(cid)
        if not cluster_info:
            self.show_placeholder_details()
            return

        meta = cluster_info['meta']
        slots = cluster_info['slots']
        self.current_slots_data = {} # For context menu copying

        # Meta details section
        meta_frame = ttk.LabelFrame(self.details_frame, text=f"Details for Cluster {cid}")
        meta_frame.pack(fill='x', pady=(0, 10))

        details_grid = ttk.Frame(meta_frame, padding=10)
        details_grid.pack(fill='x')

        row = 0
        for i, (key, value) in enumerate(meta.items()):
            ttk.Label(details_grid, text=f"{key}:", font=('Segoe UI', 10, 'bold')).grid(row=row, column=(i%3)*2, sticky='w', padx=5, pady=2)
            ttk.Label(details_grid, text=str(value)).grid(row=row, column=(i%3)*2 + 1, sticky='w', padx=5, pady=2)
            if i%3 == 2: row += 1

        # Time slots section
        slots_frame = ttk.LabelFrame(self.details_frame, text="Time Slots Analysis")
        slots_frame.pack(fill='both', expand=True)

        self.slots_tree = ttk.Treeview(slots_frame, columns=('Day', 'Time', 'PickupRate', 'AvgDuration', 'BestTime'), show='headings')
        self.slots_tree.pack(fill='both', expand=True, side='left', padx=5, pady=5)
        self.slots_tree.bind('<Button-3>', self.show_context_menu)

        vsb = ttk.Scrollbar(slots_frame, orient="vertical", command=self.slots_tree.yview)
        vsb.pack(side='right', fill='y')
        self.slots_tree.configure(yscrollcommand=vsb.set)

        self.slots_tree.heading('Day', text='Day')
        self.slots_tree.heading('Time', text='Time')
        self.slots_tree.heading('PickupRate', text='Pickup Rate')
        self.slots_tree.heading('AvgDuration', text='Avg Duration (s)')
        self.slots_tree.heading('BestTime', text='Best Time')

        for i, slot in enumerate(slots):
            pickup_rate = slot['PickupRate']
            avg_duration = slot['AvgDuration']
            pickup_str = f"{pickup_rate:.2f}%" if isinstance(pickup_rate, (int, float)) and not math.isnan(pickup_rate) else "N/A"
            duration_str = f"{avg_duration:.1f}" if isinstance(avg_duration, (int, float)) and not math.isnan(avg_duration) else "N/A"
            item_id = self.slots_tree.insert('', 'end', values=[slot['Day'], slot['Time'], pickup_str, duration_str, slot.get('BestTime', '')])
            self.current_slots_data[item_id] = slot

    def show_context_menu(self, event):
        self.clicked_widget = event.widget
        item_id = self.clicked_widget.identify_row(event.y)

        if not item_id:
            return

        self.clicked_widget.selection_set(item_id)
        self.clicked_item_id = item_id

        is_cluster_tree = (self.clicked_widget == self.cluster_tree)
        self.context_menu.entryconfig("Copy Cluster Info", state=tk.NORMAL if is_cluster_tree else tk.DISABLED)
        self.context_menu.entryconfig("Copy Slot Info", state=tk.NORMAL if not is_cluster_tree else tk.DISABLED)

        self.context_menu.post(event.x_root, event.y_root)

    def copy_cluster_info(self):
        if not self.clicked_item_id: return
        cluster_id = int(self.clicked_item_id)
        cluster_info = self.data.get(cluster_id, {})
        copy_row_to_clipboard(cluster_info.get('meta', {}))

    def copy_slot_info(self):
        if not self.clicked_item_id: return
        slot_data = self.current_slots_data.get(self.clicked_item_id)
        if slot_data:
            copy_slot_to_clipboard(slot_data)

    def sort_by_column(self, col, reverse):
        data_items = [(self.cluster_tree.set(k, col), k) for k in self.cluster_tree.get_children('')]
        try:
            # Attempt to sort numerically if possible
            data_items.sort(key=lambda t: float(t[0]) if str(t[0]).strip() else float('-inf'), reverse=reverse)
        except (ValueError, TypeError):
            # Fallback to string sorting
            data_items.sort(key=lambda t: str(t[0]).lower(), reverse=reverse)

        for index, (_, k) in enumerate(data_items):
            self.cluster_tree.move(k, '', index)

        self.cluster_tree.heading(col, command=lambda _col=col: self.sort_by_column(_col, not reverse))

    def run(self):
        self.root.mainloop()

# ---------------------- Entrypoint ----------------------

def create_gui():
    app = ClusterViewerGUI()
    app.run()

if __name__ == '__main__':
    create_gui()
