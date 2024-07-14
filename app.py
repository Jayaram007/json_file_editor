from flask import Flask, render_template, request, redirect, flash
import json
import os

app = Flask(__name__)

# Global variable to store selected files
selected_files = []
union_name_values = set()  # Initialize the set globally

# Sample data for demonstration
run_config_files = {
    'bank_fin_nifty': 'run_config_bank_fin_nifty.json',
    'bank_nifty': 'run_config_bank_nifty.json',
    'bank': 'run_config_bank.json',
}

# Load JSON data
def load_json_data(filename):
    with open(os.path.join('run_config_files', filename), 'r') as file:
        return json.load(file)

@app.route('/')
def index():
    return render_template('index.html', run_config_files=run_config_files)

@app.route('/show_data', methods=['GET', 'POST'])
def show_data():
    global selected_files
    global union_name_values  # Include this line if not it does not work 

    if request.method == 'POST':
        selected_files = request.form.getlist('selected_files')
        union_name_values = set()

        for run_config_file in selected_files:
            data = load_json_data(run_config_files[run_config_file])
            union_name_values.update(item['name'] for item in data if item.get('editable'))

        data_for_rendering = {}
        for selected_file in selected_files:
            data = load_json_data(run_config_files[selected_file])
            data_for_rendering[selected_file] = {}
            for name in union_name_values:
                found_item = next((item for item in data if item['name'] == name and item.get('editable')), None)
                if found_item:
                    data_for_rendering[selected_file][name] = {'value': found_item['value'], 'low': found_item.get('low'), 'high': found_item.get('high')}
                else:
                    data_for_rendering[selected_file][name] = {'value': '', 'low': '', 'high': ''}

        return render_template('result.html', selected_files=selected_files, union_name_values=union_name_values, name_data=data_for_rendering, run_config_files=run_config_files)
    elif request.method == 'GET':
        return redirect('/')
    else:
        return 'Not a valid request method for this route'

@app.route('/save_changes', methods=['POST'])
def save_changes():
    global selected_files
    global union_name_values

    data_for_rendering = {file_name: {name: {'value': ''} for name in union_name_values} for file_name in selected_files}

    for run_config_file_name in selected_files:
        if f'table1_{run_config_file_name}' in request.form:
            changed_data = {}  # Dictionary to hold changed data for the run_config_file_name

            data = load_json_data(run_config_files[run_config_file_name])
            
            for name in union_name_values:
                value_key = f'{run_config_file_name}_{name}_value'
                value = request.form.get(value_key)
                low = next((float(item.get('low', float('-inf'))) for item in data if item['name'] == name), float('-inf'))
                high = next((float(item.get('high', float('inf'))) for item in data if item['name'] == name), float('inf'))

                try:
                    value = float(value)
                    if low <= value <= high:
                        changed_data[name] = {'value': value}
                    else:
                        data_for_rendering[run_config_file_name][name]['error'] = f'Value must be between {low} and {high}'
                except ValueError:
                    data_for_rendering[run_config_file_name][name]['error'] = f'Invalid value'

            file_path = os.path.join('run_config_files', run_config_files[run_config_file_name])
            with open(file_path, 'r') as json_file:
                data = json.load(json_file)
                for item in data:
                    name = item['name']
                    if name in changed_data:
                        item['value'] = changed_data[name]['value']

            with open(file_path, 'w') as json_file:
                json.dump(data, json_file, indent=4)
    
    # After processing the form data, perform a redirect to the same page
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)