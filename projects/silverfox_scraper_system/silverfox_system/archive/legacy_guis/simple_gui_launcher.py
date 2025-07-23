#!/usr/bin/env python3
"""
Simple GUI Launcher - Bulletproof Version

This is a simplified, reliable GUI that guarantees dealership names will display.
Prioritizes functionality over polish.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import json
from pathlib import Path

# Add paths to ensure imports work
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / "scraper"))
sys.path.insert(0, str(current_dir / "scraper" / "ui"))

class SimpleDealershipGUI:
    """Simple, reliable GUI for dealership scanning"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Silverfox Dealership Scraper")
        self.root.geometry("800x600")
        
        self.dealerships = {}
        self.selected_dealerships = []
        
        self.load_dealerships()
        self.setup_ui()
    
    def load_dealerships(self):
        """Load dealerships from any available source - bulletproof approach"""
        print("Loading dealership configurations...")
        
        # Method 1: Try JSON config files (most reliable)
        config_dir = current_dir / "dealership_configs"
        if config_dir.exists():
            for json_file in config_dir.glob("*.json"):
                try:
                    with open(json_file, 'r') as f:
                        config = json.load(f)
                    
                    dealer_id = config.get('id', json_file.stem)
                    name = config.get('name', dealer_id.replace('_', ' ').title())
                    
                    self.dealerships[dealer_id] = {
                        'name': name,
                        'id': dealer_id,
                        'config': config,
                        'source': 'json_config'
                    }
                    print(f"✓ Loaded: {dealer_id} -> {name}")
                    
                except Exception as e:
                    print(f"✗ Error loading {json_file}: {e}")
        
        # Method 2: Hardcoded reliable dealerships if JSON fails
        if not self.dealerships:
            print("No JSON configs found, using hardcoded dealerships...")
            hardcoded = {
                'columbiahonda': {
                    'name': 'Columbia Honda',
                    'base_url': 'https://www.columbiahonda.com',
                    'brand': 'Honda',
                    'locality': 'Columbia'
                },
                'joemachenshyundai': {
                    'name': 'Joe Machens Hyundai', 
                    'base_url': 'https://www.joemachenshyundai.com',
                    'brand': 'Hyundai',
                    'locality': 'Columbia'
                },
                'suntrupfordkirkwood': {
                    'name': 'Suntrup Ford Kirkwood',
                    'base_url': 'https://www.suntrupfordkirkwood.com',
                    'brand': 'Ford',
                    'locality': 'Kirkwood'
                },
                'bmwstlouis': {
                    'name': 'BMW of St. Louis',
                    'base_url': 'https://www.bmwstlouis.com',
                    'brand': 'BMW',
                    'locality': 'St. Louis'
                }
            }
            
            for dealer_id, config in hardcoded.items():
                self.dealerships[dealer_id] = {
                    'name': config['name'],
                    'id': dealer_id,
                    'config': config,
                    'source': 'hardcoded'
                }
                print(f"✓ Added hardcoded: {dealer_id} -> {config['name']}")
        
        print(f"Total dealerships loaded: {len(self.dealerships)}")
        
        # Debug: Print all loaded dealerships
        print("\nAll loaded dealerships:")
        for dealer_id, info in self.dealerships.items():
            print(f"  {dealer_id}: {info['name']} ({info['source']})")
    
    def setup_ui(self):
        """Setup simple, functional UI"""
        
        # Title
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill=tk.X, padx=10, pady=5)
        
        title_label = ttk.Label(title_frame, 
                               text="🚀 Silverfox Dealership Scraper", 
                               font=('Arial', 14, 'bold'))
        title_label.pack()
        
        status_text = f"Loaded {len(self.dealerships)} dealerships"
        status_label = ttk.Label(title_frame, text=status_text, foreground='green')
        status_label.pack()
        
        # Main content
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Dealership list
        list_frame = ttk.LabelFrame(main_frame, text="Select Dealerships to Scan", padding=10)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Search box
        search_frame = ttk.Frame(list_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_dealerships)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Quick select buttons
        button_frame = ttk.Frame(list_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(button_frame, text="Select All", 
                  command=self.select_all).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Clear All", 
                  command=self.clear_all).pack(side=tk.LEFT)
        
        # Dealership listbox with scrollbar
        listbox_frame = ttk.Frame(list_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create listbox
        self.dealership_listbox = tk.Listbox(listbox_frame, selectmode=tk.MULTIPLE)
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, 
                                 command=self.dealership_listbox.yview)
        self.dealership_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.dealership_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate listbox
        self.populate_dealership_list()
        
        # Settings panel
        settings_frame = ttk.LabelFrame(main_frame, text="Scan Settings", padding=10)
        settings_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        # Max vehicles setting
        ttk.Label(settings_frame, text="Max vehicles per dealership:").pack(anchor=tk.W)
        self.max_vehicles_var = tk.StringVar(value="50")
        ttk.Entry(settings_frame, textvariable=self.max_vehicles_var, width=10).pack(anchor=tk.W, pady=(0, 10))
        
        # Vehicle types
        ttk.Label(settings_frame, text="Vehicle types to scan:").pack(anchor=tk.W)
        
        self.vehicle_types = {}
        for vtype, label in [('new', 'New'), ('po', 'Pre-Owned'), ('cpo', 'Certified Pre-Owned')]:
            var = tk.BooleanVar(value=True)
            self.vehicle_types[vtype] = var
            ttk.Checkbutton(settings_frame, text=label, variable=var).pack(anchor=tk.W)
        
        # Selection info
        ttk.Label(settings_frame, text="").pack(pady=10)  # Spacer
        ttk.Label(settings_frame, text="Selected dealerships:", 
                 font=('Arial', 9, 'bold')).pack(anchor=tk.W)
        
        self.selection_text = tk.Text(settings_frame, height=8, width=25, wrap=tk.WORD)
        selection_scroll = ttk.Scrollbar(settings_frame, orient=tk.VERTICAL, 
                                       command=self.selection_text.yview)
        self.selection_text.configure(yscrollcommand=selection_scroll.set)
        
        text_frame = ttk.Frame(settings_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        
        self.selection_text.pack(in_=text_frame, side=tk.LEFT, fill=tk.BOTH, expand=True)
        selection_scroll.pack(in_=text_frame, side=tk.RIGHT, fill=tk.Y)
        
        # Action buttons
        action_frame = ttk.Frame(settings_frame)
        action_frame.pack(fill=tk.X)
        
        ttk.Button(action_frame, text="🚀 Start Scan", 
                  command=self.start_scan).pack(fill=tk.X, pady=2)
        ttk.Button(action_frame, text="⚙️ Settings", 
                  command=self.open_settings).pack(fill=tk.X, pady=2)
        ttk.Button(action_frame, text="📊 View Results", 
                  command=self.view_results).pack(fill=tk.X, pady=2)
        
        # Bind selection event
        self.dealership_listbox.bind('<<ListboxSelect>>', self.on_selection_change)
        
        # Update selection display
        self.update_selection_display()
    
    def populate_dealership_list(self):
        """Populate the dealership listbox with names"""
        self.dealership_listbox.delete(0, tk.END)
        
        # Sort dealerships by name for better organization
        sorted_dealers = sorted(self.dealerships.items(), 
                               key=lambda x: x[1]['name'])
        
        for dealer_id, info in sorted_dealers:
            display_text = f"{info['name']} ({dealer_id})"
            self.dealership_listbox.insert(tk.END, display_text)
        
        print(f"Populated listbox with {len(sorted_dealers)} dealerships")
    
    def filter_dealerships(self, *args):
        """Filter dealerships based on search"""
        search_term = self.search_var.get().lower()
        
        self.dealership_listbox.delete(0, tk.END)
        
        sorted_dealers = sorted(self.dealerships.items(), 
                               key=lambda x: x[1]['name'])
        
        for dealer_id, info in sorted_dealers:
            name = info['name'].lower()
            if search_term in name or search_term in dealer_id.lower():
                display_text = f"{info['name']} ({dealer_id})"
                self.dealership_listbox.insert(tk.END, display_text)
    
    def select_all(self):
        """Select all visible dealerships"""
        self.dealership_listbox.select_set(0, tk.END)
        self.on_selection_change()
    
    def clear_all(self):
        """Clear all selections"""
        self.dealership_listbox.selection_clear(0, tk.END)
        self.on_selection_change()
    
    def on_selection_change(self, event=None):
        """Handle selection changes"""
        selected_indices = self.dealership_listbox.curselection()
        
        self.selected_dealerships = []
        for index in selected_indices:
            item_text = self.dealership_listbox.get(index)
            # Extract dealer_id from "Name (dealer_id)" format
            dealer_id = item_text.split('(')[-1].rstrip(')')
            if dealer_id in self.dealerships:
                self.selected_dealerships.append(dealer_id)
        
        self.update_selection_display()
    
    def update_selection_display(self):
        """Update the selection display"""
        self.selection_text.delete(1.0, tk.END)
        
        if not self.selected_dealerships:
            self.selection_text.insert(tk.END, "No dealerships selected.\n\nSelect dealerships from the list to begin scanning.")
        else:
            self.selection_text.insert(tk.END, f"Selected: {len(self.selected_dealerships)} dealerships\n\n")
            
            for dealer_id in self.selected_dealerships:
                info = self.dealerships.get(dealer_id, {})
                name = info.get('name', dealer_id)
                self.selection_text.insert(tk.END, f"• {name}\n")
            
            estimated_time = len(self.selected_dealerships) * 3
            self.selection_text.insert(tk.END, f"\nEstimated time: ~{estimated_time} minutes")
    
    def start_scan(self):
        """Start the scan with selected dealerships"""
        if not self.selected_dealerships:
            messagebox.showwarning("No Selection", 
                                  "Please select at least one dealership to scan.")
            return
        
        try:
            max_vehicles = int(self.max_vehicles_var.get())
            if max_vehicles < 1 or max_vehicles > 1000:
                raise ValueError("Max vehicles must be between 1 and 1000")
        except ValueError as e:
            messagebox.showerror("Invalid Setting", str(e))
            return
        
        # Get selected vehicle types
        selected_types = [vtype for vtype, var in self.vehicle_types.items() if var.get()]
        if not selected_types:
            messagebox.showwarning("No Vehicle Types", 
                                  "Please select at least one vehicle type to scan.")
            return
        
        # Show confirmation
        dealer_names = [self.dealerships[d]['name'] for d in self.selected_dealerships]
        message = f"Start scan for {len(self.selected_dealerships)} dealerships?\n\n"
        message += "\n".join(f"• {name}" for name in dealer_names[:10])
        if len(dealer_names) > 10:
            message += f"\n... and {len(dealer_names) - 10} more"
        
        message += f"\n\nSettings:\n• Max vehicles: {max_vehicles}"
        message += f"\n• Vehicle types: {', '.join(selected_types)}"
        
        if messagebox.askyesno("Confirm Scan", message):
            self.execute_scan(max_vehicles, selected_types)
    
    def execute_scan(self, max_vehicles, vehicle_types):
        """Execute the actual scan"""
        # For now, just show what would be scanned
        scan_config = {
            'dealerships': self.selected_dealerships,
            'max_vehicles': max_vehicles,
            'vehicle_types': vehicle_types,
            'configs': {d: self.dealerships[d]['config'] for d in self.selected_dealerships}
        }
        
        # Show the configuration that would be used
        config_window = tk.Toplevel(self.root)
        config_window.title("Scan Configuration")
        config_window.geometry("600x400")
        
        text_widget = tk.Text(config_window, wrap=tk.WORD)
        scroll = ttk.Scrollbar(config_window, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scroll.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        config_text = json.dumps(scan_config, indent=2)
        text_widget.insert(tk.END, config_text)
        
        messagebox.showinfo("Scan Ready", 
                           f"Scan configuration prepared for {len(self.selected_dealerships)} dealerships.\n\n"
                           "This is a demo - actual scanning would start here.")
    
    def open_settings(self):
        """Open settings for selected dealership"""
        if not self.selected_dealerships:
            messagebox.showinfo("No Selection", 
                               "Please select a dealership first to configure its settings.")
            return
        
        # For multiple selections, use the first one
        dealer_id = self.selected_dealerships[0]
        dealer_info = self.dealerships[dealer_id]
        
        # Simple settings dialog
        settings_window = tk.Toplevel(self.root)
        settings_window.title(f"Settings - {dealer_info['name']}")
        settings_window.geometry("500x400")
        settings_window.grab_set()
        
        # Settings content
        settings_frame = ttk.Frame(settings_window, padding=20)
        settings_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(settings_frame, 
                 text=f"Settings for {dealer_info['name']}",
                 font=('Arial', 12, 'bold')).pack(pady=(0, 20))
        
        # Show current configuration
        config_text = tk.Text(settings_frame, height=15, wrap=tk.WORD)
        config_scroll = ttk.Scrollbar(settings_frame, orient=tk.VERTICAL, 
                                     command=config_text.yview)
        config_text.configure(yscrollcommand=config_scroll.set)
        
        config_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        config_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        config_content = json.dumps(dealer_info['config'], indent=2)
        config_text.insert(tk.END, config_content)
        
        # Close button
        ttk.Button(settings_frame, text="Close", 
                  command=settings_window.destroy).pack(pady=(10, 0))
    
    def view_results(self):
        """View scan results"""
        output_dir = current_dir / "output_data"
        if output_dir.exists():
            files = list(output_dir.glob("*.csv"))
            if files:
                messagebox.showinfo("Results Found", 
                                   f"Found {len(files)} result files in output_data/")
            else:
                messagebox.showinfo("No Results", 
                                   "No CSV result files found in output_data/")
        else:
            messagebox.showinfo("No Results", 
                               "Output directory not found. Run a scan first.")
    
    def run(self):
        """Run the GUI"""
        print(f"\n🚀 Starting Simple Dealership GUI with {len(self.dealerships)} dealerships")
        print("Dealership names should now be visible in the list!")
        self.root.mainloop()

def main():
    """Main function"""
    print("🚀 Launching Simple Dealership GUI...")
    
    try:
        app = SimpleDealershipGUI()
        app.run()
    except Exception as e:
        print(f"❌ Failed to start GUI: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()