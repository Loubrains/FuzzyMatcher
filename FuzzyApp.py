import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import ctypes
import pandas as pd
import re
import chardet
from thefuzz import fuzz

# Set DPI Awareness
ctypes.windll.shcore.SetProcessDpiAwareness(1)

def file_import(file_path):
    with open(file_path, 'rb') as file:
        encoding = chardet.detect(file.read())['encoding']
    df = pd.read_csv(file_path, encoding=encoding)
    return df

def preprocess_text(text):
    # Lowercase, remove leading and trailing white space
    text = str(text).lower().strip()
    # Remove special characters
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text

def fuzzy_matching(df_preprocessed, match_string_entry):
    match_string = match_string_entry.get()
    # Fuzzy match element with given string
    def fuzzy_match(element):
        return fuzz.WRatio(match_string, str(element))

    # Get fuzzy matching scores and format result: (response, score)
    results = []
    for row in df_preprocessed.itertuples(index=True, name=None):
        for response in row[1:]:
            score = fuzzy_match(response)
            # Append a dictionary for each matching record
            results.append({'response': response, 'score': score})

    # Convert list of dictionaries to DataFrame
    df_result = pd.DataFrame(results)

    return df_result

# Main application class
class FuzzyMatcherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Fuzzy Matcher")
        self.geometry("1000x600")

        # Initialize variable for categorization type
        self.categorization_var = tk.StringVar(value="Single")

        # File upload process
        self.df = None
        while self.df is None:
            file_path = filedialog.askopenfilename(title= "Please select a file containing your dataset")
            if file_path:
                self.df = file_import(file_path)
                if self.df.empty or self.df.shape[1] < 2:  # Check if the DataFrame is empty or has less than 2 columns
                    messagebox.showerror("Error", "Dataset is empty or does not contain enough columns.")
                    return
            else:
                # Provide an option to exit the application
                if messagebox.askyesno("Exit", "No file selected. Do you want to exit the application?"):
                    self.destroy()  # Close the application
                    return

        # Preprocess text, initialize categories and label all responses as 'Uncategorized'
        self.initialize_data_structures()

        # Ask for categorization type after file is selected
        self.after(100, self.set_categorization_type)

        # Configure the grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        # Create frames
        left_frame = tk.Frame(self)
        middle_frame = tk.Frame(self)
        right_frame = tk.Frame(self)
        bottom_frame = tk.Frame(self)

        left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        middle_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        right_frame.grid(row=0, column=2, sticky="nsew", padx=10, pady=10)
        bottom_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=10, pady=10)

        # Left Frame Widgets (Match Results)
        self.match_string_label = tk.Label(left_frame, text="Enter String to Match:")
        self.match_string_entry = tk.Entry(left_frame)
        self.threshold_label = tk.Label(left_frame, text="Set Fuzz Threshold (100 is precise, 0 is imprecise):")
        self.threshold_slider = tk.Scale(left_frame, from_=0, to=100, orient="horizontal", resolution=1,
                                        command=lambda val: self.display_match_results())
        self.threshold_slider.set(60)  # Setting default value to 60
        self.match_button = tk.Button(left_frame, text="Match", command=self.process_match)
        self.categorize_button = tk.Button(left_frame, text="Categorize Selected", command=self.categorize_response)
        self.categorization_label = tk.Label(left_frame, text="Categorization Type: Single") # Default text, will be updated later
        self.results_tree = ttk.Treeview(left_frame, columns=('Response', 'Score', 'Count'), show='headings')
        self.results_tree.heading('Response', text='Response')
        self.results_tree.heading('Score', text='Score')
        self.results_tree.heading('Count', text='Count')
        results_scrollbar = tk.Scrollbar(left_frame, orient="vertical", command=self.results_tree.yview)
        
        self.match_string_label.grid(row=0, column=0, sticky="ew")
        self.match_string_entry.grid(row=1, column=0, sticky="ew")
        self.threshold_label.grid(row=2, column=0, sticky="ew")
        self.threshold_slider.grid(row=3, column=0, sticky="ew")
        self.categorization_label.grid(row=4, column=0, sticky="ew")
        self.match_button.grid(row=5, column=0, sticky="ew")
        self.categorize_button.grid(row=5, column=1, sticky="ew")
        self.results_tree.grid(row=6, column=0, columnspan=2, sticky="nsew")
        results_scrollbar.grid(row=6, column=2, sticky="ns")
        self.results_tree.configure(yscrollcommand=results_scrollbar.set)

        # Middle Frame Widgets (Category Results)
        self.display_category_results_button = tk.Button(middle_frame, text="Display Category Results", command=self.display_category_results)
        self.category_results_tree = ttk.Treeview(middle_frame, columns=('Response', 'Count'), show='headings')
        self.category_results_tree.heading('Response', text='Response')
        self.category_results_tree.heading('Count', text='Count')
        category_results_scrollbar = tk.Scrollbar(middle_frame, orient="vertical", command=self.category_results_tree.yview)
        
        self.display_category_results_button.grid(row=0, column=0, sticky="ew")
        self.category_results_tree.grid(row=1, column=0, sticky="nsew")
        category_results_scrollbar.grid(row=1, column=1, sticky="ns")
        self.category_results_tree.configure(yscrollcommand=category_results_scrollbar.set)

        # Right Frame Widgets (Categories)
        self.new_category_entry = tk.Entry(right_frame)
        self.add_category_button = tk.Button(right_frame, text="Add Category", command=self.create_category)
        self.categories_tree = ttk.Treeview(right_frame, columns=('Category', 'Count'), show='headings')
        self.categories_tree.heading('Category', text='Category')
        self.categories_tree.heading('Count', text='Count')
        categories_scrollbar = tk.Scrollbar(right_frame, orient="vertical", command=self.categories_tree.yview)

        self.new_category_entry.grid(row=0, column=0, sticky="ew")
        self.add_category_button.grid(row=1, column=0, sticky="ew")
        self.categories_tree.grid(row=2, column=0, sticky="nsew")
        categories_scrollbar.grid(row=2, column=1, sticky="ns")
        self.categories_tree.configure(yscrollcommand=categories_scrollbar.set)

        # Bottom Frame Widget (Export Button)
        self.export_csv_button = tk.Button(bottom_frame, text="Export to CSV", command=self.export_to_csv)
        self.export_csv_button.grid(row=0, column=2, sticky="e")

        # Display categories
        self.display_categories()

    def initialize_data_structures(self):
        # Preprocess text
        self.df_preprocessed = self.df.iloc[:, 1:].map(preprocess_text)
        self.response_columns= [col for col in self.df_preprocessed.columns]

        # Initialize categorized data (uuids and preprocessed responses)
        uuids = categorized_data = self.df.iloc[:, 0]
        self.categorized_data = pd.concat([uuids, self.df_preprocessed], axis=1)
        # Add 'Uncategorized category' and set all responses to 1
        self.categorized_data['Uncategorized'] = 1

        # Create a flattened DataFrame of the preprocessed responses
        df_series = self.df_preprocessed.stack().reset_index(drop=True)

        # Count each response including duplicates
        self.response_counts = df_series.value_counts().to_dict()

        # Initialize categories for display and set all unique responses to 'Uncategorized'
        self.categories_for_display = {'Uncategorized': set(df_series)}

        # Initialize match results dataframe
        self.match_results = pd.DataFrame(columns=['response', 'score'])

    def set_categorization_type(self):
        popup = tk.Toplevel(self)
        popup.title("Select Categorization Type")
        popup.geometry("400x200")

        # Center the popup on the main window
        window_width = self.winfo_reqwidth()
        window_height = self.winfo_reqheight()
        position_right = int(self.winfo_screenwidth()/2 - window_width/2)
        position_down = int(self.winfo_screenheight()/2 - window_height/2)
        popup.geometry("+{}+{}".format(position_right, position_down))

        # Keep the popup window on top
        popup.transient(self)  # Keep it on top of the main window
        popup.grab_set()       # Ensure all events are directed to this window until closed

        def confirm_categorization_type():
            chosen_type = self.categorization_var.get()
            self.categorization_label.config(text="Categorization Type: " + chosen_type)

        single_categorization_rb = tk.Radiobutton(popup, text="Single Categorization", variable=self.categorization_var, value="Single")
        multi_categorization_rb = tk.Radiobutton(popup, text="Multi Categorization", variable=self.categorization_var, value="Multi")
        confirm_button = tk.Button(popup, text="Confirm", command=lambda: [confirm_categorization_type(), popup.destroy()])

        single_categorization_rb.pack()
        multi_categorization_rb.pack()
        confirm_button.pack()

    def create_category(self):
        new_category = self.new_category_entry.get()
        if new_category and new_category not in self.categorized_data.columns:
            self.categorized_data[new_category] = 0
            self.categories_for_display[new_category] = set()
            self.display_categories()

    def display_categories(self):
        selected_categories = self.selected_categories()

        for item in self.categories_tree.get_children():
            self.categories_tree.delete(item)
        
        for category, responses in self.categories_for_display.items():
            count = sum(self.response_counts.get(response, 0) for response in responses)
            self.categories_tree.insert('', 'end', values=(category, count))
            self.update_treeview_selection(selected_categories=selected_categories)

    def display_category_results(self):
        selected_categories = self.categories_tree.selection()
        
        if len(selected_categories) == 1:
            category = self.categories_tree.item(selected_categories[0])['values'][0]
            
            # Clear existing items in the results display area
            for item in self.category_results_tree.get_children():
                self.category_results_tree.delete(item)

            # Display responses and counts for the selected category
            if category in self.categories_for_display:
                for response in self.categories_for_display[category]:
                    count = self.response_counts[response]
                    self.category_results_tree.insert('', 'end', values=(response, count))

            # Update the results display to reflect the selected category
            self.match_string_label.config(text=f"Results for Category: {category}")

        elif len(selected_categories) > 1:
            messagebox.showerror("Error", "Please select only one category")
        
        else:
            messagebox.showerror("Error", "No category selected")

    def categorize_response(self):
        selected_responses = self.selected_responses()
        selected_categories = self.selected_categories()

        if not selected_categories or not selected_responses:
            messagebox.showinfo("Info", "Please select both a category and responses to categorize.")
            return
        
        # Initalize mask for getting rows in categorized_data corresponding to selected responses
        mask = pd.Series([False] * len(self.categorized_data))

        # Iterate over each response column in categorized_data
        for column in self.categorized_data[self.response_columns]:
            # Update mask where response matches any of the selected responses
            mask |= self.categorized_data[column].isin(selected_responses)

        # Single categorization mode behaviour
        if self.categorization_var.get() == "Single":
            # Show warning if multiple categories selected
            if len(selected_categories) > 1:
                messagebox.showwarning("Warning", "Only one category can be selected in Single Categorization mode.")
                return
            
            # Remove responses from 'Uncategorized' in categorized_data
            self.categorized_data.loc[mask, 'Uncategorized'] = 0
            # Remove responses from categories display and matched responses display
            self.categories_for_display['Uncategorized'] -= selected_responses
            self.match_results = self.match_results[~self.match_results['response'].isin(self.selected_responses())]

        for category in selected_categories:
            # Categorize data (set selected responses equal to 1 for selected categories)
            self.categorized_data.loc[mask, category] = 1

            # Add response to categories for display
            self.categories_for_display[category].update(selected_responses)

        # Update categories and results displays
        self.display_categories()
        self.display_match_results()
        self.update_treeview_selection(selected_categories=selected_categories, selected_responses=selected_responses)

    def process_match(self):
        if self.df_preprocessed is not None:
            # Fuzzy match
            self.match_results = fuzzy_matching(self.df_preprocessed, self.match_string_entry)
            self.display_match_results()
        else:
            messagebox.showerror("Error", "No dataset loaded")
        
    def display_match_results(self):
        # Retrieve the current threshold value from the slider
        threshold = self.threshold_slider.get()

        # Filter the results based on the threshold
        filtered_results = self.match_results[self.match_results['score'] >= threshold]

        # Aggregate and count unique instances
        aggregated_results = filtered_results.groupby('response').agg(
            max_score=pd.NamedAgg(column='score', aggfunc='max'),
            count=pd.NamedAgg(column='response', aggfunc='count')
        ).reset_index()

        # Sort the results first by max_score in descending order, then by count in descending order
        sorted_results = aggregated_results.sort_values(by=['max_score', 'count'], ascending=[False, False])

        # Clear existing items in the results display area
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        # Populate the display area with aggregated unique filtered results
        for _, row in sorted_results.iterrows():
            self.results_tree.insert('', 'end', values=(row['response'], row['max_score'], row['count']))

        ### Update this method to display ORIGINAL STRING ###

    def selected_categories(self):
        return {self.categories_tree.item(item_id)['values'][0] for item_id in self.categories_tree.selection()}
    
    def selected_responses(self):
        return {self.results_tree.item(item_id)['values'][0] for item_id in self.results_tree.selection()}

    def update_treeview_selection(self, selected_categories=None, selected_responses=None):
        def reselect_treeview_items(treeview, values):
            for item in treeview.get_children():
                if treeview.item(item)['values'][0] in values:
                    treeview.selection_add(item)

        # Re-select categories and if multi-categorization re-select match results
        if selected_categories is not None:
            reselect_treeview_items(self.categories_tree, selected_categories)
        if self.categorization_var.get() == "Multi" and selected_responses is not None:
            reselect_treeview_items(self.results_tree, selected_responses)

    def save_session(self):
        # Logic to save current state in json (or other data type), to be reloaded later
        pass

    def load_session(self):
        # Logic to load previously saved state from json (or other data type)
        pass

    def export_to_csv(self):
        # Create export dataframe with all preprocessed response columns removed
        export_df = self.categorized_data.drop(columns=self.response_columns)

        if self.categorization_var.get() == "Multi":
            export_df.drop('Uncategorized', axis=1, inplace=True)

        # Export to CSV
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save As"
        )

        if file_path:
            export_df.to_csv(file_path, index=False)
            messagebox.showinfo("Export", "Data exported successfully to " + file_path)
        else:
            messagebox.showinfo("Export", "Export cancelled")

# Running the application
if __name__ == "__main__":
    app = FuzzyMatcherApp()
    app.mainloop()
