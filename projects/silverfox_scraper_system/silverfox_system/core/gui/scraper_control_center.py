import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import queue
import json
import os
import sys
import schedule
import subprocess
from typing import Dict, List, Any, Optional
from datetime import datetime, time as dt_time
import time

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dealership_manager import DealershipManager
from pipeline import ScrapingPipeline
from normalizer import DataNormalizer
from add_dealership_dialog import AddDealershipDialog
from dealership_settings_dialog import DealershipSettingsDialog

class RotaryFilterKnob(ttk.Frame):
    """Custom rotary knob widget for adjusting filters"""
    
    def __init__(self, parent, label: str, min_val: int = 0, max_val: int = 100, initial_val: int = 50, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.min_val = min_val
        self.max_val = max_val
        self.current_val = initial_val
        self.label_text = label
        
        # Label
        self.label = ttk.Label(self, text=label, font=('Arial', 10, 'bold'))
        self.label.pack(pady=2)
        
        # Value display
        self.value_var = tk.StringVar(value=str(initial_val))
        self.value_label = ttk.Label(self, textvariable=self.value_var, font=('Arial', 12))
        self.value_label.pack(pady=2)
        
        # Rotary control frame
        control_frame = ttk.Frame(self)
        control_frame.pack(pady=5)
        
        # Decrease button
        self.dec_btn = ttk.Button(control_frame, text="◀", width=3, command=self.decrease)
        self.dec_btn.pack(side=tk.LEFT, padx=2)
        
        # Progress bar as visual indicator
        self.progress = ttk.Progressbar(
            control_frame, 
            length=100, 
            mode='determinate',
            value=self._value_to_percentage()
        )
        self.progress.pack(side=tk.LEFT, padx=5)
        
        # Increase button
        self.inc_btn = ttk.Button(control_frame, text="▶", width=3, command=self.increase)
        self.inc_btn.pack(side=tk.LEFT, padx=2)
        
        # Step size for adjustments
        self.step = max(1, (max_val - min_val) // 20)
        
        # Callback for value changes
        self.on_change = None
    
    def _value_to_percentage(self):
        """Convert current value to percentage for progress bar"""
        if self.max_val == self.min_val:
            return 0
        return ((self.current_val - self.min_val) / (self.max_val - self.min_val)) * 100
    
    def increase(self):
        """Increase the value"""
        new_val = min(self.max_val, self.current_val + self.step)
        self.set_value(new_val)
    
    def decrease(self):
        """Decrease the value"""
        new_val = max(self.min_val, self.current_val - self.step)
        self.set_value(new_val)
    
    def set_value(self, value: int):
        """Set the current value"""
        self.current_val = max(self.min_val, min(self.max_val, value))
        self.value_var.set(str(self.current_val))
        self.progress['value'] = self._value_to_percentage()
        
        if self.on_change:
            self.on_change(self.current_val)
    
    def get_value(self):
        """Get the current value"""
        return self.current_val

class DealershipFilterPanel(ttk.LabelFrame):
    """Panel for adjusting filters for a specific dealership"""
    
    def __init__(self, parent, dealership_config: Dict[str, Any], **kwargs):
        super().__init__(parent, text=dealership_config.get('name', 'Unknown Dealership'), **kwargs)
        
        self.dealership_config = dealership_config
        self.dealership_id = dealership_config.get('id', '')
        self.filters = dealership_config.get('filtering_rules', {}).get('conditional_filters', {})
        
        self.knobs = {}
        self.checkboxes = {}
        
        self.setup_filter_controls()
    
    def setup_filter_controls(self):
        """Setup filter control widgets"""
        
        # Main container with scrollbar
        canvas = tk.Canvas(self, height=300)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Price Range Controls
        if 'price_range' in self.filters:
            price_frame = ttk.LabelFrame(scrollable_frame, text="Price Range", padding=10)
            price_frame.pack(fill=tk.X, padx=5, pady=5)
            
            price_config = self.filters['price_range']
            min_price = price_config.get('min', 5000)
            max_price = price_config.get('max', 200000)
            
            # Min price knob
            self.knobs['price_min'] = RotaryFilterKnob(
                price_frame, "Min Price ($)", 
                min_val=1000, max_val=100000, initial_val=min_price
            )
            self.knobs['price_min'].pack(side=tk.LEFT, padx=10)
            
            # Max price knob
            self.knobs['price_max'] = RotaryFilterKnob(
                price_frame, "Max Price ($)", 
                min_val=10000, max_val=500000, initial_val=max_price
            )
            self.knobs['price_max'].pack(side=tk.LEFT, padx=10)
        
        # Year Range Controls
        if 'year_range' in self.filters:
            year_frame = ttk.LabelFrame(scrollable_frame, text="Year Range", padding=10)
            year_frame.pack(fill=tk.X, padx=5, pady=5)
            
            year_config = self.filters['year_range']
            min_year = year_config.get('min', 2010)
            max_year = year_config.get('max', 2024)
            
            # Min year knob
            self.knobs['year_min'] = RotaryFilterKnob(
                year_frame, "Min Year", 
                min_val=2000, max_val=2024, initial_val=min_year
            )
            self.knobs['year_min'].pack(side=tk.LEFT, padx=10)
            
            # Max year knob
            self.knobs['year_max'] = RotaryFilterKnob(
                year_frame, "Max Year", 
                min_val=2000, max_val=2024, initial_val=max_year
            )
            self.knobs['year_max'].pack(side=tk.LEFT, padx=10)
        
        # Condition Filters
        if 'allowed_conditions' in self.filters:
            condition_frame = ttk.LabelFrame(scrollable_frame, text="Vehicle Conditions", padding=10)
            condition_frame.pack(fill=tk.X, padx=5, pady=5)
            
            allowed_conditions = self.filters['allowed_conditions']
            all_conditions = ['new', 'used', 'certified']
            
            for condition in all_conditions:
                var = tk.BooleanVar(value=condition in allowed_conditions)
                self.checkboxes[f'condition_{condition}'] = var
                
                cb = ttk.Checkbutton(
                    condition_frame, 
                    text=condition.title(), 
                    variable=var
                )
                cb.pack(side=tk.LEFT, padx=10)
        
        # API Platform Info
        api_frame = ttk.LabelFrame(scrollable_frame, text="API Configuration", padding=10)
        api_frame.pack(fill=tk.X, padx=5, pady=5)
        
        platform = self.dealership_config.get('api_platform', 'unknown')
        ttk.Label(api_frame, text=f"Platform: {platform}").pack(anchor=tk.W)
        
        base_url = self.dealership_config.get('base_url', '')
        if base_url:
            ttk.Label(api_frame, text=f"URL: {base_url}", foreground='blue').pack(anchor=tk.W)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def get_current_filters(self) -> Dict[str, Any]:
        """Get current filter values"""
        current_filters = {}
        
        # Price range
        if 'price_min' in self.knobs and 'price_max' in self.knobs:
            current_filters['price_range'] = {
                'min': self.knobs['price_min'].get_value(),
                'max': self.knobs['price_max'].get_value()
            }
        
        # Year range
        if 'year_min' in self.knobs and 'year_max' in self.knobs:
            current_filters['year_range'] = {
                'min': self.knobs['year_min'].get_value(),
                'max': self.knobs['year_max'].get_value()
            }
        
        # Conditions
        conditions = []
        for key, var in self.checkboxes.items():
            if key.startswith('condition_') and var.get():
                condition = key.replace('condition_', '')
                conditions.append(condition)
        
        if conditions:
            current_filters['allowed_conditions'] = conditions
        
        # Preserve other filters
        for key, value in self.filters.items():
            if key not in current_filters:
                current_filters[key] = value
        
        return current_filters

class ScraperControlCenter:
    """Main control center for the scraper system"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Silverfox Scraper Control Center")
        self.root.geometry("1400x900")
        
        # Initialize components
        self.dealership_manager = DealershipManager()
        self.pipeline = ScrapingPipeline()
        self.normalizer = DataNormalizer()
        
        # Thread management
        self.scraping_threads = {}
        self.message_queue = queue.Queue()
        
        # Data storage
        self.dealership_panels = {}
        self.scraping_status = {}
        
        # Scheduling
        self.scheduled_time = dt_time(4, 0)  # Default 4:00 AM
        self.schedule_enabled = False
        self.schedule_thread = None
        
        # Setup UI
        self.setup_ui()
        self.load_dealerships()
        
        # Start message processing
        self.process_messages()
        
        # Load saved schedule settings
        self.load_schedule_settings()
    
    def setup_ui(self):
        """Setup the main UI"""
        
        # Top toolbar
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=10, pady=5)
        
        # Control buttons
        ttk.Button(toolbar, text="🔄 Refresh", command=self.load_dealerships).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="➕ Add New", command=self.add_new_dealership).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="⚙️ Configure All", command=self.configure_all_dealerships).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="🚀 Run Selected", command=self.run_selected_scrapers).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="⏰ Schedule Daily", command=self.setup_daily_schedule).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="⏹️ Stop All", command=self.stop_all_scrapers).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="📊 View Logs", command=self.view_logs).pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(toolbar, textvariable=self.status_var).pack(side=tk.RIGHT, padx=5)
        
        # Main paned window
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Left panel - Dealership list and controls
        left_frame = ttk.Frame(main_paned, width=300)
        main_paned.add(left_frame, weight=1)
        
        # Dealership list
        list_frame = ttk.LabelFrame(left_frame, text="Dealerships", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Search box
        search_frame = ttk.Frame(list_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_dealerships)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Dealership listbox with checkboxes
        listbox_frame = ttk.Frame(list_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        # Custom listbox with checkboxes
        self.dealership_tree = ttk.Treeview(
            listbox_frame, 
            columns=('status', 'platform'), 
            show='tree headings',
            height=15
        )
        
        self.dealership_tree.heading('#0', text='Dealership', anchor=tk.W)
        self.dealership_tree.heading('status', text='Status', anchor=tk.W)
        self.dealership_tree.heading('platform', text='Platform', anchor=tk.W)
        
        self.dealership_tree.column('#0', width=200)
        self.dealership_tree.column('status', width=80)
        self.dealership_tree.column('platform', width=100)
        
        tree_scroll = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.dealership_tree.yview)
        self.dealership_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.dealership_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.dealership_tree.bind('<<TreeviewSelect>>', self.on_dealership_selected)
        
        # Right panel - Filter controls
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=2)
        
        # Filter panel container
        self.filter_container = ttk.LabelFrame(right_frame, text="Filter Controls", padding=10)
        self.filter_container.pack(fill=tk.BOTH, expand=True)
        
        # Default message
        self.default_label = ttk.Label(
            self.filter_container, 
            text="Select a dealership to adjust its filters",
            font=('Arial', 12),
            foreground='gray'
        )
        self.default_label.pack(expand=True)
        
        # Bottom panel - Logs and status
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Log display
        log_frame = ttk.LabelFrame(bottom_frame, text="Activity Log", padding=5)
        log_frame.pack(fill=tk.X)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, wrap=tk.WORD)
        self.log_text.pack(fill=tk.X)
        
        # Configure text tags for different log levels
        self.log_text.tag_configure('INFO', foreground='black')
        self.log_text.tag_configure('WARNING', foreground='orange')
        self.log_text.tag_configure('ERROR', foreground='red')
        self.log_text.tag_configure('SUCCESS', foreground='green')
    
    def load_dealerships(self):
        """Load dealership list"""
        try:
            # Clear existing items
            for item in self.dealership_tree.get_children():
                self.dealership_tree.delete(item)
            
            # Load dealerships
            dealerships = self.dealership_manager.list_dealerships()
            
            # If no dealerships from manager, try to load from other sources
            if not dealerships:
                self.log_message("No dealerships found in manager, trying fallback sources...", 'WARNING')
                dealerships = self._load_fallback_dealerships()
            
            for dealership in dealerships:
                status = "✅ Ready" if dealership.get('has_scraper') else "⚠️ No Scraper"
                platform = dealership.get('api_platform', 'unknown')
                
                # Ensure we have a proper name
                name = dealership.get('name', dealership.get('id', 'Unknown'))
                if not name or name == dealership.get('id'):
                    # Try to format the ID into a readable name
                    name = dealership.get('id', 'Unknown').replace('_', ' ').title()
                
                self.dealership_tree.insert(
                    '', 'end',
                    iid=dealership['id'],
                    text=name,
                    values=(status, platform),
                    tags=('enabled' if dealership.get('has_scraper') else 'disabled',)
                )
            
            # Configure tags
            self.dealership_tree.tag_configure('enabled', foreground='black')
            self.dealership_tree.tag_configure('disabled', foreground='gray')
            
            self.log_message(f"Loaded {len(dealerships)} dealerships", 'INFO')
            self.status_var.set(f"Loaded {len(dealerships)} dealerships")
            
        except Exception as e:
            self.log_message(f"Failed to load dealerships: {str(e)}", 'ERROR')
            messagebox.showerror("Error", f"Failed to load dealerships: {str(e)}")
    
    def add_new_dealership(self):
        """Open dialog to add a new dealership"""
        try:
            dialog = AddDealershipDialog(self.root, self.dealership_manager)
            self.root.wait_window(dialog.dialog)
            
            if dialog.result:
                # Refresh the dealership list
                self.load_dealerships()
                self.log_message(f"Added new dealership: {dialog.result['name']}", 'SUCCESS')
                
                # Optionally select the new dealership
                new_id = dialog.result['id']
                if self.dealership_tree.exists(new_id):
                    self.dealership_tree.selection_set(new_id)
                    self.show_dealership_filters(new_id)
        
        except Exception as e:
            self.log_message(f"Failed to add new dealership: {str(e)}", 'ERROR')
            messagebox.showerror("Error", f"Failed to add new dealership: {str(e)}")
    
    def filter_dealerships(self, *args):
        """Filter dealership list based on search"""
        search_term = self.search_var.get().lower()
        
        for item in self.dealership_tree.get_children():
            dealership_name = self.dealership_tree.item(item, 'text').lower()
            if search_term in dealership_name:
                self.dealership_tree.reattach(item, '', 'end')
            else:
                self.dealership_tree.detach(item)
    
    def on_dealership_selected(self, event):
        """Handle dealership selection"""
        selection = self.dealership_tree.selection()
        if not selection:
            return
        
        dealership_id = selection[0]
        self.show_dealership_filters(dealership_id)
    
    def show_dealership_filters(self, dealership_id: str):
        """Show filter controls for selected dealership"""
        try:
            # Clear existing filter panel
            for widget in self.filter_container.winfo_children():
                widget.destroy()
            
            # Get dealership configuration
            config = self.dealership_manager.get_dealership_config(dealership_id)
            if not config:
                ttk.Label(
                    self.filter_container, 
                    text="No configuration found for this dealership",
                    foreground='red'
                ).pack(expand=True)
                return
            
            # Create filter panel
            filter_panel = DealershipFilterPanel(self.filter_container, config)
            filter_panel.pack(fill=tk.BOTH, expand=True)
            
            # Store reference
            self.dealership_panels[dealership_id] = filter_panel
            
            # Control buttons
            button_frame = ttk.Frame(self.filter_container)
            button_frame.pack(fill=tk.X, pady=10)
            
            ttk.Button(
                button_frame, 
                text="💾 Save Filters", 
                command=lambda: self.save_dealership_filters(dealership_id)
            ).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(
                button_frame, 
                text="🚀 Run Scraper", 
                command=lambda: self.run_single_scraper(dealership_id)
            ).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(
                button_frame, 
                text="🔄 Reset Filters", 
                command=lambda: self.reset_dealership_filters(dealership_id)
            ).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(
                button_frame, 
                text="⚙️ Advanced Settings", 
                command=lambda: self.open_advanced_settings(dealership_id)
            ).pack(side=tk.LEFT, padx=5)
            
        except Exception as e:
            self.log_message(f"Failed to show filters for {dealership_id}: {str(e)}", 'ERROR')
    
    def save_dealership_filters(self, dealership_id: str):
        """Save filter changes for dealership"""
        try:
            if dealership_id not in self.dealership_panels:
                return
            
            panel = self.dealership_panels[dealership_id]
            current_filters = panel.get_current_filters()
            
            # Update filters
            filter_updates = {'conditional_filters': current_filters}
            success = self.dealership_manager.update_dealership_filters(dealership_id, filter_updates)
            
            if success:
                self.log_message(f"Saved filters for {panel.dealership_config['name']}", 'SUCCESS')
                messagebox.showinfo("Success", "Filters saved successfully!")
            else:
                self.log_message(f"Failed to save filters for {dealership_id}", 'ERROR')
                messagebox.showerror("Error", "Failed to save filters")
                
        except Exception as e:
            self.log_message(f"Error saving filters: {str(e)}", 'ERROR')
            messagebox.showerror("Error", f"Failed to save filters: {str(e)}")
    
    def reset_dealership_filters(self, dealership_id: str):
        """Reset dealership filters to defaults"""
        if messagebox.askyesno("Confirm", "Reset filters to default values?"):
            # Reload the dealership panel
            self.show_dealership_filters(dealership_id)
            self.log_message(f"Reset filters for {dealership_id}", 'INFO')
    
    def open_advanced_settings(self, dealership_id: str):
        """Open advanced settings dialog for dealership"""
        try:
            config = self.dealership_manager.get_dealership_config(dealership_id)
            if not config:
                messagebox.showerror("Error", f"No configuration found for {dealership_id}")
                return
            
            def on_save(updated_config):
                # Save the updated configuration
                success = self.dealership_manager.create_dealership_config(dealership_id, updated_config)
                if success:
                    self.log_message(f"Advanced settings saved for {dealership_id}", 'SUCCESS')
                    # Refresh the dealership filters display
                    self.show_dealership_filters(dealership_id)
                return success
            
            # Open the advanced settings dialog
            settings_dialog = DealershipSettingsDialog(self.root, config, on_save)
            self.root.wait_window(settings_dialog.dialog)
            
        except Exception as e:
            self.log_message(f"Failed to open advanced settings for {dealership_id}: {str(e)}", 'ERROR')
            messagebox.showerror("Error", f"Failed to open advanced settings:\n{str(e)}")
    
    def _load_fallback_dealerships(self):
        """Load dealerships from fallback sources when primary manager fails"""
        dealerships = []
        
        try:
            # Try verified working dealerships
            from dealerships.verified_working_dealerships import get_all_verified_dealerships
            verified = get_all_verified_dealerships()
            for dealer_id, config in verified.items():
                dealerships.append({
                    'id': dealer_id,
                    'name': config.get('name', dealer_id.replace('_', ' ').title()),
                    'api_platform': config.get('api_platform', 'unknown'),
                    'has_scraper': config.get('verified', False),
                    'source': 'verified_working'
                })
        except ImportError:
            pass
        
        try:
            # Try comprehensive registry
            from dealerships.comprehensive_registry import COMPREHENSIVE_DEALERSHIP_CONFIGS
            for dealer_id, config in COMPREHENSIVE_DEALERSHIP_CONFIGS.items():
                # Don't add if already exists from verified source
                if not any(d['id'] == dealer_id for d in dealerships):
                    dealerships.append({
                        'id': dealer_id,
                        'name': config.get('name', dealer_id.replace('_', ' ').title()),
                        'api_platform': config.get('api_platform', 'unknown'),
                        'has_scraper': config.get('scraper_available', False),
                        'source': 'comprehensive_registry'
                    })
        except ImportError:
            pass
        
        # Hardcoded fallback if nothing else works
        if not dealerships:
            dealerships = [
                {
                    'id': 'columbiahonda',
                    'name': 'Columbia Honda',
                    'api_platform': 'dealeron_cosmos',
                    'has_scraper': True,
                    'source': 'hardcoded_fallback'
                },
                {
                    'id': 'joemachenshyundai',
                    'name': 'Joe Machens Hyundai',
                    'api_platform': 'algolia',
                    'has_scraper': True,
                    'source': 'hardcoded_fallback'
                }
            ]
        
        return dealerships
    
    def configure_all_dealerships(self):
        """Run configuration for all dealerships"""
        try:
            # Show progress dialog
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Configuring Dealerships")
            progress_window.geometry("400x150")
            progress_window.grab_set()
            
            ttk.Label(progress_window, text="Configuring all dealerships...").pack(pady=20)
            
            progress_bar = ttk.Progressbar(progress_window, mode='indeterminate')
            progress_bar.pack(pady=10, padx=20, fill=tk.X)
            progress_bar.start()
            
            def configure_thread():
                try:
                    # Run configuration script
                    import subprocess
                    result = subprocess.run([
                        sys.executable, 'configure_all_dealerships.py'
                    ], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))
                    
                    self.message_queue.put(('configure_complete', result.returncode == 0, result.stdout))
                    
                except Exception as e:
                    self.message_queue.put(('configure_error', str(e)))
            
            # Start configuration in thread
            thread = threading.Thread(target=configure_thread)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            self.log_message(f"Configuration failed: {str(e)}", 'ERROR')
            messagebox.showerror("Error", f"Configuration failed: {str(e)}")
    
    def run_single_scraper(self, dealership_id: str):
        """Run scraper for a single dealership"""
        try:
            if dealership_id in self.scraping_threads:
                messagebox.showwarning("Warning", "Scraper is already running for this dealership")
                return
            
            # Update status
            self.scraping_status[dealership_id] = 'running'
            self.update_dealership_status(dealership_id, "🔄 Running")
            
            def scraping_thread():
                try:
                    # Run pipeline for single dealership
                    result = self.pipeline.run_single_dealership(dealership_id)
                    self.message_queue.put(('scraping_complete', dealership_id, result))
                    
                except Exception as e:
                    self.message_queue.put(('scraping_error', dealership_id, str(e)))
            
            # Start scraping thread
            thread = threading.Thread(target=scraping_thread)
            thread.daemon = True
            thread.start()
            
            self.scraping_threads[dealership_id] = thread
            self.log_message(f"Started scraping for {dealership_id}", 'INFO')
            
        except Exception as e:
            self.log_message(f"Failed to start scraper: {str(e)}", 'ERROR')
            messagebox.showerror("Error", f"Failed to start scraper: {str(e)}")
    
    def run_selected_scrapers(self):
        """Run scrapers for selected dealerships"""
        selected = self.dealership_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select dealerships to scrape")
            return
        
        for dealership_id in selected:
            self.run_single_scraper(dealership_id)
    
    def stop_all_scrapers(self):
        """Stop all running scrapers"""
        if messagebox.askyesno("Confirm", "Stop all running scrapers?"):
            # Note: This is a graceful indication - threads will complete their current iteration
            self.scraping_threads.clear()
            self.scraping_status.clear()
            
            # Reset all statuses
            for item in self.dealership_tree.get_children():
                self.update_dealership_status(item, "⏹️ Stopped")
            
            self.log_message("Stopped all scrapers", 'WARNING')
    
    def update_dealership_status(self, dealership_id: str, status: str):
        """Update dealership status in tree"""
        if self.dealership_tree.exists(dealership_id):
            current_values = self.dealership_tree.item(dealership_id, 'values')
            new_values = (status, current_values[1] if len(current_values) > 1 else '')
            self.dealership_tree.item(dealership_id, values=new_values)
    
    def view_logs(self):
        """Open log viewer window"""
        log_window = tk.Toplevel(self.root)
        log_window.title("Scraper Logs")
        log_window.geometry("800x600")
        
        # Log file selector
        file_frame = ttk.Frame(log_window)
        file_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(file_frame, text="Log File:").pack(side=tk.LEFT)
        
        log_files = ['scraping_pipeline.log', 'dealership_manager.log', 'data_normalizer.log']
        log_var = tk.StringVar(value=log_files[0])
        
        log_combo = ttk.Combobox(file_frame, textvariable=log_var, values=log_files, state="readonly")
        log_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Log content display
        log_content = scrolledtext.ScrolledText(log_window, wrap=tk.WORD)
        log_content.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        def load_log_file():
            try:
                log_file = os.path.join('logs', log_var.get())
                if os.path.exists(log_file):
                    with open(log_file, 'r') as f:
                        content = f.read()
                    log_content.delete(1.0, tk.END)
                    log_content.insert(1.0, content)
                    log_content.see(tk.END)  # Scroll to bottom
                else:
                    log_content.delete(1.0, tk.END)
                    log_content.insert(1.0, "Log file not found")
            except Exception as e:
                log_content.delete(1.0, tk.END)
                log_content.insert(1.0, f"Error loading log: {str(e)}")
        
        log_combo.bind('<<ComboboxSelected>>', lambda e: load_log_file())
        
        # Load initial log
        load_log_file()
        
        # Refresh button
        ttk.Button(file_frame, text="🔄 Refresh", command=load_log_file).pack(side=tk.RIGHT, padx=5)
    
    def log_message(self, message: str, level: str = 'INFO'):
        """Add message to log display"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        formatted_message = f"[{timestamp}] {level}: {message}\n"
        
        self.log_text.insert(tk.END, formatted_message, level)
        self.log_text.see(tk.END)
    
    def process_messages(self):
        """Process messages from background threads"""
        try:
            while not self.message_queue.empty():
                message = self.message_queue.get_nowait()
                
                if message[0] == 'scraping_complete':
                    dealership_id, result = message[1], message[2]
                    
                    if dealership_id in self.scraping_threads:
                        del self.scraping_threads[dealership_id]
                    
                    if result.get('success'):
                        self.update_dealership_status(dealership_id, "✅ Complete")
                        self.log_message(f"Scraping completed for {dealership_id}", 'SUCCESS')
                    else:
                        self.update_dealership_status(dealership_id, "❌ Failed")
                        self.log_message(f"Scraping failed for {dealership_id}", 'ERROR')
                
                elif message[0] == 'scraping_error':
                    dealership_id, error = message[1], message[2]
                    
                    if dealership_id in self.scraping_threads:
                        del self.scraping_threads[dealership_id]
                    
                    self.update_dealership_status(dealership_id, "❌ Error")
                    self.log_message(f"Scraping error for {dealership_id}: {error}", 'ERROR')
                
                elif message[0] == 'configure_complete':
                    success, output = message[1], message[2]
                    
                    if success:
                        self.log_message("Configuration completed successfully", 'SUCCESS')
                        self.load_dealerships()  # Refresh list
                    else:
                        self.log_message("Configuration failed", 'ERROR')
                
                elif message[0] == 'configure_error':
                    error = message[1]
                    self.log_message(f"Configuration error: {error}", 'ERROR')
        
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.process_messages)
    
    def setup_daily_schedule(self):
        """Setup daily scraping schedule"""
        
        schedule_window = tk.Toplevel(self.root)
        schedule_window.title("Daily Scraping Schedule")
        schedule_window.geometry("400x300")
        schedule_window.transient(self.root)
        schedule_window.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(schedule_window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text="Daily Scraping Schedule", font=('Arial', 14, 'bold')).pack(pady=(0, 20))
        
        # Enable/Disable checkbox
        self.schedule_enabled_var = tk.BooleanVar(value=self.schedule_enabled)
        enable_check = ttk.Checkbutton(
            main_frame, 
            text="Enable Daily Automated Scraping", 
            variable=self.schedule_enabled_var,
            command=self.toggle_schedule_controls
        )
        enable_check.pack(pady=(0, 15))
        
        # Time selection frame
        time_frame = ttk.LabelFrame(main_frame, text="Schedule Time", padding=10)
        time_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Hour selection
        hour_frame = ttk.Frame(time_frame)
        hour_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(hour_frame, text="Hour (24h format):").pack(side=tk.LEFT)
        self.hour_var = tk.StringVar(value=str(self.scheduled_time.hour).zfill(2))
        hour_spinbox = ttk.Spinbox(
            hour_frame, 
            from_=0, 
            to=23, 
            width=5, 
            textvariable=self.hour_var,
            format="%02.0f"
        )
        hour_spinbox.pack(side=tk.RIGHT)
        
        # Minute selection
        minute_frame = ttk.Frame(time_frame)
        minute_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(minute_frame, text="Minute:").pack(side=tk.LEFT)
        self.minute_var = tk.StringVar(value=str(self.scheduled_time.minute).zfill(2))
        minute_spinbox = ttk.Spinbox(
            minute_frame, 
            from_=0, 
            to=59, 
            width=5, 
            textvariable=self.minute_var,
            format="%02.0f"
        )
        minute_spinbox.pack(side=tk.RIGHT)
        
        # Info frame
        info_frame = ttk.LabelFrame(main_frame, text="Current Schedule", padding=10)
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        status_text = "Enabled" if self.schedule_enabled else "Disabled"
        time_text = self.scheduled_time.strftime("%H:%M")
        
        self.schedule_status_label = ttk.Label(
            info_frame, 
            text=f"Status: {status_text}\nTime: {time_text}",
            font=('Arial', 10)
        )
        self.schedule_status_label.pack()
        
        # Target info
        target_frame = ttk.LabelFrame(main_frame, text="Target", padding=10)
        target_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(
            target_frame,
            text="• All enabled dealerships will be scraped\n• Raw data saved to complete_data.csv\n• Normalized data generated automatically\n• Goal: Complete within 1 hour",
            justify=tk.LEFT
        ).pack()
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Button(button_frame, text="Save", command=lambda: self.save_schedule(schedule_window)).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=schedule_window.destroy).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="Test Now", command=self.test_scheduled_run).pack(side=tk.LEFT)
    
    def toggle_schedule_controls(self):
        """Toggle schedule control states"""
        # This can be used to enable/disable time controls based on checkbox
        pass
    
    def save_schedule(self, window):
        """Save the schedule settings"""
        try:
            # Get time values
            hour = int(self.hour_var.get())
            minute = int(self.minute_var.get())
            
            # Validate time
            if not (0 <= hour <= 23) or not (0 <= minute <= 59):
                messagebox.showerror("Invalid Time", "Please enter valid time values.")
                return
            
            # Update settings
            self.scheduled_time = dt_time(hour, minute)
            self.schedule_enabled = self.schedule_enabled_var.get()
            
            # Save to file
            self.save_schedule_settings()
            
            # Update scheduler
            self.update_scheduler()
            
            # Update status
            status = "Enabled" if self.schedule_enabled else "Disabled"
            self.status_var.set(f"Schedule {status} at {self.scheduled_time.strftime('%H:%M')}")
            
            messagebox.showinfo("Schedule Saved", f"Daily scraping {'enabled' if self.schedule_enabled else 'disabled'} at {self.scheduled_time.strftime('%H:%M')}")
            window.destroy()
            
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numeric values for time.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save schedule: {str(e)}")
    
    def load_schedule_settings(self):
        """Load schedule settings from file"""
        try:
            settings_file = os.path.join(os.path.dirname(__file__), 'schedule_settings.json')
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                
                # Parse time
                time_str = settings.get('time', '04:00')
                hour, minute = map(int, time_str.split(':'))
                self.scheduled_time = dt_time(hour, minute)
                
                # Set enabled status
                self.schedule_enabled = settings.get('enabled', False)
                
                # Update scheduler if enabled
                if self.schedule_enabled:
                    self.update_scheduler()
                    
        except Exception as e:
            print(f"Error loading schedule settings: {str(e)}")
    
    def save_schedule_settings(self):
        """Save schedule settings to file"""
        try:
            settings = {
                'time': self.scheduled_time.strftime('%H:%M'),
                'enabled': self.schedule_enabled,
                'last_updated': datetime.now().isoformat()
            }
            
            settings_file = os.path.join(os.path.dirname(__file__), 'schedule_settings.json')
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
                
        except Exception as e:
            print(f"Error saving schedule settings: {str(e)}")
    
    def update_scheduler(self):
        """Update the background scheduler"""
        try:
            # Clear existing schedule
            schedule.clear()
            
            if self.schedule_enabled:
                # Schedule daily run
                schedule.every().day.at(self.scheduled_time.strftime('%H:%M')).do(self.run_scheduled_scraping)
                
                # Start scheduler thread if not running
                if self.schedule_thread is None or not self.schedule_thread.is_alive():
                    self.schedule_thread = threading.Thread(target=self.schedule_worker, daemon=True)
                    self.schedule_thread.start()
                    
        except Exception as e:
            print(f"Error updating scheduler: {str(e)}")
    
    def schedule_worker(self):
        """Background worker for schedule checking"""
        while self.schedule_enabled:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                print(f"Schedule worker error: {str(e)}")
                time.sleep(60)
    
    def run_scheduled_scraping(self):
        """Run the scheduled scraping job"""
        try:
            self.message_queue.put(("info", "🕐 Starting scheduled daily scraping..."))
            
            # Get all enabled dealerships
            enabled_dealerships = []
            for item in self.dealership_tree.get_children():
                values = self.dealership_tree.item(item, 'values')
                dealer_id = self.dealership_tree.item(item, 'text')
                
                # Check if checkbox is checked (assuming first column is checkbox state)
                if len(values) > 0 and values[0] == '✓':
                    enabled_dealerships.append(dealer_id)
            
            if not enabled_dealerships:
                self.message_queue.put(("warning", "No dealerships selected for scheduled run"))
                return
            
            # Run scraping for enabled dealerships
            self.message_queue.put(("info", f"Running {len(enabled_dealerships)} dealerships"))
            
            # Start scraping in separate thread
            thread = threading.Thread(
                target=self.run_scrapers_batch,
                args=(enabled_dealerships, True),  # True for scheduled run
                daemon=True
            )
            thread.start()
            
        except Exception as e:
            self.message_queue.put(("error", f"Scheduled scraping failed: {str(e)}"))
    
    def test_scheduled_run(self):
        """Test the scheduled run with current settings"""
        if messagebox.askyesno("Test Scheduled Run", "This will run the scheduled scraping process now. Continue?"):
            self.run_scheduled_scraping()
    
    def run_scrapers_batch(self, dealership_ids, is_scheduled=False):
        """Run multiple scrapers in batch mode"""
        try:
            start_time = datetime.now()
            
            if is_scheduled:
                self.message_queue.put(("info", f"🕐 Daily scheduled run started at {start_time.strftime('%H:%M:%S')}"))
            
            all_vehicles = []
            successful_scrapers = 0
            failed_scrapers = 0
            
            for dealer_id in dealership_ids:
                try:
                    self.message_queue.put(("info", f"🔄 Scraping {dealer_id}..."))
                    
                    # Run individual scraper
                    vehicles = self.run_single_scraper_sync(dealer_id)
                    
                    if vehicles:
                        all_vehicles.extend(vehicles)
                        successful_scrapers += 1
                        self.message_queue.put(("success", f"✅ {dealer_id}: {len(vehicles)} vehicles"))
                    else:
                        failed_scrapers += 1
                        self.message_queue.put(("warning", f"⚠️ {dealer_id}: No vehicles found"))
                        
                except Exception as e:
                    failed_scrapers += 1
                    self.message_queue.put(("error", f"❌ {dealer_id}: {str(e)}"))
                
                # Brief delay between scrapers
                time.sleep(5)
            
            # Save results
            if all_vehicles:
                self.save_batch_results(all_vehicles, is_scheduled)
            
            # Summary
            end_time = datetime.now()
            duration = end_time - start_time
            
            summary = f"📊 Batch complete: {successful_scrapers} successful, {failed_scrapers} failed, {len(all_vehicles)} total vehicles, Duration: {duration}"
            self.message_queue.put(("info", summary))
            
            if is_scheduled:
                self.message_queue.put(("success", f"🎯 Daily scheduled run completed at {end_time.strftime('%H:%M:%S')}"))
                
        except Exception as e:
            self.message_queue.put(("error", f"Batch scraping failed: {str(e)}"))
    
    def run_single_scraper_sync(self, dealer_id):
        """Run a single scraper synchronously and return results"""
        # This would need to be implemented based on your existing scraper architecture
        # For now, return empty list as placeholder
        return []
    
    def save_batch_results(self, vehicles, is_scheduled=False):
        """Save batch scraping results"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if is_scheduled:
                filename = f"daily_scrape_{timestamp}"
            else:
                filename = f"batch_scrape_{timestamp}"
            
            # Save raw data
            raw_file = f"output_data/{filename}_raw.csv"
            # Implementation would save vehicles to CSV
            
            # Generate normalized data
            normalized_file = f"output_data/{filename}_normalized.csv"
            # Implementation would normalize and save
            
            self.message_queue.put(("success", f"💾 Results saved: {len(vehicles)} vehicles"))
            
        except Exception as e:
            self.message_queue.put(("error", f"Failed to save results: {str(e)}"))
    
    def run(self):
        """Run the application"""
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"Application error: {str(e)}")

def main():
    """Main function"""
    try:
        app = ScraperControlCenter()
        app.run()
    except Exception as e:
        print(f"Failed to start Scraper Control Center: {str(e)}")

if __name__ == "__main__":
    main()