import ctypes
import pandas as pd
from io import StringIO
from FuzzyUI import FuzzyUI
from DataModel import DataModel
from FileManager import FileManager

# Set DPI awareness
ctypes.windll.shcore.SetProcessDpiAwareness(1)


# Main application class
class Controller:
    def __init__(
        self, user_interface: FuzzyUI, data_model: DataModel, file_manager: FileManager
    ):
        super().__init__()
        self.user_interface = user_interface
        self.data_model = data_model
        self.file_manager = file_manager

        self.setup_UI_bindings()

        self.user_interface.after(100, self.display_categories)
        self.user_interface.after(
            100,
            self.refresh_category_results_for_currently_displayed_category,
        )

    def setup_UI_bindings(self):
        self.user_interface.match_string_entry.bind(
            "<Return>", lambda event: self.perform_fuzzy_match()
        )
        self.user_interface.threshold_slider.bind(
            "<ButtonRelease-1>", lambda val: self.display_match_results()
        )
        self.user_interface.match_button.bind(
            "<Button-1>", lambda event: self.perform_fuzzy_match()
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
            "<Button-1>", lambda event: self.rename_category()
        )
        self.user_interface.delete_categories_button.bind(
            "<Button-1>", lambda event: self.delete_categories()
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

    ### ----------------------- Main Functionality ----------------------- ###
    def perform_fuzzy_match(self):
        self.data_model.perform_fuzzy_match(
            self.user_interface.match_string_entry.get()
        )
        self.display_match_results()

    def categorize_selected_responses(self):
        responses, categories = (
            self.user_interface.selected_match_responses(),
            self.user_interface.selected_categories(),
        )

        if not categories or not responses:
            self.user_interface.show_warning(
                "Please select both a category and responses to categorize."
            )
            return

        if "Missing data" in categories:
            self.user_interface.show_warning(
                'You cannot categorize values into "Missing data".'
            )
            return

        if "nan" in responses or "missing data" in responses:
            self.user_interface.show_warning(
                'You cannot recategorize "NaN" or "Missing data" values',
            )

        if (
            self.user_interface.categorization_type.get() == "Single"
            and len(categories) > 1
        ):
            self.user_interface.show_warning(
                "Only one category can be selected in Single Categorization mode.",
            )
            return

        self.categorize_responses(responses, categories)

    def categorize_responses(self, responses, categories):
        responses -= {"nan", "missing data"}
        # In categorized_data, each category is a column, with a 1 or 0 for each response

        # Boolean mask for rows in categorized_data containing selected responses
        mask = pd.Series([False] * len(self.data_model.categorized_data))

        for column in self.data_model.categorized_data[
            self.data_model.response_columns
        ]:
            mask |= self.data_model.categorized_data[column].isin(responses)

        if self.user_interface.categorization_type.get() == "Single":
            self.data_model.categorized_data.loc[mask, "Uncategorized"] = 0
            self.data_model.categorized_dict["Uncategorized"] -= responses

        for category in categories:
            self.data_model.categorized_data.loc[mask, category] = 1
            self.data_model.categorized_dict[category].update(responses)

        self.display_categories()
        self.perform_fuzzy_match()
        self.update_treeview_selections(
            selected_categories=categories,
            selected_responses=responses,
        )
        self.refresh_category_results_for_currently_displayed_category()

    def recategorize_selected_responses(self):
        responses, categories = (
            self.user_interface.selected_category_responses(),
            self.user_interface.selected_categories(),
        )

        if not categories or not responses:
            self.user_interface.show_warning(
                "Please select both a category and responses in the category results display to categorize.",
            )
            return

        if self.data_model.currently_displayed_category == "Missing data":
            self.user_interface.show_info(
                'You cannot recategorize "NaN" or "Missing data" values.'
            )
            return

        if "Missing data" in categories:
            self.user_interface.show_warning(
                'You cannot categorize values into "Missing data".'
            )
            return

        if (
            self.user_interface.categorization_type.get() == "Single"
            and len(categories) > 1
        ):
            self.user_interface.show_warning(
                "Only one category can be selected in Single Categorization mode.",
            )
            return

        self.recategorize_responses(responses, categories)

    def recategorize_responses(self, responses, categories):
        # In categorized_data, each category is a column, with a 1 or 0 for each response

        # Boolean mask for rows in categorized_data containing selected responses
        mask = pd.Series([False] * len(self.data_model.categorized_data))

        for column in self.data_model.categorized_data[
            self.data_model.response_columns
        ]:
            mask |= self.data_model.categorized_data[column].isin(responses)

        self.data_model.categorized_data.loc[
            mask, self.data_model.currently_displayed_category
        ] = 0
        self.data_model.categorized_dict[
            self.data_model.currently_displayed_category
        ] -= responses

        for category in categories:
            self.data_model.categorized_data.loc[mask, category] = 1
            self.data_model.categorized_dict[category].update(responses)

        self.display_categories()
        self.update_treeview_selections(
            selected_categories=categories,
            selected_responses=responses,
        )
        self.refresh_category_results_for_currently_displayed_category()

    def categorize_missing_data(self):
        def is_missing(value):
            return (
                pd.isna(value)
                or value is None
                or value == "missing data"
                or value == "nan"
            )

        all_missing_mask = self.data_model.df_preprocessed.map(is_missing).all(  # type: ignore
            axis=1
        )  # Boolean mask where each row is True if all elements are missing
        self.data_model.categorized_data.loc[all_missing_mask, "Missing data"] = 1
        self.data_model.categorized_data.loc[all_missing_mask, "Uncategorized"] = 0

    def calculate_count(self, responses):
        return sum(
            self.data_model.response_counts.get(response, 0) for response in responses
        )

    def calculate_percentage(self, responses, include_missing_data_bool):
        count = self.calculate_count(responses)

        total_responses = sum(self.data_model.response_counts.values())

        if not include_missing_data_bool:
            missing_data_count = self.calculate_count(
                self.data_model.categorized_dict["Missing data"]
            )
            total_responses = (
                sum(self.data_model.response_counts.values()) - missing_data_count
            )

        return (count / total_responses) * 100 if total_responses > 0 else 0

    def create_category(self):
        new_category = self.user_interface.new_category_entry.get()
        success, message = self.data_model.create_category(new_category)

        if success:
            self.display_categories()
        else:
            self.user_interface.show_error(message)

    def rename_category(self):
        selected_categories = self.user_interface.selected_categories()

        if len(selected_categories) != 1:
            self.user_interface.show_warning("Please select one category to rename.")
            return

        if (
            "Uncategorized" in selected_categories
            or "Missing data" in selected_categories
        ):
            self.user_interface.show_warning(
                'You may not rename the categories "Uncategorized" or "Missing data".',
            )
            return

        old_category = selected_categories.pop()

        # Create popup
        self.user_interface.create_rename_category_popup(old_category)
        # Bind widgets to commands
        self.user_interface.ok_button.bind(
            "<Button-1>", lambda event: self.on_rename_category_entry()
        )
        self.user_interface.new_category_entry.bind(
            "<Return>", lambda event: self.on_rename_category_entry()
        )
        self.user_interface.cancel_button.bind(
            "<Button-1>",
            lambda event: self.user_interface.rename_dialog_popup.destroy(),
        )

    def on_rename_category_entry(self):
        old_category = self.user_interface.selected_categories().pop()
        new_category = self.user_interface.new_category_entry.get()

        if not new_category:
            self.user_interface.show_error("Please enter a non-empty category name.")
            return

        success, message = self.data_model.rename_category(old_category, new_category)

        if success:
            self.user_interface.rename_dialog_popup.destroy()
            self.display_categories()
            self.refresh_category_results_for_currently_displayed_category()
        else:
            self.user_interface.show_error(message)

    def delete_categories(self):
        selected_categories = self.user_interface.selected_categories()

        if not selected_categories:
            self.user_interface.show_warning("Please select categories to delete.")
            return

        if (
            "Uncategorized" in selected_categories
            or "Missing data" in selected_categories
        ):
            self.user_interface.show_warning(
                "You may not delete the categories 'Uncategorized' or 'Missing data'.",
            )
            return

        if self.user_interface.show_askyesno(
            "Confirmation", "Are you sure you want to delete the selected categories?"
        ):
            self.data_model.delete_categories(
                selected_categories, self.user_interface.categorization_type.get()
            )
            self.display_categories()
            self.refresh_category_results_for_currently_displayed_category()

    ### ----------------------- UI management ----------------------- ###
    def display_match_results(self):
        # Filter the fuzzy match results based on the threshold
        filtered_results = self.data_model.fuzzy_match_results[
            self.data_model.fuzzy_match_results["score"]
            >= self.user_interface.threshold_slider.get()
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

    def display_category_results_for_selected_category(self):
        selected_categories = self.user_interface.categories_tree.selection()

        if len(selected_categories) == 1:
            # Get the selected category as a string
            category = self.user_interface.categories_tree.item(selected_categories[0])[
                "values"
            ][0]

            self.display_category_results(category)

            # Assign variable for currently displayed category
            self.data_model.currently_displayed_category = (
                category  # This is now the currently displayed category
            )

        elif len(selected_categories) > 1:
            self.user_interface.show_warning("Please select only one category")

        else:
            self.user_interface.show_error("No category selected")

    def refresh_category_results_for_currently_displayed_category(self):
        category = self.data_model.currently_displayed_category

        if not category:
            self.user_interface.show_error("No category results currently displayed")
            return

        self.display_category_results(category)

    def display_category_results(self, category):
        for item in self.user_interface.category_results_tree.get_children():
            self.user_interface.category_results_tree.delete(item)

        if category in self.data_model.categorized_dict:
            responses_and_counts = [
                (response, self.data_model.response_counts.get(response, 0))
                for response in self.data_model.categorized_dict[category]
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

    def display_categories(self):
        selected_categories = self.user_interface.selected_categories()
        include_missing_data_bool = self.user_interface.include_missing_data_bool.get()

        for item in self.user_interface.categories_tree.get_children():
            self.user_interface.categories_tree.delete(item)

        for category, responses in self.data_model.categorized_dict.items():
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
        if (
            self.user_interface.categorization_type.get() == "Multi"
            and selected_responses is not None
        ):
            reselect_treeview_items(
                self.user_interface.match_results_tree, selected_responses
            )

    ### ----------------------- Project Management ----------------------- ###
    def start_new_project(self):
        if self.file_import_new_project():
            self.populate_data_structures_new_project()
            self.display_categories()
            self.refresh_category_results_for_currently_displayed_category()
            self.display_match_results()
            self.user_interface.show_info("Data imported successfully")
            self.ask_categorization_type()

    def file_import_new_project(self):
        if not (
            file_path := self.user_interface.show_open_file_dialog(
                title="Please select a file containing your dataset"
            )
        ):
            return False

        self.df = self.file_manager.read_csv_to_dataframe(file_path)

        if self.df.empty or self.df.shape[1] < 2:
            self.user_interface.show_error(
                "Dataset is empty or does not contain enough columns.\nThe dataset should contain uuids in the first column, and the subsequent columns should contian responses",
            )
            return False

        return True

    def populate_data_structures_new_project(self):
        self.data_model.df_preprocessed = pd.DataFrame(
            self.df.iloc[:, 1:].map(
                self.data_model.preprocess_text  # , na_action="ignore"
            )  # type: ignore
        )

        # categories_display is dict of categories to the deduplicated set of all responses
        df_series = self.data_model.df_preprocessed.stack().reset_index(drop=True)
        self.data_model.categorized_dict = {
            "Uncategorized": set(df_series) - {"nan", "missing data"},
            "Missing data": {"nan", "missing data"},  # default
        }

        self.data_model.response_counts = df_series.value_counts().to_dict()

        uuids = self.df.iloc[:, 0]
        self.data_model.response_columns = list(self.data_model.df_preprocessed.columns)

        # categorized_data carries all response columns and all categories until export where response columns are dropped
        # In categorized_data, each category is a column, with a 1 or 0 for each response
        self.data_model.categorized_data = pd.concat(
            [uuids, self.data_model.df_preprocessed], axis=1
        )
        self.data_model.categorized_data[
            "Uncategorized"
        ] = 1  # Everything starts uncategorized
        self.data_model.categorized_data["Missing data"] = 0
        self.categorize_missing_data()

        self.data_model.currently_displayed_category = "Uncategorized"  # Default

        self.data_model.fuzzy_match_results = pd.DataFrame(
            columns=["response", "score"]
        )  # Default
        self.user_interface.include_missing_data_bool.set(False)

    def ask_categorization_type(self):
        # Create popup
        self.user_interface.create_ask_categorization_type_popup()

        # Functions to execute upon confirm/Enter
        def _on_confirm():
            self.set_categorization_type_label()
            self.user_interface.categorization_type_popup.destroy()

        # Bind widgets to commands
        self.user_interface.confirm_button.bind(
            "<Button-1>", lambda event: _on_confirm()
        )
        self.user_interface.categorization_type_popup.bind(
            "<Return>", lambda event: _on_confirm()
        )

    def set_categorization_type_label(self):
        chosen_type = self.user_interface.categorization_type.get()
        self.user_interface.categorization_label.config(
            text="Categorization Type: " + chosen_type
        )

    def load_project(self):
        if data_loaded := self.file_import_load_project():
            self.populate_data_structures_load_project(data_loaded)
            self.set_categorization_type_label()
            self.display_match_results()
            self.refresh_category_results_for_currently_displayed_category()
            self.display_categories()
            self.user_interface.show_info("Project loaded successfully")

    def file_import_load_project(self):
        if not (
            file_path := self.user_interface.show_open_file_dialog(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Load Project",
            )
        ):
            return False
        return self.file_manager.load_json(file_path)

    def populate_data_structures_load_project(self, data_loaded):
        # Convert JSON back to data / set default variable values
        self.user_interface.categorization_type.set(data_loaded["categorization_type"])
        self.data_model.df_preprocessed = pd.read_json(
            StringIO(data_loaded["df_preprocessed"])
        )
        self.data_model.response_columns = data_loaded["response_columns"]
        self.data_model.categorized_data = pd.read_json(
            StringIO(data_loaded["categorized_data"])
        )
        self.data_model.response_counts = data_loaded["response_counts"]
        self.data_model.categorized_dict = {
            k: set(v) for k, v in data_loaded["categories_display"].items()
        }
        self.data_model.currently_displayed_category = "Uncategorized"  # Default
        self.data_model.fuzzy_match_results = pd.DataFrame(
            columns=["response", "score"]
        )  # Default
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
            self.user_interface.show_info("Data appended successfully")

    def file_import_append_data(self):
        if not (
            file_path := self.user_interface.show_open_file_dialog(
                title="Select file to append"
            )
        ):
            return False

        try:
            new_df = self.file_manager.read_csv_to_dataframe(file_path)

            if new_df.empty or new_df.shape[1] != self.df.shape[1]:
                self.user_interface.show_error(
                    "Dataset is empty or does not have the same shape as the current dataset.\n\nThe dataset should contain uuids in the first column, and the subsequent columns should contain the same number of response columns.",
                )
                return False

            self.df = pd.concat([self.df, new_df], ignore_index=True)
            return True

        except Exception as e:
            self.user_interface.show_error(f"Failed to append data: {e}")

    def populate_data_structures_append_data(self):
        old_data_size = len(self.data_model.df_preprocessed)
        new_df_preprocessed = pd.DataFrame(
            self.df.iloc[old_data_size:, 1:].map(self.data_model.preprocess_text)  # type: ignore
        )
        self.data_model.df_preprocessed = pd.concat(
            [self.data_model.df_preprocessed, new_df_preprocessed]
        )

        # categories_display is dict of categories to the deduplicated set of all responses
        new_df_series = new_df_preprocessed.stack().reset_index(drop=True)
        df_series = self.data_model.df_preprocessed.stack().reset_index(drop=True)
        self.data_model.response_counts = df_series.value_counts().to_dict()
        self.data_model.categorized_dict["Uncategorized"].update(
            set(new_df_series) - {"nan", "missing data"}
        )

        new_categorized_data = pd.concat(
            [self.df.iloc[old_data_size:, 0], new_df_preprocessed], axis=1
        )
        self.data_model.categorized_data = pd.concat(
            [self.data_model.categorized_data, new_categorized_data], axis=0
        )

        self.data_model.categorized_data.loc[
            old_data_size:, "Uncategorized"
        ] = 1  # Everything starts uncategorized
        self.data_model.categorized_data.loc[old_data_size:, "Missing data"] = 0
        self.categorize_missing_data()

        self.data_model.currently_displayed_category = "Uncategorized"  # Default
        self.data_model.fuzzy_match_results = pd.DataFrame(
            columns=["response", "score"]
        )  # Default

    def save_project(self):
        # Pandas NAType is not JSON serializable
        def none_handler(o):
            if pd.isna(o):
                return None

        data_to_save = {
            "categorization_type": self.user_interface.categorization_type.get(),
            "df_preprocessed": self.data_model.df_preprocessed.to_json(),
            "response_columns": self.data_model.response_columns,
            "categorized_data": self.data_model.categorized_data.to_json(),
            "response_counts": self.data_model.response_counts,
            "categories_display": {
                k: list(v) for k, v in self.data_model.categorized_dict.items()
            },
            "include_missing_data_bool": self.user_interface.include_missing_data_bool.get(),
        }

        if file_path := self.user_interface.show_save_file_dialog(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Project As",
        ):
            self.file_manager.save_data_to_json(file_path, data_to_save, none_handler)

            self.user_interface.show_info("Project saved successfully to\n" + file_path)

    def export_to_csv(self):
        # Exported data needs only UUIDs and category binaries to be able to be imported into Q.
        export_df = self.data_model.categorized_data.drop(
            columns=self.data_model.response_columns
        )

        if self.user_interface.categorization_type.get() == "Multi":
            export_df.drop("Uncategorized", axis=1, inplace=True)

        if file_path := self.user_interface.show_save_file_dialog(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save As",
        ):
            self.file_manager.export_dataframe_to_csv(file_path, export_df)

            self.user_interface.show_info("Data exported successfully to\n" + file_path)
        else:
            self.user_interface.show_info("Export cancelled")
