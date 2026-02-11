import json
import pandas as pd

with open('results/test_latency_cost_results.json', 'r') as f:
    data = json.load(f)

df = pd.DataFrame(data)

html = """
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.4/css/jquery.dataTables.min.css">
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.4/js/jquery.dataTables.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { width: 100%; }
    </style>
</head>
<body>
    <h1>Bedrock Model Performance Results</h1>
""" + df.to_html(index=False, table_id='results') + """
    <script>
        $(document).ready(function() {
            $('#results').DataTable({
                pageLength: 25,
                order: [[1, 'asc']]
            });
        });
    </script>
</body>
</html>
"""

with open('results/results_table.html', 'w') as f:
    f.write(html)

print("Interactive table created: results/results_table.html")
