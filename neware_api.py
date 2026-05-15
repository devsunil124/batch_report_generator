import socket
import json
import random
import time
import xml.etree.ElementTree as ET

class NewareAPI:
    def __init__(self, ip="192.168.0.81", port=502):
        self.ip = ip
        self.port = port
        self.simulated_cycle = 12
        self.simulated_start_time = time.time()
        self.simulated_voltage = 1.6
        self.simulated_current = 200.0

    def test_connection(self):
        """Attempts to connect to the Neware TCP API port. Returns (bool, message)"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2.0)
                s.connect((self.ip, self.port))
                return True, f"Successfully connected to {self.ip}:{self.port}"
        except socket.timeout:
            return False, f"Connection to {self.ip}:{self.port} timed out."
        except ConnectionRefusedError:
            return False, f"Connection refused. Is the API service running on {self.port}?"
        except Exception as e:
            return False, f"Connection error: {str(e)}"

    def get_live_data(self, unit=1, channel=1, simulate=True):
        """
        Fetches live data. 
        If simulate=True or connection fails, returns simulated data.
        """
        if not simulate:
            try:
                # Basic TCP socket request format for Neware API
                # Note: The exact XML structure depends on BTS 8.0 specific manual.
                # This is a generic implementation to catch the response.
                req_xml = f'''<?xml version="1.0" encoding="utf-8"?>
<request>
    <command>get_channel_status</command>
    <unit>{unit}</unit>
    <channel>{channel}</channel>
</request>'''
                
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(3.0)
                    s.connect((self.ip, self.port))
                    s.sendall(req_xml.encode('utf-8'))
                    
                    data = s.recv(4096).decode('utf-8')
                    
                    # Try to parse the XML (this will fail if the structure is not valid XML)
                    root = ET.fromstring(data)
                    
                    # Example extraction (we will adapt these tags to the actual BTS 8.0 response once we see it)
                    voltage = float(root.findtext('voltage', '0.0'))
                    current = float(root.findtext('current', '0.0'))
                    cycle = int(root.findtext('cycle', '0'))
                    status = root.findtext('status', 'Unknown')
                    
                    return {
                        "status": status,
                        "voltage": voltage,
                        "current": current,
                        "cycle": cycle,
                        "capacity": 0.0,
                        "raw_xml": data, # Return raw XML for debugging
                        "simulated": False
                    }
                    
            except Exception as e:
                # Return explicit error if physical connection fails
                print("API Error:", str(e))
                return {
                    "status": "ERROR",
                    "voltage": 0.0,
                    "current": 0.0,
                    "cycle": 0,
                    "capacity": 0.0,
                    "raw_xml": f"Connection Error: {str(e)}",
                    "simulated": False
                }

        # === SIMULATION MODE ===
        # Generates realistic-looking ZnBr cycle data moving over time
        elapsed = time.time() - self.simulated_start_time
        
        # Simulate a 10-minute cycle
        cycle_phase = (elapsed % 600) / 600.0 
        
        if cycle_phase < 0.4:
            # Charge phase
            status = "Charging"
            self.simulated_current = 250.0 + random.uniform(-2, 2)
            self.simulated_voltage = 1.5 + (cycle_phase * 1.5) + random.uniform(-0.01, 0.01) # Voltage goes up
        elif cycle_phase < 0.5:
            # Rest phase
            status = "Resting"
            self.simulated_current = 0.0
            self.simulated_voltage = 1.8 + random.uniform(-0.01, 0.01)
        elif cycle_phase < 0.9:
            # Discharge phase
            status = "Discharging"
            self.simulated_current = -250.0 + random.uniform(-2, 2)
            self.simulated_voltage = 1.8 - ((cycle_phase-0.5) * 1.5) + random.uniform(-0.01, 0.01) # Voltage goes down
        else:
            # Rest before next cycle
            status = "Resting"
            self.simulated_current = 0.0
            self.simulated_voltage = 1.2 + random.uniform(-0.01, 0.01)
            
        current_cycle = self.simulated_cycle + int(elapsed // 600)

        return {
            "status": status,
            "voltage": round(self.simulated_voltage, 4),
            "current": round(self.simulated_current, 1),
            "cycle": current_cycle,
            "capacity": round(15.2 * cycle_phase, 2), # Dummy capacity
            "simulated": True
        }
