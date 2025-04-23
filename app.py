from dash import Dash, dcc, html, Input, Output, State
import pandas as pd
import plotly.express as px

# Load data
url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vRxoHS5Dg6Zh9dItLxYvWgWf-WM7oZgKAUQTOYqP1SWZo_AS9g0T3ek-PhY4c2vA6Re4MZjg2QHPxm1/pub?gid=337648147&single=true&output=csv'
df = pd.read_csv(url)
df['Playoffs'] = df['Playoffs'].fillna(False)

# Create app
app = Dash(__name__, suppress_callback_exceptions=True)

app.title = "NBA Dashboard"

app.layout = html.Div([
    html.H1("🏀 NBA Player Performance Dashboard", style={'textAlign': 'center', 'padding': '10px', 'backgroundColor': '#1e1e2f', 'color': 'white'}),

    html.Div([
        # Sidebar filters
        html.Div([
            html.H3("Filters", style={'color': '#333'}),
            html.Label("Select Team:", style={'marginTop': '10px'}),
            dcc.Dropdown(
                id='team-filter',
                options=[{'label': team, 'value': team} for team in sorted(df['Tm'].unique())],
                multi=True,
                placeholder="All Teams",
                style={'padding': '6px', 'marginBottom': '15px'}
            ),
            html.Label("Select Year:", style={'marginTop': '15px'}),
            dcc.Dropdown(
                id='year-filter',
                options=[{'label': str(year), 'value': year} for year in sorted(df['Year'].unique())],
                multi=True,
                placeholder="All Years",
                style={'padding': '6px', 'marginBottom': '15px'}
            ),
            html.Label("Select Game Type:", style={'marginTop': '15px'}),
            dcc.Dropdown(
                id='game-type-filter',
                options=[
                    {'label': 'All Games', 'value': 'all'},
                    {'label': 'Regular Season Only', 'value': 'regular'},
                    {'label': 'Playoffs Only', 'value': 'playoffs'},
                ],
                value='all',
                style={'padding': '6px', 'marginBottom': '15px'}
            ),
            html.Button("Apply Filters", id='apply-btn', n_clicks=0, style={'marginTop': '20px', 'padding': '10px'})
        ], style={
            'flex': '25%',
            'padding': '20px',
            'backgroundColor': '#f4f4f4',
            'borderRight': '1px solid #ccc',
            'height': '85vh',
            'overflowY': 'auto'
        }),

        # Main content area
        html.Div([
            dcc.Tabs(id='tabs', value='tab1', children=[
                dcc.Tab(label='🏆 Top Player Metrics', value='tab1'),
                dcc.Tab(label='📈 Game Score Dist.', value='tab2'),
                dcc.Tab(label='🎯 Points vs Assists', value='tab3'),
                dcc.Tab(label='📊 Team Stats Overview', value='tab4')
            ]),
            html.Div(id='tabs-content', style={'padding': '20px'}),
            html.Div(id='player-details', style={'padding': '20px'})  # New: player detail section
        ], style={'flex': '75%', 'padding': '10px'})
    ], style={'display': 'flex', 'flexDirection': 'row'}),

    # Hidden store
    dcc.Store(id='selected-player-id'),

    # Footer
    html.Footer([
        html.Div([
            html.H4("About This Dashboard", style={'marginBottom': '5px'}),
            html.P("This dashboard provides an interactive exploration of NBA player statistics, allowing filtering by team, season, and game type."),
            html.P("Use the tabs to view top players, score distribution, scoring vs assists, and team-level stats. Each chart includes brief insights to help interpret the data."),
            html.P("Built by Sneha. Data from Basketball Reference.")
        ], style={'textAlign': 'center', 'padding': '15px', 'backgroundColor': '#1e1e2f', 'color': 'white'})
    ])
])

