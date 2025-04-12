import random
import math
import datetime

# --- Simulation Parameters ---
SIMULATION_DURATION_MINUTES = 24 * 60  # Simulate for 24 hours
TIME_STEP_MINUTES = 5                 # Process events every 5 minutes
NUM_SATELLITES = 15
NUM_STATIONS = 3

STATION_CAPACITIES = [2, 3, 4] # Max simultaneous connections per station
STATION_POSITIONS = [(0,0), (100, 50), (-50, 100)] # Simple 2D coordinates for distance

SATELLITE_DATA_MIN_GB = 5
SATELLITE_DATA_MAX_GB = 50
SATELLITE_DATA_LIMIT_PER_CONTACT_GB = 10
PRIORITY_SATELLITE_PROBABILITY = 0.15 # Chance a satellite is high priority
DAMAGED_SATELLITE_PROBABILITY = 0.10 # Chance a satellite starts damaged

NORMAL_TRANSMISSION_SPEED_GB_PER_MINUTE = 0.5
BURST_TRANSMISSION_SPEED_GB_PER_MINUTE = 1.5 # Faster speed for the first contact
MAX_CONNECTION_DISTANCE = 200 # Arbitrary distance unit

# Maintenance schedule: (start_minute, end_minute) relative to simulation start
STATION_MAINTENANCE = {
    0: [(120, 180)], # Station 0 offline from minute 120 to 180 (2nd to 3rd hour)
    1: [(300, 360)], # Station 1 offline from minute 300 to 360 (5th to 6th hour)
    # Station 2 has no scheduled maintenance in this example
}

TRANSMISSION_ERROR_PROBABILITY = 0.05 # Chance of error per time step per connection
JAMMING_PROBABILITY = 0.02          # Chance of complete jamming per time step per connection
ERROR_DATA_REDUCTION_FACTOR = 0.5   # If error, only transmit 50% of intended data

# --- Classes ---

class Satellite:
    def __init__(self, id, priority, initial_data, data_limit, position):
        self.id = id
        self.priority = priority
        self.data_to_send = initial_data
        self.data_limit_per_contact = data_limit
        self.position = position # Example: (x, y) tuple
        self.status = "operational" # "operational" or "damaged"
        self.first_contact_done = False
        self.connected_to_station_id = None
        self.connection_start_time = -1
        self.data_sent_this_contact = 0

    def __repr__(self):
        return f"Sat-{self.id} (Prio:{self.priority}, Data:{self.data_to_send:.1f}GB, Status:{self.status})"

    def is_damaged(self):
        return self.status == "damaged"

    def needs_connection(self):
        return self.data_to_send > 0 and self.connected_to_station_id is None and not self.is_damaged()

    def connect(self, station_id, current_time):
        self.connected_to_station_id = station_id
        self.connection_start_time = current_time
        self.data_sent_this_contact = 0
        # Burst speed applies until the *first* data chunk is successfully sent in the first connection
        # self.first_contact_done flag will be set after transmission

    def disconnect(self):
        self.connected_to_station_id = None
        self.connection_start_time = -1
        self.data_sent_this_contact = 0
        # Note: first_contact_done remains True once set

    def transmit_data(self, amount, current_time):
        transmitted = min(amount, self.data_to_send, self.data_limit_per_contact - self.data_sent_this_contact)
        self.data_to_send -= transmitted
        self.data_sent_this_contact += transmitted
        if transmitted > 0 and not self.first_contact_done:
             self.first_contact_done = True # Mark burst speed as used after first successful transmission
        return transmitted

    def distance_to(self, station_pos):
        return math.sqrt((self.position[0] - station_pos[0])**2 + (self.position[1] - station_pos[1])**2)


