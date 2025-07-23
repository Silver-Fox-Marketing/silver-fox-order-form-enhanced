import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dealership_manager import DealershipManager

class FilterEditorUI:
    """GUI for editing dealership filter rules"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Dealership Filter Editor")
        self.root.geometry("1200x800")
        
        # Initialize dealership manager
        self.dealership_manager = DealershipManager()
        
        # Current dealership and filters
        self.current_dealership = None
        self.current_filters = {}
        
        # Setup UI
        self.setup_ui()
        self.load_dealerships()
    
    def setup_ui(self):
        """Setup the main UI components"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top frame for dealership selection
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Dealership selection
        ttk.Label(top_frame, text="Select Dealership:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.dealership_var = tk.StringVar()
        self.dealership_combo = ttk.Combobox(
            top_frame, 
            textvariable=self.dealership_var,
            state="readonly",
            width=40
        )
        self.dealership_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.dealership_combo.bind('<<ComboboxSelected>>', self.on_dealership_selected)
        
        # Refresh button
        ttk.Button(top_frame, text="Refresh", command=self.load_dealerships).pack(side=tk.LEFT, padx=(10, 0))
        
        # Paned window for left/right split
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Left frame for filter list
        left_frame = ttk.LabelFrame(paned_window, text="Filter Categories", padding=10)
        paned_window.add(left_frame, weight=1)
        
        # Filter category list
        self.filter_listbox = tk.Listbox(left_frame, height=15)
        self.filter_listbox.pack(fill=tk.BOTH, expand=True)
        self.filter_listbox.bind('<<ListboxSelect>>', self.on_filter_selected)
        
        # Add/Remove filter buttons
        filter_button_frame = ttk.Frame(left_frame)
        filter_button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(filter_button_frame, text="Add Filter", command=self.add_filter).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(filter_button_frame, text="Remove Filter", command=self.remove_filter).pack(side=tk.LEFT)
        
        # Right frame for filter editor
        right_frame = ttk.LabelFrame(paned_window, text="Filter Editor", padding=10)
        paned_window.add(right_frame, weight=2)
        
        # Filter editor notebook
        self.editor_notebook = ttk.Notebook(right_frame)
        self.editor_notebook.pack(fill=tk.BOTH, expand=True)
        
        self.setup_filter_editors()
        
        # Bottom frame for save/load buttons
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(bottom_frame, text="Save Changes", command=self.save_changes).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(bottom_frame, text="Export Config", command=self.export_config).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(bottom_frame, text="Import Config", command=self.import_config).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(bottom_frame, text="Reset to Default", command=self.reset_to_default).pack(side=tk.LEFT, padx=(10, 0))
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, pady=(5, 0))
    
    def setup_filter_editors(self):
        """Setup filter editor tabs"""
        
        # Price Range Editor
        self.price_frame = ttk.Frame(self.editor_notebook)
        self.editor_notebook.add(self.price_frame, text="Price Range")
        
        ttk.Label(self.price_frame, text="Minimum Price:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.price_min_var = tk.StringVar()
        ttk.Entry(self.price_frame, textvariable=self.price_min_var, width=15).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(self.price_frame, text="Maximum Price:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.price_max_var = tk.StringVar()
        ttk.Entry(self.price_frame, textvariable=self.price_max_var, width=15).grid(row=1, column=1, padx=5, pady=5)
        
        # Year Range Editor
        self.year_frame = ttk.Frame(self.editor_notebook)
        self.editor_notebook.add(self.year_frame, text="Year Range")
        
        ttk.Label(self.year_frame, text="Minimum Year:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.year_min_var = tk.StringVar()
        ttk.Entry(self.year_frame, textvariable=self.year_min_var, width=15).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(self.year_frame, text="Maximum Year:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.year_max_var = tk.StringVar()
        ttk.Entry(self.year_frame, textvariable=self.year_max_var, width=15).grid(row=1, column=1, padx=5, pady=5)
        
        # Make/Model Filters
        self.make_frame = ttk.Frame(self.editor_notebook)
        self.editor_notebook.add(self.make_frame, text="Make/Model")
        
        # Allowed makes
        ttk.Label(self.make_frame, text="Allowed Makes (one per line):").grid(row=0, column=0, sticky=tk.NW, padx=5, pady=5)
        self.allowed_makes_text = tk.Text(self.make_frame, height=8, width=30)
        self.allowed_makes_text.grid(row=1, column=0, padx=5, pady=5)
        
        # Excluded makes
        ttk.Label(self.make_frame, text="Excluded Makes (one per line):").grid(row=0, column=1, sticky=tk.NW, padx=5, pady=5)
        self.excluded_makes_text = tk.Text(self.make_frame, height=8, width=30)
        self.excluded_makes_text.grid(row=1, column=1, padx=5, pady=5)
        
        # Condition Filters
        self.condition_frame = ttk.Frame(self.editor_notebook)
        self.editor_notebook.add(self.condition_frame, text="Conditions")
        
        ttk.Label(self.condition_frame, text="Allowed Conditions:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.condition_vars = {}
        conditions = ['new', 'used', 'certified', 'demo']
        for i, condition in enumerate(conditions):
            var = tk.BooleanVar()
            self.condition_vars[condition] = var
            ttk.Checkbutton(self.condition_frame, text=condition.title(), variable=var).grid(
                row=1+i, column=0, sticky=tk.W, padx=20, pady=2
            )
        
        # Custom Filters
        self.custom_frame = ttk.Frame(self.editor_notebook)
        self.editor_notebook.add(self.custom_frame, text="Custom Filters")
        
        ttk.Label(self.custom_frame, text="Custom Filter JSON:").pack(anchor=tk.W, padx=5, pady=5)
        
        self.custom_text = tk.Text(self.custom_frame, height=20, width=80)
        self.custom_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add scrollbar to custom text
        custom_scrollbar = ttk.Scrollbar(self.custom_frame, orient=tk.VERTICAL, command=self.custom_text.yview)
        custom_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.custom_text.config(yscrollcommand=custom_scrollbar.set)
    
    def load_dealerships(self):
        """Load dealership list"""
        try:
            dealerships = self.dealership_manager.list_dealerships()
            
            # Clear and populate combobox
            self.dealership_combo['values'] = [
                f"{d['name']} ({d['id']})" for d in dealerships
            ]
            
            self.status_var.set(f"Loaded {len(dealerships)} dealerships")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load dealerships: {str(e)}")
    
    def on_dealership_selected(self, event):
        """Handle dealership selection"""
        try:
            selection = self.dealership_var.get()
            if not selection:
                return
            
            # Extract dealership ID from selection
            dealership_id = selection.split('(')[-1].rstrip(')')
            self.current_dealership = dealership_id
            
            # Load dealership configuration
            config = self.dealership_manager.get_dealership_config(dealership_id)
            if config:
                self.current_filters = config.get('filtering_rules', {}).get('conditional_filters', {})
                self.populate_filter_list()
                self.status_var.set(f"Loaded filters for {config.get('name', dealership_id)}")
            else:
                self.current_filters = {}
                self.populate_filter_list()
                self.status_var.set(f"No configuration found for {dealership_id}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load dealership config: {str(e)}")
    
    def populate_filter_list(self):
        """Populate the filter list"""
        self.filter_listbox.delete(0, tk.END)
        
        for filter_type in self.current_filters.keys():
            self.filter_listbox.insert(tk.END, filter_type)
    
    def on_filter_selected(self, event):
        """Handle filter selection"""
        try:
            selection = self.filter_listbox.curselection()
            if not selection:
                return
            
            filter_type = self.filter_listbox.get(selection[0])
            self.load_filter_editor(filter_type)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load filter: {str(e)}")
    
    def load_filter_editor(self, filter_type: str):
        """Load filter data into appropriate editor"""
        filter_data = self.current_filters.get(filter_type, {})
        
        if filter_type == 'price_range':
            self.price_min_var.set(str(filter_data.get('min', '')))
            self.price_max_var.set(str(filter_data.get('max', '')))
            self.editor_notebook.select(self.price_frame)
            
        elif filter_type == 'year_range':
            self.year_min_var.set(str(filter_data.get('min', '')))
            self.year_max_var.set(str(filter_data.get('max', '')))
            self.editor_notebook.select(self.year_frame)
            
        elif filter_type in ['allowed_makes', 'excluded_makes']:
            if filter_type == 'allowed_makes':
                self.allowed_makes_text.delete(1.0, tk.END)
                if isinstance(filter_data, list):
                    self.allowed_makes_text.insert(1.0, '\n'.join(filter_data))
            else:
                self.excluded_makes_text.delete(1.0, tk.END)
                if isinstance(filter_data, list):
                    self.excluded_makes_text.insert(1.0, '\n'.join(filter_data))
            self.editor_notebook.select(self.make_frame)
            
        elif filter_type == 'allowed_conditions':
            # Reset all condition checkboxes
            for var in self.condition_vars.values():
                var.set(False)
            
            # Set checked conditions
            if isinstance(filter_data, list):
                for condition in filter_data:
                    if condition in self.condition_vars:
                        self.condition_vars[condition].set(True)
            self.editor_notebook.select(self.condition_frame)
            
        else:
            # Custom filter - show as JSON
            self.custom_text.delete(1.0, tk.END)
            self.custom_text.insert(1.0, json.dumps(filter_data, indent=2))
            self.editor_notebook.select(self.custom_frame)
    
    def add_filter(self):
        """Add a new filter"""
        dialog = FilterTypeDialog(self.root, self.dealership_manager)
        if dialog.result:
            filter_type = dialog.result
            
            # Add empty filter
            if filter_type not in self.current_filters:
                if filter_type in ['price_range', 'year_range']:
                    self.current_filters[filter_type] = {'min': 0, 'max': 0}
                elif filter_type in ['allowed_makes', 'excluded_makes', 'allowed_conditions']:
                    self.current_filters[filter_type] = []
                else:
                    self.current_filters[filter_type] = {}
                
                self.populate_filter_list()
                self.status_var.set(f"Added filter: {filter_type}")
    
    def remove_filter(self):
        """Remove selected filter"""
        selection = self.filter_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a filter to remove")
            return
        
        filter_type = self.filter_listbox.get(selection[0])
        
        if messagebox.askyesno("Confirm", f"Remove filter '{filter_type}'?"):
            del self.current_filters[filter_type]
            self.populate_filter_list()
            self.status_var.set(f"Removed filter: {filter_type}")
    
    def save_changes(self):
        """Save current filter changes"""
        if not self.current_dealership:
            messagebox.showwarning("Warning", "Please select a dealership first")
            return
        
        try:
            # Collect data from editors
            self.collect_filter_data()
            
            # Update dealership filters
            filter_updates = {'conditional_filters': self.current_filters}
            
            success = self.dealership_manager.update_dealership_filters(
                self.current_dealership, filter_updates
            )
            
            if success:
                self.status_var.set("Changes saved successfully")
                messagebox.showinfo("Success", "Filter changes saved successfully")
            else:
                messagebox.showerror("Error", "Failed to save changes")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save changes: {str(e)}")
    
    def collect_filter_data(self):
        """Collect data from all editors"""
        # Price range
        if self.price_min_var.get() or self.price_max_var.get():
            price_filter = {}
            if self.price_min_var.get():
                price_filter['min'] = int(self.price_min_var.get())
            if self.price_max_var.get():
                price_filter['max'] = int(self.price_max_var.get())
            if price_filter:
                self.current_filters['price_range'] = price_filter
        
        # Year range
        if self.year_min_var.get() or self.year_max_var.get():
            year_filter = {}
            if self.year_min_var.get():
                year_filter['min'] = int(self.year_min_var.get())
            if self.year_max_var.get():
                year_filter['max'] = int(self.year_max_var.get())
            if year_filter:
                self.current_filters['year_range'] = year_filter
        
        # Makes
        allowed_makes = self.allowed_makes_text.get(1.0, tk.END).strip()
        if allowed_makes:
            self.current_filters['allowed_makes'] = [
                make.strip() for make in allowed_makes.split('\n') if make.strip()
            ]
        
        excluded_makes = self.excluded_makes_text.get(1.0, tk.END).strip()
        if excluded_makes:
            self.current_filters['excluded_makes'] = [
                make.strip() for make in excluded_makes.split('\n') if make.strip()
            ]
        
        # Conditions
        allowed_conditions = [
            condition for condition, var in self.condition_vars.items() if var.get()
        ]
        if allowed_conditions:
            self.current_filters['allowed_conditions'] = allowed_conditions
    
    def export_config(self):
        """Export dealership configuration"""
        if not self.current_dealership:
            messagebox.showwarning("Warning", "Please select a dealership first")
            return
        
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Export Dealership Configuration"
            )
            
            if filename:
                success = self.dealership_manager.export_dealership_config(
                    self.current_dealership, filename
                )
                
                if success:
                    messagebox.showinfo("Success", f"Configuration exported to {filename}")
                else:
                    messagebox.showerror("Error", "Failed to export configuration")
                    
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {str(e)}")
    
    def import_config(self):
        """Import dealership configuration"""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Import Dealership Configuration"
            )
            
            if filename:
                success = self.dealership_manager.import_dealership_config(filename)
                
                if success:
                    self.load_dealerships()
                    messagebox.showinfo("Success", f"Configuration imported from {filename}")
                else:
                    messagebox.showerror("Error", "Failed to import configuration")
                    
        except Exception as e:
            messagebox.showerror("Error", f"Import failed: {str(e)}")
    
    def reset_to_default(self):
        """Reset filters to default values"""
        if not self.current_dealership:
            messagebox.showwarning("Warning", "Please select a dealership first")
            return
        
        if messagebox.askyesno("Confirm", "Reset all filters to default values?"):
            self.current_filters = {
                'price_range': {'min': 1000, 'max': 500000},
                'year_range': {'min': 2000, 'max': 2024},
                'allowed_conditions': ['new', 'used']
            }
            self.populate_filter_list()
            self.status_var.set("Filters reset to default")
    
    def run(self):
        """Run the UI"""
        self.root.mainloop()

class FilterTypeDialog:
    """Dialog for selecting filter type to add"""
    
    def __init__(self, parent, dealership_manager):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add Filter")
        self.dialog.geometry("400x300")
        self.dialog.grab_set()
        
        # Filter types
        available_filters = dealership_manager.get_available_filter_types()
        
        ttk.Label(self.dialog, text="Select Filter Type:").pack(pady=10)
        
        self.filter_var = tk.StringVar()
        
        for filter_type, info in available_filters.items():
            ttk.Radiobutton(
                self.dialog,
                text=f"{filter_type} - {info['description']}",
                variable=self.filter_var,
                value=filter_type
            ).pack(anchor=tk.W, padx=20, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel_clicked).pack(side=tk.LEFT, padx=5)
    
    def ok_clicked(self):
        if self.filter_var.get():
            self.result = self.filter_var.get()
        self.dialog.destroy()
    
    def cancel_clicked(self):
        self.result = None
        self.dialog.destroy()

if __name__ == "__main__":
    app = FilterEditorUI()
    app.run()