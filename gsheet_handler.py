import gspread
import time
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime


# use creds to create a client to interact with the Google Drive API
scope = ['https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(r'./client_secret.json', scope)
client = gspread.authorize(creds)


def parse_to_sheet(df, spreadsheet, index=None, logging=None, date=True, start_range='A'):
    """ :receives: dataframe to parse, Gsheet object, index is row to start parsing from, logging file to remove duplicates, 
         against, date=True to add collection date (today) column, start range is what range to start parsing from
    """
    if df.empty:
      print('[!] DataFrame is empty (no results) @parse_to_sheet')
      return 0
    
    df = df.fillna('NA')

    if date:
      df['date'] = [datetime.today().strftime('%Y-%m-%d')]*len(df)
      
    time.sleep(2)
    
    # if logging:
    #   df = s3_db_check(df, logging['path'], logging['col'])
    
    if not index:
      try:
        index = len(spreadsheet.col_values(1))+1
      except:
        time.sleep(10)
        index = len(spreadsheet.col_values(1))+1
      
    try:
      spreadsheet.update(f'{start_range}{index}:ZZ{index+99000}', df.astype(str).values.tolist())
    except Exception as e: #API quota error
      time.sleep(1)
      if 'the maximum of 50000 characters in a single cell' in str(e):
        print('[!] Your input contains more than the maximum of 50000 characters in a single cell. \n truncating ...')
        try: df = df.apply(lambda x: x.astype(str).str[:45000])
        except Exception as e: print(f'[!] truncationg failed: ({str(e)}), \n skipping ...')
      elif 'exceeds grid limits' in str(e):
        print('[!] "exceeds grid limits" error detected, adding row...')
        spreadsheet.add_rows(10000)
      else:
        print(f'API Error - quota? \n sleeping for 15 secs \n Error: {str(e)}')
        time.sleep(15)
      try:
        time.sleep(1)
        spreadsheet.update(f'{start_range}{index}:ZZ{index+60000}', df.astype(str).values.tolist())
      except Exception as e:
          print(df)
          df.astype(str).display()
          raise ValueError(f"Error in Gsheet: {str(spreadsheet)} \n Error: {str(e)}")
    
    return len(df)
  
  