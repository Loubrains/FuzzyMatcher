import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class ScreenCoords:
    def __init__(self):
        self.WINDOW_SIZE_MULTIPLIER = 0.8
        self.POPUP_WIDTH = "400"
        self.POPUP_HEIGHT = "200"

    def update_coords(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.window_width = int(screen_width * self.WINDOW_SIZE_MULTIPLIER)
        self.window_height = int(screen_height * self.WINDOW_SIZE_MULTIPLIER)
        self.centre_x = int((screen_width - self.window_width) / 2)
        self.centre_y = int((screen_height - self.window_height) / 2)


class FuzzyUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.screen_coords = ScreenCoords()
        self.screen_coords.update_coords(
            self.winfo_screenwidth(), self.winfo_screenheight()
        )

        self.title("Fuzzy Matcher")

        # Setup the UI
        self.initialize_window()
        self.configure_grid()
        self.configure_frames()
        self.include_missing_data_bool = tk.BooleanVar(value=True)
        self.create_widgets()
        self.bind_widgets_to_frames()
        self.configure_sub_grids()
        self.configure_style()
        self.resize_treeview_columns()
        self.resize_text_wraplength()

        # Bind resizing functions to window size change
        self.bind("<Configure>", self.on_window_resize)

    ### ----------------------- UI Setup ----------------------- ###
    def initialize_window(self):
        self.geometry(
            f"{self.screen_coords.window_width}x{self.screen_coords.window_height}+{self.screen_coords.centre_x}+{self.screen_coords.centre_y}"
        )
        # self.state('zoomed')

    def configure_grid(self):
        self.grid_columnconfigure(0, weight=1)  # Fuzzy matching
        self.grid_columnconfigure(1, weight=1)  # Category results
        self.grid_columnconfigure(2, weight=1)  # Categories display
        self.grid_rowconfigure(0, weight=0)  # Buttons, entries, labels, etc
        self.grid_rowconfigure(1, weight=1)  # Treeviews
        self.grid_rowconfigure(2, weight=0)  # Project management
        # Weights set such that all columns and only middle row can expand/contract

    def configure_frames(self):
        self.top_left_frame = tk.Frame(self)
        self.middle_left_frame = tk.Frame(self)
        self.top_middle_frame = tk.Frame(self)
        self.middle_middle_frame = tk.Frame(self)
        self.top_right_frame = tk.Frame(self)
        self.middle_right_frame = tk.Frame(self)
        self.bottom_frame = tk.Frame(self)

        self.top_left_frame.grid(row=0, column=0, sticky="sew", padx=10, pady=10)
        self.middle_left_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.top_middle_frame.grid(row=0, column=1, sticky="sew", padx=10, pady=10)
        self.middle_middle_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        self.top_right_frame.grid(row=0, column=2, sticky="sew", padx=10, pady=10)
        self.middle_right_frame.grid(row=1, column=2, sticky="nsew", padx=10, pady=10)
        self.bottom_frame.grid(
            row=2, column=0, columnspan=3, sticky="new", padx=10, pady=10
        )

    def create_widgets(self):
        # Top left frame widgets (fuzzy matching entry, slider, buttons and lable)
        self.match_string_label = tk.Label(
            self.top_left_frame, text="Enter String to Match:"
        )
        self.match_string_entry = tk.Entry(self.top_left_frame)
        self.threshold_label = tk.Label(
            self.top_left_frame,
            text="Set Fuzz Threshold (100 is precise, 0 is imprecise):",
        )
        self.threshold_slider = tk.Scale(
            self.top_left_frame, from_=0, to=100, orient="horizontal", resolution=1
        )
        self.threshold_slider.set(
            60
        )  # Setting default value to 60, gets decent results
        self.match_button = tk.Button(self.top_left_frame, text="Match")
        self.categorize_button = tk.Button(
            self.top_left_frame, text="Categorize Selected Results"
        )
        self.categorization_label = tk.Label(
            self.top_left_frame, text="Categorization Type: Single"
        )

        # Middle_left frame widgets (fuzzy matching treeview)
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

        # Top middle frame widgets (category results buttons and labels)
        self.display_category_results_for_selected_category_button = tk.Button(
            self.top_middle_frame, text="Display Category Results"
        )
        self.recategorize_selected_responses_button = tk.Button(
            self.top_middle_frame, text="Recategorize Selected Results"
        )
        self.category_results_label = tk.Label(
            self.top_middle_frame, text="Results for Category: "
        )

        # Middle Frame Widgets (category results treeview)
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

        # Top right frame widgets (category buttons and entry)
        self.new_category_entry = tk.Entry(self.top_right_frame)
        self.add_category_button = tk.Button(self.top_right_frame, text="Add Category")
        self.rename_category_button = tk.Button(
            self.top_right_frame, text="Rename Category"
        )
        self.delete_categories_button = tk.Button(
            self.top_right_frame, text="Delete Category"
        )
        self.delete_categories_button.bind()
        self.include_missing_data_checkbox = tk.Checkbutton(
            self.top_right_frame,
            text="Base to total",
            variable=self.include_missing_data_bool,
        )

        # Top middle frame widgets (categories treeview)
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

        # Bottom frame widgets (new project, load project, save project, export to csv)
        self.new_project_button = tk.Button(self.bottom_frame, text="New Project")
        self.load_button = tk.Button(self.bottom_frame, text="Load Project")
        self.append_data_button = tk.Button(self.bottom_frame, text="Append Data")
        self.save_button = tk.Button(self.bottom_frame, text="Save Project")
        self.export_csv_button = tk.Button(self.bottom_frame, text="Export to CSV")

    def bind_widgets_to_frames(self):
        # Top left frame widgets
        self.match_string_label.grid(row=0, column=0, sticky="ew", padx=5)
        self.match_string_entry.grid(row=1, column=0, sticky="ew", padx=5)
        self.threshold_label.grid(row=0, column=1, sticky="ew", padx=5)
        self.threshold_slider.grid(row=1, column=1, sticky="ew", padx=5)
        self.categorization_label.grid(row=2, column=1, sticky="ew")
        self.match_button.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        self.categorize_button.grid(row=3, column=1, sticky="ew", padx=10, pady=10)

        # Middle left frame widgets
        self.match_results_tree.grid(
            row=0, column=0, columnspan=2, sticky="nsew", padx=10, pady=10
        )
        self.results_scrollbar.grid(row=0, column=2, sticky="ns")
        self.match_results_tree.configure(yscrollcommand=self.results_scrollbar.set)

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
        self.category_results_tree.configure(
            yscrollcommand=self.category_results_scrollbar.set
        )

        # Top right frame widgets
        self.new_category_entry.grid(row=0, column=0, sticky="ew", padx=5)
        self.add_category_button.grid(row=0, column=1, sticky="ew", padx=5)
        self.rename_category_button.grid(row=0, column=2, sticky="ew", padx=5)
        self.delete_categories_button.grid(row=0, column=3, sticky="ew", padx=5)
        self.include_missing_data_checkbox.grid(row=1, column=3, sticky="e")

        # Middle right frame widgets
        self.categories_tree.grid(
            row=0, column=0, columnspan=4, sticky="nsew", padx=10, pady=10
        )
        self.categories_scrollbar.grid(row=0, column=4, sticky="ns")
        self.categories_tree.configure(yscrollcommand=self.categories_scrollbar.set)

        # Bottom frame widgets
        self.new_project_button.grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.append_data_button.grid(row=0, column=1, sticky="w", padx=10, pady=10)
        self.load_button.grid(row=1, column=0, sticky="w", padx=10, pady=10)
        self.save_button.grid(row=0, column=2, sticky="e", padx=10, pady=10)
        self.export_csv_button.grid(row=1, column=2, sticky="e", padx=10, pady=10)

    def configure_sub_grids(self):
        # Allow the treeviews to expand vertically
        self.middle_left_frame.grid_rowconfigure(0, weight=1)
        self.middle_middle_frame.grid_rowconfigure(0, weight=1)
        self.middle_right_frame.grid_rowconfigure(0, weight=1)

        # Don't allow the scrollbar to expand horizontally
        self.middle_left_frame.grid_columnconfigure(2, weight=0)
        self.middle_middle_frame.grid_columnconfigure(2, weight=0)
        self.middle_right_frame.grid_columnconfigure(4, weight=0)

        # Allow all buttons and treviews to expand/contract horizontally together
        self.top_left_frame.grid_columnconfigure(0, weight=1)
        self.top_left_frame.grid_columnconfigure(1, weight=1)
        self.middle_left_frame.grid_columnconfigure(0, weight=1)
        self.middle_left_frame.grid_columnconfigure(1, weight=1)
        self.top_middle_frame.grid_columnconfigure(0, weight=1)
        self.top_middle_frame.grid_columnconfigure(1, weight=1)
        self.middle_middle_frame.grid_columnconfigure(0, weight=1)
        self.middle_middle_frame.grid_columnconfigure(1, weight=1)
        self.top_right_frame.grid_columnconfigure(0, weight=1)
        self.top_right_frame.grid_columnconfigure(1, weight=1)
        self.top_right_frame.grid_columnconfigure(2, weight=1)
        self.top_right_frame.grid_columnconfigure(3, weight=1)
        self.middle_right_frame.grid_columnconfigure(0, weight=1)
        self.middle_right_frame.grid_columnconfigure(1, weight=1)
        self.middle_right_frame.grid_columnconfigure(2, weight=1)
        self.middle_right_frame.grid_columnconfigure(3, weight=1)

        # Allow the bottom frame to expand horizontally
        self.bottom_frame.columnconfigure(0, weight=1)
        self.bottom_frame.columnconfigure(1, weight=1)
        self.bottom_frame.columnconfigure(2, weight=1)

    def configure_style(self):
        # Configure Treeview style for larger row height and centered column text
        style = ttk.Style(self)
        style.configure("Treeview", rowheight=25)
        style.configure("Treeview.Item", anchor="center")

    def on_window_resize(self, event):
        self.resize_treeview_columns()
        self.resize_text_wraplength()

    def resize_text_wraplength(self):
        for frame in self.winfo_children():
            for widget in frame.winfo_children():
                if isinstance(widget, (tk.Label, tk.Button, tk.Radiobutton)):
                    width = (
                        widget.winfo_width() + 10
                    )  # Extra added to make it slightly less eager to resize
                    widget.configure(wraplength=width)

    def resize_treeview_columns(self):
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

                        treeview.column(
                            treeview["columns"][0], width=first_column_width
                        )
                        for col in treeview["columns"][1:]:
                            treeview.column(
                                col, minwidth=50, width=secondary_column_width
                            )
                    else:
                        # If there is only one column, it should take all the space
                        treeview.column(treeview["columns"][0], width=treeview_width)
