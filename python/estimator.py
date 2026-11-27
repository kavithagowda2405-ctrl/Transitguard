import math

def update(t_est, t_air, dt, tau):
    """First-order lag: payload follows air slowly."""
    return t_est + (t_air - t_est) * (1 - math.exp(-dt / tau))

def time_to_limit(t_est, t_air, limit, tau):
    """Seconds until t_est reaches limit if air stays at t_air.
    Returns None if the air is not beyond the limit
    or the estimate is already past it."""
    if (t_est - limit) * (t_air - limit) >= 0:
        return None
    return tau * math.log((t_est - t_air) / (limit - t_air))