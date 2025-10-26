#!/usr/bin/env python3
"""
iPhone Shortcuts Integration Script
Generates Shortcuts app code for health data export
"""

def generate_sleep_shortcut():
    """Generate Shortcuts app code for sleep data export"""
    return """
# Sleep Data Export Shortcut
# Add this to your iPhone Shortcuts app

# 1. Get Sleep Analysis
# Action: Get Health Sample
# Type: Sleep Analysis
# Period: Last 6 Hours

# 2. Format Data
# Action: Get Text from Input
# Format: JSON with sleep data fields

# 3. Send to API
# Action: Get Contents of URL
# Method: POST
# URL: https://your-api-endpoint.com/api/sleep
# Headers: Authorization: Bearer YOUR_API_KEY
# Body: Text from previous action

# 4. Handle Response
# Action: Show Result
# Display success/error message
"""

def generate_exercise_shortcut():
    """Generate Shortcuts app code for exercise data export"""
    return """
# Exercise Data Export Shortcut
# Add this to your iPhone Shortcuts app

# 1. Get Workout Data
# Action: Get Health Sample
# Type: Workout
# Period: Last 15 Minutes

# 2. Get Activity Data
# Action: Get Health Sample
# Type: Active Energy Burned
# Period: Last 15 Minutes

# 3. Get Heart Rate Data
# Action: Get Health Sample
# Type: Heart Rate
# Period: Last 15 Minutes

# 4. Combine Data
# Action: Combine Text
# Format: JSON with all exercise data

# 5. Send to API
# Action: Get Contents of URL
# Method: POST
# URL: https://your-api-endpoint.com/api/exercise
# Headers: Authorization: Bearer YOUR_API_KEY
# Body: Combined text

# 6. Handle Response
# Action: Show Result
# Display success/error message
"""

def generate_automation_setup():
    """Generate automation setup instructions"""
    return """
# iPhone Automation Setup

## Sleep Data Automation (Every 6 Hours)
1. Open Shortcuts app
2. Go to Automation tab
3. Create Personal Automation
4. Choose "Time of Day"
5. Set to repeat every 6 hours
6. Add action: Run Shortcut
7. Select "Sleep Data Export" shortcut

## Exercise Data Automation (Every 15 Minutes)
1. Open Shortcuts app
2. Go to Automation tab
3. Create Personal Automation
4. Choose "Time of Day"
5. Set to repeat every 15 minutes
6. Add action: Run Shortcut
7. Select "Exercise Data Export" shortcut

## Alternative: Location-Based Triggers
- When arriving at gym
- When leaving home
- When arriving at home

## Alternative: App-Based Triggers
- When Health app is opened
- When Workout app finishes
- When Sleep app is used
"""

if __name__ == "__main__":
    print("📱 iPhone Shortcuts Integration Guide")
    print("=" * 50)
    
    print("\n🛏️ SLEEP DATA SHORTCUT:")
    print(generate_sleep_shortcut())
    
    print("\n🏃 EXERCISE DATA SHORTCUT:")
    print(generate_exercise_shortcut())
    
    print("\n⏰ AUTOMATION SETUP:")
    print(generate_automation_setup())
    
    print("\n📋 SETUP CHECKLIST:")
    print("1. ✅ Create sleep data export shortcut")
    print("2. ✅ Create exercise data export shortcut")
    print("3. ✅ Set up 6-hour sleep automation")
    print("4. ✅ Set up 15-minute exercise automation")
    print("5. ✅ Test shortcuts manually")
    print("6. ✅ Verify data reaches your API")
    print("7. ✅ Check database for incoming data")
