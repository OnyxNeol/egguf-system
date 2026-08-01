"""
EGGUF GUI Application

The main GUI that handles the user flow:
1. User opens an EGGUF file
2. Window pops up: "Do you want to add any extensions to your AI?"
   - Yes -> browse for EFE file -> SCAN -> show scan results -> apply if accepted
   - Just exploring/doing something else -> show EGGUF info

Built with tkinter (no external dependencies needed).
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import json
import threading
from datetime import datetime

from egguf_format import read_egguf, write_egguf, EGGUFFile
from efe_format import read_efe, is_efe_file
from scanner import scan_efe, format_scan_report, ScanResult
from extensions import apply_efe_to_egguf, get_extension_summary, get_type_display


# Theme colors
BG_COLOR = "#1a1a2e"
PANEL_COLOR = "#16213e"
ACCENT_COLOR = "#0f3460"
ACCENT2_COLOR = "#e94560"
TEXT_COLOR = "#e0e0e0"
TEXT_DIM = "#8888aa"
GREEN = "#4ecca3"
RED = "#e94560"
YELLOW = "#f0a500"


class EGGUFApp:
    """Main EGGUF application window."""

    def __init__(self, egguf_path: str = None):
        self.root = tk.Tk()
        self.root.title("EGGUF — Extensible GGUF")
        self.root.geometry("750x560")
        self.root.configure(bg=BG_COLOR)
        self.egguf_path = egguf_path
        self.egguf = None
        self._setup_window()
        if egguf_path:
            self.root.after(100, lambda: self._show_initial_dialog(egguf_path))

    def _setup_window(self):
        self.root.minsize(550, 420)
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"+{x}+{y}")

    # ─── Initial Popup Dialog ───

    def _show_initial_dialog(self, path: str):
        """Show the initial popup: 'Do you want to add any extensions to your AI?'"""
        popup = tk.Toplevel(self.root)
        popup.title("EGGUF")
        popup.geometry("500x300")
        popup.configure(bg=BG_COLOR)
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()

        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - 250
        y = (popup.winfo_screenheight() // 2) - 150
        popup.geometry(f"+{x}+{y}")

        tk.Label(popup, text="EGGUF", font=("Segoe UI", 24, "bold"),
                 bg=BG_COLOR, fg=ACCENT2_COLOR).pack(pady=(30, 5))
        tk.Label(popup, text="Extensible GGUF", font=("Segoe UI", 10),
                 bg=BG_COLOR, fg=TEXT_DIM).pack(pady=(0, 20))

        tk.Label(popup, text="Do you want to add any extensions to your AI?",
                 font=("Segoe UI", 13), bg=BG_COLOR, fg=TEXT_COLOR,
                 wraplength=420).pack(pady=(0, 30))

        if path:
            fname = os.path.basename(path)
            tk.Label(popup, text=f"File: {fname}", font=("Segoe UI", 9),
                     bg=BG_COLOR, fg=TEXT_DIM).pack(pady=(0, 20))

        btn_frame = tk.Frame(popup, bg=BG_COLOR)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Yes", font=("Segoe UI", 12, "bold"),
                  bg=GREEN, fg="white", width=18, height=1, cursor="hand2",
                  command=lambda: self._on_yes(popup, path)).pack(side=tk.LEFT, padx=10)

        tk.Button(btn_frame, text="Just exploring / doing something else",
                  font=("Segoe UI", 10), bg=ACCENT_COLOR, fg=TEXT_COLOR,
                  width=30, height=2, cursor="hand2",
                  command=lambda: self._on_explore(popup, path)).pack(side=tk.LEFT, padx=10)

        popup.protocol("WM_DELETE_WINDOW", lambda: self._on_close_popup(popup))

    def _on_yes(self, popup, path):
        popup.destroy()
        self._browse_for_efe(path)

    def _on_explore(self, popup, path):
        popup.destroy()
        self._show_egguf_info(path)

    def _on_close_popup(self, popup):
        popup.destroy()
        if self.egguf_path:
            self._show_egguf_info(self.egguf_path)
        else:
            self.root.destroy()

    # ─── EFE Browser + Scanner ───

    def _browse_for_efe(self, egguf_path: str):
        """Open a file browser to select an EFE file."""
        efe_path = filedialog.askopenfilename(
            title="Select an EFE extension file",
            filetypes=[("EFE Files", "*.efe"), ("All Files", "*.*")],
            parent=self.root
        )
        if not efe_path:
            self._show_egguf_info(egguf_path)
            return
        self._scan_and_preview_efe(egguf_path, efe_path)

    def _scan_and_preview_efe(self, egguf_path: str, efe_path: str):
        """Scan the EFE file and show results before applying."""
        # Step 1: Scan
        scan_result = scan_efe(efe_path)

        # Create scan results window
        win = tk.Toplevel(self.root)
        win.title("EGGUF Scanner — EFE Validation")
        win.geometry("700x600")
        win.configure(bg=BG_COLOR)
        win.transient(self.root)
        win.grab_set()

        # Header
        header = tk.Frame(win, bg=PANEL_COLOR, height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        status_text = "✅ ACCEPTED" if scan_result.accepted else "❌ REJECTED"
        status_color = GREEN if scan_result.accepted else RED

        tk.Label(header, text="EGGUF Scanner", font=("Segoe UI", 14, "bold"),
                 bg=PANEL_COLOR, fg=ACCENT2_COLOR).pack(side=tk.LEFT, padx=20, pady=8)
        tk.Label(header, text=status_text, font=("Segoe UI", 12, "bold"),
                 bg=PANEL_COLOR, fg=status_color).pack(side=tk.RIGHT, padx=20, pady=8)

        # Scan summary
        summary_frame = tk.Frame(win, bg=BG_COLOR)
        summary_frame.pack(fill=tk.X, padx=15, pady=10)

        tk.Label(summary_frame, font=("Segoe UI", 9), bg=BG_COLOR, fg=TEXT_DIM,
                 text=f"File: {os.path.basename(efe_path)}  |  "
                      f"Lines: {scan_result.total_lines}  |  "
                      f"Code lines: {scan_result.code_lines}  |  "
                      f"#use: annotations: {scan_result.use_comments}").pack(anchor=tk.W)

        efe_name = ""
        if scan_result.accepted:
            from efe_format import read_efe
            efe = read_efe(efe_path, execute=False)
            efe_name = efe.metadata.get("efe", "Unknown")
            desc = efe.metadata.get("description", "")
            if efe_name:
                tk.Label(summary_frame, text=f"Package: {efe_name}", font=("Segoe UI", 11, "bold"),
                         bg=BG_COLOR, fg=TEXT_COLOR).pack(anchor=tk.W, pady=(5, 0))
            if desc:
                tk.Label(summary_frame, text=desc, font=("Segoe UI", 9),
                         bg=BG_COLOR, fg=TEXT_DIM, wraplength=650, justify=tk.LEFT).pack(anchor=tk.W, pady=(2, 0))

        # If rejected, show error
        if not scan_result.accepted:
            error_frame = tk.Frame(win, bg="#2a1a1a", bd=2, relief=tk.FLAT)
            error_frame.pack(fill=tk.X, padx=15, pady=10)

            tk.Label(error_frame, text="⚠ Scanner Rejected This File", font=("Segoe UI", 12, "bold"),
                     bg="#2a1a1a", fg=RED).pack(anchor=tk.W, padx=15, pady=(10, 5))
            tk.Label(error_frame, text=scan_result.error, font=("Segoe UI", 9),
                     bg="#2a1a1a", fg=TEXT_COLOR, wraplength=620, justify=tk.LEFT).pack(anchor=tk.W, padx=15, pady=(0, 10))

            btn_frame = tk.Frame(win, bg=BG_COLOR)
            btn_frame.pack(fill=tk.X, padx=15, pady=15)
            tk.Button(btn_frame, text="Choose Different File", font=("Segoe UI", 10),
                      bg=ACCENT_COLOR, fg=TEXT_COLOR, width=20, cursor="hand2",
                      command=lambda: [win.destroy(), self._browse_for_efe(egguf_path)]).pack(side=tk.LEFT, padx=5)
            tk.Button(btn_frame, text="Cancel", font=("Segoe UI", 10),
                      bg="#333", fg=TEXT_COLOR, width=12, cursor="hand2",
                      command=lambda: [win.destroy(), self._show_egguf_info(egguf_path)]).pack(side=tk.LEFT, padx=5)
            return

        # Accepted — show scan results (code lines + #use: annotations)
        results_label = tk.Label(win, text="Scan Results — All code lines validated:", font=("Segoe UI", 10, "bold"),
                                 bg=BG_COLOR, fg=TEXT_COLOR)
        results_label.pack(anchor=tk.W, padx=15, pady=(5, 5))

        # Scrollable results
        list_frame = tk.Frame(win, bg=BG_COLOR)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        canvas = tk.Canvas(list_frame, bg=BG_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=BG_COLOR)

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for item in scan_result.items:
            item_card = tk.Frame(scrollable, bg=PANEL_COLOR, bd=1, relief=tk.FLAT)
            item_card.pack(fill=tk.X, padx=5, pady=3)

            # Line number + type badge
            top_row = tk.Frame(item_card, bg=PANEL_COLOR)
            top_row.pack(fill=tk.X, padx=10, pady=(8, 2))

            type_tag = f"[{item.directive_name}]" if item.line_type == "directive" else "[code]"
            type_color = YELLOW if item.line_type == "directive" else ACCENT2_COLOR

            tk.Label(top_row, text=f"Line {item.line_number}", font=("Segoe UI", 8),
                     bg=PANEL_COLOR, fg=TEXT_DIM).pack(side=tk.LEFT)
            tk.Label(top_row, text=type_tag, font=("Segoe UI", 8, "bold"),
                     bg=PANEL_COLOR, fg=type_color).pack(side=tk.LEFT, padx=8)

            # Code line
            tk.Label(top_row, text=item.code_line, font=("Consolas", 9),
                     bg=PANEL_COLOR, fg=TEXT_COLOR).pack(side=tk.LEFT, fill=tk.X, expand=True)

            # #use: description
            use_row = tk.Frame(item_card, bg=PANEL_COLOR)
            use_row.pack(fill=tk.X, padx=10, pady=(0, 8))
            tk.Label(use_row, text="#use:", font=("Segoe UI", 8, "bold"),
                     bg=PANEL_COLOR, fg=GREEN).pack(side=tk.LEFT)
            tk.Label(use_row, text=item.use_description, font=("Segoe UI", 9),
                     bg=PANEL_COLOR, fg=TEXT_COLOR, wraplength=600, justify=tk.LEFT).pack(side=tk.LEFT, fill=tk.X, padx=5)

        # Execute and get configs
        from efe_format import read_efe
        efe = read_efe(efe_path, execute=True)

        # Show extracted configs
        if efe.configs:
            config_label = tk.Label(win, text=f"Extensions to apply ({len(efe.configs)}):", font=("Segoe UI", 10, "bold"),
                                    bg=BG_COLOR, fg=TEXT_COLOR)
            config_label.pack(anchor=tk.W, padx=15, pady=(10, 5))

            # Config checkboxes
            check_frame = tk.Frame(win, bg=BG_COLOR)
            check_frame.pack(fill=tk.X, padx=15, pady=5)

            check_vars = {}
            for i, config in enumerate(efe.configs):
                var = tk.BooleanVar(value=True)
                check_vars[config.get("name", f"ext_{i}")] = var

                c = tk.Frame(check_frame, bg=PANEL_COLOR, bd=1, relief=tk.FLAT)
                c.pack(fill=tk.X, padx=5, pady=2)
                cb = tk.Checkbutton(c, variable=var, bg=PANEL_COLOR, activebackground=PANEL_COLOR,
                                    selectcolor=ACCENT_COLOR, cursor="hand2")
                cb.pack(side=tk.LEFT, padx=8, pady=5)

                display = get_type_display(config.get("ext_type", "unknown"))
                tk.Label(c, text=f"{config['name']}", font=("Segoe UI", 9, "bold"),
                         bg=PANEL_COLOR, fg=TEXT_COLOR).pack(side=tk.LEFT, padx=5, pady=5)
                tk.Label(c, text=f"({display})", font=("Segoe UI", 8),
                         bg=PANEL_COLOR, fg=TEXT_DIM).pack(side=tk.LEFT, pady=5)

        # Buttons
        btn_frame = tk.Frame(win, bg=BG_COLOR)
        btn_frame.pack(fill=tk.X, padx=15, pady=15)

        tk.Button(btn_frame, text="Apply Extensions", font=("Segoe UI", 11, "bold"),
                  bg=GREEN, fg="white", width=20, cursor="hand2",
                  command=lambda: self._apply_extensions(win, egguf_path, efe_path, efe, check_vars)).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="Choose Different File", font=("Segoe UI", 9),
                  bg=ACCENT_COLOR, fg=TEXT_COLOR, width=18, cursor="hand2",
                  command=lambda: [win.destroy(), self._browse_for_efe(egguf_path)]).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="Cancel", font=("Segoe UI", 9),
                  bg="#333", fg=TEXT_COLOR, width=10, cursor="hand2",
                  command=lambda: [win.destroy(), self._show_egguf_info(egguf_path)]).pack(side=tk.RIGHT, padx=5)

    def _apply_extensions(self, win, egguf_path, efe_path, efe, check_vars):
        """Apply selected extensions from the EFE to the EGGUF."""
        selected = [name for name, var in check_vars.items() if var.get()]
        if not selected:
            messagebox.showwarning("No Selection", "Select at least one extension to apply.", parent=win)
            return

        try:
            egguf = read_egguf(egguf_path)
            applied = apply_efe_to_egguf(egguf, efe.configs, selected)
            write_egguf(egguf_path, egguf)
            self.egguf = egguf
            win.destroy()
            messagebox.showinfo(
                "Success",
                f"Applied {len(applied)} extension(s) successfully!\n\n" +
                "\n".join(f"  + {name}" for name in applied),
                parent=self.root
            )
            self._show_egguf_info(egguf_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply extensions:\n{e}", parent=win)

    # ─── EGGUF Info View ───

    def _show_egguf_info(self, egguf_path: str):
        """Show detailed info about the EGGUF file."""
        try:
            egguf = read_egguf(egguf_path)
            self.egguf = egguf
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read EGGUF file:\n{e}", parent=self.root)
            self.root.destroy()
            return

        for widget in self.root.winfo_children():
            widget.destroy()

        # Header
        header = tk.Frame(self.root, bg=PANEL_COLOR, height=70)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="EGGUF", font=("Segoe UI", 18, "bold"),
                 bg=PANEL_COLOR, fg=ACCENT2_COLOR).pack(side=tk.LEFT, padx=20, pady=10)

        model_name = egguf.metadata.get("name", "Unknown Model")
        tk.Label(header, text=model_name, font=("Segoe UI", 14),
                 bg=PANEL_COLOR, fg=TEXT_COLOR).pack(side=tk.LEFT, padx=10, pady=10)

        # Scrollable content
        canvas = tk.Canvas(self.root, bg=BG_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient=tk.VERTICAL, command=canvas.yview)
        content = tk.Frame(canvas, bg=BG_COLOR)
        content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(20, 0))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Model info
        info_section = tk.LabelFrame(content, text="Model Information", font=("Segoe UI", 11, "bold"),
                                      bg=BG_COLOR, fg=TEXT_COLOR, bd=1, relief=tk.FLAT,
                                      highlightbackground=ACCENT_COLOR, highlightthickness=1)
        info_section.pack(fill=tk.X, padx=5, pady=10, ipadx=10, ipady=10)

        info_items = [
            ("Name", egguf.metadata.get("name", "Unknown")),
            ("Architecture", egguf.metadata.get("architecture", "unknown")),
            ("Base Model", egguf.metadata.get("base_model", "unknown")),
            ("Source GGUF", egguf.metadata.get("source_gguf", "unknown")),
            ("GGUF Version", egguf.metadata.get("gguf_version", "unknown")),
            ("Created", egguf.metadata.get("created_date", "unknown")[:19].replace("T", " ")),
            ("GGUF Size", f"{egguf.gguf_size_mb:.2f} MB"),
            ("Description", egguf.metadata.get("description", "(none)") or "(none)"),
        ]

        for label, value in info_items:
            row = tk.Frame(info_section, bg=BG_COLOR)
            row.pack(fill=tk.X, padx=15, pady=2)
            tk.Label(row, text=f"{label}:", font=("Segoe UI", 9, "bold"),
                     bg=BG_COLOR, fg=TEXT_DIM, width=14, anchor=tk.W).pack(side=tk.LEFT)
            tk.Label(row, text=str(value), font=("Segoe UI", 9),
                     bg=BG_COLOR, fg=TEXT_COLOR, anchor=tk.W, wraplength=480, justify=tk.LEFT).pack(side=tk.LEFT, fill=tk.X)

        # Extensions
        ext_section = tk.LabelFrame(content, text=f"Applied Extensions ({egguf.extension_count})",
                                     font=("Segoe UI", 11, "bold"),
                                     bg=BG_COLOR, fg=TEXT_COLOR, bd=1, relief=tk.FLAT,
                                     highlightbackground=ACCENT_COLOR, highlightthickness=1)
        ext_section.pack(fill=tk.X, padx=5, pady=10, ipadx=10, ipady=10)

        if egguf.extensions:
            summaries = get_extension_summary(egguf)
            for s in summaries:
                ext_card = tk.Frame(ext_section, bg=PANEL_COLOR, bd=1, relief=tk.FLAT)
                ext_card.pack(fill=tk.X, padx=10, pady=4)

                tk.Label(ext_card, text=f"{s['name']}", font=("Segoe UI", 10, "bold"),
                         bg=PANEL_COLOR, fg=TEXT_COLOR).pack(anchor=tk.W, padx=10, pady=(8, 2))
                tk.Label(ext_card, text=f"Type: {get_type_display(s['type'])}", font=("Segoe UI", 8),
                         bg=PANEL_COLOR, fg=TEXT_DIM).pack(anchor=tk.W, padx=10)
                if s.get("description"):
                    tk.Label(ext_card, text=s["description"], font=("Segoe UI", 9),
                             bg=PANEL_COLOR, fg=TEXT_DIM, wraplength=520, justify=tk.LEFT).pack(anchor=tk.W, padx=10, pady=(2, 4))
                if "data" in s and isinstance(s["data"], dict):
                    data_str = json.dumps(s["data"], indent=2)[:300]
                    if len(json.dumps(s["data"])) > 300:
                        data_str += "..."
                    tk.Label(ext_card, text=data_str, font=("Consolas", 8),
                             bg=PANEL_COLOR, fg=GREEN, wraplength=520, justify=tk.LEFT).pack(anchor=tk.W, padx=10, pady=(2, 8))
                tk.Button(ext_card, text="Remove", font=("Segoe UI", 8),
                          bg=ACCENT2_COLOR, fg="white", width=8, cursor="hand2",
                          command=lambda n=s['name']: self._remove_extension(n)).pack(anchor=tk.E, padx=10, pady=(0, 8))
        else:
            tk.Label(ext_section, text="No extensions applied. This is a base EGGUF file.",
                     font=("Segoe UI", 10), bg=BG_COLOR, fg=TEXT_DIM).pack(padx=15, pady=15)

        # Bottom actions
        action_frame = tk.Frame(content, bg=BG_COLOR)
        action_frame.pack(fill=tk.X, padx=5, pady=15)

        tk.Button(action_frame, text="+ Add Extension (EFE)", font=("Segoe UI", 10, "bold"),
                  bg=GREEN, fg="white", width=22, height=1, cursor="hand2",
                  command=lambda: self._browse_for_efe(self.egguf_path)).pack(side=tk.LEFT, padx=5)
        tk.Button(action_frame, text="Export GGUF", font=("Segoe UI", 10),
                  bg=ACCENT_COLOR, fg=TEXT_COLOR, width=15, height=1, cursor="hand2",
                  command=self._export_gguf).pack(side=tk.LEFT, padx=5)
        tk.Button(action_frame, text="Create EFE...", font=("Segoe UI", 10),
                  bg=ACCENT_COLOR, fg=TEXT_COLOR, width=15, height=1, cursor="hand2",
                  command=self._open_efe_creator).pack(side=tk.LEFT, padx=5)
        tk.Button(action_frame, text="Close", font=("Segoe UI", 10),
                  bg="#333", fg=TEXT_COLOR, width=10, height=1, cursor="hand2",
                  command=self.root.destroy).pack(side=tk.RIGHT, padx=5)

    def _remove_extension(self, name: str):
        if not self.egguf or not self.egguf_path:
            return
        if not messagebox.askyesno("Remove Extension", f"Remove '{name}'?", parent=self.root):
            return
        self.egguf.remove_extension(name)
        write_egguf(self.egguf_path, self.egguf)
        self._show_egguf_info(self.egguf_path)

    def _export_gguf(self):
        if not self.egguf or not self.egguf.has_gguf:
            messagebox.showwarning("No GGUF", "This EGGUF file has no GGUF data to export.", parent=self.root)
            return
        path = filedialog.asksaveasfilename(title="Export GGUF", defaultextension=".gguf",
                                             filetypes=[("GGUF Files", "*.gguf"), ("All Files", "*.*")],
                                             parent=self.root)
        if not path:
            return
        try:
            with open(path, "wb") as f:
                f.write(self.egguf.gguf_data)
            messagebox.showinfo("Success", f"Exported GGUF to:\n{path}", parent=self.root)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export:\n{e}", parent=self.root)

    def _open_efe_creator(self):
        from efe_creator import EFECreator
        creator = EFECreator(self.root)

    def run(self):
        self.root.mainloop()
