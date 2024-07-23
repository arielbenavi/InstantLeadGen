from telegram_wrapper import telegram_noti

telegram_noti(f'[+] Wallet address {row["btc_address"]} (whale # {row["index"]}) '
                f'{to_Str} BTC @ {row["trans_time"]} \n'
                f'This amounts to {row["percent_of_portfolio"]} % of his entire portfolio. \n')
