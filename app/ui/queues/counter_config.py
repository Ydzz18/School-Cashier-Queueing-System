"""Counter configuration UI for managing multiple service counters."""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import logging
from typing import Callable, Optional, List

from app.ui.components import THEME, StyledButton, Divider, SectionHeader
from app.models.counter import Counter
from app.services.counter_service import CounterService

logger = logging.getLogger(__name__)


class CounterConfigDialog(tk.Toplevel):
    """Dialog for adding/editing/deleting counters."""
    
    def __init__(
        self,
        parent: tk.Widget,
        counter_service: CounterService,
        on_counters_changed: Optional[Callable[[List[Counter]], None]] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.title("Counter Management")
        self.geometry("600x500")
        self.configure(bg=THEME["bg_dark"])
        self.grab_set()
        
        self.counter_service = counter_service
        self.on_counters_changed = on_counters_changed
        
        self._build_ui()
        self._load_counters()
    
    def _build_ui(self):
        """Build the counter management UI."""
        # Header
        header = tk.Frame(self, bg=THEME["bg_card"])
        header.pack(fill="x", padx=0, pady=0)
        
        tk.Label(
            header,
            text="  ⚙  Counter Management",
            font=("Segoe UI", 16, "bold"),
            fg=THEME["accent"],
            bg=THEME["bg_card"],
            pady=12,
        ).pack(side="left", padx=THEME["pad"])
        
        Divider(self).pack(fill="x")
        
        # Main content
        content = tk.Frame(self, bg=THEME["bg_dark"])
        content.pack(fill="both", expand=True, padx=THEME["pad"], pady=THEME["pad"])
        
        # Buttons frame
        btn_frame = tk.Frame(content, bg=THEME["bg_dark"])
        btn_frame.pack(fill="x", pady=(0, THEME["pad"]))
        
        StyledButton(
            btn_frame,
            "+ Add Counter",
            preset="primary",
            command=self._add_counter
        ).pack(side="left", padx=(0, 8))
        
        StyledButton(
            btn_frame,
            "📝 Edit",
            preset="muted",
            command=self._edit_selected
        ).pack(side="left", padx=4)
        
        StyledButton(
            btn_frame,
            "🗑 Delete",
            preset="danger",
            command=self._delete_selected
        ).pack(side="left", padx=4)
        
        # Counters list
        list_frame = tk.Frame(content, bg=THEME["bg_dark"])
        list_frame.pack(fill="both", expand=True)
        
        SectionHeader(list_frame, "Active Counters").pack(anchor="w", pady=(0, 12))
        
        # Treeview for counters
        columns = ("Name", "Department", "Operator", "Served", "Status")
        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            height=15,
            show="tree headings"
        )
        
        # Style the treeview
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            'Treeview',
            background=THEME["bg_card"],
            foreground=THEME["text"],
            fieldbackground=THEME["bg_card"],
            borderwidth=0
        )
        style.configure(
            'Treeview.Heading',
            background=THEME["bg_input"],
            foreground=THEME["text"]
        )
        style.map('Treeview', background=[('selected', THEME["accent"])])
        
        # Define columns
        self.tree.column("#0", width=0, stretch=False)
        self.tree.column("Name", anchor="w", width=120)
        self.tree.column("Department", anchor="w", width=100)
        self.tree.column("Operator", anchor="w", width=100)
        self.tree.column("Served", anchor="center", width=60)
        self.tree.column("Status", anchor="center", width=80)
        
        # Headings
        self.tree.heading("#0", text="", anchor="w")
        self.tree.heading("Name", text="Name", anchor="w")
        self.tree.heading("Department", text="Department", anchor="w")
        self.tree.heading("Operator", text="Operator", anchor="w")
        self.tree.heading("Served", text="Served", anchor="center")
        self.tree.heading("Status", text="Status", anchor="center")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        
        # Footer
        Divider(self).pack(fill="x")
        footer = tk.Frame(self, bg=THEME["bg_card"])
        footer.pack(fill="x")
        
        StyledButton(
            footer,
            "Close",
            preset="muted",
            command=self.destroy
        ).pack(side="right", padx=THEME["pad"], pady=THEME["pad_s"])
    
    def _load_counters(self):
        """Load and display counters from service."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Load counters
        counters = self.counter_service.get_all_counters()
        
        for counter in counters:
            status = "Active" if counter.is_active else "Inactive"
            self.tree.insert(
                "",
                "end",
                iid=counter.counter_id,
                text="",
                values=(
                    counter.counter_name,
                    counter.department,
                    counter.operator_name,
                    counter.tickets_served_today,
                    status
                ),
                tags=("active" if counter.is_active else "inactive",)
            )
    
    def _add_counter(self):
        """Show dialog to add a new counter."""
        dialog = tk.Toplevel(self)
        dialog.title("Add Counter")
        dialog.geometry("400x250")
        dialog.configure(bg=THEME["bg_dark"])
        dialog.grab_set()
        
        # Counter name
        tk.Label(dialog, text="Counter Name:", bg=THEME["bg_dark"], fg=THEME["text"]).pack(
            anchor="w", padx=THEME["pad"], pady=(THEME["pad"], 4)
        )
        name_entry = tk.Entry(dialog, bg=THEME["bg_input"], fg=THEME["text"])
        name_entry.pack(fill="x", padx=THEME["pad"], pady=(0, 12))
        name_entry.insert(0, "Counter")
        
        # Department
        tk.Label(dialog, text="Department:", bg=THEME["bg_dark"], fg=THEME["text"]).pack(
            anchor="w", padx=THEME["pad"], pady=(THEME["pad"], 4)
        )
        dept_entry = tk.Entry(dialog, bg=THEME["bg_input"], fg=THEME["text"])
        dept_entry.pack(fill="x", padx=THEME["pad"], pady=(0, 12))
        
        # Operator
        tk.Label(dialog, text="Operator Name (optional):", bg=THEME["bg_dark"], fg=THEME["text"]).pack(
            anchor="w", padx=THEME["pad"], pady=(THEME["pad"], 4)
        )
        operator_entry = tk.Entry(dialog, bg=THEME["bg_input"], fg=THEME["text"])
        operator_entry.pack(fill="x", padx=THEME["pad"], pady=(0, 20))
        
        def save_counter():
            name = name_entry.get().strip()
            dept = dept_entry.get().strip()
            operator = operator_entry.get().strip()
            
            if not name:
                messagebox.showwarning("Validation", "Counter name is required")
                return
            
            self.counter_service.create_counter(name, dept, operator)
            self._load_counters()
            
            if self.on_counters_changed:
                self.on_counters_changed(self.counter_service.get_all_counters())
            
            dialog.destroy()
            messagebox.showinfo("Success", f"Counter '{name}' created successfully")
        
        button_frame = tk.Frame(dialog, bg=THEME["bg_dark"])
        button_frame.pack(fill="x", padx=THEME["pad"], pady=THEME["pad"])
        
        StyledButton(button_frame, "Save", preset="primary", command=save_counter).pack(
            side="left", padx=(0, 8)
        )
        StyledButton(button_frame, "Cancel", preset="muted", command=dialog.destroy).pack(
            side="left"
        )
    
    def _edit_selected(self):
        """Edit the selected counter."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Selection", "Please select a counter to edit")
            return
        
        counter_id = selection[0]
        selected_counter = self.counter_service.get_counter(counter_id)
        
        if not selected_counter:
            messagebox.showerror("Error", "Counter not found")
            return
        
        # Show edit dialog
        dialog = tk.Toplevel(self)
        dialog.title(f"Edit {selected_counter.counter_name}")
        dialog.geometry("400x250")
        dialog.configure(bg=THEME["bg_dark"])
        dialog.grab_set()
        
        # Counter name
        tk.Label(dialog, text="Counter Name:", bg=THEME["bg_dark"], fg=THEME["text"]).pack(
            anchor="w", padx=THEME["pad"], pady=(THEME["pad"], 4)
        )
        name_entry = tk.Entry(dialog, bg=THEME["bg_input"], fg=THEME["text"])
        name_entry.pack(fill="x", padx=THEME["pad"], pady=(0, 12))
        name_entry.insert(0, selected_counter.counter_name)
        
        # Department
        tk.Label(dialog, text="Department:", bg=THEME["bg_dark"], fg=THEME["text"]).pack(
            anchor="w", padx=THEME["pad"], pady=(THEME["pad"], 4)
        )
        dept_entry = tk.Entry(dialog, bg=THEME["bg_input"], fg=THEME["text"])
        dept_entry.pack(fill="x", padx=THEME["pad"], pady=(0, 12))
        dept_entry.insert(0, selected_counter.department)
        
        # Operator
        tk.Label(dialog, text="Operator Name:", bg=THEME["bg_dark"], fg=THEME["text"]).pack(
            anchor="w", padx=THEME["pad"], pady=(THEME["pad"], 4)
        )
        operator_entry = tk.Entry(dialog, bg=THEME["bg_input"], fg=THEME["text"])
        operator_entry.pack(fill="x", padx=THEME["pad"], pady=(0, 20))
        operator_entry.insert(0, selected_counter.operator_name)
        
        def save_changes():
            self.counter_service.update_counter(
                selected_counter.counter_id,
                counter_name=name_entry.get().strip(),
                department=dept_entry.get().strip(),
                operator_name=operator_entry.get().strip()
            )
            self._load_counters()
            
            if self.on_counters_changed:
                self.on_counters_changed(self.counter_service.get_all_counters())
            
            dialog.destroy()
            messagebox.showinfo("Success", "Counter updated successfully")
        
        button_frame = tk.Frame(dialog, bg=THEME["bg_dark"])
        button_frame.pack(fill="x", padx=THEME["pad"], pady=THEME["pad"])
        
        StyledButton(button_frame, "Save", preset="primary", command=save_changes).pack(
            side="left", padx=(0, 8)
        )
        StyledButton(button_frame, "Cancel", preset="muted", command=dialog.destroy).pack(
            side="left"
        )
    
    def _delete_selected(self):
        """Delete the selected counter."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Selection", "Please select a counter to delete")
            return
        
        counter_id = selection[0]
        selected_counter = self.counter_service.get_counter(counter_id)
        if not selected_counter:
            messagebox.showerror("Error", "Counter not found")
            return

        counter_name = selected_counter.counter_name
        
        if messagebox.askyesno("Confirm Delete", f"Delete counter '{counter_name}'?"):
            self.counter_service.delete_counter(selected_counter.counter_id)
            self._load_counters()
            
            if self.on_counters_changed:
                self.on_counters_changed(self.counter_service.get_all_counters())
            
            messagebox.showinfo("Success", f"Counter '{counter_name}' deleted")
