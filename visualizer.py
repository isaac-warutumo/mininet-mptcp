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
            margin-top: 50px;
        }
        th, td {
            text-align: center;
        }
        .table {
            border: 1px solid #dee2e6;
        }
        .table th {
            background-color: #343a40;
            color: white;
        }
        .table-warning {
            background-color: #ffe08a;
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

        function buildTable(columns, data) {
            let html = '';
            const totalColumns = columns.length;

            html += '<thead>';
            html += '<tr>';
            html += `<th colspan="3">Parameters</th>`;
            html += `<th colspan="${totalColumns - 3}">Network Conditions</th>`;
            html += '</tr>';
            
            // Add the column headers with colspan
            html += '<tr>';
            
            let prevCol = null;
            let colSpanCount = 1;

            for (let i = 0; i < columns.length; i++) {
                const col = columns[i] === "None" ? "" : columns[i];

                if (prevCol === col) {
                    colSpanCount++;
                    continue;
                } else {
                    if (prevCol !== null) {
                        html += `<th colspan="${colSpanCount}">${prevCol}</th>`;
                    }

                    prevCol = col;
                    colSpanCount = 1;
                }
            }
            
            // Handle last column header
            if (prevCol !== null) {
                html += `<th colspan="${colSpanCount}">${prevCol}</th>`;
            }

            html += '</tr>';
            html += '</thead>';

            // Add data rows
            html += '<tbody>';

            data.forEach((row) => {
                html += '<tr>';

                colSpanCount = 1;  // Resetting for data rows
                for (let i = 0; i < row.length; i++) {
                    if (row[i] === "None") {
                        colSpanCount++;
                        continue;
                    }
                    
                    if (colSpanCount > 1) {
                        html += `<td colspan="${colSpanCount}"></td>`;
                        colSpanCount = 1;
                    }

                    html += `<td>${row[i]}</td>`;
                }

                // Handle trailing empty cells
                if (colSpanCount > 1) {
                    html += `<td colspan="${colSpanCount}"></td>`;
                }

                html += '</tr>';
            });

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