# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser

import os
import dash
import pickle
import socket
import string
import numpy as np
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

if os.path.exists('tmp2.csv'):
    os.remove('tmp2.csv')

# Load in the data (can heroku do this...)?
with open('enc.pickle', 'rb') as handle:
    enc = pickle.load(handle)

# Set to "best" cipher
enc.set_encipher(idx_pairing=enc.df_score['idx'][0])
enc.get_corpus()
lipsum = ' '.join(enc.df_encipher['word_x'].head(4))

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
    html.H2(html.A('Create your own enciphered poem', target='_blank', href='http://www.erikdrysdale.com/enciphered')),
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
    html.Div([html.Button("Download", id="btn"), Download(id="download1"), Download(id="download2")]),
    html.Br(), html.Br(), html.Br(), html.Br(), 
    html.Div(id='table-container',  className='tableDiv'),
    html.Br(), html.Br(), html.Br(), html.Br(), 
])

@app.callback(
    Output("download1", "data"),
    [Input("btn", "n_clicks")]
)
def func(n_clicks):
    if os.path.exists('tmp.csv') and n_clicks is not None:
        df1 = pd.read_csv('tmp.csv')
        fn = 'poem_' + datetime.now().strftime('%Y_%m_%d_%H_%M_%S') + '.csv'
        os.remove('tmp.csv')
        return send_data_frame(df1.to_csv, fn, index=False)

@app.callback(
    Output("download2", "data"),
    [Input("btn", "n_clicks")]
)
def func(n_clicks):
    if os.path.exists('tmp2.csv') and n_clicks is not None:
        df2 = pd.read_csv('tmp2.csv')
        fn = 'dict_' + datetime.now().strftime('%Y_%m_%d_%H_%M_%S') + '.csv'
        os.remove('tmp2.csv')
        return send_data_frame(df2.to_csv, fn, index=False)

@app.callback(
    [Output('table-container','children'), Output('text_output3', 'children'), Output('text_output4', 'children'), Output('text_output5', 'children')],
    [Input('user_idx', 'value')]
)
def update_idx(idx):   # idx=1
    # (i) Get the encipher index
    ridx = min(max(idx-1,0), n_enc-1)
    idx = int(enc.df_score.loc[ridx]['idx'])
    enc.set_encipher(idx_pairing=idx)
    enc.get_corpus()

    # (ii) Format to relevant values
    tmp_df = enc.df_encipher.drop(columns=['def_y'])
    vec_weight = tmp_df['weight'].values
    if np.all(vec_weight == vec_weight.astype(int)):
        tmp_df['weight'] = vec_weight.astype(int)
    tmp_df = tmp_df.sort_values('weight',ascending=False).reset_index(drop=True)
    tmp_df['num'] = range(1,len(tmp_df)+1)
    # Ensure last two columns are weight, definition
    cn_last = ['weight','def_x']
    cn_ord = list(tmp_df.columns.drop(cn_last)) + cn_last
    tmp_df = tmp_df[cn_ord]
    tmp_df.to_csv('tmp2.csv',index=False)

    # (iii) Get the relevant parts of speech
    df_pos = tmp_df['pos_x'].value_counts().reset_index()
    df_pos.rename(columns={'index':'pos', 'pos_x':'n'}, inplace=True)
    df_pos = df_pos.merge(enc.pos_def,'inner')
    tmp_desc = df_pos['desc'].str.split(',',1,True)[0]
    tmp_desc = tmp_desc.str.split('\\s',1,True)[0]
    df_pos['desc'] = tmp_desc
    df_pos_n = df_pos.groupby('desc').n.sum().sort_values(ascending=False).reset_index()
    # Convert to strings
    str_pos_n = ', '.join(df_pos_n.apply(lambda x: '%s (%i)' % (x['desc'],x['n']),1))
    str_pos_def = ', '.join(df_pos.apply(lambda x: '%s=%s' % (x['pos'],x['desc']),1))
    # Clean up letter pairing
    str_pairing = enc.str_pairing.replace(',',', ')

    # (iv) Set up the dash table
    style_table = {'overflowX':'scroll', 'width':1400, 'overflowY':'scroll', 'height':600}
    style_cell = {'textAlign': 'left', 'min-width':75}
    columns = [{'name':cc, 'id': cc} for cc in tmp_df.columns]
    data = tmp_df.to_dict('records')
    tab = dash_table.DataTable(id='table', columns=columns,data=data, style_table=style_table, style_cell=style_cell, sort_action='native')
    return [tab, str_pairing, str_pos_n, str_pos_def, ]

@app.callback(
    [Output('text_output1', 'children'), Output('text_output2', 'children')],
    [Input('user_idx', 'value'), Input('submit_button', 'n_clicks')],
    State('text1', 'value')
)
def update_text(idx, n_clicks, txt):
    # idx=1;n_clicks=1;txt='the and to a'

    ridx = min(max(idx-1,0), n_enc-1)
    idx = int(enc.df_score.loc[ridx]['idx'])
    enc.set_encipher(idx_pairing=idx)
    enc.get_corpus()

    if n_clicks > 0:
        # determine letters to remove
        plaintxt = pd.Series([txt]).str.replace(regex_verboten,'',regex=True)[0]
        ltxt = plaintxt.lower()
        ctxt = str(enc.alpha_trans(ltxt)[0])
        ciphertxt = ''.join([c.upper() if p.isupper() else c for p,c in zip(plaintxt, ctxt)])
        val1 = 'plaintext:\n' + plaintxt
        val2 = 'ciphertext:\n' + ciphertxt
        vv = [val1, val2]
        tmp_df = pd.DataFrame({'idx':idx, 'pairing':enc.str_pairing, 'plaintext':plaintxt, 'ciphertext':ciphertxt},index=[0])
        tmp_df.to_csv('tmp.csv',index=False)
    else:
        vv = [no_update, no_update]
    return vv

if __name__ == '__main__':
    if socket.gethostname() == 'RT5362WL-GGB':
        app.run_server(host='127.0.0.1', port='8050', debug=True)
    else:
        app.run_server(debug=True)

