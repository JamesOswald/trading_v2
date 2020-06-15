FROM python:3.7.7
COPY trading_crypto .
ENV PYTHONPATH=./ \
    GDAX_EXCHANGE_ID=1 \
    GDAX_KEY_MAIN=f5fd0edc8e6b3ee717c2aa1c3c97c3a4 \
    GDAX_KEY_SECRET=32rgiUIoz5sPs+fF/8ZdVdfkTtZ2eRLnIXI1fe2gzsvL77IEQv55w2/1gYYiwyab3ngGqPr1LXAWfM+5XTWH5w== \
    GDAX_PASSPHRASE=50k4l0op67m \
    GDAX_ROOT_URL=https://api.pro.coinbase.com \
    GDAX_SOCKET_URL=wss://ws-feed.pro.coinbase.com \ 
    GDAX_EXCHANGE_NAME=gdax \
    GDAX_RECORDING_DEPTH=False \
    GDAX_RECORDING_FEE=False
CMD ["python", "apis/gdax_api.py"]