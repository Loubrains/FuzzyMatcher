import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import ctypes
from typing import Any
import pandas as pd
import re
import chardet
from thefuzz import fuzz
import json
from io import StringIO

# Set DPI awareness
ctypes.windll.shcore.SetProcessDpiAwareness(1)


class FileManager:
    def file_import(self, file_path):
        with open(file_path, "rb") as file:
            encoding = chardet.detect(file.read())["encoding"]  # Detect encoding
        df = pd.read_csv(file_path, encoding=encoding)
        return df


class DataProcessor:
    def preprocess_text(self, text: Any) -> str:
        text = str(text).lower()
        text = re.sub(
            r"\s+", " ", text
        )  # Convert one or more of any kind of space to single space
        text = re.sub(r"[^a-z0-9\s]", "", text)  # Remove special characters
        text = text.strip()
        return text

    def fuzzy_matching(self, df_preprocessed, match_string):
        def fuzzy_match(element):
            return fuzz.WRatio(
                match_string, str(element)
            )  # Weighted ratio of several fuzzy matching protocols

        # Get fuzzy matching scores and format result: {response: score}
        results = []
        for row in df_preprocessed.itertuples(index=True, name=None):
            for response in row[1:]:
                score = fuzzy_match(response)
                results.append({"response": response, "score": score})

        df_result = pd.DataFrame(results)

        return df_result


