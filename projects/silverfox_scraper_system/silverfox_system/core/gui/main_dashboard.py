#!/usr/bin/env python3
"""
Enhanced Main Dashboard for Silverfox Scraper System

Features:
- Initial screen with previous raw/normalized CSV outputs
- Organization by dealership name, locality, and vehicle type
- Central button to begin new scraper scan
- New scan window with dealership selection and settings
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import threading
import queue

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from batch_scraper import BatchScraper
    from normalizer import DataNormalizer
    from error_reporter import ErrorReporter
    
    # Import VERIFIED WORKING dealership configurations for GUI
    try:
        from dealerships.verified_working_dealerships import get_production_ready_dealerships
        DEALERSHIP_CONFIGS = get_production_ready_dealerships()
        print(f"✅ GUI loaded {len(DEALERSHIP_CONFIGS)} VERIFIED WORKING dealership configurations")
    except ImportError:
        # Fallback to comprehensive registry if verified not available
        from dealerships.comprehensive_registry import COMPREHENSIVE_DEALERSHIP_CONFIGS
        DEALERSHIP_CONFIGS = COMPREHENSIVE_DEALERSHIP_CONFIGS
        print(f"⚠️ GUI using comprehensive registry fallback: {len(DEALERSHIP_CONFIGS)} dealerships")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    
    # Try fallback to production scraper
    try:
        from dealerships.production_scraper import DEALERSHIP_CONFIGS
        print(f"⚠️  Using production scraper fallback: {len(DEALERSHIP_CONFIGS)} dealerships")
    except ImportError:
        # Last resort fallback
        DEALERSHIP_CONFIGS = {
            'columbiahonda': {'name': 'Columbia Honda', 'base_url': 'https://columbiahonda.com', 'brand': 'Honda', 'locality': 'Columbia'},
            'joemachenshyundai': {'name': 'Joe Machens Hyundai', 'base_url': 'https://joemachenshyundai.com', 'brand': 'Hyundai', 'locality': 'Missouri'},
            'suntrupfordkirkwood': {'name': 'Suntrup Ford Kirkwood', 'base_url': 'https://suntrupford.com', 'brand': 'Ford', 'locality': 'Kirkwood'},
            'bmwstlouis': {'name': 'BMW of St. Louis', 'base_url': 'https://bmwstlouis.com', 'brand': 'BMW', 'locality': 'St. Louis'}
        }
        print(f"⚠️  Using hardcoded fallback: {len(DEALERSHIP_CONFIGS)} dealerships")

class FileOrganizer:
    """Organize and analyze output files"""
    
    def __init__(self, output_dir: str = "output_data"):
        self.output_dir = Path(output_dir)
        
    def get_organized_files(self) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """Organize files by dealership and type"""
        organized = {
            'raw_csv': {},
            'normalized_csv': {},
            'json_metadata': {}
        }
        
        if not self.output_dir.exists():
            return organized
            
        # Scan all files in output directory
        for file_path in self.output_dir.glob("*"):
            if file_path.is_file():
                file_info = self._analyze_file(file_path)
                if file_info:
                    file_type = file_info['type']
                    dealership = file_info['dealership']
                    
                    if dealership not in organized[file_type]:
                        organized[file_type][dealership] = []
                    
                    organized[file_type][dealership].append(file_info)
        
        # Sort files by date (newest first)
        for file_type in organized:
            for dealership in organized[file_type]:
                organized[file_type][dealership].sort(
                    key=lambda x: x['timestamp'], reverse=True
                )
        
        return organized
    
    def _analyze_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Analyze a single file and extract metadata"""
        filename = file_path.name
        
        # Skip temporary and system files
        if filename.startswith('.') or filename.endswith('.tmp'):
            return None
            
        # Determine file type and dealership
        if filename.endswith('.csv'):
            if 'normalized' in filename:
                file_type = 'normalized_csv'
            else:
                file_type = 'raw_csv'
        elif filename.endswith('.json'):
            file_type = 'json_metadata'
        else:
            return None
        
        # Extract dealership name from filename
        dealership = 'unknown'
        for dealer_id in DEALERSHIP_CONFIGS.keys():
            if dealer_id in filename:
                dealership = dealer_id
                break
        
        # Check for batch files
        if 'batch' in filename:
            dealership = 'batch_combined'
        
        # Get file stats
        stat = file_path.stat()
        timestamp = datetime.fromtimestamp(stat.st_mtime)
        
        # Try to extract additional info for CSV files
        vehicle_count = 0
        vehicle_types = []
        
        if file_type in ['raw_csv', 'normalized_csv']:
            try:
                df = pd.read_csv(file_path, nrows=1000)  # Limit for performance
                vehicle_count = len(df)
                
                # Detect vehicle types
                if 'normalized_status' in df.columns:
                    status_counts = df['normalized_status'].value_counts()
                    vehicle_types = list(status_counts.index)
                elif 'condition' in df.columns:
                    vehicle_types = df['condition'].dropna().unique().tolist()
                elif 'year' in df.columns:
                    # Infer new vs used based on year
                    current_year = datetime.now().year
                    new_count = sum(df['year'] >= current_year)
                    used_count = vehicle_count - new_count
                    if new_count > 0:
                        vehicle_types.append('new')
                    if used_count > 0:
                        vehicle_types.append('po')
                        
            except Exception:
                pass  # File might be corrupted or empty
        
        return {
            'path': file_path,
            'filename': filename,
            'type': file_type,
            'dealership': dealership,
            'dealership_name': DEALERSHIP_CONFIGS.get(dealership, {}).get('name', dealership.title()),
            'size': stat.st_size,
            'timestamp': timestamp,
            'vehicle_count': vehicle_count,
            'vehicle_types': vehicle_types,
            'locality': self._get_dealership_locality(dealership)
        }
    
    def _get_dealership_locality(self, dealership_id: str) -> str:
        """Get locality/region for dealership"""
        # Simple mapping based on dealership names
        locality_map = {
            'columbia': 'Columbia',
            'stlouis': 'St. Louis',
            'kirkwood': 'Kirkwood',
            'westcounty': 'West County',
            'frontenac': 'Frontenac',
            'machens': 'Columbia',
            'suntrup': 'St. Louis Area',
            'bommarito': 'St. Louis Area'
        }
        
        for key, locality in locality_map.items():
            if key in dealership_id.lower():
                return locality
        
        return 'Unknown'

