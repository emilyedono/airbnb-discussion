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
    return True
  elif x == 'f':
    return False
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


# Selectbox: Filter by Origin
neighborhood_options = ["All"] + list(airbnb["neighborhood"].unique())
neighborhood = st.selectbox("Filter by Neighborhood", options=neighborhood_options)

# Filter the DataFrame only if a specific neighborhood is selected
if neighborhood != "All":
    filtered_airbnb = airbnb[airbnb["neighborhood"] == neighborhood]
else:
    filtered_airbnb = airbnb

## get median price per person per neighborhood
bar1 = alt.Chart(filtered_airbnb, title='Median Price per Neighborhood').mark_bar().encode(
    alt.X("median_price:Q").axis(title='Price per Person ($)'),
    alt.Y("neighborhood", sort='-x').axis(title='Boston Neighborhood')
).transform_aggregate(
  median_price='median(price_per_person)',
  groupby=['neighborhood']
)

# get count of listings by neighborhood colored by host type
stackbar = alt.Chart(filtered_airbnb, title='Count of Listings by Neighborhood and Host Type').mark_bar().encode(
    alt.X("listings:Q").axis(title='Count of Listings'),
    alt.Y("neighborhood", sort='-x').axis(title='Boston Neighborhood'),
    color="host_type:N"
).transform_aggregate(
  listings='count()',
  groupby=['neighborhood', 'host_type']
)

# Scatter plot using Altair
scatter = alt.Chart(filtered_airbnb, title='Scatter Plot of Review Score and Price per Person').mark_circle().encode(
    x=alt.X("review_scores_rating:Q").axis(title='Review Score'),
    y=alt.Y("price_per_person:Q").axis(title='Price per Person ($)'),
    color="host_type:N",
    tooltip=["review_scores_rating", "price_per_person", "host_type"]
).interactive()

filtered_airbnb_sup = filtered_airbnb.dropna(subset=['host_is_superhost', 'host_type'])

bar3 = alt.Chart(filtered_airbnb_sup, title='Total Listings by Host Type and Superhost').mark_bar().encode(
  x=alt.X("host_type").axis(title='Host Type'),
  y=alt.Y("count()", title='Number of Listings'),
  color=alt.Color("host_is_superhost:N", title = "Superhost")
)
filtered_airbnb['host_since'] = pd.to_datetime(filtered_airbnb['host_since'])
filtered_airbnb['host_join_year'] = filtered_airbnb['host_since'].dt.year

filtered_airbnb_tenure = filtered_airbnb.dropna(subset=['host_tenure', 'host_type'], inplace=True)

area_chart = alt.Chart(filtered_airbnb, title='Total Hosts by Tenure and Host Type').mark_area().encode(
    x=alt.X('host_tenure:O', title='Host Tenure'),
    y=alt.Y('host_id', aggregate='distinct', title='# of Hosts', stack='zero'),
    color=alt.Color('host_type:N', title='Host Type'),
    tooltip=['host_tenure:N', 'host_type:N', alt.Tooltip('distinct(host_id):Q', title='Distinct Count of Hosts')]
)

# Streamlit app
st.title("Boston Airbnb Host Behavior")
# st.altair_chart(bar1, use_container_width=True)
# st.altair_chart(stackbar, use_container_width=True)
st.altair_chart(bar3)
st.altair_chart(area_chart)
st.altair_chart(scatter)