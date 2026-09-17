"""Run `python dashboard.py` and open http://127.0.0.1:8050."""
from pathlib import Path
import pandas as pd
import plotly.express as px
from dash import Dash,dcc,html,Input,Output

ROOT=Path(__file__).resolve().parent
df=pd.read_csv(ROOT/'data/spacex_launch_dash.csv')
df['Outcome']=df['class'].map({0:'Other outcome',1:'Successful landing'})
app=Dash(__name__)
server=app.server
app.layout=html.Div([
    html.H1('SpaceX launch records'),
    html.P('IBM historical dashboard sample: 56 launches. Landing outcome is distinct from mission outcome.'),
    html.Label('Launch site'),
    dcc.Dropdown(id='site-dropdown',options=[{'label':'All sites','value':'ALL'}]+[{'label':v,'value':v} for v in sorted(df['Launch Site'].unique())],value='ALL',clearable=False),
    html.Label('Payload range (kg)',style={'display':'block','marginTop':'20px'}),
    dcc.RangeSlider(id='payload-slider',min=0,max=float(df['Payload Mass (kg)'].max()),step=100,value=[0,float(df['Payload Mass (kg)'].max())],marks={0:'0',2500:'2500',5000:'5000',7500:'7500',10000:'10000'},tooltip={'always_visible':True}),
    html.Div([dcc.Graph(id='success-pie',style={'width':'48%'}),dcc.Graph(id='payload-scatter',style={'width':'52%'})],style={'display':'flex'}),
    html.P(id='filtered-count'),
],style={'fontFamily':'Arial,sans-serif','maxWidth':'1250px','margin':'30px auto','color':'#17324d'})

def figures(site,payload):
    d=df[df['Payload Mass (kg)'].between(*payload)].copy()
    if site!='ALL':
        d=d[d['Launch Site']==site]
    if site=='ALL':
        successes=d.groupby('Launch Site',as_index=False)['class'].sum()
        pie=px.pie(successes,names='Launch Site',values='class',title='Share of successful landings by site')
    else:
        counts=d.Outcome.value_counts().rename_axis('Outcome').reset_index(name='Count')
        pie=px.pie(counts,names='Outcome',values='Count',title=f'Landing outcomes: {site}')
    pie.update_traces(textinfo='label+percent')
    scatter=px.scatter(d,x='Payload Mass (kg)',y='class',color='Booster Version Category',hover_data=['Launch Site','Flight Number'],title='Payload versus landing outcome',labels={'class':'Landing outcome (1=success)'})
    scatter.update_yaxes(tickvals=[0,1],ticktext=['Other outcome','Success'],range=[-.15,1.15])
    scatter.update_traces(marker={'size':11,'opacity':.8})
    for f in [pie,scatter]:
        f.update_layout(template='plotly_white',font={'family':'Arial','size':15},height=440,margin={'l':55,'r':20,'t':65,'b':50})
    return pie,scatter,f'{len(d)} launch records in the selected site and payload range.'

@app.callback(Output('success-pie','figure'),Output('payload-scatter','figure'),Output('filtered-count','children'),Input('site-dropdown','value'),Input('payload-slider','value'))
def update(site,payload):
    return figures(site,payload)

def export_figures():
    for key,site in [('all','ALL'),('ksc','KSC LC-39A')]:
        pie,scatter,count=figures(site,[0,10000])
        # A standalone rendering of actual callback figures, not a screenshot
        # of a running Dash app. Useful as an offline HTML view.
        body=f'<h1>SpaceX: {site}</h1><p>{count}</p><p>Export of the Dash callback figures, full payload range.</p>'
        body+='<div style="display:flex">'+pie.to_html(full_html=False,include_plotlyjs=True,default_width='48%')+scatter.to_html(full_html=False,include_plotlyjs=False,default_width='52%')+'</div>'
        (ROOT/f'results/dashboard_{key}.html').write_text('<html><head><meta charset="utf-8"></head><body style="font-family:Arial">'+body+'</body></html>')

if __name__=='__main__':
    app.run(debug=False)
