import logging
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import inspect
import ctypes
import pandas as pd

# Setup logging
logger = logging.getLogger(__name__)

# Set DPI awareness
ctypes.windll.shcore.SetProcessDpiAwareness(1)


class FuzzyUI(tk.Tk):
    def __init__(self):
        logger.info("Initializing UI")

        super().__init__()

        self.title("Fuzzy Matcher")
        self.WINDOW_SIZE_MULTIPLIER = 0.8
        self.update_coords(self.winfo_screenwidth(), self.winfo_screenheight())

        self.is_including_missing_data = tk.BooleanVar(value=False)
        self.categorization_type = tk.StringVar(value="Single")

        # Setup the UI
        self.initialize_window()
        self.configure_grid()
        self.configure_frames()
        self.create_widgets()
        self.bind_widgets_to_frames()
        self.configure_sub_grids()
        self.configure_style()
        self.resize_treeview_columns()
        self.resize_text_wraplength()

        # Bind resizing functions to window resize
        self.bind("<Configure>", self.on_window_resize)

    ### ----------------------- Setup ----------------------- ###
    def update_coords(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.window_width = int(screen_width * self.WINDOW_SIZE_MULTIPLIER)
        self.window_height = int(screen_height * self.WINDOW_SIZE_MULTIPLIER)
        self.centre_x = int((screen_width - self.window_width) / 2)
        self.centre_y = int((screen_height - self.window_height) / 2)

    def initialize_window(self) -> None:
        self.geometry(f"{self.window_width}x{self.window_height}+{self.centre_x}+{self.centre_y}")
        # self.state('zoomed')

    def configure_grid(self) -> None:
        self.grid_columnconfigure(0, weight=1)  # Fuzzy matching
        self.grid_columnconfigure(1, weight=1)  # Category results
        self.grid_columnconfigure(2, weight=1)  # Categories display
        self.grid_rowconfigure(0, weight=0)  # Buttons, entries, labels, etc
        self.grid_rowconfigure(1, weight=1)  # Treeviews
        self.grid_rowconfigure(2, weight=0)  # Project management
        # Weights set such that all columns and only middle row can expand/contract

    def configure_frames(self) -> None:
        self.top_left_frame = tk.Frame(self)
        self.middle_left_frame = tk.Frame(self)
        self.bottom_left_frame = tk.Frame(self)
        self.top_middle_frame = tk.Frame(self)
        self.middle_middle_frame = tk.Frame(self)
        self.bottom_middle_frame = tk.Frame(self)
        self.top_right_frame = tk.Frame(self)
        self.middle_right_frame = tk.Frame(self)
        self.bottom_right_frame = tk.Frame(self)

        self.top_left_frame.grid(row=0, column=0, sticky="sew", padx=10, pady=10)
        self.middle_left_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.bottom_left_frame.grid(row=2, column=0, sticky="new", padx=10, pady=10)
        self.top_middle_frame.grid(row=0, column=1, sticky="sew", padx=10, pady=10)
        self.middle_middle_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        self.bottom_middle_frame.grid(row=2, column=1, sticky="new", padx=10, pady=10)
        self.top_right_frame.grid(row=0, column=2, sticky="sew", padx=10, pady=10)
        self.middle_right_frame.grid(row=1, column=2, sticky="nsew", padx=10, pady=10)
        self.bottom_right_frame.grid(row=2, column=2, sticky="new", padx=10, pady=10)

    def create_widgets(self) -> None:
        # Top left frame widgets (fuzzy matching entry, slider, buttons and lable)
        self.match_string_label = tk.Label(self.top_left_frame, text="Enter String to Match:")
        self.match_string_entry = tk.Entry(self.top_left_frame)
        self.threshold_label = tk.Label(
            self.top_left_frame,
            text="Set Fuzz Threshold (100 is precise, 0 is imprecise):",
        )
        self.threshold_slider = tk.Scale(
            self.top_left_frame, from_=0, to=100, orient="horizontal", resolution=1
        )
        self.threshold_slider.set(60)  # Setting default value to 60, gets decent results
        self.match_button = tk.Button(self.top_left_frame, text="Match")
        self.categorize_button = tk.Button(self.top_left_frame, text="Categorize Selected Results")
        self.categorization_label = tk.Label(
            self.top_left_frame, text="Categorization Type: Single"
        )

        # Middle left frame widgets (fuzzy matching treeview)
        self.match_results_tree = ttk.Treeview(
            self.middle_left_frame,
            columns=("Response", "Score", "Count"),
            show="headings",
        )
        self.match_results_tree.heading("Response", text="Response")
        self.match_results_tree.heading("Score", text="Score")
        self.match_results_tree.heading("Count", text="Count")
        self.match_results_tree.column("Score", anchor="center")
        self.match_results_tree.column("Count", anchor="center")
        self.results_scrollbar = tk.Scrollbar(
            self.middle_left_frame,
            orient="vertical",
            command=self.match_results_tree.yview,
        )

        # Bottom left frame widgets (new project, load project, append data)
        self.new_project_button = tk.Button(self.bottom_left_frame, text="New Project")
        self.load_button = tk.Button(self.bottom_left_frame, text="Load Project")
        self.append_data_button = tk.Button(self.bottom_left_frame, text="Append Data")

        # Top middle frame widgets (category results buttons and labels)
        self.display_category_results_for_selected_category_button = tk.Button(
            self.top_middle_frame, text="Display Category Results"
        )
        self.recategorize_selected_responses_button = tk.Button(
            self.top_middle_frame, text="Recategorize Selected Results"
        )
        self.category_results_label = tk.Label(self.top_middle_frame, text="Results for Category: ")

        # Middle middle frame widgets (category results treeview)
        self.category_results_tree = ttk.Treeview(
            self.middle_middle_frame, columns=("Response", "Count"), show="headings"
        )
        self.category_results_tree.heading("Response", text="Response")
        self.category_results_tree.heading("Count", text="Count")
        self.category_results_tree.column("Count", anchor="center")
        self.category_results_scrollbar = tk.Scrollbar(
            self.middle_middle_frame,
            orient="vertical",
            command=self.category_results_tree.yview,
        )

        # Bottom middle frame widgets (None)

        # Top right frame widgets (category buttons and entry)
        self.new_category_entry = tk.Entry(self.top_right_frame)
        self.add_category_button = tk.Button(self.top_right_frame, text="Add Category")
        self.rename_category_button = tk.Button(self.top_right_frame, text="Rename Category")
        self.delete_categories_button = tk.Button(self.top_right_frame, text="Delete Category")
        self.delete_categories_button.bind()
        self.include_missing_data_checkbox = tk.Checkbutton(
            self.top_right_frame,
            text="Base to total",
            variable=self.is_including_missing_data,
        )

        # Middle right frame widgets (categories treeview)
        self.categories_tree = ttk.Treeview(
            self.middle_right_frame,
            columns=("Category", "Count", "Percentage"),
            show="headings",
        )
        self.categories_tree.heading("Category", text="Category")
        self.categories_tree.heading("Count", text="Count")
        self.categories_tree.heading("Percentage", text="%")
        self.categories_tree.column("Count", anchor="center")
        self.categories_tree.column("Percentage", anchor="center")
        self.categories_scrollbar = tk.Scrollbar(
            self.middle_right_frame,
            orient="vertical",
            command=self.categories_tree.yview,
        )

        # Bottom right frame widgets (new project, load project, save project, export to csv)
        self.save_button = tk.Button(self.bottom_right_frame, text="Save Project")
        self.export_csv_button = tk.Button(self.bottom_right_frame, text="Export to CSV")

    def bind_widgets_to_frames(self) -> None:
        # Top left frame widgets
        self.match_string_label.grid(row=0, column=0, sticky="ew", padx=5)
        self.match_string_entry.grid(row=1, column=0, sticky="ew", padx=5)
        self.threshold_label.grid(row=0, column=1, sticky="ew", padx=5)
        self.threshold_slider.grid(row=1, column=1, sticky="ew", padx=5)
        self.categorization_label.grid(row=2, column=1, sticky="ew")
        self.match_button.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        self.categorize_button.grid(row=3, column=1, sticky="ew", padx=10, pady=10)

        # Middle left frame widgets
        self.match_results_tree.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
        self.results_scrollbar.grid(row=0, column=2, sticky="ns")
        self.match_results_tree.configure(yscrollcommand=self.results_scrollbar.set)

        # Bottom left frame widgets
        self.new_project_button.grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.append_data_button.grid(row=0, column=1, sticky="w", padx=10, pady=10)
        self.load_button.grid(row=1, column=0, sticky="w", padx=10, pady=10)

        # Top middle frame widgets
        self.display_category_results_for_selected_category_button.grid(
            row=0, column=0, sticky="ew", padx=10, pady=10
        )
        self.recategorize_selected_responses_button.grid(
            row=0, column=1, sticky="ew", padx=10, pady=10
        )
        self.category_results_label.grid(
            row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=10
        )

        # Middle middle frame widgets
        self.category_results_tree.grid(
            row=0, column=0, columnspan=2, sticky="nsew", padx=10, pady=10
        )
        self.category_results_scrollbar.grid(row=0, column=2, sticky="ns")
        self.category_results_tree.configure(yscrollcommand=self.category_results_scrollbar.set)

        # Bottm middle frame widgets

        # Top right frame widgets
        self.new_category_entry.grid(row=0, column=0, sticky="ew", padx=5)
        self.add_category_button.grid(row=0, column=1, sticky="ew", padx=5)
        self.rename_category_button.grid(row=0, column=2, sticky="ew", padx=5)
        self.delete_categories_button.grid(row=0, column=3, sticky="ew", padx=5)
        self.include_missing_data_checkbox.grid(row=1, column=3, sticky="e")

        # Middle right frame widgets
        self.categories_tree.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=10, pady=10)
        self.categories_scrollbar.grid(row=0, column=4, sticky="ns")
        self.categories_tree.configure(yscrollcommand=self.categories_scrollbar.set)

        # Bottom right frame widgets
        self.save_button.grid(row=0, column=0, sticky="e", padx=10, pady=10)
        self.export_csv_button.grid(row=1, column=0, sticky="e", padx=10, pady=10)

    def configure_sub_grids(self) -> None:
        # TODO: Use loops to reduce boilerplate

        # Allow all buttons and treviews to expand/contract horizontally together
        self.top_left_frame.grid_columnconfigure(0, weight=1)
        self.top_left_frame.grid_columnconfigure(1, weight=1)
        self.middle_left_frame.grid_columnconfigure(0, weight=1)
        self.middle_left_frame.grid_columnconfigure(1, weight=1)
        self.bottom_left_frame.grid_columnconfigure(1, weight=1)
        self.top_middle_frame.grid_columnconfigure(0, weight=1)
        self.top_middle_frame.grid_columnconfigure(1, weight=1)
        self.middle_middle_frame.grid_columnconfigure(0, weight=1)
        self.middle_middle_frame.grid_columnconfigure(1, weight=1)
        self.bottom_middle_frame.grid_columnconfigure(0, weight=1)
        self.top_right_frame.grid_columnconfigure(0, weight=1)
        self.top_right_frame.grid_columnconfigure(1, weight=1)
        self.top_right_frame.grid_columnconfigure(2, weight=1)
        self.top_right_frame.grid_columnconfigure(3, weight=1)
        self.middle_right_frame.grid_columnconfigure(0, weight=1)
        self.middle_right_frame.grid_columnconfigure(1, weight=1)
        self.middle_right_frame.grid_columnconfigure(2, weight=1)
        self.middle_right_frame.grid_columnconfigure(3, weight=1)
        self.bottom_right_frame.grid_columnconfigure(0, weight=1)

        # Allow the treeviews to expand vertically
        self.middle_left_frame.grid_rowconfigure(0, weight=1)
        self.middle_middle_frame.grid_rowconfigure(0, weight=1)
        self.middle_right_frame.grid_rowconfigure(0, weight=1)

        # Allow the bottom left frame buttons to group together
        self.bottom_left_frame.grid_columnconfigure(0, weight=0)

        # Don't allow the scrollbar to expand horizontally
        self.middle_left_frame.grid_columnconfigure(2, weight=0)
        self.middle_middle_frame.grid_columnconfigure(2, weight=0)
        self.middle_right_frame.grid_columnconfigure(4, weight=0)

    def configure_style(self) -> None:
        # Configure Treeview style for larger row height and centered column text
        style = ttk.Style(self)
        style.configure("Treeview", rowheight=25)
        style.configure("Treeview.Item", anchor="center")

    def on_window_resize(self, event) -> None:
        self.resize_treeview_columns()
        self.resize_text_wraplength()

    def resize_text_wraplength(self) -> None:
        for frame in self.winfo_children():
            for widget in frame.winfo_children():
                if isinstance(widget, (tk.Label, tk.Button, tk.Radiobutton)):
                    width = (
                        widget.winfo_width() + 10
                    )  # Extra added to make it slightly less eager to resize
                    widget.configure(wraplength=width)

    def resize_treeview_columns(self) -> None:
        for frame in self.winfo_children():
            for widget in frame.winfo_children():
                if isinstance(widget, ttk.Treeview):
                    treeview = widget
                    treeview_width = treeview.winfo_width()

                    num_columns = len(treeview["columns"])
                    if num_columns > 1:
                        # Each column after the first one should be 1/6th the total treeview width,
                        # with the first one taking the remaining space.
                        secondary_column_width = treeview_width // 6
                        first_column_width = treeview_width - (
                            secondary_column_width * (num_columns - 1)
                        )

                        treeview.column(treeview["columns"][0], width=first_column_width)
                        for col in treeview["columns"][1:]:
                            treeview.column(col, minwidth=50, width=secondary_column_width)
                    else:
                        # If there is only one column, it should take all the space
                        treeview.column(treeview["columns"][0], width=treeview_width)

    ### ----------------------- Display Management ----------------------- ###
    def display_fuzzy_match_results(self, processed_results: pd.DataFrame):
        logger.info("Displaying fuzzy match results")
        for item in self.match_results_tree.get_children():
            self.match_results_tree.delete(item)

        for _, row in processed_results.iterrows():
            self.match_results_tree.insert(
                "", "end", values=(row["response"], row["score"], row["count"])
            )

    def display_category_results(self, category: str, responses_and_counts):
        logger.info("Displaying category results")
        for item in self.category_results_tree.get_children():
            self.category_results_tree.delete(item)

        for response, count in responses_and_counts:
            self.category_results_tree.insert("", "end", values=(response, count))

        self.category_results_label.config(text=f"Results for Category: {category}")

    def display_categories(self, formatted_categories_metrics):
        logger.info("Displaying categories and metrics")
        selected_categories = self.selected_categories()

        for item in self.categories_tree.get_children():
            self.categories_tree.delete(item)

        for category, count, percentage_str in formatted_categories_metrics:
            self.categories_tree.insert("", "end", values=(category, count, percentage_str))

        self.update_treeview_selections(selected_categories=selected_categories)

    def set_categorization_type_label(self):
        logger.info("Setting categorization type label")
        chosen_type = self.categorization_type.get()
        self.categorization_label.config(text="Categorization Type: " + chosen_type)

    ### ----------------------- Popups ----------------------- ###
    def create_popup(self, title: str) -> tk.Toplevel:
        popup = tk.Toplevel(self)
        popup.title(title)

        # Center the popup on the main window
        self.POPUP_WIDTH = "400"
        self.POPUP_HEIGHT = "200"
        popup.geometry(f"{self.POPUP_WIDTH}x{self.POPUP_HEIGHT}+{self.centre_x}+{self.centre_y}")

        # Keep the popup window on top
        # Ensure all events are directed to this window until closed
        # Set focus on this popup so that you can straight away press enter
        popup.transient(self)
        popup.grab_set()
        popup.focus_set()

        return popup

    def create_rename_category_popup(self, old_category):
        logger.info("Creating rename category popup")
        self.rename_dialog_popup = self.create_popup("Rename Category")

        # Create widgets
        self.label = tk.Label(
            self.rename_dialog_popup, text=f"Enter a new name for '{old_category}':"
        )
        self.new_category_entry = tk.Entry(self.rename_dialog_popup)
        self.ok_button = tk.Button(self.rename_dialog_popup, text="OK")
        self.cancel_button = tk.Button(self.rename_dialog_popup, text="Cancel")

        # Add widgets to popup
        self.label.pack(pady=10)
        self.new_category_entry.pack()
        self.ok_button.pack(side="left", padx=20)
        self.cancel_button.pack(side="right", padx=20)

        # Set focus to the string entry
        self.new_category_entry.focus_set()

    def create_ask_categorization_type_popup(self):
        logger.info("Creating categorization type popup")
        self.categorization_type_popup = self.create_popup("Select Categorization Type")

        # Create buttons that assign value to self.categoriztation_type
        single_categorization_rb = tk.Radiobutton(
            self.categorization_type_popup,
            text="Single Categorization",
            variable=self.categorization_type,
            value="Single",
        )
        multi_categorization_rb = tk.Radiobutton(
            self.categorization_type_popup,
            text="Multi Categorization",
            variable=self.categorization_type,
            value="Multi",
        )
        self.confirm_button = tk.Button(
            self.categorization_type_popup,
            text="Confirm",
        )

        # Functions to execute upon confirm/Enter
        def _on_confirm():
            self.set_categorization_type_label()
            self.categorization_type_popup.destroy()

        # Bind widgets to commands
        self.confirm_button.bind("<Button-1>", lambda event: _on_confirm())
        self.categorization_type_popup.bind("<Return>", lambda event: _on_confirm())

        # Add the buttons to the window
        single_categorization_rb.pack()
        multi_categorization_rb.pack()
        self.confirm_button.pack()

    ### ----------------------- Dialog Boxes ----------------------- ###
    def show_open_file_dialog(self, *args, **kwargs) -> str:
        logger.info("Displaying open file dialog")
        return filedialog.askopenfilename(*args, **kwargs)

    def show_save_file_dialog(self, *args, **kwargs) -> str:
        logger.info("Displaying save file dialog")
        return filedialog.asksaveasfilename(*args, **kwargs)

    def show_askyesno(self, title: str, message: str) -> bool:
        logger.info("Displaying yes/no dialog")
        return messagebox.askyesno(title, message)

    def show_error(self, message: str) -> None:
        logger.info("Displaying error message")
        messagebox.showerror("Error", inspect.cleandoc(message))

    def show_info(self, message) -> None:
        logger.info("Displaying info message")
        messagebox.showinfo("Info", inspect.cleandoc(message))

    def show_warning(self, message) -> None:
        logger.info("Displaying warning message")
        messagebox.showwarning("Warning", inspect.cleandoc(message))

    ### ----------------------- Treeview Selections ----------------------- ###
    def selected_match_responses(self) -> set[str]:
        return {
            self.match_results_tree.item(item_id)["values"][0]
            for item_id in self.match_results_tree.selection()
        }

    def selected_category_responses(self) -> set[str]:
        return {
            self.category_results_tree.item(item_id)["values"][0]
            for item_id in self.category_results_tree.selection()
        }

    def selected_categories(self) -> set[str]:
        return {
            self.categories_tree.item(item_id)["values"][0]
            for item_id in self.categories_tree.selection()
        }

    def update_treeview_selections(self, selected_categories=None, selected_responses=None):
        def reselect_treeview_items(treeview, values):
            for item in treeview.get_children():
                if treeview.item(item)["values"][0] in values:
                    treeview.selection_add(item)

        # Re-select categories and if multi-categorization re-select match results
        logger.info("Updating treeview selections")
        if selected_categories is not None:
            reselect_treeview_items(self.categories_tree, selected_categories)
        if self.categorization_type.get() == "Multi" and selected_responses is not None:
            reselect_treeview_items(self.match_results_tree, selected_responses)
