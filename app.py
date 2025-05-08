from dash import Dash, dcc, html, Input, Output, State, ctx, ALL
import plotly.express as px
import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error
import importlib.util
import urllib.request


# Helper function to load remote Python module
def load_remote_module(url, module_name):
    response = urllib.request.urlopen(url)
    code = response.read().decode("utf-8")
    spec = importlib.util.spec_from_loader(module_name, loader=None)
    module = importlib.util.module_from_spec(spec)
    exec(code, module.__dict__)
    return module


# Load remote modules for computation
functions_url = "https://raw.githubusercontent.com/DS4Ag/dpest/main/dpest/functions.py"
functions = load_remote_module(functions_url, "functions")


# Compute RMSE by grouping
def compute_grouped_rmse(df, group_cols):
    def rmse(y_true, y_pred):
        return np.sqrt(mean_squared_error(y_true, y_pred))

    grouped_rmse = df.groupby(group_cols)[['value_measured', 'value_simulated']].apply(
        lambda g: rmse(g['value_measured'], g['value_simulated'])).reset_index(name='rmse')
    return grouped_rmse


# Initialize Dash app
app = Dash(__name__)

# Read data (this part should be adapted to your needs)
# Load your overview_data here, assuming it's ready
overview_data = pd.read_csv('overview_data.csv')

# Compute RMSE
rmse_data = compute_grouped_rmse(overview_data,
                                 ['variable', 'calibration_method', 'short_label', 'long_label', 'treatment'])

# Layout of the Dash app
app.layout = html.Div(style={'font-family': 'Arial', 'padding': '20px'}, children=[

    # Header Section
    html.Div(style={'backgroundColor': '#343a40', 'padding': '20px', 'color': '#ffffff'}, children=[
        html.H1('RMSE Analysis Dashboard', style={'textAlign': 'center'}),
        html.P('Visualizing RMSE values by different variables and treatments', style={'textAlign': 'center'})
    ]),

    # Filters Section (if needed for your dashboard)
    html.Div(style={'display': 'flex', 'marginTop': '20px'}, children=[
        html.Div(style={'width': '25%', 'padding': '20px', 'backgroundColor': '#f8f9fa',
                        'borderRadius': '10px', 'boxShadow': '0px 4px 6px rgba(0,0,0,0.1)', 'marginBottom': '10px'},
                 children=[
                     html.H3('Filters'),
                     html.Label('Select Variable:'),
                     dcc.Dropdown(
                         id='variable-dropdown',
                         options=[{'label': var, 'value': var} for var in rmse_data['variable'].unique()],
                         value=rmse_data['variable'].unique()[0],
                         style={'marginBottom': '20px'}
                     ),
                     html.Label('Select Calibration Method:'),
                     dcc.Dropdown(
                         id='calibration-method-dropdown',
                         options=[{'label': method, 'value': method} for method in
                                  rmse_data['calibration_method'].unique()],
                         value=rmse_data['calibration_method'].unique()[0],
                         style={'marginBottom': '20px'}
                     ),

                    dcc.Checklist(
                        id='short-label-checklist',
                        options=[{'label': label, 'value': label} for label in overview_data['short_label'].unique()],
                        value=overview_data['short_label'].unique().tolist(),  # Default to all short_labels selected
                        inline=False,  # Ensures the checkboxes are stacked vertically instead of horizontally
                        style={'marginBottom': '20px', 'display': 'block'}  # Make each checkbox appear on a new line
                    ),

                 ]),

        # Chart Section
        html.Div(style={'width': '75%', 'paddingLeft': '20px'}, children=[
            dcc.Loading(
                id="loading-graphs",
                type="circle",
                children=html.Div(id='charts-container', style={
                    "display": "flex",
                    "flexDirection": "column",
                    "gap": "30px",
                    "width": "100%"
                })
            )
        ])
    ])
])


# Define the callback to update the heatmap
@app.callback(
    Output('charts-container', 'children'),
    [Input('variable-dropdown', 'value'),
     Input('calibration-method-dropdown', 'value'),
     Input('short-label-checklist', 'value')]  # Add checklist to inputs
)
def update_heatmap(selected_variable, selected_method, selected_short_labels):
    # Filter data based on selected values
    filtered_data = rmse_data[(rmse_data['variable'] == selected_variable) &
                              (rmse_data['calibration_method'] == selected_method) &
                              (rmse_data['short_label'].isin(selected_short_labels))]  # Apply short_label filter

    # Pivot data for heatmap
    pivot_table = filtered_data.pivot(index='treatment', columns='short_label', values='rmse')

    # Round the RMSE values to 1 decimal
    rounded_values = pivot_table.round(2)

    # Create heatmap
    fig = px.imshow(rounded_values, labels=dict(x="Calibration Settings", y="Treatment", color="RMSE"),
                    color_continuous_scale='YlGnBu', title=f'RMSE for {selected_variable}', text_auto=True)

    # Update layout settings
    fig.update_layout(
        xaxis_title="Calibration Settings",
        yaxis_title="Treatment",
        font=dict(size=14),
        height=600,
        xaxis=dict(tickmode='linear'),
        yaxis=dict(tickmode='linear'),
    )

    fig = px.imshow(
        pivot_table,
        labels=dict(x="Calibration Settings", y="Treatment", color="RMSE"),
        color_continuous_scale='YlGnBu',
        title=f'RMSE for {selected_variable}',
        aspect="auto"
    )

    return [dcc.Graph(figure=fig)]


# Run the app
if __name__ == '__main__':
    app.run(debug=False
            )
