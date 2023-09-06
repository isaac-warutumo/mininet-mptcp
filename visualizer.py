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
        <h2 class="text-center mb-4">File Transfer Time Table</h2>
        <table id="data-table" class="table table-striped table-hover"></table>
    </div>
    <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.9.3/dist/umd/popper.min.js"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
    <script>
        function buildTable(columns, data) {
            let html = '';
            html += '<thead>';
            columns.forEach((col, index) => {
                const colspan = index < 3 ? 1 : 3;
                html += '<th colspan="' + colspan + '">' + col + '</th>';
            });
            html += '</thead>';

            html += '<tbody>';
            data.forEach((row) => {
                html += '<tr>';
                row.forEach((cell, index) => {
                    const klass = index >= 3 && (cell == 99.6 || cell == 99.5) ? ' class="table-warning"' : '';
                    html += '<td' + klass + '>' + cell + '</td>';
                });
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
            fetch_data().then(() => {
                setInterval(fetch_data, 5000);
            }).catch((err) => console.log(err));
        });
    </script>
</body>
</html>
'''

@app.errorhandler(500)
def internal_error(exception):
    app.logger.error(exception)
    return render_template_string('<p>An internal server error occurred.</p>'), 500

@app.route("/")
def home():
    return render_template_string(template)

@app.route("/data")
def get_data():
    df = pd.read_csv('data.csv')
    df = df.fillna('None')  
    data = df.values.tolist()
    columns = df.columns.values.tolist()
    return jsonify({'columns': columns, 'data': data})

if __name__ == "__main__":
    app.run(debug=True)