import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Toplevel, Listbox
import json
import os
import webbrowser
import uuid

DATA_FILE = 'class_data_v2.json'

class AdithaAlamaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ADITHAALAMA CLASS HANDLE (Final UI)")
        self.geometry("1200x750")

        self.data = self.load_data()
        self.setup_styles()
        self.create_widgets()
        self.create_context_menu()
        self.populate_treeview()
        self.update_summary()
        self.on_selection_change() # Initially disable buttons

    def setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", rowheight=28, font=('Segoe UI', 10))
        style.configure("Treeview.Heading", font=('Segoe UI', 11, 'bold'), relief="flat")
        style.configure("TButton", font=('Segoe UI', 10), padding=5)
        style.configure("TLabel", font=('Segoe UI', 10))
        style.configure("Title.TLabel", font=('Segoe UI', 16, 'bold'), foreground='#00529B')
        style.configure("Summary.TLabel", font=('Segoe UI', 11, 'bold'), foreground='#333')
        style.map('Treeview', background=[('selected', '#0078D7')])

    def load_data(self):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"categories": ["Physics", "Chemistry"], "entries": []}

    def save_data(self):
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4)
        self.update_combobox_values()

    def create_widgets(self):
        top_frame = ttk.Frame(self, padding="10")
        top_frame.pack(fill=tk.X, side=tk.TOP)
        
        ttk.Label(top_frame, text="ADITHAALAMA CLASS HANDLE", style="Title.TLabel").pack(side=tk.LEFT, padx=10)
        
        ttk.Button(top_frame, text="Add New Entry", command=self.open_add_edit_window).pack(side=tk.RIGHT, padx=5)
        ttk.Button(top_frame, text="Manage Categories", command=self.open_category_manager).pack(side=tk.RIGHT, padx=5)

        ttk.Label(top_frame, text="Filter by Class:").pack(side=tk.LEFT, padx=(20, 5))
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(top_frame, textvariable=self.category_var, state="readonly")
        self.update_combobox_values()
        self.category_combo.set("All Classes")
        self.category_combo.pack(side=tk.LEFT, padx=5)
        self.category_combo.bind("<<ComboboxSelected>>", lambda e: self.populate_treeview())
        
        middle_frame = ttk.Frame(self, padding="10")
        middle_frame.pack(fill=tk.BOTH, expand=True)

        cols = ('Viewed', 'Description', 'PDF', 'Video', 'Notes')
        self.tree = ttk.Treeview(middle_frame, columns=cols, show='headings', selectmode="browse")
        
        self.tree.heading('Viewed', text='Viewed')
        self.tree.heading('Description', text='Description')
        self.tree.heading('PDF', text='PDF Available')
        self.tree.heading('Video', text='Video Available')
        self.tree.heading('Notes', text='Notes')
        
        self.tree.column('Viewed', width=80, anchor=tk.CENTER, stretch=tk.NO)
        self.tree.column('Description', width=300)
        self.tree.column('PDF', width=120, anchor=tk.CENTER, stretch=tk.NO)
        self.tree.column('Video', width=120, anchor=tk.CENTER, stretch=tk.NO)
        self.tree.column('Notes', width=400)
        
        self.tree.bind("<Button-1>", self.on_tree_cell_click)
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<<TreeviewSelect>>", self.on_selection_change)

        scrollbar = ttk.Scrollbar(middle_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # --- New Action Frame for Buttons ---
        action_frame = ttk.Frame(self, padding=(10, 5, 10, 5))
        action_frame.pack(fill=tk.X, side=tk.TOP)
        
        self.pdf_button = ttk.Button(action_frame, text="Open Selected PDF", command=lambda: self.open_link_or_file('pdf'))
        self.pdf_button.pack(side=tk.LEFT, padx=5)
        
        self.video_button = ttk.Button(action_frame, text="Open Selected Video", command=lambda: self.open_link_or_file('video'))
        self.video_button.pack(side=tk.LEFT, padx=5)

        bottom_frame = ttk.Frame(self, padding="10")
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.summary_label = ttk.Label(bottom_frame, text="", style="Summary.TLabel")
        self.summary_label.pack(side=tk.LEFT, padx=10)
        
    def create_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Edit Entry", command=self.edit_selected_entry)
        self.context_menu.add_command(label="Delete Entry", command=self.delete_selected_entry)

    def on_tree_cell_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell": return

        item_id = self.tree.identify_row(event.y)
        column_id = self.tree.identify_column(event.x)
        
        if not item_id: return
        self.tree.selection_set(item_id)
        
        if column_id == '#1': # 'Viewed' column
            self.toggle_status(item_id)

    def on_selection_change(self, event=None):
        item_id = self.get_selected_item_id()
        if not item_id:
            self.pdf_button.config(state='disabled')
            self.video_button.config(state='disabled')
            return

        entry = next((e for e in self.data['entries'] if e['id'] == item_id), None)
        if not entry: return

        # Enable/disable PDF button based on path existence
        if entry.get('pdf_path'):
            self.pdf_button.config(state='normal')
        else:
            self.pdf_button.config(state='disabled')

        # Enable/disable Video button based on link existence
        if entry.get('video_link'):
            self.video_button.config(state='normal')
        else:
            self.video_button.config(state='disabled')

    def show_context_menu(self, event):
        item_id = self.tree.identify_row(event.y)
        if item_id:
            self.tree.selection_set(item_id)
            self.context_menu.post(event.x_root, event.y_root)

    def populate_treeview(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        category = self.category_var.get()
        filtered_entries = [e for e in self.data['entries'] if category == "All Classes" or e.get('category') == category]
        filtered_entries.sort(key=lambda x: x['description'])

        self.tree.tag_configure('completed', foreground='green')
        self.tree.tag_configure('pending', foreground='black')

        for entry in filtered_entries:
            status_text = "☑" if entry.get('completed') else "☐"
            status_tag = 'completed' if entry.get('completed') else 'pending'
            pdf_text = "Yes" if entry.get('pdf_path') else "No"
            video_text = "Yes" if entry.get('video_link') else "No"
            
            self.tree.insert('', tk.END, iid=entry['id'],
                             values=(status_text, entry['description'], pdf_text, video_text, entry.get('notes', '')),
                             tags=(status_tag,))
        self.update_summary()
        self.on_selection_change()

    def update_summary(self):
        category = self.category_var.get()
        entries = [e for e in self.data['entries'] if category == "All Classes" or e.get('category') == category]
        total = len(entries)
        completed = sum(1 for e in entries if e.get('completed'))
        summary_text = f"Displaying: {category}   |   Total Items: {total}   |   ☑ Viewed: {completed}"
        self.summary_label.config(text=summary_text)

    def update_combobox_values(self):
        self.category_combo['values'] = ["All Classes"] + sorted(self.data['categories'])

    def get_selected_item_id(self):
        selection = self.tree.selection()
        return selection[0] if selection else None

    def edit_selected_entry(self):
        item_id = self.get_selected_item_id()
        if item_id:
            self.open_add_edit_window(item_id)

    def delete_selected_entry(self):
        item_id = self.get_selected_item_id()
        if not item_id: return
        
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the selected entry?"):
            self.data['entries'] = [e for e in self.data['entries'] if e['id'] != item_id]
            self.save_data()
            self.populate_treeview()

    def toggle_status(self, item_id):
        if not item_id: return
        for entry in self.data['entries']:
            if entry['id'] == item_id:
                entry['completed'] = not entry.get('completed', False)
                break
        self.save_data()
        self.populate_treeview()

    def open_link_or_file(self, file_type):
        item_id = self.get_selected_item_id()
        if not item_id:
            messagebox.showinfo("No Selection", "Please select an entry from the list first.")
            return

        entry = next((e for e in self.data['entries'] if e['id'] == item_id), None)
        if not entry: return
        
        path = ""
        if file_type == 'pdf':
            path = entry.get('pdf_path')
            if path and os.path.exists(path):
                try: os.startfile(path)
                except AttributeError: webbrowser.open(f'file://{os.path.realpath(path)}')
            elif path: messagebox.showwarning("Not Found", "The PDF file was not found at the specified path.")

        elif file_type == 'video':
            path = entry.get('video_link')
            if path and path.startswith(('http://', 'https://')):
                webbrowser.open_new_tab(path)
            elif path: messagebox.showwarning("Invalid Link", "The video link is not a valid URL.")

    def open_add_edit_window(self, item_id=None):
        AddEditWindow(self, self.data, self.save_data, self.populate_treeview, item_id)

    def open_category_manager(self):
        CategoryManager(self, self.data, self.save_data)


# Helper windows (AddEditWindow, CategoryManager) are unchanged and included for completeness.
class AddEditWindow(Toplevel):
    def __init__(self, parent, data, save_callback, refresh_callback, item_id=None):
        super().__init__(parent)
        self.transient(parent)
        self.grab_set()
        
        self.data = data
        self.save_callback = save_callback
        self.refresh_callback = refresh_callback
        self.item_id = item_id
        
        self.entry_data = {}
        if self.item_id:
            self.title("Edit Entry")
            self.entry_data = next((e for e in self.data['entries'] if e['id'] == self.item_id), {})
        else:
            self.title("Add New Entry")
        self.create_widgets()

    def create_widgets(self):
        frame = ttk.Frame(self, padding="15")
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frame, text="Category:").grid(row=0, column=0, sticky="w", pady=5)
        self.category_var = tk.StringVar(value=self.entry_data.get('category'))
        ttk.Combobox(frame, textvariable=self.category_var, values=sorted(self.data['categories']), state="readonly").grid(row=0, column=1, columnspan=2, sticky="ew")
        ttk.Label(frame, text="Description:").grid(row=1, column=0, sticky="w", pady=5)
        self.desc_var = tk.StringVar(value=self.entry_data.get('description', ''))
        ttk.Entry(frame, textvariable=self.desc_var).grid(row=1, column=1, columnspan=2, sticky="ew")
        ttk.Label(frame, text="PDF Path:").grid(row=2, column=0, sticky="w", pady=5)
        self.pdf_var = tk.StringVar(value=self.entry_data.get('pdf_path', ''))
        ttk.Entry(frame, textvariable=self.pdf_var).grid(row=2, column=1, sticky="ew")
        ttk.Button(frame, text="Browse...", command=self.browse_pdf).grid(row=2, column=2, padx=(5,0))
        ttk.Label(frame, text="Video Link:").grid(row=3, column=0, sticky="w", pady=5)
        self.video_var = tk.StringVar(value=self.entry_data.get('video_link', ''))
        ttk.Entry(frame, textvariable=self.video_var).grid(row=3, column=1, columnspan=2, sticky="ew")
        ttk.Label(frame, text="Special Note:").grid(row=4, column=0, sticky="nw", pady=5)
        self.notes_text = tk.Text(frame, height=5, width=40, font=('Segoe UI', 10))
        self.notes_text.insert(tk.END, self.entry_data.get('notes', ''))
        self.notes_text.grid(row=4, column=1, columnspan=2, sticky="ew")
        save_button = ttk.Button(frame, text="Save Entry", command=self.save_entry)
        save_button.grid(row=5, column=1, columnspan=2, sticky="e", pady=(20, 0))
        frame.columnconfigure(1, weight=1)

    def browse_pdf(self):
        filepath = filedialog.askopenfilename(title="Select PDF", filetypes=(("PDF Files", "*.pdf"),))
        if filepath:
            self.pdf_var.set(filepath)

    def save_entry(self):
        category = self.category_var.get()
        description = self.desc_var.get().strip()
        if not category or not description:
            messagebox.showerror("Validation Error", "Category and Description are required.", parent=self)
            return
        updated_data = {
            "category": category, "description": description,
            "pdf_path": self.pdf_var.get().strip(), "video_link": self.video_var.get().strip(),
            "notes": self.notes_text.get("1.0", tk.END).strip()
        }
        if self.item_id:
            for entry in self.data['entries']:
                if entry['id'] == self.item_id: entry.update(updated_data)
        else:
            updated_data['id'] = str(uuid.uuid4())
            updated_data['completed'] = False
            self.data['entries'].append(updated_data)
        self.save_callback()
        self.refresh_callback()
        self.destroy()

class CategoryManager(Toplevel):
    def __init__(self, parent, data, save_callback):
        super().__init__(parent)
        self.title("Manage Categories"); self.geometry("350x400"); self.transient(parent); self.grab_set()
        self.data = data; self.save_callback = save_callback
        frame = ttk.Frame(self, padding="15"); frame.pack(fill=tk.BOTH, expand=True)
        self.listbox = Listbox(frame, font=('Segoe UI', 10)); self.listbox.pack(fill=tk.BOTH, expand=True)
        self.refresh_list()
        entry_frame = ttk.Frame(frame, padding=(0, 10, 0, 0)); entry_frame.pack(fill=tk.X)
        self.new_cat_var = tk.StringVar()
        ttk.Entry(entry_frame, textvariable=self.new_cat_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(entry_frame, text="Add", command=self.add_category).pack(side=tk.LEFT, padx=(5,0))
        ttk.Button(frame, text="Remove Selected", command=self.remove_category).pack(fill=tk.X, pady=(5,0))
        ttk.Button(frame, text="Close", command=self.destroy).pack(fill=tk.X, pady=(5,0))

    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        for cat in sorted(self.data['categories']): self.listbox.insert(tk.END, cat)

    def add_category(self):
        new_cat = self.new_cat_var.get().strip()
        if new_cat and new_cat not in self.data['categories']:
            self.data['categories'].append(new_cat); self.save_callback(); self.refresh_list(); self.new_cat_var.set("")
        elif not new_cat: messagebox.showwarning("Input Error", "Category name cannot be empty.", parent=self)
        else: messagebox.showwarning("Duplicate", "This category already exists.", parent=self)
    
    def remove_category(self):
        selection = self.listbox.curselection()
        if not selection: messagebox.showwarning("Selection Error", "Please select a category to remove.", parent=self); return
        selected_cat = self.listbox.get(selection[0])
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to remove '{selected_cat}'?"):
            self.data['categories'].remove(selected_cat); self.save_callback(); self.refresh_list()

if __name__ == "__main__":
    app = AdithaAlamaApp()
    app.mainloop()