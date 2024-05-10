import matplotlib
matplotlib.use('Agg')

from flask import Flask, render_template, jsonify, request, redirect, url_for
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import re
import psutil
import time
import os

# Initialize Flask application with the template folder specified
app = Flask(__name__, template_folder="templates")

# Load the CSV file
df = pd.read_csv("log_data.csv")

# Function to extract digits from text
def extract_digits(text):
    if not text:
        return 0
    return sum(c.isdigit() for c in text)

# Function to extract words from text
def extract_words(text):
    if not text:
        return 0
    return len(text.split())

# Function to extract error code from text
def extract_error_code(text):
    if not text:
        return 'Unknown'
    match = re.search(r'Error Code: (\w+)', text)
    return match.group(1) if match else 'Unknown'

# Function to extract timestamp from text
def extract_timestamp(text):
    if not text:
        return 'Unknown'
    match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', text)
    return match.group(1) if match else 'Unknown'

# Function to calculate the average number of words per log entry
def calculate_average_words(data):
    total_words = sum(extract_words(entry['Log Message']) for entry in data)
    return total_words / len(data)

# Function to calculate the average number of digits per log entry
def calculate_average_digits(data):
    total_digits = sum(extract_digits(entry['Log Message']) for entry in data)
    return total_digits / len(data)

# Function to count the number of log entries per error code
def count_log_entries_per_error_code(data):
    error_codes_count = {}
    for entry in data:
        error_code = extract_error_code(entry['Log Message'])
        error_codes_count[error_code] = error_codes_count.get(error_code, 0) + 1
    return error_codes_count

# Function to calculate the distribution of log severities
def calculate_log_severity_distribution(data):
    log_severity_counts = {}
    for entry in data:
        log_severity = entry['Log Severity']
        log_severity_counts[log_severity] = log_severity_counts.get(log_severity, 0) + 1
    return log_severity_counts

# Function to calculate the distribution of log levels
def calculate_log_level_distribution(data):
    log_level_counts = {}
    for entry in data:
        log_level = entry['Log Level']
        log_level_counts[log_level] = log_level_counts.get(log_level, 0) + 1
    return log_level_counts

# Function to calculate the distribution of log types
def calculate_log_type_distribution(data):
    log_type_counts = {}
    for entry in data:
        log_type = entry['Log Type']
        log_type_counts[log_type] = log_type_counts.get(log_type, 0) + 1
    return log_type_counts

# Function to calculate the distribution of user activities
def calculate_user_activity_distribution(data):
    user_activity_counts = {}
    for entry in data:
        user_activity = entry['User Activity']
        user_activity_counts[user_activity] = user_activity_counts.get(user_activity, 0) + 1
    return user_activity_counts

# Function to calculate uptime
def calculate_uptime():
    boot_time = psutil.boot_time()
    current_time = time.time()
    uptime_seconds = current_time - boot_time
    uptime_hours = uptime_seconds / 3600
    return round(uptime_hours, 2)

