#!/bin/bash

# Define the range of seasons you want to loop through
for season in {1..170}; do
  echo "Fetching data for season $season..."
  
  # Run the curl command with the current season number
  curl -X 'GET' \
    "https://api.rgl.gg/v0/seasons/$season" \
    -H 'accept: */*' >> "season_output.json"

  echo -e "\n\n" >> "season_output.json"

  # Optional: add a small delay between requests to be nice to the API
  sleep 1
done

echo "All seasons downloaded!"
