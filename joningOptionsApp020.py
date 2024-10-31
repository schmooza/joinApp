import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import json
import os

# Initialize Tkinter window
root = tk.Tk()
root.title("Data Join App")

# Default user preferences
preferences = {
    "widget_text_size": 10,
    "menu_text_size": 10
}
preferences_file = "preferences.json"

# Load user preferences if they exist
if os.path.exists(preferences_file):
    with open(preferences_file, "r") as file:
        preferences.update(json.load(file))

# Configure grid layout
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=1)
root.grid_rowconfigure(4, weight=1)
root.grid_rowconfigure(6, weight=1)

# Initialize variables for datasets
data1 = pd.DataFrame()
data2 = pd.DataFrame()
result = pd.DataFrame()  # Placeholder for the join result

# Function to adjust text size for data widgets
def set_widget_text_size(size):
    preferences["widget_text_size"] = size
    font = ("TkDefaultFont", size)
    data1_text.configure(font=font)
    data2_text.configure(font=font)
    result_tree.tag_configure("data", font=font)

# Function to adjust text size for all menu items
def set_menu_text_size(size):
    preferences["menu_text_size"] = size
    font = ("TkDefaultFont", size)
    # Apply to all menu items (labels, buttons, comboboxes, section titles)
    for widget in [load_data1_button, load_data2_button, join_button, 
                   increase_text_button, decrease_text_button, 
                   increase_menu_text_button, decrease_menu_text_button, sort_button] + menu_labels:
        widget.configure(font=font)
    join_type.configure(font=font)
    sort_column.configure(font=font)
    sort_column_2.configure(font=font)
    sort_order_choice.configure(font=font)
    # Also apply to Data 1, Data 2, and Join Result labels
    data1_label.configure(font=font)
    data2_label.configure(font=font)
    join_result_label.configure(font=font)

# Function to load data from CSV for Data 1
def load_data1():
    global data1
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file_path:
        data1 = pd.read_csv(file_path)
        data1_text.delete(1.0, tk.END)
        data1_text.insert(tk.END, data1.to_string(index=False))
        
        # Adjust the height based on number of rows
        row_count = len(data1)
        data1_text.config(height=min(20, row_count + 2))  # Set a max height limit

# Function to load data from CSV for Data 2
def load_data2():
    global data2
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file_path:
        data2 = pd.read_csv(file_path)
        data2_text.delete(1.0, tk.END)
        data2_text.insert(tk.END, data2.to_string(index=False))
        
        # Adjust the height based on number of rows
        row_count = len(data2)
        data2_text.config(height=min(20, row_count + 2))  # Set a max height limit

# Function to display join type info
def update_join_info(event=None):
    join_type_text.delete(1.0, tk.END)
    selected_join = join_type.get().strip()
    
    join_descriptions = {
        "Inner": "Inner Join: Returns rows that have matching values in both datasets.",
        "Left": "Left Join: Returns all rows from the left dataset and matching rows from the right dataset.",
        "Right": "Right Join: Returns all rows from the right dataset and matching rows from the left dataset.",
        "Outer": "Outer Join: Returns all rows when there is a match in either left or right dataset.",
        "Cross": "Cross Join: Returns all combinations of rows from both datasets."
    }
    
    join_type_text.insert(tk.END, join_descriptions.get(selected_join, ""))

# Function to perform join on all columns except 'name' and include 'name' in the result
def join_data():
    global result
    if not data1.empty and not data2.empty:
        join_type_selected = join_type.get().strip().lower()  # Get join type

        # Ensure column names are in a consistent format
        data1.columns = data1.columns.str.strip()
        data2.columns = data2.columns.str.strip()

        # Determine columns to join on (all columns except 'name') and explicitly include 'name'
        join_columns = [col for col in data1.columns if col in data2.columns and col != 'name']
        join_columns_with_name = ['name'] + join_columns  # Include 'name' as a join key

        # Handle Cross Join separately
        if join_type_selected == "cross":
            data1['_key'] = 1
            data2['_key'] = 1
            result = data1.merge(data2, on='_key').drop(columns=['_key'])
            data1.drop(columns=['_key'], inplace=True)
            data2.drop(columns=['_key'], inplace=True)
        else:
            try:
                result = data1.merge(data2, on=join_columns_with_name, how=join_type_selected, suffixes=('_1', '_2'))
            except KeyError as e:
                messagebox.showerror("Join Error", f"Join operation failed: {e}")
                return
            except pd.errors.MergeError as e:
                messagebox.showerror("Join Error", f"Merge operation failed: {e}")
                return

        # Populate sort dropdowns with columns from the join result
        sort_column['values'] = list(result.columns)
        sort_column_2['values'] = list(result.columns)  # Secondary sort dropdown

        # Display the join result in the Treeview
        display_join_result()

def display_join_result():
    # Clear previous Treeview contents
    for item in result_tree.get_children():
        result_tree.delete(item)

    # Set columns based on the join result and configure headings
    result_tree["columns"] = list(result.columns)
    result_tree["show"] = "headings"
    for col in result.columns:
        result_tree.heading(col, text=col)
        result_tree.column(col, anchor="center", width=100)

    # Insert rows into Treeview
    for _, row in result.iterrows():
        result_tree.insert("", "end", values=list(row), tags=("data",))

# Function to save user preferences on window close
def on_closing():
    with open(preferences_file, "w") as file:
        json.dump(preferences, file)
    root.destroy()

