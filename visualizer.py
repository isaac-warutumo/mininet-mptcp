from flask import Flask, render_template_string, jsonify
import pandas as pd

app = Flask(__name__)

template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>File Transfer Time Table</title>
    <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f8f9fa;
        }
        .container {
            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;  
            margin-top: 50px;
        }
        .table {
            border: 1px solid #dee2e6;
        }
        .table th {
            text-align: center;
            background-color: #343a40;
            color: white;
        }
        td {
            border: none !important;
        }
        .parameter-column {
            background-color: #343a40;
            color: white;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h2 class="text-center mb-4">MPTCPv1 | File Transfer Time Table</h2>
        <table id="data-table" class="table table-striped table-hover"></table>
    </div>
    <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.9.3/dist/umd/popper.min.js"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
    <script>

        function get_color(value, min_value, max_value) {
            let middle_value = 100;
            let r, g, b;

            if (value < middle_value) {
                value = 1 - ((middle_value - value) / (middle_value - min_value));
                r = 255;
                g = Math.floor(255 * value);
            } else if (value > 100) {
                value = 1 - ((value - middle_value) / (max_value - middle_value));
                r = Math.floor(255 * value);
                g = 255;
            } else {
                r = 255;
                g = 255;
            }

            b = 0;
            return `rgb(${r}, ${g}, ${b})`;
        }

        function buildTable(columns, data) {
            let html = '';
            const totalColumns = columns.length;

            html += '<thead>';
            html += '<tr>';
            html += `<th colspan="3">Parameters</th>`;
            html += `<th colspan="${totalColumns - 3}">Network Conditions</th>`;
            html += '</tr>';

            // Merging column headers with the same name and also span over empty cells
            html += '<tr>';
            let prevCol = null;
            let colSpanCount = 1;

            for (let i = 0; i < columns.length; i++) {
                const col = columns[i] === "None" ? "" : columns[i];
                
                if (prevCol === col || col === "") {
                    colSpanCount++;
                } else {
                    if (prevCol) {
                        html += `<th colspan="${colSpanCount}">${prevCol}</th>`;
                    }
                    colSpanCount = 1;
                }
                
                if (i === columns.length - 1 && col) {
                    html += `<th colspan="${colSpanCount}">${col}</th>`;
                }
                
                if (col !== "") {
                    prevCol = col;
                }
            }

            html += '</tr>';

            if (data.length > 0) {
                const firstRow = data[0];
                html += '<tr>';
                firstRow.forEach((cell) => {
                    html += `<th>${cell === "None" ? "" : cell}</th>`;
                });
                html += '</tr>';
            }
            
            html += '</thead>';

            // Add data rows
            html += '<tbody>';
            let numericData = data.slice(1).map(row => row.slice(3)).flat().map(Number).filter(cell => !isNaN(cell));
            let min_value = Math.min(...numericData);
            let max_value = Math.max(...numericData);
            console.log(min_value, max_value);
            for (let rowIndex = 1; rowIndex < data.length; rowIndex++) {
                const row = data[rowIndex];
                html += '<tr>';
                row.forEach((cell, cellIndex) => {
                    let style = "";
                    if ((cellIndex + 1) > 3 && !isNaN(cell)) {  // adjust based on your real index
                        const color = get_color(parseFloat(cell), min_value, max_value);
                        style = `style="background-color:${color};"`;
                    }

                    if ((cellIndex + 1) <= 3) {  
                        html += `<td class="parameter-column" ${style}>${cell === "None" ? "" : cell}</td>`;
                    } else {
                        html += `<td ${style}>${cell === "None" ? "" : cell}</td>`;
                    }
                });
                html += '</tr>';
            }
            html += '</tbody>';

            $("#data-table").html(html);
        }

        function fetch_data() {
            return new Promise((resolve, reject) => {
                $.getJSON("/data", function(data) {
                    resolve();
                    buildTable(data['columns'], data['data']);
                }).fail(function() {
                    console.log('Error occurred fetching data.');
                    reject();
                });
            });
        }

        $(document).ready(function() {
            // Try to fetch immediately
            fetch_data().catch((err) => console.log(err));

            // Then keep trying to fetch every 5000 ms
            setInterval(() => {
                fetch_data().catch((err) => console.log(err));
            }, 5000);
        });

    </script>
</body>
</html>
'''

@app.route("/")
def home():
    return render_template_string(template)

@app.route("/data")
def get_data():
    # Read the CSV file without headers
    df = pd.read_csv('data.csv', header=None)
    df = df.fillna('None')

    # Assign new headers based on unique entries in the first row
    headers = []
    for col in df.iloc[0]:
        if headers.count(col) > 0:
            headers.append(col)  # keep duplicate as is
        else:
            headers.append(col if 'Unnamed' not in col else 'None')

    # Set new headers and drop the first row
    df.columns = headers
    df = df[1:]

    # Convert DataFrame to list of lists and list of columns
    data = df.values.tolist()
    columns = df.columns.values.tolist()

    return jsonify({'columns': columns, 'data': data})

if __name__ == "__main__":
    app.run(debug=True)