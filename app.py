from flask import Flask, render_template, request, send_file, redirect, url_for
import yfinance as yf
import pandas as pd
from io import StringIO

app = Flask(__name__)
downloaded_data = pd.DataFrame()

@app.route('/', methods=['GET', 'POST'])
def index():
    stock_data = []
    ticker = ''
    period = '5d'
    error_message = None

    if request.method == 'POST':
        ticker = request.form['ticker'].upper().strip()
        if not ticker.endswith('.JK'):
            ticker += '.JK'
        period = request.form.get('period', '5d')

        try:
            data = yf.download(ticker, period=period)
            if data.empty:
                error_message = 'Data tidak ditemukan'
            else:
                data.reset_index(inplace=True)
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = ['_'.join([str(i) for i in col if i]).capitalize() for col in data.columns.values]
                else:
                    data.columns = [str(col).capitalize() for col in data.columns]
                # Setelah pengubahan kolom di atas
                for col in data.columns:
                    if col.lower().startswith('close'):
                        data.rename(columns={col: 'Close'}, inplace=True)
                    if col.lower().startswith('open'):
                        data.rename(columns={col: 'Open'}, inplace=True)
                    if col.lower().startswith('high'):
                        data.rename(columns={col: 'High'}, inplace=True)
                    if col.lower().startswith('low'):
                        data.rename(columns={col: 'Low'}, inplace=True)
                    if col.lower().startswith('volume'):
                        data.rename(columns={col: 'Volume'}, inplace=True)
                    if col.lower().startswith('date'):
                        data.rename(columns={col: 'Date'}, inplace=True)
                if 'Date' in data.columns:
                    data['Date'] = data['Date'].astype(str)
                stock_data = data.to_dict('records')
                global downloaded_data
                downloaded_data = data
                print(data.columns)
                print(data.head())
        except Exception as e:
            error_message = f'Error: {e}'

    return render_template(
        "index.html",
        stock_data=stock_data,
        ticker=ticker,
        period=period,
        error_message=error_message
    )

@app.route('/download')
def download():
    global downloaded_data
    if downloaded_data.empty:
        return "Belum ada data", 400
    csv = downloaded_data.to_csv(index=False)
    buf = StringIO(csv)
    buf.seek(0)  # Penting agar file bisa diunduh
    return send_file(
        buf,
        mimetype='text/csv',
        as_attachment=True,
        download_name='data_saham.csv'
    )

@app.route('/screening', methods=['POST'])
def screening():
    import yfinance as yf
    tickers = request.form['tickers'].upper().replace(' ', '').split(',')
    period = request.form.get('period', '1mo')
    result = []
    for ticker in tickers:
        if not ticker.endswith('.JK'):
            ticker += '.JK'
        try:
            data = yf.download(ticker, period=period)
            if data.empty or len(data) < 20:
                continue
            close = data['Close']
            vol = data['Volume']
            ma20 = close.rolling(20).mean()
            # Screening: close terakhir > MA20 dan volume terakhir > rata-rata volume 20 hari
            if close.iloc[-1] > ma20.iloc[-1] and vol.iloc[-1] > vol.rolling(20).mean().iloc[-1]:
                result.append(f"{ticker} (Close: {close.iloc[-1]:,.0f}, MA20: {ma20.iloc[-1]:,.0f}, Vol: {vol.iloc[-1]:,.0f})")
        except Exception as e:
            continue
    return render_template(
        "index.html",
        screening_result=result,
        stock_data=[],
        error_message=None
    )

if __name__ == '__main__':
    app.run()



