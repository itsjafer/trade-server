import os
import sys

from flask import Flask, request, jsonify
from flask_cors import CORS
from tradestation_api import TradeStation
from schwab_api import Schwab

app = Flask(__name__)
CORS(app)

@app.route("/")
def hello_world():
    name = os.environ.get("NAME", "World")
    return "Hello {}!".format(name)

@app.route('/trade_schwab', methods=['POST'])
def trade_schwab():
    if len(request.form['totp']) <= 0:
        return "Unable to place trade: Missing TOTP secret"

    if len(request.form['username']) <= 0 or len(request.form['password']) <= 0:
        return "Unable to place trade: Missing username and password"

    messagesResponse = {"messages": list()}
    try:
        s = Schwab.get_instance(
            username=request.form['username'],
            password=request.form['password'],
            headless=False,
            totp=request.form['totp']
        )

        s.login(screenshot=False)

        account_info = s.get_account_info()

        if len(request.form['ticker']) <= 0:
            return account_info
            
        tickers = request.form['ticker'].split(',')
        for ticker in tickers:
            for account_id in account_info:
                messages, success = s.trade(
                    ticker=ticker, 
                    side=request.form['side'], 
                    qty=int(request.form['qty']),
                    account_id=account_id,
                    dry_run=request.form['dry_run']
                )
                if not success:
                    messagesResponse["messages"].extend(messages)

    except Exception as e:
        print(e)
        del s

        return "Unable to place trade: " + str(e)
    
    account_info = s.get_account_info()

    if not success:
        return messagesResponse

    return account_info

@app.route('/trade_ts', methods=['POST'])
def trade_ts():
    try:
        ts = TradeStation.get_instance(
            username=request.form['username'],
            password=request.form['password'],
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:87.0) Gecko/20100101 Firefox/87.0",
            totp=request.form['totp']
        )

        ts.login(screenshot=False)
        tickers = request.form['ticker'].split(',')
        for ticker in tickers:
            for i in range(int(request.form['accounts'])):
                ts.trade(
                    ticker=ticker, 
                    side=request.form['side'], 
                    qty=int(request.form['qty']),
                    account_index=i,
                    screenshot=False
                )
    except Exception as e:
        print(e)
        del ts
        return "Unable to place trade: " + str(e)

    return "TradeStation trade seems to have finished!"
    

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))