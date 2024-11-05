import base64
import io
import dash_bootstrap_components as dbc
from dash import Dash, dcc, html, dash_table, Input, Output, State, no_update
import plotly.express as px
import pandas as pd

# ایجاد برنامه Dash با استفاده از تم Flatly
app = Dash(__name__, suppress_callback_exceptions=True)

# طرح‌بندی اصلی صفحه
app.layout = dbc.Container([
    dcc.Store(id='memory-stored-data', storage_type='memory'),  # ذخیره داده‌ها در حافظه مرورگر
    # dbc.Row([navbar]),
    dbc.Row([
        html.H1(['Welcome to Our Data Visualization and Analysis Tool!'], style={'textAlign': 'center'}),
        dcc.Upload(id='file-upload',
            children=html.Div([html.P('Drag and Drop or   '), html.Button('Select File')], className='uplode-section')),            
    ], id='Row_update'),

    html.Div(id='data-upload-output', children=[]),
], fluid=True)

# پردازش و بارگذاری فایل‌های CSV و Excel
@app.callback(
    Output('data-upload-output', 'children'),
    Output('Row_update', 'style'),
    Output('memory-stored-data', 'data'),
    Input('file-upload', 'contents'),
    State('file-upload', 'filename'),
    State('file-upload', 'last_modified'),
    State('data-upload-output', 'children'),
    prevent_initial_call=True
)
def update_output(contents, filename, date, children):
    if contents is not None:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        try:
            # بارگذاری فایل CSV یا Excel
            if 'csv' in filename:
                df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            elif 'xls' in filename:
                df = pd.read_excel(io.BytesIO(decoded))

            # حذف ستون‌هایی با بیش از ۹۰ درصد داده‌های خالی
            threshold = int(0.9 * len(df))
            df = df.dropna(axis=1, thresh=threshold)

            # به‌روزرسانی خروجی با فایل آپلود شده
            children.append(
                dbc.Container([
                    dbc.Row([
                        html.H3([f"File name: {filename.split('.')[0]}"], style={'textAlign': 'center'}),
                        html.H4(f"Total Rows = {len(df)}"),
                        html.H4(f"Total Columns = {len(df.columns)}"),
                        html.H4([f"Columns: {' - '.join(df.columns)}"], className='wrap-text')
                    ], id='Row_info'),
                    html.Hr(),
                    dbc.Row([
                        dbc.Row([
                            dbc.Col([dcc.Dropdown(
                                    options=[{'label': col, 'value': col} for col in df.columns],
                                    value=[df.columns[0]],
                                    id='column-dropdown',
                                    multi=True,
                                    searchable=True
                                )]),
                            dbc.Col([dcc.Dropdown(
                                    id='chart-type-dropdown',
                                    options=[
                                        {'label': 'Histogram', 'value': 'hist'},
                                        {'label': 'Scatter-Chart', 'value': 'scatter'},
                                        {'label': 'Bar-Chart', 'value': 'bar'},
                                        {'label': 'Pie-Chart', 'value': 'pie'},
                                        {'label': 'Sunburst-Chart', 'value': 'sun'}],
                                    value='hist'
                            )])
                        ], id='Row_select'),
                        dbc.Row([
                            dbc.Col([
                                dbc.Row([dash_table.DataTable(
                                        id='data-table',
                                        page_size=5,
                                        column_selectable='multi',
                                        selected_columns=[],
                                        editable=False,
                                        filter_action="native",
                                        sort_action="native",
                                        sort_mode="multi",
                                        style_header={ 'textAlign': 'center' },
                                        style_cell={'textAlign': 'center'},
                                        tooltip_data=[
                                            {column: {'value': str(value), 'type': 'markdown'} for column, value in row.items()}
                                            for row in df.to_dict('records')
                                        ],
                                        tooltip_duration=None,
                                        style_data={'whiteSpace': 'normal'},
                                    )])
                            ], id='col-tabel'),
                            dbc.Col([
                                dbc.Row([
                                    dbc.Col([dcc.Graph(id='graph-display')], id='chart'),
                                    dbc.Col([html.H4("Options", style={'textAlign': 'center'}),
                                        dcc.Checklist(
                                        id='chart-options-checklist',
                                        options=[{'label': 'Color', 'value': 'color'}],
                                        value=['color']
                                    )], id='option')
                                ], id='Row-chart'),
                                dbc.Row([
                                    dbc.Row(id='row_color_picker', children=[dcc.RadioItems(id='color-picker', options=[])], style={'display': 'none'}),
                                    dbc.Row(id='row_range_slider',children=[
                                        dcc.Slider(id='range-slider', min=10, max=50),
                                        dbc.Row([
                                            html.H4("Set Histogram Bins Parameters:"),
                                            dbc.Col(dcc.Input(id='min-input', type='number', placeholder='Min', style={'width': '30%'})),
                                            dbc.Col(dcc.Input(id='max-input', type='number', placeholder='Max', style={'width': '30%'})),
                                            dbc.Col(dcc.Input(id='step-input', type='number', placeholder='Step', style={'width': '30%'})),
                                            dbc.Col(html.Button('Apply', id='apply-button', n_clicks=0))])],
                                        style={'display': 'none'}),
                                    dbc.Row(id='row_color_column', children=[dcc.RadioItems(id='color_column', options=[], inline=True),], style={'display': 'none'}),
                                    dbc.Row(id='row_bar_mode', children=[dcc.RadioItems(id='bar_mode', options=[], inline=True),], style={'display': 'none'}),
                                    dbc.Row(id='row_color_plot', children=[dcc.Dropdown(id='color_plot', options=[])], style={'display': 'none'})
                                ],id='chart-tool')
                            ], id='col-chart')
                        ], id='Row-chart-tabel'),
                    ], id='Row_main'),
                ])
            )
        except Exception as e:
            print(e)
            return html.Div(['There was an error processing this file.'])
        
        return children, {'display': 'none'}, df.to_dict('records')
    else:
        return "", no_update, no_update

