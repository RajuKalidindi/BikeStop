import os
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from wordcloud import WordCloud
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use the Agg backend to save the figure to a file instead of displaying it

def generate_bike_usage_chart(bike_usage, path):
    bike_counts = pd.Series(bike_usage).value_counts()
    top_bikes = bike_counts[:10].sort_index()
    top_bikes.index = top_bikes.index.astype(str)
    plt.figure(figsize=(10, 8))
    plt.bar(top_bikes.index, top_bikes)
    plt.title('Top 10 Most Used Bikes')
    plt.xlabel('Bike ID')
    plt.ylabel('Usage Count')
    plt.savefig(path)
    plt.close()

def generate_customer_usage_pie_chart(customer_usage, path):
    customer_counts = pd.Series(customer_usage).value_counts()
    top_customers = customer_counts[:5]
    labels = [f'Customer {id}: {freq} rides' for id, freq in zip(top_customers.index, top_customers)]
    plt.figure(figsize=(10, 8))
    plt.pie(top_customers, labels=labels, autopct='%1.1f%%')
    plt.title('Top 5 Active Customers')
    plt.savefig(path)
    plt.close()

def generate_line_chart(start_times, path):
    start_hours = pd.Series(start_times).dt.hour
    hour_counts = start_hours.value_counts().sort_index()
    plt.figure(figsize=(10, 8))
    plt.plot(hour_counts.index, hour_counts)
    plt.title('Bike Rentals by Hour of Day')
    plt.xlabel('Hour of Day')
    plt.ylabel('Frequency')
    plt.savefig(path)
    plt.close()

def generate_heatmap(locations, path):
    df = pd.DataFrame(locations, columns=['Start', 'End'])
    matrix = pd.crosstab(df['Start'], df['End'])
    plt.figure(figsize=(10, 8))
    sns.heatmap(matrix, cmap='viridis')
    plt.title('Most Travelled Routes')
    plt.savefig(path)
    plt.close()

def generate_bar_chart(ratings, path):
    plt.hist(ratings, bins=[1, 2, 3, 4, 5, 6], align='left', rwidth=0.8)
    plt.xticks(range(1, 6))
    plt.xlabel('Star Rating')
    plt.ylabel('Frequency')
    plt.title('Review Ratings')
    plt.savefig(path)
    plt.close()

def generate_wordcloud(comments):
    stop_words = set(stopwords.words('english'))
    word_tokens = word_tokenize(comments)
    filtered_comments = [w for w in word_tokens if not w in stop_words]
    wordcloud = WordCloud(width=1000, height=500).generate(' '.join(filtered_comments))
    return wordcloud

def save_wordcloud(wordcloud, path):
    wordcloud.to_file(path)