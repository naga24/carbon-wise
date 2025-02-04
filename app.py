import streamlit as st
import google.generativeai as genai
import pandas as pd
import matplotlib.pyplot as plt
import re

# Set page title and favicon
st.set_page_config(page_title="Sustainable Living", page_icon="🌍", layout="centered")

# Get API key
API_KEY = st.sidebar.text_input("Enter your Gemini API Key", type="password")

# Configure Gemini API
genai.configure(api_key=API_KEY)

# Carbon footprint calculation constants
ABOUT = {
    "Carbon Footprint": "Carbon footprint is the total amount of greenhouse gases (including carbon dioxide and methane) that are generated by our actions. It is measured in units of carbon dioxide (CO2) and is usually expressed in kilograms per day or year. This app calculates your carbon footprint based on your daily travel, energy usage, diet, and other factors and suggests ways to reduce it with personalized recommendations and a sustainable meal plan diet using LLM.",
}
TRANSPORT_EMISSIONS = {
    "Car": 0.2, "Bus": 0.1, "Bike": 0.0, "Train": 0.05, "Walking": 0.0
}

CAR_EMISSIONS = {
    "Electric": 0.05, "Hybrid": 0.12, "Gasoline": 0.25, "Diesel": 0.30
}

ENERGY_EMISSIONS = {"Solar": 0.1, "Wind": 0.05, "Natural Gas": 0.6, "Coal": 1.0, "Electricity mix": 0.5}
DIET_EMISSIONS = {"Meat-heavy": 2.5, "Balanced": 1.5, "Vegetarian": 1.0, "Vegan": 0.7}
TRAVEL_EMISSIONS = {"Monthly": 3.0, "Quarterly": 1.5, "Annually": 0.5, "Never": 0.0}

# Function to calculate carbon footprint
def calculate_carbon_footprint(inputs):
    transport_footprint = inputs["transport_km"] * TRANSPORT_EMISSIONS.get(inputs["transport_mode"], 0)
    car_footprint = CAR_EMISSIONS.get(inputs["car_type"], 0) * inputs["transport_km"]
    public_transport_footprint = TRANSPORT_EMISSIONS.get(inputs["secondary_transport"], 0) * inputs["public_transport_freq"]

    energy_footprint = inputs["energy_usage"] * ENERGY_EMISSIONS.get(inputs["energy_source"], 0) / inputs["household_size"]
    diet_footprint = DIET_EMISSIONS.get(inputs["diet"], 0)
    travel_footprint = TRAVEL_EMISSIONS.get(inputs["flight_frequency"], 0)

    total_footprint = transport_footprint + car_footprint + public_transport_footprint + energy_footprint + diet_footprint + travel_footprint
    return total_footprint, {
        "Transport": transport_footprint + car_footprint + public_transport_footprint,
        "Energy": energy_footprint,
        "Diet": diet_footprint,
        "Travel": travel_footprint
    }

# Function for recommendations using Gemini AI
def generate_recommendations(model, user_inputs):
    prompt = f"""
    User details:
    - Transport: {user_inputs["transport_mode"]} ({user_inputs["car_type"]})
    - Energy source: {user_inputs["energy_source"]}
    - Diet: {user_inputs["diet"]}
    - Flight frequency: {user_inputs["flight_frequency"]}
    
    Provide 3 personalized eco-friendly recommendations.
    """
    response = model.generate_content(prompt)
    return response.text.strip()

def parse_meal_plan(response_text):
    """
    Extracts meal category percentages from the AI-generated response.
    Expected format in response: "Breakfast: 25%, Lunch: 35%, Dinner: 30%, Snacks: 10%"
    """
    meal_plan = {}
    matches = re.findall(r"(\w+):\s*(\d+)%", response_text)  # Extract categories & percentages
    for category, percentage in matches:
        meal_plan[category] = int(percentage)
    
    # Ensure total is 100% (normalize if needed)
    total = sum(meal_plan.values())
    if total != 100 and total > 0:
        meal_plan = {k: (v / total) * 100 for k, v in meal_plan.items()}  
    
    return meal_plan if meal_plan else {"Breakfast": 25, "Lunch": 35, "Dinner": 30, "Snacks": 10}  # Fallback values

