#!/usr/bin/env python3
# gui_installer_windows.py - GUI Installer cho Windows với 1 nút bấm

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import os
import sys
import webbrowser
from pathlib import Path

class PhotoboothInstallerWindows:
    def __init__(self, root):
        self.root = root
        self.root.title("PhotoboothApp - One-Click Installer (Windows)")
        self.root.geometry("700x550")
        self.root.resizable(True, True)
        
        # Center window
        self.center_window()
        
        self.setup_ui()
        self.check_installation_status()
        
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def setup_ui(self):
        # Title
        title_label = tk.Label(
            self.root, 
            text="🚀 PhotoboothApp Installer (Windows)", 
            font=("Arial", 18, "bold"),
            fg="#2E86AB"
        )
        title_label.pack(pady=20)
        
        # Warning label for admin rights
        warning_label = tk.Label(
            self.root,
            text="⚠️ Make sure to run this as Administrator for full installation",
            font=("Arial", 10),
            fg="#FF9800",
            bg="#FFF3E0"
        )
        warning_label.pack(pady=5, padx=20, fill="x")
        
        # Status frame
        status_frame = tk.Frame(self.root)
        status_frame.pack(pady=10, padx=20, fill="x")
        
        self.status_label = tk.Label(
            status_frame,
            text="🔍 Checking installation status...",
            font=("Arial", 12),
            fg="#666666"
        )
        self.status_label.pack()
        
        # Main button
        self.main_button = tk.Button(
            self.root,
            text="🎯 ONE-CLICK INSTALL & DEPLOY",
            font=("Arial", 14, "bold"),
            bg="#4CAF50",
            fg="white",
            height=2,
            width=35,
            command=self.start_installation,
            relief="raised",
            bd=3
        )
        self.main_button.pack(pady=30)
        
        # Progress bar
        self.progress = ttk.Progressbar(
            self.root,
            mode='indeterminate',
            length=500
        )
        self.progress.pack(pady=10)
        
        # Log area
        log_frame = tk.Frame(self.root)
        log_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        tk.Label(log_frame, text="📋 Installation Log:", font=("Arial", 10, "bold")).pack(anchor="w")
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            width=80,
            font=("Consolas", 9),
            bg="#f8f9fa",
            fg="#333333"
        )
        self.log_text.pack(fill="both", expand=True)
        
        # Control buttons
        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=10)
        
        self.open_app_button = tk.Button(
            control_frame,
            text="🌐 Open App",
            command=self.open_app,
            bg="#2196F3",
            fg="white",
            state="disabled"
        )
        self.open_app_button.pack(side="left", padx=5)
        
        self.stop_autostart_button = tk.Button(
            control_frame,
            text="⏹️ Stop Auto-Start",
            command=self.stop_autostart,
            bg="#FF9800",
            fg="white",
            state="disabled"
        )
        self.stop_autostart_button.pack(side="left", padx=5)
        
        self.rebuild_button = tk.Button(
            control_frame,
            text="🔨 Rebuild",
            command=self.rebuild_app,
            bg="#9C27B0",
            fg="white",
            state="disabled"
        )
        self.rebuild_button.pack(side="left", padx=5)
        
        self.open_folder_button = tk.Button(
            control_frame,
            text="📁 Open Folder",
            command=self.open_folder,
            bg="#607D8B",
            fg="white"
        )
        self.open_folder_button.pack(side="left", padx=5)
        
    def log(self, message):
        """Add message to log area"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update()
        
    def check_installation_status(self):
        """Check if app is already installed"""
        exe_path = Path("dist/PhotoboothApp.exe")
        
        # Check Task Scheduler
        try:
            result = subprocess.run(
                ['schtasks', '/query', '/tn', 'PhotoboothApp AutoStart'],
                capture_output=True, text=True
            )
            autostart_configured = result.returncode == 0
        except:
            autostart_configured = False
        
        if exe_path.exists() and autostart_configured:
            self.status_label.config(
                text="✅ PhotoboothApp is installed and configured!",
                fg="#4CAF50"
            )
            self.main_button.config(
                text="🔄 REINSTALL & REDEPLOY",
                bg="#FF9800"
            )
            self.open_app_button.config(state="normal")
            self.stop_autostart_button.config(state="normal")
            self.rebuild_button.config(state="normal")
            self.log("✅ Found existing installation with auto-start")
        elif exe_path.exists():
            self.status_label.config(
                text="⚠️ App is built but auto-start not configured",
                fg="#FF9800"
            )
            self.main_button.config(
                text="⚙️ CONFIGURE AUTO-START",
                bg="#FF9800"
            )
            self.open_app_button.config(state="normal")
            self.rebuild_button.config(state="normal")
            self.log("⚠️ Found app but auto-start not configured")
        else:
            self.status_label.config(
                text="❌ PhotoboothApp not installed",
                fg="#F44336"
            )
            self.log("❌ No existing installation found")
            
    def run_command(self, command, description):
        """Run Windows batch command and log output"""
        self.log(f"🔄 {description}...")
        try:
            # Use cmd /c to run batch files
            if command.endswith('.bat'):
                cmd = ['cmd', '/c', command]
            else:
                cmd = command.split()
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                cwd=os.getcwd()
            )
            
            for line in process.stdout:
                line = line.strip()
                if line and not line.startswith('Press any key'):
                    self.log(f"  {line}")
                    
            process.wait()
            
            if process.returncode == 0:
                self.log(f"✅ {description} completed successfully!")
                return True
            else:
                self.log(f"❌ {description} failed with exit code {process.returncode}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error during {description}: {str(e)}")
            return False
            
    def check_admin_rights(self):
        """Check if running as administrator"""
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
            
    def start_installation(self):
        """Start installation process in separate thread"""
        # Check admin rights
        if not self.check_admin_rights():
            response = messagebox.askywarning(
                "Administrator Rights Required",
                "This installer works best with Administrator privileges.\n\n"
                "Some features like auto-start may not work properly without admin rights.\n\n"
                "Do you want to continue anyway?",
                type=messagebox.YESNO
            )
            if response == messagebox.NO:
                return
                
        self.main_button.config(state="disabled")
        self.progress.start(10)
        
        # Run installation in separate thread to prevent GUI freeze
        thread = threading.Thread(target=self.installation_worker)
        thread.daemon = True
        thread.start()
        
    def installation_worker(self):
        """Main installation worker thread"""
        try:
            self.log("🚀 Starting PhotoboothApp installation for Windows...")
            self.log("=" * 60)
            
            # Check if quick_setup exists, if not use individual steps
            if Path("quick_setup_windows.bat").exists():
                if not self.run_command("quick_setup_windows.bat", "Running complete setup"):
                    self.installation_failed("Complete setup failed")
                    return
            else:
                # Step 1: Fresh install (environment setup)
                if not self.run_command("fresh_install_windows.bat", "Setting up environment"):
                    self.installation_failed("Environment setup failed")
                    return
                    
                # Step 2: Deploy (build + auto-start)
                if not self.run_command("deploy_windows.bat", "Building and deploying app"):
                    self.installation_failed("Deployment failed")
                    return
                
            # Success!
            self.installation_completed()
            
        except Exception as e:
            self.installation_failed(f"Unexpected error: {str(e)}")
            
    def installation_completed(self):
        """Handle successful installation"""
        self.root.after(0, self._installation_completed_ui)
        
    def _installation_completed_ui(self):
        """Update UI after successful installation"""
        self.progress.stop()
        self.main_button.config(state="normal")
        
        self.log("=" * 60)
        self.log("🎉 INSTALLATION COMPLETED SUCCESSFULLY! 🎉")
        self.log("✅ PhotoboothApp is ready to use!")
        self.log("🌐 Access your app at: http://localhost:5000")
        self.log("🔄 App will start automatically on login")
        
        self.status_label.config(
            text="🎉 Installation completed successfully!",
            fg="#4CAF50"
        )
        
        self.main_button.config(
            text="🔄 REINSTALL & REDEPLOY",
            bg="#FF9800"
        )
        
        # Enable control buttons
        self.open_app_button.config(state="normal")
        self.stop_autostart_button.config(state="normal")
        self.rebuild_button.config(state="normal")
        
        # Show success dialog
        messagebox.showinfo(
            "Installation Complete", 
            "🎉 PhotoboothApp installed successfully!\n\n"
            "✅ App will start automatically on login\n"
            "🌐 Access at: http://localhost:5000\n"
            "📁 Executable: dist\\PhotoboothApp.exe\n\n"
            "Click 'Open App' to launch it now!"
        )
        
    def installation_failed(self, error_msg):
        """Handle installation failure"""
        self.root.after(0, lambda: self._installation_failed_ui(error_msg))
        
    def _installation_failed_ui(self, error_msg):
        """Update UI after installation failure"""
        self.progress.stop()
        self.main_button.config(state="normal")
        
        self.log("=" * 60)
        self.log(f"❌ INSTALLATION FAILED: {error_msg}")
        self.log("📋 Check the log above for details")
        
        self.status_label.config(
            text="❌ Installation failed",
            fg="#F44336"
        )
        
        messagebox.showerror("Installation Failed", f"❌ {error_msg}\n\nCheck the log for details.")
        
    def open_app(self):
        """Open the app in browser"""
        webbrowser.open("http://localhost:5000")
        self.log("🌐 Opening app in browser...")
        
    def open_folder(self):
        """Open current folder in Windows Explorer"""
        os.startfile(os.getcwd())
        self.log("📁 Opening folder in Explorer...")
        
    def stop_autostart(self):
        """Stop auto-start"""
        if self.run_command("uninstall_autostart_windows.bat", "Stopping auto-start"):
            self.log("⏹️ Auto-start disabled")
            self.stop_autostart_button.config(state="disabled")
            messagebox.showinfo("Auto-Start Stopped", "Auto-start has been disabled.")
        else:
            messagebox.showerror("Error", "Failed to stop auto-start.")
            
    def rebuild_app(self):
        """Rebuild the app"""
        self.main_button.config(state="disabled")
        self.progress.start(10)
        
        thread = threading.Thread(target=self._rebuild_worker)
        thread.daemon = True
        thread.start()
        
    def _rebuild_worker(self):
        """Rebuild worker thread"""
        success = self.run_command("build_exe_windows.bat", "Rebuilding app")
        
        self.root.after(0, lambda: self._rebuild_completed(success))
        
    def _rebuild_completed(self, success):
        """Handle rebuild completion"""
        self.progress.stop()
        self.main_button.config(state="normal")
        
        if success:
            self.log("🔨 Rebuild completed successfully!")
            messagebox.showinfo("Rebuild Complete", "App rebuilt successfully!")
        else:
            messagebox.showerror("Rebuild Failed", "Failed to rebuild app.")

def main():
    # Check if we're in the right directory
    if not Path("app.py").exists():
        messagebox.showerror(
            "Wrong Directory", 
            "Please run this installer from the PhotoboothApp directory\n"
            "(the directory containing app.py)"
        )
        sys.exit(1)
        
    root = tk.Tk()
    app = PhotoboothInstallerWindows(root)
    root.mainloop()

if __name__ == "__main__":
    main()
