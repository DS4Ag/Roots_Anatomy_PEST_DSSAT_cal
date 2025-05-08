import numpy as np
import pandas as pd

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