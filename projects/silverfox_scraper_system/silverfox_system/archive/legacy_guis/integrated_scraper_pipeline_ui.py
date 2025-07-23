#!/usr/bin/env python3
"""
Integrated Scraper Pipeline UI - Complete Integration
Combines existing scraper GUI with Universal Pipeline UI
Includes human verification checkpoints and step-by-step pipeline progression
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import queue
import json
import os
import sys
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import pandas as pd
import time
import subprocess

# Add scraper directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scraper'))

try:
    # Import scraper components
    from batch_scraper import BatchScraper
    from normalizer import VehicleDataNormalizer
    from order_processor import OrderProcessor, OrderConfig
    from qr_processor import QRProcessor
    from apps_script_functions import AppsScriptProcessor, create_apps_script_processor
    from google_sheets_filters import GoogleSheetsFilters
    
    # Import verified dealerships
    from dealerships.verified_working_dealerships import get_production_ready_dealerships
    DEALERSHIP_CONFIGS = get_production_ready_dealerships()
    
except ImportError as e:
    print(f"⚠️ Import warning: {e}")
    DEALERSHIP_CONFIGS = {}

class HumanVerificationDialog:
    """Modal dialog for human verification checkpoints"""
    
    def __init__(self, parent, stage_name: str, data_preview: Dict[str, Any], verification_type: str = "data"):
        self.parent = parent
        self.stage_name = stage_name
        self.data_preview = data_preview
        self.verification_type = verification_type
        self.result = None
        self.approved = False
        self.feedback = ""
        
        # Create modal dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Human Verification - {stage_name}")
        self.dialog.geometry("800x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.center_dialog()
        
        self.create_verification_interface()
        
    def center_dialog(self):
        """Center dialog on parent window"""
        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - 400
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - 300
        self.dialog.geometry(f"800x600+{x}+{y}")
    
    def create_verification_interface(self):
        """Create the verification interface"""
        main_frame = tk.Frame(self.dialog, bg='#ffffff', padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # Header
        header_frame = tk.Frame(main_frame, bg='#ffffff')
        header_frame.pack(fill='x', pady=(0, 20))
        
        # Icon and title
        title_frame = tk.Frame(header_frame, bg='#ffffff')
        title_frame.pack(fill='x')
        
        icon_label = tk.Label(title_frame, text="🔍", font=('Arial', 24), bg='#ffffff')
        icon_label.pack(side='left', padx=(0, 15))
        
        title_label = tk.Label(title_frame, text=f"Verification Required: {self.stage_name}", 
                              font=('Arial', 16, 'bold'), bg='#ffffff', fg='#2c3e50')
        title_label.pack(side='left')
        
        # Description
        desc_text = self.get_verification_description()
        desc_label = tk.Label(header_frame, text=desc_text, font=('Arial', 11), 
                             bg='#ffffff', fg='#7f8c8d', wraplength=750, justify='left')
        desc_label.pack(fill='x', pady=(10, 0))
        
        # Data preview section
        preview_frame = tk.LabelFrame(main_frame, text="Data Preview", font=('Arial', 12, 'bold'),
                                     bg='#ffffff', fg='#34495e', padx=15, pady=10)
        preview_frame.pack(fill='both', expand=True, pady=(0, 20))
        
        # Create data preview
        self.create_data_preview(preview_frame)
        
        # Verification controls
        controls_frame = tk.Frame(main_frame, bg='#ffffff')
        controls_frame.pack(fill='x', pady=(0, 10))
        
        # Feedback section
        feedback_frame = tk.LabelFrame(controls_frame, text="Verification Notes (Optional)", 
                                      font=('Arial', 11, 'bold'), bg='#ffffff', fg='#34495e')
        feedback_frame.pack(fill='x', pady=(0, 15))
        
        self.feedback_text = tk.Text(feedback_frame, height=3, font=('Arial', 10), 
                                    wrap=tk.WORD, relief='flat', bd=1)
        self.feedback_text.pack(fill='x', padx=10, pady=10)
        
        # Action buttons
        button_frame = tk.Frame(controls_frame, bg='#ffffff')
        button_frame.pack(fill='x')
        
        # Reject button
        reject_btn = tk.Button(button_frame, text="❌ Reject & Stop Pipeline", 
                              command=self.reject_data,
                              font=('Arial', 11, 'bold'), bg='#e74c3c', fg='white',
                              relief='flat', bd=0, padx=20, pady=10)
        reject_btn.pack(side='left', padx=(0, 10))
        
        # Modify button
        modify_btn = tk.Button(button_frame, text="✏️ Request Modifications", 
                              command=self.request_modifications,
                              font=('Arial', 11, 'bold'), bg='#f39c12', fg='white',
                              relief='flat', bd=0, padx=20, pady=10)
        modify_btn.pack(side='left', padx=(0, 10))
        
        # Approve button
        approve_btn = tk.Button(button_frame, text="✅ Approve & Continue", 
                               command=self.approve_data,
                               font=('Arial', 11, 'bold'), bg='#27ae60', fg='white',
                               relief='flat', bd=0, padx=20, pady=10)
        approve_btn.pack(side='right')
        
        # Bind Enter key to approve
        self.dialog.bind('<Return>', lambda e: self.approve_data())
        self.dialog.bind('<Escape>', lambda e: self.reject_data())
        
        # Focus on approve button
        approve_btn.focus_set()
    
    def get_verification_description(self) -> str:
        """Get description text based on verification type"""
        descriptions = {
            "data": "Please review the data below and verify it meets quality standards before continuing.",
            "scraping": "Verify that the scraped data looks correct and complete.",
            "normalization": "Check that the data normalization process worked correctly.",
            "order_processing": "Review the order processing results for accuracy.",
            "apps_script": "Verify the Apps Script function execution results.",
            "qr_generation": "Check that QR codes were generated correctly.",
            "validation": "Final validation - ensure all pipeline steps completed successfully."
        }
        return descriptions.get(self.verification_type, descriptions["data"])
    
    def create_data_preview(self, parent):
        """Create scrollable data preview"""
        # Create notebook for different data views
        notebook = ttk.Notebook(parent)
        notebook.pack(fill='both', expand=True)
        
        # Summary tab
        summary_frame = tk.Frame(notebook, bg='#ffffff')
        notebook.add(summary_frame, text="Summary")
        
        summary_text = scrolledtext.ScrolledText(summary_frame, height=10, font=('Courier New', 10))
        summary_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Add summary information
        summary_info = self.format_summary_data()
        summary_text.insert(tk.END, summary_info)
        summary_text.config(state=tk.DISABLED)
        
        # Details tab
        details_frame = tk.Frame(notebook, bg='#ffffff')
        notebook.add(details_frame, text="Raw Data")
        
        details_text = scrolledtext.ScrolledText(details_frame, height=10, font=('Courier New', 9))
        details_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Add detailed data
        details_info = json.dumps(self.data_preview, indent=2, default=str)
        details_text.insert(tk.END, details_info)
        details_text.config(state=tk.DISABLED)
        
        # Statistics tab if applicable
        if isinstance(self.data_preview, dict) and 'statistics' in self.data_preview:
            stats_frame = tk.Frame(notebook, bg='#ffffff')
            notebook.add(stats_frame, text="Statistics")
            
            stats_text = scrolledtext.ScrolledText(stats_frame, height=10, font=('Courier New', 10))
            stats_text.pack(fill='both', expand=True, padx=10, pady=10)
            
            stats_info = json.dumps(self.data_preview['statistics'], indent=2, default=str)
            stats_text.insert(tk.END, stats_info)
            stats_text.config(state=tk.DISABLED)
    
    def format_summary_data(self) -> str:
        """Format data for summary view"""
        summary_lines = [
            f"🎯 VERIFICATION CHECKPOINT: {self.stage_name.upper()}",
            f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "📊 DATA SUMMARY:",
            "─" * 50
        ]
        
        if isinstance(self.data_preview, dict):
            for key, value in self.data_preview.items():
                if key == 'statistics':
                    continue
                
                if isinstance(value, (list, tuple)):
                    summary_lines.append(f"  {key}: {len(value)} items")
                    if len(value) > 0 and hasattr(value[0], '__dict__'):
                        summary_lines.append(f"    Sample: {str(value[0])[:100]}...")
                elif isinstance(value, dict):
                    summary_lines.append(f"  {key}: {len(value)} entries")
                else:
                    val_str = str(value)
                    if len(val_str) > 100:
                        val_str = val_str[:100] + "..."
                    summary_lines.append(f"  {key}: {val_str}")
        else:
            summary_lines.append(f"  Data Type: {type(self.data_preview).__name__}")
            summary_lines.append(f"  Content: {str(self.data_preview)[:200]}...")
        
        return "\n".join(summary_lines)
    
    def approve_data(self):
        """Approve the data and continue pipeline"""
        self.approved = True
        self.feedback = self.feedback_text.get("1.0", tk.END).strip()
        self.result = {
            "approved": True,
            "action": "continue",
            "feedback": self.feedback,
            "timestamp": datetime.now().isoformat()
        }
        self.dialog.destroy()
    
    def reject_data(self):
        """Reject the data and stop pipeline"""
        self.approved = False
        self.feedback = self.feedback_text.get("1.0", tk.END).strip()
        self.result = {
            "approved": False,
            "action": "stop",
            "feedback": self.feedback,
            "timestamp": datetime.now().isoformat()
        }
        self.dialog.destroy()
    
    def request_modifications(self):
        """Request modifications to the data"""
        self.approved = False
        self.feedback = self.feedback_text.get("1.0", tk.END).strip()
        
        if not self.feedback:
            messagebox.showwarning("Feedback Required", 
                                 "Please provide feedback about what modifications are needed.")
            return
        
        self.result = {
            "approved": False,
            "action": "modify",
            "feedback": self.feedback,
            "timestamp": datetime.now().isoformat()
        }
        self.dialog.destroy()
    
    def wait_for_result(self) -> Dict[str, Any]:
        """Wait for user decision and return result"""
        self.dialog.wait_window()
        return self.result or {"approved": False, "action": "stop", "feedback": "", "timestamp": datetime.now().isoformat()}

class IntegratedScraperPipelineUI:
    """Complete integrated UI combining scraper and pipeline functionality"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        
        # Initialize components
        self.db_manager = self.setup_database()
        self.message_queue = queue.Queue()
        self.current_thread = None
        self.pipeline_paused = False
        self.verification_results = {}
        
        # UI state tracking
        self.ui_state = {
            'current_tab': 0,
            'pipeline_running': False,
            'verification_pending': False,
            'selected_dealerships': [],
            'current_stage': None
        }
        
        # Initialize data structures
        self.dealership_vars = {}
        self.pipeline_stages = self.initialize_pipeline_stages()
        self.selected_dealerships = []
        
        # Create main interface
        self.create_integrated_interface()
        
        # Start update loop
        self.root.after(100, self.process_message_queue)
        
        print("✅ Integrated Scraper Pipeline UI initialized successfully")
    
    def setup_window(self):
        """Configure main window"""
        self.root.title("🚗 Silverfox Assistant - Integrated Scraper & Pipeline System")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 700)
        
        # Configure styling
        style = ttk.Style()
        style.configure('Pipeline.TFrame', background='#f8f9fa')
        style.configure('Stage.TFrame', background='#ffffff')
        style.configure('Header.TLabel', font=('Arial', 14, 'bold'))
        style.configure('Subheader.TLabel', font=('Arial', 12, 'bold'))
        
        # Center window
        self.center_window()
    
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - 700
        y = (self.root.winfo_screenheight() // 2) - 450
        self.root.geometry(f"1400x900+{x}+{y}")
    
    def setup_database(self):
        """Setup database manager"""
        from polished_universal_pipeline_ui import DatabaseManager
        return DatabaseManager()
    
    def initialize_pipeline_stages(self) -> Dict[str, Any]:
        """Initialize pipeline stages with verification checkpoints"""
        stages = {}
        
        stage_configs = [
            {
                'id': 'dealership_selection',
                'name': 'Dealership Selection',
                'description': 'Select and configure dealerships for scraping',
                'verification': True,
                'verification_type': 'selection'
            },
            {
                'id': 'data_scraping',
                'name': 'Data Scraping',
                'description': 'Scrape vehicle data from selected dealerships',
                'verification': True,
                'verification_type': 'scraping'
            },
            {
                'id': 'data_normalization',
                'name': 'Data Normalization',
                'description': 'Clean and normalize scraped data',
                'verification': True,
                'verification_type': 'normalization'
            },
            {
                'id': 'order_processing',
                'name': 'Order Processing',
                'description': 'Process orders using business logic',
                'verification': True,
                'verification_type': 'order_processing'
            },
            {
                'id': 'apps_script_functions',
                'name': 'Apps Script Functions',
                'description': 'Execute Google Apps Script equivalent functions',
                'verification': True,
                'verification_type': 'apps_script'
            },
            {
                'id': 'qr_generation',
                'name': 'QR Code Generation',
                'description': 'Generate QR codes for processed vehicles',
                'verification': True,
                'verification_type': 'qr_generation'
            },
            {
                'id': 'final_validation',
                'name': 'Final Validation',
                'description': 'Complete pipeline validation and export',
                'verification': True,
                'verification_type': 'validation'
            }
        ]
        
        for i, config in enumerate(stage_configs):
            stages[config['id']] = {
                'order': i + 1,
                'name': config['name'],
                'description': config['description'],
                'status': 'pending',
                'progress': 0.0,
                'verification_required': config['verification'],
                'verification_type': config['verification_type'],
                'verification_result': None,
                'started_at': None,
                'completed_at': None,
                'error_message': None,
                'data': None
            }
        
        return stages
    
    def create_integrated_interface(self):
        """Create the main integrated interface"""
        # Main container
        main_container = tk.Frame(self.root, bg='#f8f9fa')
        main_container.pack(fill='both', expand=True)
        
        # Header section
        self.create_header_section(main_container)
        
        # Main content area with notebook
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Create tabs
        self.create_pipeline_overview_tab()
        self.create_dealership_selection_tab()
        self.create_scraping_control_tab()
        self.create_data_processing_tab()
        self.create_order_management_tab()
        self.create_system_monitoring_tab()
        
        # Status bar
        self.create_status_bar(main_container)
        
        # Bind tab change events
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
    
    def create_header_section(self, parent):
        """Create header with pipeline status"""
        header_frame = tk.Frame(parent, bg='#2c3e50', height=80)
        header_frame.pack(fill='x', padx=20, pady=(20, 0))
        header_frame.pack_propagate(False)
        
        # Left side - title
        left_frame = tk.Frame(header_frame, bg='#2c3e50')
        left_frame.pack(side='left', fill='y', padx=20, pady=15)
        
        title_label = tk.Label(left_frame, text="🚗 Silverfox Assistant", 
                              font=('Arial', 18, 'bold'), bg='#2c3e50', fg='white')
        title_label.pack(anchor='w')
        
        subtitle_label = tk.Label(left_frame, text="Integrated Scraper & Pipeline System", 
                                 font=('Arial', 12), bg='#2c3e50', fg='#bdc3c7')
        subtitle_label.pack(anchor='w')
        
        # Right side - pipeline status
        right_frame = tk.Frame(header_frame, bg='#2c3e50')
        right_frame.pack(side='right', fill='y', padx=20, pady=15)
        
        self.pipeline_status_label = tk.Label(right_frame, text="Pipeline Status: Ready", 
                                            font=('Arial', 12, 'bold'), bg='#2c3e50', fg='#27ae60')
        self.pipeline_status_label.pack(anchor='e')
        
        self.pipeline_progress_label = tk.Label(right_frame, text="Progress: 0/7 stages completed", 
                                              font=('Arial', 10), bg='#2c3e50', fg='#bdc3c7')
        self.pipeline_progress_label.pack(anchor='e')
    
    def create_pipeline_overview_tab(self):
        """Create pipeline overview tab"""
        overview_frame = tk.Frame(self.notebook, bg='#ffffff')
        self.notebook.add(overview_frame, text="📊 Pipeline Overview")
        
        # Create scrollable frame
        canvas = tk.Canvas(overview_frame, bg='#ffffff')
        scrollbar = ttk.Scrollbar(overview_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#ffffff')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True, padx=20, pady=20)
        scrollbar.pack(side="right", fill="y", pady=20)
        
        # Pipeline stages visualization
        self.create_pipeline_stages_visual(scrollable_frame)
        
        # Control panel
        self.create_pipeline_controls(scrollable_frame)
        
        # Store reference to canvas for scroll binding
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
    
    def create_pipeline_stages_visual(self, parent):
        """Create visual pipeline stages"""
        stages_frame = tk.LabelFrame(parent, text="Pipeline Stages", font=('Arial', 14, 'bold'),
                                   bg='#ffffff', fg='#2c3e50', padx=20, pady=15)
        stages_frame.pack(fill='x', pady=(0, 20))
        
        self.stage_widgets = {}
        
        for stage_id, stage_info in self.pipeline_stages.items():
            stage_frame = self.create_stage_widget(stages_frame, stage_id, stage_info)
            stage_frame.pack(fill='x', pady=5)
            self.stage_widgets[stage_id] = stage_frame
    
    def create_stage_widget(self, parent, stage_id: str, stage_info: Dict[str, Any]) -> tk.Frame:
        """Create individual stage widget"""
        # Main stage frame
        stage_frame = tk.Frame(parent, bg='#f8f9fa', relief='solid', bd=1)
        
        # Left side - stage info
        info_frame = tk.Frame(stage_frame, bg='#f8f9fa')
        info_frame.pack(side='left', fill='both', expand=True, padx=15, pady=10)
        
        # Stage title with status icon
        title_frame = tk.Frame(info_frame, bg='#f8f9fa')
        title_frame.pack(fill='x')
        
        # Status icon
        status_icon = "⏳" if stage_info['status'] == 'pending' else \
                     "🔄" if stage_info['status'] == 'running' else \
                     "✅" if stage_info['status'] == 'completed' else "❌"
        
        icon_label = tk.Label(title_frame, text=status_icon, font=('Arial', 16), bg='#f8f9fa')
        icon_label.pack(side='left', padx=(0, 10))
        
        title_label = tk.Label(title_frame, text=f"{stage_info['order']}. {stage_info['name']}", 
                              font=('Arial', 12, 'bold'), bg='#f8f9fa', fg='#2c3e50')
        title_label.pack(side='left')
        
        # Verification indicator
        if stage_info['verification_required']:
            verify_label = tk.Label(title_frame, text="🔍 Verification Required", 
                                   font=('Arial', 10), bg='#f8f9fa', fg='#f39c12')
            verify_label.pack(side='right')
        
        # Description
        desc_label = tk.Label(info_frame, text=stage_info['description'], 
                             font=('Arial', 10), bg='#f8f9fa', fg='#7f8c8d',
                             wraplength=600, justify='left')
        desc_label.pack(fill='x', pady=(5, 0))
        
        # Progress bar
        progress_frame = tk.Frame(info_frame, bg='#f8f9fa')
        progress_frame.pack(fill='x', pady=(10, 0))
        
        progress_bar = ttk.Progressbar(progress_frame, length=300, mode='determinate')
        progress_bar.pack(side='left')
        progress_bar['value'] = stage_info['progress']
        
        progress_label = tk.Label(progress_frame, text=f"{stage_info['progress']:.1f}%", 
                                 font=('Arial', 10), bg='#f8f9fa', fg='#34495e')
        progress_label.pack(side='left', padx=(10, 0))
        
        # Right side - action buttons
        action_frame = tk.Frame(stage_frame, bg='#f8f9fa')
        action_frame.pack(side='right', padx=15, pady=10)
        
        # Skip verification button (for testing)
        if stage_info['verification_required'] and stage_info['status'] == 'pending':
            skip_btn = tk.Button(action_frame, text="Skip Verification", 
                                command=lambda s=stage_id: self.skip_verification(s),
                                font=('Arial', 9), bg='#95a5a6', fg='white',
                                relief='flat', bd=0, padx=10, pady=5)
            skip_btn.pack()
        
        # Store widget references
        setattr(stage_frame, 'progress_bar', progress_bar)
        setattr(stage_frame, 'progress_label', progress_label)
        setattr(stage_frame, 'icon_label', icon_label)
        setattr(stage_frame, 'title_label', title_label)
        
        return stage_frame
    
    def create_pipeline_controls(self, parent):
        """Create pipeline control buttons"""
        controls_frame = tk.LabelFrame(parent, text="Pipeline Controls", font=('Arial', 14, 'bold'),
                                     bg='#ffffff', fg='#2c3e50', padx=20, pady=15)
        controls_frame.pack(fill='x', pady=20)
        
        # Button frame
        button_frame = tk.Frame(controls_frame, bg='#ffffff')
        button_frame.pack(fill='x', pady=10)
        
        # Start pipeline button
        self.start_pipeline_btn = tk.Button(button_frame, text="🚀 Start Complete Pipeline", 
                                          command=self.start_complete_pipeline,
                                          font=('Arial', 12, 'bold'), bg='#27ae60', fg='white',
                                          relief='flat', bd=0, padx=25, pady=12)
        self.start_pipeline_btn.pack(side='left', padx=(0, 10))
        
        # Pause/Resume button
        self.pause_pipeline_btn = tk.Button(button_frame, text="⏸️ Pause Pipeline", 
                                          command=self.toggle_pipeline_pause,
                                          font=('Arial', 12, 'bold'), bg='#f39c12', fg='white',
                                          relief='flat', bd=0, padx=25, pady=12)
        self.pause_pipeline_btn.pack(side='left', padx=(0, 10))
        
        # Stop pipeline button
        self.stop_pipeline_btn = tk.Button(button_frame, text="⏹️ Stop Pipeline", 
                                         command=self.stop_pipeline,
                                         font=('Arial', 12, 'bold'), bg='#e74c3c', fg='white',
                                         relief='flat', bd=0, padx=25, pady=12)
        self.stop_pipeline_btn.pack(side='left', padx=(0, 10))
        
        # Reset pipeline button
        reset_btn = tk.Button(button_frame, text="🔄 Reset Pipeline", 
                            command=self.reset_pipeline,
                            font=('Arial', 12), bg='#95a5a6', fg='white',
                            relief='flat', bd=0, padx=20, pady=12)
        reset_btn.pack(side='right')
        
        # Options frame
        options_frame = tk.Frame(controls_frame, bg='#ffffff')
        options_frame.pack(fill='x', pady=(10, 0))
        
        # Verification options
        self.auto_approve_var = tk.BooleanVar(value=False)
        auto_approve_cb = tk.Checkbutton(options_frame, text="Auto-approve verifications (Testing Only)", 
                                       variable=self.auto_approve_var,
                                       font=('Arial', 10), bg='#ffffff', fg='#e74c3c')
        auto_approve_cb.pack(side='left')
        
        # Pipeline mode
        mode_label = tk.Label(options_frame, text="Mode:", font=('Arial', 10, 'bold'), 
                            bg='#ffffff', fg='#2c3e50')
        mode_label.pack(side='right', padx=(0, 5))
        
        self.pipeline_mode_var = tk.StringVar(value="interactive")
        mode_combo = ttk.Combobox(options_frame, textvariable=self.pipeline_mode_var,
                                values=["interactive", "automated", "manual"],
                                state="readonly", width=12)
        mode_combo.pack(side='right')
    
    def create_dealership_selection_tab(self):
        """Create dealership selection tab"""
        selection_frame = tk.Frame(self.notebook, bg='#ffffff')
        self.notebook.add(selection_frame, text="🏢 Dealership Selection")
        
        # Import dealership selection from existing GUI
        self.create_dealership_selection_interface(selection_frame)
    
    def create_dealership_selection_interface(self, parent):
        """Create dealership selection interface based on existing GUI"""
        # Header
        header_frame = tk.Frame(parent, bg='#ffffff', pady=20)
        header_frame.pack(fill='x', padx=20)
        
        title_label = tk.Label(header_frame, text="Select Dealerships for Processing", 
                              font=('Arial', 16, 'bold'), bg='#ffffff', fg='#2c3e50')
        title_label.pack(anchor='w')
        
        subtitle_label = tk.Label(header_frame, text="Choose which dealerships to include in the pipeline", 
                                 font=('Arial', 12), bg='#ffffff', fg='#7f8c8d')
        subtitle_label.pack(anchor='w', pady=(5, 0))
        
        # Search and filter section
        filter_frame = tk.LabelFrame(parent, text="Search & Filter", font=('Arial', 12, 'bold'),
                                   bg='#ffffff', fg='#2c3e50', padx=15, pady=10)
        filter_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        search_frame = tk.Frame(filter_frame, bg='#ffffff')
        search_frame.pack(fill='x', pady=5)
        
        tk.Label(search_frame, text="Search:", font=('Arial', 10, 'bold'), 
                bg='#ffffff', fg='#2c3e50').pack(side='left', padx=(0, 10))
        
        self.dealership_search = tk.Entry(search_frame, font=('Arial', 10), width=30)
        self.dealership_search.pack(side='left', padx=(0, 20))
        self.dealership_search.bind('<KeyRelease>', self._filter_dealerships)
        
        # Selection controls
        selection_controls = tk.Frame(filter_frame, bg='#ffffff')
        selection_controls.pack(fill='x', pady=(10, 5))
        
        select_all_btn = tk.Button(selection_controls, text="Select All", 
                                  command=self.select_all_dealerships,
                                  font=('Arial', 10), bg='#3498db', fg='white',
                                  relief='flat', bd=0, padx=15, pady=5)
        select_all_btn.pack(side='left', padx=(0, 10))
        
        clear_all_btn = tk.Button(selection_controls, text="Clear All", 
                                 command=self.clear_all_dealerships,
                                 font=('Arial', 10), bg='#95a5a6', fg='white',
                                 relief='flat', bd=0, padx=15, pady=5)
        clear_all_btn.pack(side='left')
        
        # Selected count
        self.selected_count_label = tk.Label(selection_controls, text="Selected: 0", 
                                           font=('Arial', 10, 'bold'), bg='#ffffff', fg='#27ae60')
        self.selected_count_label.pack(side='right')
        
        # Dealership list
        list_frame = tk.LabelFrame(parent, text="Available Dealerships", font=('Arial', 12, 'bold'),
                                 bg='#ffffff', fg='#2c3e50', padx=15, pady=10)
        list_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Create scrollable dealership list
        self.create_scrollable_dealership_list(list_frame)
        
        # Load dealerships
        self.load_dealerships()
    
    def create_scrollable_dealership_list(self, parent):
        """Create scrollable dealership list"""
        # Create canvas and scrollbar
        canvas = tk.Canvas(parent, bg='#f8f9fa', highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        self.dealership_container = tk.Frame(canvas, bg='#f8f9fa')
        
        self.dealership_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.dealership_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        canvas.pack(side="left", fill="both", expand=True, padx=(0, 5))
        scrollbar.pack(side="right", fill="y")
        
        # Mouse wheel binding
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        self.dealership_canvas = canvas
    
    def load_dealerships(self):
        """Load and display dealerships"""
        # Clear existing
        for widget in self.dealership_container.winfo_children():
            widget.destroy()
        
        self.dealership_vars = {}
        self.dealership_checkboxes = {}
        
        # Load from DEALERSHIP_CONFIGS
        dealerships = sorted(DEALERSHIP_CONFIGS.keys()) if DEALERSHIP_CONFIGS else []
        
        if not dealerships:
            # Create sample dealerships for testing
            dealerships = [
                "columbia_honda", "joe_machens_hyundai", "volkswagen_columbia",
                "toyota_columbia", "ford_columbia", "chevrolet_columbia"
            ]
        
        # Create grid layout
        cols = 2
        for i, dealership_id in enumerate(dealerships):
            var = tk.BooleanVar()
            self.dealership_vars[dealership_id] = var
            
            row = i // cols
            col = i % cols
            
            # Create dealership card
            card_frame = tk.Frame(self.dealership_container, bg='#ffffff', relief='solid', bd=1)
            card_frame.grid(row=row, column=col, sticky='ew', padx=5, pady=3)
            
            # Configure grid weights
            self.dealership_container.grid_columnconfigure(col, weight=1)
            
            # Checkbox and name
            cb_frame = tk.Frame(card_frame, bg='#ffffff')
            cb_frame.pack(fill='x', padx=15, pady=10)
            
            cb = tk.Checkbutton(cb_frame, text=dealership_id.replace('_', ' ').title(), 
                               variable=var, command=self.update_selection_count,
                               font=('Arial', 11, 'bold'), bg='#ffffff', fg='#2c3e50')
            cb.pack(side='left')
            
            # Status indicator
            status_label = tk.Label(cb_frame, text="✅ Ready", font=('Arial', 9), 
                                   bg='#ffffff', fg='#27ae60')
            status_label.pack(side='right')
            
            self.dealership_checkboxes[dealership_id] = cb
        
        self.update_selection_count()
    
    def update_selection_count(self):
        """Update selected dealership count"""
        selected_count = sum(1 for var in self.dealership_vars.values() if var.get())
        self.selected_count_label.config(text=f"Selected: {selected_count}")
    
    def select_all_dealerships(self):
        """Select all visible dealerships"""
        for var in self.dealership_vars.values():
            var.set(True)
        self.update_selection_count()
    
    def clear_all_dealerships(self):
        """Clear all dealership selections"""
        for var in self.dealership_vars.values():
            var.set(False)
        self.update_selection_count()
    
    def _filter_dealerships(self, event=None):
        """Filter dealerships based on search term"""
        search_term = self.dealership_search.get().lower()
        
        for dealership_id, cb in self.dealership_checkboxes.items():
            if search_term in dealership_id.lower():
                cb.master.master.pack(fill='x', padx=5, pady=3)
            else:
                cb.master.master.pack_forget()
    
    def create_scraping_control_tab(self):
        """Create scraping control tab"""
        scraping_frame = tk.Frame(self.notebook, bg='#ffffff')
        self.notebook.add(scraping_frame, text="🔍 Scraping Control")
        
        # Add scraping controls here
        self.create_scraping_interface(scraping_frame)
    
    def create_scraping_interface(self, parent):
        """Create scraping control interface"""
        # Header
        header_frame = tk.Frame(parent, bg='#ffffff', pady=20)
        header_frame.pack(fill='x', padx=20)
        
        title_label = tk.Label(header_frame, text="Scraping Configuration & Control", 
                              font=('Arial', 16, 'bold'), bg='#ffffff', fg='#2c3e50')
        title_label.pack(anchor='w')
        
        # Configuration section
        config_frame = tk.LabelFrame(parent, text="Scraping Configuration", font=('Arial', 12, 'bold'),
                                   bg='#ffffff', fg='#2c3e50', padx=15, pady=10)
        config_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        # Settings grid
        settings_frame = tk.Frame(config_frame, bg='#ffffff')
        settings_frame.pack(fill='x', pady=10)
        
        # Concurrent connections
        tk.Label(settings_frame, text="Concurrent Connections:", font=('Arial', 10, 'bold'), 
                bg='#ffffff', fg='#2c3e50').grid(row=0, column=0, sticky='w', padx=(0, 10), pady=5)
        
        self.concurrent_var = tk.IntVar(value=3)
        concurrent_spin = tk.Spinbox(settings_frame, from_=1, to=10, textvariable=self.concurrent_var, 
                                   width=5, font=('Arial', 10))
        concurrent_spin.grid(row=0, column=1, sticky='w', pady=5)
        
        # Timeout
        tk.Label(settings_frame, text="Timeout (seconds):", font=('Arial', 10, 'bold'), 
                bg='#ffffff', fg='#2c3e50').grid(row=0, column=2, sticky='w', padx=(20, 10), pady=5)
        
        self.timeout_var = tk.IntVar(value=30)
        timeout_spin = tk.Spinbox(settings_frame, from_=10, to=120, textvariable=self.timeout_var, 
                                width=5, font=('Arial', 10))
        timeout_spin.grid(row=0, column=3, sticky='w', pady=5)
        
        # Validation
        self.validate_data_var = tk.BooleanVar(value=True)
        validate_cb = tk.Checkbutton(settings_frame, text="Validate scraped data", 
                                   variable=self.validate_data_var, font=('Arial', 10), 
                                   bg='#ffffff', fg='#2c3e50')
        validate_cb.grid(row=1, column=0, columnspan=2, sticky='w', pady=5)
        
        # Progress section
        progress_frame = tk.LabelFrame(parent, text="Scraping Progress", font=('Arial', 12, 'bold'),
                                     bg='#ffffff', fg='#2c3e50', padx=15, pady=10)
        progress_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Progress display
        self.create_scraping_progress_display(progress_frame)
    
    def create_scraping_progress_display(self, parent):
        """Create scraping progress display"""
        # Overall progress
        overall_frame = tk.Frame(parent, bg='#ffffff')
        overall_frame.pack(fill='x', pady=10)
        
        tk.Label(overall_frame, text="Overall Progress:", font=('Arial', 11, 'bold'), 
                bg='#ffffff', fg='#2c3e50').pack(anchor='w')
        
        self.overall_progress = ttk.Progressbar(overall_frame, length=500, mode='determinate')
        self.overall_progress.pack(fill='x', pady=5)
        
        self.overall_progress_label = tk.Label(overall_frame, text="Ready to start", 
                                             font=('Arial', 10), bg='#ffffff', fg='#7f8c8d')
        self.overall_progress_label.pack(anchor='w')
        
        # Activity log
        log_frame = tk.Frame(parent, bg='#ffffff')
        log_frame.pack(fill='both', expand=True, pady=(10, 0))
        
        tk.Label(log_frame, text="Activity Log:", font=('Arial', 11, 'bold'), 
                bg='#ffffff', fg='#2c3e50').pack(anchor='w')
        
        # Create scrolled text for log
        self.activity_log = scrolledtext.ScrolledText(log_frame, height=15, font=('Courier New', 9),
                                                     wrap=tk.WORD, state=tk.DISABLED)
        self.activity_log.pack(fill='both', expand=True, pady=5)
        
        # Configure text tags for colored output
        self.activity_log.tag_configure("timestamp", foreground="#7f8c8d", font=('Courier New', 8))
        self.activity_log.tag_configure("info", foreground="#2c3e50")
        self.activity_log.tag_configure("success", foreground="#27ae60", font=('Courier New', 9, 'bold'))
        self.activity_log.tag_configure("warning", foreground="#f39c12", font=('Courier New', 9, 'bold'))
        self.activity_log.tag_configure("error", foreground="#e74c3c", font=('Courier New', 9, 'bold'))
    
    def create_data_processing_tab(self):
        """Create data processing tab"""
        processing_frame = tk.Frame(self.notebook, bg='#ffffff')
        self.notebook.add(processing_frame, text="⚙️ Data Processing")
        
        # Add data processing controls
        tk.Label(processing_frame, text="Data Processing Controls", 
                font=('Arial', 16, 'bold'), bg='#ffffff', fg='#2c3e50').pack(pady=20)
    
    def create_order_management_tab(self):
        """Create order management tab"""
        order_frame = tk.Frame(self.notebook, bg='#ffffff')
        self.notebook.add(order_frame, text="📋 Order Management")
        
        # Add order management controls
        tk.Label(order_frame, text="Order Management System", 
                font=('Arial', 16, 'bold'), bg='#ffffff', fg='#2c3e50').pack(pady=20)
    
    def create_system_monitoring_tab(self):
        """Create system monitoring tab"""
        monitoring_frame = tk.Frame(self.notebook, bg='#ffffff')
        self.notebook.add(monitoring_frame, text="📊 System Monitor")
        
        # Add system monitoring
        tk.Label(monitoring_frame, text="System Monitoring Dashboard", 
                font=('Arial', 16, 'bold'), bg='#ffffff', fg='#2c3e50').pack(pady=20)
    
    def create_status_bar(self, parent):
        """Create status bar"""
        status_frame = tk.Frame(parent, bg='#34495e', height=30)
        status_frame.pack(fill='x', side='bottom')
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(status_frame, text="Ready", font=('Arial', 10), 
                                   bg='#34495e', fg='white')
        self.status_label.pack(side='left', padx=20, pady=5)
        
        # Connection status
        self.connection_status = tk.Label(status_frame, text="Database: Connected", 
                                        font=('Arial', 10), bg='#34495e', fg='#27ae60')
        self.connection_status.pack(side='right', padx=20, pady=5)
    
    def on_tab_changed(self, event):
        """Handle tab change events"""
        self.ui_state['current_tab'] = self.notebook.index(self.notebook.select())
    
    def start_complete_pipeline(self):
        """Start the complete pipeline with verification checkpoints"""
        # Validate dealership selection
        selected = [name for name, var in self.dealership_vars.items() if var.get()]
        if not selected:
            messagebox.showwarning("No Selection", 
                                 "Please select at least one dealership before starting the pipeline.")
            return
        
        if self.ui_state['pipeline_running']:
            messagebox.showinfo("Pipeline Running", 
                              "Pipeline is already running. Please wait for completion or stop it first.")
            return
        
        # Store selected dealerships
        self.selected_dealerships = selected
        
        # Reset pipeline state
        self.reset_pipeline_state()
        
        # Start pipeline in background thread
        self.ui_state['pipeline_running'] = True
        self.current_thread = threading.Thread(target=self._run_complete_pipeline_with_verification, daemon=True)
        self.current_thread.start()
        
        # Update UI
        self.update_pipeline_controls_state()
        self.log_activity("🚀 Starting complete pipeline with verification checkpoints", "info")
    
    def _run_complete_pipeline_with_verification(self):
        """Run complete pipeline with human verification checkpoints"""
        try:
            self.message_queue.put({
                'type': 'status',
                'text': f'Starting pipeline for {len(self.selected_dealerships)} dealerships...'
            })
            
            # Execute each stage with verification
            pipeline_successful = True
            
            for stage_id, stage_info in self.pipeline_stages.items():
                if not self.ui_state['pipeline_running']:
                    break
                
                # Update stage status
                self.update_stage_status(stage_id, 'running', 0.0)
                self.ui_state['current_stage'] = stage_id
                
                # Execute stage
                stage_data = None
                try:
                    stage_data = self._execute_pipeline_stage(stage_id, stage_info)
                    self.update_stage_status(stage_id, 'completed', 100.0)
                    
                    # Human verification checkpoint
                    if stage_info['verification_required'] and not self.auto_approve_var.get():
                        verification_result = self._request_human_verification(stage_id, stage_info, stage_data)
                        
                        if not verification_result['approved']:
                            if verification_result['action'] == 'stop':
                                pipeline_successful = False
                                break
                            elif verification_result['action'] == 'modify':
                                # Handle modification request
                                self.log_activity(f"⚠️ Stage {stage_info['name']} requires modifications: {verification_result['feedback']}", "warning")
                                # For now, we'll continue but could implement retry logic
                    
                except Exception as e:
                    self.update_stage_status(stage_id, 'error', stage_info.get('progress', 0))
                    self.log_activity(f"❌ Error in stage {stage_info['name']}: {str(e)}", "error")
                    pipeline_successful = False
                    break
            
            # Update final status
            if pipeline_successful:
                self.message_queue.put({
                    'type': 'status',
                    'text': 'Pipeline completed successfully!'
                })
                self.log_activity("✅ Pipeline completed successfully!", "success")
            else:
                self.message_queue.put({
                    'type': 'status',
                    'text': 'Pipeline stopped due to error or rejection'
                })
                self.log_activity("⛔ Pipeline stopped", "warning")
                
        except Exception as e:
            self.log_activity(f"💥 Pipeline failed with error: {str(e)}", "error")
            self.message_queue.put({
                'type': 'status',
                'text': f'Pipeline failed: {str(e)}'
            })
        finally:
            self.ui_state['pipeline_running'] = False
            self.ui_state['current_stage'] = None
            self.message_queue.put({'type': 'pipeline_finished'})
    
    def _execute_pipeline_stage(self, stage_id: str, stage_info: Dict[str, Any]) -> Any:
        """Execute individual pipeline stage"""
        self.log_activity(f"🔄 Executing stage: {stage_info['name']}", "info")
        
        # Simulate stage execution with progress updates
        for progress in range(0, 101, 25):
            if not self.ui_state['pipeline_running']:
                break
            
            self.update_stage_status(stage_id, 'running', progress)
            time.sleep(0.5)  # Simulate work
        
        # Stage-specific logic would go here
        stage_data = {
            'stage_id': stage_id,
            'dealerships': self.selected_dealerships,
            'timestamp': datetime.now().isoformat(),
            'results': f"Stage {stage_info['name']} completed successfully",
            'statistics': {
                'items_processed': len(self.selected_dealerships),
                'success_rate': 100.0,
                'execution_time': '30s'
            }
        }
        
        return stage_data
    
    def _request_human_verification(self, stage_id: str, stage_info: Dict[str, Any], stage_data: Any) -> Dict[str, Any]:
        """Request human verification for pipeline stage"""
        self.log_activity(f"🔍 Requesting human verification for {stage_info['name']}", "info")
        
        # Create verification dialog on main thread
        verification_result = {}
        
        def show_verification():
            dialog = HumanVerificationDialog(
                self.root, 
                stage_info['name'], 
                stage_data,
                stage_info['verification_type']
            )
            verification_result.update(dialog.wait_for_result())
        
        # Run on main thread
        self.root.after_idle(show_verification)
        
        # Wait for result
        while not verification_result:
            time.sleep(0.1)
        
        # Log verification result
        if verification_result['approved']:
            self.log_activity(f"✅ Stage {stage_info['name']} approved by user", "success")
        else:
            action_text = {
                'stop': 'stopped',
                'modify': 'requires modifications'
            }.get(verification_result['action'], 'rejected')
            self.log_activity(f"⚠️ Stage {stage_info['name']} {action_text} by user", "warning")
        
        return verification_result
    
    def update_stage_status(self, stage_id: str, status: str, progress: float):
        """Update stage status in UI"""
        if stage_id not in self.pipeline_stages:
            return
        
        # Update data
        self.pipeline_stages[stage_id]['status'] = status
        self.pipeline_stages[stage_id]['progress'] = progress
        
        if status == 'running' and not self.pipeline_stages[stage_id]['started_at']:
            self.pipeline_stages[stage_id]['started_at'] = datetime.now().isoformat()
        elif status in ['completed', 'error']:
            self.pipeline_stages[stage_id]['completed_at'] = datetime.now().isoformat()
        
        # Update UI widget
        self.message_queue.put({
            'type': 'update_stage',
            'stage_id': stage_id,
            'status': status,
            'progress': progress
        })
    
    def skip_verification(self, stage_id: str):
        """Skip verification for testing purposes"""
        if stage_id in self.pipeline_stages:
            self.pipeline_stages[stage_id]['verification_result'] = {
                'approved': True,
                'action': 'continue',
                'feedback': 'Skipped for testing',
                'timestamp': datetime.now().isoformat()
            }
            self.log_activity(f"⏭️ Verification skipped for {self.pipeline_stages[stage_id]['name']}", "warning")
    
    def toggle_pipeline_pause(self):
        """Toggle pipeline pause state"""
        self.pipeline_paused = not self.pipeline_paused
        
        if self.pipeline_paused:
            self.pause_pipeline_btn.config(text="▶️ Resume Pipeline")
            self.log_activity("⏸️ Pipeline paused", "warning")
        else:
            self.pause_pipeline_btn.config(text="⏸️ Pause Pipeline")
            self.log_activity("▶️ Pipeline resumed", "info")
    
    def stop_pipeline(self):
        """Stop the pipeline"""
        if not self.ui_state['pipeline_running']:
            return
        
        result = messagebox.askyesno("Stop Pipeline", 
                                   "Are you sure you want to stop the pipeline? This will cancel all remaining stages.")
        
        if result:
            self.ui_state['pipeline_running'] = False
            self.log_activity("⛔ Pipeline stopped by user", "warning")
            self.update_pipeline_controls_state()
    
    def reset_pipeline(self):
        """Reset pipeline to initial state"""
        if self.ui_state['pipeline_running']:
            messagebox.showwarning("Pipeline Running", 
                                 "Cannot reset pipeline while it's running. Please stop it first.")
            return
        
        self.reset_pipeline_state()
        self.log_activity("🔄 Pipeline reset", "info")
    
    def reset_pipeline_state(self):
        """Reset all pipeline stages to initial state"""
        for stage_id, stage_info in self.pipeline_stages.items():
            stage_info['status'] = 'pending'
            stage_info['progress'] = 0.0
            stage_info['verification_result'] = None
            stage_info['started_at'] = None
            stage_info['completed_at'] = None
            stage_info['error_message'] = None
            stage_info['data'] = None
        
        # Update UI
        self.message_queue.put({'type': 'reset_pipeline'})
    
    def update_pipeline_controls_state(self):
        """Update pipeline control button states"""
        running = self.ui_state['pipeline_running']
        
        self.start_pipeline_btn.config(state='disabled' if running else 'normal')
        self.pause_pipeline_btn.config(state='normal' if running else 'disabled')
        self.stop_pipeline_btn.config(state='normal' if running else 'disabled')
    
    def process_message_queue(self):
        """Process messages from background threads"""
        try:
            while True:
                message = self.message_queue.get_nowait()
                self.handle_message(message)
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.process_message_queue)
    
    def handle_message(self, message: Dict[str, Any]):
        """Handle messages from background threads"""
        msg_type = message.get('type')
        
        if msg_type == 'status':
            self.status_label.config(text=message['text'])
        
        elif msg_type == 'update_stage':
            stage_id = message['stage_id']
            if stage_id in self.stage_widgets:
                widget = self.stage_widgets[stage_id]
                
                # Update progress bar
                widget.progress_bar['value'] = message['progress']
                widget.progress_label.config(text=f"{message['progress']:.1f}%")
                
                # Update status icon
                status_icon = "⏳" if message['status'] == 'pending' else \
                             "🔄" if message['status'] == 'running' else \
                             "✅" if message['status'] == 'completed' else "❌"
                widget.icon_label.config(text=status_icon)
        
        elif msg_type == 'reset_pipeline':
            self.reset_ui_pipeline_display()
        
        elif msg_type == 'pipeline_finished':
            self.update_pipeline_controls_state()
        
        elif msg_type == 'log_activity':
            self.log_activity(message['text'], message.get('level', 'info'))
    
    def reset_ui_pipeline_display(self):
        """Reset UI pipeline display"""
        for stage_id, widget in self.stage_widgets.items():
            widget.progress_bar['value'] = 0
            widget.progress_label.config(text="0.0%")
            widget.icon_label.config(text="⏳")
    
    def log_activity(self, message: str, level: str = "info"):
        """Log activity to the activity log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        level_config = {
            "info": ("ℹ️", "info"),
            "success": ("✅", "success"),
            "warning": ("⚠️", "warning"),
            "error": ("❌", "error")
        }
        
        icon, tag = level_config.get(level, ("ℹ️", "info"))
        
        # Enable text widget
        self.activity_log.config(state=tk.NORMAL)
        
        # Insert timestamp
        self.activity_log.insert(tk.END, f"[{timestamp}] ", "timestamp")
        
        # Insert message with icon
        self.activity_log.insert(tk.END, f"{icon} {message}\n", tag)
        
        # Auto-scroll to bottom
        self.activity_log.see(tk.END)
        
        # Disable text widget
        self.activity_log.config(state=tk.DISABLED)
        
        # Limit log size (keep last 1000 lines)
        lines = self.activity_log.get("1.0", tk.END).split('\n')
        if len(lines) > 1000:
            self.activity_log.config(state=tk.NORMAL)
            self.activity_log.delete("1.0", "100.0")
            self.activity_log.config(state=tk.DISABLED)
    
    def run(self):
        """Start the application"""
        self.log_activity("🚗 Integrated Scraper Pipeline UI started", "success")
        self.root.mainloop()

def main():
    """Main entry point"""
    try:
        app = IntegratedScraperPipelineUI()
        app.run()
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()