class GroundStation:
    def __init__(self, id, capacity, position, maintenance_schedule):
        self.id = id
        self.capacity = capacity
        self.position = position
        self.maintenance_schedule = maintenance_schedule
        self.connected_satellites = {} # {satellite_id: satellite_object}
        self.queue = [] # List of satellite objects waiting
        self.status = "online" # "online" or "offline_maintenance"

    def __repr__(self):
        return f"Station-{self.id} (Cap:{len(self.connected_satellites)}/{self.capacity}, Queue:{len(self.queue)}, Status:{self.status})"

    def update_status(self, current_time):
        was_offline = (self.status == "offline_maintenance")
        self.status = "online" # Default
        for start, end in self.maintenance_schedule:
            if start <= current_time < end:
                self.status = "offline_maintenance"
                break
        is_offline = (self.status == "offline_maintenance")

        if is_offline and not was_offline:
            # Just went offline, disconnect everyone
            disconnected_ids = list(self.connected_satellites.keys())
            for sat_id in disconnected_ids:
                sat = self.connected_satellites.pop(sat_id)
                sat.disconnect()
                log_event(current_time, "MAINTENANCE", f"Station-{self.id} going offline for maintenance. Disconnecting Sat-{sat_id}.")
            # Clear queue as well? Or let them wait until station is back? Let's clear.
            # cleared_queue = list(self.queue)
            # self.queue = []
            # for sat in cleared_queue:
            #      log_event(current_time, "MAINTENANCE", f"Station-{self.id} queue cleared due to maintenance start. Sat-{sat.id} removed.")

        elif not is_offline and was_offline:
             log_event(current_time, "MAINTENANCE", f"Station-{self.id} is back online after maintenance.")


    def is_online(self):
        return self.status == "online"

    def has_capacity(self):
        return len(self.connected_satellites) < self.capacity

    def add_to_queue(self, satellite):
        if satellite not in self.queue:
            self.queue.append(satellite)
            # Sort queue: Priority first, then FIFO (arrival order implicitly handled by append)
            self.queue.sort(key=lambda sat: sat.priority, reverse=True)
            return True
        return False # Already in queue

    def connect_satellite(self, satellite, current_time):
        if self.has_capacity() and self.is_online():
            self.connected_satellites[satellite.id] = satellite
            satellite.connect(self.id, current_time)
            return True
        return False

    def disconnect_satellite(self, satellite_id):
        if satellite_id in self.connected_satellites:
            sat = self.connected_satellites.pop(satellite_id)
            sat.disconnect()
            return sat
        return None

    def process_queue(self, current_time):
        processed_count = 0
        # Use a copy of the queue keys to iterate while modifying the original queue
        potential_connections = list(self.queue)
        for sat in potential_connections:
             if not self.has_capacity():
                 break # Station is full now

             # Attempt connection
             if self.connect_satellite(sat, current_time):
                 self.queue.remove(sat) # Remove from queue only if connection successful
                 log_event(current_time, "CONNECT", f"Sat-{sat.id} connected to Station-{self.id} from queue.")
                 processed_count += 1
             # else: # Should not happen if has_capacity check works, unless status changed mid-loop
             #    log_event(current_time, "WARNING", f"Station-{self.id} could not connect Sat-{sat.id} from queue despite apparent capacity.")

        return processed_count


# --- Simulation Logic ---

LOG_EVENTS = []

def format_time(minutes):
    """Converts simulation minutes to HH:MM format."""
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"

def log_event(time_minutes, event_type, message):
    """Adds an event to the log."""
    LOG_EVENTS.append({
        "time": time_minutes,
        "time_str": format_time(time_minutes),
        "type": event_type,
        "message": message
    })