class FileExplorer(ttk.Frame):
    """File explorer widget for browsing scraper outputs"""
    
    def __init__(self, parent, file_organizer: FileOrganizer, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.file_organizer = file_organizer
        self.organized_files = {}
        
        self.setup_ui()
        self.refresh_files()
    
    def setup_ui(self):
        """Setup the file explorer UI"""
        
        # Header frame
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(header_frame, text="📁 Scraper Output Files", 
                 font=('Arial', 12, 'bold')).pack(side=tk.LEFT)
        
        # Filter controls
        filter_frame = ttk.Frame(header_frame)
        filter_frame.pack(side=tk.RIGHT)
        
        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT, padx=(10, 5))
        
        self.filter_var = tk.StringVar()
        filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_var, 
                                   values=['All', 'Raw CSV', 'Normalized CSV', 'Metadata'], 
                                   state='readonly', width=12)
        filter_combo.set('All')
        filter_combo.pack(side=tk.LEFT, padx=5)
        filter_combo.bind('<<ComboboxSelected>>', self.apply_filter)
        
        ttk.Button(filter_frame, text="🔄", command=self.refresh_files, width=3).pack(side=tk.LEFT, padx=5)
        
        # Main treeview
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create treeview with columns
        columns = ('type', 'dealership', 'locality', 'vehicles', 'v_types', 'size', 'date')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='tree headings', height=12)
        
        # Configure column headings and widths
        self.tree.heading('#0', text='Filename', anchor=tk.W)
        self.tree.heading('type', text='Type', anchor=tk.W)
        self.tree.heading('dealership', text='Dealership', anchor=tk.W)
        self.tree.heading('locality', text='Locality', anchor=tk.W)
        self.tree.heading('vehicles', text='Vehicles', anchor=tk.CENTER)
        self.tree.heading('v_types', text='Vehicle Types', anchor=tk.W)
        self.tree.heading('size', text='Size', anchor=tk.CENTER)
        self.tree.heading('date', text='Date', anchor=tk.CENTER)
        
        self.tree.column('#0', width=200)
        self.tree.column('type', width=100)
        self.tree.column('dealership', width=150)
        self.tree.column('locality', width=100)
        self.tree.column('vehicles', width=80)
        self.tree.column('v_types', width=120)
        self.tree.column('size', width=80)
        self.tree.column('date', width=120)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Context menu
        self.tree.bind('<Button-2>', self.show_context_menu)  # Right-click on Mac
        self.tree.bind('<Button-3>', self.show_context_menu)  # Right-click on PC
        self.tree.bind('<Double-1>', self.open_file)  # Double-click
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, padx=5, pady=2)
    
    def refresh_files(self):
        """Refresh the file list"""
        try:
            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Get organized files
            self.organized_files = self.file_organizer.get_organized_files()
            
            # Populate tree
            total_files = 0
            has_any_files = False
            
            for file_type, dealerships in self.organized_files.items():
                type_display = {
                    'raw_csv': 'Raw CSV',
                    'normalized_csv': 'Normalized CSV',
                    'json_metadata': 'Metadata'
                }[file_type]
                
                if dealerships:
                    has_any_files = True
                    # Create type header
                    type_node = self.tree.insert('', 'end', text=f"📊 {type_display}", 
                                                tags=('type_header',))
                    
                    for dealership, files in dealerships.items():
                        if files:
                            # Create dealership header
                            dealership_name = files[0]['dealership_name']
                            locality = files[0]['locality']
                            
                            dealer_node = self.tree.insert(type_node, 'end', 
                                                          text=f"🏢 {dealership_name} ({locality})",
                                                          tags=('dealer_header',))
                            
                            # Add files
                            for file_info in files:
                                self.add_file_node(dealer_node, file_info)
                                total_files += 1
            
            # If no files found, show helpful message
            if not has_any_files:
                no_files_node = self.tree.insert('', 'end', text="📂 No scan results found", 
                                                tags=('info_message',))
                
                self.tree.insert(no_files_node, 'end', 
                               text="ℹ️  Run a scan to see results here",
                               tags=('info_message',))
                
                self.tree.insert(no_files_node, 'end', 
                               text="🚀 Click 'START NEW SCAN' above",
                               tags=('info_message',))
            
            # Configure tags
            self.tree.tag_configure('type_header', background='lightblue', font=('Arial', 10, 'bold'))
            self.tree.tag_configure('dealer_header', background='lightgray', font=('Arial', 9, 'bold'))
            self.tree.tag_configure('file_item', background='white')
            self.tree.tag_configure('info_message', background='lightyellow', font=('Arial', 9))
            
            # Expand type headers by default
            for item in self.tree.get_children():
                self.tree.item(item, open=True)
            
            if has_any_files:
                self.status_var.set(f"Found {total_files} files")
            else:
                self.status_var.set("No scan results yet - click 'START NEW SCAN' to begin")
            
        except Exception as e:
            print(f"Error refreshing files: {e}")  # Debug output
            # Show error in tree instead of popup
            self.tree.insert('', 'end', text=f"❌ Error loading files: {str(e)}", 
                           tags=('error_message',))
            self.tree.tag_configure('error_message', background='lightcoral', font=('Arial', 9))
            self.status_var.set("Error loading files")
    
    def add_file_node(self, parent, file_info: Dict[str, Any]):
        """Add a file node to the tree"""
        try:
            filename = file_info['filename']
            file_type = file_info['type'].replace('_', ' ').title()
            dealership = file_info['dealership_name']
            locality = file_info['locality']
            vehicles = str(file_info['vehicle_count']) if file_info['vehicle_count'] > 0 else '-'
            v_types = ', '.join(file_info['vehicle_types'][:3])  # Show first 3 types
            if len(file_info['vehicle_types']) > 3:
                v_types += '...'
            
            size = self._format_file_size(file_info['size'])
            date = file_info['timestamp'].strftime('%m/%d %H:%M')
            
            # Choose icon based on file type
            icon = {
                'raw_csv': '📄',
                'normalized_csv': '📊',
                'json_metadata': '🔧'
            }.get(file_info['type'], '📄')
            
            self.tree.insert(parent, 'end', 
                           text=f"{icon} {filename}",
                           values=(file_type, dealership, locality, vehicles, v_types, size, date),
                           tags=('file_item',))
                           
        except Exception as e:
            print(f"Error adding file node: {e}")
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes/1024:.1f}KB"
        else:
            return f"{size_bytes/(1024*1024):.1f}MB"
    
    def apply_filter(self, event=None):
        """Apply filter to file list"""
        # For now, just refresh - could implement actual filtering
        self.refresh_files()
    
    def show_context_menu(self, event):
        """Show context menu for file operations"""
        item = self.tree.selection()[0] if self.tree.selection() else None
        if not item or not self.tree.item(item, 'tags')[0] == 'file_item':
            return
        
        context_menu = tk.Menu(self, tearoff=0)
        context_menu.add_command(label="📂 Open File", command=self.open_file)
        context_menu.add_command(label="📁 Show in Folder", command=self.show_in_folder)
        context_menu.add_command(label="📊 View Summary", command=self.view_file_summary)
        context_menu.add_separator()
        context_menu.add_command(label="🗑️ Delete File", command=self.delete_file)
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def open_file(self, event=None):
        """Open selected file"""
        selection = self.tree.selection()
        if not selection:
            return
        
        # Find the file path (implementation depends on how we store file info)
        # For now, just show a message
        messagebox.showinfo("Open File", "File opening functionality will be implemented")
    
    def show_in_folder(self):
        """Show file in system folder"""
        messagebox.showinfo("Show in Folder", "Show in folder functionality will be implemented")
    
    def view_file_summary(self):
        """View file summary/stats"""
        messagebox.showinfo("File Summary", "File summary functionality will be implemented")
    
    def delete_file(self):
        """Delete selected file"""
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this file?"):
            messagebox.showinfo("Delete File", "File deletion functionality will be implemented")

