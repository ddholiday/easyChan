import efinance as ef

quote_ids = ['142.ec2602','113.rb2601','113.au2512']

for quote_id in quote_ids:
    futures_df = ef.futures.get_quote_history(quote_id,klt=15)
    print(futures_df)
    futures_df.to_csv(f'./data/{quote_id}.csv',index=False)

