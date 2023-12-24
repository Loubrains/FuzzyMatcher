from fuzzy_ui import FuzzyUI
from data_model import DataModel


# Main application class
class Controller:
    def __init__(self, user_interface: FuzzyUI, data_model: DataModel):
        super().__init__()
        self.user_interface = user_interface
        self.data_model = data_model

        self.setup_UI_bindings()

        self.user_interface.after(100, self.display_categories)
        self.user_interface.after(
            100,
            self.display_category_results,
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
            lambda event: self.on_display_selected_category_results(),
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
        self.user_interface.is_including_missing_data.trace_add(
            "write", lambda *args: self.display_categories()
        )  # Using trace_add() to make sure it calls the command only after setting the bool value.
        self.user_interface.new_project_button.bind("<Button-1>", lambda event: self.new_project())
        self.user_interface.load_button.bind("<Button-1>", lambda event: self.load_project())
        self.user_interface.append_data_button.bind(
            "<Button-1>", lambda event: self.append_data_behaviour()
        )
        self.user_interface.save_button.bind("<Button-1>", lambda event: self.save_project())
        self.user_interface.export_csv_button.bind("<Button-1>", lambda event: self.export_to_csv())

    def run(self):
        self.user_interface.mainloop()

    ### ----------------------- Main Functionality ----------------------- ###
    def perform_fuzzy_match(self):
        self.data_model.perform_fuzzy_match(self.user_interface.match_string_entry.get())
        self.display_match_results()

    def categorize_selected_responses(self):
        responses = self.user_interface.selected_match_responses()
        categories = self.user_interface.selected_categories()
        categorization_type = self.user_interface.categorization_type.get()

        if not categories or not responses:
            self.user_interface.show_warning(
                "Please select both a category and responses to categorize."
            )
            return

        if "Missing data" in categories:
            self.user_interface.show_warning('You cannot categorize values into "Missing data".')
            return

        if "nan" in responses or "missing data" in responses:
            self.user_interface.show_warning(
                'You cannot recategorize "NaN" or "Missing data" values',
            )

        if categorization_type == "Single" and len(categories) > 1:
            self.user_interface.show_warning(
                "Only one category can be selected in Single Categorization mode.",
            )
            return

        self.data_model.categorize_responses(responses, categories, categorization_type)
        self.display_categories()
        self.perform_fuzzy_match()
        self.user_interface.update_treeview_selections(
            selected_categories=categories,
            selected_responses=responses,
        )
        self.display_category_results()

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
            self.user_interface.show_info('You cannot recategorize "NaN" or "Missing data" values.')
            return

        if "Missing data" in categories:
            self.user_interface.show_warning('You cannot categorize values into "Missing data".')
            return

        if self.user_interface.categorization_type.get() == "Single" and len(categories) > 1:
            self.user_interface.show_warning(
                "Only one category can be selected in Single Categorization mode.",
            )
            return

        self.data_model.recategorize_responses(responses, categories)
        self.display_categories()
        self.user_interface.update_treeview_selections(
            selected_categories=categories,
            selected_responses=responses,
        )
        self.display_category_results()

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

        if "Uncategorized" in selected_categories or "Missing data" in selected_categories:
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
            self.display_category_results()
        else:
            self.user_interface.show_error(message)

    def delete_categories(self):
        selected_categories = self.user_interface.selected_categories()

        if not selected_categories:
            self.user_interface.show_warning("Please select categories to delete.")
            return

        if "Uncategorized" in selected_categories or "Missing data" in selected_categories:
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
            self.display_category_results()

    ### ----------------------- Project Management ----------------------- ###
    def new_project(self):
        try:
            if self.file_import_on_new_project():
                self.populate_data_structures_on_new_project()
                self.refresh_treeviews()
                self.user_interface.show_info("Data imported successfully")
                self.ask_categorization_type()
        except Exception as e:
            self.user_interface.show_error(f"Failed to initialize new project: {e}")

    def file_import_on_new_project(self):
        file_path = self.user_interface.show_open_file_dialog(
            title="Please select a file containing your dataset"
        )
        if not file_path:
            return False

        success, message = self.data_model.file_import_on_new_project(file_path)
        if not success:
            self.user_interface.show_error(message)
            return False

        return True

    def populate_data_structures_on_new_project(self):
        self.data_model.populate_data_structures_on_new_project()
        self.user_interface.is_including_missing_data.set(False)

    def ask_categorization_type(self):
        # Create popup
        self.user_interface.create_ask_categorization_type_popup()

        # Functions to execute upon confirm/Enter
        def _on_confirm():
            self.user_interface.set_categorization_type_label()
            self.user_interface.categorization_type_popup.destroy()

        # Bind widgets to commands
        self.user_interface.confirm_button.bind("<Button-1>", lambda event: _on_confirm())
        self.user_interface.categorization_type_popup.bind("<Return>", lambda event: _on_confirm())

    def load_project(self):
        try:
            if self.file_import_on_load_project():
                self.populate_data_structures_on_load_project()
                self.user_interface.set_categorization_type_label()
                self.refresh_treeviews()
                self.user_interface.show_info("Project loaded successfully")
        except Exception as e:
            self.user_interface.show_error(f"Failed to load project: {e}")

    def file_import_on_load_project(self):
        file_path = self.user_interface.show_open_file_dialog(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Project",
        )
        if not file_path:
            return False  # No need to inform the user

        success, message = self.data_model.file_import_on_load_project(file_path)
        if not success:
            self.user_interface.show_error(message)
            return False

        return True

    def populate_data_structures_on_load_project(self):
        (
            categorization_type,
            is_including_missing_data,
        ) = self.data_model.populate_data_structures_on_load_project()
        self.user_interface.categorization_type.set(categorization_type)
        self.user_interface.is_including_missing_data.set(is_including_missing_data)

    def append_data_behaviour(self):
        try:
            if self.file_import_on_append_data():
                self.data_model.populate_data_structures_on_append_data()
                self.refresh_treeviews()
                self.user_interface.show_info("Data appended successfully")
        except Exception as e:
            self.user_interface.show_error(f"Failed to append data: {e}")

    def file_import_on_append_data(self):
        file_path = self.user_interface.show_open_file_dialog(title="Select file to append")

        if not file_path:
            return False

        success, message = self.data_model.file_import_on_append_data(file_path)
        if not success:
            self.user_interface.show_error(message)
            return False

        return True

    def save_project(self):
        try:
            if file_path := self.user_interface.show_save_file_dialog(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Save Project As",
            ):
                user_interface_variables_to_add = {
                    "categorization_type": self.user_interface.categorization_type.get(),
                    "is_including_missing_data": self.user_interface.is_including_missing_data.get(),
                }
                self.data_model.save_project(file_path, user_interface_variables_to_add)
                self.user_interface.show_info("Project saved successfully to:\n\n" + file_path)
        except Exception as e:
            self.user_interface.show_error(f"Failed to save project: {e}")

    def export_to_csv(self):
        try:
            if file_path := self.user_interface.show_save_file_dialog(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Save As",
            ):
                self.data_model.export_data_to_csv(
                    file_path, self.user_interface.categorization_type.get()
                )
                self.user_interface.show_info("Data exported successfully to:\n\n" + file_path)
        except Exception as e:
            self.user_interface.show_error(f"Failed to export data to csv: {e}")

    ### ----------------------- UI management ----------------------- ###
    def refresh_treeviews(self):
        self.display_match_results()
        self.display_category_results()
        self.display_categories()

    def display_match_results(self):
        processed_results = self.data_model.process_fuzzy_match_results(
            self.user_interface.threshold_slider.get()
        )
        self.user_interface.display_match_results(processed_results)

    def on_display_selected_category_results(self):
        selected_categories = self.user_interface.selected_categories()

        if len(selected_categories) == 0:
            self.user_interface.show_error("No category selected")
            return

        if len(selected_categories) > 1:
            self.user_interface.show_warning("Please select only one category")
            return

        # Assign new currently displayed category
        self.data_model.currently_displayed_category = selected_categories.pop()
        self.display_category_results()

    def display_category_results(self):
        category = self.data_model.currently_displayed_category
        responses_and_counts = self.data_model.get_responses_and_counts(category)
        self.user_interface.display_category_results(category, responses_and_counts)

    def display_categories(self):
        is_including_missing_data = self.user_interface.is_including_missing_data.get()
        formatted_categories_metrics = self.data_model.format_categories_metrics(
            is_including_missing_data
        )
        self.user_interface.display_categories(formatted_categories_metrics)
