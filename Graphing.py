import matplotlib.pyplot as plt
import pandas as pd
import os
from Complexity import calc_complex 
from autoArima import  get_test_data
from ProperFile import predict_complexity, get_model,fields,ASNPs
import matplotlib.cbook as cbook
import matplotlib.dates as mdates
from EWMA import  predict_ansp_HWES
from MultipleSeasonality import  predict_ansp_TBATS

from matplotlib.ticker import (AutoMinorLocator, MultipleLocator)

#get the models
#predict the complexity for the test data
#seperate folders per ansp
#n title, all info in filename
#all seperate
#start from zero

def plot(asnp,field,method,n=365,parametered=True,overwrite=False):
    '''
    asnp: str
    plots the complexity of the asnp for the next 365 days
    '''
    n+=len(get_test_data('Skyguide','CPLX_FLIGHT_HRS'))
    if not overwrite:
        test = ('_parametered' if parametered else '_not_parametered') if field == 'COMPLEXITY_SCORE' else ''
        if os.path.exists(f'GRAPHS/{asnp}(n={n})'):
            if os.path.exists(f'GRAPHS/{asnp}(n={n})/{method}'):
                if f'{field}{test}.png' in os.listdir(f'GRAPHS/{asnp}(n={n})/{method}/'):
                    return
    fig = plt.figure()#figsize=(6.4,5.2))
    ax1 = fig.add_subplot()
    if field != 'COMPLEXITY_SCORE':
        datatrain = get_test_data(asnp,field,return_train=True)
        datatest = get_test_data(asnp,field)
        a=[]
        if method == 'ARIMA':
            a = pd.DataFrame(get_model(asnp, field, 'SARIMA').predict(n_periods=n))
        elif method == 'EWMA':
            a = pd.DataFrame(predict_ansp_HWES(asnp,field,n))
        elif method == 'TBATS':
            a = pd.DataFrame(predict_ansp_TBATS(asnp,field,n))

        a.index= pd.date_range(datatest.index[0], periods=len(a), freq="d")
        #plot train data complexity
        ax1.plot(datatrain, color='blue',label='Train samples')
        #plot test data complexity
        plt.plot(datatest, color='orange',label='Test samples')
        #plot predicted complexity
        ax1.plot(a,label='Forecasts',color='green')
        #add the mse to the title
    else:
        datatrain={}
        datatest={}
        for field1 in ['VERTICAL_INTER_HRS', 'HORIZ_INTER_HRS', 'SPEED_INTER_HRS', 'CPLX_INTER', 'CPLX_FLIGHT_HRS']:
            datatest[field1] = get_test_data(asnp,field1)
            datatrain[field1] = get_test_data(asnp,field1,return_train=True)
            ##################################################################################### FIX THIS
        if parametered:
            predicted_data={}
            for field2 in ['VERTICAL_INTER_HRS', 'HORIZ_INTER_HRS', 'SPEED_INTER_HRS', 'CPLX_INTER', 'CPLX_FLIGHT_HRS']:
                if method == 'ARIMA':
                    predicted_data[field2] = get_model(asnp,field2,'SARIMA').predict(n_periods=n)
                elif method == 'EWMA':
                    predicted_data[field2] = predict_ansp_HWES(asnp,field2,n)
                elif method == 'TBATS':
                    predicted_data[field2] = predict_ansp_TBATS(asnp,field2,n).squeeze()

            a= calc_complex(predicted_data)
        else:
            if method == 'ARIMA':
                a = get_model(asnp,'COMPLEXITY_SCORE','SARIMA').predict(n_periods=n)
            elif method == 'EWMA':
                a = predict_ansp_HWES(asnp,'COMPLEXITY_SCORE',n)
            elif method == 'TBATS':
                a = predict_ansp_TBATS(asnp,'COMPLEXITY_SCORE',n)

        #####################################################################################
        #a = pd.DataFrame(predict_complexity(asnp,n=n,parametered=parametered))
        a.index= pd.date_range(datatest['CPLX_INTER'].index[0], periods=len(a), freq="d")
        #plot train data complexity
        ax1.plot(calc_complex(datatrain), color='blue',label='Train samples')
        #plot test data complexity
        ax1.plot(calc_complex(datatest), color='orange',label='Test samples')
        #plot predicted complexity
        ax1.plot(a,label='Forecasts',color='green')
        #add the mse to the title
    ax1.legend()

    # Set axis ranges; by default this will put major ticks every 25.
    #ax1.set_xlim(0, 200)
    #ax1.set_ylim(0, 200)
    '''
    # Change major ticks to show every 20.
    ax1.xaxis.set_major_locator(MultipleLocator(20))
    ax1.yaxis.set_major_locator(MultipleLocator(20))

   # Change minor ticks to show every 5. (20/4 = 5)
    ax1.xaxis.set_minor_locator(AutoMinorLocator(4))
    ax1.yaxis.set_minor_locator(AutoMinorLocator(4))

   # 1Turn grid on for both major and minor ticks and style minor slightly
    # 1differently.
    ax1.grid(which='major', color='#CCCCCC', linestyle='--')
    ax1.grid(which='minor', color='#CCCCCC', linestyle=':')
    '''

   #ax1.grid(which='both', color='#DDDDDD', linewidth=0.8)
    #ax1.minorticks_on()

    #set the axis labels
    ax1.set_xlabel('Date')
    labels = {'VERTICAL_INTER_HRS': 'Vertical interaction hours',
              'HORIZ_INTER_HRS': 'Horizontal interaction hours',
              'SPEED_INTER_HRS': 'Speed interaction hours', 
              'CPLX_INTER': 'Complex interactions', 
              'CPLX_FLIGHT_HRS': 'Complexity flight hours',
              'COMPLEXITY_SCORE': 'Complexity score'}
    
    ax1.set_ylabel(labels[field])

    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%b'))
    # Rotates and right-aligns the x labels so they don't crowd each other.
    for label in ax1.get_xticklabels(which='major'):
        label.set(rotation=30, horizontalalignment='right')


    #make the y axis begin at 0
    ax1.set_ylim(0)
    #save the plot
    n_actual = n-len(get_test_data('Skyguide','CPLX_FLIGHT_HRS'))
    test = ('_parametered' if parametered else '_not_parametered') if field == 'COMPLEXITY_SCORE' else ''
    print('ansp', asnp, 'field: ', field, 'test: ', test)
    if not os.path.exists(f'GRAPHS/{asnp}(n={n_actual})'):
        os.mkdir(f'GRAPHS/{asnp}(n={n_actual})')
    if not os.path.exists(f'GRAPHS/{asnp}(n={n_actual})/{method}'):
        os.mkdir(f'GRAPHS/{asnp}(n={n_actual})/{method}')
    plt.savefig(f'GRAPHS/{asnp}(n={n_actual})/{method}/{field}{test}.png',dpi=600,pad_inches=0.01,bbox_inches='tight')
    #plt.show()
    plt.cla()
    plt.close(fig)
    

for asnp in ASNPs:
    # plot(asnp,'COMPLEXITY_SCORE','ARIMA',n=0,parametered=False)
    # plot(asnp,'COMPLEXITY_SCORE','EWMA',n=0,parametered=False)
    plot(asnp,'COMPLEXITY_SCORE','TBATS',n=365,parametered=False, overwrite=True)
    # for field in fields:
        # plot(asnp,field,'ARIMA',n=0)
        # plot(asnp,field,'EWMA',n=0)
        # plot(asnp,field,'TBATS',n=0)
        #break
    #break


#do complexity false

#Graph of training test data and predicted data