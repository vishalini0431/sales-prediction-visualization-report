from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import pandas as pd
import os
import matplotlib.pyplot as plt
from datetime import datetime
import calendar

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Ensure the uploads and visualization folders exist
uploads_dir = os.path.join(app.root_path, 'uploads')
visualizations_dir = os.path.join(app.root_path, 'visualizations')
os.makedirs(uploads_dir, exist_ok=True)
os.makedirs(visualizations_dir, exist_ok=True)

# Function to process the uploaded file and generate visualizations
def predict_items(file_path, months=None):
    try:
        # Read Excel file
        df = pd.read_excel(file_path)

        # Ensure necessary columns exist in the dataframe
        required_columns = ['customer_id', 'item', 'quantity', 'date']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Missing '{col}' column in the Excel file")

        # Convert 'date' column to datetime
        df['date'] = pd.to_datetime(df['date'])

        # Extract month from date
        df['month'] = df['date'].dt.to_period('M')

        # Filter by selected months if applicable
        if months:
            end_date = datetime.now()
            start_date = end_date - pd.DateOffset(months=int(months))
            df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

        # Group by 'item' and sum quantities
        item_totals = df.groupby('item')['quantity'].sum()

        # Predict item with the highest and lowest total quantity
        most_sold_item = item_totals.idxmax()
        least_sold_item = item_totals.idxmin()

        # Predict item likely to be sold next month (simple assumption)
        next_month_prediction = most_sold_item

        # Visualization: Plot total quantities
        fig, ax = plt.subplots()
        item_totals.plot(kind='bar', ax=ax, color='skyblue')
        ax.set_title(f'Total Quantity Sold Per Item Over Last {months} Months')
        ax.set_xlabel('Item')
        ax.set_ylabel('Total Quantity Sold')

        # Save the plot as a file
        total_sales_path = os.path.join(visualizations_dir, 'total_sales.png')
        plt.tight_layout()
        plt.savefig(total_sales_path)
        plt.close()

        # Visualization for most sold items
        fig, ax = plt.subplots()
        df_most_sold = df[df['item'] == most_sold_item]
        df_most_sold.groupby('month')['quantity'].sum().plot(kind='bar', ax=ax, color='green')
        ax.set_title(f'Most Sold Item: {most_sold_item} Sales Over Time')
        ax.set_xlabel('Month')
        ax.set_ylabel('Quantity Sold')
        most_sold_path = os.path.join(visualizations_dir, 'most_sold_items.png')
        plt.tight_layout()
        plt.savefig(most_sold_path)
        plt.close()

        # Visualization for least sold items
        fig, ax = plt.subplots()
        df_least_sold = df[df['item'] == least_sold_item]
        df_least_sold.groupby('month')['quantity'].sum().plot(kind='bar', ax=ax, color='red')
        ax.set_title(f'Least Sold Item: {least_sold_item} Sales Over Time')
        ax.set_xlabel('Month')
        ax.set_ylabel('Quantity Sold')
        least_sold_path = os.path.join(visualizations_dir, 'least_sold_items.png')
        plt.tight_layout()
        plt.savefig(least_sold_path)
        plt.close()

        return most_sold_item, least_sold_item, next_month_prediction, total_sales_path, most_sold_path, least_sold_path

    except Exception as e:
        raise ValueError(f'Error processing file: {str(e)}')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/uploader', methods=['POST'])
def uploader():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['file']
    months = request.form.get('months')

    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if file:
        file_path = os.path.join(uploads_dir, file.filename)
        file.save(file_path)

        # Predict items and generate visualizations
        try:
            most_sold_item, least_sold_item, next_month_prediction, total_sales_path, most_sold_path, least_sold_path = predict_items(file_path, months)
            flash(f'Predicted most sold item: {most_sold_item}')
            flash(f'Predicted least sold item: {least_sold_item}')
            flash(f'Item likely to be sold next month: {next_month_prediction}')
            return render_template('result.html', 
                                   total_sales_img=url_for('static', filename='visualizations/total_sales.png'),
                                   most_sold_img=url_for('static', filename='visualizations/most_sold_items.png'),
                                   least_sold_img=url_for('static', filename='visualizations/least_sold_items.png'),
                                   months=months)
        except ValueError as ve:
            flash(f'Error processing file: {str(ve)}')

        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download(filename):
    try:
        file_path = os.path.join(visualizations_dir, filename)
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        flash(f'Error downloading file: {str(e)}')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
