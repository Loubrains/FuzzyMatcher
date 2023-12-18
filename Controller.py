import tkinter as tk
from tkinter import filedialog, messagebox
import ctypes
import pandas as pd
import json
from io import StringIO
from DataModel import DataModel
from FileManager import FileManager
from FuzzyUI import FuzzyUI

# Set DPI awareness
ctypes.windll.shcore.SetProcessDpiAwareness(1)


# Main application class
class Controller:
    def __init__(self, user_interface, data_model, file_manager):
        super().__init__()
        self.user_interface = user_interface
        self.data_model = data_model
        self.file_manager = file_manager

        self.initialize_data_structures()  # Empty/default variables
        self.setup_UI_bindings()

        self.user_interface.after(100, self.display_categories)
        self.user_interface.after(
            100,
            self.refresh_category_results_for_currently_displayed_category,
        )

    def setup_UI_bindings(self):
        self.user_interface.match_string_entry.bind(
            "<Return>", lambda event: self.execute_match()
        )
        self.user_interface.threshold_slider.bind(
            "<ButtonRelease-1>", lambda val: self.display_match_results()
        )
        self.user_interface.match_button.bind(
            "<Button-1>", lambda event: self.execute_match()
        )
        self.user_interface.categorize_button.bind(
            "<Button-1>", lambda event: self.categorize_selected_responses()
        )
        self.user_interface.display_category_results_for_selected_category_button.bind(
            "<Button-1>",
            lambda event: self.display_category_results_for_selected_category(),
        )
        self.user_interface.recategorize_selected_responses_button.bind(
            "<Button-1>", lambda event: self.recategorize_selected_responses()
        )
        self.user_interface.new_category_entry.bind(
            "<Return>", lambda event: self.create_category()
        )
        self.user_interface.add_category_button.bind(
            "<Button-1>", lambda event: self.create_category()
        )
        self.user_interface.rename_category_button.bind(
            "<Button-1>", lambda event: self.ask_rename_category()
        )
        self.user_interface.delete_categories_button.bind(
            "<Button-1>", lambda event: self.ask_delete_categories()
        )
        self.user_interface.include_missing_data_bool.trace_add(
            "write", lambda *args: self.display_categories()
        )  # Using trace_add() to make sure it calls the command only after setting the bool value.
        self.user_interface.new_project_button.bind(
            "<Button-1>", lambda event: self.start_new_project()
        )
        self.user_interface.load_button.bind(
            "<Button-1>", lambda event: self.load_project()
        )
        self.user_interface.append_data_button.bind(
            "<Button-1>", lambda event: self.append_data_behaviour()
        )
        self.user_interface.save_button.bind(
            "<Button-1>", lambda event: self.save_project()
        )
        self.user_interface.export_csv_button.bind(
            "<Button-1>", lambda event: self.export_to_csv()
        )

    def run(self):
        self.user_interface.mainloop()

    ### ----------------------- UI Management ----------------------- ###
    def ask_rename_category(self):
        selected_categories = self.selected_categories()

        if len(selected_categories) != 1:
            messagebox.showinfo("Info", "Please select one category to rename.")
            return

        if (
            "Uncategorized" in selected_categories
            or "Missing data" in selected_categories
        ):
            formatted_categories = ", ".join(selected_categories)
            messagebox.showinfo(
                "Info",
                f"You may not rename the category/categories {formatted_categories}.",
            )
            return

        old_category = selected_categories.pop()

        # Create a popup to get user entry for rename
        rename_dialog_popup = tk.Toplevel(self.user_interface)
        rename_dialog_popup.title("Rename Category")

        # Center the popup on the main window

        rename_dialog_popup.geometry(
            f"{self.user_interface.screen_coords.POPUP_WIDTH}x{self.user_interface.screen_coords.POPUP_HEIGHT}+{self.user_interface.screen_coords.centre_x}+{self.user_interface.screen_coords.centre_y}"
        )

        # Keep the popup window on top and ensure all events are directed to this window until closed
        rename_dialog_popup.transient(self.user_interface)
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

        if (
            "Uncategorized" in selected_categories
            or "Missing data" in selected_categories
        ):
            formatted_categories = ", ".join(selected_categories)
            messagebox.showinfo(
                "Info",
                f"You may not delete the category/categories {formatted_categories}.",
            )
            return

        if messagebox.askyesno(
            "Confirmation", "Are you sure you want to delete the selected categories?"
        ):
            self.delete_categories_in_data(selected_categories)
            self.display_categories()
            self.refresh_category_results_for_currently_displayed_category()

    def display_match_results(self):
        # Filter the fuzzy match results based on the threshold
        filtered_results = self.match_results[
            self.match_results["score"] >= self.user_interface.threshold_slider.get()
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

        for item in self.user_interface.match_results_tree.get_children():
            self.user_interface.match_results_tree.delete(item)

        for _, row in sorted_results.iterrows():
            self.user_interface.match_results_tree.insert(
                "", "end", values=(row["response"], row["score"], row["count"])
            )

    def display_categories(self):
        selected_categories = self.selected_categories()
        include_missing_data_bool = self.user_interface.include_missing_data_bool.get()

        for item in self.user_interface.categories_tree.get_children():
            self.user_interface.categories_tree.delete(item)

        for category, responses in self.categorized_dict.items():
            count = self.calculate_count(responses)
            if not include_missing_data_bool and category == "Missing data":
                percentage_str = ""
            else:
                percentage = self.calculate_percentage(
                    responses, include_missing_data_bool
                )
                percentage_str = f"{percentage:.2f}%"
            self.user_interface.categories_tree.insert(
                "", "end", values=(category, count, percentage_str)
            )

        self.update_treeview_selections(selected_categories=selected_categories)

    def display_category_results(self, category):
        for item in self.user_interface.category_results_tree.get_children():
            self.user_interface.category_results_tree.delete(item)

        if category in self.categorized_dict:
            responses_and_counts = [
                (response, self.response_counts.get(response, 0))
                for response in self.categorized_dict[category]
            ]
            sorted_responses = sorted(
                responses_and_counts, key=lambda x: (pd.isna(x[0]), -x[1], x[0])
            )  # Sort first by score and then alphabetically

            for response, count in sorted_responses:
                self.user_interface.category_results_tree.insert(
                    "", "end", values=(response, count)
                )

        self.user_interface.category_results_label.config(
            text=f"Results for Category: {category}"
        )

    def display_category_results_for_selected_category(self):
        selected_categories = self.user_interface.categories_tree.selection()

        if len(selected_categories) == 1:
            # Get the selected category as a string
            category = self.user_interface.categories_tree.item(selected_categories[0])[
                "values"
            ][0]

            self.display_category_results(category)

            # Assign variable for currently displayed category
            self.currently_displayed_category = (
                category  # This is now the currently displayed category
            )

        elif len(selected_categories) > 1:
            messagebox.showerror("Error", "Please select only one category")

        else:
            messagebox.showerror("Error", "No category selected")

    def refresh_category_results_for_currently_displayed_category(self):
        category = self.currently_displayed_category

        if not category:
            messagebox.showerror("Error", "No category results currently displayed")
            return

        self.display_category_results(category)

    def selected_categories(self):
        return {
            self.user_interface.categories_tree.item(item_id)["values"][0]
            for item_id in self.user_interface.categories_tree.selection()
        }

    def selected_match_responses(self):
        return {
            self.user_interface.match_results_tree.item(item_id)["values"][0]
            for item_id in self.user_interface.match_results_tree.selection()
        }

    def selected_category_responses(self):
        return {
            self.user_interface.category_results_tree.item(item_id)["values"][0]
            for item_id in self.user_interface.category_results_tree.selection()
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
            reselect_treeview_items(
                self.user_interface.categories_tree, selected_categories
            )
        if self.categorization_var.get() == "Multi" and selected_responses is not None:
            reselect_treeview_items(
                self.user_interface.match_results_tree, selected_responses
            )

    ### ----------------------- Project Management ----------------------- ###
    def initialize_data_structures(self):
        # Empty variables which will be populated during new project/load project
        self.categorization_var = tk.StringVar(value="Single")
        self.df_preprocessed = pd.DataFrame()
        self.response_columns = []
        self.categorized_data = pd.DataFrame()
        self.response_counts = {}
        self.categorized_dict = {
            "Uncategorized": set(),
            "Missing data": {"nan", "missing data"},
        }
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
        if file_path := filedialog.askopenfilename(
            title="Please select a file containing your dataset"
        ):
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
            self.df.iloc[:, 1:].map(
                self.data_model.preprocess_text  # , na_action="ignore"
            )  # type: ignore
        )

        # categories_display is dict of categories to the deduplicated set of all responses
        df_series = self.df_preprocessed.stack().reset_index(drop=True)
        self.categorized_dict = {
            "Uncategorized": set(df_series) - {"nan", "missing data"},
            "Missing data": {"nan", "missing data"},  # default
        }

        self.response_counts = df_series.value_counts().to_dict()

        uuids = self.df.iloc[:, 0]
        self.response_columns = list(self.df_preprocessed.columns)

        # categorized_data carries all response columns and all categories until export where response columns are dropped
        # In categorized_data, each category is a column, with a 1 or 0 for each response
        self.categorized_data = pd.concat([uuids, self.df_preprocessed], axis=1)
        self.categorized_data["Uncategorized"] = 1  # Everything starts uncategorized
        self.categorized_data["Missing data"] = 0
        self.categorize_missing_data()

        self.currently_displayed_category = "Uncategorized"  # Default (this must come before calling self.categorize_responses below)

        self.match_results = pd.DataFrame(columns=["response", "score"])  # Default
        self.user_interface.include_missing_data_bool.set(False)

    def ask_categorization_type(self):
        # Create popup
        categorization_type_popup = tk.Toplevel(self.user_interface)
        categorization_type_popup.title("Select Categorization Type")

        # Center the popup on the main window

        categorization_type_popup.geometry(
            f"{self.user_interface.screen_coords.POPUP_WIDTH}x{self.user_interface.screen_coords.POPUP_HEIGHT}+{self.user_interface.screen_coords.centre_x}+{self.user_interface.screen_coords.centre_y}"
        )

        # Keep the popup window on top and ensure all events are directed to this window until closed
        categorization_type_popup.transient(self.user_interface)
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
        self.user_interface.categorization_label.config(
            text="Categorization Type: " + chosen_type
        )

    def load_project(self):
        if file_path := filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Project",
        ):
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
        self.categorized_dict = {
            k: set(v) for k, v in data_loaded["categories_display"].items()
        }
        self.currently_displayed_category = "Uncategorized"  # Default
        self.match_results = pd.DataFrame(columns=["response", "score"])  # Default
        self.user_interface.include_missing_data_bool.set(
            data_loaded["include_missing_data_bool"]
        )

        # In categorized_data, each category is a column, with a 1 or 0 for each response

    def append_data_behaviour(self):
        if self.file_import_append_data():
            self.populate_data_structures_append_data()  # Reinitialize with new data
            self.display_categories()
            self.refresh_category_results_for_currently_displayed_category()
            self.display_match_results()
            messagebox.showinfo("Success", "Data appended successfully")

    def file_import_append_data(self):
        if file_path := filedialog.askopenfilename(title="Select file to append"):
            try:
                new_df = self.file_manager.file_import(file_path)
                if new_df.empty or new_df.shape[1] != self.df.shape[1]:
                    messagebox.showerror(
                        "Error",
                        "Dataset is empty or does not have the same shape as the current dataset.\nThe dataset should contain uuids in the first column, and the subsequent columns should contain the same number of response columns.",
                    )
                    return False
                self.df = pd.concat([self.df, new_df], ignore_index=True)
                return True
            except Exception as e:
                messagebox.showerror("Error", f"Failed to append data: {e}")
        return False

    def populate_data_structures_append_data(self):
        old_data_size = len(self.df_preprocessed)
        new_df_preprocessed = pd.DataFrame(
            self.df.iloc[old_data_size:, 1:].map(self.data_model.preprocess_text)  # type: ignore
        )
        self.df_preprocessed = pd.concat([self.df_preprocessed, new_df_preprocessed])

        # categories_display is dict of categories to the deduplicated set of all responses
        new_df_series = new_df_preprocessed.stack().reset_index(drop=True)
        df_series = self.df_preprocessed.stack().reset_index(drop=True)
        self.response_counts = df_series.value_counts().to_dict()
        self.categorized_dict["Uncategorized"].update(
            set(new_df_series) - {"nan", "missing data"}
        )

        new_categorized_data = pd.concat(
            [self.df.iloc[old_data_size:, 0], new_df_preprocessed], axis=1
        )
        self.categorized_data = pd.concat(
            [self.categorized_data, new_categorized_data], axis=0
        )

        self.categorized_data["Uncategorized"].iloc[
            old_data_size:
        ] = 1  # Everything starts uncategorized
        self.categorized_data["Missing data"].iloc[old_data_size:] = 0
        self.categorize_missing_data()

        self.currently_displayed_category = "Uncategorized"  # Default (this must come before calling self.categorize_responses below)
        self.match_results = pd.DataFrame(columns=["response", "score"])  # Default

    def save_project(self):
        # Pandas NAType is not JSON serializable
        def none_handler(o):
            if pd.isna(o):
                return None

        data_to_save = {
            "categorization_var": self.categorization_var.get(),
            "df_preprocessed": self.df_preprocessed.to_json(),
            "response_columns": self.response_columns,
            "categorized_data": self.categorized_data.to_json(),
            "response_counts": self.response_counts,
            "categories_display": {
                k: list(v) for k, v in self.categorized_dict.items()
            },
            "include_missing_data_bool": self.user_interface.include_missing_data_bool.get(),
        }

        if file_path := filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Project As",
        ):
            with open(file_path, "w") as f:
                json.dump(data_to_save, f, default=none_handler)
            messagebox.showinfo(
                "Save Project", "Project saved successfully to " + file_path
            )

    def export_to_csv(self):
        # Exported data needs only UUIDs and category binaries to be able to be imported into Q.
        export_df = self.categorized_data.drop(columns=self.response_columns)

        if self.categorization_var.get() == "Multi":
            export_df.drop("Uncategorized", axis=1, inplace=True)

        if file_path := filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save As",
        ):
            export_df.to_csv(file_path, index=False)
            messagebox.showinfo("Export", "Data exported successfully to " + file_path)
        else:
            messagebox.showinfo("Export", "Export cancelled")

    ### ----------------------- Main Functionality ----------------------- ###
    def execute_match(self):
        if self.categorized_data.empty:
            messagebox.showerror("Error", "No dataset loaded")
            return

        if self.categorized_data is not None:
            ### The below doesn't work because I've set this all up very badly and it would stop you from seeing any response in the entire row if one response in that row is categorized ###
            # data_to_match = self.categorized_data[
            #     self.categorized_data["Uncategorized"] == 1
            # ]
            # data_to_match = data_to_match[self.response_columns]
            uncategorized_responses = self.categorized_dict["Uncategorized"]
            uncategorized_df = self.df_preprocessed[
                self.df_preprocessed.isin(uncategorized_responses)
            ].dropna(how="all")

            # Perform fuzzy matching on these uncategorized responses
            self.match_results = self.data_model.fuzzy_matching(
                uncategorized_df, self.user_interface.match_string_entry.get()
            )

            self.display_match_results()

    def categorize_missing_data(self):
        def is_missing(value):
            return (
                pd.isna(value)
                or value is None
                or value == "missing data"
                or value == "nan"
            )

        all_missing_mask = self.df_preprocessed.map(is_missing).all(  # type: ignore
            axis=1
        )  # Boolean mask where each row is True if all elements are missing
        self.categorized_data.loc[all_missing_mask, "Missing data"] = 1
        self.categorized_data.loc[all_missing_mask, "Uncategorized"] = 0

    def categorize_selected_responses(self):
        responses, categories = (
            self.selected_match_responses(),
            self.selected_categories(),
        )

        if not categories or not responses:
            messagebox.showinfo(
                "Info", "Please select both a category and responses to categorize."
            )
            return

        if "Missing data" in categories:
            messagebox.showinfo(
                "Info", 'You cannot categorize values into "Missing data".'
            )
            return

        if "nan" in responses or "missing data" in responses:
            messagebox.showwarning(
                "Warning",
                "You cannot recategorize 'NaN' or 'Missing data' values",
            )

        if self.categorization_var.get() == "Single" and len(categories) > 1:
            messagebox.showwarning(
                "Warning",
                "Only one category can be selected in Single Categorization mode.",
            )
            return

        self.categorize_responses(responses, categories)

    def categorize_responses(self, responses, categories):
        responses -= {"nan", "missing data"}
        # In categorized_data, each category is a column, with a 1 or 0 for each response

        # Boolean mask for rows in categorized_data containing selected responses
        mask = pd.Series([False] * len(self.categorized_data))

        for column in self.categorized_data[self.response_columns]:
            mask |= self.categorized_data[column].isin(responses)

        if self.categorization_var.get() == "Single":
            for category in self.categorized_dict:
                self.categorized_data.loc[mask, category] = 0
                self.categorized_dict[category] -= responses

            # # Remove responses from match results because they can't be categorized anymore in single mode
            # self.match_results = self.match_results[
            #     ~self.match_results["response"].isin(self.selected_match_responses())
            # ]

        for category in categories:
            self.categorized_data.loc[mask, category] = 1
            self.categorized_dict[category].update(responses)

        self.display_categories()
        self.execute_match()
        self.update_treeview_selections(
            selected_categories=categories,
            selected_responses=responses,
        )
        self.refresh_category_results_for_currently_displayed_category()

    def recategorize_selected_responses(self):
        responses, categories = (
            self.selected_category_responses(),
            self.selected_categories(),
        )

        if not categories or not responses:
            messagebox.showinfo(
                "Info",
                "Please select both a category and responses in the category results display to categorize.",
            )
            return

        if self.currently_displayed_category == "Missing data":
            messagebox.showinfo(
                "Info", 'You cannot recategorize "NaN" or "Missing data" values.'
            )
            return

        if "Missing data" in categories:
            messagebox.showinfo(
                "Info", 'You cannot categorize values into "Missing data".'
            )
            return

        self.recategorize_responses(responses, categories)

    def recategorize_responses(self, responses, categories):
        # In categorized_data, each category is a column, with a 1 or 0 for each response

        # Boolean mask for rows in categorized_data containing selected responses
        mask = pd.Series([False] * len(self.categorized_data))

        for column in self.categorized_data[self.response_columns]:
            mask |= self.categorized_data[column].isin(responses)

        if self.categorization_var.get() == "Single" and len(categories) > 1:
            messagebox.showwarning(
                "Warning",
                "Only one category can be selected in Single Categorization mode.",
            )
            return

        self.categorized_data.loc[mask, self.currently_displayed_category] = 0
        self.categorized_dict[self.currently_displayed_category] -= responses

        for category in categories:
            self.categorized_data.loc[mask, category] = 1
            self.categorized_dict[category].update(responses)

        self.display_categories()
        self.update_treeview_selections(
            selected_categories=categories,
            selected_responses=responses,
        )
        self.refresh_category_results_for_currently_displayed_category()

    def create_category(self):
        new_category = self.user_interface.new_category_entry.get()
        if new_category and new_category not in self.categorized_data.columns:
            self.categorized_data[new_category] = 0
            self.categorized_dict[new_category] = set()
            self.display_categories()

    def rename_category_in_data(self, old_category, new_category):
        if not new_category:
            messagebox.showinfo("Info", "Please enter a non-empty category name.")
            return

        if new_category in self.categorized_dict:
            messagebox.showinfo("Info", "A category with this name already exists.")
            return

        if old_category == "Missing data":
            messagebox.showinfo("Info", 'You cannot rename "Missing data".')
            return

        self.categorized_data.rename(columns={old_category: new_category}, inplace=True)
        self.categorized_dict[new_category] = self.categorized_dict.pop(old_category)

    def delete_categories_in_data(self, categories_to_delete):
        for category in categories_to_delete:
            if (
                self.categorization_var.get() == "Single"
            ):  # In single mode, return the responses from this category to 'Uncategorized'
                responses_to_reclassify = self.categorized_data[
                    self.categorized_data[category] == 1
                ].index
                for response_index in responses_to_reclassify:
                    self.categorized_data.loc[response_index, "Uncategorized"] = 1
                self.categorized_dict["Uncategorized"].update(
                    self.categorized_dict[category]
                )

            del self.categorized_dict[category]
            self.categorized_data.drop(columns=category, inplace=True)

    def calculate_count(self, responses):
        return sum(self.response_counts.get(response, 0) for response in responses)

    def calculate_percentage(self, responses, include_missing_data_bool):
        count = self.calculate_count(responses)

        total_responses = sum(self.response_counts.values())

        if not include_missing_data_bool:
            missing_data_count = self.calculate_count(
                self.categorized_dict["Missing data"]
            )
            total_responses = sum(self.response_counts.values()) - missing_data_count

        return (count / total_responses) * 100 if total_responses > 0 else 0
