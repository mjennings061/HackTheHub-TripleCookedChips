from django.http import HttpResponse
from django.template import loader
from .models import User

# Import packages
from urllib.request import urlopen
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from datetime import datetime, timedelta
import math
from io import StringIO

def get_elec_sub_90(start_date, end_date):
    # Format URL
    DNO = "12" # London area.
    VOLTAGE = "LV" # Low voltage.
    start_date = start_date.strftime("%d-%m-%Y")
    end_date = end_date.strftime("%d-%m-%Y")
    url = f"https://odegdcpnma.execute-api.eu-west-2.amazonaws.com/development/prices?dno={DNO}&voltage={VOLTAGE}&start={start_date}&end={end_date}"
    
    # Hit the API to get the JSON.
    response = urlopen(url)
    data_json = json.loads(response.read())
    
    # Format as a dataframe.
    df = pd.json_normalize(data_json["data"]["data"])
    df = df.drop(columns="unixTimestamp")
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], format="%H:%M %d-%m-%Y")
    df.set_index("Timestamp", inplace=True)
    
    return df

def get_electricity(start_date="01-10-2022", end_date="01-01-2023", groupBy='M'):
    """Get the weekly electricity as a pandas dataframe. 
    
    start_date: Format "DD-MM-YYYY". Start date.
    end_date: Format "DD-MM-YYYY". End date.
    groupBy: Format 'Y', 'M', or 'D'. Group by year, month or day."""
    
    # Set constants.
    DAY_LIMIT = 90
    
    # Work out if date is over 90 days.
    date_format = "%d-%m-%Y"
    start = datetime.strptime(start_date, date_format)
    end = datetime.strptime(end_date, date_format)
    delta = (end - start).days

    # Split starts and ends into separate dates.
    if delta > DAY_LIMIT:
        nRuns = math.ceil(delta / DAY_LIMIT)
        output_dfs = []
        for iRun in range(nRuns):  
            this_start = start + timedelta(days=(iRun * DAY_LIMIT))
            this_end = this_start + timedelta(days=DAY_LIMIT)
            output_dfs.append(get_elec_sub_90(this_start, this_end))

        # Concatenate dfs.
        elec_prices = pd.concat(output_dfs)
        
    else:
        elec_prices = get_elec_sub_90(start_date, end_date)
        
    # Get mean of each week, month, or day.
    elec_monthly = elec_prices.resample(groupBy).mean()

    return elec_monthly

def calculate_future_spending(monthly_spending_list, predicted_prices_df):
    """Calculate spending for the next N months based on the last bill"""
    # Get last bill value from list.
    last_bill = monthly_spending_list[-1]

    # Current date.
    current_month = datetime.now().date()

    # Filter previous months.
    future_elec = predicted_prices_df.loc[current_month - timedelta(days=32) : ]

    # Calculate percentage difference.
    diff_factor = future_elec['Overall'].pct_change()

    # Calculate future spending.
    future_spending = (1 + diff_factor) * last_bill
    future_spending = future_spending.drop(index=future_spending.index[0])
    future_spending_df = pd.DataFrame(future_spending)

    # Get past timestamps.
    past_elec_prices = predicted_prices_df.loc[: current_month]
    past_timestamps = past_elec_prices.index.values
    past_spending = pd.DataFrame({"Timestamp": past_timestamps, "Overall": monthly_spending_list})
    past_spending["Timestamp"] = pd.to_datetime(past_spending["Timestamp"], format="%d-%m-%Y")
    past_spending.set_index("Timestamp", inplace=True)

    # Combine current and future spending.
    total_spending = pd.concat([past_spending, future_spending_df])
    
    return total_spending

def get_future_elec():
    # Call the function.
    START_DATE = "01-07-2022"
    END_DATE = "01-12-2022"
    GROUP_BY = "M"
    elec_by_month = get_electricity(START_DATE, END_DATE, GROUP_BY)

    # Calculate difference in spending on electricity.
    SPENDING_ON_ELEC = [100, 98, 110]
    total_spend = calculate_future_spending(SPENDING_ON_ELEC, elec_by_month)

    return total_spend

def get_graph(df):
    """Plot a graph from a DataFrame"""
    fig = plt.figure()
    plt.plot(df)
    imgdata = StringIO()
    fig.savefig(imgdata, format="svg")
    imgdata.seek(0)

    data = imgdata.getvalue()
    return data


def index(request):
    user_list = User.objects.values_list()
    template = loader.get_template('spend4castapp/index.html')
    # Get electricity spending data.
    df = get_future_elec()
    # Get plot.
    elec_plot = get_graph(df)
    context = {
        'user_list': user_list,
        'graph': elec_plot,
        }
    return HttpResponse(template.render(context,request))    
    #return HttpResponse("Hello, world! You're at the spend4castapp index.")

def detail(request, user_id):
    return(HttpResponse("You're lookig at user %s" % user_id))

def home(request):
    template = loader.get_template('spend4castapp/home.html')
    return HttpResponse(template.render(request))