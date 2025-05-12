import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error
import getpass
import psycopg2


def database_connection(**kwargs):
    '''
    Establishes a connection to the database using the credentials provided in the DATABASE_CREDENTIALS section of the config_load.yml file.
    
    Args:
        config_load_file_name (str): Name of the configuration file.
        item_DATABASE_CREDENTIALS (str): Key specifying the database credentials in the configuration file.
        **kwargs: Additional parameters for the database connection.
            Example: dbname, user, password, host, port, etc.
    
    Returns:
        connection (psycopg2.extensions.connection): Connection object to the PostgreSQL database.
        cursor (psycopg2.extensions.cursor): Cursor object for executing SQL commands.
    '''

    # Prompt the user to enter the password if not provided in kwargs
    password = kwargs.get('password') or getpass.getpass("Enter the database password: ")

    # Construct the connection string
    DB_CONNECTION_STRING = ''
    for key, value in kwargs.items():
        if key != 'password':
            DB_CONNECTION_STRING += f'{key.lower()}={value} '

    # Add the password to the connection string
    DB_CONNECTION_STRING += f'password={password}'

    ### Open database connection
    try: 
        connection = psycopg2.connect(DB_CONNECTION_STRING)
        print("Connection created!")
    except psycopg2.Error as e: 
        print("Error: Could not make connection to the Postgres database")
        print(e)
        return None, None

    try: 
        cursor = connection.cursor()
        print("Cursor obtained!")
    except psycopg2.Error as e: 
        print("Error: Could not get cursor")
        print(e)
        connection.close()
        return None, None

    connection.set_session(autocommit=True)
    
    return connection, cursor


def describe_table(cursor, table_name):
    '''
    Retrieves and prints the structure of a given table.
    
    Args:
        cursor (psycopg2.extensions.cursor): Cursor object for executing SQL commands.
        table_name (str): Name of the table.
    '''

    try:

        sql = 'SELECT column_name, data_type FROM information_schema.columns WHERE table_name = ' + "'" + table_name  + "'" + ' ORDER BY ordinal_position'

        cursor.execute(sql)

        columns = cursor.fetchall()

        print('---------------------------------------')

        print('Table: ' + table_name)

        print('---------------------------------------')

        print('column_name | data_type')

        print('---------------------------------------')    

        for row in columns:

            print("{}".format(row[0]) + " | {}".format(row[1]))

    except psycopg2.Error as e: 
            
        print("Error: issue executing sql statement")
        print (e)
        

def compute_grouped_rmse(df, group_cols):
    """
    Compute RMSE between value_measured and value_simulated,
    grouped by specified columns.
    
    Parameters:
        df (pd.DataFrame): Input dataframe with 'value_measured' and 'value_simulated' columns.
        group_cols (list): List of columns to group by (e.g., ['calibration_method', 'experiment']).

    Returns:
        pd.DataFrame: DataFrame with group columns and RMSE values.
    """
    def rmse(y_true, y_pred):
        return np.sqrt(mean_squared_error(y_true, y_pred))

    grouped_rmse = (
        df.groupby(group_cols)[['value_measured', 'value_simulated']]
          .apply(lambda g: rmse(g['value_measured'], g['value_simulated']))
          .reset_index(name='rmse')
    )

    return grouped_rmse


def compute_grouped_nrmse(df, group_cols, norm_method='range'):
    """
    Calculate NRMSE grouped by specified columns
    
    Parameters:
    -----------
    df : DataFrame
        Must contain 'value_simulated' and 'value_measured' columns
    group_cols : list
        Columns to group by
    norm_method : str
        Normalization method: 'range', 'mean', or 'std'
    """
    # Group data
    grouped = df.groupby(group_cols)
    
    results = []
    
    for name, group in grouped:
        # Extract simulated and measured values
        y_pred = group['value_simulated']
        y_true = group['value_measured']
        
        # Calculate RMSE
        mse = ((y_pred - y_true) ** 2).mean()
        rmse = np.sqrt(mse)
        
        # Calculate normalization factor based on chosen method
        if norm_method == 'range':
            # Normalize by range of observed values
            norm_factor = y_true.max() - y_true.min()
        elif norm_method == 'mean':
            # Normalize by mean of observed values
            norm_factor = y_true.mean()
        elif norm_method == 'std':
            # Normalize by standard deviation of observed values
            norm_factor = y_true.std()
        else:
            raise ValueError("norm_method must be 'range', 'mean', or 'std'")
        
        # Avoid division by zero
        if norm_factor == 0:
            nrmse = np.nan
        else:
            nrmse = rmse / norm_factor
            
        # Create result row
        if isinstance(name, tuple):
            result = dict(zip(group_cols, name))
        else:
            result = {group_cols[0]: name}
            
        result['rmse'] = rmse
        result['nrmse'] = nrmse
        results.append(result)
    
    return pd.DataFrame(results)