# Function to sort the join result based on selected columns
def sort_result():
    global result
    if result.empty:
        messagebox.showwarning("No Data", "No joined data available to sort.")
        return

    # Get primary and secondary sort columns
    sort_by = sort_column.get()
    sort_by_2 = sort_column_2.get()
    sort_order = sort_order_choice.get()

    # Determine sort order for ascending or descending
    ascending = True if sort_order == "Ascending" else False

    # Apply sorting based on the chosen order
    if sort_order == "Random":
        result = result.sample(frac=1).reset_index(drop=True)  # Shuffle rows randomly
    else:
        if sort_by and sort_by_2 and sort_by != sort_by_2:
            result.sort_values(by=[sort_by, sort_by_2], ascending=[ascending, ascending], inplace=True)
        elif sort_by:
            result.sort_values(by=sort_by, ascending=ascending, inplace=True)

    # Display sorted data in the Treeview
    display_join_result()

# Create menu labels for easy reference to update font
menu_labels = [
    tk.Label(root, text="Join Type"),
    tk.Label(root, text="Sort By"),
    tk.Label(root, text="Then By"),
    tk.Label(root, text="Order"),
]

# Load Data buttons
load_data1_button = tk.Button(root, text="Load Data 1", command=load_data1)
load_data1_button.grid(row=0, column=0, padx=5, pady=5, sticky="w")

load_data2_button = tk.Button(root, text="Load Data 2", command=load_data2)
load_data2_button.grid(row=0, column=1, padx=5, pady=5, sticky="w")

# Join type dropdown and label
menu_labels[0].grid(row=1, column=0, sticky="w")
join_type = ttk.Combobox(root, values=["Inner", "Left", "Right", "Outer", "Cross"])
join_type.set("Inner")
join_type.bind("<<ComboboxSelected>>", update_join_info)
join_type.grid(row=1, column=1, sticky="w")

# Join button
join_button = tk.Button(root, text="Join Data", command=join_data)
join_button.grid(row=1, column=2, padx=5, pady=5, sticky="w")

# Text size adjustment buttons for widgets
increase_text_button = tk.Button(root, text="Increase Text Size", command=lambda: set_widget_text_size(preferences["widget_text_size"] + 1))
increase_text_button.grid(row=1, column=3, padx=5, pady=5)

decrease_text_button = tk.Button(root, text="Decrease Text Size", command=lambda: set_widget_text_size(max(8, preferences["widget_text_size"] - 1)))
decrease_text_button.grid(row=1, column=4, padx=5, pady=5)

# Text size adjustment buttons for menu items
increase_menu_text_button = tk.Button(root, text="Increase Menu Text Size", command=lambda: set_menu_text_size(preferences["menu_text_size"] + 1))
increase_menu_text_button.grid(row=1, column=5, padx=5, pady=5)

decrease_menu_text_button = tk.Button(root, text="Decrease Menu Text Size", command=lambda: set_menu_text_size(max(8, preferences["menu_text_size"] - 1)))
decrease_menu_text_button.grid(row=1, column=6, padx=5, pady=5)

# Info box for join type descriptions
join_type_text = tk.Text(root, height=3, width=50, wrap="word")
join_type_text.grid(row=2, column=0, columnspan=7, padx=5, pady=5, sticky="ew")
update_join_info()

# Data section labels
data1_label = tk.Label(root, text="Data 1")
data1_label.grid(row=3, column=0, sticky="w")

data2_label = tk.Label(root, text="Data 2")
data2_label.grid(row=3, column=1, sticky="w")

join_result_label = tk.Label(root, text="Join Result")
join_result_label.grid(row=5, column=0, columnspan=7, sticky="w")

# Data display boxes
data1_text = tk.Text(root, width=30)
data1_text.grid(row=4, column=0, padx=5, pady=5, sticky="nsew")

data2_text = tk.Text(root, width=30)
data2_text.grid(row=4, column=1, padx=5, pady=5, sticky="nsew")

# Join Result display with Treeview
result_tree = ttk.Treeview(root, show='headings')
result_tree.grid(row=6, column=0, columnspan=7, padx=5, pady=5, sticky="nsew")

# Sort options
menu_labels[1].grid(row=7, column=0, sticky="w")
sort_column = ttk.Combobox(root, values=[], state="readonly")
sort_column.grid(row=7, column=1, sticky="w")

menu_labels[2].grid(row=7, column=2, sticky="w")
sort_column_2 = ttk.Combobox(root, values=[], state="readonly")
sort_column_2.grid(row=7, column=3, sticky="w")

menu_labels[3].grid(row=7, column=4, sticky="w")
sort_order_choice = ttk.Combobox(root, values=["Ascending", "Descending", "Random"])
sort_order_choice.set("Ascending")
sort_order_choice.grid(row=7, column=5, sticky="w")

# Sort button
sort_button = tk.Button(root, text="Sort Data", command=sort_result)
sort_button.grid(row=7, column=6, padx=5, pady=5, sticky="w")

# Set initial text size from preferences
set_widget_text_size(preferences["widget_text_size"])
set_menu_text_size(preferences["menu_text_size"])

# Configure grid to expand with the window size
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=1)
root.grid_rowconfigure(4, weight=1)
root.grid_rowconfigure(6, weight=1)

# Bind window close event to save preferences
root.protocol("WM_DELETE_WINDOW", on_closing)

# Start Tkinter main loop
root.mainloop()