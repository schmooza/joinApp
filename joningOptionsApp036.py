import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font
import pandas as pd
import json
import os

# Initialize Tkinter window
root = tk.Tk()
root.title("Data Join App")
root.geometry("1000x600")  # Set a default size for better visibility

# Default user preferences
preferences = {
    "font_size": 10
}
preferences_file = "preferences.json"

# Load user preferences if they exist
if os.path.exists(preferences_file):
    with open(preferences_file, "r") as file:
        preferences.update(json.load(file))

# Initialize variables for datasets
data1 = pd.DataFrame()
data2 = pd.DataFrame()
result = pd.DataFrame()  # Placeholder for the join result

# Variables to store filenames
data1_filename = tk.StringVar(value="No file loaded")
data2_filename = tk.StringVar(value="No file loaded")

# Treeview style setup for row padding
style = ttk.Style()
style.configure("Treeview", rowheight=20)  # Default row height

# Function to adjust font size and row height for all elements
def set_font_size(size):
    preferences["font_size"] = size
    font_style = font.Font(size=size)
    header_font_style = font.Font(size=size, weight="bold")

    # Configure font for the Treeview headers and data
    style.configure("Treeview", font=font_style, rowheight=int(size * 1.5))
    style.configure("Treeview.Heading", font=header_font_style)

    # Apply font size to other widgets, including menu labels
    for widget in [
        load_data1_button, load_data2_button, join_button,
        increase_font_button, decrease_font_button, sort_button,
        export_csv_button, export_json_button, join_type, sort_column,
        sort_column_2, sort_order_choice, join_result_label, join_type_text
    ] + menu_labels:
        widget.configure(font=font_style)
    
    # Apply font size to filename labels
    data1_file_label.configure(font=font_style)
    data2_file_label.configure(font=font_style)

# Function to load data into Treeview for Data 1
def load_data1():
    global data1
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file_path:
        data1 = pd.read_csv(file_path)
        update_treeview(data1_tree, data1)
        data1_filename.set(f"Loaded: {os.path.basename(file_path)}")

# Function to load data into Treeview for Data 2
def load_data2():
    global data2
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file_path:
        data2 = pd.read_csv(file_path)
        update_treeview(data2_tree, data2)
        data2_filename.set(f"Loaded: {os.path.basename(file_path)}")

# Function to update Treeview with Data
def update_treeview(tree, dataframe):
    tree.delete(*tree.get_children())
    tree["columns"] = list(dataframe.columns)
    for col in dataframe.columns:
        tree.heading(col, text=col, anchor="w")
        tree.column(col, anchor="w", width=100)
    for _, row in dataframe.iterrows():
        tree.insert("", "end", values=list(row))

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
        join_type_selected = join_type.get().strip().lower()

        data1.columns = data1.columns.str.strip()
        data2.columns = data2.columns.str.strip()

        join_columns = [col for col in data1.columns if col in data2.columns and col != 'name']
        join_columns_with_name = ['name'] + join_columns

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

        sort_column['values'] = list(result.columns)
        sort_column_2['values'] = list(result.columns)

        display_join_result()

def display_join_result():
    update_treeview(result_tree, result)

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

    sort_by = sort_column.get()
    sort_by_2 = sort_column_2.get()
    sort_order = sort_order_choice.get()
    ascending = True if sort_order == "Ascending" else False

    if sort_order == "Random":
        result = result.sample(frac=1).reset_index(drop=True)
    else:
        if sort_by and sort_by_2 and sort_by != sort_by_2:
            result.sort_values(by=[sort_by, sort_by_2], ascending=[ascending, ascending], inplace=True)
        elif sort_by:
            result.sort_values(by=sort_by, ascending=ascending, inplace=True)

    display_join_result()  # Refresh the Join Result display after sorting

# Export functions
def export_to_csv():
    if result.empty:
        messagebox.showwarning("No Data", "No joined data available to export.")
        return
    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if file_path:
        result.to_csv(file_path, index=False)
        messagebox.showinfo("Export Successful", f"Data exported to {file_path}")

def export_to_json():
    if result.empty:
        messagebox.showwarning("No Data", "No joined data available to export.")
        return
    file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
    if file_path:
        result.to_json(file_path, orient="records")
        messagebox.showinfo("Export Successful", f"Data exported to {file_path}")

# Create menu labels
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

# Font size adjustment buttons
increase_font_button = tk.Button(root, text="Increase Font Size", command=lambda: set_font_size(preferences["font_size"] + 1))
increase_font_button.grid(row=1, column=3, padx=5, pady=5)

decrease_font_button = tk.Button(root, text="Decrease Font Size", command=lambda: set_font_size(max(8, preferences["font_size"] - 1)))
decrease_font_button.grid(row=1, column=4, padx=5, pady=5)

# Info box for join type descriptions
join_type_text = tk.Text(root, height=3, width=50, wrap="word")
join_type_text.grid(row=2, column=0, columnspan=7, padx=5, pady=5, sticky="ew")
update_join_info()

# Frame for Data 1 and Data 2 with equal widths
data_frame = tk.Frame(root)
data_frame.grid(row=3, column=0, columnspan=7, padx=5, pady=5, sticky="ew")

# Data 1 section with Treeview, Scrollbar, and filename label
data1_frame = tk.Frame(data_frame, width=500)
data1_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
data1_file_label = tk.Label(data1_frame, textvariable=data1_filename, fg="gray", anchor="w")
data1_file_label.pack(anchor="w", padx=5)
data1_tree = ttk.Treeview(data1_frame, show='headings', style="Treeview", height=10)
data1_tree.pack(fill="both", expand=True)

data1_scrollbar = ttk.Scrollbar(data1_frame, orient="vertical", command=data1_tree.yview)
data1_tree.configure(yscrollcommand=data1_scrollbar.set)
data1_scrollbar.pack(side="right", fill="y")

# Data 2 section with Treeview, Scrollbar, and filename label
data2_frame = tk.Frame(data_frame, width=500)
data2_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
data2_file_label = tk.Label(data2_frame, textvariable=data2_filename, fg="gray", anchor="w")
data2_file_label.pack(anchor="w", padx=5)
data2_tree = ttk.Treeview(data2_frame, show='headings', style="Treeview", height=10)
data2_tree.pack(fill="both", expand=True)

data2_scrollbar = ttk.Scrollbar(data2_frame, orient="vertical", command=data2_tree.yview)
data2_tree.configure(yscrollcommand=data2_scrollbar.set)
data2_scrollbar.pack(side="right", fill="y")

# Join Result label
join_result_label = tk.Label(root, text="Join Result")
join_result_label.grid(row=5, column=0, columnspan=7, sticky="w")

# Join Result display with Treeview
result_tree = ttk.Treeview(root, show='headings', style="Treeview")
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

# Export buttons
export_csv_button = tk.Button(root, text="Export to CSV", command=export_to_csv)
export_csv_button.grid(row=8, column=0, padx=5, pady=5, sticky="w")

export_json_button = tk.Button(root, text="Export to JSON", command=export_to_json)
export_json_button.grid(row=8, column=1, padx=5, pady=5, sticky="w")

# Set initial font size from preferences
set_font_size(preferences["font_size"])

# Configure grid to expand with the window size
root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(4, weight=1)
root.grid_rowconfigure(6, weight=1)

# Bind window close event to save preferences
root.protocol("WM_DELETE_WINDOW", on_closing)

# Start Tkinter main loop
root.mainloop()
