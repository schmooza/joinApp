import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd

# Initialize Tkinter window
root = tk.Tk()
root.title("Data Join App")

# Initialize variables for datasets
data1 = pd.DataFrame()
data2 = pd.DataFrame()
result = pd.DataFrame()  # Placeholder for the join result

# Function to load data from CSV for Data 1
def load_data1():
    global data1
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file_path:
        data1 = pd.read_csv(file_path)
        data1_text.delete(1.0, tk.END)
        data1_text.insert(tk.END, data1.to_string(index=False))

# Function to load data from CSV for Data 2
def load_data2():
    global data2
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file_path:
        data2 = pd.read_csv(file_path)
        data2_text.delete(1.0, tk.END)
        data2_text.insert(tk.END, data2.to_string(index=False))

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
            # Perform a Cross Join workaround
            data1['_key'] = 1
            data2['_key'] = 1
            result = data1.merge(data2, on='_key').drop(columns=['_key'])
            data1.drop(columns=['_key'], inplace=True)
            data2.drop(columns=['_key'], inplace=True)
        else:
            # Perform the join with suffixes for other join types
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
        if result.columns.any():
            sort_column.set(result.columns[0])  # Default to the first column for sorting

        # Clear previous Treeview contents
        for item in result_tree.get_children():
            result_tree.delete(item)

        # Set Treeview columns with a fixed total width of 400 pixels
        result_tree["columns"] = list(result.columns)
        column_width = 400 // len(result.columns) if len(result.columns) > 0 else 400  # Adjust column width
        for col in result.columns:
            result_tree.heading(col, text=col)
            result_tree.column(col, width=column_width, anchor="center")

        # Insert rows into Treeview
        for _, row in result.iterrows():
            row_values = [row[col] for col in result.columns]
            result_tree.insert("", "end", values=row_values)

# Function to sort the join result based on the selected columns and order
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

    # Clear previous Treeview contents
    for item in result_tree.get_children():
        result_tree.delete(item)

    # Insert sorted rows into Treeview
    for _, row in result.iterrows():
        row_values = [row[col] for col in result.columns]
        result_tree.insert("", "end", values=row_values)

# Function to update join type information
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

# Function to export the join result
def export_data():
    if result.empty:
        messagebox.showwarning("No Data", "No joined data available to export.")
        return

    export_format = export_format_choice.get()
    file_path = filedialog.asksaveasfilename(defaultextension=f".{export_format.lower()}",
                                             filetypes=[(f"{export_format} files", f"*.{export_format.lower()}")])

    if file_path:
        try:
            if export_format == "CSV":
                result.to_csv(file_path, index=False)
            elif export_format == "JSON":
                result.to_json(file_path, orient="records")
            messagebox.showinfo("Export Successful", f"Data successfully exported as {export_format}!")
        except Exception as e:
            messagebox.showerror("Export Error", f"An error occurred during export: {e}")

# Load Data and Join buttons at the top left of the Join Result box

# Load Data 1 button
load_data1_button = tk.Button(root, text="Load Data 1", command=load_data1)
load_data1_button.grid(row=0, column=0, padx=5, pady=5, sticky="w")

# Load Data 2 button
load_data2_button = tk.Button(root, text="Load Data 2", command=load_data2)
load_data2_button.grid(row=0, column=1, padx=5, pady=5, sticky="w")

# Join type selection
tk.Label(root, text="Join Type").grid(row=1, column=0, sticky="w")
join_type = ttk.Combobox(root, values=["Inner", "Left", "Right", "Outer", "Cross"])
join_type.set("Inner")
join_type.bind("<<ComboboxSelected>>", update_join_info)
join_type.grid(row=1, column=1, sticky="w")

# Join button
join_button = tk.Button(root, text="Join Data", command=join_data)
join_button.grid(row=1, column=2, padx=5, pady=5, sticky="w")

# Info box for join type descriptions
join_type_text = tk.Text(root, height=3, width=50, wrap="word")
join_type_text.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="w")
update_join_info()

# Data 1 display box
tk.Label(root, text="Data 1").grid(row=3, column=0, sticky="w")
data1_text = tk.Text(root, height=10, width=30)
data1_text.grid(row=4, column=0, padx=5, pady=5, sticky="w")

# Data 2 display box
tk.Label(root, text="Data 2").grid(row=3, column=1, sticky="w")
data2_text = tk.Text(root, height=10, width=30)
data2_text.grid(row=4, column=1, padx=5, pady=5, sticky="w")

# Sort options for Join Result
tk.Label(root, text="Sort By").grid(row=5, column=0, sticky="w")
sort_column = ttk.Combobox(root, values=[], state="readonly")
sort_column.grid(row=5, column=1, sticky="w")

tk.Label(root, text="Then By").grid(row=5, column=2, sticky="w")
sort_column_2 = ttk.Combobox(root, values=[], state="readonly")
sort_column_2.grid(row=5, column=3, sticky="w")

# Sort order choice dropdown
tk.Label(root, text="Order").grid(row=5, column=4, sticky="w")
sort_order_choice = ttk.Combobox(root, values=["Ascending", "Descending", "Random"])
sort_order_choice.set("Ascending")
sort_order_choice.grid(row=5, column=5, sticky="w")

# Sort button
sort_button = tk.Button(root, text="Sort Data", command=sort_result)
sort_button.grid(row=5, column=6, padx=5, pady=5, sticky="w")

# Join Result display with Treeview
tk.Label(root, text="Join Result").grid(row=6, column=0, columnspan=3, sticky="w")
result_tree = ttk.Treeview(root, show='headings')
result_tree.grid(row=7, column=0, columnspan=7, padx=5, pady=5, sticky="w")

# Export format choice dropdown
tk.Label(root, text="Export Format").grid(row=8, column=0, sticky="w")
export_format_choice = ttk.Combobox(root, values=["CSV", "JSON"])
export_format_choice.set("CSV")
export_format_choice.grid(row=8, column=1, sticky="w")

# Export button
export_button = tk.Button(root, text="Export Data", command=export_data)
export_button.grid(row=8, column=2, padx=5, pady=5, sticky="w")

# Start Tkinter main loop
root.mainloop()
