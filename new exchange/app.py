import dash
from dash import dcc
from dash import html
import plotly.graph_objects as go
import ccxt
import numpy as np

# Create Dash app instance
app = dash.Dash(__name__)

# Set interval for data updates (30 minutes)
interval = 30 * 60 * 1000

# Define symbols for fetching price data
symbol = 'BTC/USDT'

bid_prices = []
ask_prices = []
spread_fees = []
valid_exchanges = []

# Get all available exchange IDs
exchanges = ccxt.exchanges

for exchange_id in exchanges:
    try:
        exchange = getattr(ccxt, exchange_id)()
        ticker = exchange.fetch_ticker(symbol)
        bid_price = ticker['bid']
        ask_price = ticker['ask']

        # Skip if either bid or ask price is None
        if bid_price is None or ask_price is None:
            continue

        spread_fee = ask_price - bid_price

        bid_prices.append(bid_price)
        ask_prices.append(ask_price)
        spread_fees.append(spread_fee)
        valid_exchanges.append(exchange_id)
    except (ccxt.BaseError, ccxt.BadSymbol):
        continue

# Convert lists to numpy arrays
x = valid_exchanges
bid_prices = np.array(bid_prices)
ask_prices = np.array(ask_prices)
spread_fees = np.array(spread_fees)

# Set up the layout of the Dash app
app.layout = html.Div(children=[
    html.H2('Price Data Visualization'),
    dcc.Interval(id='interval', interval=interval, n_intervals=0),
    dcc.Graph(id='price-graph'),
    dcc.Graph(id='spread-graph')
])

# Callback function to update the graphs
@app.callback(
    dash.dependencies.Output('price-graph', 'figure'),
    dash.dependencies.Output('spread-graph', 'figure'),
    dash.dependencies.Input('interval', 'n_intervals')
)
def update_graph(n):
    fig_price = go.Figure()
    fig_price.add_trace(go.Bar(
        x=x,
        y=bid_prices,
        name='Bid Price'
    ))
    fig_price.add_trace(go.Bar(
        x=x,
        y=ask_prices,
        name='Ask Price',
        base=bid_prices
    ))
    fig_price.update_layout(
        title='Bid and Ask Prices for Exchanges',
        xaxis_title='Exchange',
        yaxis_title='Price',
        barmode='stack'
    )

    fig_spread = go.Figure()
    fig_spread.add_trace(go.Histogram(
        x=spread_fees,
        nbinsx=10,
        name='Spread Fee'
    ))
    fig_spread.update_layout(
        title='Spread Fees for Exchanges',
        xaxis_title='Spread Fee',
        yaxis_title='Count'
    )

    return fig_price, fig_spread

# Callback function to check for arbitrage opportunities
def check_arbitrage():
    for i in range(len(valid_exchanges)):
        for j in range(i + 1, len(valid_exchanges)):
            exchange1 = getattr(ccxt, valid_exchanges[i])()
            exchange2 = getattr(ccxt, valid_exchanges[j])()

            ticker1 = exchange1.fetch_ticker(symbol)
            ticker2 = exchange2.fetch_ticker(symbol)

            bid_price1 = ticker1['bid']
            ask_price2 = ticker2['ask']

            if bid_price1 > ask_price2:
                print(f"Arbitrage opportunity detected between {valid_exchanges[i]} and {valid_exchanges[j]}")

# Run the Dash app
if __name__ == '__main__':
    check_arbitrage()
    app.run_server(debug=True)