# Function to show meal plan pie chart
def show_meal_plan_pie_chart(country, diet):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
    Generate a low carborn diet breakdown for a person in {country} who follows a {diet} diet.Provide percentages for meal categories: Breakfast, Lunch, Dinner, Snacks, summing to 100%."""
    response = model.generate_content(prompt)

    # Example static values (replace with parsed AI response)
    # meal_data = {"Breakfast": 25, "Lunch": 35, "Dinner": 30, "Snacks": 10}
    meal_data = parse_meal_plan(response.text)
    fig, ax = plt.subplots()
    ax.pie(meal_data.values(), labels=meal_data.keys(), autopct="%1.1f%%", startangle=140)
    ax.set_title(f"{country} - {diet} Meal Plan Breakdown")
    st.pyplot(fig)
    return response.text.strip()

# Function to visualize carbon footprint breakdown
def show_footprint_chart(footprint_details):
    df = pd.DataFrame(list(footprint_details.items()), columns=["Category", "Emissions"])
    fig, ax = plt.subplots()
    ax.bar(df["Category"], df["Emissions"], color=["blue", "green", "red", "purple"])
    ax.set_ylabel("kg CO2")
    ax.set_title("Carbon Footprint Breakdown")
    st.pyplot(fig)

# Sidebar Navigation
st.sidebar.title("🌱 Sustainability Assistant")
page = st.sidebar.radio("Navigate", ["About", "Carbon Footprint Calculator", "Recommendations", "Meal Plan"])

country = st.sidebar.text_input("Enter Your Country", "India")

# Collect user inputs
if "user_inputs" not in st.session_state:
    st.session_state.user_inputs = {}

with st.sidebar.expander("Enter Your Details"):
    st.session_state.user_inputs["transport_km"] = st.number_input("Daily travel distance (km)", min_value=0.0)
    st.session_state.user_inputs["transport_mode"] = st.selectbox("Primary transport", list(TRANSPORT_EMISSIONS.keys()))
    st.session_state.user_inputs["secondary_transport"] = st.selectbox("Secondary transport", list(TRANSPORT_EMISSIONS.keys()))
    st.session_state.user_inputs["car_type"] = st.selectbox("Car type", list(CAR_EMISSIONS.keys()))
    st.session_state.user_inputs["public_transport_freq"] = st.slider("Public transport frequency", 0, 30, 5)
    st.session_state.user_inputs["energy_usage"] = st.number_input("Daily energy usage (kWh)", min_value=0.0)
    st.session_state.user_inputs["household_size"] = st.number_input("Household size", min_value=1, value=1)
    st.session_state.user_inputs["energy_source"] = st.selectbox("Primary energy source", list(ENERGY_EMISSIONS.keys()))
    st.session_state.user_inputs["diet"] = st.selectbox("Diet type", list(DIET_EMISSIONS.keys()))
    st.session_state.user_inputs["flight_frequency"] = st.selectbox("Flight frequency", list(TRAVEL_EMISSIONS.keys()))
    

if page == "Carbon Footprint Calculator":
    st.header("🌍 Carbon Footprint Calculator")
    total_footprint, footprint_details = calculate_carbon_footprint(st.session_state.user_inputs)
    st.success(f"Your estimated carbon footprint is **{total_footprint:.2f} kg CO2 per day**.")

    show_footprint_chart(footprint_details)

if page == "About":
    st.sidebar.header("💡 About")
    for key, value in ABOUT.items():
        st.image("N1.webp", "Image Credits: Google Images")
        st.sidebar.write(value)

elif page == "Recommendations":
    st.header("💡 Personalized Recommendations")
    model = genai.GenerativeModel("gemini-1.5-flash")
    recommendations = generate_recommendations(model, st.session_state.user_inputs)
    st.write(recommendations)

elif page == "Meal Plan":
    st.header("🥗 Sustainable Meal Plan")
    recommendations = show_meal_plan_pie_chart(country, st.session_state.user_inputs["diet"])
    st.write(recommendations)

st.write("💡 _Try making sustainable choices to reduce your footprint!_")
st.info("Did you know? In India, Carbon Footprint is 1-2 tons per person per year")

st.markdown("---")

st.markdown("Made with ❤️ by Nagarjun")