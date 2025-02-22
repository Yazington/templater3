import json
import tkinter as tk
from tkinter import simpledialog, messagebox
import pystray
from PIL import Image
import logging
import threading
import os

# Set up logging
logging.basicConfig(filename='templater.log', level=logging.DEBUG)

class Template:
    def __init__(self, description):
        self.description = description

    def to_dict(self):
        return {"description": self.description}

    @classmethod
    def from_dict(cls, data):
        return cls(data["description"])

class TemplateInputDialog(simpledialog.Dialog):
    def __init__(self, parent, title, initial_text=""):
        self.initial_text = initial_text
        super().__init__(parent, title)

    def body(self, master):
        self.description = tk.Text(master, width=40, height=10)
        self.description.pack(expand=True, fill=tk.BOTH)
        self.description.insert("1.0", self.initial_text)
        self.description.bind("<Shift-Return>", self.handle_shift_enter)
        return self.description

    def handle_shift_enter(self, event):
        self.description.insert(tk.INSERT, "\n")
        return "break"  # Prevents the event from being handled further

    def apply(self):
        self.result = self.description.get("1.0", tk.END).strip()

class TemplaterApp:
    def __init__(self):
        self.templates = []
        self.ensure_app_data_dir()
        self.load_templates()
        self.setup_tray()
        self.setup_ui()

    def ensure_app_data_dir(self):
        app_dir = self.get_app_data_dir()
        print(f"Application data directory: {app_dir}")
        logging.debug(f"Application data directory: {app_dir}")

    def setup_tray(self):
        print("Setting up tray icon")
        logging.debug("Setting up tray icon")
        menu = pystray.Menu(
            pystray.MenuItem("Show Templates", self.show_window),
            pystray.MenuItem("Quit", self.quit_app)
        )
        image = Image.new('RGB', (64, 64), color = (255, 0, 0))
        self.icon = pystray.Icon("Templater", image, "Templater", menu)
        print("Tray icon setup complete")
        logging.debug("Tray icon setup complete")

    def calculate_window_position(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 400  # Adjust this value if you change the window size
        window_height = 500  # Adjust this value if you change the window size
        
        # Position the window on the right side of the screen
        x = screen_width - window_width - 20  # 20 pixels padding from the right edge
        y = screen_height - window_height - 60  # 60 pixels above the taskbar (approximate)
        
        return f"{window_width}x{window_height}+{x}+{y}"

    def setup_ui(self):
        print("Setting up UI")
        logging.debug("Setting up UI")
        self.root = tk.Tk()
        self.root.title("Templater")
        self.root.geometry(self.calculate_window_position())
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

        self.template_listbox = tk.Listbox(self.root, width=50)
        self.template_listbox.pack(pady=10, expand=True, fill=tk.BOTH)
        self.template_listbox.bind('<Double-1>', self.copy_template)

        create_button = tk.Button(self.root, text="Create Template", command=self.create_template)
        create_button.pack(pady=5)

        edit_button = tk.Button(self.root, text="Edit Template", command=self.edit_template)
        edit_button.pack(pady=5)

        search_button = tk.Button(self.root, text="Search Templates", command=self.search_templates)
        search_button.pack(pady=5)

        clear_search_button = tk.Button(self.root, text="Clear Search", command=lambda: self.update_template_list())
        clear_search_button.pack(pady=5)

        self.status_bar = tk.Label(self.root, text="", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)


        self.update_template_list()
        self.update_ui()  # Start the periodic UI updates
        print("UI setup complete")
        logging.debug("UI setup complete")

    def get_app_data_dir(self):
        app_data = os.getenv('APPDATA')
        app_dir = os.path.join(app_data, 'Templater')
        os.makedirs(app_dir, exist_ok=True)
        return app_dir

    def load_templates(self):
        print("Loading templates")
        logging.debug("Loading templates")
        file_path = os.path.join(self.get_app_data_dir(), 'templates.json')
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                self.templates = [Template.from_dict(t) for t in data]
            print(f"Loaded {len(self.templates)} templates")
            logging.debug(f"Loaded {len(self.templates)} templates")
        except FileNotFoundError:
            print("templates.json not found, starting with empty list")
            logging.warning("templates.json not found, starting with empty list")
            self.templates = []
        except json.JSONDecodeError:
            print("Error decoding templates.json, starting with empty list")
            logging.error("Error decoding templates.json, starting with empty list")
            self.templates = []

    def save_templates(self):
        print("Saving templates")
        logging.debug("Saving templates")
        file_path = os.path.join(self.get_app_data_dir(), 'templates.json')
        with open(file_path, "w") as f:
            json.dump([t.to_dict() for t in self.templates], f)
        print(f"Saved {len(self.templates)} templates")
        logging.debug(f"Saved {len(self.templates)} templates")

    def update_template_list(self, query=None):
        print("Updating template list")
        logging.debug("Updating template list")
        self.template_listbox.delete(0, tk.END)
        for template in self.templates:
            if query is None or query.lower() in template.description.lower():
                self.template_listbox.insert(tk.END, template.description[:50] + "...")
        print(f"Added {self.template_listbox.size()} templates to the listbox")
        logging.debug(f"Added {self.template_listbox.size()} templates to the listbox")

    def create_template(self):
        print("Creating new template")
        logging.debug("Creating new template")
        try:
            dialog = TemplateInputDialog(self.root, title="Create Template")
            if dialog.result:
                self.templates.append(Template(dialog.result))
                self.save_templates()
                self.update_template_list()
                print(f"Created new template")
                logging.debug(f"Created new template")
        except Exception as e:
            print(f"Error creating template: {str(e)}")
            logging.error(f"Error creating template: {str(e)}")
            messagebox.showerror("Error", f"An error occurred while creating the template: {str(e)}")

    def edit_template(self):
        print("Editing template")
        logging.debug("Editing template")
        selected = self.template_listbox.curselection()
        if selected:
            index = selected[0]
            template = self.templates[index]
            try:
                dialog = TemplateInputDialog(self.root, title="Edit Template", initial_text=template.description)
                if dialog.result:
                    template.description = dialog.result
                    self.save_templates()
                    self.update_template_list()
                    print(f"Edited template")
                    logging.debug(f"Edited template")
            except Exception as e:
                print(f"Error editing template: {str(e)}")
                logging.error(f"Error editing template: {str(e)}")
                messagebox.showerror("Error", f"An error occurred while editing the template: {str(e)}")

    def search_templates(self):
        print("Searching templates")
        logging.debug("Searching templates")
        query = simpledialog.askstring("Search Templates", "Enter search query:")
        self.update_template_list(query)

    def copy_template(self, event):
        selected = self.template_listbox.curselection()
        if selected:
            index = selected[0]
            template = self.templates[index]
            self.root.clipboard_clear()
            self.root.clipboard_append(template.description)
            self.show_status_message("Template copied to clipboard!")

    def show_status_message(self, message, duration=2000):
        self.status_bar.config(text=message, fg="green", bg="lightgrey")
        self.root.after(duration, self.clear_status_message)

    def clear_status_message(self):
        self.status_bar.config(text="", fg="black", bg=self.root.cget("bg"))

    def show_window(self):
        print("Show window called")
        logging.debug("Show window called")
        
        # Set the window position before showing it
        self.root.geometry(self.calculate_window_position())
        
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        print("Window should now be visible")
        logging.debug("Window should now be visible")

    def hide_window(self):
        print("Hiding window")
        logging.debug("Hiding window")
        self.root.withdraw()

    def update_ui(self):
        # Perform any necessary UI updates here
        self.root.update_idletasks()
        self.root.after(100, self.update_ui)  # Schedule the next update

    def run_tray_icon(self):
        self.icon.run()

    def quit_app(self):
        print("Quitting application")
        logging.debug("Quitting application")
        self.icon.stop()
        self.root.quit()
        self.root.destroy()
        import sys
        sys.exit(0)  # Force exit the application

    def run(self):
        print("Starting application")
        logging.debug("Starting application")
        self.root.withdraw()  # Hide the main window initially
        
        # Start the tray icon in a separate thread
        tray_thread = threading.Thread(target=self.run_tray_icon)
        tray_thread.daemon = True  # Set as daemon thread
        tray_thread.start()
        
        try:
            # Run the tkinter main loop
            self.root.mainloop()
        except Exception as e:
            print(f"Error in main loop: {str(e)}")
            logging.error(f"Error in main loop: {str(e)}")
        finally:
            self.quit_app()  # Ensure application quits properly

if __name__ == "__main__":
    templater = TemplaterApp()
    templater.run()
