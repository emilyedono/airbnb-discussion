# app.py
import streamlit as st
import altair as alt
import pandas as pd
import numpy as np



# read in data
airbnb = pd.read_csv('listings-2.csv')

# get rid of columns with identifying info
airbnb.drop(['id', 'host_name', 'listing_url', 'picture_url', 'host_url', 'host_thumbnail_url', 'host_picture_url', 'host_location', 'host_about', 'latitude', 'longitude', 'neighbourhood_group_cleansed'], axis=1, inplace=True)

# Create numerical price and price per person columns
airbnb['price_num'] = airbnb['price'].str.replace('[\$,]', '', regex=True).astype('float')

airbnb['price_per_person'] = airbnb['price_num']/airbnb['accommodates'].replace(0,np.nan)

# Clean host response/acceptance rate to be floats
airbnb['host_response_rate'] = airbnb['host_response_rate'].str.strip('%').astype(float)/100
airbnb['host_acceptance_rate'] = airbnb['host_acceptance_rate'].str.strip('%').astype(float)/100

# Convert t/f columns to binary
def tfconvert(x):
  if x == 't':
    return 1
  elif x == 'f':
    return 0
  else:
    return None

airbnb['host_is_superhost'] = airbnb['host_is_superhost'].apply(tfconvert)
airbnb['host_has_profile_pic'] = airbnb['host_has_profile_pic'].apply(tfconvert)
airbnb['host_identity_verified'] = airbnb['host_identity_verified'].apply(tfconvert)
airbnb['instant_bookable'] = airbnb['instant_bookable'].apply(tfconvert)
airbnb['has_availability'] = airbnb['has_availability'].apply(tfconvert)

# Create host type variable
def host_type(x):
  if x == 1:
    return '1 Listing Host'
  elif x <= 5:
    return '2-5 Listings Host'
  elif x > 5:
    return '>5 Listings Host'
  else:
    return None
  
airbnb['host_type'] = airbnb['host_listings_count'].apply(host_type)

# Create host tenure variable
airbnb['host_tenure'] = pd.to_datetime(airbnb['last_scraped']).dt.year - pd.to_datetime(airbnb['host_since']).dt.year

# remove columns with a lot of nulls that won't be used in analysis
airbnb.drop(['neighbourhood','calendar_updated'], axis=1, inplace=True)

# rename neighbourhood_cleansed as it is the real neighborhood column we are interested in
airbnb.rename(columns={'neighbourhood_cleansed':'neighborhood'}, inplace=True)


## get median price per person per neighborhood
bar1 = alt.Chart(airbnb, title='Median Price per Neighborhood').mark_bar().encode(
    alt.X("median_price:Q").axis(title='Price per Person ($)'),
    alt.Y("neighborhood", sort='-x').axis(title='Boston Neighborhood')
).transform_aggregate(
  median_price='median(price_per_person)',
  groupby=['neighborhood']
)

# get count of listings by neighborhood colored by host type
stackbar = alt.Chart(airbnb, title='Count of Listings by Neighborhood and Host Type').mark_bar().encode(
    alt.X("listings:Q").axis(title='Count of Listings'),
    alt.Y("neighborhood", sort='-x').axis(title='Boston Neighborhood'),
    color="host_type:N"
).transform_aggregate(
  listings='count()',
  groupby=['neighborhood', 'host_type']
)


# Streamlit app
st.title("Boston Airbnb Host Behavior")
st.altair_chart(bar1, use_container_width=True)
st.altair_chart(stackbar, use_container_width=True)