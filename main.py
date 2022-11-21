import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from geopy.geocoders import Nominatim
import pydeck as pdk
with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
geolocator = Nominatim(user_agent="home-search")
st.title("Rental Properties in Metro Manila")

data = pd.read_csv("property_listings_final.csv", encoding="ISO-8859-1", index_col=0)
data = data.drop("Lot Area", axis=1)

property_types = data["Property Type"].unique()
st.sidebar.selectbox("Property Type", property_types, key="search_property_type")

cities = data["City"].unique()
st.sidebar.selectbox("Location(City)", cities, key="search_city")

total_listing = data.count()["Property Type"]
average_price = data["Price"].mean()

# TOP 5 CHEAPEST
top_five_cheapest_cities = data.sort_values(by="Price",ascending=True)["City"].unique()[0:5]

by_city = data.groupby(["City"])
top_five_cheapest = pd.DataFrame(columns=["City", "Average Price"])

_d = []

for city in top_five_cheapest_cities:
    _d.append([city, int(np.mean(by_city.get_group(city)["Price"]))])

for d in _d:
    top_five_cheapest.loc[len(top_five_cheapest)] = d

top_five_cheapest = top_five_cheapest.sort_values(by="Average Price", ascending=True).reset_index().drop("index", axis=1)

# TOP 5 EXPENSIVE

top_five_expensive_cities = data.sort_values(by="Price",ascending=False)["City"].unique()[0:5]

by_city = data.groupby(["City"])
top_five_expensive = pd.DataFrame(columns=["City", "Average Price"])

_d = []

for city in top_five_expensive_cities:
    _d.append([city, int(np.mean(by_city.get_group(city)["Price"]))])

for d in _d:
    top_five_expensive.loc[len(top_five_expensive)] = d

top_five_expensive = top_five_expensive.sort_values(by="Average Price", ascending=True).reset_index().drop("index", axis=1)

# Row A
a1, a2 = st.columns(2)
a1.metric("Total Listings", total_listing)
a2.metric("Overall Average Price", "₱{:,.2f}".format(average_price))

# Row B
b1, b2 = st.columns(2)
with b1:
    st.markdown("### Top 5 Cheapest")
    st.altair_chart(alt.Chart(top_five_cheapest).mark_bar().encode(x=alt.X("City", sort="y"), y=alt.Y("Average Price")), use_container_width=True)

with b2:
    st.markdown("### Top 5 Expensive")
    st.altair_chart(alt.Chart(top_five_expensive).mark_bar().encode(x=alt.X("City", sort="-y"), y=alt.Y("Average Price")), use_container_width=True)

c1, *_ = st.columns(1)

search_container = st.expander("Search result")
exept_location = []
def getCoordinate(location: str) -> tuple:
    try:
        coordinate = geolocator.geocode(location)
        return (coordinate.latitude, coordinate.longitude)
    except:
        exept_location.append(location)
        return None

def getCenter(longitudes:list, latitudes: list)->tuple:
    try:
        x = np.sum(longitudes)/len(longitudes)
        y = np.sum(latitudes)/len(latitudes)
        return (x, y)
    except:
        return (None, None)

def normalize(values: list):
    def _map(x, in_min, in_max, out_min, out_max):
        return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)
    return [_map(x, min(data["Price"]), max(data["Price"]), 100, 255) for x in values]
    
def on_click_search():
    results_container = search_container.container()
    search_data = data[data["City"]==st.session_state["search_city"]]
    search_data = search_data[search_data["Property Type"]==st.session_state["search_property_type"]]
    results_container.table(search_data.filter(items=["Description","Toatal Floor Area", "Location", "Price"]))
    all_coordinates = [ getCoordinate(location) for location in search_data["Location"].unique()]
    all_coordinates = [x for x in all_coordinates if x is not None]
    coord_price = [x for k, x in search_data[search_data.Location.isin(exept_location)==False].groupby(by="Location").mean().items()]
    coord_price = [x for x in coord_price[0]]
    coord_price = normalize(coord_price)
    df_coordinates = pd.DataFrame(
    all_coordinates,
    columns=['lat', 'lon'])
    df_coordinates["PriceColor"] = coord_price
    longitude, latitude = getCenter(longitudes=df_coordinates["lon"], latitudes=df_coordinates["lat"])
    if longitude is not None or latitude is not None:
        c1.pydeck_chart(pdk.Deck(
            map_style=None,
            initial_view_state=pdk.ViewState(
                latitude=latitude,
                longitude=longitude,
                zoom=13,
                pitch=50,
            ),
            layers=[
                pdk.Layer(
                    'ScatterplotLayer',
                    data=df_coordinates,
                    get_position='[lon, lat]',
                    get_color='[255, 30, 0, PriceColor]',
                    get_radius=100
                ),
            ],
        ))
    else:
        c1.text("Location has no results.")

st.sidebar.button("Search", on_click=on_click_search)