@app.callback(
    Output('tabs-content', 'children'),
    Input('tabs', 'value'),
    Input('apply-btn', 'n_clicks'),
    State('team-filter', 'value'),
    State('year-filter', 'value'),
    State('game-type-filter', 'value')
)
def update_dashboard(tab, _, selected_teams, selected_years, game_type):
    filtered_df = df.copy()
    if selected_teams:
        filtered_df = filtered_df[filtered_df['Tm'].isin(selected_teams)]
    if selected_years:
        filtered_df = filtered_df[filtered_df['Year'].isin(selected_years)]
    if game_type == 'regular':
        filtered_df = filtered_df[filtered_df['Playoffs'] == False]
    elif game_type == 'playoffs':
        filtered_df = filtered_df[filtered_df['Playoffs'] == True]

    if tab == 'tab1':
        top_players = (
            filtered_df.groupby("bbrID")[["PTS", "AST", "TRB", "GmSc"]]
            .mean()
            .sort_values(by="GmSc", ascending=False)
            .head(10)
            .reset_index()
        )
        return html.Div([
            html.H3("Top 10 Players by Game Score", style={'textAlign': 'center'}),
            html.P("Click on a player bar to view detailed statistics."),
            dcc.Graph(
                id='top-players-graph',
                figure=px.bar(top_players, x="bbrID", y="GmSc", color="GmSc",
                              title="Top Players - Avg Game Score",
                              hover_data={"PTS": True, "AST": True, "TRB": True}),
                clickData=None
            )
        ])

    elif tab == 'tab2':
        fig = px.histogram(filtered_df, x="GmSc", nbins=30, title="Game Score Distribution")
        return html.Div([
            html.H3("Distribution of Game Scores"),
            html.P("Most players have an average Game Score between 5 and 15."),
            dcc.Graph(figure=fig)
        ])

    elif tab == 'tab3':
        fig = px.scatter(
            filtered_df, x="PTS", y="AST", color="Tm", hover_name="bbrID",
            title="Points vs Assists", trendline="ols",
            hover_data=None, hovertemplate="<b>%{hovertext}</b><br>PTS: %{x}<br>AST: %{y}<extra></extra>"
        )
        return html.Div([
            html.H3("Player Points vs Assists Comparison"),
            html.P("Some players excel in both scoring and assisting, forming clear outliers."),
            dcc.Graph(figure=fig)
        ])

    elif tab == 'tab4':
        team_stats = (
            filtered_df.groupby("Tm")[["PTS", "AST", "TRB", "GmSc"]]
            .mean()
            .reset_index()
            .sort_values(by="PTS", ascending=False)
        )
        fig = px.bar(team_stats, x="Tm", y="PTS", color="PTS", title="Team Average Points",
                     labels={"PTS": "Avg Points per Player"})
        return html.Div([
            html.H3("📊 Team-Level Average Stats", style={'textAlign': 'center'}),
            html.P("Teams with higher average points per player often indicate better offensive performance."),
            dcc.Graph(figure=fig)
        ])

# Capture clicked player ID
@app.callback(
    Output('selected-player-id', 'data'),
    Input('top-players-graph', 'clickData')
)
def store_clicked_player(clickData):
    if clickData:
        return clickData['points'][0]['x']
    return None

# Display player details
@app.callback(
    Output('player-details', 'children'),
    Input('selected-player-id', 'data'),
    State('team-filter', 'value'),
    State('year-filter', 'value'),
    State('game-type-filter', 'value')
)
def show_player_details(player_id, selected_teams, selected_years, game_type):
    if not player_id:
        return ""

    filtered_df = df.copy()
    if selected_teams:
        filtered_df = filtered_df[filtered_df['Tm'].isin(selected_teams)]
    if selected_years:
        filtered_df = filtered_df[filtered_df['Year'].isin(selected_years)]
    if game_type == 'regular':
        filtered_df = filtered_df[filtered_df['Playoffs'] == False]
    elif game_type == 'playoffs':
        filtered_df = filtered_df[filtered_df['Playoffs'] == True]

    player_data = filtered_df[filtered_df['bbrID'] == player_id]
    if player_data.empty:
        return "No data found for selected player."

    latest_entry = player_data.iloc[-1]
    return html.Div([
        html.H4(f"Player Details: {player_id}"),
        html.P(f"Team: {latest_entry['Tm']}"),
        html.P(f"Year: {latest_entry['Year']}"),
        html.P(f"Points: {latest_entry['PTS']}"),
        html.P(f"Assists: {latest_entry['AST']}"),
        html.P(f"Rebounds: {latest_entry['TRB']}"),
        html.P(f"Game Score: {latest_entry['GmSc']}")
    ], style={'border': '1px solid #ccc', 'padding': '15px', 'marginTop': '20px'})

# Run server
if __name__ == '__main__':
    server = app.server
    app.run(debug=True,host='0.0.0.0', port=8080)
