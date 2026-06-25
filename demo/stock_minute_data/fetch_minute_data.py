from day_index import init_create_client
client = init_create_client()
code = '000400'
df = client.bars(symbol=code, frequency=7, offset=1600)
df.to_csv('000400.csv', index=False)