def run_simulation():
    # --- Initialization ---
    satellites = []
    for i in range(NUM_SATELLITES):
        is_priority = random.random() < PRIORITY_SATELLITE_PROBABILITY
        initial_data = random.uniform(SATELLITE_DATA_MIN_GB, SATELLITE_DATA_MAX_GB)
        # Simple random positioning for demonstration
        position = (random.randint(-250, 250), random.randint(-250, 250))
        sat = Satellite(
            id=i,
            priority=is_priority,
            initial_data=initial_data,
            data_limit=SATELLITE_DATA_LIMIT_PER_CONTACT_GB,
            position=position
        )
        if random.random() < DAMAGED_SATELLITE_PROBABILITY:
            sat.status = "damaged"
            log_event(0, "INIT", f"Satellite-{sat.id} initialized as DAMAGED.")
        else:
             log_event(0, "INIT", f"Satellite-{sat.id} initialized (Prio:{is_priority}, Data:{initial_data:.1f}GB, Pos:{position}).")
        satellites.append(sat)

    stations = []
    for i in range(NUM_STATIONS):
        capacity = STATION_CAPACITIES[i] if i < len(STATION_CAPACITIES) else 2 # Default capacity
        position = STATION_POSITIONS[i] if i < len(STATION_POSITIONS) else (0,0)
        maintenance = STATION_MAINTENANCE.get(i, [])
        station = GroundStation(
            id=i,
            capacity=capacity,
            position=position,
            maintenance_schedule=maintenance
        )
        log_event(0, "INIT", f"Station-{station.id} initialized (Capacity:{capacity}, Pos:{position}, Maintenance:{maintenance}).")
        stations.append(station)

    # --- Simulation Loop ---
    log_event(0, "START", f"Simulation Started. Duration: {SIMULATION_DURATION_MINUTES} mins, Step: {TIME_STEP_MINUTES} mins.")

    for current_time in range(0, SIMULATION_DURATION_MINUTES, TIME_STEP_MINUTES):

        time_str = format_time(current_time)
        # print(f"--- Time: {time_str} ({current_time} min) ---") # Optional console output

        # 1. Update Station Status (Maintenance)
        for station in stations:
            station.update_status(current_time)

        # 2. Process Station Queues (Connect waiting satellites if possible)
        for station in stations:
            if station.is_online():
                station.process_queue(current_time)

        # 3. Satellites Attempt Connections
        random.shuffle(satellites) # Randomize order each step to avoid bias
        for sat in satellites:
            if sat.needs_connection():
                # Find potential stations (online and within range)
                potential_stations = []
                for station in stations:
                     if station.is_online():
                          dist = sat.distance_to(station.position)
                          if dist <= MAX_CONNECTION_DISTANCE:
                              potential_stations.append((dist, station))

                if not potential_stations:
                    # log_event(current_time, "INFO", f"Sat-{sat.id} needs connection but no suitable stations available/in range.")
                    continue

                # Choose closest station for this example
                potential_stations.sort(key=lambda x: x[0]) # Sort by distance
                chosen_station = potential_stations[0][1]

                # Attempt connection or queueing
                if chosen_station.has_capacity():
                    if chosen_station.connect_satellite(sat, current_time):
                         log_event(current_time, "CONNECT", f"Sat-{sat.id} connected to Station-{chosen_station.id} (Dist: {potential_stations[0][0]:.1f}).")
                    # else: # Should not happen if checks are correct
                    #     log_event(current_time, "WARNING", f"Sat-{sat.id} failed immediate connection to Station-{chosen_station.id} despite capacity.")

                else: # Station is full, try to queue
                    if chosen_station.add_to_queue(sat):
                        log_event(current_time, "QUEUE", f"Station-{chosen_station.id} is full. Sat-{sat.id} added to queue (Prio:{sat.priority}).")
                    # else: # Already in queue, do nothing
                        # pass


        # 4. Data Transmission for Connected Satellites
        for station in stations:
            if not station.is_online(): continue # Skip offline stations

            # Iterate over a copy of keys as dictionary might change during iteration
            connected_ids = list(station.connected_satellites.keys())
            for sat_id in connected_ids:
                # Ensure satellite still exists in the dict (might have been disconnected by maintenance)
                if sat_id not in station.connected_satellites:
                    continue

                sat = station.connected_satellites[sat_id]

                # Check for Jamming first
                if random.random() < JAMMING_PROBABILITY:
                    log_event(current_time, "ERROR", f"JAMMING detected for Sat-{sat_id} -> Station-{station.id}. No data transmitted this step.")
                    continue # Skip transmission this step

                # Determine speed
                speed = BURST_TRANSMISSION_SPEED_GB_PER_MINUTE if not sat.first_contact_done else NORMAL_TRANSMISSION_SPEED_GB_PER_MINUTE
                potential_data_this_step = speed * TIME_STEP_MINUTES

                # Check for Transmission Error (reduces data)
                is_error = random.random() < TRANSMISSION_ERROR_PROBABILITY
                if is_error:
                    potential_data_this_step *= ERROR_DATA_REDUCTION_FACTOR
                    log_event(current_time, "ERROR", f"Transmission error for Sat-{sat_id} -> Station-{station.id}. Data rate reduced.")

                # Transmit data (function handles limits)
                transmitted = sat.transmit_data(potential_data_this_step, current_time)

                if transmitted > 0:
                     log_event(current_time, "DATA_TX", f"Sat-{sat.id} -> Station-{station.id}: Sent {transmitted:.2f} GB. "
                                                     f"(Remaining: {sat.data_to_send:.1f} GB, Sent this contact: {sat.data_sent_this_contact:.1f}/{sat.data_limit_per_contact} GB). "
                                                     f"{'Burst speed.' if speed == BURST_TRANSMISSION_SPEED_GB_PER_MINUTE and not sat.first_contact_done else ''} {'Error occurred.' if is_error else ''}")

                # 5. Check for Disconnection Conditions
                disconnect_reason = None
                if sat.data_to_send <= 0:
                    disconnect_reason = "Data transfer complete"
                elif sat.data_sent_this_contact >= sat.data_limit_per_contact:
                    disconnect_reason = f"Contact data limit ({sat.data_limit_per_contact} GB) reached"
                # Add other potential disconnect reasons here if needed (e.g., signal loss, prolonged jamming)

                if disconnect_reason:
                    station.disconnect_satellite(sat_id)
                    log_event(current_time, "DISCONNECT", f"Sat-{sat_id} disconnected from Station-{station.id}. Reason: {disconnect_reason}.")


    # --- End of Simulation ---
    log_event(SIMULATION_DURATION_MINUTES, "END", "Simulation Finished.")
    print(f"Simulation finished. Log contains {len(LOG_EVENTS)} events.")

