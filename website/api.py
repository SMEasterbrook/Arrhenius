from flask import jsonify
from website import app

from core.output_config import ReportDatatype
from data.provider import PROVIDERS


var_name_to_output_type = {
    output_type.value: output_type for output_type in ReportDatatype
}

example_config = {
    "co2": {
        "from": [1],
        "to": [0.67, 1.0, 1.5, 2.0, 2.5, 3.0]
    },
    "year": "1895",
    "grid": {
        "dims": {
            "lat": "(0, 180]",
            "lon": "(0, 360]"
        },
        "repr": ["count", "width"]
    },
    "num_layers": "[1, ...)",
    "num_iters": "[1, ...)",
    "aggregate_lat": ["before", "after", None],
    "aggregate_level": ["before", "after"],
    "temp_src": [func_name for func_name in PROVIDERS['temperature']],
    "humidity_src": [func_name for func_name in PROVIDERS['humidity']],
    "albedo_src": [func_name for func_name in PROVIDERS['albedo']],
    "absorbance_src": ["table"],
    "CO2_weight": ["closest", "low", "high", "mean"],
    "H2O_weight": ["closest", "low", "high", "mean"],
}


@app.route('/model/help', methods=['GET'])
def config_options():
    """
    Returns a response to an HTTP request for example configuration options.
    If the request is a GET request, the response contains a template for
    a configuration dictionary, most of the keys of which point to strings
    or lists that specify the range of values acceptable for that key.

    :return:
        An HTTP response containing an example configuration dictionary.
    """
    return jsonify(example_config), 200
