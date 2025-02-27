
import matplotlib.pyplot as plt
import pandas as pd
from complexity_calculation import calculate_scores_daily
from preprocessing import *
from statsmodels.tsa.seasonal import MSTL
from statsmodels.tsa.seasonal import DecomposeResult

# Sktime imports
from sktime.forecasting.tbats import TBATS
from sktime.forecasting.statsforecast import StatsForecastAutoTBATS
from sktime.utils.plotting import plot_series

from sklearn.metrics import mean_absolute_percentage_error as mape
from statsforecast import StatsForecast
import pickle

import multiprocessing as mp

import csv

import os

def MultipleSeasonalityDecomp(df, iterate):
    # mstl = MSTL(df, periods=[7, 365])
    
    print("I am working")
    model = [MSTL(season_length=[7,365])]
    sf = StatsForecast(models = model, freq = 'W')
    sf = sf.fit(df = df)
    sf.fitted_[0, 0].model_.tail(24 * 28).plot(subplots=True, grid=True)
    plt.tight_layout()
    plt.show()
    # forecasts = sf.predict()
    # res = mstl.fit()
    # res.plot()
    # plt.show()
    
    # sf.dshw(df, period1 = 7, period2 = 365, h = 365)

def forecast_TBATS(df, periods):
    # Split data
    slice = int(0.75*len(df))
    train = df[:slice].copy()
    test = df[slice:]

    # Fit and predict model
    model = TBATS(sp=periods, use_trend=True, use_box_cox=True, use_damped_trend=True)
    # print(train)
    model.fit(train)
    fh = np.arange(len(test))
    predicted_values = model.predict(fh)

    plot_series(train, test, predicted_values, labels=['Train', 'Test', 'Predicted'])
    plt.show()

    # Calculate mape
    # mape = mape(test, predicted_values)

    return train, test, predicted_values

def computeModel(df, ANSP, field, periods=[365,7]):
    df_ansp = df.loc[df['ENTITY_NAME'] == ANSP].copy()

    df_scores = calculate_scores_daily(df_ansp)

    df_field = df_scores.loc[:, field].to_frame()
    df_field.index.freq = pd.infer_freq(df_field.index)

    slice = int(0.75 * len(df_field))
    train = df_field[:slice]
    test = df_field[slice:]

    model = StatsForecastAutoTBATS(periods).fit(train)
    pickle.dump(model, open(f"TBATS/{subfolder}/{ANSP}{field}.pkl", 'wb'))
    return model

def predict_ansp_TBATS(ANSP, field, n):
    model = None
    try:
        model = pickle.load(open(f"TBATS/YEAR_WEEK/{ANSP}{field}.pkl", 'rb'))
    except:
        raise Exception(f"Model {ANSP}{field} not found")
    n = np.arange(n)
    return model.predict(n)

fields = ['CPLX_FLIGHT_HRS', 'CPLX_INTER', 'HORIZ_INTER_HRS', 'SPEED_INTER_HRS', 'VERTICAL_INTER_HRS', 'Complexity_score']
ANSPs = ['ANS CR', 'ANS Finland', 'ARMATS', 'Albcontrol', 'Austro Control', 'Avinor (Continental)', 'BULATSA', 'Croatia Control', 'DCAC Cyprus', 'DFS', 'DHMI', 'DSNA', 'EANS', 'ENAIRE', 'ENAV', 'HCAA', 'HungaroControl', 'IAA', 'LFV', 'LGS', 'LPS', 'LVNL', 'M-NAV', 'MATS', 'MOLDATSA', 'MUAC', 'NATS (Continental)', 'NAV Portugal (Continental)', 'NAVIAIR', 'Oro Navigacija', 'PANSA', 'ROMATSA', 'SMATSA', 'Sakaeronavigatsia', 'Skyguide', 'Slovenia Control', 'UkSATSE', 'skeyes']
plotting = False
subfolder = 'YEAR_WEEK'

# Importing data
df = pd.read_csv('Datasets/split_2017-2019.csv', index_col='FLT_DATE', parse_dates=True, date_format='%d-%m-%Y')
df.dropna(inplace=True)
df = calculate_scores_daily(df)

def main(ANSP):
    predicted_values = pd.DataFrame()
    test_values = pd.DataFrame()
    train_values = pd.DataFrame()
    mape_componentwise = None
    mape_total = None

    for field in fields:
        # Check if model already exists
        try:
            model = pickle.load(open(f"TBATS/{subfolder}/{ANSP}{field}.pkl", 'rb'))
        except:
            model = computeModel(df, ANSP, field)

        # Get test data
        df_ansp = df.loc[df['ENTITY_NAME'] == ANSP].copy()
        df_field = df_ansp.loc[:, field].to_frame()
        df_field.index.freq = pd.infer_freq(df_field.index)
        slice = int(0.75 * len(df_field))
        train = df_field[:slice]
        test = df_field[slice:]

        # Update dataframe
        fh = np.arange(len(test))
        predicted_values[field] = model.predict(fh)
        test_values[field] = test
        train_values[field] = train

        if field == 'Complexity_score':
            mape_total = mape(test, predicted_values[field])


    predicted_complexity = calculate_scores_daily(predicted_values.copy())

    test_complexity = calculate_scores_daily(test_values)
    mape_componentwise = mape(test_complexity['Complexity_score'], predicted_complexity['Complexity_score'])

    # Plotting
    if plotting:
        fig, axs = plt.subplots(2, 1) 
        axs[0].set_title(f'{ANSP} - Componentwise Prediction')
        train_values['Complexity_score'].plot(legend=True, label='Train', ax=axs[0])
        test_complexity['Complexity_score'].plot(legend=True, label='Test', ax=axs[0])
        predicted_complexity['Complexity_score'].plot(legend=True, label='Predicted', ax=axs[0])

        axs[1].set_title(f'{ANSP} - Total Prediction')
        train_values['Complexity_score'].plot(legend=True, label='Train', ax=axs[1])
        test_complexity['Complexity_score'].plot(legend=True, label='Test', ax=axs[1])
        predicted_values['Complexity_score'].plot(legend=True, label='Predicted', ax=axs[1])
        plt.show()

        # Plot componentwise component predictions in one figure
        fig, axs = plt.subplots(len(fields), 1)
        for field in fields:
            axs[fields.index(field)].set_title(f'{ANSP} - {field}')
            train_values[field].plot(legend=True, label='Train', ax=axs[fields.index(field)])
            test_values[field].plot(legend=True, label='Test', ax=axs[fields.index(field)])
            predicted_values[field].plot(legend=True, label='Predicted', ax=axs[fields.index(field)])
        plt.show()

    with open(f"TBATS/mape_{subfolder}.csv", 'a', newline='') as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow([ANSP, mape_total, mape_componentwise])
    print(f"{ANSP} Total mape: {mape_total}")
    print(f"{ANSP} Componentwise mape: {mape_componentwise}")

if __name__ == '__main__':
    
    # Multiple cores whooo!
    with mp.Pool(processes=8) as pool:
        pool.map(main, ANSPs)