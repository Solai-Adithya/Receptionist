"""Route declaration."""
from flask import current_app as app
from flask import render_template


@app.route('/')
def home():
    """Landing page."""
    table_ = [
        {'Course': 'CS 309', 'Giving/Taking': 'Taking',
            'Date': '25-07-2021', 'Time': '1000'}
    ]
    return render_template(
        'home.html',
        table=table_,
    )
