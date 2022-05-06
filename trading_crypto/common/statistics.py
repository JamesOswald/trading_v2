
def online_weighted_moving_average(old_average, total_weight, new_value, weight):
    old_average += (weight/total_weight) * (new_value - old_average)
    return old_average