# Function to get traffic statistics
def get_traffic_statistics():
    network_io = psutil.net_io_counters()
    return network_io.bytes_sent, network_io.bytes_recv

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/log_data')
def log_data():
    try:
        # Replace NaN values with None to ensure valid JSON
        log_data_cleaned = df.where(pd.notnull(df), None)
        
        # Convert DataFrame to dictionary
        log_data_dict = log_data_cleaned.to_dict(orient='records')
        
        # Extract the required fields and counts
        log_level_counts = df['Log Level'].value_counts().to_dict()
        log_type_counts = df['Log Type'].value_counts().to_dict()
        log_severity_counts = df['Log Severity'].value_counts().to_dict()
        user_activity_counts = df['User Activity'].value_counts().to_dict()
        
        # Return JSON response with the required data
        return jsonify({
            'log_data': log_data_dict,
            'log_level_counts': log_level_counts,
            'log_type_counts': log_type_counts,
            'log_severity_counts': log_severity_counts,
            'user_activity_counts': user_activity_counts
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/visualization')
def visualization():
    try:
        # Analyze log levels
        log_level_counts = df['Log Level'].value_counts()
        log_level_plot = plot_bar_chart(log_level_counts, 'Distribution of Log Levels', 'Log Level', 'Frequency', 'skyblue')

        # Analyze log types
        log_type_counts = df['Log Type'].value_counts()
        log_type_plot = plot_bar_chart(log_type_counts, 'Distribution of Log Types', 'Log Type', 'Frequency', 'lightgreen')

        # Analyze log severities
        log_severity_counts = df['Log Severity'].value_counts()
        log_severity_plot = plot_bar_chart(log_severity_counts, 'Distribution of Log Severities', 'Log Severity', 'Frequency', 'salmon')

        # Analyze user activities
        user_activity_counts = df['User Activity'].value_counts()
        user_activity_plot = plot_bar_chart(user_activity_counts, 'Distribution of User Activities', 'User Activity', 'Frequency', 'gold')

        # Analyze log message lengths
        log_message_lengths_plot = plot_histogram(df['Log Message'].apply(len), 'Distribution of Log Message Lengths', 'Length', 'Frequency', 'orange')

        # Scatter plot of log level vs log message length
        scatter_plot = plot_scatter(df['Log Level'], df['Log Message'].apply(len), 'Log Level vs Log Message Length')

        # Stacked bar chart of log level vs log severity
        stacked_bar_chart = plot_stacked_bar_chart(df, 'Log Level', 'Log Severity')
        
        # Calculate the distribution of log severities for the pie chart
        log_severity_pie_counts = df['Log Severity'].value_counts()
        log_severity_pie = plot_pie_chart(log_severity_pie_counts, 'Distribution of Log Severities')

        # Calculate the distribution of log types for the line chart
        log_type_line_counts = df['Log Type'].value_counts()
        log_type_line = plot_line_chart(log_type_line_counts, 'Distribution of Log Types', 'Log Type', 'Frequency')  # Adjusted for missing arguments

        return render_template('visualization.html', 
                            log_level_plot=log_level_plot,
                            log_type_plot=log_type_plot,
                            log_severity_plot=log_severity_plot,
                            user_activity_plot=user_activity_plot,
                            log_message_lengths_plot=log_message_lengths_plot,
                            scatter_plot=scatter_plot,
                            stacked_bar_chart=stacked_bar_chart,
                            log_severity_pie=log_severity_pie,
                            log_type_line=log_type_line
                            )
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        keyword = request.form['keyword']
        # Filter data based on the keyword
        filtered_data = df[df['Log Message'].str.contains(keyword, case=False)]
        return render_template('search_results.html', keyword=keyword, search_results=filtered_data)
    return render_template('search.html')


@app.route('/monitoring')
def monitoring():
    try:
        # Traffic Statistics
        traffic_stats = {
            'sent': 1000,  # Example value for sent traffic
            'received': 1500  # Example value for received traffic
        }

        # Calculate uptime
        uptime = calculate_uptime()
        
        # System CPU Utilization
        cpu_percent = psutil.cpu_percent()
        
        # System Memory Usage
        memory_usage = psutil.virtual_memory().percent
        
        # System Swap Memory Usage
        swap_memory_usage = psutil.swap_memory().percent
        
        # System Disk Usage
        disk_usage = psutil.disk_usage('/').percent
        
        # System Boot Time
        boot_time = psutil.boot_time()
        
        # System Users
        users = psutil.users()
        
        # Number of Running Processes
        num_processes = len(psutil.pids())
        
        # Number of CPU Cores
        num_cores = psutil.cpu_count()
        
        # Load Average
        load_avg = psutil.getloadavg()
        
        # Battery Information (if available)
        battery_info = None
        if hasattr(psutil, 'sensors_battery'):
            battery_info = psutil.sensors_battery()
        
        # System Temperatures (if available)
        temperatures = None
        if hasattr(psutil, 'sensors_temperatures'):
            temperatures = psutil.sensors_temperatures()
        
        # System Fan Speeds (if available)
        fan_speeds = None
        if hasattr(psutil, 'sensors_fans'):
            fan_speeds = psutil.sensors_fans()
        
        # Running Processes
        process_list = [psutil.Process(pid) for pid in psutil.pids()]
        
        # Pass the data to the template for rendering
        return render_template('monitoring_dashboard.html', 
                               traffic_stats=traffic_stats,  # Pass traffic_stats
                               uptime=uptime, 
                               cpu_percent=cpu_percent,
                               memory_usage=memory_usage, 
                               swap_memory_usage=swap_memory_usage,
                               disk_usage=disk_usage, 
                               boot_time=boot_time, 
                               users=users, 
                               num_processes=num_processes,
                               num_cores=num_cores, 
                               load_avg=load_avg, 
                               battery_info=battery_info,
                               temperatures=temperatures, 
                               fan_speeds=fan_speeds, 
                               process_list=process_list)

    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/send_alert', methods=['GET'])
def send_alert():
    # Code to send alert via email
    # Replace this with your email sending logic
    try:
        # Your email sending logic here
        # For example:
        # send_email()
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def plot_bar_chart(data, title, xlabel, ylabel, color):
    plot_image = io.BytesIO()
    plt.figure(figsize=(8, 6))
    data.plot(kind='bar', color=color)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(plot_image, format='png')
    plot_image.seek(0)
    plot_image_encoded = base64.b64encode(plot_image.getvalue()).decode('utf-8')
    plot_image.close()
    return plot_image_encoded

def plot_histogram(data, title, xlabel, ylabel, color):
    plot_image = io.BytesIO()
    plt.figure(figsize=(8, 6))
    plt.hist(data, bins=20, color=color, edgecolor='black')
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(plot_image, format='png')
    plot_image.seek(0)
    plot_image_encoded = base64.b64encode(plot_image.getvalue()).decode('utf-8')
    plot_image.close()
    return plot_image_encoded

def plot_scatter(x_data, y_data, title):
    plot_image = io.BytesIO()
    plt.figure(figsize=(8, 6))
    plt.scatter(x_data, y_data, alpha=0.5)
    plt.title(title)
    plt.xlabel('Log Level')
    plt.ylabel('Log Message Length')
    plt.tight_layout()
    plt.savefig(plot_image, format='png')
    plot_image.seek(0)
    plot_image_encoded = base64.b64encode(plot_image.getvalue()).decode('utf-8')
    plot_image.close()
    return plot_image_encoded

def plot_stacked_bar_chart(data, x_label, y_label):
    plot_image = io.BytesIO()
    plt.figure(figsize=(10, 6))
    stacked_data = data.groupby([x_label, y_label]).size().unstack()
    stacked_data.plot(kind='bar', stacked=True)
    plt.title('Stacked Bar Chart of {} vs {}'.format(x_label, y_label))
    plt.xlabel(x_label)
    plt.ylabel('Frequency')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(plot_image, format='png')
    plot_image.seek(0)
    plot_image_encoded = base64.b64encode(plot_image.getvalue()).decode('utf-8')
    plot_image.close()
    return plot_image_encoded

# Function to generate a pie chart
def plot_pie_chart(data, title):
    plot_image = io.BytesIO()
    plt.figure(figsize=(8, 6))
    data.plot(kind='pie', autopct='%1.1f%%', startangle=140)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(plot_image, format='png')
    plot_image.seek(0)
    plot_image_encoded = base64.b64encode(plot_image.getvalue()).decode('utf-8')
    plot_image.close()
    return plot_image_encoded

# Function to generate a line chart
def plot_line_chart(data, title, xlabel, ylabel, color='blue'):
    plot_image = io.BytesIO()
    plt.figure(figsize=(8, 6))
    data.plot(kind='line', color=color)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(plot_image, format='png')
    plot_image.seek(0)
    plot_image_encoded = base64.b64encode(plot_image.getvalue()).decode('utf-8')
    plot_image.close()
    return plot_image_encoded

if __name__ == '__main__':
    app.run(debug=True)
