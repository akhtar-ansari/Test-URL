import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from github import Github, GithubException
import os
from datetime import datetime
import requests
import clipboard
import csv
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

class GithubAccessApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Access Github")
        self.style = ttk.Style("flatly")  # Modern theme
        self.github = None
        self.repo = None
        self.setup_ui()
        
    def setup_ui(self):
        # Section 1: Credentials
        self.frame1 = ttk.LabelFrame(self.root, text="GitHub Credentials", padding=10)
        self.frame1.pack(padx=10, pady=5, fill="x")
        
        ttk.Label(self.frame1, text="Username:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.username_entry = ttk.Entry(self.frame1)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(self.frame1, text="Personal Access Token:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.token_entry = ttk.Entry(self.frame1, show="*")
        self.token_entry.grid(row=1, column=1, padx=5, pady=5)
        
        self.save_button = ttk.Button(self.frame1, text="Save", command=self.save_credentials, bootstyle=SUCCESS)
        self.save_button.grid(row=2, column=0, columnspan=2, pady=10)
        
        self.status_label = ttk.Label(self.frame1, text="Connection Status: Disconnected")
        self.status_label.grid(row=0, column=2, padx=10)
        
        self.status_canvas = tk.Canvas(self.frame1, width=20, height=20, highlightthickness=0)
        self.status_canvas.grid(row=0, column=3)
        self.status_indicator = self.status_canvas.create_oval(5, 5, 15, 15, fill="red")
        
        # Section 2: Repository Selection
        self.frame2 = ttk.LabelFrame(self.root, text="Repository Selection", padding=10)
        self.frame2.pack(padx=10, pady=5, fill="x")
        
        self.repo_combo = ttk.Combobox(self.frame2, state="readonly")
        self.repo_combo.grid(row=0, column=0, padx=5, pady=5)
        self.repo_combo.bind("<<ComboboxSelected>>", self.load_files)
        
        self.refresh_button = ttk.Button(self.frame2, text="Refresh", command=self.refresh_repos, bootstyle=INFO)
        self.refresh_button.grid(row=0, column=1, padx=5, pady=5)
        
        # Section 3: File Management
        self.frame3 = ttk.LabelFrame(self.root, text="File Management", padding=10)
        self.frame3.pack(padx=10, pady=5, fill="both", expand=True)
        
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.frame3, textvariable=self.search_var)
        self.search_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.search_var.trace("w", self.filter_files)
        
        self.upload_button = ttk.Button(self.frame3, text="+", command=self.upload_files, bootstyle=PRIMARY)
        self.upload_button.grid(row=0, column=1, padx=5, pady=5)
        
        self.tree = ttk.Treeview(self.frame3, columns=("File Name", "File Type", "Size", "Date", "URL"), show="headings", selectmode='extended')
        self.tree.heading("File Name", text="File Name")
        self.tree.heading("File Type", text="File Type")
        self.tree.heading("Size", text="Size (KB)")
        self.tree.heading("Date", text="Date of Upload")
        self.tree.heading("URL", text="URL")
        self.tree.column("File Name", width=200)
        self.tree.column("File Type", width=100)
        self.tree.column("Size", width=100)
        self.tree.column("Date", width=150)
        self.tree.column("URL", width=200)
        self.tree.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        
        self.scrollbar = ttk.Scrollbar(self.frame3, orient="vertical", command=self.tree.yview)
        self.scrollbar.grid(row=1, column=3, sticky="ns")
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        
        self.frame3.columnconfigure(0, weight=1)
        self.frame3.rowconfigure(1, weight=1)
        
        self.tree.bind("<Double-1>", self.download_file)

        # Download button
        self.download_button = ttk.Button(self.frame3, text="Download", command=self.download_selected_files, bootstyle=PRIMARY)
        self.download_button.grid(row=0, column=2, padx=5, pady=5)

        # Download CSV button
        self.download_csv_button = ttk.Button(self.frame3, text="Download CSV", command=self.download_csv, bootstyle=PRIMARY)
        self.download_csv_button.grid(row=0, column=3, padx=5, pady=5)

    def save_credentials(self):
        username = self.username_entry.get()
        token = self.token_entry.get()
        try:
            self.github = Github(token)
            user = self.github.get_user()   
            self.status_label.config(text=f"Connection Status: Connected ({user.login})")
            self.status_canvas.itemconfig(self.status_indicator, fill="green")
            self.refresh_repos()
        except GithubException as e:
            messagebox.showerror("Error", f"Failed to connect: {str(e)}")
            self.status_label.config(text="Connection Status: Disconnected")
            self.status_canvas.itemconfig(self.status_indicator, fill="red")
            
    def refresh_repos(self):
        if not self.github:
            messagebox.showerror("Error", "Please connect to GitHub first.")
            return
        try:
            repos = [repo.name for repo in self.github.get_user().get_repos()]
            self.repo_combo["values"] = repos
            if repos:
                self.repo_combo.current(0)
                self.load_files()
        except GithubException as e:
            messagebox.showerror("Error", f"Failed to fetch repositories: {str(e)}")
            
    def load_files(self, event=None):
        self.tree.delete(*self.tree.get_children())
        repo_name = self.repo_combo.get()
        if not repo_name or not self.github:
            return
        try:
            self.repo = self.github.get_user().get_repo(repo_name)
            contents = self.repo.get_contents("")
            for content in contents:
                if content.type == "file":
                    size = content.size / 1024  # Convert to KB
                    date = datetime.strptime(content.last_modified, "%a, %d %b %Y %H:%M:%S %Z")
                    self.tree.insert("", "end", values=(
                        content.name,
                        content.name.split(".")[-1] if "." in content.name else "N/A",
                        f"{size:.2f}",
                        date.strftime("%Y-%m-%d %H:%M:%S"),
                        content.html_url  # Store the actual URL for copying
                    ))
        except GithubException as e:
            messagebox.showerror("Error", f"Failed to load files: {str(e)}")
            
    def filter_files(self, *args):
        search_term = self.search_var.get().lower()
        self.tree.delete(*self.tree.get_children())
        if not self.repo:
            return
        try:
            contents = self.repo.get_contents("")
            for content in contents:
                if content.type == "file" and search_term in content.name.lower():
                    size = content.size / 1024
                    date = datetime.strptime(content.last_modified, "%a, %d %b %Y %H:%M:%S %Z")
                    self.tree.insert("", "end", values=(
                        content.name,
                        content.name.split(".")[-1] if "." in content.name else "N/A",
                        f"{size:.2f}",
                        date.strftime("%Y-%m-%d %H:%M:%S"),
                        content.html_url  # Store the actual URL for copying
                    ))
        except GithubException as e:
            messagebox.showerror("Error", f"Failed to filter files: {str(e)}")
            
    def download_file(self, event):
        item = self.tree.selection()
        if not item:
            return
        file_name = self.tree.item(item, "values")[0]
        self.download_single_file(file_name)
        
    def download_single_file(self, file_name):
        try:
            content = self.repo.get_contents(file_name)
            file_path = filedialog.asksaveasfilename(defaultextension=f".{content.name.split('.')[-1]}", initialfile=content.name)
            if file_path:
                with open(file_path, "wb") as f:
                    f.write(requests.get(content.download_url).content)
                messagebox.showinfo("Success", f"File {content.name} downloaded to {file_path}")
        except GithubException as e:
            messagebox.showerror("Error", f"Failed to download file: {str(e)}")
            
    def download_selected_files(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "No files selected for download.")
            return
        
        # Download files in a single operation
        for item in selected_items:
            file_name = self.tree.item(item, "values")[0]
            self.download_single_file(file_name)  # You can modify this to improve performance if needed

    def upload_files(self):
        if not self.repo:
            messagebox.showerror("Error", "Please select a repository first.")
            return
        files = filedialog.askopenfilenames()
        uploaded_files = []
        for file_path in files:
            try:
                with open(file_path, "rb") as f:
                    content = f.read()
                file_name = os.path.basename(file_path)
                self.repo.create_file(file_name, f"Upload {file_name}", content)
                uploaded_files.append(file_name)
            except GithubException as e:
                messagebox.showerror("Error", f"Failed to upload file {file_name}: {str(e)}")
        
        # Show final confirmation after all files are uploaded
        if uploaded_files:
            messagebox.showinfo("Success", f"Uploaded {len(uploaded_files)} files successfully.")

    def download_csv(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "No files selected for CSV download.")
            return
        
        csv_file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not csv_file_path:
            return
        
        with open(csv_file_path, mode='w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)
            # Write header
            csv_writer.writerow(["File Name", "File Type", "Size (KB)", "Date of Upload", "URL"])
            for item in selected_items:
                values = self.tree.item(item, "values")
                csv_writer.writerow(values)
        
        messagebox.showinfo("Success", f"CSV file saved to {csv_file_path}")

if __name__ == "__main__":
    root = ttk.Window()
    app = GithubAccessApp(root)
    root.mainloop()