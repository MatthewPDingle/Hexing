import math

def simplify_polygon(points, tolerance=1.0):
    if len(points) <= 3:
        return points
    
    def point_line_distance(point, start, end):
        if start == end:
            return math.hypot(point[0] - start[0], point[1] - start[1])
        n = abs((end[0] - start[0]) * (start[1] - point[1]) - (start[0] - point[0]) * (end[1] - start[1]))
        d = math.hypot(end[0] - start[0], end[1] - start[1])
        return n / d

    def rdp(points, epsilon, dist):
        dmax = 0.0
        index = 0
        for i in range(1, len(points) - 1):
            d = dist(points[i], points[0], points[-1])
            if d > dmax:
                index = i
                dmax = d
        if dmax >= epsilon:
            results = rdp(points[:index+1], epsilon, dist)[:-1] + rdp(points[index:], epsilon, dist)
        else:
            results = [points[0], points[-1]]
        return results

    return rdp(points, tolerance, point_line_distance)