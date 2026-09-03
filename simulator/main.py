import time

from core.drone import Drone
from core.flight_controller import FlightController


# =========================
# CREATE DRONE
# =========================

drone = Drone()

controller = FlightController(drone)


# =========================
# TAKEOFF
# =========================

drone.takeoff()

controller.set_altitude(20)

controller.set_speed(10)


# =========================
# CLIMB
# =========================

print("\nTaking off...\n")


for second in range(6):

    controller.update(1)

    drone.update(1)

    status = drone.get_status()

    print(
        f"Time: {second + 1}s | "
        f"State: {status['state']} | "
        f"Position: "
        f"X={status['position']['x']}m "
        f"Y={status['position']['y']}m "
        f"Z={status['position']['z']}m | "
        f"Velocity: "
        f"X={status['velocity']['x']}m/s "
        f"Y={status['velocity']['y']}m/s "
        f"Z={status['velocity']['z']}m/s | "
        f"Battery={status['battery']}%"
    )

    time.sleep(1)


# =========================
# FLY FORWARD
# =========================

print("\nFlying forward...\n")

controller.move_forward()

controller.set_altitude(20)


for second in range(5):

    controller.update(1)

    drone.update(1)

    status = drone.get_status()

    print(
        f"Time: {second + 7}s | "
        f"State: {status['state']} | "
        f"Position: "
        f"X={status['position']['x']}m "
        f"Y={status['position']['y']}m "
        f"Z={status['position']['z']}m"
    )

    time.sleep(1)


# =========================
# MOVE RIGHT
# =========================

print("\nMoving right...\n")

controller.stop_horizontal()

controller.move_right()


for second in range(5):

    controller.update(1)

    drone.update(1)

    status = drone.get_status()

    print(
        f"Time: {second + 12}s | "
        f"State: {status['state']} | "
        f"Position: "
        f"X={status['position']['x']}m "
        f"Y={status['position']['y']}m "
        f"Z={status['position']['z']}m"
    )

    time.sleep(1)


# =========================
# LAND
# =========================

print("\nLanding...\n")

controller.stop_horizontal()

drone.land()

controller.set_altitude(0)


for second in range(10):

    controller.update(1)

    drone.update(1)

    status = drone.get_status()

    print(
        f"Time: {second + 17}s | "
        f"State: {status['state']} | "
        f"Position: "
        f"X={status['position']['x']}m "
        f"Y={status['position']['y']}m "
        f"Z={status['position']['z']}m"
    )

    time.sleep(1)

    if status["state"] == "LANDED":

        break


print("\nFlight complete.")