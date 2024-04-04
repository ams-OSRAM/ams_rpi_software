"""note:: using `htmls_` name to avoid collisions with other html packages"""
import re
import flask
import string
import numpy as np
import pandas as pd
from pywebify import webpage
from markupsafe import Markup

def float_format(x):
    """
    Preferred default formatting for html display

    Args:
        x (numeric | list of numeric): number or iterable of numbers
            to format as HTML string

    Returns:
        formatted (str | list of str): formatted numeric string or list same
                                       if input is iterable

    """
    def _item(x):
        if isinstance(x, str):
            try:
                float(x)
            except Exception:
                return x
            if re.search('\dE-\d\d$', x, re.IGNORECASE):
                return x

        x = float(x)  # lazy way to handle int, etc ...
        if not np.isfinite(x):
            return ''

        ax = abs(x)
        if x == 0.0:
            return '0'
        if ax < 1e-2 or ax >= 1e6:
            fstr = re.sub('e\+0', 'e', '{:0.2e}'.format(x))
            return re.sub('e\-0', 'e-', fstr)
        if ax < 0.1:
            return '{:0.3f}'.format(x)
        if ax < 1:
            return '{:0.2f}'.format(x)
        if ax < 10:
            if np.mod(ax, 1):
                return '{:0.2f}'.format(x)
            return '{:0.0f}'.format(x)
        if ax < 100:
            if np.mod(ax, 1):
                return '{:0.1f}'.format(x)
            return '{:0.0f}'.format(x)

        return '{:0.0f}'.format(x)

    if hasattr(x, '__iter__') and not isinstance(x, str):
        return [_item(e) for e in x]
    else:
        return _item(x)


def table(df, name=None, float2html=True, color=False, coloraxis=0,
          fontsize=None, precision=0, cmap=None, **kwargs):
    """
    Create HTML table from dataframe

    Args:
        df (pandas.DataFrame): data table to render

    Keyword Args:
        name (str, None): file path to create HTML page

    Returns:

    .. todo:: get both the color js in the same table...

    """
    if color:
        cmap = 'Greens' if cmap is None else cmap
        sty = df.style.background_gradient(cmap=cmap, axis=coloraxis, high=0.7).set_precision(precision)
        html, js = js_datatable(sty.render(), **kwargs)

    else:
        if float2html:
            # df.apply(libreport.utils.float_format_html)  # rework function to use apply if desired for speed
            for col in df.columns:
                df[col] = df[col].map(float_format)

        html, js = js_datatable(df)

    if fontsize is not None:
        html += '''<style type="text/css">.display{font-size:%0.2fem;}</style>''' % fontsize

    page = webpage.Webpage()
    page.content(html)
    page.context['js'] += [js]
    page.pagefilename = name if name is not None else page.pagefilename
    page.render()

    return page


def js_datatable(table, tableid=None, jstype_=None, context=None, float2html=False, **kwargs):
    """
    Creates formatted html table for use with datatables.js functionality

    Args:
        table: (pandas.DataFrame|str): pandas DataFrame or html formatted table, generally from pandas.DataFrame.to_html

    Keyword Args:
        tableid (str): table unique identifier (randomly generated if not specified)
        jstype_ (str): js type (planned for future use)
        context (dict, None): context to evaluate in javasript
        float2html (bool, True): cast float to readable string

    """
    context = {} if context is None else context
    tableid = 'table'

    context['BPAGINATE'] = context['bPaginate'] if 'bPaginate' in context else 'true'
    context['BPROCESSING'] = context['bProcessing'] if 'bProcessing' in context else 'true'
    context['IDISPLAYLENGTH'] = context['iDisplayLength'] if 'iDisplayLength' in context else '25'
    context['ORDERING'] = context['ordering'] if 'ordering' in context else "asc"
    context['ORDERCOL'] = context['ordercol'] if 'ordercol' in context else "0"
    context['TABLEID'] = tableid

    if isinstance(table, pd.DataFrame):
        if float2html:
            # df.apply(libreport.utils.float_format_html)  # rework function to use apply if desired for speed
            for col in table.columns:
                table[col] = table[col].map(float_format)

        table = table.to_html(classes='display', escape=False, justify='left', **kwargs)

    # table = table.replace(r'class="dataframe display"', r'class="display table-striped table-hover" id="{0}"'.format(tableid))
    table = table.replace(r'class="dataframe display"', r'class="display" id="{0}"'.format(tableid))
    table = table.replace(r'border="1"', r' ')
    table = table.replace('<tr>', '<tr align="center">')
    #table = table.replace('<tr align="center">', '<tr align="left">')

    js = u'''
        <script type="text/javascript">
            $(document).ready(function(){
               var table =  $('#$TABLEID').dataTable(
                    {
                        sDom: 'B<"clear">lfrtip',
                        order: [[ $ORDERCOL, "$ORDERING" ]],
                        bPaginate: $BPAGINATE,
                        bsort: false,
                        iDisplayLength: $IDISPLAYLENGTH,
                        bProcessing: true,
                        colReorder: true,
                        select: true,
                        autoFill: true,
                        keys: true,
                        buttons: [
                                   {
                                        extend: 'collection',
                                        text: 'Export',
                                        buttons: [ 'copy', 'csv', 'excel', 'pdf', 'print' ]
                                    },
                                    'colvis','colvisRestore'
                                ],
                    }
                );

            });
        </script>
        '''

    tmpl = string.Template(js)
    html = tmpl.safe_substitute(context)

    js = Markup(html)

    return table, js
