from flask import Flask, render_template
import pymysql
import pandas as pd
from bokeh.plotting import figure
from bokeh.models.sources import ColumnDataSource
from bokeh.layouts import layout, row
from bokeh.models import DatetimeTickFormatter, HoverTool, Toggle
from bokeh.resources import CDN
from bokeh.embed import file_html
from config import db_params

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.options.display.expand_frame_repr = False
app = Flask(__name__, template_folder='template')


def get_data():
    result = None
    with pymysql.connect(**db_params, cursorclass=pymysql.cursors.DictCursor) as connection:
        sql = 'SELECT * FROM taxi_stats ORDER BY ts ASC'
        result = pd.read_sql(sql, connection, index_col='ts')
    return result


def handle_data(df):
    df = df.resample("5Min", ).median()
    df['dw'] = df.index.dayofweek + 1
    mask = df.dw <= 5
    work_df = df[mask]
    holi_df = df[~mask]
    work_df = work_df.groupby(work_df.index.time).median()
    holi_df = holi_df.groupby(holi_df.index.time).median()
    return work_df, holi_df


def get_chart(df):
    pr_to_color = '#0099FF'
    pr_from_color = '#FF9900'

    fig = figure(x_axis_type='datetime',
                 title=f'График изменения стоимости поездки в течение дня',
                 active_scroll="wheel_zoom", toolbar_location="above")
    fig.yaxis.axis_label = "Цена поездки, руб."
    fig.xaxis.axis_label = "Время"
    fig.xaxis.axis_label_text_font_size = "12pt"
    fig.xaxis.major_label_text_font_size = "12pt"
    fig.yaxis.axis_label_text_font_size = "12pt"
    fig.yaxis.major_label_text_font_size = "12pt"
    fig.ygrid.grid_line_alpha = 0.1
    fig.xaxis.formatter = DatetimeTickFormatter(
        hourmin=["%H:%M"],
        hours=["%H:%M"],
        days=["%d.%m.%Y"],
        months=["%d.%m.%Y"],
        years=["%d.%m.%Y"],
    )
    # ---------------------------- Цена на работу ---------------------------
    pr_to = ColumnDataSource()
    pr_to.data = dict(x=df.index, y=df.to_price)

    pr_to_line_layer = fig.line(x="x", y="y", source=pr_to, line_color=pr_to_color, alpha=0.9, line_width=3)
    pr_to_hover_tool = HoverTool(
        syncable=False,
        renderers=[pr_to_line_layer],
        tooltips=[('Время', '@x{%H:%M}'),
                  ('Цена на работу', '@y{*}руб.')],
        formatters={'@x': 'datetime',
                    '@y': 'numeral'},
        mode='vline')
    fig.add_tools(pr_to_hover_tool)
    pr_to_toggle = Toggle(label="Цена на работу", active=True)
    pr_to_toggle.js_link('active', pr_to_line_layer, 'visible')
    # ---------------------------------------------

    # ---------------------------- Цена с работы ---------------------------
    pr_from = ColumnDataSource()
    pr_from.data = dict(x=df.index, y=df.from_price)
    pr_from_line_layer = fig.line(x="x", y="y", source=pr_from, line_color=pr_from_color, alpha=0.9, line_width=3)

    pr_from_hover_tool = HoverTool(
        syncable=False,
        renderers=[pr_from_line_layer],
        tooltips=[('Время', '@x{%H:%M}'),
                  ('Цена с работы', '@y{*}руб.')],
        formatters={'@x': 'datetime',
                    '@y': 'numeral'},
        mode='vline')
    fig.add_tools(pr_from_hover_tool)

    pr_from_toggle = Toggle(label="Цена c работы", active=True)
    pr_from_toggle.js_link('active', pr_from_line_layer, 'visible')
    # ---------------------------------------------

    graph = row(fig, sizing_mode="stretch_both")
    controls = row(pr_to_toggle, pr_from_toggle, sizing_mode="scale_width")
    lay = layout(graph, controls, sizing_mode='stretch_both'),
    html = file_html(lay, CDN, "Статистика по такси")
    # return components(lay)
    return html


@app.route('/')
def start_page():
    return render_template("start_page.html")


@app.route('/w')
def show_chart_work():
    df = get_data()
    df1, df2 = handle_data(df)
    if len(df1) > 2:
        res = get_chart(df1)
        return res
    else:
        return "Нет данных за рабочие"

@app.route('/o')
def show_chart_dayoff():
    df = get_data()
    df1, df2 = handle_data(df)
    if len(df2) > 2:
        res = get_chart(df2)
        return res
    else:
        return "Нет данных за выходные"


if __name__ == "__main__":

    app.run(host='0.0.0.0', debug=False)
