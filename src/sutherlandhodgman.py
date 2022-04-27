# From: https://github.com/matt77hias/Clipping

###############################################################################
## Clipping
## ----------------------------------------------------------------------------
## Convex polygon <> AABB
## Convex polygon <> AABP
###############################################################################
import numpy as np

def lerp(alpha, p_v1, p_v2):
    return alpha * p_v1 + (1.0 - alpha) * p_v2

PLANE_THICKNESS_EPSILON = 0.000001

def classify_distance(d):
    if (d > PLANE_THICKNESS_EPSILON):
        return 1
    elif (d < -PLANE_THICKNESS_EPSILON):
        return -1
    else:
        return 0

def signed_distance_aligned(s, a, c_v, p_v):
    return s * (p_v[a] - c_v[a])

def classify_aligned(s, a, c_v, p_v):
    d = signed_distance_aligned(s, a, c_v, p_v)
    return classify_distance(d)

def clip_AABB(p_vs, pMin, pMax, step=False):
    for a in range(pMin.shape[0]):
       p_vs = clip_AABP(p_vs, 1.0, a, pMin)
       if step: print(p_vs)
       p_vs = clip_AABP(p_vs, -1.0, a, pMax)
       if step: print(p_vs)
    return p_vs

def clip_AABP(p_vs, s, a, c_v):
    nb_p_vs = len(p_vs)
    if (nb_p_vs <= 1):  return []

    new_p_vs = []
    for j in range(nb_p_vs):
        p_v1 = p_vs[(j+nb_p_vs-1) % nb_p_vs]
        p_v2 = p_vs[j]

        d1 = classify_aligned(s, a, c_v, p_v1)
        d2 = classify_aligned(s, a, c_v, p_v2)

        if d1 * d2 == -1:
            alpha  = (p_v2[a] - c_v[a]) / (p_v2[a] - p_v1[a])
            p = lerp(alpha, p_v1, p_v2)
            new_p_vs.append(p)

        if d2 >= 0:
            _safe_append(new_p_vs, p_v2)

    if (len(new_p_vs) != 0) and (np.array_equal(new_p_vs[-1], new_p_vs[0])):
        return new_p_vs[:-1]
    else:
        return new_p_vs

# (c) Matthias Moulin
def _safe_append(new_p_vs, p_v):
    if (len(new_p_vs) == 0) or (not np.array_equal(new_p_vs[-1], p_v)):
        new_p_vs.append(p_v)
