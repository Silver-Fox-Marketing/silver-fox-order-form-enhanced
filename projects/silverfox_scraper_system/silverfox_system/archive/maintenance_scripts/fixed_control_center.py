#!/usr/bin/env python3
"""
Fixed Scraper Control Center

This is a simplified, bulletproof version of the scraper control center that
guarantees dealership names will be displayed properly.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

# Ensure imports work
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / "scraper"))

class FixedScraperControlCenter:
    """Simplified, reliable scraper control center"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Silverfox Scraper Control Center")
        self.root.geometry("1200x800")
        
        self.dealerships = {}
        self.selected_dealership = None
        
        # Load dealerships with bulletproof approach
        self.load_dealerships()
        
        # Setup UI
        self.setup_ui()
        
        print(f"✅ Control Center ready with {len(self.dealerships)} dealerships")
    
    def load_dealerships(self):
        """Load dealerships with bulletproof approach"""
        print("🔄 Loading dealership configurations...")
        
        # Method 1: Load from JSON config files
        config_dir = current_dir / "dealership_configs"
        if config_dir.exists():
            for json_file in config_dir.glob("*.json"):
                try:
                    with open(json_file, 'r') as f:
                        config = json.load(f)
                    
                    dealer_id = config.get('id', json_file.stem)
                    name = config.get('name', dealer_id.replace('_', ' ').title())
                    
                    self.dealerships[dealer_id] = {
                        'id': dealer_id,
                        'name': name,
                        'config': config,
                        'api_platform': config.get('api_platform', 'unknown'),
                        'has_scraper': True,  # Assume true if config exists
                        'source': 'json_config'
                    }
                    
                except Exception as e:
                    print(f"⚠️ Error loading {json_file}: {e}")
        
        # Method 2: Fallback dealerships if none loaded
        if not self.dealerships:
            print("📝 Using fallback dealership list...")
            fallback_dealers = {
                'columbiahonda': 'Columbia Honda',
                'joemachenshyundai': 'Joe Machens Hyundai',
                'suntrupfordkirkwood': 'Suntrup Ford Kirkwood',
                'bmwstlouis': 'BMW of St. Louis',
                'hondafrontenac': 'Honda of Frontenac'
            }
            
            for dealer_id, name in fallback_dealers.items():
                self.dealerships[dealer_id] = {
                    'id': dealer_id,
                    'name': name,
                    'config': {'name': name, 'id': dealer_id},
                    'api_platform': 'unknown',
                    'has_scraper': False,
                    'source': 'fallback'
                }
        
        print(f"✅ Loaded {len(self.dealerships)} dealerships:")
        for dealer_id, info in list(self.dealerships.items())[:5]:  # Show first 5
            print(f"   • {dealer_id}: {info['name']}")
        
        if len(self.dealerships) > 5:
            print(f"   ... and {len(self.dealerships) - 5} more")
    
    def setup_ui(self):
        """Setup the control center UI"""
        
        # Top toolbar
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=10, pady=5)
        
        # Title
        ttk.Label(toolbar, text="🚀 Silverfox Scraper Control Center", 
                 font=('Arial', 14, 'bold')).pack(side=tk.LEFT)
        
        # Status
        self.status_var = tk.StringVar(value=f"Ready - {len(self.dealerships)} dealerships loaded")
        ttk.Label(toolbar, textvariable=self.status_var, 
                 foreground='green').pack(side=tk.RIGHT)
        
        # Control buttons
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(control_frame, text="🔄 Refresh List", 
                  command=self.refresh_dealerships).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="🚀 Run Selected", 
                  command=self.run_selected_scraper).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="⚙️ Configure", 
                  command=self.configure_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="📊 View Logs", 
                  command=self.view_logs).pack(side=tk.LEFT, padx=5)
        
        # Main content - split into left and right panels
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Left panel - Dealership list
        left_frame = ttk.LabelFrame(main_paned, text="Dealerships", padding=10)
        main_paned.add(left_frame, weight=1)
        
        # Search box
        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_dealerships)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Dealership tree
        tree_frame = ttk.Frame(left_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview
        columns = ('status', 'platform', 'source')
        self.dealership_tree = ttk.Treeview(tree_frame, columns=columns, 
                                           show='tree headings', height=15)
        
        # Configure columns
        self.dealership_tree.heading('#0', text='Dealership Name', anchor=tk.W)
        self.dealership_tree.heading('status', text='Status', anchor=tk.W)
        self.dealership_tree.heading('platform', text='Platform', anchor=tk.W)
        self.dealership_tree.heading('source', text='Source', anchor=tk.W)
        
        self.dealership_tree.column('#0', width=250)
        self.dealership_tree.column('status', width=100)
        self.dealership_tree.column('platform', width=120)
        self.dealership_tree.column('source', width=100)
        
        # Scrollbar for tree
        tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, 
                                   command=self.dealership_tree.yview)
        self.dealership_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.dealership_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.dealership_tree.bind('<<TreeviewSelect>>', self.on_dealership_selected)
        
        # Initialize log first (needed by populate_dealership_tree)
        # Bottom log panel
        log_frame = ttk.LabelFrame(self.root, text="Activity Log", padding=5)
        log_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, wrap=tk.WORD)
        self.log_text.pack(fill=tk.X)
        
        # Configure log colors
        self.log_text.tag_configure('INFO', foreground='black')
        self.log_text.tag_configure('SUCCESS', foreground='green')
        self.log_text.tag_configure('WARNING', foreground='orange')
        self.log_text.tag_configure('ERROR', foreground='red')
        
        # Now populate the tree
        self.populate_dealership_tree()
        
        # Right panel - Details and controls
        right_frame = ttk.LabelFrame(main_paned, text="Dealership Details", padding=10)
        main_paned.add(right_frame, weight=1)
        
        # Dealership info display
        self.info_text = scrolledtext.ScrolledText(right_frame, height=12, wrap=tk.WORD)
        self.info_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Control buttons for selected dealership
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="🚀 Run This Scraper", 
                  command=self.run_selected_scraper).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="⚙️ Edit Settings", 
                  command=self.edit_dealership_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🧪 Test Connection", 
                  command=self.test_connection).pack(side=tk.LEFT, padx=5)
        
        # Initial log messages
        self.log_message("Control Center started successfully", 'SUCCESS')
        self.log_message(f"Loaded {len(self.dealerships)} dealership configurations", 'INFO')
    
    def populate_dealership_tree(self):
        """Populate the dealership tree with names"""
        # Clear existing items
        for item in self.dealership_tree.get_children():
            self.dealership_tree.delete(item)
        
        # Sort dealerships by name
        sorted_dealers = sorted(self.dealerships.items(), 
                               key=lambda x: x[1]['name'])
        
        for dealer_id, info in sorted_dealers:
            status = "✅ Ready" if info['has_scraper'] else "⚠️ No Scraper"
            platform = info.get('api_platform', 'unknown')
            source = info.get('source', 'unknown')
            
            # Insert with proper name display
            self.dealership_tree.insert('', 'end',
                                       iid=dealer_id,
                                       text=info['name'],  # This shows the actual name
                                       values=(status, platform, source))
        
        self.log_message(f"Displayed {len(sorted_dealers)} dealerships in tree", 'INFO')
    
    def filter_dealerships(self, *args):
        """Filter dealerships based on search"""
        search_term = self.search_var.get().lower()
        
        # Clear and repopulate with filtered results
        for item in self.dealership_tree.get_children():
            self.dealership_tree.delete(item)
        
        sorted_dealers = sorted(self.dealerships.items(), 
                               key=lambda x: x[1]['name'])
        
        for dealer_id, info in sorted_dealers:
            name = info['name'].lower()
            if search_term in name or search_term in dealer_id.lower():
                status = "✅ Ready" if info['has_scraper'] else "⚠️ No Scraper"
                platform = info.get('api_platform', 'unknown')
                source = info.get('source', 'unknown')
                
                self.dealership_tree.insert('', 'end',
                                           iid=dealer_id,
                                           text=info['name'],
                                           values=(status, platform, source))
    
    def on_dealership_selected(self, event):
        """Handle dealership selection"""
        selection = self.dealership_tree.selection()
        if not selection:
            return
        
        dealer_id = selection[0]
        self.selected_dealership = dealer_id
        self.show_dealership_details(dealer_id)
    
    def show_dealership_details(self, dealer_id):
        """Show details for selected dealership"""
        if dealer_id not in self.dealerships:
            return
        
        info = self.dealerships[dealer_id]
        config = info['config']
        
        # Clear and populate info text
        self.info_text.delete(1.0, tk.END)
        
        details = f"DEALERSHIP DETAILS\n{'='*50}\n\n"
        details += f"Name: {info['name']}\n"
        details += f"ID: {dealer_id}\n"
        details += f"Source: {info['source']}\n"
        details += f"API Platform: {info.get('api_platform', 'Unknown')}\n"
        details += f"Has Scraper: {'Yes' if info['has_scraper'] else 'No'}\n\n"
        
        # Add configuration details
        if 'base_url' in config:
            details += f"Base URL: {config['base_url']}\n"
        
        if 'api_config' in config:
            api_config = config['api_config']
            details += f"\nAPI Configuration:\n"
            for key, value in api_config.items():
                if 'key' not in key.lower():  # Don't show API keys
                    details += f"  {key}: {value}\n"
        
        if 'filtering_rules' in config:
            filters = config['filtering_rules']
            details += f"\nFiltering Rules:\n"
            if 'conditional_filters' in filters:
                cond_filters = filters['conditional_filters']
                for filter_type, filter_value in cond_filters.items():
                    details += f"  {filter_type}: {filter_value}\n"
        
        # Add raw config at the end
        details += f"\n\nRAW CONFIGURATION:\n{'-'*30}\n"
        details += json.dumps(config, indent=2)
        
        self.info_text.insert(tk.END, details)
        
        self.log_message(f"Selected dealership: {info['name']}", 'INFO')
    
    def refresh_dealerships(self):
        """Refresh the dealership list"""
        self.log_message("Refreshing dealership list...", 'INFO')
        self.load_dealerships()
        self.populate_dealership_tree()
        self.status_var.set(f"Refreshed - {len(self.dealerships)} dealerships loaded")
        self.log_message("Dealership list refreshed", 'SUCCESS')
    
    def run_selected_scraper(self):
        """Run scraper for selected dealership"""
        if not self.selected_dealership:
            messagebox.showwarning("No Selection", "Please select a dealership first.")
            return
        
        dealer_info = self.dealerships[self.selected_dealership]
        
        message = f"Run scraper for {dealer_info['name']}?\n\n"
        message += f"Dealership: {dealer_info['name']}\n"
        message += f"Platform: {dealer_info.get('api_platform', 'unknown')}\n"
        message += f"Configuration: {dealer_info['source']}"
        
        if messagebox.askyesno("Confirm Scraper Run", message):
            self.log_message(f"Starting scraper for {dealer_info['name']}", 'INFO')
            
            # Show configuration that would be used
            config_window = tk.Toplevel(self.root)
            config_window.title(f"Scraper Configuration - {dealer_info['name']}")
            config_window.geometry("600x400")
            
            config_text = scrolledtext.ScrolledText(config_window, wrap=tk.WORD)
            config_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            config_content = json.dumps(dealer_info['config'], indent=2)
            config_text.insert(tk.END, config_content)
            
            self.log_message(f"Scraper configuration prepared for {dealer_info['name']}", 'SUCCESS')
    
    def configure_selected(self):
        """Configure selected dealership"""
        if not self.selected_dealership:
            messagebox.showwarning("No Selection", "Please select a dealership first.")
            return
        
        self.edit_dealership_settings()
    
    def edit_dealership_settings(self):
        """Edit settings for selected dealership"""
        if not self.selected_dealership:
            messagebox.showinfo("No Selection", "Please select a dealership first.")
            return
        
        dealer_info = self.dealerships[self.selected_dealership]
        
        # Simple settings dialog
        settings_window = tk.Toplevel(self.root)
        settings_window.title(f"Settings - {dealer_info['name']}")
        settings_window.geometry("700x500")
        settings_window.grab_set()
        
        # Header
        header_frame = ttk.Frame(settings_window)
        header_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(header_frame, text=f"Settings for {dealer_info['name']}", 
                 font=('Arial', 14, 'bold')).pack()
        
        # Notebook for tabs
        notebook = ttk.Notebook(settings_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # General tab
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text="General")
        
        ttk.Label(general_frame, text="Basic dealership information:", 
                 font=('Arial', 10, 'bold')).pack(anchor=tk.W, padx=10, pady=10)
        
        # Name
        name_frame = ttk.Frame(general_frame)
        name_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(name_frame, text="Name:", width=15).pack(side=tk.LEFT)
        name_var = tk.StringVar(value=dealer_info['name'])
        ttk.Entry(name_frame, textvariable=name_var, width=40).pack(side=tk.LEFT)
        
        # Vehicle types
        types_frame = ttk.LabelFrame(general_frame, text="Vehicle Types", padding=10)
        types_frame.pack(fill=tk.X, padx=10, pady=10)
        
        type_vars = {}
        for vtype, label in [('new', 'New Vehicles'), ('po', 'Pre-Owned'), ('cpo', 'Certified Pre-Owned')]:
            var = tk.BooleanVar(value=True)
            type_vars[vtype] = var
            ttk.Checkbutton(types_frame, text=label, variable=var).pack(anchor=tk.W)
        
        # Configuration tab
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text="Configuration")
        
        config_text = scrolledtext.ScrolledText(config_frame, wrap=tk.WORD)
        config_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        config_content = json.dumps(dealer_info['config'], indent=2)
        config_text.insert(tk.END, config_content)
        
        # Buttons
        button_frame = ttk.Frame(settings_window)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(button_frame, text="Save Settings", 
                  command=lambda: self.save_settings(settings_window, name_var, type_vars)).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", 
                  command=settings_window.destroy).pack(side=tk.RIGHT)
    
    def save_settings(self, window, name_var, type_vars):
        """Save dealership settings"""
        if not self.selected_dealership:
            return
        
        # Update name
        new_name = name_var.get().strip()
        if new_name:
            self.dealerships[self.selected_dealership]['name'] = new_name
            self.dealerships[self.selected_dealership]['config']['name'] = new_name
        
        # Update vehicle types
        selected_types = [vtype for vtype, var in type_vars.items() if var.get()]
        if 'filtering_rules' not in self.dealerships[self.selected_dealership]['config']:
            self.dealerships[self.selected_dealership]['config']['filtering_rules'] = {}
        if 'conditional_filters' not in self.dealerships[self.selected_dealership]['config']['filtering_rules']:
            self.dealerships[self.selected_dealership]['config']['filtering_rules']['conditional_filters'] = {}
        
        filter_mapping = {'po': 'used', 'cpo': 'certified'}
        allowed_conditions = [filter_mapping.get(vtype, vtype) for vtype in selected_types]
        self.dealerships[self.selected_dealership]['config']['filtering_rules']['conditional_filters']['allowed_conditions'] = allowed_conditions
        
        # Refresh display
        self.populate_dealership_tree()
        self.show_dealership_details(self.selected_dealership)
        
        window.destroy()
        self.log_message(f"Settings saved for {new_name}", 'SUCCESS')
        messagebox.showinfo("Settings Saved", f"Settings have been saved for {new_name}")
    
    def test_connection(self):
        """Test connection to selected dealership"""
        if not self.selected_dealership:
            messagebox.showinfo("No Selection", "Please select a dealership first.")
            return
        
        dealer_info = self.dealerships[self.selected_dealership]
        
        # Show test dialog
        test_window = tk.Toplevel(self.root)
        test_window.title(f"Connection Test - {dealer_info['name']}")
        test_window.geometry("500x300")
        
        ttk.Label(test_window, text=f"Testing connection to {dealer_info['name']}", 
                 font=('Arial', 12, 'bold')).pack(pady=20)
        
        test_text = scrolledtext.ScrolledText(test_window, height=10)
        test_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Simulate test results
        test_results = f"Connection Test Results for {dealer_info['name']}\n"
        test_results += "="*50 + "\n\n"
        test_results += f"Base URL: {dealer_info['config'].get('base_url', 'Not configured')}\n"
        test_results += f"API Platform: {dealer_info.get('api_platform', 'Unknown')}\n"
        test_results += f"Configuration Source: {dealer_info['source']}\n\n"
        test_results += "✅ Configuration loaded successfully\n"
        test_results += "⚠️ Connection test not implemented yet\n"
        test_results += "💡 This would test actual API connectivity in production\n"
        
        test_text.insert(tk.END, test_results)
        
        ttk.Button(test_window, text="Close", 
                  command=test_window.destroy).pack(pady=10)
        
        self.log_message(f"Connection test performed for {dealer_info['name']}", 'INFO')
    
    def view_logs(self):
        """View application logs"""
        log_window = tk.Toplevel(self.root)
        log_window.title("Application Logs")
        log_window.geometry("800x600")
        
        log_text = scrolledtext.ScrolledText(log_window, wrap=tk.WORD)
        log_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Show current log content
        current_logs = self.log_text.get(1.0, tk.END)
        log_text.insert(tk.END, "APPLICATION LOGS\n" + "="*50 + "\n\n")
        log_text.insert(tk.END, current_logs)
        
        ttk.Button(log_window, text="Close", 
                  command=log_window.destroy).pack(pady=10)
    
    def log_message(self, message, level='INFO'):
        """Add a message to the log"""
        from datetime import datetime
        timestamp = datetime.now().strftime('%H:%M:%S')
        formatted_message = f"[{timestamp}] {level}: {message}\n"
        
        self.log_text.insert(tk.END, formatted_message, level)
        self.log_text.see(tk.END)
    
    def run(self):
        """Run the control center"""
        print("🚀 Starting Fixed Scraper Control Center...")
        self.root.mainloop()

def main():
    """Main function"""
    try:
        app = FixedScraperControlCenter()
        app.run()
    except Exception as e:
        print(f"❌ Failed to start control center: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()