class DealershipScanDialog:
    """Dialog for configuring and starting new scraper scan"""
    
    def __init__(self, parent):
        self.parent = parent
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("🚀 New Scraper Scan")
        self.dialog.geometry("900x700")
        self.dialog.grab_set()
        self.dialog.resizable(True, True)
        
        # Center the dialog
        self.dialog.transient(parent)
        
        # Initialize data
        self.dealership_configs = DEALERSHIP_CONFIGS
        self.selected_dealerships = {}
        self.dealership_settings = {}
        
        self.setup_ui()
        self.load_dealerships()
    
    def setup_ui(self):
        """Setup the scan dialog UI"""
        
        # Header
        header_frame = ttk.Frame(self.dialog)
        header_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(header_frame, text="🚀 Configure New Scraper Scan", 
                 font=('Arial', 16, 'bold')).pack()
        
        ttk.Label(header_frame, text="Select dealerships and configure scan settings", 
                 font=('Arial', 10), foreground='gray').pack(pady=(5, 0))
        
        # Main content frame
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Left panel - Dealership selection
        left_frame = ttk.LabelFrame(main_frame, text="🏢 Dealership Selection", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Search box
        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="🔍 Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_dealerships)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Select all/none buttons
        select_frame = ttk.Frame(left_frame)
        select_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(select_frame, text="✅ All", command=self.select_all, width=8).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(select_frame, text="❌ None", command=self.select_none, width=8).pack(side=tk.LEFT)
        
        # Dealership list with simple, reliable scrolling
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollable frame using Frame + Scrollbar (no Canvas issues)
        container_frame = tk.Frame(list_frame)
        container_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(container_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create a Frame inside a scrollable region
        self.scroll_canvas = tk.Canvas(container_frame, 
                                      yscrollcommand=scrollbar.set,
                                      highlightthickness=0,
                                      bg='white')
        self.scroll_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.scroll_canvas.yview)
        
        # Create the actual content frame
        self.scrollable_frame = tk.Frame(self.scroll_canvas, bg='white')
        
        # Add mouse wheel support
        def _on_mousewheel(event):
            self.scroll_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _on_frame_configure(event):
            self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))
        
        # Bind events
        self.scrollable_frame.bind("<Configure>", _on_frame_configure)
        self.scroll_canvas.bind("<MouseWheel>", _on_mousewheel)
        
        # Create window for the frame
        self.scroll_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Bind mouse wheel to canvas and its children
        def bind_to_mousewheel(widget):
            widget.bind("<MouseWheel>", _on_mousewheel)
            for child in widget.winfo_children():
                bind_to_mousewheel(child)
        
        self.bind_mousewheel = bind_to_mousewheel
        
        # Right panel - Scan settings
        right_frame = ttk.LabelFrame(main_frame, text="⚙️ Scan Settings", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        
        # Global settings
        ttk.Label(right_frame, text="Global Settings", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        
        # Max vehicles per dealership
        vehicles_frame = ttk.Frame(right_frame)
        vehicles_frame.pack(fill=tk.X, pady=5)
        ttk.Label(vehicles_frame, text="Max vehicles per dealership:").pack(anchor=tk.W)
        self.max_vehicles_var = tk.StringVar(value="50")
        ttk.Entry(vehicles_frame, textvariable=self.max_vehicles_var, width=10).pack(anchor=tk.W, pady=(2, 0))
        
        # Concurrent scrapers
        concurrent_frame = ttk.Frame(right_frame)
        concurrent_frame.pack(fill=tk.X, pady=5)
        ttk.Label(concurrent_frame, text="Concurrent scrapers:").pack(anchor=tk.W)
        self.concurrent_var = tk.StringVar(value="3")
        ttk.Entry(concurrent_frame, textvariable=self.concurrent_var, width=10).pack(anchor=tk.W, pady=(2, 0))
        
        # Auto-normalize results
        self.auto_normalize_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(right_frame, text="Auto-normalize results", 
                       variable=self.auto_normalize_var).pack(anchor=tk.W, pady=10)
        
        # Save raw data
        self.save_raw_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(right_frame, text="Save raw data", 
                       variable=self.save_raw_var).pack(anchor=tk.W, pady=5)
        
        # Separator
        ttk.Separator(right_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        
        # Selected dealerships info
        ttk.Label(right_frame, text="Selection Summary", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        
        self.selection_info = tk.Text(right_frame, height=8, width=25, wrap=tk.WORD)
        self.selection_info.pack(fill=tk.BOTH, expand=True)
        self.selection_info.config(state=tk.DISABLED)
        
        # Bottom buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(button_frame, text="❌ Cancel", command=self.cancel).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="🚀 Start Scan", command=self.start_scan).pack(side=tk.RIGHT)
    
    def load_dealerships(self):
        """Load dealership list with settings controls"""
        
        print(f"🔧 Loading dealerships in dialog... Found {len(self.dealership_configs)} configs")
        
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self.dealership_widgets = {}
        
        if not self.dealership_configs:
            # Show message if no dealerships found
            no_dealers_label = ttk.Label(self.scrollable_frame, 
                                       text="❌ No dealership configurations found!\n\nPlease check that dealership files are properly configured.",
                                       font=('Arial', 10),
                                       foreground='red',
                                       justify='center')
            no_dealers_label.pack(pady=20, padx=20)
        else:
            for dealer_id, config in self.dealership_configs.items():
                print(f"   Creating widget for: {dealer_id} - {config.get('name', dealer_id)}")
                self.create_dealership_widget(dealer_id, config)
            
            # Update scroll region and bind mouse wheel events
            def update_scroll_and_events():
                # Update scroll region
                self.scroll_canvas.update_idletasks()
                self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))
                
                # Bind mouse wheel to all widgets
                self.bind_mousewheel(self.scrollable_frame)
                
                # Also bind to the dialog window itself
                self.dialog.bind("<MouseWheel>", lambda e: self.scroll_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
            
            # Delay to ensure widgets are rendered
            self.dialog.after(100, update_scroll_and_events)
        
        self.update_selection_info()
    
    def create_dealership_widget(self, dealer_id: str, config: Dict[str, Any]):
        """Create widget for a single dealership"""
        
        # Main frame for this dealership - use regular Frame instead of ttk.Frame for better visibility
        dealer_frame = tk.Frame(self.scrollable_frame, relief=tk.RAISED, bd=1, bg='#f0f0f0')
        dealer_frame.pack(fill=tk.X, pady=2, padx=5)
        
        # Checkbox and name
        header_frame = tk.Frame(dealer_frame, bg='#f0f0f0')
        header_frame.pack(fill=tk.X, padx=5, pady=3)
        
        # Checkbox for selection
        checkbox_var = tk.BooleanVar()
        checkbox = tk.Checkbutton(header_frame, variable=checkbox_var, 
                                 command=lambda: self.on_dealership_toggled(dealer_id),
                                 bg='#f0f0f0')
        checkbox.pack(side=tk.LEFT)
        
        # Dealership name and info
        name_frame = tk.Frame(header_frame, bg='#f0f0f0')
        name_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Name with brand - use tk.Label for better visibility
        name_text = config.get('name', dealer_id)
        brand = config.get('brand', '')
        if brand and brand not in name_text:
            name_text = f"{name_text} ({brand})"
        
        name_label = tk.Label(name_frame, text=name_text, 
                             font=('Arial', 10, 'bold'),
                             bg='#f0f0f0', fg='black')
        name_label.pack(anchor=tk.W)
        
        # Location info
        locality = config.get('locality', '')
        if locality:
            location_label = tk.Label(name_frame, text=f"📍 {locality}", 
                                     font=('Arial', 8),
                                     bg='#f0f0f0', fg='gray')
            location_label.pack(anchor=tk.W)
        
        # URL (if available and short enough)
        base_url = config.get('base_url', '')
        if base_url and len(base_url) < 50:
            url_label = tk.Label(name_frame, text=base_url, 
                                font=('Arial', 8),
                                bg='#f0f0f0', fg='blue')
            url_label.pack(anchor=tk.W)
        
        # Status indicators
        status_frame = ttk.Frame(name_frame)
        status_frame.pack(anchor=tk.W, pady=(2, 0))
        
        # Vehicle type selector for this dealership
        vehicle_frame = tk.Frame(dealer_frame, bg='#f0f0f0')
        vehicle_frame.pack(fill=tk.X, pady=(5, 0), padx=5)
        
        # Vehicle types label
        types_label = tk.Label(vehicle_frame, text="Vehicle Types:", 
                              font=('Arial', 8, 'bold'),
                              bg='#f0f0f0', fg='black')
        types_label.pack(anchor=tk.W)
        
        types_frame = tk.Frame(vehicle_frame, bg='#f0f0f0')
        types_frame.pack(anchor=tk.W, pady=(2, 0))
        
        # Vehicle type checkboxes
        self.dealership_settings[dealer_id] = {
            'new': tk.BooleanVar(value=True),
            'po': tk.BooleanVar(value=True), 
            'cpo': tk.BooleanVar(value=True)
        }
        
        type_configs = {
            'new': {'label': '🆕 New', 'color': '#4CAF50'},
            'po': {'label': '🚗 Pre-Owned', 'color': '#FF9800'},
            'cpo': {'label': '⭐ CPO', 'color': '#2196F3'}
        }
        
        for v_type, type_config in type_configs.items():
            cb = tk.Checkbutton(types_frame, 
                               text=type_config['label'],
                               variable=self.dealership_settings[dealer_id][v_type],
                               font=('Arial', 8),
                               fg=type_config['color'],
                               bg='#f0f0f0',
                               selectcolor='white')
            cb.pack(side=tk.LEFT, padx=(0, 10))
        
        # Status indicators  
        status_frame = tk.Frame(dealer_frame, bg='#f0f0f0')
        status_frame.pack(anchor=tk.W, pady=(5, 0), padx=5)
        
        # Anti-bot protection indicator
        if config.get('anti_bot_protection', False):
            status_label = tk.Label(status_frame, text="🛡️ Protected", 
                                   font=('Arial', 8),
                                   fg='orange', bg='#f0f0f0')
            status_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Chrome driver required
        if config.get('requires_chrome', False):
            chrome_label = tk.Label(status_frame, text="🌐 Chrome Required", 
                                   font=('Arial', 8),
                                   fg='blue', bg='#f0f0f0')
            chrome_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Settings button
        settings_btn = ttk.Button(header_frame, text="⚙️", width=3, 
                                 command=lambda: self.show_dealership_settings(dealer_id))
        settings_btn.pack(side=tk.RIGHT)
        
        # Settings panel (initially hidden)
        settings_panel = ttk.Frame(dealer_frame)
        # Will be shown/hidden by settings button
        
        # Vehicle type selection
        types_frame = ttk.LabelFrame(settings_panel, text="Vehicle Types", padding=5)
        types_frame.pack(fill=tk.X, pady=(5, 0))
        
        type_vars = {}
        for vehicle_type, label in [('new', 'New'), ('po', 'Pre-Owned'), ('cpo', 'Certified Pre-Owned')]:
            var = tk.BooleanVar(value=True)  # Default to all selected
            type_vars[vehicle_type] = var
            ttk.Checkbutton(types_frame, text=label, variable=var).pack(side=tk.LEFT, padx=5)
        
        # Store references
        self.dealership_widgets[dealer_id] = {
            'frame': dealer_frame,
            'checkbox_var': checkbox_var,
            'settings_panel': settings_panel,
            'type_vars': type_vars,
            'settings_visible': False
        }
        
        # Initialize settings
        self.dealership_settings[dealer_id] = {
            'vehicle_types': ['new', 'po', 'cpo'],
            'max_vehicles': 50
        }
    
    def show_dealership_settings(self, dealer_id: str):
        """Toggle settings panel for dealership"""
        widget_info = self.dealership_widgets[dealer_id]
        
        if widget_info['settings_visible']:
            # Hide settings
            widget_info['settings_panel'].pack_forget()
            widget_info['settings_visible'] = False
        else:
            # Show settings
            widget_info['settings_panel'].pack(fill=tk.X, pady=(5, 0))
            widget_info['settings_visible'] = True
    
    def on_dealership_toggled(self, dealer_id: str):
        """Handle dealership selection toggle"""
        widget_info = self.dealership_widgets[dealer_id]
        is_selected = widget_info['checkbox_var'].get()
        
        if is_selected:
            self.selected_dealerships[dealer_id] = True
        else:
            self.selected_dealerships.pop(dealer_id, None)
        
        self.update_selection_info()
    
    def update_selection_info(self):
        """Update the selection summary"""
        selected_count = len(self.selected_dealerships)
        
        info_text = f"Selected: {selected_count} dealerships\n\n"
        
        if selected_count > 0:
            info_text += "Selected dealerships:\n"
            for dealer_id in list(self.selected_dealerships.keys())[:10]:  # Show first 10
                config = self.dealership_configs.get(dealer_id, {})
                name = config.get('name', dealer_id)
                info_text += f"• {name}\n"
            
            if selected_count > 10:
                info_text += f"... and {selected_count - 10} more\n"
        
        self.selection_info.config(state=tk.NORMAL)
        self.selection_info.delete(1.0, tk.END)
        self.selection_info.insert(1.0, info_text)
        self.selection_info.config(state=tk.DISABLED)
    
    def filter_dealerships(self, *args):
        """Filter dealerships based on search"""
        search_term = self.search_var.get().lower()
        
        for dealer_id, widget_info in self.dealership_widgets.items():
            config = self.dealership_configs.get(dealer_id, {})
            name = config.get('name', dealer_id).lower()
            
            if search_term in name or search_term in dealer_id.lower():
                widget_info['frame'].pack(fill=tk.X, pady=2)
            else:
                widget_info['frame'].pack_forget()
    
    def select_all(self):
        """Select all visible dealerships"""
        for dealer_id, widget_info in self.dealership_widgets.items():
            if widget_info['frame'].winfo_viewable():
                widget_info['checkbox_var'].set(True)
                self.selected_dealerships[dealer_id] = True
        
        self.update_selection_info()
    
    def select_none(self):
        """Deselect all dealerships"""
        for widget_info in self.dealership_widgets.values():
            widget_info['checkbox_var'].set(False)
        
        self.selected_dealerships.clear()
        self.update_selection_info()
    
    def start_scan(self):
        """Start the scraping scan"""
        if not self.selected_dealerships:
            messagebox.showwarning("No Selection", "Please select at least one dealership to scan.")
            return
        
        try:
            # Collect settings
            max_vehicles = int(self.max_vehicles_var.get())
            concurrent = int(self.concurrent_var.get())
            
            # Validate settings
            if max_vehicles < 1 or max_vehicles > 1000:
                raise ValueError("Max vehicles must be between 1 and 1000")
            
            if concurrent < 1 or concurrent > 10:
                raise ValueError("Concurrent scrapers must be between 1 and 10")
            
            # Prepare result
            self.result = {
                'dealerships': list(self.selected_dealerships.keys()),
                'settings': {
                    'max_vehicles': max_vehicles,
                    'concurrent': concurrent,
                    'auto_normalize': self.auto_normalize_var.get(),
                    'save_raw': self.save_raw_var.get()
                },
                'dealership_settings': self.dealership_settings
            }
            
            self.dialog.destroy()
            
        except ValueError as e:
            messagebox.showerror("Invalid Settings", str(e))
    
    def cancel(self):
        """Cancel the dialog"""
        self.result = None
        self.dialog.destroy()

class MainDashboard:
    """Enhanced main dashboard for the scraper system"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🚀 Silverfox Scraper Dashboard")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Initialize components
        self.file_organizer = FileOrganizer()
        self.batch_scraper = None
        self.current_scan_thread = None
        self.scan_queue = queue.Queue()
        
        # Setup UI
        self.setup_ui()
        
        # Start message processing
        self.process_messages()
    
    def setup_ui(self):
        """Setup the main dashboard UI"""
        
        # Header with title and logo
        header_frame = ttk.Frame(self.root, relief=tk.RAISED, padding=10)
        header_frame.pack(fill=tk.X)
        
        # Title
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(side=tk.LEFT)
        
        ttk.Label(title_frame, text="🚀 Silverfox Scraper", 
                 font=('Arial', 20, 'bold')).pack(anchor=tk.W)
        ttk.Label(title_frame, text="Advanced Automotive Data Collection System", 
                 font=('Arial', 12), foreground='gray').pack(anchor=tk.W)
        
        # Status and controls
        controls_frame = ttk.Frame(header_frame)
        controls_frame.pack(side=tk.RIGHT)
        
        # Status indicator
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(controls_frame, textvariable=self.status_var, 
                                font=('Arial', 10, 'bold'), foreground='green')
        status_label.pack(anchor=tk.E, pady=(0, 5))
        
        # Quick action buttons
        action_frame = ttk.Frame(controls_frame)
        action_frame.pack(anchor=tk.E)
        
        ttk.Button(action_frame, text="🔄 Refresh", command=self.refresh_data, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="📊 Reports", command=self.show_reports, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="⚙️ Settings", command=self.show_settings, width=12).pack(side=tk.LEFT, padx=2)
        
        # Main content area
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Central scan button (prominent)
        scan_frame = ttk.Frame(main_frame)
        scan_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Large central button
        scan_button = tk.Button(scan_frame, 
                               text="🚀 START NEW SCAN",
                               font=('Arial', 16, 'bold'),
                               bg='#4CAF50',
                               fg='white',
                               height=2,
                               command=self.start_new_scan,
                               cursor='hand2')
        scan_button.pack(expand=True)
        
        # Quick scan options
        quick_frame = ttk.Frame(scan_frame)
        quick_frame.pack(pady=(10, 0))
        
        ttk.Button(quick_frame, text="⚡ Quick Scan (3 dealers)", 
                  command=self.quick_scan).pack(side=tk.LEFT, padx=5)
        ttk.Button(quick_frame, text="🔄 Repeat Last Scan", 
                  command=self.repeat_last_scan).pack(side=tk.LEFT, padx=5)
        ttk.Button(quick_frame, text="📋 Batch All Dealers", 
                  command=self.batch_all_dealers).pack(side=tk.LEFT, padx=5)
        
        # File explorer
        explorer_frame = ttk.LabelFrame(main_frame, text="📁 Previous Scan Results", padding=10)
        explorer_frame.pack(fill=tk.BOTH, expand=True)
        
        print("🔧 Creating FileExplorer...")
        try:
            self.file_explorer = FileExplorer(explorer_frame, self.file_organizer)
            self.file_explorer.pack(fill=tk.BOTH, expand=True)
            print("✅ FileExplorer created and packed successfully")
        except Exception as e:
            print(f"❌ FileExplorer creation failed: {e}")
            # Show error message in explorer frame
            error_label = ttk.Label(explorer_frame, 
                                  text=f"❌ Error loading file explorer: {str(e)}",
                                  font=('Arial', 10),
                                  foreground='red')
            error_label.pack(pady=20)
        
        # Progress bar (hidden by default)
        self.progress_frame = ttk.Frame(self.root)
        # Will be shown during scans
        
        self.progress_var = tk.StringVar(value="")
        self.progress_label = ttk.Label(self.progress_frame, textvariable=self.progress_var)
        self.progress_label.pack(pady=5)
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, padx=20, pady=5)
    
    def start_new_scan(self):
        """Open new scan configuration dialog"""
        try:
            # Use the bulletproof GUI with guaranteed visibility
            from bulletproof_gui import BulletproofDealershipGUI
            dialog = BulletproofDealershipGUI()
            result = dialog.run()
            
            if result:
                self.execute_scan(result)
        except Exception as e:
            print(f"Error opening bulletproof GUI: {e}")
            try:
                # Fallback to simple scanner
                from simple_dealership_scanner import SimpleDealershipScanner
                dialog = SimpleDealershipScanner(self.root)
                self.root.wait_window(dialog.dialog)
                
                if dialog.result:
                    self.execute_scan(dialog.result)
            except Exception as e2:
                print(f"Error opening fallback dialog: {e2}")
                # Final fallback to terminal
                print("🔧 All GUI methods failed. Please use terminal scanner:")
                print("python terminal_scanner.py")
                messagebox.showinfo("GUI Issue", 
                                   "GUI display issue detected.\n\n"
                                   "Please use the terminal scanner:\n"
                                   "python terminal_scanner.py")
    
    def execute_scan(self, scan_config: Dict[str, Any]):
        """Execute a scan with given configuration"""
        try:
            # Show progress
            self.show_progress("Initializing scan...")
            
            # Start scan in background thread
            def scan_thread():
                try:
                    batch_scraper = BatchScraper(
                        max_concurrent=scan_config['settings']['concurrent']
                    )
                    
                    self.scan_queue.put(('status', 'Starting batch scrape...'))
                    
                    results = batch_scraper.scrape_dealerships(
                        scan_config['dealerships'],
                        scan_config['settings']['max_vehicles']
                    )
                    
                    if scan_config['settings']['auto_normalize']:
                        self.scan_queue.put(('status', 'Normalizing results...'))
                        # Normalize results here
                        
                    self.scan_queue.put(('complete', results))
                    
                except Exception as e:
                    self.scan_queue.put(('error', str(e)))
            
            self.current_scan_thread = threading.Thread(target=scan_thread)
            self.current_scan_thread.daemon = True
            self.current_scan_thread.start()
            
        except Exception as e:
            self.hide_progress()
            messagebox.showerror("Scan Error", f"Failed to start scan: {str(e)}")
    
    def quick_scan(self):
        """Execute a quick scan with predefined settings"""
        quick_dealerships = ['columbiahonda', 'joemachenshyundai', 'suntrupfordkirkwood']
        scan_config = {
            'dealerships': quick_dealerships,
            'settings': {
                'max_vehicles': 10,
                'concurrent': 2,
                'auto_normalize': True,
                'save_raw': True
            }
        }
        self.execute_scan(scan_config)
    
    def repeat_last_scan(self):
        """Repeat the last scan configuration"""
        messagebox.showinfo("Repeat Scan", "Repeat last scan functionality will be implemented")
    
    def batch_all_dealers(self):
        """Run batch scan on all configured dealers"""
        if messagebox.askyesno("Confirm Batch Scan", 
                              "This will scan ALL configured dealerships. This may take 30-60 minutes. Continue?"):
            scan_config = {
                'dealerships': list(DEALERSHIP_CONFIGS.keys()),
                'settings': {
                    'max_vehicles': 50,
                    'concurrent': 3,
                    'auto_normalize': True,
                    'save_raw': True
                }
            }
            self.execute_scan(scan_config)
    
    def show_progress(self, message: str):
        """Show progress bar with message"""
        self.progress_var.set(message)
        self.progress_frame.pack(fill=tk.X, padx=10, pady=5)
        self.progress_bar.start()
        self.status_var.set("Scanning...")
    
    def hide_progress(self):
        """Hide progress bar"""
        self.progress_bar.stop()
        self.progress_frame.pack_forget()
        self.status_var.set("Ready")
    
    def process_messages(self):
        """Process messages from background threads"""
        try:
            while not self.scan_queue.empty():
                message_type, data = self.scan_queue.get_nowait()
                
                if message_type == 'status':
                    self.progress_var.set(data)
                elif message_type == 'complete':
                    self.hide_progress()
                    self.on_scan_complete(data)
                elif message_type == 'error':
                    self.hide_progress()
                    messagebox.showerror("Scan Error", f"Scan failed: {data}")
        
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.process_messages)
    
    def on_scan_complete(self, results):
        """Handle scan completion"""
        successful = sum(1 for r in results if r.get('success', False))
        total = len(results)
        vehicles = sum(r.get('vehicle_count', 0) for r in results)
        
        message = f"Scan complete!\n\nResults:\n"
        message += f"• {successful}/{total} dealerships successful\n"
        message += f"• {vehicles} total vehicles found\n"
        message += f"• Files saved to output_data/\n\n"
        message += "Refresh the file list to see new results."
        
        messagebox.showinfo("Scan Complete", message)
        
        # Refresh file list
        self.refresh_data()
    
    def refresh_data(self):
        """Refresh all data displays"""
        self.file_explorer.refresh_files()
        self.status_var.set("Data refreshed")
    
    def show_reports(self):
        """Show reporting interface"""
        messagebox.showinfo("Reports", "Reporting interface will be implemented")
    
    def show_settings(self):
        """Show settings dialog"""
        messagebox.showinfo("Settings", "Settings interface will be implemented")
    
    def run(self):
        """Run the application"""
        try:
            self.root.mainloop()
        except Exception as e:
            messagebox.showerror("Application Error", f"An error occurred: {str(e)}")

def main():
    """Main function"""
    try:
        app = MainDashboard()
        app.run()
    except Exception as e:
        print(f"Failed to start dashboard: {str(e)}")

if __name__ == "__main__":
    main()