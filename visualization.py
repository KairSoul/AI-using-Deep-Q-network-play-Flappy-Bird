# visualize_csv.py
import os
import pandas as pd
import matplotlib.pyplot as plt

def draw_from_csv(csv_path="train_log.csv"):
    # Check if the CSV log file exists
    if not os.path.exists(csv_path):
        print(f"Error: Log file '{csv_path}' not found. Run game.py in AI mode first!")
        return

    # Read data from the CSV file using pandas
    df = pd.read_csv(csv_path)

    # Check if there is enough data to plot
    if len(df) < 2:
        print("Data is too small to build a proper timeline. Please train more matches!")
        return

    # --------------------------------------------------
    # DATA PROCESSING & NORMALIZATION
    # --------------------------------------------------
    # Calculate cumulative steps to establish a proper RL timeline on X-axis
    df['Total_Steps'] = df['Steps'].cumsum()
    
    # Calculate rolling window mean of scores to smooth out raw performance spikes
    window_size = min(20, len(df))
    df['Rolling_Mean_Score'] = df['Score'].rolling(window=window_size, min_periods=1).mean()

    # --------------------------------------------------
    # VISUALIZATION LAYER (Dual Subplots)
    # --------------------------------------------------
    x_axis = df['Total_Steps']
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5.5))

    # --- LEFT CHART: PERFORMANCE EVOLUTION ---
    # Plot smoothed rolling mean score line
    ax1.plot(x_axis, df['Rolling_Mean_Score'], color='#1f77b4', linewidth=2, label=f'Rolling Mean Score (w={window_size})')
    # Plot raw scores faintly behind to visualize variance
    ax1.plot(x_axis, df['Score'], color='#1f77b4', alpha=0.15, linewidth=0.5)
    
    ax1.set_xlabel('Total Steps')
    ax1.set_ylabel('Mean Score / Reward')
    ax1.set_title('AI Performance Evolution')
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.legend(loc='upper left')

    # --- RIGHT CHART: EXPLORATION RATE DECAY ---
    # Plot the Epsilon decay rate over the exact same timeline
    ax2.plot(x_axis, df['Epsilon'], color='#1f77b4', linewidth=2, label='Epsilon ($\epsilon$)')
    
    ax2.set_xlabel('Total Steps')
    ax2.set_ylabel('Epsilon Value')
    ax2.set_title('Exploration Rate ($\epsilon$ Decay)')
    ax2.grid(True, linestyle='--', alpha=0.5)
    ax2.legend(loc='upper right')

    # Adjust spacing dynamically to prevent overlapping
    plt.tight_layout()
    
    # Render graphs onto screen
    print("Reading CSV records and rendering charts...")
    plt.show()

if __name__ == "__main__":
    draw_from_csv()