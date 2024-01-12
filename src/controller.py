import logging
import logging_utils
from typing import Callable, Tuple
from fuzzy_ui import FuzzyUI
from data_model import DataModel

# Setup logging
logger = logging.getLogger(__name__)


# Main application class
class Controller:
    def __init__(self, user_interface: FuzzyUI, data_model: DataModel):
        logger.info("Initializing controller")

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
            "<Return>", lambda event: self.fuzzy_match_logic()
        )
        self.user_interface.threshold_slider.bind(
            "<ButtonRelease-1>", lambda val: self.display_fuzzy_match_results()
        )
        self.user_interface.match_button.bind("<Button-1>", lambda event: self.fuzzy_match_logic())
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
            "<Button-1>", lambda event: self.append_data_logic()
        )
        self.user_interface.save_button.bind("<Button-1>", lambda event: self.save_project())
        self.user_interface.export_csv_button.bind(
            "<Button-1>", lambda event: self.export_data_to_csv()
        )

    def run(self):
        logger.info("Starting the app mainloop")
        self.user_interface.mainloop()

    ### ----------------------- Main Functionality ----------------------- ###
    def fuzzy_match_logic(self):
        logger.info("Getting string entry")
        string_to_match = self.user_interface.match_string_entry.get()
        logger.info(f'Calling data model to fuzzy match: "{string_to_match}"')
        self.data_model.fuzzy_match_logic(string_to_match)
        self.display_fuzzy_match_results()

    def categorize_selected_responses(self):
        logger.info("Getting selected categories and responses")
        responses = self.user_interface.selected_match_responses()
        categories = self.user_interface.selected_categories()
        categorization_type = self.user_interface.categorization_type.get()

        if not categories or not responses:
            logger.warning("Both a category and response must be selected to categorize")
            logger.debug(f"selected categories:{categories}, selected responses:{responses}")
            self.user_interface.show_warning(
                "Please select both a category and responses to categorize."
            )
            return

        if categorization_type == "Single" and len(categories) > 1:
            logger.warning("Only one category can be selected in Single Categorization mode.")
            logger.debug(f"selected categories:{categories}")
            self.user_interface.show_warning(
                "Only one category can be selected in Single Categorization mode.",
            )
            return

        logger.info("Calling data model to categorize selected responses into selected categories")
        self.data_model.categorize_responses(responses, categories, categorization_type)

        self.refresh_treeviews()
        self.user_interface.update_treeview_selections(
            selected_categories=categories,
            selected_responses=responses,
        )

    def recategorize_selected_responses(self):
        logger.info("Getting selected categories and responses")
        responses, categories = (
            self.user_interface.selected_category_responses(),
            self.user_interface.selected_categories(),
        )

        if not categories or not responses:
            logger.warning(
                "Both a category and response from the category results display must be selected to categorize"
            )
            logger.debug(f"selected categories:{categories}, selected responses:{responses}")
            self.user_interface.show_warning(
                "Please select both a category and responses in the category results display to categorize.",
            )
            return

        if self.user_interface.categorization_type.get() == "Single" and len(categories) > 1:
            logger.warning("Only one category can be selected in Single Categorization mode.")
            logger.debug(f"selected categories:{categories}")
            self.user_interface.show_warning(
                "Only one category can be selected in Single Categorization mode.",
            )
            return

        logger.info(
            "Calling data model to recategorize selected responses into selected categories"
        )
        self.data_model.recategorize_responses(responses, categories)

        self.refresh_treeviews()
        self.user_interface.update_treeview_selections(
            selected_categories=categories,
            selected_responses=responses,
        )

    def create_category(self):
        logger.info("Getting new category entry")
        new_category = self.user_interface.new_category_entry.get()

        if not new_category:
            message = "Category name cannot be empty"
            logger.warning(message)
            logging_utils.format_and_log_data_for_debug(logger, {"new_category": new_category})
            return False, message

        logger.info(f'Calling data model to create new category: "{new_category}"')
        success, message = self.data_model.create_category(new_category)

        if success:
            self.display_categories()
        else:
            self.user_interface.show_error(message)

    def rename_category(self):
        logger.info("Getting selected categories")
        selected_categories = self.user_interface.selected_categories()

        if len(selected_categories) != 1:
            logger.warning("One category to be renamed has not been selected")
            logger.debug(f"selected_categories: {selected_categories}")
            self.user_interface.show_warning("Please select one category to rename.")
            return

        if "Uncategorized" in selected_categories:
            logger.warning('Category "Uncategorized" cannot be renamed')
            logger.debug(f"selected_categories: {selected_categories}")
            self.user_interface.show_warning(
                'You may not rename the category "Uncategorized".',
            )
            return

        old_category = selected_categories.pop()

        # Create popup
        logger.info("Calling UI to create rename popup")
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
        logger.info("Getting new category entry")
        new_category = self.user_interface.new_category_entry.get()

        if not new_category:
            logger.error("New category entry must be non-empty")
            logger.debug(f'new_category: "{new_category}"')
            self.user_interface.show_error("Please enter a non-empty category name.")
            return

        logger.info(
            f"Calling data model to rename category. Old category: {old_category}, new category: {new_category}"
        )
        success, message = self.data_model.rename_category(old_category, new_category)

        if success:
            self.user_interface.rename_dialog_popup.destroy()
            self.display_categories()
            self.display_category_results()
        else:
            self.user_interface.show_error(message)

    def delete_categories(self):
        logger.info("Getting selected categories")
        selected_categories = self.user_interface.selected_categories()

        if not selected_categories:
            logger.warning("No categories selected to delete")
            logger.debug(f"Selected categories: {selected_categories}")
            self.user_interface.show_warning("Please select categories to delete.")
            return

        if "Uncategorized" in selected_categories:
            logger.warning('Category "Uncategorized" cannot be deleted')
            logger.debug(f"selected_categories: {selected_categories}")
            self.user_interface.show_warning(
                'You may not delete the category "Uncategorized".',
            )
            return

        logger.info("Calling UI to get confirmation")
        if self.user_interface.show_askyesno(
            "Confirmation", "Are you sure you want to delete the selected categories?"
        ):
            logger.info(
                f"Category deletion confirmed. Calling data model to delete categories: {selected_categories}"
            )
            self.data_model.delete_categories(
                selected_categories, self.user_interface.categorization_type.get()
            )
            self.display_categories()
            self.display_category_results()
        else:
            logger.info("Category deletion aborted")

    ### ----------------------- Project Management ----------------------- ###
    def new_project(self):
        logger.info("Starting new project")
        try:
            if self.file_import_logic(
                file_types=[("CSV files", "*.csv"), ("XLSX files", "*.xlsx"), ("All files", "*.*")],
                title="Please select a file containing your dataset",
                data_model_method=self.data_model.file_import_on_new_project,
            ):
                self.populate_data_structures_on_new_project()
                self.refresh_treeviews()
                self.user_interface.show_info("Data imported successfully")
                self.ask_categorization_type()
                logger.info("New project setup successfully")

        except Exception as e:
            logger.exception("")
            self.user_interface.show_error(f"Failed to initialize new project: {e}")

    def populate_data_structures_on_new_project(self):
        logger.info("Calling data model to populate data structures")
        self.data_model.populate_data_structures_on_new_project()
        logger.info("Resetting UI variables")
        self.user_interface.is_including_missing_data.set(False)

    def ask_categorization_type(self):
        logger.info("Calling UI to create popup for categorization type")
        self.user_interface.create_ask_categorization_type_popup()

    def load_project(self):
        logger.info("Starting load project")
        try:
            if self.file_import_logic(
                file_types=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Load Project",
                data_model_method=self.data_model.file_import_on_load_project,
            ):
                self.populate_data_structures_on_load_project()
                self.user_interface.set_categorization_type_label()
                self.refresh_treeviews()
                logger.info("Project loaded successfully")
                self.user_interface.show_info("Project loaded successfully")

        except Exception as e:
            logger.exception("")
            self.user_interface.show_error(f"Failed to load project: {e}")

    def populate_data_structures_on_load_project(self):
        logger.info("Calling data model to popuate data structures")
        (
            categorization_type,
            is_including_missing_data,
        ) = self.data_model.populate_data_structures_on_load_project()

        logger.info("Calling UI to set UI variables")
        self.user_interface.categorization_type.set(categorization_type)
        self.user_interface.is_including_missing_data.set(is_including_missing_data)

    def append_data_logic(self):
        logger.info("Starting append data")
        try:
            if self.file_import_logic(
                file_types=[("CSV files", "*.csv"), ("XLSX files", "*.xlsx"), ("All files", "*.*")],
                title="Select file containing data to append",
                data_model_method=self.data_model.file_import_on_append_data,
            ):
                self.data_model.populate_data_structures_on_append_data()
                self.refresh_treeviews()
                logger.info("Data appended successfully")
                self.user_interface.show_info("Data appended successfully")
        except Exception as e:
            logger.exception("")
            self.user_interface.show_error(f"Failed to append data: {e}")

    def file_import_logic(
        self, file_types: list[Tuple[str, str]], title: str, data_model_method: Callable
    ) -> bool:
        logger.info("Calling UI to get file path")
        file_path = self.user_interface.show_open_file_dialog(
            filetypes=file_types,
            title=title,
        )

        if not file_path:
            logger.info("No file path selected")
            return False

        logger.info("Calling data model to import file")
        success, message = data_model_method(file_path)

        if not success:
            logger.error(message)
            self.user_interface.show_error(message)
            return False

        return True

    def save_project(self):
        # TODO: Possibly abstract out this and export_data_to_csv into a single method?
        logger.info("Starting save project")
        try:
            logger.info("Calling UI to get file path")
            if file_path := self.user_interface.show_save_file_dialog(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Save Project As",
            ):
                user_interface_variables_to_add = {
                    "categorization_type": self.user_interface.categorization_type.get(),
                    "is_including_missing_data": self.user_interface.is_including_missing_data.get(),
                }

                logger.info("Calling data model to save project")
                self.data_model.save_project(file_path, user_interface_variables_to_add)
                logger.info("Project saved successfully")
                self.user_interface.show_info("Project saved successfully to:\n\n" + file_path)

            else:
                logger.info("No file path selected")

        except Exception as e:
            logger.exception("")
            self.user_interface.show_error(f"Failed to save project: {e}")

    def export_data_to_csv(self):
        logger.info("Starting data export")
        try:
            logger.info("Calling UI to get file path")
            if file_path := self.user_interface.show_save_file_dialog(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Save As",
            ):
                categorization_type = self.user_interface.categorization_type.get()
                logger.info("Calling data model to export data")
                self.data_model.export_data_to_csv(file_path, categorization_type)
                logger.info("Data exported successfully")
                self.user_interface.show_info("Data exported successfully to:\n\n" + file_path)

            else:
                logger.info("No file path selected")

        except Exception as e:
            logger.exception("")
            self.user_interface.show_error(f"Failed to export data to csv: {e}")

    ### ----------------------- UI management ----------------------- ###
    def refresh_treeviews(self):
        self.display_fuzzy_match_results()
        self.display_category_results()
        self.display_categories()

    def display_fuzzy_match_results(self):
        logger.info("Calling UI to get fuzzy threshold")
        threshold = self.user_interface.threshold_slider.get()
        logger.info("Calling data model to process and return fuzzy match results")
        processed_results = self.data_model.process_fuzzy_match_results(threshold)
        logger.info("Calling UI to display fuzzy match results")
        self.user_interface.display_fuzzy_match_results(processed_results)

    def on_display_selected_category_results(self):
        logger.info("Calling UI to get selected categories")
        selected_categories = self.user_interface.selected_categories()

        if len(selected_categories) == 0:
            logger.error("No category selected to display results of")
            logger.debug(f"selected categories: {selected_categories}")
            self.user_interface.show_error("No category selected")
            return

        if len(selected_categories) > 1:
            logger.error("Only one category can be displayed")
            logger.debug(f"selected categories: {selected_categories}")
            self.user_interface.show_warning("Please select only one category")
            return

        # Assign new currently displayed category
        new_current_category = selected_categories.pop()
        logger.info(
            f"Calling data model to set new currently displayed category: {new_current_category}"
        )
        self.data_model.currently_displayed_category = new_current_category

        self.display_category_results()

    def display_category_results(self):
        logger.info("Calling data model to get currently displayed category and data")
        category = self.data_model.currently_displayed_category
        responses_and_counts = self.data_model.get_responses_and_counts(category)
        logger.info("Calling UI to display category results")
        self.user_interface.display_category_results(category, responses_and_counts)

    def display_categories(self):
        logger.info("Calling UI to get is_including_missing_data bool")
        is_including_missing_data = self.user_interface.is_including_missing_data.get()
        logger.info("Calling data model to format category metrics")
        formatted_categories_metrics = self.data_model.format_categories_metrics(
            is_including_missing_data
        )
        logger.info("Calling UI to display categories and metrics")
        self.user_interface.display_categories(formatted_categories_metrics)
