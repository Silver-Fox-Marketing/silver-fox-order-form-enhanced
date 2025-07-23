#!/usr/bin/env python3
"""
Working GUI - GUARANTEED to show dealership names

This is the simplest, most reliable version that prioritizes function over form.
It WILL show dealership names in the GUI.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from pathlib import Path

class WorkingGUI:
    """Ultra-simple, reliable GUI that shows dealership names"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Silverfox Dealership Scraper - Working Version")
        self.root.geometry("900x600")
        
        self.dealerships = self.load_dealerships()
        self.setup_ui()
        
        print(f"✅ GUI started with {len(self.dealerships)} dealerships")
        print("Dealership names are now visible in the GUI!")
    
    def load_dealerships(self):
        """Load dealerships - bulletproof method"""
        dealerships = {}
        
        # Try to load from JSON files
        config_dir = Path(__file__).parent / "dealership_configs"
        
        if config_dir.exists():
            print(f"📁 Loading from: {config_dir}")
            json_files = list(config_dir.glob("*.json"))
            print(f"📄 Found {len(json_files)} JSON files")
            
            for json_file in json_files:
                try:
                    with open(json_file, 'r') as f:
                        config = json.load(f)
                    
                    dealer_id = config.get('id', json_file.stem)
                    name = config.get('name')
                    
                    if not name:
                        # Generate name from ID
                        name = dealer_id.replace('_', ' ').title()
                    
                    dealerships[dealer_id] = {
                        'name': name,
                        'id': dealer_id,
                        'base_url': config.get('base_url', ''),
                        'platform': config.get('api_platform', 'unknown'),
                        'config': config
                    }
                    
                    print(f"✓ {dealer_id} -> {name}")
                    
                except Exception as e:
                    print(f"✗ Error loading {json_file.name}: {e}")
        
        # Fallback if no files found
        if not dealerships:
            print("🔄 Using fallback dealerships")
            fallback = {
                'columbiahonda': 'Columbia Honda',
                'joemachenshyundai': 'Joe Machens Hyundai',
                'suntrupfordkirkwood': 'Suntrup Ford Kirkwood',
                'bmwstlouis': 'BMW of St. Louis',
                'hondafrontenac': 'Honda of Frontenac'
            }
            
            for dealer_id, name in fallback.items():
                dealerships[dealer_id] = {
                    'name': name,
                    'id': dealer_id,
                    'base_url': f'https://www.{dealer_id}.com',
                    'platform': 'unknown',
                    'config': {'name': name, 'id': dealer_id}
                }
        
        print(f"🎯 Total loaded: {len(dealerships)} dealerships")
        return dealerships
    
    def setup_ui(self):
        """Setup simple UI"""
        
        # Title
        title_frame = tk.Frame(self.root, bg='#2c3e50', height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, 
                              text="🚀 Silverfox Dealership Scraper",
                              font=('Arial', 16, 'bold'),
                              bg='#2c3e50', fg='white')
        title_label.pack(expand=True)
        
        # Status bar
        status_frame = tk.Frame(self.root, bg='#27ae60', height=30)
        status_frame.pack(fill=tk.X)
        status_frame.pack_propagate(False)
        
        status_label = tk.Label(status_frame,
                               text=f"✅ {len(self.dealerships)} dealerships loaded and ready",
                               bg='#27ae60', fg='white', font=('Arial', 10))
        status_label.pack(expand=True)
        
        # Main content
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Dealership list
        left_frame = tk.LabelFrame(main_frame, text="SELECT DEALERSHIPS", 
                                  font=('Arial', 10, 'bold'), pady=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Search
        search_frame = tk.Frame(left_frame)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(search_frame, text="🔍 Search:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.update_list)
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=('Arial', 10))
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Dealership listbox
        list_frame = tk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Listbox with scrollbar
        self.listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE, 
                                 font=('Arial', 10), height=20)
        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Quick select buttons
        button_frame = tk.Frame(left_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(button_frame, text="✅ Select All", command=self.select_all,
                 bg='#3498db', fg='white', font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=(0, 5))
        tk.Button(button_frame, text="❌ Clear All", command=self.clear_all,
                 bg='#e74c3c', fg='white', font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        
        # Right panel - Settings and actions
        right_frame = tk.LabelFrame(main_frame, text="SCAN SETTINGS", 
                                   font=('Arial', 10, 'bold'), pady=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        
        # Settings
        settings_inner = tk.Frame(right_frame)
        settings_inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Max vehicles
        tk.Label(settings_inner, text="Max vehicles per dealership:", 
                font=('Arial', 9, 'bold')).pack(anchor=tk.W)
        self.max_vehicles_var = tk.StringVar(value="50")
        max_entry = tk.Entry(settings_inner, textvariable=self.max_vehicles_var, 
                           width=10, font=('Arial', 10))
        max_entry.pack(anchor=tk.W, pady=(2, 10))
        
        # Vehicle types
        tk.Label(settings_inner, text="Vehicle types:", 
                font=('Arial', 9, 'bold')).pack(anchor=tk.W)
        
        self.vehicle_types = {}
        for vtype, label in [('new', 'New'), ('po', 'Pre-Owned'), ('cpo', 'Certified')]:
            var = tk.BooleanVar(value=True)
            self.vehicle_types[vtype] = var
            cb = tk.Checkbutton(settings_inner, text=label, variable=var, font=('Arial', 9))
            cb.pack(anchor=tk.W)
        
        # Selected info
        tk.Label(settings_inner, text="", height=1).pack()  # Spacer
        tk.Label(settings_inner, text="Selected dealerships:", 
                font=('Arial', 9, 'bold')).pack(anchor=tk.W)
        
        self.info_text = tk.Text(settings_inner, height=10, width=30, 
                               wrap=tk.WORD, font=('Arial', 9))
        info_scroll = tk.Scrollbar(settings_inner, orient=tk.VERTICAL, 
                                 command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=info_scroll.set)
        
        info_frame = tk.Frame(settings_inner)
        info_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.info_text.pack(in_=info_frame, side=tk.LEFT, fill=tk.BOTH, expand=True)
        info_scroll.pack(in_=info_frame, side=tk.RIGHT, fill=tk.Y)
        
        # Action buttons
        action_frame = tk.Frame(right_frame)
        action_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Big start button
        start_btn = tk.Button(action_frame, text="🚀 START SCAN", 
                             command=self.start_scan,
                             bg='#27ae60', fg='white', 
                             font=('Arial', 12, 'bold'), height=2)
        start_btn.pack(fill=tk.X, pady=(0, 5))
        
        # Other buttons
        tk.Button(action_frame, text="⚙️ Settings", command=self.open_settings,
                 bg='#f39c12', fg='white', font=('Arial', 10)).pack(fill=tk.X, pady=2)
        tk.Button(action_frame, text="📊 View Results", command=self.view_results,
                 bg='#9b59b6', fg='white', font=('Arial', 10)).pack(fill=tk.X, pady=2)
        
        # Populate the list
        self.populate_list()
        
        # Bind selection event
        self.listbox.bind('<<ListboxSelect>>', self.on_selection_changed)
        
        # Update info initially
        self.update_info()
    
    def populate_list(self):
        """Populate listbox with dealership names"""
        self.listbox.delete(0, tk.END)
        
        # Sort by name for better UX
        sorted_dealers = sorted(self.dealerships.items(), 
                               key=lambda x: x[1]['name'])
        
        for dealer_id, info in sorted_dealers:
            # Show NAME first, then ID in parentheses
            display_text = f"{info['name']} ({dealer_id})"
            self.listbox.insert(tk.END, display_text)
        
        print(f"📋 Populated list with {len(sorted_dealers)} dealership names")
    
    def update_list(self, *args):
        """Update list based on search"""
        search_term = self.search_var.get().lower()
        self.listbox.delete(0, tk.END)
        
        sorted_dealers = sorted(self.dealerships.items(), 
                               key=lambda x: x[1]['name'])
        
        for dealer_id, info in sorted_dealers:
            name = info['name'].lower()
            if search_term in name or search_term in dealer_id.lower():
                display_text = f"{info['name']} ({dealer_id})"
                self.listbox.insert(tk.END, display_text)
    
    def select_all(self):
        """Select all visible items"""
        self.listbox.select_set(0, tk.END)
        self.update_info()
    
    def clear_all(self):
        """Clear all selections"""
        self.listbox.selection_clear(0, tk.END)
        self.update_info()
    
    def on_selection_changed(self, event=None):
        """Handle selection changes"""
        self.update_info()
    
    def update_info(self):
        """Update the selection info display"""
        selected_indices = self.listbox.curselection()
        
        self.info_text.delete(1.0, tk.END)
        
        if not selected_indices:
            self.info_text.insert(tk.END, "No dealerships selected.\n\n")
            self.info_text.insert(tk.END, "Select dealerships from the list to begin scanning.")
        else:
            self.info_text.insert(tk.END, f"Selected: {len(selected_indices)} dealerships\n\n")
            
            for i, index in enumerate(selected_indices):
                if i < 10:  # Show first 10
                    item_text = self.listbox.get(index)
                    # Extract just the name part (before the parentheses)
                    name = item_text.split(' (')[0]
                    self.info_text.insert(tk.END, f"• {name}\n")
                elif i == 10:
                    remaining = len(selected_indices) - 10
                    self.info_text.insert(tk.END, f"... and {remaining} more\n")
                    break
            
            estimated_time = len(selected_indices) * 3
            self.info_text.insert(tk.END, f"\nEstimated time: ~{estimated_time} minutes")
    
    def start_scan(self):
        """Start the scan"""
        selected_indices = self.listbox.curselection()
        
        if not selected_indices:
            messagebox.showwarning("No Selection", 
                                  "Please select at least one dealership to scan.")
            return
        
        # Get selected dealerships
        selected_dealers = []
        for index in selected_indices:
            item_text = self.listbox.get(index)
            # Extract dealer_id from "Name (dealer_id)" format
            dealer_id = item_text.split('(')[-1].rstrip(')')
            if dealer_id in self.dealerships:
                selected_dealers.append(dealer_id)
        
        # Validate settings
        try:
            max_vehicles = int(self.max_vehicles_var.get())
            if max_vehicles < 1 or max_vehicles > 1000:
                raise ValueError("Max vehicles must be between 1 and 1000")
        except ValueError as e:
            messagebox.showerror("Invalid Setting", str(e))
            return
        
        # Get vehicle types
        selected_types = [vtype for vtype, var in self.vehicle_types.items() if var.get()]
        if not selected_types:
            messagebox.showwarning("No Vehicle Types", 
                                  "Please select at least one vehicle type.")
            return
        
        # Show confirmation
        dealer_names = [self.dealerships[d]['name'] for d in selected_dealers]
        message = f"Start scan for {len(selected_dealers)} dealerships?\n\n"
        message += "\n".join(f"• {name}" for name in dealer_names[:8])
        if len(dealer_names) > 8:
            message += f"\n... and {len(dealer_names) - 8} more"
        
        message += f"\n\nSettings:\n• Max vehicles: {max_vehicles}"
        message += f"\n• Vehicle types: {', '.join(selected_types)}"
        
        if messagebox.askyesno("Confirm Scan", message):
            self.execute_scan(selected_dealers, max_vehicles, selected_types)
    
    def execute_scan(self, dealer_ids, max_vehicles, vehicle_types):
        """Execute the scan (demo version)"""
        # Create scan configuration
        scan_config = {
            'dealerships': dealer_ids,
            'max_vehicles': max_vehicles,
            'vehicle_types': vehicle_types,
            'configs': {}
        }
        
        # Add configurations for selected dealerships
        for dealer_id in dealer_ids:
            scan_config['configs'][dealer_id] = self.dealerships[dealer_id]['config']
        
        # Show the configuration window
        config_window = tk.Toplevel(self.root)
        config_window.title("Scan Configuration Ready")
        config_window.geometry("700x500")
        config_window.grab_set()
        
        # Header
        header_frame = tk.Frame(config_window, bg='#27ae60', height=50)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="✅ Scan Configuration Generated", 
                font=('Arial', 14, 'bold'), bg='#27ae60', fg='white').pack(expand=True)
        
        # Content
        content_frame = tk.Frame(config_window)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content_frame, text="The following configuration would be used for scanning:",
                font=('Arial', 10)).pack(anchor=tk.W, pady=(0, 10))
        
        # Configuration display
        config_text = tk.Text(content_frame, wrap=tk.WORD, font=('Courier', 9))
        config_scroll = tk.Scrollbar(content_frame, orient=tk.VERTICAL, command=config_text.yview)
        config_text.configure(yscrollcommand=config_scroll.set)
        
        config_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        config_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Insert configuration
        config_json = json.dumps(scan_config, indent=2)
        config_text.insert(tk.END, config_json)
        
        # Buttons
        button_frame = tk.Frame(config_window)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Button(button_frame, text="✅ Looks Good", command=config_window.destroy,
                 bg='#27ae60', fg='white', font=('Arial', 10, 'bold')).pack(side=tk.RIGHT, padx=5)
        tk.Button(button_frame, text="📋 Copy Config", 
                 command=lambda: self.copy_to_clipboard(config_json),
                 bg='#3498db', fg='white', font=('Arial', 10)).pack(side=tk.RIGHT, padx=5)
        
        messagebox.showinfo("Scan Ready", 
                           f"✅ Scan configuration prepared for {len(dealer_ids)} dealerships!\n\n"
                           "In a production environment, this would start the actual scraping process.")
    
    def copy_to_clipboard(self, text):
        """Copy text to clipboard"""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("Copied", "Configuration copied to clipboard!")
    
    def open_settings(self):
        """Open settings for a selected dealership"""
        selected_indices = self.listbox.curselection()
        
        if not selected_indices:
            messagebox.showinfo("No Selection", 
                               "Please select a dealership first to view its settings.")
            return
        
        # Use first selected dealership
        index = selected_indices[0]
        item_text = self.listbox.get(index)
        dealer_id = item_text.split('(')[-1].rstrip(')')
        
        if dealer_id not in self.dealerships:
            return
        
        dealer_info = self.dealerships[dealer_id]
        
        # Simple settings window
        settings_window = tk.Toplevel(self.root)
        settings_window.title(f"Settings - {dealer_info['name']}")
        settings_window.geometry("600x400")
        settings_window.grab_set()
        
        # Header
        header_frame = tk.Frame(settings_window, bg='#34495e', height=50)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text=f"⚙️ {dealer_info['name']}", 
                font=('Arial', 14, 'bold'), bg='#34495e', fg='white').pack(expand=True)
        
        # Content
        content_frame = tk.Frame(settings_window)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Basic info
        info_frame = tk.LabelFrame(content_frame, text="Dealership Information", pady=10)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(info_frame, text=f"Name: {dealer_info['name']}", 
                font=('Arial', 10, 'bold')).pack(anchor=tk.W, padx=10)
        tk.Label(info_frame, text=f"ID: {dealer_id}").pack(anchor=tk.W, padx=10)
        tk.Label(info_frame, text=f"Platform: {dealer_info['platform']}").pack(anchor=tk.W, padx=10)
        if dealer_info['base_url']:
            tk.Label(info_frame, text=f"URL: {dealer_info['base_url']}", 
                    fg='blue').pack(anchor=tk.W, padx=10)
        
        # Configuration
        config_frame = tk.LabelFrame(content_frame, text="Configuration", pady=10)
        config_frame.pack(fill=tk.BOTH, expand=True)
        
        config_text = tk.Text(config_frame, wrap=tk.WORD, font=('Courier', 9))
        config_scroll = tk.Scrollbar(config_frame, orient=tk.VERTICAL, command=config_text.yview)
        config_text.configure(yscrollcommand=config_scroll.set)
        
        config_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        config_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        config_json = json.dumps(dealer_info['config'], indent=2)
        config_text.insert(tk.END, config_json)
        
        # Close button
        tk.Button(settings_window, text="Close", command=settings_window.destroy,
                 bg='#95a5a6', fg='white', font=('Arial', 10)).pack(pady=10)
    
    def view_results(self):
        """View scan results"""
        output_dir = Path(__file__).parent / "output_data"
        
        if output_dir.exists():
            csv_files = list(output_dir.glob("*.csv"))
            json_files = list(output_dir.glob("*.json"))
            
            total_files = len(csv_files) + len(json_files)
            
            if total_files > 0:
                message = f"📊 Found {total_files} result files:\n\n"
                message += f"• {len(csv_files)} CSV files\n"
                message += f"• {len(json_files)} JSON files\n\n"
                message += f"Location: {output_dir}"
                messagebox.showinfo("Scan Results", message)
            else:
                messagebox.showinfo("No Results", 
                                   "No result files found.\n\nRun a scan first to generate results.")
        else:
            messagebox.showinfo("No Results", 
                               "Output directory not found.\n\nRun a scan first to create results.")
    
    def run(self):
        """Run the GUI"""
        print("🚀 Starting Working GUI...")
        print("All dealership names should be visible!")
        self.root.mainloop()

def main():
    """Main function"""
    print("=" * 60)
    print("🚀 SILVERFOX DEALERSHIP SCRAPER - WORKING VERSION")
    print("=" * 60)
    print("This version guarantees that dealership names will be displayed!")
    print()
    
    try:
        app = WorkingGUI()
        app.run()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()