# به‌روزرسانی جدول با ستون‌های انتخاب شده
@app.callback(
    Output('data-table', 'columns'),
    Output('data-table', 'data'),
    Input('column-dropdown', 'value'),
    State('memory-stored-data', 'data')
)
def update_table(selected_columns, stored_data):
    if stored_data is None:
        return no_update, no_update
    
    df = pd.DataFrame(stored_data)
    filtered_df = df[selected_columns]

    return [{"name": col, "id": col, "selectable": True} for col in selected_columns], filtered_df.to_dict('records')
# به‌روزرسانی گزینه‌های نمودار با توجه به نوع نمودار
@app.callback(
    Output('chart-options-checklist', 'options'),
    Output('chart-options-checklist', 'value'),
    Input('chart-type-dropdown', 'value')
)
def update_chart_options(chart_type):
    # تعریف گزینه‌های مختلف برای هر نوع نمودار
    if chart_type == 'hist':
        return [{'label': 'RangeSlider', 'value': 'RangeSlider'}, {'label': 'Color', 'value': 'Color'}], ['RangeSlider', 'Color']
    elif chart_type == 'bar':
        return [{'label': 'Color Column', 'value': 'colorColumn'}, {'label': 'Bar mode', 'value': 'Bar-mode'}], ['colorColumn', 'Bar-mode']
    elif chart_type == 'scatter':
        return [{'label': 'Color', 'value': 'Color'}], ['Color']
    elif chart_type == 'sun':
        return [{'label': 'Color plot', 'value': 'Color_plot'}, {'label': 'Color Column', 'value': 'colorColumn'}], ['Color_plot', 'colorColumn']
    else:
        return [], []

# به روز رسانی ابزار اسلایدر برای تعیین میزان بینز ها
@app.callback(
    [
        Output('row_range_slider', 'style'),
        Output('range-slider', 'min'),
        Output('range-slider', 'max'),
        Output('range-slider', 'step')
    ],
    [Input('chart-options-checklist', 'value'),
     Input('apply-button', 'n_clicks')],  # ورودی دکمه برای فراخوانی
    [State('min-input', 'value'), State('max-input', 'value'), State('step-input', 'value')]
)
def update_range_slider(selected_options,n_clicks, min_val, max_val, step_val):
    if 'RangeSlider' in selected_options:
        row_slider_style = {'display': 'flex'}
        # اگر کاربر مقادیری وارد نکرده باشد، از مقادیر پیش‌فرض استفاده می‌شود
        min_val = min_val if min_val is not None else 50
        max_val = max_val if max_val is not None else 200
        step_val = step_val if step_val is not None else 10
        return row_slider_style, min_val, max_val, step_val
    return {'display': 'none'}, no_update, no_update, no_update  # مخفی‌کردن اسلایدر

# به روز رسانی ابزار رنگ برای شخصی سازی نمودار ها
@app.callback(
    [
        Output('row_color_picker', 'style'),
        Output('color-picker', 'options')
    ],
    [Input('chart-options-checklist', 'value')]
)
def update_color_picker(selected_options):
    if 'Color' in selected_options:
        color_options = [{'label': color, 'value': color} for color in ['red', 'green', 'blue', 'black']]
        return {'display': 'flex'}, color_options  # نمایش و تنظیم گزینه‌های رنگ
    return {'display': 'none'}, no_update  # مخفی‌کردن انتخاب رنگ

