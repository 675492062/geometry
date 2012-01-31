from geometry import (tran1, tran2, tran3, so2, so3, se2, se3, S1, SE2, SE3,
                      S2,
    Tran1, Tran2, Tran3, T1, T2, T3, R1, R2, SO2, SO3, R3, RandomManifold,
    assert_allclose)
from nose.plugins.attrib import attr
import itertools
import numpy as np


def check_geodesic_consistency(M, a, b, divisions=5):
    ''' 
        Check that there is consistency in the geodesics. 
    
        This is a test that 
        
            x(t) = geodesic( a, b, t) 
            
        interpolates between a and b, checking 
            
            d(a, x(t)) + d(x(t), b) = d(a,b)
    
    '''
    check_geodesic_consistency.description = (
        '%s: Checking geodesic consistency. '
        '(a: %s, b: %s)'
        % (M, M.friendly(a), M.friendly(b)))

    d = M.distance(a, b)

    ts = np.linspace(0, 1, divisions)
    for t in ts:
        c = M.geodesic(a, b, t)
        M.belongs(c)
        d1 = M.distance(a, c)
        d2 = M.distance(c, b)

        assert_allclose(d1 + d2, d, atol=1e-7)


def check_logmap1(M, a, b):
    ''' This is a test that:
    
            Exp_a( Log_a(b) ) = b
            
    '''
    check_logmap1.description = (
        '%s: Checking that logmap/expmap work. '
        '(a: %s, b: %s)'
        % (M, M.friendly(a), M.friendly(b)))

    bv = M.logmap(a, b)
    b2 = M.expmap(bv)
    assert_allclose(M.distance(b, b2), 0, atol=1e-7)


def check_logmap3(M, a, b):
    check_logmap3.description = (
        '%s: Checking that distance is consistent with logmap/expmap '
        '(a: %s, b: %s)'
        % (M, M.friendly(a), M.friendly(b)))

    d = M.distance(a, b)
    base, vel = M.logmap(a, b)
    ratios = [0.5, 0.3]
    for ratio in ratios:
        b2 = M.expmap((base, vel * ratio))
        d2 = M.distance(a, b2)
        assert_allclose(d * ratio, d2, atol=1e-7)


def check_friendly(M, a):
    M.friendly(a)


def check_interesting_point_in_manifold(M, p):
    check_interesting_point_in_manifold.description = '%s: %s' % (M, p)
    M.belongs(p)


def check_enough_points(M):
    points = list(M.interesting_points())
    if not points:
        raise ValueError('No test points for %s.' % M)


def check_manifold_suite(M, num_random=5):

    yield check_enough_points, M

    points = M.interesting_points()

    if isinstance(M, RandomManifold):
        for i in range(num_random): #@UnusedVariable
            points.append(M.sample_uniform())

    one_point_functions = [check_friendly, check_interesting_point_in_manifold]
    two_point_functions = [check_geodesic_consistency, check_logmap1,
                           check_logmap3]

    for f in one_point_functions:
        for a in points:
            yield f, M, a

    for f in two_point_functions:
        for a, b in itertools.product(points, points):
            yield f, M, a, b


def manifolds_to_check():
# import warnings
#    warnings.warn('Some checks disabled')
    return  [
        SO3, SO2,
        R1, R2, R3,
        T1, T2, T3,
        Tran1, Tran2, Tran3,
        SE2, SE3,
        S1, S2,
        se2, se3,
        so2, so3,
        tran1, tran2, tran3,
    ]


def test_dimensions():
    x = [
        (SO3, 3),
        (SO2, 1),
        (R1, 1),
        (R2, 2),
        (R3, 3),
        (T1, 1), (T2, 2), (T3, 3),
        (Tran1, 1), (Tran2, 2), (Tran3, 3),
        (SE2, 3), (SE3, 6),
        (S1, 1), (S2, 2),
        (se2, 3), (se3, 6),
        (so2, 1), (so3, 3),
        (tran1, 1), (tran2, 2), (tran3, 3)
    ]

    for M, dim in x:
        actual = M.get_dimension()
        msg = 'Expected %d for %s, got %d ' % (dim, M, actual)
        assert actual == dim, msg


@attr('manifolds')
def test_manifolds():
    for M in manifolds_to_check():
        #print('Testing %s' % M)
        for x in check_manifold_suite(M):
            yield x


if __name__ == '__main__':
    test_manifolds()
