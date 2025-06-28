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
    return "Superhost"
  elif x == 'f':
    return "Not Superhost"
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

st.title("Boston Airbnb Host Behavior")

# Selectbox: Filter by Origin
neighborhood_options = ["All"] + list(airbnb["neighborhood"].unique())
neighborhood = st.selectbox("Filter by Neighborhood", options=neighborhood_options)

# Slider: Filter by Price per Person
price_range = st.slider("Select Price Range ($)",
                            int(airbnb["price_per_person"].min()), 
                            int(airbnb["price_per_person"].mean() + 3*airbnb["price_per_person"].std()), 
                            ((int(airbnb["price_per_person"].min()), int(airbnb["price_per_person"].mean() + 3*airbnb["price_per_person"].std()))))
# Filter the DataFrame only if a specific neighborhood is selected
if neighborhood != "All":
    filtered_airbnb = airbnb[(airbnb["neighborhood"] == neighborhood) & 
                    (airbnb["price_per_person"].between(*price_range))]
else:
    filtered_airbnb = airbnb[airbnb["price_per_person"].between(*price_range)]

# ## get median price per person per neighborhood
# bar1 = alt.Chart(filtered_airbnb, title='Median Price per Neighborhood').mark_bar().encode(
#     alt.X("median_price:Q").axis(title='Price per Person ($)'),
#     alt.Y("neighborhood", sort='-x').axis(title='Boston Neighborhood')
# ).transform_aggregate(
#   median_price='median(price_per_person)',
#   groupby=['neighborhood']
# )

# # get count of listings by neighborhood colored by host type
# stackbar = alt.Chart(filtered_airbnb, title='Count of Listings by Neighborhood and Host Type').mark_bar().encode(
#     alt.X("listings:Q").axis(title='Count of Listings'),
#     alt.Y("neighborhood", sort='-x').axis(title='Boston Neighborhood'),
#     color="host_type:N"
# ).transform_aggregate(
#   listings='count()',
#   groupby=['neighborhood', 'host_type']
# )

filtered_airbnb = filtered_airbnb.dropna(subset=['host_is_superhost', 'host_type', 'review_scores_rating', 'price_per_person', 'host_tenure', 'host_id'])
# Create a click selection
superhost_click = alt.selection_point(fields=['host_is_superhost'], empty="all")
#superhost_click = alt.selection_point(encodings=['color'])
host_type_click = alt.selection_point(fields=['host_type'], empty='all')

# Bar chart
bar3 = alt.Chart(filtered_airbnb).mark_bar().encode(
    x=alt.X("count()", title='Number of Listings'),
    y=alt.Y("host_type:N", title='Host Type'),
    color=alt.Color("host_is_superhost:N", title="Superhost", scale=alt.Scale(
        domain=["Superhost", "Not Superhost"],
        range=["#2ca02c", "#9467bd"]  # from tableau10
    ), legend=alt.Legend(orient='top')),
    opacity=alt.condition(superhost_click, alt.value(1), alt.value(0.3))
).add_params(superhost_click).properties(
    title=alt.TitleParams(
        text='Total Listings by Host Type and Superhost',
        anchor='middle'
    ))

# Scatter plot
scatter = alt.Chart(filtered_airbnb, title='Review Score vs Price per Person').mark_circle().encode(
    x=alt.X("review_scores_rating:Q", title='Review Score'),
    y=alt.Y("price_per_person:Q", title='Price per Person ($)'),
    color=alt.Color("host_type:N", scale=alt.Scale(scheme='tableau10'), legend=None),
    tooltip=["review_scores_rating", "price_per_person", "host_type"],
    opacity=alt.condition(host_type_click, alt.value(1), alt.value(0.2))
).transform_filter(superhost_click).add_params(host_type_click)

# Area chart
area_chart = alt.Chart(filtered_airbnb).mark_area().encode(
    x=alt.X('host_tenure:O', title='Host Tenure'),
    y=alt.Y('count()', title='# of Listings'),
    color=alt.Color('host_type:N', scale=alt.Scale(scheme='tableau10'), legend=alt.Legend(orient='bottom', title='Host Type')),
    opacity=alt.condition(host_type_click, alt.value(1), alt.value(0.1)),
    tooltip=[alt.Tooltip('host_tenure:O'), alt.Tooltip('host_type:N'), alt.Tooltip('distinct(host_id):Q')]
).transform_filter(superhost_click).properties(
    title=alt.TitleParams(
        text='Count of Listings by Host Tenure and Type',
        anchor='middle'
    )).add_params(host_type_click)

layout = alt.vconcat(
    bar3,
    area_chart,
    scatter
).resolve_scale(color='independent')
# st.altair_chart(bar1, use_container_width=True)
# st.altair_chart(stackbar, use_container_width=True)
# st.altair_chart(bar3)
# st.altair_chart(area_chart)
# st.altair_chart(scatter)
st.altair_chart(layout, use_container_width=True)
# st.altair_chart(bar3, use_container_width=True)

# # Use Streamlit's layout for side-by-side
# col1, col2 = st.columns(2)

# with col1:
#     st.altair_chart(area_chart, use_container_width=True)

# with col2:
#     st.altair_chart(scatter, use_container_width=True)

# testing testing 123

