"""
EFE Creator GUI (Python-based format)

A visual tool for creating EFE (Extensions For EGGUF) files.
The EFE files are Python code with #use: annotations after/before
every code line. The creator generates the Python code automatically
from user input and includes #use: comments.

Users can:
  - Choose extension types from a dropdown
  - Configure each extension's parameters
  - Write their own #use: description for each line
  - Preview the generated Python code
  - Save as a .efe file
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
import os
from datetime import datetime

from scanner import DIRECTIVE_PREFIXES


# Extension type templates — each generates Python code lines
# Format: (display_name, [(code_template, param_fields), ...])
EXTENSION_TEMPLATES = {
    "system_prompt": {
        "display": "System Prompt / Persona",
        "lines": [
            ('system.prompt("{prompt}", "{persona_name}")', ["prompt", "persona_name"]),
        ],
    },
    "generation_params": {
        "display": "Generation Parameters",
        "lines": [
            ('params.temperature({temperature})', ["temperature"]),
            ('params.top_p({top_p})', ["top_p"]),
            ('params.top_k({top_k})', ["top_k"]),
            ('params.max_tokens({max_new_tokens})', ["max_new_tokens"]),
        ],
    },
    "response_format": {
        "display": "Response Format",
        "lines": [
            ('response.markdown()', []),
            ('response.format("{format}", "{schema}")', ["format", "schema"]),
        ],
    },
    "behavior_mod": {
        "display": "Behavior Modification",
        "lines": [
            ('behavior.always("{rule}")', ["rule"]),
            ('behavior.never("{rule}")', ["rule2"]),
        ],
    },
    "knowledge_inject": {
        "display": "Knowledge Injection",
        "lines": [
            ('knowledge.inject("{knowledge}", "{topic}", "{priority}")', ["knowledge", "topic", "priority"]),
        ],
    },
    "safety_filter": {
        "display": "Safety Filter",
        "lines": [
            ('safety.filter([{rules}], "{strictness}")', ["rules", "strictness"]),
        ],
    },
    "chat_template": {
        "display": "Chat Template",
        "lines": [
            ('chat.template("{template}", "{name}")', ["template", "name"]),
        ],
    },
    "context_window": {
        "display": "Context Window",
        "lines": [
            ('context.window({max_tokens}, "{truncate}")', ["max_tokens", "truncate"]),
        ],
    },
    "stop_tokens": {
        "display": "Stop Tokens",
        "lines": [
            ('stop.tokens([{tokens}])', ["tokens"]),
        ],
    },
    "capability_unlock": {
        "display": "Capability Unlock",
        "lines": [
            ('capability.unlock("{capability}")', ["capability"]),
        ],
    },
    "webapi_directive": {
        "display": "Web API (directive)",
        "lines": [
            ('webapi:{provider}_{api_key}', ["provider", "api_key"]),
        ],
    },
    "lora_directive": {
        "display": "LoRA Adapter (directive)",
        "lines": [
            ('lora:{path}:{scale}', ["path", "scale"]),
        ],
    },
    "custom_code": {
        "display": "Custom Python Code",
        "lines": [
            ('{code}', ["code"]),
        ],
    },
    "knowledge_database_file": {
        "display": "Knowledge Database (Upload File)",
        "lines": [
            ('knowledge.database("{file_path}", description="{description}")', ["file_path", "description"]),
        ],
    },
    "knowledge_database_inline": {
        "display": "Knowledge Database (Inline Data)",
        "lines": [
            ('knowledge.inline({inline_data}, description="{description}")', ["inline_data", "description"]),
        ],
    },
    "knowledge_search": {
        "display": "Database Search Instruction",
        "lines": [
            ('knowledge.search_if_unknown("{instruction}")', ["instruction"]),
        ],
    },
    "knowledge_embed": {
        "display": "Embed Database as Context",
        "lines": [
            ('knowledge.embed_context(max_chars={max_chars})', ["max_chars"]),
        ],
    },
}


class EFECreator:
    """GUI for creating Python-based EFE files with #use: annotations."""

    def __init__(self, parent=None):
        self.parent = parent
        self.win = tk.Toplevel(parent) if parent else tk.Tk()
        self.win.title("EFE Creator — Extensions For EGGUF")
        self.win.geometry("800x700")
        self.win.configure(bg="#1a1a2e")
        self.entries = []  # list of (ext_type, code_lines_with_use)
        self._build_ui()

    def _build_ui(self):
        BG = "#1a1a2e"
        PANEL = "#16213e"
        ACCENT = "#0f3460"
        ACCENT2 = "#e94560"
        TEXT = "#e0e0e0"
        DIM = "#8888aa"
        GREEN = "#4ecca3"

        # Header
        header = tk.Frame(self.win, bg=PANEL, height=55)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="EFE Creator", font=("Segoe UI", 16, "bold"),
                 bg=PANEL, fg=ACCENT2).pack(side=tk.LEFT, padx=20, pady=6)
        tk.Label(header, text="Python code + #use: annotations", font=("Segoe UI", 9),
                 bg=PANEL, fg=DIM).pack(side=tk.LEFT, padx=5, pady=6)

        # Package metadata
        meta_frame = tk.LabelFrame(self.win, text="Package Information", font=("Segoe UI", 10, "bold"),
                                   bg=BG, fg=TEXT, bd=1, relief=tk.FLAT,
                                   highlightbackground=ACCENT, highlightthickness=1)
        meta_frame.pack(fill=tk.X, padx=15, pady=10, ipadx=10, ipady=8)

        for i, (label, var_name) in enumerate([
            ("Package Name:", "name"),
            ("Author:", "author"),
            ("Description:", "desc"),
        ]):
            row = tk.Frame(meta_frame, bg=BG)
            row.pack(fill=tk.X, padx=10, pady=3)
            tk.Label(row, text=label, font=("Segoe UI", 9), bg=BG, fg=DIM, width=15, anchor=tk.W).pack(side=tk.LEFT)
            entry = tk.Entry(row, font=("Segoe UI", 9), bg=PANEL, fg=TEXT, width=45, bd=1, relief=tk.FLAT)
            entry.pack(side=tk.LEFT, padx=5)
            setattr(self, f"pkg_{var_name}_var", tk.StringVar())
            entry.config(textvariable=getattr(self, f"pkg_{var_name}_var"))

        # Extension builder
        builder_frame = tk.LabelFrame(self.win, text="Add Extension", font=("Segoe UI", 10, "bold"),
                                       bg=BG, fg=TEXT, bd=1, relief=tk.FLAT,
                                       highlightbackground=ACCENT, highlightthickness=1)
        builder_frame.pack(fill=tk.X, padx=15, pady=5, ipadx=10, ipady=8)

        # Type selector
        type_row = tk.Frame(builder_frame, bg=BG)
        type_row.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(type_row, text="Extension Type:", font=("Segoe UI", 9), bg=BG, fg=DIM, width=15, anchor=tk.W).pack(side=tk.LEFT)
        self.type_var = tk.StringVar()
        type_display_names = [t["display"] for t in EXTENSION_TEMPLATES.values()]
        self.type_combo = ttk.Combobox(type_row, textvariable=self.type_var,
                                       values=type_display_names, state="readonly",
                                       width=35, font=("Segoe UI", 9))
        self.type_combo.pack(side=tk.LEFT, padx=5)
        if type_display_names:
            self.type_var.set(type_display_names[0])
        self._display_to_key = {v["display"]: k for k, v in EXTENSION_TEMPLATES.items()}

        # Config fields (dynamically generated)
        self.fields_container = tk.Frame(builder_frame, bg=BG)
        self.fields_container.pack(fill=tk.X, padx=10, pady=5)
        self.field_vars = {}

        self.type_combo.bind("<<ComboboxSelected>>", lambda e: self._update_fields())

        # Add line button
        add_row = tk.Frame(builder_frame, bg=BG)
        add_row.pack(fill=tk.X, padx=10, pady=5)

        tk.Button(add_row, text="+ Add Code Line", font=("Segoe UI", 9, "bold"),
                  bg=GREEN, fg="white", width=18, cursor="hand2",
                  command=self._add_line).pack(side=tk.LEFT, padx=5)

        # Initialize fields for the first type
        self._update_fields()

        # Code lines list
        list_section = tk.LabelFrame(self.win, text="Code Lines (with #use:)", font=("Segoe UI", 10, "bold"),
                                     bg=BG, fg=TEXT, bd=1, relief=tk.FLAT,
                                     highlightbackground=ACCENT, highlightthickness=1)
        list_section.pack(fill=tk.BOTH, expand=True, padx=15, pady=10, ipadx=10, ipady=8)

        self.lines_frame = tk.Frame(list_section, bg=BG)
        self.lines_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollable
        canvas = tk.Canvas(self.lines_frame, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.lines_frame, orient=tk.VERTICAL, command=canvas.yview)
        self.lines_container = tk.Frame(canvas, bg=BG)
        self.lines_container.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.lines_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.empty_label = tk.Label(self.lines_container,
                                    text="No code lines yet.\nSelect an extension type, fill in the fields,\nand click '+ Add Code Line'.",
                                    font=("Segoe UI", 10), bg=BG, fg=DIM, justify=tk.CENTER)
        self.empty_label.pack(pady=30)

        # Bottom buttons
        btn_frame = tk.Frame(self.win, bg=BG)
        btn_frame.pack(fill=tk.X, padx=15, pady=12)

        tk.Button(btn_frame, text="Preview Code", font=("Segoe UI", 10),
                  bg=ACCENT, fg=TEXT, width=15, cursor="hand2",
                  command=self._preview_code).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="Save EFE File", font=("Segoe UI", 11, "bold"),
                  bg=GREEN, fg="white", width=18, cursor="hand2",
                  command=self._save_efe).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="Clear", font=("Segoe UI", 9),
                  bg="#333", fg=TEXT, width=10, cursor="hand2",
                  command=self._clear).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="Close", font=("Segoe UI", 9),
                  bg="#333", fg=TEXT, width=10, cursor="hand2",
                  command=self.win.destroy).pack(side=tk.RIGHT, padx=5)

    def _update_fields(self):
        """Update the configuration fields based on the selected extension type."""
        for w in self.fields_container.winfo_children():
            w.destroy()
        self.field_vars = {}

        display_name = self.type_var.get()
        if not display_name:
            return
        ext_key = self._display_to_key.get(display_name)
        if not ext_key:
            return

        template_info = EXTENSION_TEMPLATES[ext_key]
        all_fields = set()
        for code_template, field_names in template_info["lines"]:
            all_fields.update(field_names)

        # Create field entries
        for field in sorted(all_fields):
            row = tk.Frame(self.fields_container, bg="#1a1a2e")
            row.pack(fill=tk.X, padx=5, pady=3)

            display = field.replace("_", " ").title()
            tk.Label(row, text=f"{display}:", font=("Segoe UI", 9), bg="#1a1a2e",
                     fg="#8888aa", width=18, anchor=tk.W).pack(side=tk.LEFT)

            # file_path: Entry + Browse button + Preview button
            if field == "file_path":
                var = tk.StringVar()
                entry = tk.Entry(row, textvariable=var, font=("Segoe UI", 9), bg="#16213e",
                                 fg="#e0e0e0", width=35, bd=1, relief=tk.FLAT)
                entry.pack(side=tk.LEFT, padx=5)
                self.field_vars[field] = ("var", var)

                def browse_file(v=var):
                    fpath = filedialog.askopenfilename(
                        title="Select Database File",
                        filetypes=[
                            ("JSON Files", "*.json"),
                            ("CSV Files", "*.csv"),
                            ("SQLite Databases", "*.db *.sqlite *.sqlite3"),
                            ("Text Files", "*.txt *.md"),
                            ("All Files", "*.*")
                        ],
                        parent=self.win
                    )
                    if fpath:
                        v.set(fpath)

                tk.Button(row, text="Browse...", font=("Segoe UI", 8, "bold"),
                          bg="#0f3460", fg="#e0e0e0", width=8, cursor="hand2",
                          command=browse_file).pack(side=tk.LEFT, padx=2)

                def preview_file(v=var):
                    fpath = v.get().strip()
                    if not fpath or not os.path.exists(fpath):
                        messagebox.showwarning("No File", "Select a file first.", parent=self.win)
                        return
                    self._show_database_preview(fpath)

                tk.Button(row, text="Preview Data", font=("Segoe UI", 8),
                          bg="#4ecca3", fg="white", width=10, cursor="hand2",
                          command=preview_file).pack(side=tk.LEFT, padx=2)

            # inline_data: large Text widget for JSON entry + Format button
            elif field == "inline_data":
                entry = tk.Text(row, font=("Consolas", 9), bg="#16213e", fg="#e0e0e0",
                                width=45, height=8, bd=1, relief=tk.FLAT)
                entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
                entry.insert("1.0", "[\n  {\"name\": \"Example\", \"value\": 1}\n]")
                self.field_vars[field] = ("text", entry)

                # Add format/validate button below
                btn_row = tk.Frame(self.fields_container, bg="#1a1a2e")
                btn_row.pack(fill=tk.X, padx=5, pady=2)

                def validate_json(e=entry):
                    raw = e.get("1.0", tk.END).strip()
                    try:
                        parsed = json.loads(raw)
                        formatted = json.dumps(parsed, indent=2)
                        e.delete("1.0", tk.END)
                        e.insert("1.0", formatted)
                        count = len(parsed) if isinstance(parsed, list) else 1
                        messagebox.showinfo("Valid JSON",
                            f"Valid JSON! {count} record(s) found.\nData is ready to use.",
                            parent=self.win)
                    except json.JSONDecodeError as ex:
                        messagebox.showerror("Invalid JSON",
                            f"JSON syntax error:\n{ex}",
                            parent=self.win)

                tk.Button(btn_row, text="Validate JSON", font=("Segoe UI", 8, "bold"),
                          bg="#4ecca3", fg="white", width=12, cursor="hand2",
                          command=validate_json).pack(side=tk.LEFT, padx=20)

            # instruction: Text widget with default value
            elif field == "instruction":
                entry = tk.Text(row, font=("Segoe UI", 9), bg="#16213e", fg="#e0e0e0",
                                width=45, height=3, bd=1, relief=tk.FLAT)
                entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
                entry.insert("1.0", "Search through the AI/database if your knowledge doesn't contain the answer to the user")
                self.field_vars[field] = ("text", entry)

            # max_chars: Entry with default value
            elif field == "max_chars":
                var = tk.StringVar(value="8000")
                entry = tk.Entry(row, textvariable=var, font=("Segoe UI", 9), bg="#16213e",
                                 fg="#e0e0e0", width=45, bd=1, relief=tk.FLAT)
                entry.pack(side=tk.LEFT, padx=5)
                self.field_vars[field] = ("var", var)

            # Use Text widget for longer fields, Entry for shorter
            elif field in ("prompt", "knowledge", "template", "rules", "code"):
                entry = tk.Text(row, font=("Segoe UI", 9), bg="#16213e", fg="#e0e0e0",
                                width=45, height=3, bd=1, relief=tk.FLAT)
                entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
                self.field_vars[field] = ("text", entry)
            else:
                var = tk.StringVar()
                entry = tk.Entry(row, textvariable=var, font=("Segoe UI", 9), bg="#16213e",
                                 fg="#e0e0e0", width=45, bd=1, relief=tk.FLAT)
                entry.pack(side=tk.LEFT, padx=5)
                self.field_vars[field] = ("var", var)

    def _get_field_value(self, field):
        """Get the value of a configuration field."""
        if field not in self.field_vars:
            return ""
        kind, widget = self.field_vars[field]
        if kind == "text":
            return widget.get("1.0", tk.END).strip()
        else:
            return widget.get().strip()

    def _show_database_preview(self, file_path):
        """Show a preview of the selected database file in a popup window."""
        try:
            ext = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""
            preview_text = ""

            if ext == "json":
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    preview_text = f"[JSON Array] {len(data)} records\n\n"
                    for i, record in enumerate(data[:10]):
                        preview_text += f"Record {i+1}: {json.dumps(record, indent=0)}\n"
                    if len(data) > 10:
                        preview_text += f"\n... and {len(data) - 10} more records"
                elif isinstance(data, dict):
                    preview_text = f"[JSON Object]\n\n"
                    for key, value in data.items():
                        if isinstance(value, list):
                            preview_text += f"{key}: {len(value)} items\n"
                            for j, item in enumerate(value[:3]):
                                preview_text += f"  {json.dumps(item, indent=0)}\n"
                            if len(value) > 3:
                                preview_text += f"  ... and {len(value) - 3} more\n"
                        else:
                            preview_text += f"{key}: {value}\n"
                    preview_text = json.dumps(data, indent=2)[:3000]

            elif ext in ("csv", "tsv"):
                import csv
                with open(file_path, "r", encoding="utf-8", newline="") as f:
                    reader = csv.DictReader(f)
                    records = list(reader)
                preview_text = f"[CSV] {len(records)} records\n\n"
                preview_text += "Columns: " + ", ".join(reader.fieldnames or []) + "\n\n"
                for i, record in enumerate(records[:10]):
                    preview_text += f"Row {i+1}: " + " | ".join(f"{k}={v}" for k, v in record.items()) + "\n"
                if len(records) > 10:
                    preview_text += f"\n... and {len(records) - 10} more records"

            elif ext in ("db", "sqlite", "sqlite3"):
                import sqlite3
                conn = sqlite3.connect(file_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [r[0] for r in cursor.fetchall()]
                preview_text = f"[SQLite] Tables: {', '.join(tables)}\n\n"
                for table in tables:
                    cursor.execute(f"SELECT * FROM {table} LIMIT 5")
                    cols = [d[0] for d in cursor.description]
                    rows = cursor.fetchall()
                    preview_text += f"Table '{table}' ({len(cols)} columns, showing {len(rows)} rows):\n"
                    preview_text += "  Columns: " + ", ".join(cols) + "\n"
                    for row in rows:
                        preview_text += f"  {dict(zip(cols, row))}\n"
                    preview_text += "\n"
                conn.close()

            else:  # text
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                preview_text = f"[Text] {len(lines)} lines\n\n"
                for i, line in enumerate(lines[:20]):
                    preview_text += f"{i+1}: {line.rstrip()}\n"
                if len(lines) > 20:
                    preview_text += f"\n... and {len(lines) - 20} more lines"

        except Exception as e:
            preview_text = f"Error reading file:\n{e}"

        win = tk.Toplevel(self.win)
        win.title(f"Database Preview — {os.path.basename(file_path)}")
        win.geometry("700x500")
        win.configure(bg="#1a1a2e")

        header = tk.Frame(win, bg="#16213e", height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text=f"📊 {os.path.basename(file_path)}", font=("Segoe UI", 11, "bold"),
                 bg="#16213e", fg="#4ecca3").pack(side=tk.LEFT, padx=15, pady=8)

        text = tk.Text(win, font=("Consolas", 9), bg="#16213e", fg="#e0e0e0",
                       wrap=tk.WORD, bd=0, padx=15, pady=10)
        text.pack(fill=tk.BOTH, expand=True)
        text.insert("1.0", preview_text)
        text.config(state=tk.DISABLED)

        tk.Button(win, text="Close", font=("Segoe UI", 10),
                  bg="#0f3460", fg="#e0e0e0", width=12, cursor="hand2",
                  command=win.destroy).pack(pady=10)

    def _add_line(self):
        """Add a code line with #use: annotation."""
        display_name = self.type_var.get()
        ext_key = self._display_to_key.get(display_name, "")
        if not ext_key:
            return

        template_info = EXTENSION_TEMPLATES[ext_key]

        # Get field values
        values = {}
        for field in self.field_vars:
            values[field] = self._get_field_value(field)

        # Generate code lines from templates
        for code_template, field_names in template_info["lines"]:
            # Skip if required fields are empty
            required = [f for f in field_names if f not in ("persona_name", "schema", "name", "topic", "priority", "scale", "rules", "tokens", "description", "instruction", "max_chars")]
            if any(not values.get(f) for f in required):
                continue

            # Fill in the template
            try:
                # For list-type fields, format as Python list
                filled_values = {}
                for f in field_names:
                    v = values.get(f, "")
                    if f in ("rules", "tokens"):
                        # Convert multiline to Python list
                        items = [line.strip() for line in v.split("\n") if line.strip()]
                        filled_values[f] = ", ".join(f'"{item}"' for item in items)
                    elif f in ("temperature", "top_p", "top_k", "max_new_tokens", "max_tokens", "scale", "max_chars"):
                        try:
                            filled_values[f] = str(float(v)) if "." in v else str(int(v))
                        except ValueError:
                            filled_values[f] = v
                    elif f == "inline_data":
                        # Use raw JSON data, don't wrap in quotes
                        filled_values[f] = v
                    elif f == "file_path":
                        # Escape backslashes in file paths
                        filled_values[f] = v.replace('\\', '/').replace('"', '\\"')
                    else:
                        filled_values[f] = v.replace('"', '\\"')
                code = code_template.format(**filled_values)
            except (KeyError, ValueError):
                code = code_template

            # Ask for #use: description
            self._add_line_with_use(code, ext_key, display_name)

    def _add_line_with_use(self, code_line, ext_key, display_name):
        """Add a code line with its #use: annotation to the list."""
        # Create a dialog for the #use: description
        dlg = tk.Toplevel(self.win)
        dlg.title("#use: Annotation")
        dlg.geometry("550x250")
        dlg.configure(bg="#1a1a2e")
        dlg.transient(self.win)
        dlg.grab_set()

        tk.Label(dlg, text="Code Line:", font=("Segoe UI", 9, "bold"),
                 bg="#1a1a2e", fg="#8888aa").pack(anchor=tk.W, padx=15, pady=(15, 5))
        tk.Label(dlg, text=code_line, font=("Consolas", 10),
                 bg="#16213e", fg="#e0e0e0", wraplength=500, justify=tk.LEFT).pack(anchor=tk.W, padx=15, pady=(0, 10))

        tk.Label(dlg, text="#use: description (REQUIRED):", font=("Segoe UI", 9, "bold"),
                 bg="#1a1a2e", fg="#4ecca3").pack(anchor=tk.W, padx=15, pady=(5, 5))

        use_entry = tk.Text(dlg, font=("Segoe UI", 9), bg="#16213e", fg="#e0e0e0",
                            width=65, height=4, bd=1, relief=tk.FLAT)
        use_entry.pack(padx=15, pady=5, fill=tk.X)
        use_entry.focus_set()

        def on_add():
            use_text = use_entry.get("1.0", tk.END).strip()
            if not use_text:
                messagebox.showwarning("Required", "You must write a #use: description for every code line.", parent=dlg)
                return
            self.entries.append((code_line, use_text, ext_key, display_name))
            dlg.destroy()
            self._refresh_lines()

        tk.Button(dlg, text="Add Line", font=("Segoe UI", 10, "bold"),
                  bg="#4ecca3", fg="white", width=15, cursor="hand2",
                  command=on_add).pack(pady=10)
        tk.Button(dlg, text="Cancel", font=("Segoe UI", 9),
                  bg="#0f3460", fg="#e0e0e0", width=10, cursor="hand2",
                  command=dlg.destroy).pack()

    def _refresh_lines(self):
        """Refresh the code lines display."""
        for w in self.lines_container.winfo_children():
            w.destroy()

        if not self.entries:
            self.empty_label = tk.Label(self.lines_container,
                                        text="No code lines yet.\nSelect an extension type, fill in the fields,\nand click '+ Add Code Line'.",
                                        font=("Segoe UI", 10), bg="#1a1a2e", fg="#8888aa", justify=tk.CENTER)
            self.empty_label.pack(pady=30)
            return

        for i, (code, use_text, ext_key, display_name) in enumerate(self.entries):
            card = tk.Frame(self.lines_container, bg="#16213e", bd=1, relief=tk.FLAT)
            card.pack(fill=tk.X, padx=5, pady=3)

            # #use: line (green)
            use_row = tk.Frame(card, bg="#16213e")
            use_row.pack(fill=tk.X, padx=10, pady=(8, 2))
            tk.Label(use_row, text="#use:", font=("Segoe UI", 9, "bold"),
                     bg="#16213e", fg="#4ecca3").pack(side=tk.LEFT)
            tk.Label(use_row, text=use_text, font=("Segoe UI", 9),
                     bg="#16213e", fg="#e0e0e0", wraplength=600, justify=tk.LEFT).pack(side=tk.LEFT, padx=5)

            # Code line
            tk.Label(card, text=code, font=("Consolas", 9),
                     bg="#16213e", fg="#e0e0e0", wraplength=600, justify=tk.LEFT).pack(anchor=tk.W, padx=10, pady=(0, 2))

            # Type badge + remove
            badge_row = tk.Frame(card, bg="#16213e")
            badge_row.pack(fill=tk.X, padx=10, pady=(0, 8))
            tk.Label(badge_row, text=f"[{display_name}]", font=("Segoe UI", 7),
                     bg="#16213e", fg="#8888aa").pack(side=tk.LEFT)
            tk.Button(badge_row, text="Remove", font=("Segoe UI", 7),
                      bg="#e94560", fg="white", width=6, cursor="hand2",
                      command=lambda idx=i: self._remove_line(idx)).pack(side=tk.RIGHT)

    def _remove_line(self, idx):
        if 0 <= idx < len(self.entries):
            self.entries.pop(idx)
            self._refresh_lines()

    def _clear(self):
        if not self.entries:
            return
        if messagebox.askyesno("Clear All", "Remove all code lines?", parent=self.win):
            self.entries.clear()
            self._refresh_lines()

    def _generate_code(self):
        """Generate the full EFE file content as a string."""
        lines = []
        lines.append(f"# === EFE: {self.pkg_name_var.get().strip() or 'Untitled'} ===")
        lines.append(f"# === Author: {self.pkg_author_var.get().strip() or 'Unknown'} ===")
        desc = self.pkg_desc_var.get().strip()
        if desc:
            lines.append(f"# === Description: {desc} ===")
        lines.append(f"# === Created: {datetime.now().isoformat()} ===")
        lines.append("")

        # Add import line
        lines.append("#use:Import the EGGUF extension toolkit for accessing model APIs")
        lines.append("from egguf_ext import system, params, response, behavior, knowledge, safety, chat, context, tokenizer, capability, embed, stop")
        lines.append("")

        for code, use_text, ext_key, display_name in self.entries:
            lines.append(f"#use:{use_text}")
            lines.append(code)
            lines.append("")

        return "\n".join(lines)

    def _preview_code(self):
        """Show a preview of the generated EFE file."""
        if not self.entries:
            messagebox.showwarning("No Lines", "Add at least one code line first.", parent=self.win)
            return

        code = self._generate_code()

        win = tk.Toplevel(self.win)
        win.title("EFE Code Preview")
        win.geometry("700x500")
        win.configure(bg="#1a1a2e")

        text = tk.Text(win, font=("Consolas", 10), bg="#16213e", fg="#e0e0e0",
                       wrap=tk.WORD, bd=0, padx=15, pady=15)
        text.pack(fill=tk.BOTH, expand=True)
        text.insert("1.0", code)
        text.config(state=tk.DISABLED)

        tk.Button(win, text="Close", font=("Segoe UI", 10),
                  bg="#0f3460", fg="#e0e0e0", width=12, cursor="hand2",
                  command=win.destroy).pack(pady=10)

    def _save_efe(self):
        """Save the EFE file."""
        if not self.entries:
            messagebox.showwarning("No Lines", "Add at least one code line before saving.", parent=self.win)
            return

        path = filedialog.asksaveasfilename(
            title="Save EFE File", defaultextension=".efe",
            filetypes=[("EFE Files", "*.efe"), ("All Files", "*.*")],
            parent=self.win
        )
        if not path:
            return

        code = self._generate_code()

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(code)

            # Verify with scanner
            from scanner import scan_efe, format_scan_report
            result = scan_efe(path)

            if result.accepted:
                messagebox.showinfo("Saved", f"EFE file saved and scanner-approved!\n\nPath: {path}\nCode lines: {result.code_lines}", parent=self.win)
            else:
                messagebox.showwarning("Saved (Scanner Warning)", f"File saved but scanner found an issue:\n\n{result.error}\n\nThe file may not be accepted by EGGUF.", parent=self.win)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save:\n{e}", parent=self.win)
