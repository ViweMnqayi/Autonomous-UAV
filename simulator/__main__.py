"""
Entry point for running the simulator package directly.
Usage: python -m simulator
"""

import sys
import argparse
from simulator import print_package_info, check_dependencies

def main():
    """Main entry point for the simulator package"""
    parser = argparse.ArgumentParser(
        description='Autonomous UAV Simulation System'
    )
    parser.add_argument(
        '--info',
        action='store_true',
        help='Show package information'
    )
    parser.add_argument(
        '--check-deps',
        action='store_true',
        help='Check dependencies'
    )
    parser.add_argument(
        '--run',
        action='store_true',
        help='Run the simulation'
    )
    parser.add_argument(
        '--api',
        action='store_true',
        help='Start the API server'
    )
    
    args = parser.parse_args()
    
    if args.info:
        print_package_info()
        return
    
    if args.check_deps:
        deps = check_dependencies()
        print("Dependencies:")
        for dep, installed in deps.items():
            status = "[X]" if installed else "[ ]"
            print("  {0} {1}".format(status, dep))
        return
    
    if args.api:
        from simulator.main import start_server
        start_server()
        return
    
    if args.run:
        from simulator.core.drone import Drone
        from simulator.core.flight_controller import FlightController
        
        print("[Simulation] Starting simulation...")
        drone = Drone()
        controller = FlightController(drone)
        
        import time
        drone.takeoff()
        controller.set_altitude(10)
        
        try:
            while drone.state != "LANDED":
                controller.update(0.1)
                drone.update(0.1)
                status = drone.get_status()
                print("[State] {0} | [Alt] {1:.1f}m | [Battery] {2:.1f}%".format(
                    status['state'], 
                    status['position']['z'], 
                    status['battery']
                ))
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n[Simulation] Simulation stopped")
    
    if not any(vars(args).values()):
        print("Welcome to Autonomous UAV Simulation!")
        print("Usage:")
        print("  --info          Show package information")
        print("  --run           Start simulation")
        print("  --api           Start API server")
        print("  --check-deps    Check dependencies")

if __name__ == "__main__":
    main()