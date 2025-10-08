def tri(x, a, b, c):
    if x <= a or x >= c:
        return 0.0
    if x == b:
        return 1.0
    if x < b:
        return (x - a) / (b - a)
    return (c - x) / (c - b)

def fuzz_error(e):
    # Input scaled -100..100
    return {
        'N': tri(e, -100, -50, 0),
        'Z': tri(e, -30, 0, 30),
        'P': tri(e, 0, 50, 100)
    }

def fuzz_delta(d):
    return {
        'N': tri(d, -100, -50, 0),
        'Z': tri(d, -30, 0, 30),
        'P': tri(d, 0, 50, 100)
    }

# --- Fuzzy rule base ---
consequent = {'N': -80, 'Z': 0, 'P': 80}
rules = [
    ('N','N','N'), ('N','Z','N'), ('N','P','Z'),
    ('Z','N','N'), ('Z','Z','Z'), ('Z','P','P'),
    ('P','N','Z'), ('P','Z','P'), ('P','P','P')
]

def infer(error, delta):
    fe = fuzz_error(error)
    fd = fuzz_delta(delta)
    num = 0.0
    den = 0.0
    for (e_term, d_term, out_term) in rules:
        strength = min(fe[e_term], fd[d_term])
        num += strength * consequent[out_term]
        den += strength
    return num / den if den != 0 else 0.0

# --- Main tracking loop ---
def track(iterations):
    global last_err
    for _ in range(iterations):
        if ultrasonic_sensor.distance_centimeters > 10:
            r = color_sensor.reflected_light_intensity
            err = r - SP  # typically -50..+50

            # scale to -100..100
            e_scaled = max(-100, min(100, (err / 50.0) * 100.0))
            d = err - last_err
            d_scaled = max(-100, min(100, (d / 50.0) * 100.0))

            # fuzzy inference
            steer = infer(e_scaled, d_scaled)  # -80..80
            steer_norm = steer / 80.0          # normalize -1..1

            # compute motor speeds
            left  = BASE_SPEED * (1 + steer_norm)
            right = BASE_SPEED * (1 - steer_norm)

            # clamp to valid range
            speedL = int(max(min(left, 100), -100))
            speedR = int(max(min(right, 100), -100))

            # send to motors
            tank_drive.on(speedL, speedR)

            last_err = err

            # optional debug print
            print(f"R={r}, Err={err:+.1f}, Steer={steer:+.1f}, L={speedL}, R={speedR}")

            time.sleep(0.01)  # small delay for smooth control

    tank_drive.off(brake=True)