# به روز رسانی مدل نمودار بار
@app.callback(
        [
            Output('row_bar_mode', 'style'),
            Output('bar_mode', 'options'),
            Output('bar_mode', 'value')
        ],
        Input('chart-options-checklist', 'value'),
)
def update_bar_mode(selected_options):
    if 'Bar-mode' in selected_options:
        bar_options = [{'label': mode, 'value': mode} for mode in ['relative', 'group', 'overlay']]
        value = 'relative'
        return {'display': 'flex'}, bar_options, value
    return {'display': 'none'}, no_update, no_update

# به روز رسانی ستون رنگ در نمودار
@app.callback(
        [
            Output('row_color_column', 'style'),
            Output('color_column', 'options')
        ],
        Input('chart-options-checklist', 'value'),
        Input('data-table', 'derived_virtual_data'),
)
def update_color_column(selected_options,data):
    df = pd.DataFrame(data)
    if 'colorColumn' in selected_options:
        color_column = [{'label': column, 'value': column} for column in df.columns]
        return {'display': 'flex'}, color_column
    return {'display': 'none'}, no_update

# به روز رسانی باکس رنگ
@app.callback(
        [
            Output('row_color_plot', 'style'),
            Output('color_plot', 'options'),
            Output('color_plot', 'value'),
        ],
        Input('chart-options-checklist', 'value'),
)
def update_color_plot(selected_options):
    if 'Color_plot' in selected_options:
        color_plot = [{'label': 'Dark2', 'value': 'Dark2'},
                      {'label': 'Set3', 'value': 'Set3'},
                      {'label': 'T10', 'value': 'T10'},
                      {'label': 'Plotly', 'value': 'Plotly'}]
        return {'display': 'flex'}, color_plot, 'Plotly'
    return {'display': 'none'}, no_update, no_update

# به‌روزرسانی و ایجاد نمودار
@app.callback(
    Output('graph-display', 'figure'),
    [
        Input('chart-type-dropdown', 'value'),
        Input('data-table', 'selected_columns'),
        Input('data-table', 'derived_virtual_data'),
        Input('color-picker', 'value'),
        Input('range-slider', 'value'),
        Input('bar_mode', 'value'),
        Input('color_column', 'value'),
        Input('color_plot', 'value')
    ],
    
    prevent_initial_call=True
)
def update_chart(
    chart_type, selected_columns, filtered_data, selected_color, range_value, barmode_value, color_column_value, color_plot_valye
    ):
    if len(selected_columns) == 0:
        return no_update

    df = pd.DataFrame(filtered_data)
    selected_data = df[selected_columns]

    # تنظیم نوع نمودار بر اساس انتخاب کاربر
    if chart_type == 'pie' and len(selected_columns) == 1:
        return px.pie(selected_data, names=selected_columns[0])
    elif chart_type == 'hist' and len(selected_columns) == 1:
        fig = px.histogram(selected_data, x=selected_columns[0])
        fig.update_traces(marker=dict(color=selected_color), nbinsx=range_value)
        return fig
    elif chart_type == 'scatter' and len(selected_columns) == 2:
        return px.scatter(selected_data, x=selected_columns[0], y=selected_columns[1]).update_traces(marker=dict(color=selected_color))
    elif chart_type == 'bar' and len(selected_columns) >= 2:
        fig = px.bar(df, x=selected_columns[0], y=selected_columns[1], color=color_column_value)
        fig.update_traces(marker=dict(color=selected_color))
        fig.update_layout(barmode=barmode_value)
        return fig
    elif chart_type == 'sun' and len(selected_columns) >= 1:
        if 'Dark2' in color_plot_valye:
            color_sequence = px.colors.qualitative.Dark2
        elif 'Set3' in color_plot_valye:
            color_sequence = px.colors.qualitative.Set3
        elif 'T10' in color_plot_valye:
            color_sequence = px.colors.qualitative.T10
        elif 'Plotly' in color_plot_valye:
            color_sequence = px.colors.qualitative.Plotly            
        return px.sunburst(selected_data, path=[selected_columns[i] for i in range(len(selected_columns))],
                           color=color_column_value,
                           color_discrete_sequence=color_sequence)
    
    return px.scatter(title="Invalid chart configuration")

# اجرای سرور برنامه
if __name__ == '__main__':
    app.run_server(debug=True)
