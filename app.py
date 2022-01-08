# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser

import os
import dash
import pickle
import socket
import string
import pandas as pd
from dash import no_update, dash_table, dcc, html
from datetime import datetime
from dash_extensions import Download
from dash.dependencies import Input, Output, State
from dash_extensions.snippets import send_data_frame

app = dash.Dash()
server = app.server

if os.path.exists('tmp.csv'):
    os.remove('tmp.csv')

# Load in the data (can heroku do this...)?
with open('enc.pickle', 'rb') as handle:
    enc = pickle.load(handle)

lipsum = ' '.join(enc.df_encipher['word'].head(4))

style_row = {'display': 'inline-block', 'width': '500px', 'padding':0}
style_output = {'display': 'inline-block', 'width': '400px',
                'whiteSpace': 'pre-line', 'font-size':'110%'}
style_textarea = {'height': 200, 'width': 400}

letters = ', '.join(enc.letters)
n_letters = len(enc.letters)
n_enc = enc.idx_max['n_encipher']

# Determine verboten letters
all_letters = pd.Series(list(string.ascii_letters))
okay_letters = enc.letters.append(enc.letters.str.upper())
regex_verboten = '[%s]' % ''.join(all_letters[~all_letters.isin(okay_letters)])

app.layout = html.Div([
    html.H2('Create your own enciphered poem'),
    html.H3('Using only %i letters: %s' % (n_letters, letters)),
    html.Br(),
    html.Div([
        html.Div(dcc.Textarea(id='text1',value=lipsum,style=style_textarea), style=style_row),
        html.Div(id='text_output1', style={**style_output,**{'padding-right':100}}),
        html.Div(id='text_output2', style={**style_output,**{'padding':0}})
    ]),
    html.Button('Submit', id='submit_button', n_clicks=0),
    html.Br(), html.Br(),
    html.H3('Pick an index from 1-%i (1 has most (weighted) words, %i has the fewest)' % (n_enc, n_enc)),
    dcc.Input(id='user_idx',placeholder='Enter an interger...',type='number', value=1,min=1,max=n_enc,step=1),
    html.Br(), 
    html.Div(id='text_output3', style={**style_output,**{'padding-right':100}}),
    html.Div(id='text_output4', style={**style_output,**{'padding-right':100}}),
    html.Div(id='text_output5', style={**style_output,**{'padding-right':100}}),
    html.Br(), html.Br(),
    html.Div([html.Button("Download", id="btn"), Download(id="download")]),
    html.Br(), html.Br(), html.Br(), html.Br(), 
    html.Div(id='table-container',  className='tableDiv'),
    html.Br(), html.Br(), html.Br(), html.Br(), 
])

@app.callback(
    Output("download", "data"),
    [Input("btn", "n_clicks")]
)
def func(n_clicks):
    if os.path.exists('tmp.csv') and n_clicks is not None:
        print('exists')
        df = pd.read_csv('tmp.csv')
        fn = 'poem_' + datetime.now().strftime('%Y_%m_%d_%H_%M_%S') + '.csv'
        os.remove('tmp.csv')
        return send_data_frame(df.to_csv, fn, index=False)

@app.callback(
    [Output('table-container','children')],
    [Input('user_idx', 'value')]
)
def update_idx(idx):
    # Get the encipher index
    ridx = min(max(idx-1,0), n_enc-1)
    idx = int(enc.df_score.loc[ridx]['idx'])
    enc.set_encipher(idx_pairing=idx)
    enc.get_corpus()
    # Set up the dash table
    style_table = {'overflowX':'scroll', 'width':1000}  # 'height':'4100px', 'overflowY':'scroll'
    style_cell = {'textAlign': 'left'}
    columns = [{'name':cc, 'id': cc} for cc in enc.df_encipher.columns]
    data = enc.df_encipher.to_dict('records')
    tab = dash_table.DataTable(id='table', columns=columns,data=data, style_table=style_table, style_cell=style_cell)
    return [tab, ]

@app.callback(
    [Output('text_output1', 'children'), Output('text_output2', 'children')],
    [Input('user_idx', 'value'), Input('submit_button', 'n_clicks')],
    State('text1', 'value')
)
def update_text(idx, n_clicks, txt):
    if n_clicks > 0:
        # determine letters to remove
        plaintxt = pd.Series([txt]).str.replace(regex_verboten,'',regex=True)[0]
        ciphertxt = enc.alpha_trans(plaintxt)[0]
        val1 = 'plaintext:\n' + plaintxt
        val2 = 'ciphertext:\n' + ciphertxt
        vv = [val1, val2]
        tmp_df = pd.DataFrame({'idx':idx, 'original':plaintxt, 'enciphered':ciphertxt},index=[0])
        tmp_df.to_csv('tmp.csv',index=False)
    else:
        vv = [no_update, no_update]
    return vv

if __name__ == '__main__':
    if socket.gethostname() == 'RT5362WL-GGB':
        app.run_server(host='127.0.0.1', port='8050', debug=True)
    else:
        app.run_server(debug=True)