# Main application class
class FuzzyMatcherApp(tk.Tk):
    def __init__(self, data_processor, file_manager):
        super().__init__()
        self.data_processor = data_processor
        self.file_manager = file_manager

        self.title("Fuzzy Matcher")

        self.initialize_data_structures()  # Empty/default variables

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

        # Bind resizing functions to window size change
        self.bind("<Configure>", self.on_window_resize)

        # After setting up the UI, refresh all displays
        self.after(100, self.display_categories)
        self.after(100, self.refresh_category_results_for_currently_displayed_category)

    ### ----------------------- UI Setup ----------------------- ###
    def initialize_window(self):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_size_multiplier = 0.8
        window_width = int(screen_width * window_size_multiplier)
        window_height = int(screen_height * window_size_multiplier)
        x_position = int((screen_width - window_width) / 2)
        y_position = int((screen_height - window_height) / 2)

        self.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
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
        self.match_string_entry.bind("<Return>", lambda event: self.process_match())
        self.threshold_label = tk.Label(
            self.top_left_frame,
            text="Set Fuzz Threshold (100 is precise, 0 is imprecise):",
        )
        self.threshold_slider = tk.Scale(
            self.top_left_frame,
            from_=0,
            to=100,
            orient="horizontal",
            resolution=1,
            command=lambda val: self.display_match_results(),
        )
        self.threshold_slider.set(
            60
        )  # Setting default value to 60, gets decent results
        self.match_button = tk.Button(
            self.top_left_frame, text="Match", command=self.process_match
        )
        self.categorize_button = tk.Button(
            self.top_left_frame,
            text="Categorize Selected Results",
            command=self.categorize_response,
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
            self.top_middle_frame,
            text="Display Category Results",
            command=self.display_category_results_for_selected_category,
        )
        self.recategorize_selected_responses_button = tk.Button(
            self.top_middle_frame,
            text="Recategorize Selected Results",
            command=self.recategorize_response,
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
        self.new_category_entry.bind("<Return>", lambda event: self.create_category())
        self.add_category_button = tk.Button(
            self.top_right_frame, text="Add Category", command=self.create_category
        )
        self.rename_category_button = tk.Button(
            self.top_right_frame,
            text="Rename Category",
            command=self.ask_rename_category,
        )
        self.delete_categories_button = tk.Button(
            self.top_right_frame,
            text="Delete Category",
            command=self.ask_delete_categories,
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
        self.new_project_button = tk.Button(
            self.bottom_frame, text="New Project", command=self.start_new_project
        )
        self.load_button = tk.Button(
            self.bottom_frame, text="Load Project", command=self.load_project
        )
        self.save_button = tk.Button(
            self.bottom_frame, text="Save Project", command=self.save_project
        )
        self.export_csv_button = tk.Button(
            self.bottom_frame, text="Export to CSV", command=self.export_to_csv
        )

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

        # Middle right frame widgets
        self.categories_tree.grid(
            row=0, column=0, columnspan=4, sticky="nsew", padx=10, pady=10
        )
        self.categories_scrollbar.grid(row=0, column=4, sticky="ns")
        self.categories_tree.configure(yscrollcommand=self.categories_scrollbar.set)

        # Bottom frame widgets
        self.new_project_button.grid(row=0, column=0, sticky="w", padx=10, pady=10)
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

    ### ----------------------- UI Management ----------------------- ###
    def ask_rename_category(self):
        selected_categories = self.selected_categories()

        if len(selected_categories) != 1:
            messagebox.showinfo("Info", "Please select one category to rename.")
            return

        if "Uncategorized" in selected_categories:
            messagebox.showinfo(
                "Info", "You may not rename the 'Uncategorized' category."
            )
            return

        old_category = selected_categories.pop()

        # Create a popup to get user entry for rename
        rename_dialog_popup = tk.Toplevel(self)
        rename_dialog_popup.title("Rename Category")
        rename_dialog_popup.geometry("300x100")

        # Center the popup on the main window
        window_width = self.winfo_reqwidth()
        window_height = self.winfo_reqheight()
        position_right = int(self.winfo_screenwidth() / 2 - window_width / 2)
        position_down = int(self.winfo_screenheight() / 2 - window_height / 2)
        rename_dialog_popup.geometry("+{}+{}".format(position_right, position_down))

        # Keep the popup window on top and ensure all events are directed to this window until closed
        rename_dialog_popup.transient(self)
        rename_dialog_popup.grab_set()

        # Create widgets
        label = tk.Label(
            rename_dialog_popup, text=f"Enter a new name for '{old_category}':"
        )
        new_category_entry = tk.Entry(rename_dialog_popup)
        ok_button = tk.Button(
            rename_dialog_popup,
            text="OK",
            command=lambda: [
                self.rename_category_in_data(old_category, new_category_entry.get()),
                rename_dialog_popup.destroy(),
                self.display_categories(),
                self.refresh_category_results_for_currently_displayed_category(),
            ],
        )
        cancel_button = tk.Button(
            rename_dialog_popup, text="Cancel", command=rename_dialog_popup.destroy
        )

        # Add widgets to popup
        label.pack(pady=10)
        new_category_entry.pack()
        ok_button.pack(side="left", padx=20)
        cancel_button.pack(side="right", padx=20)

    def ask_delete_categories(self):
        selected_categories = self.selected_categories()

        if not selected_categories:
            messagebox.showinfo("Info", "Please select categories to delete.")
            return

        if "Uncategorized" in selected_categories:
            messagebox.showinfo(
                "Info", "You may not delete the category 'Uncategorized'."
            )
            return

        confirmation = messagebox.askyesno(
            "Confirmation", "Are you sure you want to delete the selected categories?"
        )
        if confirmation:
            self.delete_categories_in_data(selected_categories)
            self.display_categories()
            self.refresh_category_results_for_currently_displayed_category()

    def display_match_results(self):
        # Filter the fuzzy match results based on the threshold
        filtered_results = self.match_results[
            self.match_results["score"] >= self.threshold_slider.get()
        ]

        aggregated_results = (
            filtered_results.groupby("response")
            .agg(
                score=pd.NamedAgg(column="score", aggfunc="max"),
                count=pd.NamedAgg(column="response", aggfunc="count"),
            )
            .reset_index()
        )

        sorted_results = aggregated_results.sort_values(
            by=["score", "count"], ascending=[False, False]
        )

        for item in self.match_results_tree.get_children():
            self.match_results_tree.delete(item)

        for _, row in sorted_results.iterrows():
            self.match_results_tree.insert(
                "", "end", values=(row["response"], row["max_score"], row["count"])
            )

    def display_categories(self):
        selected_categories = self.selected_categories()

        for item in self.categories_tree.get_children():
            self.categories_tree.delete(item)

        for category, responses in self.categories_display.items():
            count = self.calculate_count(responses)
            percentage = self.calculate_percentage(responses)
            self.categories_tree.insert(
                "", "end", values=(category, count, f"{percentage:.2f}%")
            )

        self.update_treeview_selections(selected_categories=selected_categories)

    def display_category_results_for_selected_category(self):
        selected_categories = self.categories_tree.selection()

        if len(selected_categories) == 1:
            # Get the selected category as a string
            category = self.categories_tree.item(selected_categories[0])["values"][0]

            for item in self.category_results_tree.get_children():
                self.category_results_tree.delete(item)

            if category in self.categories_display:
                responses_and_counts = [
                    (response, self.response_counts[response])
                    for response in self.categories_display[category]
                ]
                sorted_responses = sorted(
                    responses_and_counts, key=lambda x: (-x[1], x[0])
                )

                for response, count in sorted_responses:
                    self.category_results_tree.insert(
                        "", "end", values=(response, count)
                    )

            self.category_results_label.config(text=f"Results for Category: {category}")

            # Assign variable for currently displayed category
            self.currently_displayed_category = category

        elif len(selected_categories) > 1:
            messagebox.showerror("Error", "Please select only one category")

        else:
            messagebox.showerror("Error", "No category selected")

    def refresh_category_results_for_currently_displayed_category(self):
        category = self.currently_displayed_category

        if not category:
            messagebox.showerror("Error", "No category results currently displayed")
            return

        for item in self.category_results_tree.get_children():
            self.category_results_tree.delete(item)

        if category in self.categories_display:
            responses_and_counts = [
                (response, self.response_counts[response])
                for response in self.categories_display[category]
            ]
            sorted_responses = sorted(responses_and_counts, key=lambda x: (-x[1], x[0]))

            for response, count in sorted_responses:
                self.category_results_tree.insert("", "end", values=(response, count))

        self.category_results_label.config(text=f"Results for Category: {category}")

    def selected_categories(self):
        return {
            self.categories_tree.item(item_id)["values"][0]
            for item_id in self.categories_tree.selection()
        }

    def selected_match_responses(self):
        return {
            self.match_results_tree.item(item_id)["values"][0]
            for item_id in self.match_results_tree.selection()
        }

    def selected_category_responses(self):
        return {
            self.category_results_tree.item(item_id)["values"][0]
            for item_id in self.category_results_tree.selection()
        }

    def update_treeview_selections(
        self, selected_categories=None, selected_responses=None
    ):
        def reselect_treeview_items(treeview, values):
            for item in treeview.get_children():
                if treeview.item(item)["values"][0] in values:
                    treeview.selection_add(item)

        # Re-select categories and if multi-categorization re-select match results
        if selected_categories is not None:
            reselect_treeview_items(self.categories_tree, selected_categories)
        if self.categorization_var.get() == "Multi" and selected_responses is not None:
            reselect_treeview_items(self.match_results_tree, selected_responses)

    ### ----------------------- Project Management ----------------------- ###
    def initialize_data_structures(self):
        # Empty variables which will be populated during new project/load project
        self.categorization_var = tk.StringVar(value="Single")
        self.df_preprocessed = pd.DataFrame()
        self.response_columns = []
        self.categorized_data = pd.DataFrame()
        self.response_counts = {}
        self.categories_display = {"Uncategorized": set()}
        self.match_results = pd.DataFrame(columns=["response", "score"])
        self.currently_displayed_category = "Uncategorized"

        # categorized_data will contain a column for each, with a 1 or 0 for each response

    def start_new_project(self):
        if self.file_import_process():
            self.populate_data_structures_new_project()
            self.display_categories()
            self.refresh_category_results_for_currently_displayed_category()
            self.display_match_results()
            self.ask_categorization_type()

    def file_import_process(self):
        is_file_selected = False
        file_path = filedialog.askopenfilename(
            title="Please select a file containing your dataset"
        )
        if file_path:
            self.df = self.file_manager.file_import(file_path)
            if self.df.empty or self.df.shape[1] < 2:
                messagebox.showerror(
                    "Error",
                    "Dataset is empty or does not contain enough columns.\nThe dataset should contain uuids in the first column, and the subsequent columns should contian responses",
                )
            else:
                is_file_selected = True
        return is_file_selected

    def populate_data_structures_new_project(self):
        self.df_preprocessed = pd.DataFrame(
            self.df.iloc[:, 1:].map(self.data_processor.preprocess_text)
        )

        self.response_columns = [col for col in self.df_preprocessed.columns]

        # categorized_data carries all response columns and all categories until export where response columns are dropped
        # In categorized_data, each category is a column, with a 1 or 0 for each response
        uuids = categorized_data = self.df.iloc[:, 0]
        self.categorized_data = pd.concat([uuids, self.df_preprocessed], axis=1)
        self.categorized_data["Uncategorized"] = 1  # Everything starts uncategorized

        # categories_display is dict of categories to the deduplicated set of all responses
        df_series = self.df_preprocessed.stack().reset_index(drop=True)
        self.categories_display = {"Uncategorized": set(df_series)}

        self.response_counts = df_series.value_counts().to_dict()

        self.match_results = pd.DataFrame(columns=["response", "score"])  # Default
        self.currently_displayed_category = "Uncategorized"  # Default

    def ask_categorization_type(self):
        # Create popup
        categorization_type_popup = tk.Toplevel(self)
        categorization_type_popup.title("Select Categorization Type")
        categorization_type_popup.geometry("400x200")

        # Center the popup on the main window
        window_width = self.winfo_reqwidth()
        window_height = self.winfo_reqheight()
        position_right = int(self.winfo_screenwidth() / 2 - window_width / 2)
        position_down = int(self.winfo_screenheight() / 2 - window_height / 2)
        categorization_type_popup.geometry(
            "+{}+{}".format(position_right, position_down)
        )

        # Keep the popup window on top and ensure all events are directed to this window until closed
        categorization_type_popup.transient(self)
        categorization_type_popup.grab_set()

        # Create buttons that assign value to self.categoriztation_type
        single_categorization_rb = tk.Radiobutton(
            categorization_type_popup,
            text="Single Categorization",
            variable=self.categorization_var,
            value="Single",
        )
        multi_categorization_rb = tk.Radiobutton(
            categorization_type_popup,
            text="Multi Categorization",
            variable=self.categorization_var,
            value="Multi",
        )
        confirm_button = tk.Button(
            categorization_type_popup,
            text="Confirm",
            command=lambda: [
                self.set_categorization_type_label(),
                categorization_type_popup.destroy(),
            ],
        )

        # Add the buttons to the window
        single_categorization_rb.pack()
        multi_categorization_rb.pack()
        confirm_button.pack()

    def set_categorization_type_label(self):
        chosen_type = self.categorization_var.get()
        self.categorization_label.config(text="Categorization Type: " + chosen_type)

    def load_project(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Project",
        )

        if file_path:
            with open(file_path, "r") as f:
                data_loaded = json.load(f)

            self.populate_data_structures_load_project(data_loaded)
            self.set_categorization_type_label()
            self.display_match_results()
            self.refresh_category_results_for_currently_displayed_category()
            self.display_categories()

            messagebox.showinfo(
                "Load Project", "Project loaded successfully from " + file_path
            )

    def populate_data_structures_load_project(self, data_loaded):
        # Convert JSON back to data / set default variable values
        self.categorization_var.set(data_loaded["categorization_var"])
        self.df_preprocessed = pd.read_json(StringIO(data_loaded["df_preprocessed"]))
        self.response_columns = data_loaded["response_columns"]
        self.categorized_data = pd.read_json(StringIO(data_loaded["categorized_data"]))
        self.response_counts = data_loaded["response_counts"]
        self.categories_display = {
            k: set(v) for k, v in data_loaded["categories_display"].items()
        }
        self.currently_displayed_category = "Uncategorized"  # Default
        self.match_results = pd.DataFrame(columns=["response", "score"])  # Default

        # In categorized_data, each category is a column, with a 1 or 0 for each response

    def save_project(self):
        data_to_save = {
            "categorization_var": self.categorization_var.get(),
            "df_preprocessed": self.df_preprocessed.to_json(),
            "response_columns": self.response_columns,
            "categorized_data": self.categorized_data.to_json(),
            "response_counts": self.response_counts,
            "categories_display": {
                k: list(v) for k, v in self.categories_display.items()
            },
        }

        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Project As",
        )

        if file_path:
            with open(file_path, "w") as f:
                json.dump(data_to_save, f)
            messagebox.showinfo(
                "Save Project", "Project saved successfully to " + file_path
            )

    def export_to_csv(self):
        # Exported data needs only UUIDs and category binaries to be able to be imported into Q.
        export_df = self.categorized_data.drop(columns=self.response_columns)

        if self.categorization_var.get() == "Multi":
            export_df.drop("Uncategorized", axis=1, inplace=True)

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save As",
        )

        if file_path:
            export_df.to_csv(file_path, index=False)
            messagebox.showinfo("Export", "Data exported successfully to " + file_path)
        else:
            messagebox.showinfo("Export", "Export cancelled")

    ### ----------------------- Main Functionality ----------------------- ###
    def process_match(self):
        if self.df_preprocessed is not None:
            self.match_results = self.data_processor.fuzzy_matching(
                self.df_preprocessed, self.match_string_entry.get()
            )
            self.display_match_results()
        else:
            messagebox.showerror("Error", "No dataset loaded")

    def categorize_response(self):
        # In categorized_data, each category is a column, with a 1 or 0 for each response

        selected_responses = self.selected_match_responses()
        selected_categories = self.selected_categories()

        if not selected_categories or not selected_responses:
            messagebox.showinfo(
                "Info", "Please select both a category and responses to categorize."
            )
            return

        # Boolean mask for rows in categorized_data corresponding to selected responses (initially all False)
        mask = pd.Series([False] * len(self.categorized_data))

        for column in self.categorized_data[self.response_columns]:
            mask |= self.categorized_data[column].isin(selected_responses)

        if self.categorization_var.get() == "Single":
            if len(selected_categories) > 1:
                messagebox.showwarning(
                    "Warning",
                    "Only one category can be selected in Single Categorization mode.",
                )
                return

            self.categorized_data.loc[mask, "Uncategorized"] = 0
            self.categories_display["Uncategorized"] -= selected_responses
            # Remove responses from match results because they can't be categorized anymore in single mode
            self.match_results = self.match_results[
                ~self.match_results["response"].isin(self.selected_match_responses())
            ]

        for category in selected_categories:
            self.categorized_data.loc[mask, category] = 1
            self.categories_display[category].update(selected_responses)

        self.display_categories()
        self.display_match_results()
        self.update_treeview_selections(
            selected_categories=selected_categories,
            selected_responses=selected_responses,
        )
        self.refresh_category_results_for_currently_displayed_category()

    def recategorize_response(self):
        # In categorized_data, each category is a column, with a 1 or 0 for each response

        selected_responses = self.selected_category_responses()
        selected_categories = self.selected_categories()

        if not selected_categories or not selected_responses:
            messagebox.showinfo(
                "Info",
                "Please select both a category and responses in the category results display to categorize.",
            )
            return

        # Boolean mask for rows in categorized_data corresponding to selected responses (initially all False)
        mask = pd.Series([False] * len(self.categorized_data))

        for column in self.categorized_data[self.response_columns]:
            mask |= self.categorized_data[column].isin(selected_responses)

        if self.categorization_var.get() == "Single" and len(selected_categories) > 1:
            messagebox.showwarning(
                "Warning",
                "Only one category can be selected in Single Categorization mode.",
            )
            return

        self.categorized_data.loc[mask, self.currently_displayed_category] = 0
        self.categories_display[self.currently_displayed_category] -= selected_responses

        for category in selected_categories:
            self.categorized_data.loc[mask, category] = 1
            self.categories_display[category].update(selected_responses)

        self.display_categories()
        self.update_treeview_selections(
            selected_categories=selected_categories,
            selected_responses=selected_responses,
        )
        self.refresh_category_results_for_currently_displayed_category()

    def create_category(self):
        new_category = self.new_category_entry.get()
        if new_category and new_category not in self.categorized_data.columns:
            self.categorized_data[new_category] = 0
            self.categories_display[new_category] = set()
            self.display_categories()

    def rename_category_in_data(self, old_category, new_category):
        if not new_category:
            messagebox.showinfo("Info", "Please enter a non-empty category name.")
            return

        if new_category in self.categories_display:
            messagebox.showinfo("Info", "A category with this name already exists.")
            return

        self.categorized_data.rename(columns={old_category: new_category}, inplace=True)
        self.categories_display[new_category] = self.categories_display.pop(
            old_category
        )

    def delete_categories_in_data(self, categories_to_delete):
        for category in categories_to_delete:
            del self.categories_display[category]
            self.categorized_data.drop(columns=category, inplace=True)

    def calculate_count(self, responses):
        return sum(self.response_counts.get(response, 0) for response in responses)

    def calculate_percentage(self, responses):
        ### UPDATE THIS TO BE PERCENTAGE OF NON 'Missing data'/NaN VALUES ###
        count = self.calculate_count(responses)
        total_responses = sum(self.response_counts.values())
        return (count / total_responses) * 100 if total_responses > 0 else 0


if __name__ == "__main__":
    data_processor = DataProcessor()
    file_manager = FileManager()
    app = FuzzyMatcherApp(data_processor, file_manager)
    app.mainloop()
