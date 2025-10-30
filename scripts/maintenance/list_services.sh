#!/bin/bash

# This script lists all available services and their statuses on a Ubuntu system.

echo "Listing all systemd services and their status..."
echo "--------------------------------------------------"
systemctl list-unit-files --type=service

echo ""
echo "Listing currently active/inactive services..."
echo "---------------------------------------------"
systemctl list-units --type=service --all

echo ""
echo "Checking status of each service..."
echo "----------------------------------"
for service in $(systemctl list-unit-files --type=service --no-pager --no-legend | awk '{print $1}'); do
    echo "Status for $service:"
    systemctl status "$service" --no-pager -n 0 | grep -E 'Loaded:|Active:'
    echo "----------------------------------"
done
