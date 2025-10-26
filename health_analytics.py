#!/usr/bin/env python3
"""
Data Analytics and Visualization Script
Analyzes health data stored in Amazon RDS
"""

import os
import pandas as pd
import pymysql
from datetime import datetime, timedelta
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import seaborn as sns

load_dotenv()

class HealthDataAnalyzer:
    def __init__(self):
        self.connection = pymysql.connect(
            host=os.getenv('RDS_HOST'),
            user=os.getenv('RDS_USER'),
            password=os.getenv('RDS_PASSWORD'),
            database=os.getenv('RDS_DATABASE'),
            port=int(os.getenv('RDS_PORT', 3306)),
            charset='utf8mb4'
        )
    
    def get_sleep_analytics(self, days=30):
        """Analyze sleep data for the last N days"""
        query = """
        SELECT 
            date,
            sleep_duration_minutes,
            deep_sleep_minutes,
            light_sleep_minutes,
            rem_sleep_minutes,
            sleep_efficiency,
            heart_rate_avg
        FROM sleep_data 
        WHERE date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
        ORDER BY date
        """
        
        df = pd.read_sql(query, self.connection, params=[days])
        
        if df.empty:
            print("No sleep data available")
            return None
        
        # Calculate statistics
        stats = {
            'avg_sleep_duration': df['sleep_duration_minutes'].mean(),
            'avg_deep_sleep': df['deep_sleep_minutes'].mean(),
            'avg_light_sleep': df['light_sleep_minutes'].mean(),
            'avg_rem_sleep': df['rem_sleep_minutes'].mean(),
            'avg_sleep_efficiency': df['sleep_efficiency'].mean(),
            'avg_heart_rate': df['heart_rate_avg'].mean(),
            'total_nights': len(df)
        }
        
        return df, stats
    
    def get_exercise_analytics(self, days=7):
        """Analyze exercise data for the last N days"""
        query = """
        SELECT 
            timestamp,
            activity_type,
            duration_minutes,
            calories_burned,
            distance_km,
            steps,
            heart_rate_avg,
            heart_rate_max,
            active_energy_kcal
        FROM exercise_data 
        WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
        ORDER BY timestamp
        """
        
        df = pd.read_sql(query, self.connection, params=[days])
        
        if df.empty:
            print("No exercise data available")
            return None
        
        # Calculate statistics
        stats = {
            'total_sessions': len(df),
            'total_duration_minutes': df['duration_minutes'].sum(),
            'total_calories': df['calories_burned'].sum(),
            'total_distance_km': df['distance_km'].sum(),
            'total_steps': df['steps'].sum(),
            'avg_heart_rate': df['heart_rate_avg'].mean(),
            'max_heart_rate': df['heart_rate_max'].max(),
            'most_common_activity': df['activity_type'].mode().iloc[0] if not df['activity_type'].mode().empty else 'N/A'
        }
        
        return df, stats
    
    def create_sleep_visualization(self, df):
        """Create sleep data visualizations"""
        if df is None or df.empty:
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Sleep Data Analysis', fontsize=16)
        
        # Sleep duration over time
        axes[0, 0].plot(df['date'], df['sleep_duration_minutes'])
        axes[0, 0].set_title('Sleep Duration Over Time')
        axes[0, 0].set_ylabel('Minutes')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # Sleep stages distribution
        sleep_stages = ['deep_sleep_minutes', 'light_sleep_minutes', 'rem_sleep_minutes']
        axes[0, 1].pie([df[stage].mean() for stage in sleep_stages], 
                       labels=['Deep Sleep', 'Light Sleep', 'REM Sleep'],
                       autopct='%1.1f%%')
        axes[0, 1].set_title('Average Sleep Stages Distribution')
        
        # Sleep efficiency
        axes[1, 0].scatter(df['date'], df['sleep_efficiency'])
        axes[1, 0].set_title('Sleep Efficiency Over Time')
        axes[1, 0].set_ylabel('Efficiency %')
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # Heart rate during sleep
        axes[1, 1].plot(df['date'], df['heart_rate_avg'])
        axes[1, 1].set_title('Average Heart Rate During Sleep')
        axes[1, 1].set_ylabel('BPM')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig('sleep_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def create_exercise_visualization(self, df):
        """Create exercise data visualizations"""
        if df is None or df.empty:
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Exercise Data Analysis', fontsize=16)
        
        # Activity types distribution
        activity_counts = df['activity_type'].value_counts()
        axes[0, 0].pie(activity_counts.values, labels=activity_counts.index, autopct='%1.1f%%')
        axes[0, 0].set_title('Activity Types Distribution')
        
        # Calories burned over time
        df['date'] = pd.to_datetime(df['timestamp']).dt.date
        daily_calories = df.groupby('date')['calories_burned'].sum()
        axes[0, 1].plot(daily_calories.index, daily_calories.values)
        axes[0, 1].set_title('Daily Calories Burned')
        axes[0, 1].set_ylabel('Calories')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # Heart rate distribution
        axes[1, 0].hist(df['heart_rate_avg'].dropna(), bins=20, alpha=0.7)
        axes[1, 0].set_title('Heart Rate Distribution')
        axes[1, 0].set_xlabel('BPM')
        axes[1, 0].set_ylabel('Frequency')
        
        # Duration vs Calories
        axes[1, 1].scatter(df['duration_minutes'], df['calories_burned'])
        axes[1, 1].set_title('Duration vs Calories Burned')
        axes[1, 1].set_xlabel('Duration (minutes)')
        axes[1, 1].set_ylabel('Calories')
        
        plt.tight_layout()
        plt.savefig('exercise_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def generate_report(self):
        """Generate comprehensive health report"""
        print("📊 HEALTH DATA ANALYTICS REPORT")
        print("=" * 50)
        
        # Sleep analysis
        print("\n🛏️ SLEEP ANALYSIS (Last 30 Days)")
        sleep_data, sleep_stats = self.get_sleep_analytics(30)
        
        if sleep_stats:
            print(f"Average Sleep Duration: {sleep_stats['avg_sleep_duration']:.1f} minutes")
            print(f"Average Deep Sleep: {sleep_stats['avg_deep_sleep']:.1f} minutes")
            print(f"Average Light Sleep: {sleep_stats['avg_light_sleep']:.1f} minutes")
            print(f"Average REM Sleep: {sleep_stats['avg_rem_sleep']:.1f} minutes")
            print(f"Average Sleep Efficiency: {sleep_stats['avg_sleep_efficiency']:.1f}%")
            print(f"Average Heart Rate: {sleep_stats['avg_heart_rate']:.1f} BPM")
            print(f"Total Nights Recorded: {sleep_stats['total_nights']}")
            
            # Create sleep visualization
            self.create_sleep_visualization(sleep_data)
        
        # Exercise analysis
        print("\n🏃 EXERCISE ANALYSIS (Last 7 Days)")
        exercise_data, exercise_stats = self.get_exercise_analytics(7)
        
        if exercise_stats:
            print(f"Total Exercise Sessions: {exercise_stats['total_sessions']}")
            print(f"Total Duration: {exercise_stats['total_duration_minutes']:.1f} minutes")
            print(f"Total Calories Burned: {exercise_stats['total_calories']}")
            print(f"Total Distance: {exercise_stats['total_distance_km']:.2f} km")
            print(f"Total Steps: {exercise_stats['total_steps']}")
            print(f"Average Heart Rate: {exercise_stats['avg_heart_rate']:.1f} BPM")
            print(f"Maximum Heart Rate: {exercise_stats['max_heart_rate']} BPM")
            print(f"Most Common Activity: {exercise_stats['most_common_activity']}")
            
            # Create exercise visualization
            self.create_exercise_visualization(exercise_data)
        
        print("\n📈 Visualizations saved as:")
        print("   - sleep_analysis.png")
        print("   - exercise_analysis.png")
    
    def close_connection(self):
        """Close database connection"""
        self.connection.close()

if __name__ == "__main__":
    analyzer = HealthDataAnalyzer()
    
    try:
        analyzer.generate_report()
    except Exception as e:
        print(f"❌ Error generating report: {e}")
    finally:
        analyzer.close_connection()
