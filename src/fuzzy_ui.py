"""
This module provides a tkinter-based user interface via a `FuzzyUI` class for the FuzzyMatcher application.

Responsible for displaying information to the user and getting user-input to serve to the controller of the application.

Key functionality:
- Fuzzy matching: Users can input strings and adjust the fuzziness threshold to find similar responses.
- Category management: Users can add, rename, or delete categories to organize matched responses effectively.
- Displaying data: Match results and categorized responses are displayed in Treeview widgets.
- File management: Users have options to start new projects, load existing projects, append data, save progress, and export results.

Main dependencies:
- tkinter: for the GUI components.
- pandas: for data manipulation.
- inspect: for cleaner error message displays.
- ctypes: for DPI awareness, ensuring the UI scales correctly on high-resolution displays.

Author: Louie Atkins-Turkish (louie@tapestryresearch.com)
"""

import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Tuple
import inspect
import ctypes
import pandas as pd

# Setup logging
logger = logging.getLogger(__name__)

# Set DPI awareness
ctypes.windll.shcore.SetProcessDpiAwareness(1)


class FuzzyUI(tk.Tk):
    """
    A tkinter user interface class for fuzzy matching and categorizing survey responses.

    Attributes:
        WINDOW_SIZE_MULTIPLIER (float): Defines the size of the main window relative to the screen size.
        is_including_missing_data (tk.BooleanVar): A variable to track the inclusion of missing data when calculating category percentages for display.
        categorization_type (tk.StringVar): A variable to track the type of categorization (Single or Multi)
            Single allows only one category per response, Multi allows multiple.

    Methods:
        display_fuzzy_match_results: Displays the results of fuzzy matching in the corresponding Treeview.
        display_category_results: Displays the categorized results in the corresponding Treeview.
        display_categories: Displays the list of categories and related metrics in the corresponding Treeview.
        set_categorization_type_label: Sets the label indicating the current categorization type.
        create_popup: Creates a general purpose popup window.
        create_rename_category_popup: Creates a popup window for renaming a category.
        create_ask_categorization_type_popup: Creates a popup window for selecting the categorization type.
        show_open_file_dialog: Displays a dialog to open a file.
        show_save_file_dialog: Displays a dialog to save a file.
        show_askyesno: Displays a Yes/No dialog.
        show_error: Displays an error message dialog.
        show_info: Displays an informational message dialog.
        show_warning: Displays a warning message dialog.
        selected_match_responses: Returns a set of selected responses from the match results Treeview.
        selected_category_responses: Returns a set of selected responses from the category results Treeview.
        selected_categories: Returns a set of selected categories from the categories Treeview.
        update_treeview_selections: Updates the selections in Treeview widgets based on specified criteria.
    """

    def __init__(self) -> None:
        """
        Sets up the main window, configures layout grids, creates frames and widgets, and binds window resize events.
        """

        logger.info("Initializing UI")
        super().__init__()

        self.title("Fuzzy Matcher")
        self.WINDOW_SIZE_MULTIPLIER = 0.8
        self.update_coords(self.winfo_screenwidth(), self.winfo_screenheight())

        # UI variables
        self.is_including_missing_data = tk.BooleanVar(value=False)
        self.categorization_type = tk.StringVar(value="Single")

        # Setup the UI
        self.initialize_window()
        self.configure_grid()
        self.configure_frames()
        self.create_widgets()
        self.position_widgets_in_frames()
        self.configure_sub_grids()
        self.configure_style()
        self.resize_treeview_columns()
        self.resize_text_wraplength()

        # Bind resizing functions to window resize
        self.bind("<Configure>", self.on_window_resize)

    ### ----------------------- Setup ----------------------- ###
    def update_coords(self, screen_width: int, screen_height: int) -> None:
        """
        Updates the main window's position and size based on the screen dimensions.

        Args:
            screen_width (int): The width of the screen. Used with self.winfo_screenwidth().
            screen_height (int): The height of the screen. Used with self.winfo_screenheight().
        """

        self.screen_width = screen_width
        self.screen_height = screen_height
        self.window_width = int(screen_width * self.WINDOW_SIZE_MULTIPLIER)
        self.window_height = int(screen_height * self.WINDOW_SIZE_MULTIPLIER)
        self.centre_x = int((screen_width - self.window_width) / 2)
        self.centre_y = int((screen_height - self.window_height) / 2)

    def initialize_window(self) -> None:
        """
        Initializes the main window with the same aspect ratio as your screen (augmented by `WINDOW_SIZE_MULTIPLIER`).
        Places it at the center of the screen.
        """

        self.geometry(f"{self.window_width}x{self.window_height}+{self.centre_x}+{self.centre_y}")
        # self.state('zoomed')

    def configure_grid(self) -> None:
        """
        Configures the main window grid layout, defining how frames will be placed and resized.
        """

        self.grid_columnconfigure(0, weight=1)  # Fuzzy matching
        self.grid_columnconfigure(1, weight=1)  # Category results
        self.grid_columnconfigure(2, weight=1)  # Categories display
        self.grid_rowconfigure(0, weight=0)  # Buttons, entries, labels, etc
        self.grid_rowconfigure(1, weight=1)  # Treeviews
        self.grid_rowconfigure(2, weight=0)  # Project management
        # Weights set such that all columns and only middle row can expand/contract

    def configure_frames(self) -> None:
        """
        Creates frames for different sections of the UI and positions them within the main window grid.
        `self.frames` is a dictionary of position names (e.g. "top_left") to frames.
        """

        self.frames = {}

        positions = [
            "top_left",
            "middle_left",
            "bottom_left",
            "top_middle",
            "middle_middle",
            "bottom_middle",
            "top_right",
            "middle_right",
            "bottom_right",
        ]

        for position in positions:
            self.frames[position] = tk.Frame(self)

        self.frames["top_left"].grid(row=0, column=0, sticky="sew", padx=10, pady=10)
        self.frames["middle_left"].grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.frames["bottom_left"].grid(row=2, column=0, sticky="new", padx=10, pady=10)
        self.frames["top_middle"].grid(row=0, column=1, sticky="sew", padx=10, pady=10)
        self.frames["middle_middle"].grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        self.frames["bottom_middle"].grid(row=2, column=1, sticky="new", padx=10, pady=10)
        self.frames["top_right"].grid(row=0, column=2, sticky="sew", padx=10, pady=10)
        self.frames["middle_right"].grid(row=1, column=2, sticky="nsew", padx=10, pady=10)
        self.frames["bottom_right"].grid(row=2, column=2, sticky="new", padx=10, pady=10)

    def create_widgets(self) -> None:
        """
        Creates various UI widgets (buttons, labels, entries, treeviews, etc.) and assigns them to frames.
        """

        # Top left frame widgets (fuzzy matching entry, slider, buttons and lable)
        self.match_string_label = tk.Label(self.frames["top_left"], text="Enter String to Match:")
        self.match_string_entry = tk.Entry(self.frames["top_left"])
        self.threshold_label = tk.Label(
            self.frames["top_left"],
            text="Set Fuzz Threshold (100 is precise, 0 is imprecise):",
        )
        self.threshold_slider = tk.Scale(
            self.frames["top_left"], from_=0, to=100, orient="horizontal", resolution=1
        )
        self.threshold_slider.set(60)  # Setting default value to 60, gets decent results
        self.match_button = tk.Button(self.frames["top_left"], text="Match")
        self.categorize_button = tk.Button(
            self.frames["top_left"], text="Categorize Selected Results"
        )
        self.categorization_label = tk.Label(
            self.frames["top_left"], text="Categorization Type: Single"
        )

        # Middle left frame widgets (fuzzy matching treeview)
        self.match_results_tree = ttk.Treeview(
            self.frames["middle_left"],
            columns=("Response", "Score", "Count"),
            show="headings",
        )
        for col in ["Response", "Score", "Count"]:
            self.match_results_tree.heading(col, text=col)
            if col != "Response":
                self.match_results_tree.column(col, anchor="center")
        self.results_scrollbar = tk.Scrollbar(
            self.frames["middle_left"],
            orient="vertical",
            command=self.match_results_tree.yview,
        )

        # Bottom left frame widgets (new project, load project, append data)
        self.new_project_button = tk.Button(self.frames["bottom_left"], text="New Project")
        self.load_button = tk.Button(self.frames["bottom_left"], text="Load Project")
        self.append_data_button = tk.Button(self.frames["bottom_left"], text="Append Data")

        # Top middle frame widgets (category results buttons and labels)
        self.display_category_results_for_selected_category_button = tk.Button(
            self.frames["top_middle"], text="Display Category Results"
        )
        self.recategorize_selected_responses_button = tk.Button(
            self.frames["top_middle"], text="Recategorize Selected Results"
        )
        self.category_results_label = tk.Label(
            self.frames["top_middle"], text="Results for Category: "
        )

        # Middle middle frame widgets (category results treeview)
        self.category_results_tree = ttk.Treeview(
            self.frames["middle_middle"], columns=("Response", "Count"), show="headings"
        )
        self.category_results_tree.heading("Response", text="Response")
        self.category_results_tree.heading("Count", text="Count")
        self.category_results_tree.column("Count", anchor="center")
        self.category_results_scrollbar = tk.Scrollbar(
            self.frames["middle_middle"],
            orient="vertical",
            command=self.category_results_tree.yview,
        )

        # Bottom middle frame widgets (None)

        # Top right frame widgets (category buttons and entry)
        self.new_category_entry = tk.Entry(self.frames["top_right"])
        self.add_category_button = tk.Button(self.frames["top_right"], text="Add Category")
        self.rename_category_button = tk.Button(self.frames["top_right"], text="Rename Category")
        self.delete_categories_button = tk.Button(self.frames["top_right"], text="Delete Category")
        self.delete_categories_button.bind()
        self.include_missing_data_checkbox = tk.Checkbutton(
            self.frames["top_right"],
            text="Base to total",
            variable=self.is_including_missing_data,
        )

        # Middle right frame widgets (categories treeview)
        self.categories_tree = ttk.Treeview(
            self.frames["middle_right"],
            columns=("Category", "Count", "Percentage"),
            show="headings",
        )
        self.categories_tree.heading("Category", text="Category")
        self.categories_tree.heading("Count", text="Count")
        self.categories_tree.heading("Percentage", text="%")
        self.categories_tree.column("Count", anchor="center")
        self.categories_tree.column("Percentage", anchor="center")
        self.categories_scrollbar = tk.Scrollbar(
            self.frames["middle_right"],
            orient="vertical",
            command=self.categories_tree.yview,
        )

        # Bottom right frame widgets (new project, load project, save project, export to csv)
        self.export_csv_button = tk.Button(self.frames["bottom_right"], text="Export to CSV")
        self.save_button = tk.Button(self.frames["bottom_right"], text="Save Project")

    def position_widgets_in_frames(self) -> None:
        """
        Positions the created widgets within their respective frames, defining layout properties.
        """

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
        self.export_csv_button.grid(row=0, column=0, sticky="e", padx=10, pady=10)
        self.save_button.grid(row=1, column=0, sticky="e", padx=10, pady=10)

    def configure_sub_grids(self) -> None:
        """
        Configures the grid layouts within individual frames, ensuring proper alignment and sizing of widgets.
        """

        # Allow all buttons and treviews to expand/contract horizontally together
        for frame in self.frames.values():
            for col in range(frame.grid_size()[0]):
                frame.grid_columnconfigure(col, weight=1)

        for frame in [
            self.frames["middle_left"],
            self.frames["middle_middle"],
            self.frames["middle_right"],
        ]:
            # Don't allow the scrollbars to expand horizontally
            last_column = frame.grid_size()[0] - 1
            frame.grid_columnconfigure(last_column, weight=0)
            # Allow the treeviews to expand vertically
            frame.grid_rowconfigure(0, weight=1)

        # Allow the bottom left frame buttons to group together on the left
        self.frames["bottom_left"].grid_columnconfigure(0, weight=0)

    def configure_style(self) -> None:
        """
        Configure global properties of the interface, such as Treeview row height and text alignment.
        """

        # Configure Treeview style for larger row height and centered column text
        style = ttk.Style(self)
        style.configure("Treeview", rowheight=25)
        style.configure("Treeview.Item", anchor="center")

    def on_window_resize(self, event) -> None:
        """
        Handles window resize events, resizing Treeview columns and text wrap lengths accordingly.

        Args:
            event: The resize event object.
        """

        self.resize_treeview_columns()
        self.resize_text_wraplength()

    def resize_text_wraplength(self) -> None:
        """
        Adjusts the wrap length of text in labels, buttons, and radio buttons when the main window is resized.
        """

        for frame in self.winfo_children():
            for widget in frame.winfo_children():
                if isinstance(widget, (tk.Label, tk.Button, tk.Radiobutton)):
                    # Extra added to make it slightly less eager to resize
                    width = widget.winfo_width() + 10
                    widget.configure(wraplength=width)

    def resize_treeview_columns(self) -> None:
        """
        Adjusts the width of Treeview columns based on the width of the Treeview widget during window resizing.

        Each column after the first one is set to 1/6th the total treeview width, and the first one takes the remaining space.
        """

        for frame in self.winfo_children():
            for widget in frame.winfo_children():
                if isinstance(widget, ttk.Treeview):
                    treeview = widget
                    treeview_width = treeview.winfo_width()

                    num_columns = len(treeview["columns"])
                    if num_columns > 1:
                        # Each column after the first one is set to 1/6th the total treeview width
                        # The first one takes the remaining space.
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
    def display_fuzzy_match_results(self, processed_results: pd.DataFrame) -> None:
        """
        Displays the results of fuzzy matching in the `match_results_tree` Treeview.

        Args:
            processed_results (pd.DataFrame): A DataFrame containing the fuzzy match results.
                Expected to contain 'response', 'score', and 'count' columns.
        """

        logger.info("Displaying fuzzy match results")
        for item in self.match_results_tree.get_children():
            self.match_results_tree.delete(item)

        for _, row in processed_results.iterrows():
            self.match_results_tree.insert(
                "", "end", values=(row["response"], row["score"], row["count"])
            )

    def display_category_results(
        self, category: str, responses_and_counts: list[Tuple[str, int]]
    ) -> None:
        """
        Displays the results for a specific category in the `category_results_tree` Treeview.

        Args:
            category (str): The name of the category for which results are being displayed.
            responses_and_counts (list[Tuple[str, int]]): A list of tuples, each containing a response and the count of occurances.
        """

        logger.info("Displaying category results")
        for item in self.category_results_tree.get_children():
            self.category_results_tree.delete(item)

        for response, count in responses_and_counts:
            self.category_results_tree.insert("", "end", values=(response, count))

        self.category_results_label.config(text=f"Results for Category: {category}")

    def display_categories(self, formatted_categories_metrics: list[Tuple[str, int, str]]) -> None:
        """
        Displays the list of categories and related metrics in the `categories_tree` Treeview.

        Args:
            formatted_categories_metrics (list[Tuple[str, int, str]]): An list of tuples, each containing the category name,
                count of responses, and the percentage as a string.
        """

        logger.info("Displaying categories and metrics")
        selected_categories = self.selected_categories()

        for item in self.categories_tree.get_children():
            self.categories_tree.delete(item)

        for category, count, percentage_str in formatted_categories_metrics:
            self.categories_tree.insert("", "end", values=(category, count, percentage_str))

        self.update_treeview_selections(selected_categories=selected_categories)

    def set_categorization_type_label(self) -> None:
        """
        Sets `categorization_type_label` to reflect the current value of the `categorization_type` variable.
        """

        logger.info("Setting categorization type label")
        chosen_type = self.categorization_type.get()
        self.categorization_label.config(text="Categorization Type: " + chosen_type)

    ### ----------------------- Popups ----------------------- ###
    def create_popup(self, title: str) -> tk.Toplevel:
        """
        Creates a general-purpose popup window.

        Args:
            title (str): The title of the popup window.

        Returns:
            tk.Toplevel: The created popup window.
        """

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

    def create_rename_category_popup(self, old_category: str) -> None:
        """
        Creates a popup window for renaming a category.

        Args:
            old_category (str): The name of the category to be renamed.
        """

        logger.info("Creating rename category popup")
        self.rename_dialog_popup = self.create_popup("Rename Category")

        # Create widgets
        self.label = tk.Label(
            self.rename_dialog_popup, text=f"Enter a new name for '{old_category}':"
        )
        self.rename_category_entry = tk.Entry(self.rename_dialog_popup)
        self.ok_button = tk.Button(self.rename_dialog_popup, text="OK")
        self.cancel_button = tk.Button(self.rename_dialog_popup, text="Cancel")

        # Add widgets to popup
        self.label.pack(pady=10)
        self.rename_category_entry.pack()
        self.ok_button.pack(side="left", padx=20)
        self.cancel_button.pack(side="right", padx=20)

        # Set focus to the string entry
        self.rename_category_entry.focus_set()

    def create_ask_categorization_type_popup(self):
        """
        Creates a popup window that allows the user to select the categorization type (Single or Multi).
        """

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
        """
        Displays a dialog to open a file.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            str: The path of the selected file.
        """

        logger.info("Displaying open file dialog")
        return filedialog.askopenfilename(*args, **kwargs)

    def show_save_file_dialog(self, *args, **kwargs) -> str:
        """
        Displays a dialog to save a file.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            str: The path where the file is to be saved.
        """

        logger.info("Displaying save file dialog")
        return filedialog.asksaveasfilename(*args, **kwargs)

    def show_askyesno(self, title: str, message: str) -> bool:
        """
        Displays a Yes/No dialog.

        Args:
            title (str): The title of the dialog.
            message (str): The message to be displayed in the dialog.

        Returns:
            bool: The answer of the user (True for 'Yes', False for 'No').
        """

        logger.info("Displaying yes/no dialog")
        return messagebox.askyesno(title, message)

    def show_error(self, message: str) -> None:
        """
        Displays an error message dialog.

        Args:
            message (str): The error message to be displayed.
        """

        logger.info("Displaying error message")
        messagebox.showerror("Error", inspect.cleandoc(message))

    def show_info(self, message: str) -> None:
        """
        Displays an informational message dialog.

        Args:
            message (str): The informational message to be displayed.
        """

        logger.info("Displaying info message")
        messagebox.showinfo("Info", inspect.cleandoc(message))

    def show_warning(self, message: str) -> None:
        """
        Displays a warning message dialog.

        Args:
            message (str): The warning message to be displayed.
        """

        logger.info("Displaying warning message")
        messagebox.showwarning("Warning", inspect.cleandoc(message))

    ### ----------------------- Treeview Selections ----------------------- ###
    def selected_match_responses(self) -> set[str]:
        """
        Returns a set of selected responses from the `match_results_tree` Treeview.

        Returns:
            set[str]: The selected responses.
        """

        return {
            self.match_results_tree.item(item_id)["values"][0]
            for item_id in self.match_results_tree.selection()
        }

    def selected_category_responses(self) -> set[str]:
        """
        Returns a set of selected responses from the `category_results_tree` Treeview.

        Returns:
            set[str]: The selected responses.
        """

        return {
            self.category_results_tree.item(item_id)["values"][0]
            for item_id in self.category_results_tree.selection()
        }

    def selected_categories(self) -> set[str]:
        """
        Returns a set of selected categories from the `categories_tree` Treeview.

        Returns:
            set[str]: The selected categories.
        """

        return {
            self.categories_tree.item(item_id)["values"][0]
            for item_id in self.categories_tree.selection()
        }

    def update_treeview_selections(
        self, selected_categories: set[str] = set(), selected_responses: set[str] = set()
    ) -> None:
        """
        Updates the selections in Treeview widgets based on specified criteria.

        Args:
            selected_categories (set[str], optional): A set of category names to be re-selected in the `categories_tree`.
            selected_responses (set[str], optional): A set of responses to be re-selected in the `match_results_tree`
                if categorization_type is 'Multi'.
        """

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
