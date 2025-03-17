import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from datetime import datetime

# Функция для загрузки данных
def load_data(file):
    data = pd.read_csv(file)
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    return data

# Вычисление скользящего среднего и стандартного отклонения
def calculate_rolling_stats(data):
    data['rolling_mean'] = data.groupby('city')['temperature'].transform(lambda x: x.rolling(window=30, min_periods=1).mean())
    data['rolling_std'] = data.groupby('city')['temperature'].transform(lambda x: x.rolling(window=30, min_periods=1).std())
    data['anomaly'] = np.abs(data['temperature'] - data['rolling_mean']) > 2 * data['rolling_std']
    return data

# Функция для получения текущей температуры через OpenWeatherMap API (синхронный метод)
def get_current_weather(api_key, city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        temperature = data['main']['temp']
        weather_description = data['weather'][0]['description']
        return temperature, weather_description
    else:
        error_data = response.json()
        return None, error_data

# Функция для определения сезона
def get_season(month):
    if month in [12, 1, 2]:
        return "Зима"
    elif month in [3, 4, 5]:
        return "Весна"
    elif month in [6, 7, 8]:
        return "Лето"
    elif month in [9, 10, 11]:
        return "Осень"

def main():
    # Дизайн хоть какой то ...
    st.markdown(
        """
        <style>
        .stApp {
            background-image: url("https://images.unsplash.com/photo-1536514498073-50e69d39c6cf?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2071&q=80");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            border-radius: 5px;
            padding: 10px 20px;
            font-size: 16px;
        }
        .stMarkdown h1 {
            color: #ffffff;
            text-shadow: 2px 2px 4px #000000;
        }
        .stMarkdown h2 {
            color: #ffffff;
            text-shadow: 2px 2px 4px #000000;
        }
        .stMarkdown h3 {
            color: #ffffff;
            text-shadow: 2px 2px 4px #000000;
        }
        .stMarkdown p {
            color: #ffffff;
            font-size: 18px;
        }
        .stTextInput>div>div>input {
            background-color: #ffffff;
            color: #000000;
        }
        .stAlert {
            background-color: #ffcccc;
            color: #000000;
            border-radius: 5px;
            padding: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.title('Анализ температурных данных с помощью Streamlit и мониторинг текущей температуры')

    # Загрузка CSV
    uploaded_file = st.file_uploader("Выберите CSV-файл", type=['csv'])
    if uploaded_file is not None:
        data = load_data(uploaded_file)
        data = calculate_rolling_stats(data)

        # Выбор города
        city = st.selectbox('Выберите город', data['city'].unique())
        city_data = data[data['city'] == city]

        # Визуализация
        st.subheader(f'Температура в городе {city}')
        fig, ax = plt.subplots(figsize=(20, 10))
        ax.plot(city_data['timestamp'], city_data['temperature'], label='Температура', color='blue')
        ax.plot(city_data['timestamp'], city_data['rolling_mean'], label='Скользящее среднее', color='red')
        ax.scatter(city_data[city_data['anomaly']]['timestamp'], city_data[city_data['anomaly']]['temperature'], color='yellow', label='Аномалии')
        ax.set_title(f'Температура в городе {city}', color='black')
        ax.set_xlabel('Дата', color='black')
        ax.set_ylabel('Температура (°C)', color='black')
        ax.tick_params(colors='black')
        ax.legend()
        ax.set_facecolor('#00000000')
        fig.patch.set_facecolor('#00000000')
        st.pyplot(fig)

        # Сезонные профили
        st.subheader(f'Сезонные профили для города {city}')
        seasons = city_data['season'].unique()
        for season in seasons:
            season_data = city_data[city_data['season'] == season]
            mean_temp = season_data['temperature'].mean()
            std_temp = season_data['temperature'].std()
            st.write(f"{season}: Средняя температура = {mean_temp:.1f}°C, Стандартное отклонение = {std_temp:.1f}°C")

        # Форма для ввода API-ключа
        st.subheader('Мониторинг текущей температуры')
        api_key = st.text_input("Введите API-ключ OpenWeatherMap", type="password")

        if api_key:  # Если ключ введен
            current_temp, weather_data = get_current_weather(api_key, city)
            if current_temp is not None:
                st.write(f"Текущая температура в {city}: {current_temp}°C")
                st.write(f"Погода: {weather_data}")

                # Сравнение с историческими данными
                season = get_season(datetime.now().month)
                historical_data = city_data[city_data['season'] == season]
                mean_temp = historical_data['temperature'].mean()
                std_temp = historical_data['temperature'].std()

                if abs(current_temp - mean_temp) > 2 * std_temp:
                    st.write("Текущая температура является аномальной для этого сезона.")
                else:
                    st.write("Текущая температура находится в пределах нормы.")
            else:
                if weather_data.get("cod") == 401:
                    st.error(f"Ошибка: {weather_data['message']}")
                else:
                    st.error("Не удалось получить данные о текущей температуре. Проверьте название города.")
        else:  # Если ключ не введен
            st.warning("Введите API-ключ для получения текущей температуры.")

if __name__ == '__main__':
    main()
