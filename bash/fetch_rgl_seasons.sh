#!/bin/bash

# Check if start ID was provided
if [ $# -eq 1 ]; then
    start_id=$1
else
    start_id=1
fi

# Create CSV header only if starting from ID 1
if [ $start_id -eq 1 ]; then
    echo "seasonId,name,formatName,regionName" > rgl-seasons.csv
fi

# Function to extract value from JSON for a given key
extract_value() {
    local json="$1"
    local key="$2"
    local value=$(echo "$json" | grep -o "\"$key\":\"[^\"]*\"" | cut -d'"' -f4)
    local null_value=$(echo "$json" | grep -o "\"$key\":null" | cut -d':' -f2)
    
    if [ ! -z "$value" ]; then
        echo "\"$value\""
    elif [ ! -z "$null_value" ]; then
        echo "null"
    else
        echo "null"
    fi
}

# Function to process and save season data
process_season() {
    local id=$1
    local response=$2
    
    if [[ $response == *"\"name\""* ]]; then
        name=$(extract_value "$response" "name")
        formatName=$(extract_value "$response" "formatName")
        regionName=$(extract_value "$response" "regionName")
        
        csv_line="$id,$name,$formatName,$regionName"
        echo "$csv_line"
        echo "$csv_line" >> rgl-seasons.csv
        return 0  # Valid season
    else
        csv_line="$id,null,null,null"
        echo "$csv_line"
        echo "$csv_line" >> rgl-seasons.csv
        return 1  # Invalid season
    fi
}

consecutive_nulls=0
current_id=$start_id
last_valid_id=$((start_id - 1))
should_exit=false

echo "Starting from ID: $start_id"

while ! $should_exit; do
    response=$(curl -s -X 'GET' "https://api.rgl.gg/v0/seasons/$current_id" -H 'accept: */*')
    
    if process_season $current_id "$response"; then
        last_valid_id=$current_id
        consecutive_nulls=0
    else
        consecutive_nulls=$((consecutive_nulls + 1))
    fi
    
    # Exit if we've gone too far past the last valid ID
    if [ $consecutive_nulls -gt 50 ]; then
        echo "Stopping: No valid seasons found in last 50 IDs"
        should_exit=true
    fi
    
    current_id=$((current_id + 1))
    sleep 0.5
done

echo "Data collection complete. Check rgl-seasons.csv for results."
