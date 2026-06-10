# stats_milestones.py
import os
import pandas as pd

def generate_high_score_milestones(csv_path="train_log.csv"):
    # Check if the CSV log file exists
    if not os.path.exists(csv_path):
        print(f"Error: Log file '{csv_path}' not found. Please run game.py or train.py first!")
        return

    # Read data from the CSV file using pandas
    df = pd.read_csv(csv_path)

    if len(df) == 0:
        print("Log file is empty. No data to process!")
        return

    # Calculate cumulative total steps for timeline reference
    df['Total_Steps'] = df['Steps'].cumsum()

    print("=" * 65)
    print(f"{'NEW HIGH SCORE MILESTONES REPORT':^65}")
    print("=" * 65)
    # Print the table headers
    print(f"{'No.':<5} | {'Episode':<10} | {'Total Steps':<15} | {'New High Score':<15}")
    print("-" * 65)

    current_max_score = -1
    milestone_count = 0

    # Iterate through each match to detect when a new record is established
    for index, row in df.iterrows():
        score = int(row['Score'])
        
        # If the score of this episode breaks the previous high score record
        if score > current_max_score:
            current_max_score = score
            milestone_count += 1
            
            # Extract clean metrics from the row
            episode = int(row['Episode'])
            total_steps = int(row['Total_Steps'])
            
            # Print the formatted row in the table
            print(f"{milestone_count:<5} | {episode:<10} | {total_steps:<15,} | {current_max_score:<15}")

    print("=" * 65)
    print(f" Total Milestones Found: {milestone_count}")
    print(f" Ultimate High Score Achieved: {current_max_score} points")
    print("=" * 65)

if __name__ == "__main__":
    generate_high_score_milestones()