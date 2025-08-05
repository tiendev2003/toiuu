#!/usr/bin/env python3
# gui_installer.py - GUI Installer với 1 nút bấm duy nhất

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import os
import sys
from pathlib import Path

class PhotoboothInstaller:
    def __init__(self, root):
        self.root = root
        self.root.title("PhotoboothApp - One-Click Installer")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Center window
        self.root.eval('tk::PlaceWindow . center')
        
        self.setup_ui()
        self.check_installation_status()
        
    def setup_ui(self):
        # Title
        title_label = tk.Label(
            self.root, 
            text="🚀 PhotoboothApp Installer", 
            font=("Arial", 18, "bold"),
            fg="#2E86AB"
        )
        title_label.pack(pady=20)
        
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
            width=30,
            command=self.start_installation,
            relief="raised",
            bd=3
        )
        self.main_button.pack(pady=30)
        
        # Progress bar
        self.progress = ttk.Progressbar(
            self.root,
            mode='indeterminate',
            length=400
        )
        self.progress.pack(pady=10)
        
        # Log area
        log_frame = tk.Frame(self.root)
        log_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        tk.Label(log_frame, text="📋 Installation Log:", font=("Arial", 10, "bold")).pack(anchor="w")
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            width=70,
            font=("Courier", 9),
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
        
    def log(self, message):
        """Add message to log area"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update()
        
    def check_installation_status(self):
        """Check if app is already installed"""
        exe_path = Path("dist/PhotoboothApp")
        plist_path = Path.home() / "Library/LaunchAgents/com.photobooth.app.plist"
        
        if exe_path.exists() and plist_path.exists():
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
            self.log("✅ Found existing installation")
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
        """Run shell command and log output"""
        self.log(f"🔄 {description}...")
        try:
            # Make script executable if it's a .sh file
            if command.endswith('.sh'):
                subprocess.run(['chmod', '+x', command], check=True)
            
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                cwd=os.getcwd()
            )
            
            for line in process.stdout:
                line = line.strip()
                if line:
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
            
    def start_installation(self):
        """Start installation process in separate thread"""
        self.main_button.config(state="disabled")
        self.progress.start(10)
        
        # Run installation in separate thread to prevent GUI freeze
        thread = threading.Thread(target=self.installation_worker)
        thread.daemon = True
        thread.start()
        
    def installation_worker(self):
        """Main installation worker thread"""
        try:
            self.log("🚀 Starting PhotoboothApp installation...")
            self.log("=" * 50)
            
            # Step 1: Fresh install (environment setup)
            if not self.run_command("./fresh_install.sh", "Setting up environment"):
                self.installation_failed("Environment setup failed")
                return
                
            # Step 2: Deploy (build + auto-start)
            if not self.run_command("./deploy.sh", "Building and deploying app"):
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
        
        self.log("=" * 50)
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
            "🌐 Access at: http://localhost:5000\n\n"
            "Click 'Open App' to launch it now!"
        )
        
    def installation_failed(self, error_msg):
        """Handle installation failure"""
        self.root.after(0, lambda: self._installation_failed_ui(error_msg))
        
    def _installation_failed_ui(self, error_msg):
        """Update UI after installation failure"""
        self.progress.stop()
        self.main_button.config(state="normal")
        
        self.log("=" * 50)
        self.log(f"❌ INSTALLATION FAILED: {error_msg}")
        self.log("📋 Check the log above for details")
        
        self.status_label.config(
            text="❌ Installation failed",
            fg="#F44336"
        )
        
        messagebox.showerror("Installation Failed", f"❌ {error_msg}\n\nCheck the log for details.")
        
    def open_app(self):
        """Open the app in browser"""
        import webbrowser
        webbrowser.open("http://localhost:5000")
        self.log("🌐 Opening app in browser...")
        
    def stop_autostart(self):
        """Stop auto-start"""
        if self.run_command("./uninstall_autostart.sh", "Stopping auto-start"):
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
        success = self.run_command("./build_exe.sh", "Rebuilding app")
        
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
    app = PhotoboothInstaller(root)
    root.mainloop()

if __name__ == "__main__":
    main()