# --- HTML Report Generation ---

def generate_html_report(log_data, filename="simulation_log.html"):
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Satellite Communication Simulation Log</title>
    <style>
        body { font-family: sans-serif; line-height: 1.4; padding: 20px; background-color: #f4f4f4; }
        h1 { text-align: center; color: #333; }
        .log-entry {
            border-left: 5px solid #ccc;
            padding: 8px 15px;
            margin-bottom: 8px;
            background-color: #fff;
            border-radius: 4px;
            box-shadow: 1px 1px 3px rgba(0,0,0,0.1);
        }
        .log-entry .time { font-weight: bold; color: #555; min-width: 50px; display: inline-block;}
        .log-entry .type { font-weight: bold; margin: 0 10px; padding: 2px 6px; border-radius: 3px; color: white; }
        .log-INIT { border-left-color: #777; } .type-INIT { background-color: #777; }
        .log-START { border-left-color: #2a9fd6; } .type-START { background-color: #2a9fd6; }
        .log-END { border-left-color: #2a9fd6; } .type-END { background-color: #2a9fd6; }
        .log-CONNECT { border-left-color: #4CAF50; } .type-CONNECT { background-color: #4CAF50; }
        .log-DISCONNECT { border-left-color: #ff9800; } .type-DISCONNECT { background-color: #ff9800; }
        .log-QUEUE { border-left-color: #607d8b; } .type-QUEUE { background-color: #607d8b; }
        .log-DATA_TX { border-left-color: #00bcd4; } .type-DATA_TX { background-color: #00bcd4; color: #333; }
        .log-ERROR { border-left-color: #f44336; } .type-ERROR { background-color: #f44336; }
        .log-MAINTENANCE { border-left-color: #9c27b0; } .type-MAINTENANCE { background-color: #9c27b0; }
        .log-INFO { border-left-color: #bdbdbd; } .type-INFO { background-color: #bdbdbd; color: #333;}
        .log-WARNING { border-left-color: #ffeb3b; } .type-WARNING { background-color: #ffeb3b; color: #333;}

    </style>
</head>
<body>
    <h1>Satellite Communication Simulation Log</h1>
    <div id="log-container">
"""

    for entry in log_data:
        time_str = entry['time_str']
        event_type = entry['type']
        message = entry['message']
        # Basic HTML escaping for the message
        message_safe = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        html_content += f'        <div class="log-entry log-{event_type}">\n'
        html_content += f'            <span class="time">{time_str}</span>\n'
        html_content += f'            <span class="type type-{event_type}">{event_type}</span>\n'
        html_content += f'            <span class="message">{message_safe}</span>\n'
        html_content += f'        </div>\n'

    html_content += """
    </div>
</body>
</html>
"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"HTML report generated: {filename}")
    except IOError as e:
        print(f"Error writing HTML file: {e}")

# --- Main Execution ---
if __name__ == "__main__":
    # Set a seed for reproducibility if needed
    # random.seed(42)

    run_simulation()
    generate_html_report(LOG_EVENTS)