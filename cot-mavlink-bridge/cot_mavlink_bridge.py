import socket
import time
import argparse
import logging
from pymavlink import mavutil
from lxml import etree
from datetime import datetime, timezone, timedelta

def main():
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="CoT-MAVLink Bridge")
    parser.add_argument("--mavlink_ip", type=str, default="127.0.0.1", help="MAVLink UDP IP")
    parser.add_argument("--mavlink_port", type=int, default=14550, help="MAVLink UDP port")
    parser.add_argument("--cot_ip", type=str, default="<tailscale-ip>", help="TAK Server IP")
    parser.add_argument("--cot_port", type=int, default=8087, help="TAK Server port")
    parser.add_argument("--cot_cmd_port", type=int, default=8088, help="CoT command listen port")
    parser.add_argument("--send_rate", type=float, default=1.0, help="CoT GPS send rate (Hz)")
    parser.add_argument("--ttl", type=int, default=30, help="CoT event TTL (seconds)")
    parser.add_argument("--log", type=str, default="cot_out.xml", help="CoT XML log file")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--callsign", type=str, default="Alpha01", help="CoT callsign")
    parser.add_argument("--group", type=str, default="GroupA", help="Tactical group ID")
    args = parser.parse_args()

    MAVLINK_UDP_IP = args.mavlink_ip
    MAVLINK_UDP_PORT = args.mavlink_port
    COT_SERVER_IP = args.cot_ip
    COT_SERVER_PORT = args.cot_port
    COT_COMMAND_PORT = args.cot_cmd_port
    SEND_RATE = args.send_rate
    TTL = args.ttl
    LOG_FILE = args.log
    CALLSIGN = args.callsign
    GROUP = args.group
    DRONE_UID = f"drone-{socket.gethostname()}"

    # --- Logging Setup ---
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='[%(levelname)s] %(message)s'
    )

    # --- MAVLink Connection ---
    try:
        mav = mavutil.mavlink_connection(f'udp:{MAVLINK_UDP_IP}:{MAVLINK_UDP_PORT}', timeout=5)
        logging.info("Connecting to MAVLink stream...")
        heartbeat = mav.wait_heartbeat(timeout=10)
        if not heartbeat:
            print("❌ MAVLink connection timeout")
            exit(1)
        logging.info(f"Heartbeat received from system {mav.target_system} component {mav.target_component}")
    except Exception as e:
        logging.error(f"Failed to connect to MAVLink: {e}")
        return

    # --- CoT UDP Socket ---
    cot_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # --- CoT Command Listener Socket ---
    cmd_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    cmd_sock.bind(("0.0.0.0", COT_COMMAND_PORT))
    cmd_sock.setblocking(False)

    # --- CoT Sender Function ---
    def send_cot(lat, lon, alt):
        # Only send if GPS fix is available (not 0,0,0)
        if lat == 0.0 and lon == 0.0 and alt == 0.0:
            logging.debug("Skipping CoT heartbeat: no GPS fix yet.")
            return
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        stale = (datetime.now(timezone.utc) + timedelta(seconds=TTL)).isoformat().replace("+00:00", "Z")
        root = etree.Element(
            "event", version="2.0", type="a-f-G-U-C", uid=DRONE_UID,
            how="m-g", time=now, start=now, stale=stale
        )
        point = etree.SubElement(root, "point", lat=str(lat), lon=str(lon), hae=str(alt), ce="5.0", le="5.0")
        detail = etree.SubElement(root, "detail")
        contact = etree.SubElement(detail, "contact", callsign=CALLSIGN)
        group = etree.SubElement(detail, "group", name=GROUP, role="team")
        xml = etree.tostring(root, encoding="UTF-8")
        cot_sock.sendto(xml, (COT_SERVER_IP, COT_SERVER_PORT))
        logging.info(f"Sent CoT: lat={lat}, lon={lon}, alt={alt}")
        # Log XML to file
        try:
            xml_str = xml.decode("utf-8")
            with open(LOG_FILE, "a") as f:
                f.write(xml_str + "\n")
            if logging.getLogger().level == logging.DEBUG:
                logging.debug(f"CoT XML:\n{xml_str}")
        except Exception as e:
            logging.warning(f"Failed to log CoT XML: {e}")

    # --- CoT Command Parser Function ---
    def parse_cot_command(data):
        try:
            if isinstance(data, bytes):
                data = data.decode('utf-8')
            tree = etree.fromstring(data)
            detail = tree.find(".//detail")
            if detail is None:
                logging.warning("No <detail> in CoT command")
                return
            cmd = detail.find("command")
            if cmd is not None and cmd.get("action"):
                action = cmd.get("action")
                logging.info(f"Received command: {action}")
                if mav.target_system is None or mav.target_component is None:
                    logging.warning("MAVLink target system/component not initialized")
                    return
                if action == "ARM":
                    mav.mav.command_long_send(
                        mav.target_system, mav.target_component,
                        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                        0, 1, 0, 0, 0, 0, 0, 0
                    )
                    logging.info("Sent ARM command")
                elif action == "DISARM":
                    mav.mav.command_long_send(
                        mav.target_system, mav.target_component,
                        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                        0, 0, 0, 0, 0, 0, 0, 0
                    )
                    logging.info("Sent DISARM command")
                elif action == "RTL":
                    mav.mav.command_long_send(
                        mav.target_system, mav.target_component,
                        mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH,
                        0, 0, 0, 0, 0, 0, 0, 0
                    )
                    logging.info("Sent RTL command")
                else:
                    logging.warning(f"Unknown command action: {action}")
            else:
                logging.warning("No <command> with action in CoT command")
        except Exception as e:
            logging.error(f"Command parse error: {e}")

    # --- Main Loop ---
    logging.info("Starting CoT-MAVLink bridge...")
    last_cot_time = 0
    last_cmd_time = 0
    last_heartbeat_time = 0
    last_lat, last_lon, last_alt = 0.0, 0.0, 0.0
    try:
        while True:
            msg = mav.recv_match(type='GLOBAL_POSITION_INT', blocking=False)
            now = time.time()
            gps_updated = False
            if msg:
                lat = msg.lat / 1e7
                lon = msg.lon / 1e7
                alt = msg.alt / 1000.0
                last_lat, last_lon, last_alt = lat, lon, alt
                gps_updated = True

            # Send CoT if GPS updated (SEND_RATE Hz) or heartbeat interval (10s)
            if ((gps_updated and now - last_cot_time >= 1.0/SEND_RATE) or (now - last_heartbeat_time >= 10.0)):
                send_cot(last_lat, last_lon, last_alt)
                last_cot_time = now
                last_heartbeat_time = now

            # CoT ➜ MAVLink (rate limit: 10Hz)
            try:
                data, _ = cmd_sock.recvfrom(2048)
                if time.time() - last_cmd_time >= 0.1:
                    parse_cot_command(data)
                    last_cmd_time = time.time()
            except BlockingIOError:
                pass

            # ...handle other MAVLink messages if needed...
            time.sleep(0.05)
    except KeyboardInterrupt:
        logging.info("Exiting bridge.")

if __name__ == "__main__":
    main()